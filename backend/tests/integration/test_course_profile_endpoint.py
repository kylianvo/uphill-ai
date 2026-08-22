"""Tests for POST /api/kb/race-courses/course-profile -- the admin endpoint
that attaches a curated GPX-derived checkpoint list to a race_courses KB
entry, for a specific edition year and optional route variant. Uses the
real test DB (save_kb_chunks / engine), following test_kb_endpoints.py's
pattern, since this endpoint writes to the KB."""

from sqlalchemy import text

from db import engine, get_kb_chunks, save_kb_chunks


def _admin_headers(client):
    client.post("/api/auth/mock-login", json={"email": "profile-admin@uphill.ai"})
    with engine.connect() as conn:
        conn.execute(text("UPDATE users SET role = 'admin' WHERE email = 'profile-admin@uphill.ai'"))
        conn.commit()
    resp = client.post("/api/auth/mock-login", json={"email": "profile-admin@uphill.ai"})
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def _seed_race(title="Sapa Jungle Ultra"):
    save_kb_chunks(
        [
            {
                "domain": "race_courses",
                "kind": "race_profile",
                "title": title,
                "content": "A jungle ultra...",
                "payload": {
                    "race_name": title,
                    "aliases": [],
                    "distances": [{"label": "50km", "distance_km": 50.0, "elevation_gain_m": 2000}],
                    "matching_hints": {"name_keywords": [title.lower()]},
                },
            }
        ]
    )


_CHECKPOINTS = [
    {
        "name": "Start",
        "distance_meters": 0,
        "elevation_meters": 1500.0,
        "segment_gain_meters": 0.0,
        "segment_loss_meters": 0.0,
    },
    {
        "name": "KM 48.0",
        "distance_meters": 48000.0,
        "elevation_meters": 2000.0,
        "segment_gain_meters": 500.0,
        "segment_loss_meters": 0.0,
    },
]


def test_requires_admin(client, auth_headers):
    _seed_race()
    resp = client.post(
        "/api/kb/race-courses/course-profile",
        json={"race_name": "Sapa Jungle Ultra", "distance_label": "50km", "checkpoints": _CHECKPOINTS, "year": 2026},
        headers=auth_headers["headers"],
    )
    assert resp.status_code == 403


def test_unknown_race_returns_404(client):
    headers = _admin_headers(client)
    resp = client.post(
        "/api/kb/race-courses/course-profile",
        json={
            "race_name": "Totally Unknown Race",
            "distance_label": "50km",
            "checkpoints": _CHECKPOINTS,
            "year": 2026,
        },
        headers=headers,
    )
    assert resp.status_code == 404


