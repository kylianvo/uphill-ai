import pytest

from services import observability, plan_signals


def _quiet_db(monkeypatch, sent):
    monkeypatch.setattr(plan_signals.observability, "score", lambda **kw: sent.append(kw))
    monkeypatch.setattr(plan_signals.db, "get_plan_generation_trace", lambda pid: None)
    monkeypatch.setattr(plan_signals.db, "set_plan_generation_trace", lambda *a: None)


def test_volume_fit_and_tier_scored(monkeypatch):
    sent = []
    _quiet_db(monkeypatch, sent)
    monkeypatch.setattr(plan_signals.plan_checks, "run_checks", lambda w: [])
    monkeypatch.setattr(plan_signals.plan_checks, "pass_share", lambda r: None)
    workouts = [
        {"week_number": 2, "distance_km": 60.0, "type": "Easy"},
        {"week_number": 2, "distance_km": 60.0, "type": "Long Run"},
    ]
    plan_signals.record_generation(
        plan_id=1,
        user_id=2,
        block_number=1,
        workouts=workouts,
        trace_id="a" * 32,
        tier="sub_elite",
        measured_weekly_km=150.0,
    )
    by_name = {s["name"]: s["value"] for s in sent}
    assert by_name["plan_tier"] == "sub_elite"
    assert by_name["plan_volume_fit"] == 0.8


def test_volume_fit_is_symmetric_above_the_measured_volume(monkeypatch):
    sent = []
    _quiet_db(monkeypatch, sent)
    workouts = [{"week_number": 2, "distance_km": 125.0, "type": "Easy"}]
    plan_signals.record_generation(
        plan_id=1, user_id=2, block_number=1, workouts=workouts, trace_id="a" * 32, measured_weekly_km=100.0
    )
    assert {s["name"]: s["value"] for s in sent}["plan_volume_fit"] == 0.8


def test_no_volume_fit_without_measured_volume(monkeypatch):
    sent = []
    _quiet_db(monkeypatch, sent)
    plan_signals.record_generation(plan_id=1, user_id=2, block_number=1, workouts=[], trace_id="a" * 32, tier="novice")
    names = {s["name"] for s in sent}
    assert "plan_volume_fit" not in names and "plan_tier" in names


def test_a_plan_checks_failure_cannot_swallow_the_new_scores(monkeypatch):
    sent = []
    _quiet_db(monkeypatch, sent)

    def boom(w):
        raise RuntimeError("checks broke")

    monkeypatch.setattr(plan_signals.plan_checks, "run_checks", boom)
    workouts = [{"week_number": 2, "distance_km": 90.0}]
    plan_signals.record_generation(
        plan_id=1,
        user_id=2,
        block_number=1,
        workouts=workouts,
        trace_id="a" * 32,
        tier="elite",
        measured_weekly_km=100.0,
    )
    assert {s["name"] for s in sent} == {"plan_tier", "plan_volume_fit"}


def test_score_specs_accept_only_valid_tier_and_fit_values(monkeypatch):
    class Client:
        def __init__(self):
            self.calls = []

        def create_score(self, **kw):
            self.calls.append(kw)

    client = Client()
    monkeypatch.setattr(observability, "_client", client)
    observability.score(trace_id="a" * 32, name="plan_tier", value="elite")
    observability.score(trace_id="a" * 32, name="plan_tier", value="pro")
    observability.score(trace_id="a" * 32, name="plan_volume_fit", value=0.8)
    observability.score(trace_id="a" * 32, name="plan_volume_fit", value=1.2)
    assert [(c["name"], c["value"]) for c in client.calls] == [("plan_tier", "elite"), ("plan_volume_fit", 0.8)]


def test_live_scores_use_contextual_checks_and_exclude_unavailable(monkeypatch):
    sent = []
    _quiet_db(monkeypatch, sent)
    monkeypatch.setattr(
        plan_signals.plan_checks,
        "run_context_checks",
        lambda w, *, context: {"arithmetic": True, "progression": False, "access": None},
    )
    monkeypatch.setattr(plan_signals.plan_checks, "run_checks", lambda w: {"progression": True})
    plan_signals.record_generation(
        plan_id=1, user_id=2, block_number=1, workouts=[], trace_id="a" * 32, context={"week_coverage": {1: 7}}
    )
    assert {s["name"]: s["value"] for s in sent}["plan_checks"] == 0.5


@pytest.mark.parametrize(
    "minutes,phases,weeks,expected",
    [
        ([100, 40, 160], ["Base", "Recovery", "Base"], [1, 2, 3], 0.75),
        ([60, 90], ["Base", "Base"], [1, 3], 1.0),
    ],
)
def test_live_score_calendar_and_recovery_rebound(monkeypatch, minutes, phases, weeks, expected):
    from services.workout_prescription import apply_prescription

    sent = []
    _quiet_db(monkeypatch, sent)
    rows = []
    for duration, phase, week in zip(minutes, phases, weeks):
        row = {
            "week_number": week,
            "day_of_week": "Tuesday",
            "type": "Easy",
            "phase": phase,
            "segments": [
                {
                    "kind": "run",
                    "duration_minutes": duration,
                    "zone": "Zone 1",
                    "setting": "flat_outdoor",
                    "pace_min_per_km": 6,
                }
            ],
        }
        apply_prescription(row, lang="en")
        rows.append(row)
    plan_signals.record_generation(
        plan_id=1,
        user_id=2,
        block_number=1,
        workouts=rows,
        trace_id="a" * 32,
        context={"week_coverage": dict.fromkeys(weeks, 7)},
    )
    assert {s["name"]: s["value"] for s in sent}["plan_checks"] == expected
