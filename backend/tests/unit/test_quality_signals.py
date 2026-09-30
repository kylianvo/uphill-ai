"""Live quality signals: feedback tokens, catalog/brand scores, plan checks, goal outcomes."""

from config import settings
from services import goal_outcomes, observability, plan_checks, quality_signals

TRACE = "d" * 32


def test_feedback_token_round_trips_and_rejects_tampering(monkeypatch):
    monkeypatch.setattr(settings, "OBSERVABILITY_ID_SALT", "salt")
    token = quality_signals.feedback_token(TRACE, "gear_finder")

    assert quality_signals.verify_feedback_token(token) == (TRACE, "gear_finder")
    assert quality_signals.verify_feedback_token(token.replace("gear_finder", "nutrition_lab")) is None
    assert quality_signals.verify_feedback_token("e" * 32 + token[32:]) is None
    assert quality_signals.verify_feedback_token("garbage") is None
    assert quality_signals.feedback_token(None, "gear_finder") is None


def test_catalog_and_brand_scores(monkeypatch):
    calls = []
    monkeypatch.setattr(observability, "score", lambda **kw: calls.append((kw["name"], kw["value"])))
    recs = [{"brand": "Hoka", "model": "Speedgoat 7"}, {"brand": "Salomon", "model": "Genesis"}]

    quality_signals.score_recommendations(TRACE, recs, ["Hoka Speedgoat 7", "Salomon Genesis"], "Hoka")
    assert calls == [("catalog_valid", 1), ("brand_respected", 0)]

    calls.clear()
    quality_signals.score_recommendations(TRACE, recs[:1], ["Salomon Genesis"], None)
    assert calls == [("catalog_valid", 0)]


def test_plan_checks_flag_intensity_spikes_and_broken_sessions():
    easy = {"title": "Easy", "type": "Easy", "target_zone": "Zone 2", "duration_minutes": 60, "week_number": 1}
    hard = {"title": "Tempo", "type": "Tempo", "target_zone": "Zone 4", "duration_minutes": 60, "week_number": 1}
    assert plan_checks.run_checks([easy, easy, easy, hard]) == {"easy_share": True, "complete_sessions": True}
    assert plan_checks.run_checks([easy, hard])["easy_share"] is False

    week2 = {**easy, "week_number": 2, "duration_minutes": 300, "phase": "Build"}
    assert plan_checks.check_progression([{**easy, "phase": "Base"}, week2]) is False
    assert plan_checks.check_progression([{**easy, "phase": "Recovery"}, week2]) is True
    assert plan_checks.check_complete_sessions([{**easy, "duration_minutes": 0}]) is False
    assert plan_checks.pass_share({"a": True, "b": False}) == 0.5


def test_goal_outcome_scores_and_applied_choice():
    goals = {"a": 360, "b": 400, "c": 450}
    assert goal_outcomes.outcome_scores(goals, 410 * 60) == {"goal_hit": 1, "goal_error": 10 / 410}
    assert goal_outcomes.outcome_scores(goals, 500 * 60)["goal_hit"] == 0
    assert goal_outcomes.outcome_scores({}, 1000) is None
    assert goal_outcomes.applied_choice(goals, 400.4) == "realistic"
    assert goal_outcomes.applied_choice(goals, 420) == "custom"


def test_new_score_names_are_allowlisted(monkeypatch):
    class Client:
        calls: list = []

        def create_score(self, **kw):
            self.calls.append((kw["name"], kw["value"]))

    client = Client()
    monkeypatch.setattr(observability, "_client", client)
    for name, value in [
        ("block_compliance", 0.8),
        ("plan_reworked", 1),
        ("plan_checks", 1.0),
        ("goal_hit", 0),
        ("goal_error", 0.05),
        ("goal_applied", "realistic"),
        ("catalog_valid", 1),
        ("brand_respected", 0),
        ("goal_applied", "bogus"),
        ("block_compliance", 1.5),
    ]:
        observability.score(trace_id=TRACE, name=name, value=value)
    assert len(client.calls) == 8
