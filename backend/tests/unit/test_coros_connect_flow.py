"""Unit tests for the COROS connect/callback CSRF binding -- no DB, no live COROS.

RFC 6749 section 10.12 (OAuth client CSRF): `state` alone is unguessable and
single-use, so nothing can forge it, but nothing bound the callback to the
browser that started the flow. Without the cookie set in `/coros/connect` and
checked in `/coros/callback`, an attacker could start their own `/connect`,
get back a legitimate authorize URL bound to *their* user_id, and lure a
victim into completing COROS consent on it -- binding the victim's COROS
account (sleep, HRV, training data) to the attacker's Uphill account.
"""

import time
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import integrations
from services.coros_oauth import TokenSet

app = FastAPI()
app.include_router(integrations.router, prefix="/api")
client = TestClient(app, follow_redirects=False)

CALLBACK = "/api/integrations/coros/callback"
COOKIE_NAME = integrations.COROS_OAUTH_STATE_COOKIE


@pytest.fixture(autouse=True)
def _clean_pending_auth_and_cookies():
    """_PENDING_AUTH is process-global state shared by every test in this
    file -- isolate each test from the others, and never carry a cookie from
    one test's client calls into the next."""
    integrations._PENDING_AUTH.clear()
    client.cookies.clear()
    yield
    integrations._PENDING_AUTH.clear()
    client.cookies.clear()


def _seed_pending(state: str, user_id: int = 42, verifier: str = "verifier123") -> None:
    integrations._PENDING_AUTH[state] = (user_id, verifier, time.monotonic())


def test_callback_without_cookie_redirects_to_error_and_creates_no_connection(monkeypatch):
    state = "state-no-cookie"
    _seed_pending(state)
    saved = []
    monkeypatch.setattr(integrations.db, "save_connection", lambda **kw: saved.append(kw))

    resp = client.get(CALLBACK, params={"code": "auth-code", "state": state})

    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "https://uphill-ai.io.vn/?coros=error"
    assert saved == []
    # An attacker replaying a bare `state` with no cookie must not be able to
    # consume -- and thereby invalidate -- the real athlete's pending entry.
    assert state in integrations._PENDING_AUTH


def test_callback_with_mismatched_cookie_redirects_to_error_and_creates_no_connection(monkeypatch):
    state = "state-mismatch"
    _seed_pending(state)
    saved = []
    monkeypatch.setattr(integrations.db, "save_connection", lambda **kw: saved.append(kw))
    client.cookies.set(COOKIE_NAME, "some-other-attacker-controlled-state")

    resp = client.get(CALLBACK, params={"code": "auth-code", "state": state})

    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "https://uphill-ai.io.vn/?coros=error"
    assert saved == []
    assert state in integrations._PENDING_AUTH


def test_callback_with_matching_cookie_connects(monkeypatch):
    state = "state-match"
    _seed_pending(state, user_id=42, verifier="verifier123")
    saved = {}

    async def fake_exchange_code(code, verifier):
        assert code == "auth-code"
        assert verifier == "verifier123"
        return TokenSet(access_token="at", refresh_token="rt", expires_at=datetime.now(UTC) + timedelta(hours=1))

    monkeypatch.setattr(integrations.coros_oauth, "exchange_code", fake_exchange_code)
    monkeypatch.setattr(integrations.token_crypto, "encrypt_token", lambda t: f"enc:{t}")
    monkeypatch.setattr(integrations.db, "save_connection", lambda **kw: saved.update(kw))
    client.cookies.set(COOKIE_NAME, state)

    resp = client.get(CALLBACK, params={"code": "auth-code", "state": state})

    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "https://uphill-ai.io.vn/?coros=connected"
    assert saved["user_id"] == 42
    assert saved["access_token_enc"] == "enc:at"
    assert saved["refresh_token_enc"] == "enc:rt"
    # Consumed exactly once -- a replay of the same callback must not connect again.
    assert state not in integrations._PENDING_AUTH
    # The one-shot CSRF cookie is cleared on the way out.
    assert "Max-Age=0" in resp.headers.get("set-cookie", "")


