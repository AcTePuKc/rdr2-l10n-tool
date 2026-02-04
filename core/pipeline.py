from __future__ import annotations
from pathlib import Path
from collections import defaultdict, Counter
import shutil
from datetime import datetime
from dataclasses import dataclass


from .io_txt import Entry, scan_input_folder, write_txt_file
from .io_tsv import write_master_tsv, read_master_tsv
from .normalize import normalize_text, OFF, SAFE, STRICT
from .qa import run_qa, QaIssue, run_qa, write_qa_report

@dataclass
class Stats:
    files: int
    entries: int
    translated: int
    todo: int
    unique_files: int
    flags_top: list[tuple[str, int]]
    source_hint: str  # "input folder" или "master.tsv"

def compute_stats_from_master(master_path: Path) -> Stats:
    entries = read_master_tsv(master_path)
    files = len(set(e.file for e in entries if e.file))
    total = len(entries)
    translated = sum(1 for e in entries if e.translated.strip())
    todo = total - translated

    flags = [e.flags.strip() for e in entries if e.flags and e.flags.strip()]
    c = Counter(flags)
    flags_top = c.most_common(8)

    return Stats(
        files=files,
        entries=total,
        translated=translated,
        todo=todo,
        unique_files=files,
        flags_top=flags_top,
        source_hint=f"master: {master_path}"
    )

def compute_stats_from_input(input_dir: Path) -> Stats:
    entries, ignored = scan_input_folder(input_dir)
    files = len(set(e.file for e in entries if e.file))
    total = len(entries)

    # тук няма translated (входът е raw), но пак връщаме поле за консистентност
    return Stats(
        files=files,
        entries=total,
        translated=0,
        todo=total,
        unique_files=files,
        flags_top=[("ignored_txt_files", len(ignored))] if ignored else [],
        source_hint=f"input: {input_dir}"
    )

def build_master(input_dir: Path, master_path: Path) -> tuple[int, int]:
    entries, ignored = scan_input_folder(input_dir)
    # ignored txt files report-ване ще добавим в UI
    write_master_tsv(master_path, entries)
    return len(entries), len(ignored)


def backup_file(path: Path, backup_dir: Path) -> Path | None:
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = backup_dir / f"{path.stem}.backup_{ts}{path.suffix}"
    shutil.copy2(path, dst)
    return dst


def apply_chunks_to_master(master_entries: list[Entry], chunk_entries: list[Entry]) -> tuple[list[Entry], int]:
    # index master by (file,key)
    index: dict[tuple[str, str], Entry] = {
        (e.file, e.key): e for e in master_entries}
    updated = 0
    for c in chunk_entries:
        k = (c.file, c.key)
        if k in index:
            m = index[k]
            # пренасяме само work полетата
            m.translated = c.translated
            m.note = c.note
            m.flags = c.flags
            updated += 1
    return list(index.values()), updated


def merge_many_chunks(master_path: Path, chunk_paths: list[Path], backup_dir: Path | None = None) -> tuple[int, int, Path | None]:
    master = read_master_tsv(master_path)

    total_updated = 0
    total_rows = 0
    for cp in chunk_paths:
        ch = read_master_tsv(cp)
        total_rows += len(ch)
        master, upd = apply_chunks_to_master(master, ch)
        total_updated += upd

    backup_path = None
    if backup_dir is not None:
        backup_path = backup_file(master_path, backup_dir)

    # Презаписваме master.tsv (една истина, без двойни файлове)
    write_master_tsv(master_path, master)
    return total_updated, total_rows, backup_path


def export_output(master_path: Path, output_dir: Path, normalization_mode: str = SAFE,
                  use_crlf: bool = True, run_sanity: bool = True,
                  affected_only_from_chunks: list[Path] | None = None) -> tuple[int, list[QaIssue]]:
    entries = read_master_tsv(master_path)

    # optional: ограничаваме до засегнати файлове от chunk-ове
    affected_files: set[str] | None = None
    if affected_only_from_chunks:
        affected_files = set()
        for cp in affected_only_from_chunks:
            for e in read_master_tsv(cp):
                affected_files.add(e.file)

    # normalize
    for e in entries:
        if e.translated.strip():
            normed, _ = normalize_text(e.translated, normalization_mode)
            e.translated = normed

    issues = []
    if run_sanity:
        issues = run_qa(entries)
        # при критични проблеми може да блокираме export; засега връщаме issues и UI решава
        write_qa_report(Path("05_reports") / "qa_report.tsv", issues)

    CRITICAL = {"tag_mismatch", "placeholder_mismatch", "sl_mismatch"}

    critical_issues = [it for it in issues if it.issue_type in CRITICAL]
    if run_sanity and critical_issues:
        # Не експортираме нищо, само report-а
        return 0, issues

    # group by file
    by_file: dict[str, list[Entry]] = defaultdict(list)
    for e in entries:
        if affected_files is not None and e.file not in affected_files:
            continue
        by_file[e.file].append(e)

    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for fname, rows in by_file.items():
        out_path = output_dir / fname
        # запазваме реда както е в master (idx)
        rows.sort(key=lambda x: x.idx)
        write_txt_file(out_path, rows, use_crlf=use_crlf)
        written += 1

    return written, issues
