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
