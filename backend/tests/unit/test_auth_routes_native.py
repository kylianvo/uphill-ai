"""Route tests for native auth. User/session helpers and external token checks are faked."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

import db
import main
from services import apple_auth

client = TestClient(main.app)

WEB_ID = "451637841654-0eoo8qsa5fgnpm4cq0br8phgkhh92c5a.apps.googleusercontent.com"
IOS_ID = "451637841654-ncj3jhv24t9rq665noctori05faajiej.apps.googleusercontent.com"
_USER = {"id": 11, "email": "ana@example.com", "name": "Ana", "role": "user"}


@pytest.fixture(autouse=True)
def created(monkeypatch):
    seen = {}

    def fake_create_or_get_user(email, name, provider, provider_user_id, role="user", onboarding_complete=False):
        seen.update(email=email, name=name, provider=provider, provider_user_id=provider_user_id, role=role)
        return {**_USER, "email": email, "name": name}

    monkeypatch.setattr(main, "create_or_get_user", fake_create_or_get_user)
    monkeypatch.setattr(
        main, "create_session", lambda uid: {"session_token": "tok", "expires_at": "2030-01-01T00:00:00+00:00"}
    )
    monkeypatch.setattr(main, "get_user_by_provider", lambda provider, pid: None)
    return seen


def _fake_google(monkeypatch, payload):
    class _Resp:
        status_code = 200

        def json(self):
            return payload

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url, params=None):
            return _Resp()

    monkeypatch.setattr(main.httpx, "AsyncClient", lambda *a, **k: _Client())


@pytest.mark.parametrize("aud", [WEB_ID, IOS_ID])
def test_google_accepts_uphill_client_ids(monkeypatch, aud):
    _fake_google(monkeypatch, {"aud": aud, "email": "ana@example.com", "sub": "g1", "name": "Ana"})
    resp = client.post("/api/auth/google", json={"credential": "x"})
    assert resp.status_code == 200
    assert resp.json()["session_token"] == "tok"


def test_google_rejects_foreign_audience(monkeypatch, created):
    _fake_google(monkeypatch, {"aud": "999-other.apps.googleusercontent.com", "email": "ana@example.com", "sub": "g1"})
    resp = client.post("/api/auth/google", json={"credential": "x"})
    assert resp.status_code == 401
    assert created == {}


def _fake_apple(monkeypatch, claims=None, error=False):
    def verify(token, audiences, jwk_client=None):
        assert audiences == ["uphill.ai.app", "ai.uphill.app"]
        if error:
            raise apple_auth.AppleTokenError("bad")
        return claims

    monkeypatch.setattr(main.apple_auth, "verify_identity_token", verify)


def test_apple_creates_user_from_verified_email(monkeypatch, created):
    _fake_apple(monkeypatch, {"sub": "a1", "email": "Ana@PrivateRelay.AppleID.com", "email_verified": "true"})
    resp = client.post("/api/auth/apple", json={"identity_token": "jwt", "full_name": "Ana Le"})
    assert resp.status_code == 200
    assert resp.json()["user"]["name"] == "Ana Le"
    assert created == {
        "email": "ana@privaterelay.appleid.com",
        "name": "Ana Le",
        "provider": "apple",
        "provider_user_id": "a1",
        "role": "user",
    }


def test_apple_returning_user_found_by_subject(monkeypatch, created):
    _fake_apple(monkeypatch, {"sub": "a1"})
    monkeypatch.setattr(
        main, "get_user_by_provider", lambda provider, pid: _USER if (provider, pid) == ("apple", "a1") else None
    )
    resp = client.post("/api/auth/apple", json={"identity_token": "jwt"})
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "ana@example.com"
    assert created == {}


def test_apple_new_user_without_verified_email_is_rejected(monkeypatch):
    _fake_apple(monkeypatch, {"sub": "a2", "email": "x@y.z", "email_verified": "false"})
    resp = client.post("/api/auth/apple", json={"identity_token": "jwt"})
    assert resp.status_code == 400


def test_apple_invalid_token_is_401(monkeypatch):
    _fake_apple(monkeypatch, error=True)
    resp = client.post("/api/auth/apple", json={"identity_token": "jwt"})
    assert resp.status_code == 401


def test_apple_subject_links_existing_email_account(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, name TEXT, role TEXT, "
                "provider TEXT, provider_user_id TEXT)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO users (id, email, name, role, provider, provider_user_id) "
                "VALUES (11, 'ana@example.com', 'Ana', 'user', 'google', 'g1')"
            )
        )
    monkeypatch.setattr(db, "engine", engine)

    user = db.create_or_get_user("ana@example.com", "Ana", "apple", "a1")

    assert user["id"] == 11
    assert db.get_user_by_provider("apple", "a1")["id"] == 11
