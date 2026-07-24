"""Integration tests for the human-coach roster (Phase 1): is_coach on
users, the coach_athletes table, invite/accept, and the roster read
endpoint. See docs/superpowers/specs/2026-07-20-coach-role-design.md."""

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from db import (
    accept_coach_invite,
    create_coach_invite,
    engine,
    get_active_coach_link_for_athlete,
    get_coach_athlete_by_id,
    get_coach_athlete_link,
    get_roster_for_coach,
    set_user_is_coach,
)


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


class TestDbHelpers:
    def test_set_user_is_coach_flips_the_flag(self):
        user_id = _create_user("helper-coach@uphill.ai")
        assert set_user_is_coach(user_id, True) is True
        with engine.connect() as conn:
            row = conn.execute(text("SELECT is_coach FROM users WHERE id = :id"), {"id": user_id}).fetchone()
        assert row[0] is True

    def test_create_coach_invite_inserts_invited_row(self):
        coach_id = _create_user("helper-coach2@uphill.ai")
        athlete_id = _create_user("helper-athlete2@uphill.ai")
        link = create_coach_invite(coach_id, athlete_id)
        assert link["status"] == "invited"
        assert link["coach_id"] == coach_id
        assert link["athlete_id"] == athlete_id

    def test_create_coach_invite_reopens_a_removed_link(self):
        coach_id = _create_user("helper-coach3@uphill.ai")
        athlete_id = _create_user("helper-athlete3@uphill.ai")
        first = create_coach_invite(coach_id, athlete_id)
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE coach_athletes SET status = 'removed', removed_at = NOW() WHERE id = :id"),
                {"id": first["id"]},
            )
            conn.commit()
        reopened = create_coach_invite(coach_id, athlete_id)
        assert reopened["id"] == first["id"]
        assert reopened["status"] == "invited"
        assert reopened["removed_at"] is None

    def test_create_coach_invite_leaves_an_active_link_untouched(self):
        coach_id = _create_user("helper-coach4@uphill.ai")
        athlete_id = _create_user("helper-athlete4@uphill.ai")
        first = create_coach_invite(coach_id, athlete_id)
        accept_coach_invite(first["id"], athlete_id)
        unchanged = create_coach_invite(coach_id, athlete_id)
        assert unchanged["id"] == first["id"]
        assert unchanged["status"] == "active"

    def test_accept_coach_invite_activates_a_pending_invite(self):
        coach_id = _create_user("helper-coach5@uphill.ai")
        athlete_id = _create_user("helper-athlete5@uphill.ai")
        link = create_coach_invite(coach_id, athlete_id)
        accepted = accept_coach_invite(link["id"], athlete_id)
        assert accepted["status"] == "active"
        assert accepted["responded_at"] is not None

    def test_accept_coach_invite_returns_none_for_wrong_athlete(self):
        coach_id = _create_user("helper-coach6@uphill.ai")
        athlete_id = _create_user("helper-athlete6@uphill.ai")
        someone_else_id = _create_user("helper-someone-else@uphill.ai")
        link = create_coach_invite(coach_id, athlete_id)
        assert accept_coach_invite(link["id"], someone_else_id) is None

    def test_accept_coach_invite_returns_none_when_already_accepted(self):
        coach_id = _create_user("helper-coach7@uphill.ai")
        athlete_id = _create_user("helper-athlete7@uphill.ai")
        link = create_coach_invite(coach_id, athlete_id)
        accept_coach_invite(link["id"], athlete_id)
        assert accept_coach_invite(link["id"], athlete_id) is None

    def test_get_active_coach_link_for_athlete_finds_only_active_status(self):
        coach_id = _create_user("helper-coach8@uphill.ai")
        athlete_id = _create_user("helper-athlete8@uphill.ai")
        assert get_active_coach_link_for_athlete(athlete_id) is None
        link = create_coach_invite(coach_id, athlete_id)
        assert get_active_coach_link_for_athlete(athlete_id) is None  # still 'invited'
        accept_coach_invite(link["id"], athlete_id)
        active = get_active_coach_link_for_athlete(athlete_id)
        assert active["id"] == link["id"]

    def test_get_coach_athlete_link_and_by_id(self):
        coach_id = _create_user("helper-coach9@uphill.ai")
        athlete_id = _create_user("helper-athlete9@uphill.ai")
        link = create_coach_invite(coach_id, athlete_id)
        assert get_coach_athlete_link(coach_id, athlete_id)["id"] == link["id"]
        assert get_coach_athlete_by_id(link["id"])["id"] == link["id"]
        assert get_coach_athlete_by_id(999999) is None

    def test_get_roster_for_coach_excludes_removed_and_other_coaches(self):
        coach_id = _create_user("helper-coach10@uphill.ai")
        other_coach_id = _create_user("helper-other-coach10@uphill.ai")
        active_athlete = _create_user("helper-athlete10a@uphill.ai")
        pending_athlete = _create_user("helper-athlete10b@uphill.ai")
        removed_athlete = _create_user("helper-athlete10c@uphill.ai")
        others_athlete = _create_user("helper-athlete10d@uphill.ai")

        active_link = create_coach_invite(coach_id, active_athlete)
        accept_coach_invite(active_link["id"], active_athlete)
        create_coach_invite(coach_id, pending_athlete)
        removed_link = create_coach_invite(coach_id, removed_athlete)
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE coach_athletes SET status = 'removed' WHERE id = :id"), {"id": removed_link["id"]}
            )
            conn.commit()
        create_coach_invite(other_coach_id, others_athlete)

        roster = get_roster_for_coach(coach_id)
        athlete_ids = {r["athlete_id"] for r in roster}
        assert athlete_ids == {active_athlete, pending_athlete}
        statuses = {r["athlete_id"]: r["status"] for r in roster}
        assert statuses[active_athlete] == "active"
        assert statuses[pending_athlete] == "invited"
        assert all("athlete_email" in r and "athlete_name" in r for r in roster)
