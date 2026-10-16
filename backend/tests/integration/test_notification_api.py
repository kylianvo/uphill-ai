from uuid import uuid4


def test_preferences_validate_and_ignore_identity(client, auth_headers):
    path = "/api/notifications/preferences"
    headers = auth_headers["headers"]
    assert client.patch(path, headers=headers, json={"timezone": "Bad/Zone"}).status_code == 422
    assert client.patch(path, headers=headers, json={"user_id": 99}).status_code == 422
    assert client.patch(path, headers=headers, json={"quiet_start": "07:00"}).status_code == 422
    r = client.patch(path, headers=headers, json={"timezone": "Australia/Sydney", "workouts_enabled": True})
    assert r.status_code == 200
    assert r.json()["workouts_enabled"] is True


def test_registration_and_open_are_owned(client, auth_headers):
    path = "/api/notifications/installations/" + str(uuid4())
    body = {"token": "ab" * 32, "environment": "sandbox", "permission": "authorized"}
    assert client.put(path, json=body).status_code == 401
    assert client.put(path, json=body, headers=auth_headers["headers"]).status_code == 200
    assert (
        client.post("/api/notifications/" + str(uuid4()) + "/opened", headers=auth_headers["headers"]).status_code
        == 404
    )
