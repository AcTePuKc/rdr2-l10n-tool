from __future__ import annotations

SAFE = "safe"
OFF = "off"
STRICT = "strict"

def normalize_text(text: str, mode: str) -> tuple[str, list[str]]:
    issues: list[str] = []
    if mode == OFF:
        return text, issues

    out = text

    # Safe: махаме опасни whitespace артефакти
    out2 = out.replace("\u00A0", " ")  # NBSP
    if out2 != out:
        issues.append("replaced_nbsp")
        out = out2

    # zero-width chars
    for zw in ["\u200B", "\u200C", "\u200D", "\uFEFF"]:
        if zw in out:
            out = out.replace(zw, "")
            issues.append("removed_zero_width")

    # trim само краища
    trimmed = out.strip()
    if trimmed != out:
        out = trimmed
        issues.append("trimmed_ends")

    if mode != STRICT:
        return out, issues

    # Strict: типографски към ASCII
    repl = {
        "–": "-",
        "—": "-",
        "“": "\"",
        "”": "\"",
        "„": "\"",
        "’": "'",
        "…": "...",
    }
    for a, b in repl.items():
        if a in out:
            out = out.replace(a, b)
            issues.append(f"strict_replaced_{ord(a)}")

    # ѝ: не го пипаме по подразбиране; добавя се само ако потвърдите, че RDR2 не го рендва
    return out, issues
