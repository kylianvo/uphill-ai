from datetime import UTC, datetime

from services import beginner_milestones as bm
from services.athlete_tier import get_profile
from services.plan_rules import build_rules_block

BEGINNER = get_profile("beginner")
NOW = datetime(2026, 10, 20, tzinfo=UTC)


def _ms(target="10k", achieved=(), event=None):
    rows = [{"milestone_key": k, "achieved_at": NOW, "source": "auto"} for k in achieved]
    ctx = bm.serialize(target, bool(event), rows)
    ctx["event"] = event
    return ctx


def test_rules_without_milestones_unchanged():
    assert build_rules_block(BEGINNER, 5) == build_rules_block(BEGINNER, 5, milestones=None)


def test_rules_stage_b_only_after_jog_30_on_10k():
    before = build_rules_block(BEGINNER, 30, milestones=_ms("10k", ["jog_5", "jog_10", "jog_20"]))
    after = build_rules_block(BEGINNER, 30, milestones=_ms("10k", ["jog_5", "jog_10", "jog_20", "jog_30"]))
    five_k = build_rules_block(BEGINNER, 30, milestones=_ms("5k", ["jog_30"]))
    assert "STAGE B" not in before and "STAGE B" not in five_k
    assert "STAGE B" in after and "plan_lint" not in after
    assert "25%" in after  # the long-run growth cap comes from plan_lint.MAX_LONG_RUN_GROWTH


def test_goal_description_names_target_next_and_event():
    text = bm.goal_description(_ms("5k", ["first_session"], event={"name": "Parkrun", "date": "2026-12-12"}))
    assert "First 5K" in text and "5 minutes of unbroken jogging" in text and "weeks 3-5" in text
    assert "Parkrun" in text and "2026-12-12" in text and "Walk breaks are part of the plan" in text


def test_goal_description_without_event_omits_event_text():
    assert "event" not in bm.goal_description(_ms("5k")).lower()


def test_goal_description_none_without_milestones():
    assert bm.goal_description(None) is None
