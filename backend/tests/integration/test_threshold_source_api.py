"""threshold_source on profile update and onboarding; GET /api/auth/fitness-snapshot.
Scratch DB only."""

PROFILE = {"age": 37, "max_hr": 183, "resting_hr": 60, "aet_hr": 150, "ant_hr": 165}


def _update(client, headers, **extra):
    return client.post("/api/auth/update-profile", json={**PROFILE, **extra}, headers=headers)


def test_profile_update_round_trips_threshold_source(client, auth_headers):
    assert _update(client, auth_headers["headers"], threshold_source="field").status_code == 200
    me = client.get("/api/auth/me", headers=auth_headers["headers"]).json()
    assert me["threshold_source"] == "field"


def test_profile_update_without_threshold_source_keeps_the_stored_value(client, auth_headers):
    _update(client, auth_headers["headers"], threshold_source="lab")
    assert _update(client, auth_headers["headers"]).status_code == 200
    assert client.get("/api/auth/me", headers=auth_headers["headers"]).json()["threshold_source"] == "lab"


def test_profile_update_rejects_unknown_threshold_source(client, auth_headers):
    assert _update(client, auth_headers["headers"], threshold_source="guess").status_code == 422


def test_new_users_report_unknown(client, auth_headers):
    assert client.get("/api/auth/me", headers=auth_headers["headers"]).json()["threshold_source"] == "unknown"


def test_onboarding_accepts_threshold_source(client, auth_headers, mock_plan_generation):
    resp = client.post(
        "/api/auth/onboarding",
        headers=auth_headers["headers"],
        json={
            "goal_type": "race",
            "race_name": "Synthetic 50K",
            "race_date": "2027-05-01",
            "days_per_week": 4,
            "plan_start_date": "2027-03-15",
            "aet_hr": 150,
            "ant_hr": 165,
            "threshold_source": "estimated",
        },
    )
    assert resp.status_code == 200, resp.text
    assert client.get("/api/auth/me", headers=auth_headers["headers"]).json()["threshold_source"] == "estimated"


def test_fitness_snapshot_endpoint_without_coros(client, auth_headers):
    _update(client, auth_headers["headers"], threshold_source="field")
    resp = client.get("/api/auth/fitness-snapshot", headers=auth_headers["headers"])
    assert resp.status_code == 200, resp.text
    snap = resp.json()
    assert snap["weekly_km_source"] == "self_reported"
    assert snap["threshold_source"] == "field"
    assert snap["tier"] is None


def test_fitness_snapshot_requires_auth(client):
    assert client.get("/api/auth/fitness-snapshot").status_code == 401
