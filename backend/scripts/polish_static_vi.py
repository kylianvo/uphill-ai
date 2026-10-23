"""Polish static Vietnamese copy with vi-humanizer and rewrite the source files in place.

Usage (llama-server on :7870, see services/vi_humanizer.py):
  VI_HUMANIZER_URL=http://127.0.0.1:7870 python scripts/polish_static_vi.py translations|xcstrings [--limit N] [--dry]

Only the Vietnamese side is touched. A rewrite is kept only if services.vi_humanizer.acceptable() passes
(numbers, placeholders, protected terms, banned words, length); otherwise the original stays. Review with git diff.
"""

import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.vi_humanizer import humanize  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TRANSLATIONS = ROOT / "frontend/src/app/translations.ts"
XCSTRINGS = ROOT / "ios-native/UphillAI/Resources/Localizable.xcstrings"
MIN_CHARS = 80  # short labels have too little context; the model mangles them (seen on 40 translations.ts labels)
KV = re.compile(r'^(\s+)(\w+): "((?:[^"\\]|\\.)*)"(,?)\s*$')


async def polish_all(pairs: list[tuple[str, str | None]], limit: int | None) -> dict[str, str]:
    """pairs = (vietnamese, english source or None); returns {old vi: new vi} for accepted rewrites."""
    todo = list({vi: (vi, en) for vi, en in pairs if len(vi) >= MIN_CHARS}.values())[:limit]
    sem, out = asyncio.Semaphore(3), {}

    async def one(i: int, item: tuple[str, str | None]):
        t, en = item
        async with sem:
            new = await humanize(t, en)
        if new != t:
            out[t] = new
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(todo)}", flush=True)

    await asyncio.gather(*(one(i, t) for i, t in enumerate(todo)))
    print(f"polished {len(out)} of {len(todo)} candidate strings")
    return out


def translations(limit, dry):
    lines = TRANSLATIONS.read_text(encoding="utf-8").split("\n")
    start = next(i for i, ln in enumerate(lines) if ln.startswith("  vi: {"))
    vi = [(i, KV.match(ln)) for i, ln in enumerate(lines) if i > start]
    vi = [(i, m) for i, m in vi if m]
    values = {m.group(2): json.loads(f'"{m.group(3)}"') for _, m in vi}
    en = {m.group(2): json.loads(f'"{m.group(3)}"') for ln in lines[:start] if (m := KV.match(ln))}
    changed = asyncio.run(polish_all([(v, en.get(k)) for k, v in values.items()], limit))
    for i, m in vi:
        old = values[m.group(2)]
        if old in changed:
            lines[i] = f"{m.group(1)}{m.group(2)}: {json.dumps(changed[old], ensure_ascii=False)}{m.group(4)}"
    if not dry:
        TRANSLATIONS.write_text("\n".join(lines), encoding="utf-8")


def xcstrings(limit, dry):
    raw = XCSTRINGS.read_text(encoding="utf-8")
    data = json.loads(raw)
    olds = [
        v["localizations"]["vi"]["stringUnit"]["value"]
        for v in data["strings"].values()
        if "vi" in v.get("localizations", {})
    ]
    changed = asyncio.run(polish_all([(o, k) for k, o in zip(data["strings"], olds)], limit))
    for old, new in changed.items():
        a, b = f'"value" : {json.dumps(old, ensure_ascii=False)}', f'"value" : {json.dumps(new, ensure_ascii=False)}'
        assert a in raw, f"cannot locate {old!r}"
        raw = raw.replace(a, b)
    assert len(json.loads(raw)["strings"]) == len(data["strings"])
    if not dry:
        XCSTRINGS.write_text(raw, encoding="utf-8")


if __name__ == "__main__":
    which = sys.argv[1]
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    {"translations": translations, "xcstrings": xcstrings}[which](limit, "--dry" in sys.argv)
