"""Schema tests for activity match state. Needs a live Postgres."""

from sqlalchemy import text

from db import engine


def _columns(table: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = :t"),
            {"t": table},
        ).fetchall()
    return {r[0] for r in rows}


def test_activities_carries_match_state():
    cols = _columns("activities")
    assert {"matched_workout_id", "match_confidence", "match_method", "match_details"} <= cols


def test_matched_workout_id_survives_workout_deletion():
    # A deleted plan must not cascade-delete the athlete's activity history.
    with engine.connect() as conn:
        rule = conn.execute(
            text("""
            SELECT rc.delete_rule
            FROM information_schema.referential_constraints rc
            JOIN information_schema.key_column_usage kcu
              ON kcu.constraint_name = rc.constraint_name
            WHERE kcu.table_name = 'activities' AND kcu.column_name = 'matched_workout_id'
            """)
        ).scalar()
    assert rule == "SET NULL"


def test_one_workout_cannot_be_claimed_by_two_activities():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT indexdef FROM pg_indexes WHERE tablename = 'activities'")).fetchall()
    assert any("UNIQUE" in r[0] and "matched_workout_id" in r[0] for r in rows)
