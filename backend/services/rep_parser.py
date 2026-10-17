"""One unambiguous repetition block from a session's Process text."""

import re

_PROCESS = re.compile(r"Process\s*[:\-]\s*(.*?)(?=\b(?:Overall|Reason|Benefit|Warning)\s*[:\-]|$)", re.I | re.S)
_REP = re.compile(
    r"(?<![\w.,+\-])(\d+)\s*(?:[x×]|reps?\s+of)\s*(\d+(?:\.\d+)?)\s*-?\s*"
    r"(km|min(?:ute)?s?|phút|s(?:ec(?:ond)?s?)?|giây|m)\b",
    re.I,
)


def parse_rep_block(text: str) -> tuple[int, float, str] | None:
    process = _PROCESS.search(text)
    blocks = set()
    for match in _REP.finditer(process[1] if process else text):
        reps, value, unit = int(match[1]), float(match[2]), match[3].lower()
        unit = (
            "min"
            if unit.startswith("min") or unit == "phút"
            else "s"
            if unit.startswith("s") or unit == "giây"
            else unit
        )
        if reps > 0 and value > 0:
            blocks.add((reps, value, unit))
    return next(iter(blocks)) if len(blocks) == 1 else None
