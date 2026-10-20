from datetime import date, timedelta

from config import settings
from services import goal_service
from services.plan_generator import PlanGenerator


class FakeDb:
    def __init__(self, user):
        self._user = user

    def get_user_by_id(self, user_id):
        return self._user


def _plan(started_weeks_ago, race_in_weeks):
    return {
        "id": 1, "user_id": 1, "goal_type": "finish", "course_distance_km": 56.4,
        "course_elevation_gain_m": 2946, "days_per_week": 6, "athlete_tier": "recreational",
        "start_date": (date.today() - timedelta(weeks=started_weeks_ago)).isoformat(),
        "race_date": (date.today() + timedelta(weeks=race_in_weeks)).isoformat(),
    }  # fmt: skip


ASSESSED = {"goals": {"a": 500.0, "b": 540.0, "c": 600.0}}


def test_a_started_plan_is_not_judged_on_a_stale_volume_and_a_shrinking_runway(monkeypatch):
    monkeypatch.setattr(goal_service, "db", FakeDb({"current_weekly_km": 30, "zone2_pace_min": "6:30"}))
    started = goal_service.feasibility_for(_plan(started_weeks_ago=10, race_in_weeks=8), ASSESSED)
    assert started["verdict"] != "unsupported" and "more_weeks" not in started["levers"]
    not_started = goal_service.feasibility_for(_plan(started_weeks_ago=-1, race_in_weeks=8), ASSESSED)
    assert "more_weeks" in not_started["levers"]


def test_pace_is_estimated_only_when_the_athlete_has_no_stored_zone2(monkeypatch):
    monkeypatch.setattr(goal_service, "db", FakeDb({"current_weekly_km": 60}))
    assert goal_service.feasibility_for(_plan(0, 26), ASSESSED)["confidence"] == "estimated"
    monkeypatch.setattr(goal_service, "db", FakeDb({"current_weekly_km": 60, "zone2_pace_min": "6:30"}))
    assert goal_service.feasibility_for(_plan(0, 26), ASSESSED)["confidence"] == "measured"


def test_adapting_a_week_does_not_ask_for_the_peak_long_run(monkeypatch):
    monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
    race = {
        "course_distance_km": 104.2,
        "course_elevation_gain_m": 5533,
        "goal_type": "time",
        "target_time_hours": 14.67,
    }
    weeks = [{"week_number": 12, "day_of_week": "Tuesday", "type": "Easy", "duration_minutes": 60, "phase": "Peak"}]
    kw = dict(plan_id=0, race_info=race, total_weeks=13, cutoff_time_hours=29.0, flat_pace_min_km=6.0)
    full = PlanGenerator._lint_issues(weeks, "sub_elite", target_week=None, **kw)
    adapt = PlanGenerator._lint_issues(weeks, "sub_elite", target_week=12, **kw)
    assert "TIME_ON_FEET" in {i.code for i in full}
    assert "TIME_ON_FEET" not in {i.code for i in adapt}
