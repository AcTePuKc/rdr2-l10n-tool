from __future__ import annotations
from pathlib import Path
from .io_txt import Entry
from .io_tsv import write_master_tsv
from collections import Counter
import csv
from .io_tsv import read_master_tsv


def write_chunks_index(chunks_dir: Path, index_path: Path) -> None:
    rows = []

    for chunk_path in sorted(chunks_dir.glob("chunk_*.tsv")):
        entries = read_master_tsv(chunk_path)

        files = [e.file for e in entries if e.file]
        unique_files = sorted(set(files))
        file_count = len(unique_files)
        entry_count = len(entries)

        # heuristic hint
        hint = ""
        if unique_files == ["global.txt"]:
            hint = "global"
        elif any("menu" in f.lower() or "ui" in f.lower() for f in unique_files):
            hint = "ui"
        elif entry_count < 300:
            hint = "small"
        else:
            hint = "mixed"

        rows.append([
            chunk_path.name,
            entry_count,
            file_count,
            ";".join(unique_files[:10]) + (";..." if file_count > 10 else ""),
            hint
        ])

    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["chunk", "entries", "unique_files", "files", "hint"])
        for r in rows:
            w.writerow(r)

def chunk_entries(entries: list[Entry], chunk_size: int, separate_global: bool = True) -> list[list[Entry]]:
    chunks: list[list[Entry]] = []
    rest = entries

    if separate_global:
        g = [e for e in entries if e.file.lower() == "global.txt"]
        rest = [e for e in entries if e.file.lower() != "global.txt"]
        if g:
            # global може да е голям: режем го на chunks
            for i in range(0, len(g), chunk_size):
                chunks.append(g[i:i+chunk_size])

    for i in range(0, len(rest), chunk_size):
        chunks.append(rest[i:i+chunk_size])

    return chunks

def write_chunks(out_dir: Path, chunks: list[list[Entry]]) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for idx, ch in enumerate(chunks, start=1):
        p = out_dir / f"chunk_{idx:04d}.tsv"
        write_master_tsv(p, ch)
        paths.append(p)
    return paths
