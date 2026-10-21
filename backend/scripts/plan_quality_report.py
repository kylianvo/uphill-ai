"""Score saved persona runs with plan_quality: python scripts/plan_quality_report.py /tmp/personas2 /tmp/rules"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import plan_live_personas as P  # noqa: E402

from services import plan_quality  # noqa: E402

for d in sys.argv[1:]:
    print(f"== {d}")
    for f in sorted(Path(d).glob("*.json")):
        run = json.loads(f.read_text())
        persona = P.PERSONAS[run["persona"]]
        plan = persona["plan"]
        z2 = f"{persona['user']['zone2_pace_min']} - {persona['user']['zone2_pace_max']}"
        outdoor = bool(
            plan.get("training_mountain")
            or plan.get("mountain_days")
            or plan.get("training_environment") in ("hilly", "mixed")
        )
        rows = plan_quality.assess(
            run["workouts"],
            {
                **plan,
                **{k: persona["user"].get(k) for k in ("aet_hr", "ant_hr", "threshold_source")},
                "outdoor_climbing": outdoor,
            },
            z2,
        )
        bad = [f"{c.name.split(':')[0][:34]} [{c.detail[:45]}]" for c in rows if not c.ok]
        print(f"{run['persona']:30} {len(rows) - len(bad)}/{len(rows)}  " + "; ".join(bad))
