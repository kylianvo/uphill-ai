"""Check the LLM judge (services/llm_judge.py) against hand-labelled synthetic cases.

  python scripts/judge_calibration.py [--min-agreement 0.85]

Each case in tests/golden/judge_calibration/cases.json labels the criteria it is about
(1 = clearly meets, 0 = clearly fails). The judge's 0-1 score counts as a pass at >= 0.5.
Prints agreement and the confusion counts per criterion, and exits 1 when any criterion's
agreement is below --min-agreement. Run it after every change to the llm_judge prompt.
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CASES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "golden", "judge_calibration", "cases.json"
)


def agreement(results: list[tuple[dict, dict]]) -> dict[str, dict[str, int]]:
    """criterion -> {tp, tn, fp, fn} over the labelled (expected, judged) pairs."""
    table: dict[str, dict[str, int]] = {}
    for expected, judged in results:
        for criterion, label in expected.items():
            if criterion not in judged:
                continue
            passed = judged[criterion] >= 0.5
            cell = ("tp" if passed else "fn") if label == 1 else ("fp" if passed else "tn")
            table.setdefault(criterion, {"tp": 0, "tn": 0, "fp": 0, "fn": 0})[cell] += 1
    return table


async def _judge_all(cases: list[dict]) -> list[tuple[dict, dict]]:
    from config import settings
    from services import llm_judge

    out = []
    for case in cases:
        try:
            judged = await llm_judge.judge_reply(
                question=case["question"],
                reply=case["reply"],
                evidence=None,
                lang=case["lang"],
                api_key=settings.GEMINI_API_KEY,
            )
        except Exception as exc:
            print(f"[calibration] {case['id']}: judge failed ({type(exc).__name__})")
            continue
        misses = [k for k, v in case["expected"].items() if (judged[k] >= 0.5) != (v == 1)]
        print(f"[calibration] {case['id']}: {'ok' if not misses else 'DISAGREE on ' + ', '.join(misses)}")
        out.append((case["expected"], judged))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-agreement", type=float, default=0.85)
    args = parser.parse_args()

    from services import observability

    observability.init()
    cases = json.load(open(CASES, encoding="utf-8"))["cases"]
    table = agreement(asyncio.run(_judge_all(cases)))
    failing = []
    for criterion, c in sorted(table.items()):
        total = sum(c.values())
        rate = (c["tp"] + c["tn"]) / total if total else 0.0
        print(f"[calibration] {criterion}: {rate:.0%} agreement over {total} labels {c}")
        if rate < args.min_agreement:
            failing.append(criterion)
    observability.flush()
    if failing:
        sys.exit(f"[calibration] below {args.min_agreement:.0%}: {', '.join(failing)}")


if __name__ == "__main__":
    main()
