from main import _resolve_zone_pace_and_hr
from services.plan_generator import PlanGenerator


def test_coach_zone_edit_uses_the_same_threshold_pace_as_plan_generation():
    athlete = {
        "threshold_pace": "3:55",
        "aet_hr": 134,
        "ant_hr": 163,
        "zone2_pace_min": "6:30",
        "zone2_pace_max": "5:45",
    }
    pace, hr = _resolve_zone_pace_and_hr(athlete, "Zone 2", 60)
    expected = PlanGenerator.resolve_pace_zones(athlete, athlete.get("goal_type"))["zone2_pace"]
    assert pace == f"{expected} /km" == "4:54 - 4:30 /km"
    assert hr == "120-134 bpm"
