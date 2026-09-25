from services.race_history import build_summary, prompt_summary


def _manual(client, headers, name="Mountain 50k"):
    response = client.post(
        "/api/race-history/results",
        headers=headers,
        json={
            "discipline": "trail",
            "race_name": name,
            "race_date": "2025-09-20",
            "distance_km": 50,
            "elevation_gain_m": 1500,
            "finish_time_sec": 22000,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_manual_result_is_owner_scoped_and_hidden_only_from_prompt(client, auth_headers):
    headers, user_id = auth_headers["headers"], auth_headers["user_id"]
    result = _manual(client, headers)
    hidden = client.patch(f"/api/race-history/results/{result['id']}", headers=headers, json={"hidden": True})
    assert hidden.status_code == 200
    assert build_summary(user_id)["longest_finish"]["id"] == result["id"]
    assert prompt_summary(user_id) == ""
    estimate = client.post(
        "/api/coach/goal-estimate",
        headers=headers,
        json={
            "distance_km": 50,
            "elevation_gain_m": 1500,
            "reference_result_id": result["id"],
        },
    )
    assert estimate.status_code == 200, estimate.text

    other = client.post("/api/auth/mock-login", json={"email": "another-runner@uphill.ai"}).json()
    other_headers = {"Authorization": f"Bearer {other['session_token']}"}
    assert (
        client.patch(
            f"/api/race-history/results/{result['id']}", headers=other_headers, json={"hidden": False}
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/coach/goal-estimate",
            headers=other_headers,
            json={
                "distance_km": 50,
                "reference_result_id": result["id"],
            },
        ).status_code
        == 404
    )


def test_dnf_cannot_be_reference(client, auth_headers):
    response = client.post(
        "/api/race-history/results",
        headers=auth_headers["headers"],
        json={
            "discipline": "trail",
            "race_name": "DNF Race",
            "race_date": "2025-09-20",
            "distance_km": 50,
            "is_dnf": True,
        },
    )
    assert response.status_code == 200
    assert (
        client.post(
            "/api/coach/goal-estimate",
            headers=auth_headers["headers"],
            json={
                "distance_km": 50,
                "reference_result_id": response.json()["id"],
            },
        ).status_code
        == 404
    )


def test_vbm_selection_and_bib_evidence_survive_refresh(client, auth_headers, monkeypatch):
    from services import race_history

    parent = {
        "event": "FMM",
        "vbm_id": "SHARED RUNNER",
        "full_name": "SHARED RUNNER",
        "race_full_name": "TEST MARATHON 03/12/2023",
        "race_day": "2023-12-03",
        "mark": "03:39:14",
        "bib": "47107",
        "other_results_full": [
            {"race": "TEST MARATHON 03/12/2023", "time": "03:39:14", "bib": "47107"},
            {"race": "OTHER MARATHON 04/12/2022", "time": "03:42:00", "bib": "99999"},
        ],
    }
    monkeypatch.setattr(race_history, "_fetch", lambda *args, **kwargs: {"data": [parent]})
    headers = auth_headers["headers"]
    claim = client.post(
        "/api/race-history/claims", headers=headers, json={"source": "vbm", "external_id": "SHARED RUNNER"}
    ).json()
    assert race_history.sync_claim(claim["id"]) == 2
    results = client.get("/api/race-history", headers=headers).json()["results"]
    assert len(results) == 2 and all(not row["selected"] for row in results)
    selected = next(row for row in results if row["bib"] == "47107")
    assert (
        client.patch(
            f"/api/race-history/results/{selected['id']}", headers=headers, json={"selected": True}
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/race-history/claims/{claim['id']}/verify-bib", headers=headers, json={"bib": "47107"}
        ).status_code
        == 200
    )
    assert race_history.sync_claim(claim["id"]) == 2
    refreshed = client.get("/api/race-history", headers=headers).json()
    assert next(row for row in refreshed["results"] if row["id"] == selected["id"])["verified"]
    assert sum(row["selected"] for row in refreshed["results"]) == 1