def test_unknown_distance_label_returns_422(client):
    _seed_race("Distance Mismatch Ultra")
    headers = _admin_headers(client)
    resp = client.post(
        "/api/kb/race-courses/course-profile",
        json={
            "race_name": "Distance Mismatch Ultra",
            "distance_label": "100km",
            "checkpoints": _CHECKPOINTS,
            "year": 2026,
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_empty_checkpoints_returns_422(client):
    _seed_race("Empty Checkpoints Ultra")
    headers = _admin_headers(client)
    resp = client.post(
        "/api/kb/race-courses/course-profile",
        json={"race_name": "Empty Checkpoints Ultra", "distance_label": "50km", "checkpoints": [], "year": 2026},
        headers=headers,
    )
    assert resp.status_code == 422


def test_valid_request_saves_profile(client, monkeypatch, tmp_path):
    from services import kb_distiller

    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    _seed_race("Saved Profile Ultra")
    headers = _admin_headers(client)
    resp = client.post(
        "/api/kb/race-courses/course-profile",
        json={
            "race_name": "Saved Profile Ultra",
            "distance_label": "50km",
            "checkpoints": _CHECKPOINTS,
            "year": 2026,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body == {"race_name": "Saved Profile Ultra", "distance_label": "50km", "year": 2026, "checkpoint_count": 2}

    chunk = next(c for c in get_kb_chunks("race_courses", kind="race_profile") if c["title"] == "Saved Profile Ultra")
    saved_profile = chunk["payload"]["course_profiles"]["50km"]["2026"]
    assert saved_profile["checkpoints"] == _CHECKPOINTS
    assert saved_profile["source"] == "gpx_upload"
    assert saved_profile["variant"] is None


def test_variant_tag_is_saved(client, monkeypatch, tmp_path):
    from services import kb_distiller

    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    _seed_race("Variant Ultra")
    headers = _admin_headers(client)
    resp = client.post(
        "/api/kb/race-courses/course-profile",
        json={
            "race_name": "Variant Ultra",
            "distance_label": "50km",
            "checkpoints": _CHECKPOINTS,
            "year": 2026,
            "variant": "langbiang-reversed",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    chunk = next(c for c in get_kb_chunks("race_courses", kind="race_profile") if c["title"] == "Variant Ultra")
    assert chunk["payload"]["course_profiles"]["50km"]["2026"]["variant"] == "langbiang-reversed"


def test_reupload_same_year_overwrites_only_that_year(client, monkeypatch, tmp_path):
    from services import kb_distiller

    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    _seed_race("Reupload Ultra")
    headers = _admin_headers(client)
    client.post(
        "/api/kb/race-courses/course-profile",
        json={"race_name": "Reupload Ultra", "distance_label": "50km", "checkpoints": _CHECKPOINTS, "year": 2026},
        headers=headers,
    )
    new_checkpoints = [
        {
            "name": "Start",
            "distance_meters": 0,
            "elevation_meters": 1600.0,
            "segment_gain_meters": 0.0,
            "segment_loss_meters": 0.0,
        },
        {
            "name": "Finish",
            "distance_meters": 49000.0,
            "elevation_meters": 2100.0,
            "segment_gain_meters": 500.0,
            "segment_loss_meters": 0.0,
        },
    ]
    resp = client.post(
        "/api/kb/race-courses/course-profile",
        json={
            "race_name": "Reupload Ultra",
            "distance_label": "50km",
            "checkpoints": new_checkpoints,
            "year": 2026,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    chunk = next(c for c in get_kb_chunks("race_courses", kind="race_profile") if c["title"] == "Reupload Ultra")
    assert chunk["payload"]["course_profiles"]["50km"]["2026"]["checkpoints"] == new_checkpoints


def test_different_year_adds_alongside_existing_years(client, monkeypatch, tmp_path):
    from services import kb_distiller

    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    _seed_race("Multi Year Ultra")
    headers = _admin_headers(client)
    client.post(
        "/api/kb/race-courses/course-profile",
        json={
            "race_name": "Multi Year Ultra",
            "distance_label": "50km",
            "checkpoints": _CHECKPOINTS,
            "year": 2025,
            "variant": "standard",
        },
        headers=headers,
    )
    new_checkpoints = [
        {
            "name": "Start",
            "distance_meters": 0,
            "elevation_meters": 1600.0,
            "segment_gain_meters": 0.0,
            "segment_loss_meters": 0.0,
        },
        {
            "name": "Finish",
            "distance_meters": 49000.0,
            "elevation_meters": 2100.0,
            "segment_gain_meters": 500.0,
            "segment_loss_meters": 0.0,
        },
    ]
    resp = client.post(
        "/api/kb/race-courses/course-profile",
        json={
            "race_name": "Multi Year Ultra",
            "distance_label": "50km",
            "checkpoints": new_checkpoints,
            "year": 2026,
            "variant": "langbiang-reversed",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    chunk = next(c for c in get_kb_chunks("race_courses", kind="race_profile") if c["title"] == "Multi Year Ultra")
    profiles = chunk["payload"]["course_profiles"]["50km"]
    assert profiles["2025"]["checkpoints"] == _CHECKPOINTS
    assert profiles["2025"]["variant"] == "standard"
    assert profiles["2026"]["checkpoints"] == new_checkpoints
    assert profiles["2026"]["variant"] == "langbiang-reversed"


def test_mismatched_distance_returns_422(client):
    _seed_race("Wrong Distance GPX Ultra")  # seeds a "50km" distance entry at distance_km=50.0
    headers = _admin_headers(client)
    # checkpoints totaling ~100km posted against the race's curated "50km" label
    wrong_distance_checkpoints = [
        {
            "name": "Start",
            "distance_meters": 0,
            "elevation_meters": 1500.0,
            "segment_gain_meters": 0.0,
            "segment_loss_meters": 0.0,
        },
        {
            "name": "Finish",
            "distance_meters": 100000.0,
            "elevation_meters": 2000.0,
            "segment_gain_meters": 500.0,
            "segment_loss_meters": 0.0,
        },
    ]
    resp = client.post(
        "/api/kb/race-courses/course-profile",
        json={
            "race_name": "Wrong Distance GPX Ultra",
            "distance_label": "50km",
            "checkpoints": wrong_distance_checkpoints,
            "year": 2026,
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_close_enough_distance_is_accepted(client, monkeypatch, tmp_path):
    from services import kb_distiller

    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    _seed_race("Close Enough Distance Ultra")  # "50km" distance entry at distance_km=50.0
    headers = _admin_headers(client)
    # within 15% tolerance -- 52km checkpoints against a 50km label should pass
    close_checkpoints = [
        {
            "name": "Start",
            "distance_meters": 0,
            "elevation_meters": 1500.0,
            "segment_gain_meters": 0.0,
            "segment_loss_meters": 0.0,
        },
        {
            "name": "Finish",
            "distance_meters": 52000.0,
            "elevation_meters": 2000.0,
            "segment_gain_meters": 500.0,
            "segment_loss_meters": 0.0,
        },
    ]
    resp = client.post(
        "/api/kb/race-courses/course-profile",
        json={
            "race_name": "Close Enough Distance Ultra",
            "distance_label": "50km",
            "checkpoints": close_checkpoints,
            "year": 2026,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
