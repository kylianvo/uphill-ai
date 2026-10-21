"""A beginner plan with an event must not be treated as a race plan by the goal engine."""

import main
from config import settings


class _SyncThread:
    def __init__(self, target, daemon=None):
        self.target = target

    def start(self):
        self.target()


def test_beginner_event_plan_gets_no_race_feasibility(monkeypatch):
    monkeypatch.setattr(settings, "GOAL_ASSESS_ON_PLAN_CREATE", True)
    monkeypatch.setattr(main.threading, "Thread", _SyncThread)
    plan = {
        "id": 5,
        "goal_type": "start_running",
        "milestone_target": "5k",
        "has_target_event": True,
        "course_distance_km": None,
    }
    monkeypatch.setattr(main, "get_plan_by_id", lambda pid: plan)
    monkeypatch.setattr(main, "get_user_by_id", lambda uid: {"id": uid})
    from services import goal_service

    monkeypatch.setattr(
        goal_service, "run_for_plan", lambda *a, **k: (_ for _ in ()).throw(AssertionError("race path"))
    )
    main._assess_new_plan(7, 5)  # no distance on a beginner plan: nothing to assess
