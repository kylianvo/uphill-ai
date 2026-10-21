"""OFFLINE helper: propose natural rewrites of the Vietnamese text in saved persona runs, for HUMAN review.

Uses a vi-humanizer server running on this machine (https://github.com/ContextBoxAI/vi-humanizer, llama.cpp,
OpenAI-compatible). Nothing here runs in the app, CI or production, and nothing is applied automatically: the output
is a JSON of before/after pairs. A person keeps the good ones and adds them to kb_seed/vi_lexicon.json.

    python scripts/vi_polish.py /tmp/replay17/vn_hanoi_ham_lon_100k_vi.json --server http://127.0.0.1:7870 [--limit 40]

The prompt tells the model to keep the English training terms of the Vietnamese copy contract. It still tends to
translate Warm-up / Cool-down; treat that as a style call, not an error.
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

KEEP = (
    "Giữ nguyên các thuật ngữ tiếng Anh này, không dịch: Warm-up, Cool-down, Zone 1-5, Easy Run, Long Run, Tempo, "
    "power-hiking, Hill Sprints, Strides, carbs, sodium, electrolytes, race, pace, D+, Treadmill, Deload, Taper."
)
PROMPT = (
    "Viết lại văn bản trong ngoặc kép cho tự nhiên, như người Việt thật viết. Giữ nguyên thông tin, cách xưng hô và "
    f"mức trang trọng của bản gốc. {KEEP} Chỉ trả về văn bản đã viết lại, không thêm lời dẫn.\n\n"
    '"""\n{t}\n"""'
)


def rewrite(server: str, text: str, temperature: float = 0.2) -> str:
    body = {
        "model": "vi-humanizer",
        "messages": [{"role": "user", "content": PROMPT.replace("{t}", text)}],
        "temperature": temperature,
        "max_tokens": 400,
    }
    req = urllib.request.Request(
        f"{server}/v1/chat/completions", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    return json.load(urllib.request.urlopen(req, timeout=120))["choices"][0]["message"]["content"].strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run", help="a /tmp/<dir>/<persona>.json written by plan_live_personas.py")
    ap.add_argument("--server", default="http://127.0.0.1:7870")
    ap.add_argument("--limit", type=int, default=40, help="max distinct sentences to send")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    run = json.loads(Path(args.run).read_text())
    seen: dict[str, None] = {}
    for w in run["workouts"]:
        for field in ("title", "description", "fueling_tip"):
            for sentence in re.split(r"(?<=[.!?])\s+", str(w.get(field) or "")):
                if 20 <= len(sentence) <= 400 and sentence not in seen:
                    seen[sentence] = None
    pairs = []
    for sentence in list(seen)[: args.limit]:
        new = rewrite(args.server, sentence)
        if new != sentence:
            pairs.append({"before": sentence, "after": new})
            print(f"- {sentence}\n+ {new}\n")
    out = Path(args.out or Path(args.run).with_suffix(".vi_polish.json"))
    out.write_text(json.dumps(pairs, ensure_ascii=False, indent=1))
    print(f"{len(pairs)} proposals written to {out} (review them; nothing was applied)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
