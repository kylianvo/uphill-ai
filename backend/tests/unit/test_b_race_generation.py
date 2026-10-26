"""The B-race guard survives the generator's own post-processing (rule-based path, no model)."""

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import plan_reliability as pr  # noqa: E402


def test_b_race_keeps_its_own_text_and_the_rest_of_its_week():
    race = {"id": 1, "race_name": "B1", "race_date": (pr.A_RACE_DAY - timedelta(days=42)).isoformat(),  # a Saturday
            "distance_km": 21, "elevation_gain_m": 800, "effort": "training", "kept_against": None}  # fmt: skip
    ws = pr._generate([race])
    row = next(w for w in ws if w.get("plan_race_id") == 1)
    assert "B-race" in row["description"]
    assert row["day_of_week"] == "Saturday"
    sunday = [w for w in ws if w["week_number"] == row["week_number"] and w["day_of_week"] == "Sunday"]
    # The goal race's "rest after the race" rule must not touch it; the guard's own shaping may.
    assert sunday and sunday[0]["description"] != "Rest day. Sleep, light stretching and recovery."
