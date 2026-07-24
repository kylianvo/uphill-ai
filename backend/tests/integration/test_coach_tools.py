"""Integration tests for Phase 4: coach-facing goal/gear/pacing/nutrition
tool wrappers and the AI co-pilot chat. See
docs/superpowers/specs/2026-07-20-coach-role-design.md and
docs/superpowers/plans/2026-07-20-coach-role-phase4-coach-tools.md."""


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


_GOAL_ESTIMATE_PAYLOAD = {"distance_km": 50, "elevation_gain_m": 2000, "flat_pace_min_km": 5.5}


class TestCoachGoalEstimateEndpoint:
    def test_self_serve_goal_estimate_is_unaffected(self, client):
        """Regression guard for the _goal_estimate_core extraction."""
        resp = client.post("/api/coach/goal-estimate", json=_GOAL_ESTIMATE_PAYLOAD)
        assert resp.status_code == 200, resp.text
        assert "distance_km" in resp.json()

    def test_coach_can_get_a_goal_estimate_for_an_athlete(self, client):
        coach_headers, _ = _make_coach(client, "goalest-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "goalest-athlete1@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/goal-estimate", json=_GOAL_ESTIMATE_PAYLOAD, headers=coach_headers
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["distance_km"] == 50

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "goalest-coach2@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/goal-estimate",
            json=_GOAL_ESTIMATE_PAYLOAD,
            headers=coach_headers,
        )
        assert resp.status_code == 403

    def test_athlete_can_use_it_on_themself(self, client, auth_headers):
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/goal-estimate",
            json=_GOAL_ESTIMATE_PAYLOAD,
            headers=auth_headers["headers"],
        )
        assert resp.status_code == 200


_PACING_PAYLOAD = {
    "checkpoints": [
        {"name": "Start", "distance_meters": 0, "elevation_m": 100},
        {"name": "Finish", "distance_meters": 10000, "elevation_m": 100},
    ],
    "target_flat_pace_min_km": 6.0,
}


class TestCoachCalculatePacingEndpoint:
    def test_self_serve_calculate_pacing_is_unaffected(self, client):
        resp = client.post("/api/coach/calculate-pacing", json=_PACING_PAYLOAD)
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    def test_coach_can_calculate_pacing_for_an_athlete(self, client):
        coach_headers, _ = _make_coach(client, "pacing-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "pacing-athlete1@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/calculate-pacing", json=_PACING_PAYLOAD, headers=coach_headers
        )
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "pacing-coach2@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/calculate-pacing",
            json=_PACING_PAYLOAD,
            headers=coach_headers,
        )
        assert resp.status_code == 403


_FUELING_PAYLOAD = {"distance_km": 50, "target_time_hours": 8}


class TestCoachCalculateFuelingEndpoint:
    def test_self_serve_calculate_fueling_is_unaffected(self, client):
        resp = client.post("/api/coach/calculate-fueling", json=_FUELING_PAYLOAD)
        assert resp.status_code == 200, resp.text

    def test_coach_can_calculate_fueling_for_an_athlete(self, client):
        coach_headers, _ = _make_coach(client, "fueling-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "fueling-athlete1@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/calculate-fueling", json=_FUELING_PAYLOAD, headers=coach_headers
        )
        assert resp.status_code == 200, resp.text

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "fueling-coach2@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/calculate-fueling",
            json=_FUELING_PAYLOAD,
            headers=coach_headers,
        )
        assert resp.status_code == 403
