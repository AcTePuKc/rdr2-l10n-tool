from __future__ import annotations
from dataclasses import dataclass
from .normalize import normalize_text, SAFE
from pathlib import Path
import re

KEY_RE = re.compile(r"^\s*(0x[0-9A-Fa-f]+|[_A-Za-z][_A-Za-z0-9]*)\s*=")


@dataclass
class Entry:
    file: str
    key: str
    source: str
    translated: str = ""
    note: str = ""
    flags: str = "todo"
    idx: int = 0  # вътрешно; не пишем в TSV, но помага

def is_text_kv_line(line: str) -> bool:
    return KEY_RE.match(line) is not None

def split_kv(line: str) -> tuple[str, str] | None:
    # split само по първото '='
    if "=" not in line:
        return None
    left, right = line.split("=", 1)
    key = left.strip()
    val = right.lstrip()
    # ако има водещ интервал след '=', го махаме само един път; пазим останалото
    return key, val.rstrip("\r\n")

def decode_best_effort(data: bytes) -> str:
    # BOM sniff
    if data.startswith(b"\xff\xfe"):
        return data.decode("utf-16le", errors="replace")
    if data.startswith(b"\xfe\xff"):
        return data.decode("utf-16be", errors="replace")
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig", errors="replace")

    # try utf-8 first
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        # fallback: latin-1 (1:1 mapping, не губи байтове)
        return data.decode("latin-1", errors="replace")

def read_txt_file(path: Path) -> list[Entry]:
    entries: list[Entry] = []
    data = path.read_bytes()
    text = decode_best_effort(data)
    raw = text.splitlines()
    i = 0
    idx = 0
    while i < len(raw):
        line = raw[i]
        if is_text_kv_line(line):
            kv = split_kv(line)
            if kv:
                key, source = kv
                entries.append(Entry(file=path.name, key=key, source=source, idx=idx))
                idx += 1
        i += 1
    return entries

def scan_input_folder(folder: Path) -> tuple[list[Entry], list[str]]:
    all_entries: list[Entry] = []
    ignored: list[str] = []
    for p in sorted(folder.glob("*.txt")):
        try:
            all_entries.extend(read_txt_file(p))
        except Exception:
            ignored.append(p.name)
    return all_entries, ignored

def write_txt_file(path: Path, entries: list[Entry], use_crlf: bool = True) -> None:
    nl = "\r\n" if use_crlf else "\n"
    lines: list[str] = []
    for e in entries:
        text = e.translated if e.translated.strip() else e.source
        text, _ = normalize_text(text, SAFE)
        lines.append(f"{e.key} = {text}")
        lines.append("")  # празен ред между entries
    # махаме последния празен ред само ако искаш супер чисто; засега го оставяме консистентно
    path.write_text(nl.join(lines), encoding="utf-8", newline=nl)
