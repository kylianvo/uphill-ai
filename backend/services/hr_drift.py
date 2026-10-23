"""Heart-rate drift on a long run: how much less speed each heartbeat buys in the second half.

The durability signal from the literature review (Smyth et al.: later, smaller decoupling went with
better marathon performance). Computed from COROS's 1 km auto-laps using grade-adjusted pace, so
hills don't read as fatigue. Lower is better; a negative value means the second half was more efficient.
"""

import json
from statistics import mean

LAP_CM = 100000  # COROS lap distances are in centimetres: 1 km auto-laps
MIN_FULL_LAPS = 10


def drift_pct(lap_json: str) -> float | None:
    """Percent drop in grade-adjusted speed per heartbeat from the first half to the second, or None
    when the run has too few complete 1 km laps or any of them lacks heart rate or pace."""
    try:
        doc = json.loads(lap_json)
    except (json.JSONDecodeError, TypeError):
        return None
    group = next((g for g in doc.get("lapGroups") or [] if g.get("lapDistance") == LAP_CM), None)
    laps = [lap for lap in (group or {}).get("laps") or [] if lap.get("distance") == LAP_CM]
    if len(laps) < MIN_FULL_LAPS or any(not lap.get("avgHr") or not lap.get("adjustedPace") for lap in laps):
        return None
    half = len(laps) // 2

    def efficiency(part: list[dict]) -> float:
        return mean(1000 / lap["adjustedPace"] for lap in part) / mean(lap["avgHr"] for lap in part)

    return round((efficiency(laps[:half]) / efficiency(laps[half:]) - 1) * 100, 1)
