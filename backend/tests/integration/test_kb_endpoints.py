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
