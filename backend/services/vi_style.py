"""Natural Vietnamese for generated plan text, without a model at runtime.

Three layers, all deterministic and driven by kb_seed/vi_lexicon.json:
  1. sanitize_vi  - replaces the words and phrases the contract bans (and a treadmill-belt safety rewrite);
  2. vi_sentence_case - Title Case headings become sentence case, English training terms and proper nouns kept;
  3. naturalness_issues - detects what replacement cannot repair (hype words, doubled words, Title Case runs,
     untranslated English sentences, known weird phrases). The caller then swaps the text for a reviewed template,
     so unnatural wording never reaches the athlete.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

_LEXICON = Path(__file__).resolve().parent.parent / "kb_seed" / "vi_lexicon.json"

_UNSAFE_BELT = (  # never a jump onto a moving treadmill belt, in either language
    (
        r"jump(?:ing)?\s+(?:on|onto)\s+(?:the\s+)?(?:moving\s+)?(?:belt|treadmill)",
        "step onto the belt only after it is running at walking speed",
    ),
    (
        r"nhảy\s+(?:vào|lên)\s+(?:belt|băng chuyền|máy chạy)(?:\s+bứt tốc)?",
        "bước lên belt khi belt đang chạy ở tốc độ đi bộ",
    ),
)


@lru_cache(maxsize=1)
def lexicon() -> dict:
    return json.loads(_LEXICON.read_text(encoding="utf-8"))


def _keep() -> frozenset[str]:
    return frozenset(lexicon()["keep_english"])


def sanitize_belt(text: str) -> str:
    """The treadmill-belt safety rewrite alone (English plans)."""
    return re.sub(_UNSAFE_BELT[0][0], _UNSAFE_BELT[0][1], text, flags=re.IGNORECASE)


def sanitize_vi(text: str) -> str:
    """Replaces the banned Vietnamese words and phrases the model still writes and rewrites any instruction to
    jump onto a moving treadmill belt."""
    for pattern, replacement in [tuple(p) for p in lexicon()["replace"]] + list(_UNSAFE_BELT):
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    # a word the model repeats by accident ("Khởi động động", "nước rút rút", "dốc dốc")
    text = re.sub(r"\b(\w{3,})\s+\1\b", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"(Khởi động) động\b", r"\1", text)
    text = re.sub(r"(nước rút) rút\b", r"\1", text)
    from services.training_mountains import MOUNTAINS

    for m in MOUNTAINS.values():  # the model lowercases place names ("núi hàm lợn")
        place = m.name_vi.split(" ", 1)[1] if m.name_vi.split()[0] in ("Núi", "Trail") else m.name_vi
        text = re.sub(rf"\b(núi|Núi|trail|Trail)\s+{re.escape(place)}\b", rf"\1 {place}", text, flags=re.IGNORECASE)
    return text


def vi_sentence_case(title: str, keep: frozenset[str] = frozenset()) -> str:
    """A Title Case Vietnamese heading ('Buổi Chạy Đường Dài') becomes sentence case; English technical terms,
    numbers, acronyms and the proper nouns in `keep` keep their form. Short or already sentence-case titles are
    untouched."""
    words = title.split()
    capped = [w for w in words if w[:1].isupper()]
    if len(words) < 3 or len(capped) < 0.6 * len(words):
        return title
    terms = _keep()
    out = [
        w
        if (w.strip(".,:;()") in terms or w.strip(".,:;()") in keep or any(c.isdigit() for c in w) or w.isupper())
        else w.lower()
        for w in words
    ]
    out[0] = out[0][:1].upper() + out[0][1:]
    return " ".join(out)


_WORD = re.compile(r"[^\W\d_]+(?:[-'][^\W\d_]+)*", re.UNICODE)


def naturalness_issues(text: str, keep: frozenset[str] = frozenset()) -> list[str]:
    """What is still unnatural after sanitizing. Empty means the text may go to the athlete."""
    issues: list[str] = []
    lower = text.lower()
    for word in lexicon()["banned"]:
        if word.lower() in lower:
            issues.append(f"banned:{word}")
    if re.search(r"\b(\w{3,})\s+\1\b", text, flags=re.IGNORECASE):
        issues.append("doubled-word")
    from services.training_mountains import MOUNTAINS

    names = {tok for m in MOUNTAINS.values() for tok in f"{m.name_vi} {m.name_en}".split()}
    terms = _keep() | names | keep  # English terms and proper nouns are not "unnatural"
    for part in re.split(r"[.;:→\n]+", text):  # a run of capitalised words inside one clause
        run = 0
        for token in _WORD.findall(part):
            if token[:1].isupper() and token not in terms and not token.isupper():
                run += 1
                if run >= 4:
                    issues.append("title-case")
                    break
            else:
                run = 0
        if "title-case" in issues:
            break
    for sentence in re.split(r"[.;→\n]+", text):
        tokens = _WORD.findall(sentence)
        if len(tokens) < 6:
            continue
        english = [t for t in tokens if t.isascii() and t not in terms and t.lower() not in {"a", "e"}]
        if len(english) >= 0.7 * len(tokens):
            issues.append("english-sentence")
            break
    return issues
