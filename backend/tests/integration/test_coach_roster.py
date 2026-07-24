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


def _admin_headers(client):
    resp = client.post("/api/auth/mock-login", json={"email": "admin@uphill.ai"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def _make_coach(client, email="make-coach@uphill.ai"):
    """Logs in as `email` (creating the user via mock-login), then promotes
    it to coach status via the admin endpoint. Returns (headers, user_id)."""
    resp = client.post("/api/auth/mock-login", json={"email": email})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    user_id = data["user"]["id"]
    headers = {"Authorization": f"Bearer {data['session_token']}"}
    promote = client.post(
        f"/api/admin/users/{user_id}/coach-status", json={"is_coach": True}, headers=_admin_headers(client)
    )
    assert promote.status_code == 200, promote.text
    return headers, user_id


class TestCoachStatusEndpoint:
    def test_me_reports_is_coach_false_by_default(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers["headers"])
        assert resp.status_code == 200
        assert resp.json()["is_coach"] is False

    def test_admin_can_grant_coach_status(self, client):
        headers, user_id = _make_coach(client)
        resp = client.get("/api/auth/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["is_coach"] is True

    def test_admin_can_revoke_coach_status(self, client):
        headers, user_id = _make_coach(client)
        revoke = client.post(
            f"/api/admin/users/{user_id}/coach-status", json={"is_coach": False}, headers=_admin_headers(client)
        )
        assert revoke.status_code == 200
        assert revoke.json()["is_coach"] is False

    def test_non_admin_cannot_grant_coach_status(self, client, auth_headers):
        resp = client.post(
            f"/api/admin/users/{auth_headers['user_id']}/coach-status",
            json={"is_coach": True},
            headers=auth_headers["headers"],
        )
        assert resp.status_code == 403

    def test_coach_status_endpoint_404s_for_unknown_user(self, client):
        resp = client.post(
            "/api/admin/users/999999/coach-status", json={"is_coach": True}, headers=_admin_headers(client)
        )
        assert resp.status_code == 404


class TestInviteEndpoint:
    def test_coach_can_invite_an_existing_athlete(self, client):
        coach_headers, _ = _make_coach(client, "invite-coach1@uphill.ai")
        client.post("/api/auth/mock-login", json={"email": "invite-athlete1@uphill.ai"})
        resp = client.post(
            "/api/coaching/invite", json={"athlete_email": "invite-athlete1@uphill.ai"}, headers=coach_headers
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "invited"

    def test_non_coach_cannot_invite(self, client, auth_headers):
        client.post("/api/auth/mock-login", json={"email": "invite-athlete2@uphill.ai"})
        resp = client.post(
            "/api/coaching/invite",
            json={"athlete_email": "invite-athlete2@uphill.ai"},
            headers=auth_headers["headers"],
        )
        assert resp.status_code == 403

    def test_invite_404s_for_unregistered_email(self, client):
        coach_headers, _ = _make_coach(client, "invite-coach3@uphill.ai")
        resp = client.post(
            "/api/coaching/invite", json={"athlete_email": "nobody-registered@uphill.ai"}, headers=coach_headers
        )
        assert resp.status_code == 404

    def test_coach_cannot_invite_self(self, client):
        coach_headers, _ = _make_coach(client, "invite-coach4@uphill.ai")
        resp = client.post(
            "/api/coaching/invite", json={"athlete_email": "invite-coach4@uphill.ai"}, headers=coach_headers
        )
        assert resp.status_code == 400

    def test_invite_conflicts_when_athlete_has_a_different_active_coach(self, client):
        first_coach_headers, _ = _make_coach(client, "invite-coach5a@uphill.ai")
        second_coach_headers, _ = _make_coach(client, "invite-coach5b@uphill.ai")
        athlete_resp = client.post("/api/auth/mock-login", json={"email": "invite-athlete5@uphill.ai"})
        athlete_headers = {"Authorization": f"Bearer {athlete_resp.json()['session_token']}"}

        invite_resp = client.post(
            "/api/coaching/invite", json={"athlete_email": "invite-athlete5@uphill.ai"}, headers=first_coach_headers
        )
        invite_id = invite_resp.json()["id"]
        client.post(f"/api/coaching/invites/{invite_id}/accept", headers=athlete_headers)

        conflict = client.post(
            "/api/coaching/invite", json={"athlete_email": "invite-athlete5@uphill.ai"}, headers=second_coach_headers
        )
        assert conflict.status_code == 409


class TestAcceptEndpoint:
    def test_athlete_can_accept_their_invite(self, client):
        coach_headers, _ = _make_coach(client, "accept-coach1@uphill.ai")
        athlete_resp = client.post("/api/auth/mock-login", json={"email": "accept-athlete1@uphill.ai"})
        athlete_headers = {"Authorization": f"Bearer {athlete_resp.json()['session_token']}"}

        invite = client.post(
            "/api/coaching/invite", json={"athlete_email": "accept-athlete1@uphill.ai"}, headers=coach_headers
        ).json()
        resp = client.post(f"/api/coaching/invites/{invite['id']}/accept", headers=athlete_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "active"

    def test_accept_404s_for_someone_else_s_invite(self, client):
        coach_headers, _ = _make_coach(client, "accept-coach2@uphill.ai")
        client.post("/api/auth/mock-login", json={"email": "accept-athlete2@uphill.ai"})
        other_resp = client.post("/api/auth/mock-login", json={"email": "accept-someone-else2@uphill.ai"})
        other_headers = {"Authorization": f"Bearer {other_resp.json()['session_token']}"}

        invite = client.post(
            "/api/coaching/invite", json={"athlete_email": "accept-athlete2@uphill.ai"}, headers=coach_headers
        ).json()
        resp = client.post(f"/api/coaching/invites/{invite['id']}/accept", headers=other_headers)
        assert resp.status_code == 404

    def test_accept_404s_for_unknown_invite_id(self, client, auth_headers):
        resp = client.post("/api/coaching/invites/999999/accept", headers=auth_headers["headers"])
        assert resp.status_code == 404

    def test_accept_conflicts_when_athlete_already_has_a_different_active_coach(self, client):
        # Both invites are created while the athlete has no active coach yet
        # (so invite-creation's own conflict check doesn't block either one);
        # only accepting the second one, after the first is already active,
        # should hit accept_invite's conflict check.
        first_coach_headers, _ = _make_coach(client, "accept-coach3a@uphill.ai")
        second_coach_headers, _ = _make_coach(client, "accept-coach3b@uphill.ai")
        athlete_resp = client.post("/api/auth/mock-login", json={"email": "accept-athlete3@uphill.ai"})
        athlete_headers = {"Authorization": f"Bearer {athlete_resp.json()['session_token']}"}

        first_invite = client.post(
            "/api/coaching/invite", json={"athlete_email": "accept-athlete3@uphill.ai"}, headers=first_coach_headers
        ).json()
        second_invite = client.post(
            "/api/coaching/invite", json={"athlete_email": "accept-athlete3@uphill.ai"}, headers=second_coach_headers
        ).json()

        client.post(f"/api/coaching/invites/{first_invite['id']}/accept", headers=athlete_headers)
        resp = client.post(f"/api/coaching/invites/{second_invite['id']}/accept", headers=athlete_headers)
        assert resp.status_code == 409


class TestRosterEndpoint:
    def test_roster_starts_empty(self, client):
        coach_headers, _ = _make_coach(client, "roster-coach1@uphill.ai")
        resp = client.get("/api/coaching/roster", headers=coach_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_roster_includes_invited_and_active_athletes(self, client):
        coach_headers, _ = _make_coach(client, "roster-coach2@uphill.ai")
        athlete_resp = client.post("/api/auth/mock-login", json={"email": "roster-athlete2a@uphill.ai"})
        athlete_headers = {"Authorization": f"Bearer {athlete_resp.json()['session_token']}"}
        client.post("/api/auth/mock-login", json={"email": "roster-athlete2b@uphill.ai"})

        invite_a = client.post(
            "/api/coaching/invite", json={"athlete_email": "roster-athlete2a@uphill.ai"}, headers=coach_headers
        ).json()
        client.post(f"/api/coaching/invites/{invite_a['id']}/accept", headers=athlete_headers)
        client.post("/api/coaching/invite", json={"athlete_email": "roster-athlete2b@uphill.ai"}, headers=coach_headers)

        resp = client.get("/api/coaching/roster", headers=coach_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2
        statuses = {row["athlete_email"]: row["status"] for row in body}
        assert statuses["roster-athlete2a@uphill.ai"] == "active"
        assert statuses["roster-athlete2b@uphill.ai"] == "invited"

    def test_non_coach_cannot_read_a_roster(self, client, auth_headers):
        resp = client.get("/api/coaching/roster", headers=auth_headers["headers"])
        assert resp.status_code == 403

    def test_roster_is_scoped_to_the_requesting_coach(self, client):
        coach_a_headers, _ = _make_coach(client, "roster-coach3a@uphill.ai")
        coach_b_headers, _ = _make_coach(client, "roster-coach3b@uphill.ai")
        client.post("/api/auth/mock-login", json={"email": "roster-athlete3@uphill.ai"})
        client.post(
            "/api/coaching/invite", json={"athlete_email": "roster-athlete3@uphill.ai"}, headers=coach_a_headers
        )

        resp_a = client.get("/api/coaching/roster", headers=coach_a_headers)
        resp_b = client.get("/api/coaching/roster", headers=coach_b_headers)
        assert len(resp_a.json()) == 1
        assert resp_b.json() == []


def _link_coach_and_athlete(client, coach_headers, athlete_email):
    """Logs in as `athlete_email` (creating the user), sends + accepts an
    invite from the already-promoted coach behind `coach_headers`. Returns
    (athlete_headers, athlete_id)."""
    athlete_resp = client.post("/api/auth/mock-login", json={"email": athlete_email})
    athlete_headers = {"Authorization": f"Bearer {athlete_resp.json()['session_token']}"}
    athlete_id = athlete_resp.json()["user"]["id"]
    invite = client.post("/api/coaching/invite", json={"athlete_email": athlete_email}, headers=coach_headers).json()
    client.post(f"/api/coaching/invites/{invite['id']}/accept", headers=athlete_headers)
    return athlete_headers, athlete_id


class TestAthleteActivePlanEndpoint:
    def test_athlete_can_view_their_own_active_plan(self, client, auth_headers):
        resp = client.get(
            f"/api/coaching/athletes/{auth_headers['user_id']}/active-plan", headers=auth_headers["headers"]
        )
        assert resp.status_code == 200
        assert resp.json() == {"active": False}

    def test_admin_can_view_any_athletes_active_plan(self, client, auth_headers):
        admin_headers = _admin_headers(client)
        resp = client.get(f"/api/coaching/athletes/{auth_headers['user_id']}/active-plan", headers=admin_headers)
        assert resp.status_code == 200

    def test_coach_with_active_link_can_view_athletes_active_plan(self, client):
        coach_headers, _ = _make_coach(client, "access-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "access-athlete1@uphill.ai")
        resp = client.get(f"/api/coaching/athletes/{athlete_id}/active-plan", headers=coach_headers)
        assert resp.status_code == 200
        assert resp.json() == {"active": False}

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "access-coach2@uphill.ai")
        resp = client.get(f"/api/coaching/athletes/{auth_headers['user_id']}/active-plan", headers=coach_headers)
        assert resp.status_code == 403

    def test_coach_with_only_a_pending_invite_is_forbidden(self, client):
        coach_headers, _ = _make_coach(client, "access-coach3@uphill.ai")
        athlete_resp = client.post("/api/auth/mock-login", json={"email": "access-athlete3@uphill.ai"})
        athlete_id = athlete_resp.json()["user"]["id"]
        client.post("/api/coaching/invite", json={"athlete_email": "access-athlete3@uphill.ai"}, headers=coach_headers)
        resp = client.get(f"/api/coaching/athletes/{athlete_id}/active-plan", headers=coach_headers)
        assert resp.status_code == 403

    def test_a_random_authenticated_user_is_forbidden(self, client, auth_headers):
        stranger_resp = client.post("/api/auth/mock-login", json={"email": "access-stranger1@uphill.ai"})
        stranger_headers = {"Authorization": f"Bearer {stranger_resp.json()['session_token']}"}
        resp = client.get(f"/api/coaching/athletes/{auth_headers['user_id']}/active-plan", headers=stranger_headers)
        assert resp.status_code == 403

    def test_coach_sees_the_athletes_actual_active_plan_and_workouts(self, client, mock_plan_generation):
        coach_headers, _ = _make_coach(client, "access-coach4@uphill.ai")
        athlete_headers, athlete_id = _link_coach_and_athlete(client, coach_headers, "access-athlete4@uphill.ai")
        gen = client.post(
            "/api/coach/generate-plan",
            json={
                "goal_type": "finish",
                "race_name": "Test 50K",
                "race_date": "2027-05-01",
                "plan_start_date": "2027-03-15",
                "days_per_week": 4,
            },
            headers=athlete_headers,
        )
        assert gen.status_code == 200, gen.text

        resp = client.get(f"/api/coaching/athletes/{athlete_id}/active-plan", headers=coach_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["active"] is True
        assert body["plan"]["race_name"] == "Test 50K"
        assert isinstance(body["workouts"], list)


class TestAthleteRecentPlansEndpoint:
    def test_coach_can_view_athletes_recent_plans(self, client, mock_plan_generation):
        coach_headers, _ = _make_coach(client, "recent-coach1@uphill.ai")
        athlete_headers, athlete_id = _link_coach_and_athlete(client, coach_headers, "recent-athlete1@uphill.ai")
        client.post(
            "/api/coach/generate-plan",
            json={
                "goal_type": "finish",
                "race_name": "Recent 50K",
                "race_date": "2027-05-01",
                "plan_start_date": "2027-03-15",
                "days_per_week": 4,
            },
            headers=athlete_headers,
        )
        resp = client.get(f"/api/coaching/athletes/{athlete_id}/recent-plans", headers=coach_headers)
        assert resp.status_code == 200
        assert len(resp.json()["plans"]) == 1
        assert resp.json()["plans"][0]["race_name"] == "Recent 50K"

    def test_coach_without_a_link_is_forbidden_from_recent_plans(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "recent-coach2@uphill.ai")
        resp = client.get(f"/api/coaching/athletes/{auth_headers['user_id']}/recent-plans", headers=coach_headers)
        assert resp.status_code == 403
