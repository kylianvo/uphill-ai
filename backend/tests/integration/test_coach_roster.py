"""Integration tests for the human-coach roster (Phase 1): is_coach on
users, the coach_athletes table, invite/accept, and the roster read
endpoint. See docs/superpowers/specs/2026-07-20-coach-role-design.md."""

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from db import engine


def _create_user(email: str) -> int:
    from db import create_or_get_user

    return create_or_get_user(email, email.split("@")[0].capitalize(), "mock", f"mock-{email}")["id"]


class TestSchema:
    def test_is_coach_defaults_to_false_for_new_users(self):
        user_id = _create_user("schema-default@uphill.ai")
        with engine.connect() as conn:
            row = conn.execute(text("SELECT is_coach FROM users WHERE id = :id"), {"id": user_id}).fetchone()
        assert row[0] is False

    def test_coach_athletes_row_defaults_status_to_invited(self):
        coach_id = _create_user("schema-coach@uphill.ai")
        athlete_id = _create_user("schema-athlete@uphill.ai")
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO coach_athletes (coach_id, athlete_id) VALUES (:c, :a)"),
                {"c": coach_id, "a": athlete_id},
            )
            conn.commit()
            row = conn.execute(
                text(
                    "SELECT status, invited_at, responded_at, removed_at FROM coach_athletes "
                    "WHERE coach_id = :c AND athlete_id = :a"
                ),
                {"c": coach_id, "a": athlete_id},
            ).fetchone()
        assert row.status == "invited"
        assert row.invited_at is not None
        assert row.responded_at is None
        assert row.removed_at is None

    def test_coach_athletes_rejects_duplicate_pair(self):
        coach_id = _create_user("schema-coach2@uphill.ai")
        athlete_id = _create_user("schema-athlete2@uphill.ai")
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO coach_athletes (coach_id, athlete_id) VALUES (:c, :a)"),
                {"c": coach_id, "a": athlete_id},
            )
            conn.commit()
            try:
                conn.execute(
                    text("INSERT INTO coach_athletes (coach_id, athlete_id) VALUES (:c, :a)"),
                    {"c": coach_id, "a": athlete_id},
                )
                conn.commit()
                raised = False
            except IntegrityError:
                conn.rollback()
                raised = True
        assert raised is True

    def test_coach_athletes_cascade_deletes_with_user(self):
        coach_id = _create_user("schema-coach3@uphill.ai")
        athlete_id = _create_user("schema-athlete3@uphill.ai")
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO coach_athletes (coach_id, athlete_id) VALUES (:c, :a)"),
                {"c": coach_id, "a": athlete_id},
            )
            conn.commit()
            conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": athlete_id})
            conn.commit()
            row = conn.execute(
                text("SELECT * FROM coach_athletes WHERE coach_id = :c AND athlete_id = :a"),
                {"c": coach_id, "a": athlete_id},
            ).fetchone()
        assert row is None
