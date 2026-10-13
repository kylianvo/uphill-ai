import db


def manual(client, headers):
    response = client.post(
        "/api/race-history/results",
        headers=headers,
        json={
            "discipline": "road",
            "race_name": "City Marathon",
            "race_date": "2023-12-03",
            "distance_km": 42.195,
            "finish_time_sec": 13154,
            "rank_overall": 30,
            "total_overall": 100,
            "user_note": "My note",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_detail_is_owner_scoped_and_survives_missing_or_failed_kb(client, auth_headers, monkeypatch):
    h = auth_headers["headers"]
    row = manual(client, h)
    endpoint = f"/api/race-history/results/{row['id']}/detail"
    monkeypatch.setattr(db, "get_kb_chunks", lambda *args, **kwargs: [])
    response = client.get(endpoint, headers=h)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["result"]["id"] == row["id"] and body["performance"]["overall_top_pct"] == 30.0
    assert body["performance"]["road_pb_key"] == "fm" and body["course_context"]["status"] == "missing"
    assert "raw" not in body["result"] and "user_id" not in body["result"]
    other = client.post("/api/auth/mock-login", json={"email": "review-other@uphill.ai"}).json()
    oh = {"Authorization": f"Bearer {other['session_token']}"}
    assert client.get(endpoint, headers=oh).status_code == 404

    def fail(*args, **kwargs):
        raise RuntimeError("KB offline")

    monkeypatch.setattr(db, "get_kb_chunks", fail)
    body = client.get(endpoint, headers=h).json()
    assert body["course_context"]["status"] == "unavailable" and body["result"]["id"] == row["id"]
    assert client.get(endpoint, headers=oh).status_code == 404


def test_coach_detail_requires_an_active_link(client, auth_headers):
    h = auth_headers["headers"]
    row = manual(client, h)
    uid = auth_headers["user_id"]
    coach = client.post("/api/auth/mock-login", json={"email": "review-coach@uphill.ai"}).json()
    ch = {"Authorization": f"Bearer {coach['session_token']}"}
    cid = db.get_user_by_email("review-coach@uphill.ai")["id"]
    db.set_user_is_coach(cid, True)
    endpoint = f"/api/coaching/athletes/{uid}/race-history/results/{row['id']}/detail"
    assert client.get(endpoint, headers=ch).status_code in (403, 404)
    link = db.create_coach_invite(cid, uid)
    db.accept_coach_invite(link["id"], uid)
    response = client.get(endpoint, headers=ch)
    assert response.status_code == 200, response.text
    foreign = client.post("/api/auth/mock-login", json={"email": "unlinked-coach@uphill.ai"}).json()
    assert client.get(endpoint, headers={"Authorization": f"Bearer {foreign['session_token']}"}).status_code in (
        403,
        404,
    )


def test_detail_validates_course_choice_and_keeps_recorded_fields(client, auth_headers, monkeypatch):
    h = auth_headers["headers"]
    row = manual(client, h)
    chunk = {
        "id": 10,
        "title": "City Marathon",
        "source_label": "Organizer",
        "payload": {
            "race_name": "City Marathon",
            "race_type": "road",
            "edition_year": 2026,
            "distances": [{"label": "Marathon", "distance_km": 42.195, "elevation_gain_m": 35}],
            "source_urls": ["javascript:alert(1)", "https://example.org/course"],
            "results": [{"year": 2026, "distance_label": "Marathon", "distance_km": 42.195, "winner_time": "2:10:00"}],
        },
    }
    monkeypatch.setattr(db, "get_kb_chunks", lambda *args, **kwargs: [chunk])
    endpoint = f"/api/race-history/results/{row['id']}/detail"
    response = client.get(endpoint, headers=h)
    assert response.status_code == 200
    detail = response.json()
    assert detail["course_context"]["course"]["edition_status"] == "different"
    assert detail["course_context"]["course"]["source_urls"] == ["https://example.org/course"]
    assert detail["historical_field"] is None
    assert detail["result"]["elevation_gain_m"] is None
    assert client.get(endpoint + "?course_id=999", headers=h).status_code == 422
    assert client.get(endpoint + "?course_id=10", headers=h).status_code == 200
    client.patch(f"/api/race-history/results/{row['id']}", headers=h, json={"hidden": True})
    hidden = client.get(endpoint, headers=h).json()
    assert hidden["performance"]["road_pb_key"] == "fm" and hidden["result"]["user_note"] == "My note"
