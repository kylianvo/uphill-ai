import json

from sqlalchemy import text

from db import engine, save_kb_chunks


def _admin_headers(client):
    """mock-login, promote to admin in the DB, then re-login so the session/user
    reflects the admin role regardless of whether role is read from DB or token."""
    client.post("/api/auth/mock-login", json={"email": "kb-admin@uphill.ai"})
    with engine.connect() as conn:
        conn.execute(text("UPDATE users SET role = 'admin' WHERE email = 'kb-admin@uphill.ai'"))
        conn.commit()
    resp = client.post("/api/auth/mock-login", json={"email": "kb-admin@uphill.ai"})
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def test_kb_distill_requires_admin(client, auth_headers):
    resp = client.post("/api/kb/distill", headers=auth_headers["headers"])
    assert resp.status_code == 403


def test_kb_import_requires_admin(client, auth_headers):
    resp = client.post("/api/kb/import", headers=auth_headers["headers"])
    assert resp.status_code == 403


def test_kb_distill_rejects_unknown_domain(client):
    headers = _admin_headers(client)
    resp = client.post("/api/kb/distill?domain=bogus", headers=headers)
    assert resp.status_code == 400


def test_kb_status_reports_counts(client, auth_headers):
    save_kb_chunks([{"domain": "gear", "kind": "catalog_item", "title": "X", "content": "c", "payload": {"a": 1}}])
    resp = client.get("/api/kb/distill/status", headers=auth_headers["headers"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["counts"]["gear"] == 1
    assert body["counts"]["nutrition"] == 0


def test_kb_import_loads_seed(client, tmp_path, monkeypatch):
    from services import kb_distiller

    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    (tmp_path / "gear.json").write_text(
        json.dumps(
            {
                "domain": "gear",
                "chunks": [
                    {
                        "domain": "gear",
                        "kind": "catalog_item",
                        "title": "Speedgoat 7",
                        "content": "c",
                        "payload": {"brand": "Hoka"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    headers = _admin_headers(client)
    resp = client.post("/api/kb/import?domain=gear", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["loaded"]["gear"] == 1


def test_kb_import_empty_seed_returns_400_not_500(client, tmp_path, monkeypatch):
    from services import kb_distiller

    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    (tmp_path / "gear.json").write_text(json.dumps({"domain": "gear", "chunks": []}), encoding="utf-8")
    headers = _admin_headers(client)
    resp = client.post("/api/kb/import?domain=gear", headers=headers)
    assert resp.status_code == 400
    assert "gear" in resp.json()["detail"]


def test_kb_import_all_returns_partial_when_some_seeds_missing(client, tmp_path, monkeypatch):
    from services import kb_distiller

    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    (tmp_path / "gear.json").write_text(
        json.dumps(
            {
                "domain": "gear",
                "chunks": [
                    {
                        "domain": "gear",
                        "kind": "catalog_item",
                        "title": "X",
                        "content": "c",
                        "payload": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    headers = _admin_headers(client)
    resp = client.post("/api/kb/import?domain=all", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "partial"
    assert body["loaded"]["gear"] == 1
    assert "nutrition" in body["errors"] and "scheduler" in body["errors"]


def test_kb_import_loads_race_courses_seed(client, tmp_path, monkeypatch):
    from services import kb_distiller

    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    (tmp_path / "race_courses.json").write_text(
        json.dumps(
            {
                "domain": "race_courses",
                "chunks": [
                    {
                        "domain": "race_courses",
                        "kind": "race_profile",
                        "title": "Test Race",
                        "content": "c",
                        "payload": {"race_name": "Test Race", "aliases": [], "distances": []},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    headers = _admin_headers(client)
    resp = client.post("/api/kb/import?domain=race_courses", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["loaded"]["race_courses"] == 1


def test_kb_distill_rejects_hand_curated_domain(client):
    headers = _admin_headers(client)
    resp = client.post("/api/kb/distill?domain=race_courses", headers=headers)
    assert resp.status_code == 400


def test_match_race_endpoint_no_auth_required(client):
    save_kb_chunks(
        [
            {
                "domain": "race_courses",
                "kind": "race_profile",
                "title": "VMM",
                "content": "Course prose here.",
                "payload": {
                    "race_name": "Vietnam Mountain Marathon",
                    "aliases": ["VMM"],
                    "terrain": ["rice terraces"],
                    "distances": [{"label": "50km", "distance_km": 46.7, "elevation_gain_m": 2800}],
                    "matching_hints": {"name_keywords": ["vmm"], "distance_km_options": [46.7]},
                },
            }
        ]
    )
    resp = client.get("/api/kb/match-race?name=VMM&distance_km=48")
    assert resp.status_code == 200
    body = resp.json()
    assert body["matched"] is True
    assert body["auto_apply"] is True
    assert body["match"]["race_name"] == "Vietnam Mountain Marathon"
    assert body["match"]["elevation_gain_m"] == 2800
    assert "candidates" not in body


def test_match_race_endpoint_returns_unmatched_for_unknown_name(client):
    resp = client.get("/api/kb/match-race?name=Totally Unknown Race XYZ")
    assert resp.status_code == 200
    assert resp.json() == {"matched": False}


def test_match_race_endpoint_returns_candidates_for_ambiguous_name(client):
    save_kb_chunks(
        [
            {
                "domain": "race_courses",
                "kind": "race_profile",
                "title": "Marathon du Mont-Blanc",
                "content": "prose",
                "payload": {
                    "race_name": "Marathon du Mont-Blanc",
                    "aliases": ["marathon du mont blanc"],
                    "terrain": ["alpine trail"],
                    "distances": [{"label": "42km", "distance_km": 42.0, "elevation_gain_m": 2500}],
                    "matching_hints": {"name_keywords": [], "distance_km_options": [42.0]},
                },
            },
            {
                "domain": "race_courses",
                "kind": "race_profile",
                "title": "Cross du Mont-Blanc",
                "content": "prose",
                "payload": {
                    "race_name": "Cross du Mont-Blanc",
                    "aliases": [],
                    "terrain": ["alpine trail"],
                    "distances": [{"label": "23km", "distance_km": 23.0, "elevation_gain_m": 1400}],
                    "matching_hints": {"name_keywords": ["marathon du mont blanc"], "distance_km_options": [23.0]},
                },
            },
        ]
    )
    resp = client.get("/api/kb/match-race?name=Marathon du Mont Blanc")
    assert resp.status_code == 200
    body = resp.json()
    assert body["matched"] is True
    assert body["auto_apply"] is False
    names = {c["race_name"] for c in body["candidates"]}
    assert names == {"Marathon du Mont-Blanc", "Cross du Mont-Blanc"}
    assert all("score" in c for c in body["candidates"])
