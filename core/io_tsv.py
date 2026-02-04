from __future__ import annotations
from pathlib import Path
from typing import Iterable
import csv

from .io_txt import Entry

HEADER = ["file", "key", "source", "translated", "note", "flags"]

def write_master_tsv(path: Path, entries: Iterable[Entry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(HEADER)
        for e in entries:
            w.writerow([e.file, e.key, e.source, e.translated, e.note, e.flags])

def read_master_tsv(path: Path) -> list[Entry]:
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        entries: list[Entry] = []
        for idx, row in enumerate(r):
            entries.append(Entry(
                file=row.get("file",""),
                key=row.get("key",""),
                source=row.get("source",""),
                translated=row.get("translated",""),
                note=row.get("note",""),
                flags=row.get("flags",""),
                idx=idx
            ))
        return entries
