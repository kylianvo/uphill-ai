"""Render a persona run (scripts/plan_live_personas.py JSON) as a compact markdown review pack for a coach.

python scripts/render_persona_pack.py /tmp/personas/quang_aptrc80.json > pack.md
"""

import json
import sys
from pathlib import Path


def render(path: str) -> str:
    d = json.loads(Path(path).read_text())
    ws = d["workouts"]
    plan = d["plan"]
    out = [f"# {d['persona']}", ""]
    out.append(
        f"Plan: {plan['total_weeks']} weeks, race {plan['race_date']}, app-resolved level: {plan['athlete_tier']}."
    )
    f = d.get("feasibility") or {}
    out.append(
        f"App feasibility verdict: {f.get('verdict')} (week holds {f.get('capacity_h')} h, goal needs {f.get('needed_h')} h; levers {f.get('levers')})."
    )
    out += ["", "## Automatic checks", ""]
    for c in d["checks"]:
        out.append(f"- {'PASS' if c['ok'] else 'FAIL'}: {c['check']} - {c['detail']}")
    out += ["", "## Week by week (minutes; sessions)", ""]
    weeks = sorted({w["week_number"] for w in ws})
    for wk in weeks:
        a = [w for w in ws if w["week_number"] == wk and w["type"] != "Rest"]
        total = sum(float(w.get("duration_minutes") or 0) for w in a)
        phase = a[0].get("phase") if a else ""
        out.append(f"### Week {wk} [{phase}] total {total:.0f} min")
        for w in a:
            extra = []
            if w.get("elevation_gain_m"):
                extra.append(f"+{float(w['elevation_gain_m']):.0f} m")
            if w.get("mountain_mode"):
                extra.append(f"mountain:{w['mountain_mode']}")
            if w.get("target_pace"):
                extra.append(f"pace {w['target_pace']}")
            if w.get("treadmill_incline"):
                extra.append(f"treadmill incline {w['treadmill_incline']}")
            if w.get("treadmill_speed") and str(w["treadmill_speed"]) not in ("0", "0.0"):
                extra.append(f"treadmill speed {w['treadmill_speed']} km/h")
            if w.get("elevation_gain_m"):
                extra.append(f"D+ {float(w['elevation_gain_m']):.0f} m")
            desc = (w.get("description") or "").replace("\n", " ")  # full text: reviewers need the whole step list
            tip = (w.get("fueling_tip") or "").replace("\n", " ")
            if tip:
                desc += f" || Fueling/notes: {tip}"
            out.append(
                f"- {w['day_of_week'][:3]} {w['type']} {float(w.get('duration_minutes') or 0):.0f} min {w.get('target_zone', '')} "
                f"| {w.get('title', '')[:70]} {' '.join(extra)} | {desc}"
            )
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    print(render(sys.argv[1]))
