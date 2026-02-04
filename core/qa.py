from __future__ import annotations
import re
from dataclasses import dataclass
from .io_txt import Entry
from pathlib import Path
import csv


TAG_BLOCK_RE = re.compile(r"~[^~]*~")
PLACEHOLDER_RE = re.compile(r"~\d+~")
SL_RE = re.compile(r"~sl:[^~]*~")
KEY_OK = re.compile(r"^(0x[0-9A-Fa-f]+|[_A-Za-z][_A-Za-z0-9]*)$")

@dataclass
class QaIssue:
    file: str
    key: str
    issue_type: str
    details: str

def write_qa_report(path: Path, issues: list[QaIssue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["file", "key", "issue_type", "details"])
        for it in issues:
            w.writerow([it.file, it.key, it.issue_type, it.details])

def count_tag_blocks(s: str) -> int:
    return len(TAG_BLOCK_RE.findall(s))

def count_placeholders(s: str) -> int:
    return len(PLACEHOLDER_RE.findall(s))

def sl_blocks(s: str) -> list[str]:
    return SL_RE.findall(s)

def run_qa(entries: list[Entry]) -> list[QaIssue]:
    issues: list[QaIssue] = []
    for e in entries:
        tgt = e.translated if e.translated.strip() else e.source

        # basic checks
        if not e.file or not e.key:
            issues.append(QaIssue(e.file, e.key, "bad_row", "missing file/key"))
            continue
        if not KEY_OK.match(e.key):
            issues.append(QaIssue(e.file, e.key, "bad_key", "unexpected key format"))

        # tag parity
        if count_tag_blocks(e.source) != count_tag_blocks(tgt):
            issues.append(QaIssue(e.file, e.key, "tag_mismatch",
                                 f"tag_blocks src={count_tag_blocks(e.source)} tgt={count_tag_blocks(tgt)}"))

        if count_placeholders(e.source) != count_placeholders(tgt):
            issues.append(QaIssue(e.file, e.key, "placeholder_mismatch",
                                 f"placeholders src={count_placeholders(e.source)} tgt={count_placeholders(tgt)}"))

        if sl_blocks(e.source) != sl_blocks(tgt):
            issues.append(QaIssue(e.file, e.key, "sl_mismatch", "sl blocks differ"))

        # length heuristic
        if e.translated.strip() and len(e.translated) > max(200, 2 * len(e.source)):
            issues.append(QaIssue(e.file, e.key, "long_translation",
                                 f"len src={len(e.source)} tgt={len(e.translated)}"))
    return issues
