"""The human-coach co-pilot block shows the tier and volume base the plan was built on.
Scratch DB only; synthetic athlete."""

import db
from tests.integration.calendar_helpers import make_plan, this_monday


def test_copilot_block_has_the_level_line(auth_headers):
    import main

    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    db.set_plan_athlete_tier(plan_id, "sub_elite")
    db.set_plan_fitness_snapshot(plan_id, {"tier_score": 3.4, "weekly_km": 138.0, "weekly_km_source": "coros"})
    block = main._build_athlete_context_block(db.get_user_by_id(uid))
    assert "Level: sub_elite (score 3.4) · plan volume base 138 km (coros)" in block


def test_copilot_block_without_a_snapshot_shows_the_tier_only(auth_headers):
    import main

    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    db.set_plan_athlete_tier(plan_id, "recreational")
    block = main._build_athlete_context_block(db.get_user_by_id(uid))
    assert "Level: recreational\n" in block + "\n"
    assert "plan volume base" not in block
