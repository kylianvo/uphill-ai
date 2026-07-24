"""Integration tests for Phase 5: coach_notes create/list endpoints. See
docs/superpowers/specs/2026-07-20-coach-role-design.md and
docs/superpowers/plans/2026-07-20-coach-role-phase5-dashboard.md."""


def _admin_headers(client):
    resp = client.post("/api/auth/mock-login", json={"email": "admin@uphill.ai"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def _make_coach(client, email="make-coach@uphill.ai"):
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


def _link_coach_and_athlete(client, coach_headers, athlete_email):
    athlete_resp = client.post("/api/auth/mock-login", json={"email": athlete_email})
    athlete_headers = {"Authorization": f"Bearer {athlete_resp.json()['session_token']}"}
    athlete_id = athlete_resp.json()["user"]["id"]
    invite = client.post("/api/coaching/invite", json={"athlete_email": athlete_email}, headers=coach_headers).json()
    client.post(f"/api/coaching/invites/{invite['id']}/accept", headers=athlete_headers)
    return athlete_headers, athlete_id


class TestCoachNotesEndpoints:
    def test_coach_can_create_a_general_note(self, client):
        coach_headers, coach_id = _make_coach(client, "notes-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "notes-athlete1@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/notes",
            json={"target_type": "general", "note": "Strong week, keep an eye on sleep."},
            headers=coach_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["coach_id"] == coach_id
        assert body["athlete_id"] == athlete_id
        assert body["target_type"] == "general"
        assert body["target_id"] is None
        assert body["note"] == "Strong week, keep an eye on sleep."

    def test_coach_can_create_a_workout_targeted_note(self, client):
        coach_headers, _ = _make_coach(client, "notes-coach2@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "notes-athlete2@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/notes",
            json={"target_type": "workout", "target_id": 42, "note": "Skip the hill repeats if calf is tight."},
            headers=coach_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["target_id"] == 42

    def test_invalid_target_type_is_rejected(self, client):
        coach_headers, _ = _make_coach(client, "notes-coach3@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "notes-athlete3@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/notes",
            json={"target_type": "bogus", "note": "x"},
            headers=coach_headers,
        )
        assert resp.status_code == 422

    def test_athlete_can_read_notes_about_themself(self, client):
        coach_headers, _ = _make_coach(client, "notes-coach4@uphill.ai")
        athlete_headers, athlete_id = _link_coach_and_athlete(client, coach_headers, "notes-athlete4@uphill.ai")
        client.post(
            f"/api/coaching/athletes/{athlete_id}/notes",
            json={"target_type": "general", "note": "Visible to both."},
            headers=coach_headers,
        )
        resp = client.get(f"/api/coaching/athletes/{athlete_id}/notes", headers=athlete_headers)
        assert resp.status_code == 200
        assert len(resp.json()["notes"]) == 1
        assert resp.json()["notes"][0]["note"] == "Visible to both."

    def test_notes_can_be_filtered_by_target(self, client):
        coach_headers, _ = _make_coach(client, "notes-coach5@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "notes-athlete5@uphill.ai")
        client.post(
            f"/api/coaching/athletes/{athlete_id}/notes",
            json={"target_type": "general", "note": "General note."},
            headers=coach_headers,
        )
        client.post(
            f"/api/coaching/athletes/{athlete_id}/notes",
            json={"target_type": "workout", "target_id": 7, "note": "Workout note."},
            headers=coach_headers,
        )
        resp = client.get(
            f"/api/coaching/athletes/{athlete_id}/notes?target_type=workout&target_id=7", headers=coach_headers
        )
        assert resp.status_code == 200
        notes = resp.json()["notes"]
        assert len(notes) == 1
        assert notes[0]["note"] == "Workout note."

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "notes-coach6@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/notes",
            json={"target_type": "general", "note": "x"},
            headers=coach_headers,
        )
        assert resp.status_code == 403
