"""List static Vietnamese copy that breaks the banned-word rules (R3 of the uphill-ai-vietnamese-copy skill).

Usage: python scripts/vi_copy_check.py   (exit 1 when anything is found)
Test files and privacy/legal content are skipped; the prompts in plan_generator.py are LLM instructions that
quote the banned words on purpose, so the backend is not scanned.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.vi_humanizer import BANNED  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCAN = [(ROOT / "frontend/src", (".ts", ".tsx")), (ROOT / "ios-native", (".swift", ".xcstrings"))]
SKIP = (".test.", ".spec.", "/tests/", "node_modules", ".bak", "privacy/content")


def violations():
    for base, exts in SCAN:
        for path in sorted(base.rglob("*")):
            rel = str(path)
            if path.suffix not in exts or any(s in rel for s in SKIP):
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                low = line.lower()
                hits = [w for w in BANNED if w in low]
                if hits:
                    yield path.relative_to(ROOT), n, hits, line.strip()[:140]


if __name__ == "__main__":
    found = list(violations())
    for path, n, hits, line in found:
        print(f"{path}:{n} {hits}\n    {line}")
    print(f"{len(found)} line(s) with banned words")
    sys.exit(1 if found else 0)
