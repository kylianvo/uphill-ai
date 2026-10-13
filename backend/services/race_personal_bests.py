from datetime import date
from typing import Any

ROAD_DISTANCES = {"5k": (5.0, 0.1), "10k": (10.0, 0.2), "hm": (21.0975, 0.5), "fm": (42.195, 0.5)}


def compute_road_prs(rows: list[dict[str, Any]], today: date) -> dict[str, dict[str, Any] | None]:
    eligible = [
        r
        for r in rows
        if r.get("selected")
        and r.get("discipline") == "road"
        and not r.get("is_dnf")
        and (r.get("finish_time_sec") or 0) > 0
    ]
    output = {}
    for key, (km, tolerance) in ROAD_DISTANCES.items():
        candidates = [r for r in eligible if abs(r["distance_km"] - km) < tolerance]
        if not candidates:
            output[key] = None
            continue
        best = min(
            candidates, key=lambda r: (r["finish_time_sec"], -date.fromisoformat(r["race_date"]).toordinal(), r["id"])
        )
        output[key] = {
            "result_id": best["id"],
            "time_sec": best["finish_time_sec"],
            "date": best["race_date"],
            "stale": (today - date.fromisoformat(best["race_date"])).days > 730,
        }
    return output
