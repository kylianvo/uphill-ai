"""plan_races persistence. Needs a live scratch Postgres (tests truncate)."""

from datetime import date, datetime

import pytest
from sqlalchemy import text

import db


@pytest.fixture()
def plan_id():
    with db.engine.connect() as conn:
        uid = conn.execute(
            text("INSERT INTO users (email, name, provider) VALUES (:e,'B','email') RETURNING id"),
            {"e": f"br-{datetime.now().timestamp()}@test.local"},
        ).scalar()
        conn.commit()
    return db.create_plan(uid, "VMM 70K", "2026-12-13", "time", 11.0, 12, start_date="2026-09-28")


def test_insert_get_update_plan_race(plan_id):
    rid = db.insert_plan_race(
        plan_id,
        {"race_name": "Ta Xua 25K", "race_date": "2026-11-01", "distance_km": 25, "elevation_gain_m": 1000,
         "options_km": [15, 25], "verdict": {"level": "good"}},
    )  # fmt: skip
    row = db.get_plan_race(plan_id, rid)
    assert row["race_date"] == date(2026, 11, 1) and row["status"] == "planned" and row["options_km"] == [15, 25]
    db.update_plan_race(rid, {"status": "cancelled", "not_a_column": 1})
    assert db.get_plan_races(plan_id) == []
    assert [r["id"] for r in db.get_plan_races(plan_id, include_cancelled=True)] == [rid]


def test_plan_delete_cascades_races(plan_id):
    db.insert_plan_race(plan_id, {"race_name": "X", "race_date": "2026-11-01", "distance_km": 21})
    with db.engine.connect() as conn:
        conn.execute(text("DELETE FROM plans WHERE id = :p"), {"p": plan_id})
        conn.commit()
    assert db.get_plan_races(plan_id, include_cancelled=True) == []