def test_connect_sets_httponly_samesite_lax_cookie_scoped_to_callback(monkeypatch):
    monkeypatch.setattr(integrations.settings, "COROS_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(integrations.settings, "TOKEN_ENCRYPTION_KEY", "test-encryption-key")
    monkeypatch.setattr(integrations.coros_oauth, "make_pkce_pair", lambda: ("verifier123", "challenge123"))

    app.dependency_overrides[integrations.get_current_user] = lambda: {"id": 42}
    try:
        resp = client.get("/api/integrations/coros/connect")
    finally:
        app.dependency_overrides.pop(integrations.get_current_user, None)

    assert resp.status_code == 200
    set_cookie = resp.headers.get("set-cookie", "")
    assert COOKIE_NAME in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert f"Path={integrations.COROS_CALLBACK_PATH}" in set_cookie
    # The state handed back in the authorize URL must be the same one stored
    # in the cookie, or the callback's comparison can never match.
    authorize_url = resp.json()["authorize_url"]
    stored_states = list(integrations._PENDING_AUTH.keys())
    assert len(stored_states) == 1
    assert stored_states[0] in authorize_url


def test_connect_returns_503_when_token_encryption_key_is_not_configured(monkeypatch):
    # A fresh deploy that set COROS_CLIENT_ID but never generated
    # TOKEN_ENCRYPTION_KEY must fail here, at /connect, with a clear 503 --
    # not after the athlete has already granted consent at COROS, which is
    # what happens if this only surfaces once the callback tries to encrypt
    # the returned tokens.
    monkeypatch.setattr(integrations.settings, "COROS_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(integrations.settings, "TOKEN_ENCRYPTION_KEY", "")

    app.dependency_overrides[integrations.get_current_user] = lambda: {"id": 42}
    try:
        resp = client.get("/api/integrations/coros/connect")
    finally:
        app.dependency_overrides.pop(integrations.get_current_user, None)

    assert resp.status_code == 503
    assert integrations._PENDING_AUTH == {}


def test_callback_redirects_to_error_when_token_encryption_is_unconfigured(monkeypatch):
    # Simulates the fresh-deploy gap this closes: exchange_code succeeds (COROS
    # accepted the code), but TOKEN_ENCRYPTION_KEY is missing so encrypt_token
    # raises TokenEncryptionUnconfigured. That must redirect to ?coros=error
    # like every other callback failure, not 500 on a bare error page outside
    # the app shell.
    state = "state-unconfigured-key"
    _seed_pending(state, user_id=42, verifier="verifier123")
    saved = []

    async def fake_exchange_code(code, verifier):
        return TokenSet(access_token="at", refresh_token="rt", expires_at=datetime.now(UTC) + timedelta(hours=1))

    monkeypatch.setattr(integrations.coros_oauth, "exchange_code", fake_exchange_code)
    monkeypatch.setattr(integrations.settings, "TOKEN_ENCRYPTION_KEY", "")
    monkeypatch.setattr(integrations.db, "save_connection", lambda **kw: saved.append(kw))
    client.cookies.set(COOKIE_NAME, state)

    resp = client.get(CALLBACK, params={"code": "auth-code", "state": state})

    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "https://uphill-ai.io.vn/?coros=error"
    assert saved == []
    assert "Max-Age=0" in resp.headers.get("set-cookie", "")


def test_callback_without_cookie_logs_a_distinct_event_from_a_mismatched_cookie(caplog):
    # A genuine CSRF attempt and a frontend that forgot `credentials: "include"`
    # on its fetch must not look identical in the logs -- this branch ships no
    # frontend yet, so the latter is the likely cause of a missing cookie.
    state = "state-log-no-cookie"
    _seed_pending(state)

    with caplog.at_level("WARNING", logger=integrations.logger.name):
        resp = client.get(CALLBACK, params={"code": "auth-code", "state": state})

    assert resp.headers["location"] == "https://uphill-ai.io.vn/?coros=error"
    events = [r.fields["event"] for r in caplog.records if hasattr(r, "fields")]
    assert "callback_state_cookie_absent" in events
    assert "callback_state_mismatch" not in events


def test_callback_with_mismatched_cookie_logs_a_distinct_event_from_a_missing_cookie(caplog):
    state = "state-log-mismatch"
    _seed_pending(state)
    client.cookies.set(COOKIE_NAME, "some-other-attacker-controlled-state")

    with caplog.at_level("WARNING", logger=integrations.logger.name):
        resp = client.get(CALLBACK, params={"code": "auth-code", "state": state})

    assert resp.headers["location"] == "https://uphill-ai.io.vn/?coros=error"
    events = [r.fields["event"] for r in caplog.records if hasattr(r, "fields")]
    assert "callback_state_mismatch" in events
    assert "callback_state_cookie_absent" not in events


def test_callback_with_safe_return_url_redirects_to_custom_frontend(monkeypatch):
    state = "state-custom-url"
    custom_url = "http://127.0.0.1:18080"
    integrations._PENDING_AUTH[state] = (42, "verifier123", time.monotonic(), custom_url)
    saved = {}

    async def fake_exchange_code(code, verifier):
        return TokenSet(access_token="at", refresh_token="rt", expires_at=datetime.now(UTC) + timedelta(hours=1))

    monkeypatch.setattr(integrations.coros_oauth, "exchange_code", fake_exchange_code)
    monkeypatch.setattr(integrations.token_crypto, "encrypt_token", lambda t: f"enc:{t}")
    monkeypatch.setattr(integrations.db, "save_connection", lambda **kw: saved.update(kw))
    monkeypatch.setattr(integrations.settings, "ALLOWED_ORIGINS", ["http://127.0.0.1:18080"])
    client.cookies.set(COOKIE_NAME, state)

    resp = client.get(CALLBACK, params={"code": "auth-code", "state": state})

    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == f"{custom_url}/?coros=connected"
    assert saved["user_id"] == 42


def test_callback_without_cookie_succeeds_when_cookie_not_required(monkeypatch):
    state = "state-no-cookie-allowed"
    integrations._PENDING_AUTH[state] = (42, "verifier123", time.monotonic(), None)
    saved = {}

    async def fake_exchange_code(code, verifier):
        return TokenSet(access_token="at", refresh_token="rt", expires_at=datetime.now(UTC) + timedelta(hours=1))

    monkeypatch.setattr(integrations.coros_oauth, "exchange_code", fake_exchange_code)
    monkeypatch.setattr(integrations.token_crypto, "encrypt_token", lambda t: f"enc:{t}")
    monkeypatch.setattr(integrations.db, "save_connection", lambda **kw: saved.update(kw))
    monkeypatch.setattr(integrations.settings, "COROS_REQUIRE_STATE_COOKIE", False)

    resp = client.get(CALLBACK, params={"code": "auth-code", "state": state})

    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "https://uphill-ai.io.vn/?coros=connected"
    assert saved["user_id"] == 42
    assert state not in integrations._PENDING_AUTH
