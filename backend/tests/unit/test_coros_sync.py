"""Unit tests for the sync orchestration -- DB and adapter are stubbed."""

from datetime import UTC, date, datetime, timedelta

import pytest

from services import coros_sync, token_crypto
from services.providers.base import CanonicalActivity, CanonicalDailyMetric


class StubAdapter:
    def __init__(self):
        self.activities = [
            CanonicalActivity(
                external_id="a1",
                provider="coros",
                activity_type="trail_run",
                start_time=datetime(2026, 8, 29, tzinfo=UTC),
                duration_seconds=5434.0,
                distance_km=15.03,
            )
        ]
        self.metrics = [CanonicalDailyMetric(date(2026, 9, 4), "coros", resting_hr=57)]

    async def fetch_activities(self, since, until):
        return self.activities

    async def fetch_daily_metrics(self, days=7):
        return self.metrics


class EmptyAdapter:
    """An adapter that genuinely has nothing new to report."""

    async def fetch_activities(self, since, until):
        return []

    async def fetch_daily_metrics(self, days=7):
        return []


@pytest.mark.asyncio
async def test_sync_persists_activities_and_metrics_and_reports_counts(monkeypatch):
    saved_activities, saved_metrics = [], []
    monkeypatch.setattr(coros_sync.db, "upsert_activity", lambda uid, a: saved_activities.append(a) or 1)
    monkeypatch.setattr(coros_sync.db, "upsert_daily_metric", lambda uid, m: saved_metrics.append(m) or 1)
    monkeypatch.setattr(coros_sync.db, "mark_connection_synced", lambda uid, p: None)

    result = await coros_sync.persist(user_id=7, adapter=StubAdapter(), days=30)

    assert result == {"activities": 1, "daily_metrics": 1}
    assert len(saved_activities) == 1
    assert len(saved_metrics) == 1


@pytest.mark.asyncio
async def test_sync_continues_when_one_activity_fails_to_persist(monkeypatch):
    # One malformed activity must not abandon the rest of the sync.
    adapter = StubAdapter()
    adapter.activities = adapter.activities * 3
    calls = {"n": 0}

    def flaky(uid, activity):
        calls["n"] += 1
        if calls["n"] == 2:
            raise ValueError("bad row")
        return calls["n"]

    monkeypatch.setattr(coros_sync.db, "upsert_activity", flaky)
    monkeypatch.setattr(coros_sync.db, "upsert_daily_metric", lambda uid, m: 1)
    monkeypatch.setattr(coros_sync.db, "mark_connection_synced", lambda uid, p: None)

    result = await coros_sync.persist(user_id=7, adapter=adapter, days=30)
    assert result["activities"] == 2


@pytest.mark.asyncio
async def test_persist_raises_when_every_activity_fails_to_persist(monkeypatch):
    """A 100% failure rate on a non-empty batch reads as the DB being down, not
    a quiet training day -- it must not come back as a clean zero count."""
    adapter = StubAdapter()

    def always_fails(uid, activity):
        raise RuntimeError("db unavailable")

    def fail_if_called(*args, **kwargs):
        pytest.fail("mark_connection_synced must not run when persistence failed completely")

    monkeypatch.setattr(coros_sync.db, "upsert_activity", always_fails)
    monkeypatch.setattr(coros_sync.db, "upsert_daily_metric", lambda uid, m: 1)
    monkeypatch.setattr(coros_sync.db, "mark_connection_synced", fail_if_called)

    with pytest.raises(coros_sync.CorosSyncPersistError):
        await coros_sync.persist(user_id=7, adapter=adapter, days=30)


@pytest.mark.asyncio
async def test_persist_raises_when_every_daily_metric_fails_to_persist(monkeypatch):
    adapter = StubAdapter()

    def always_fails(uid, metric):
        raise RuntimeError("db unavailable")

    def fail_if_called(*args, **kwargs):
        pytest.fail("mark_connection_synced must not run when persistence failed completely")

    monkeypatch.setattr(coros_sync.db, "upsert_activity", lambda uid, a: 1)
    monkeypatch.setattr(coros_sync.db, "upsert_daily_metric", always_fails)
    monkeypatch.setattr(coros_sync.db, "mark_connection_synced", fail_if_called)

    with pytest.raises(coros_sync.CorosSyncPersistError):
        await coros_sync.persist(user_id=7, adapter=adapter, days=30)


@pytest.mark.asyncio
async def test_persist_returns_zeros_without_raising_when_nothing_to_sync(monkeypatch):
    """Genuinely empty results are not the same failure mode as every row
    failing -- zero counts are the honest, correct answer here."""

    def fail_if_called(*args, **kwargs):
        pytest.fail("upsert should not be called when there is nothing to persist")

    marked = []
    monkeypatch.setattr(coros_sync.db, "upsert_activity", fail_if_called)
    monkeypatch.setattr(coros_sync.db, "upsert_daily_metric", fail_if_called)
    monkeypatch.setattr(coros_sync.db, "mark_connection_synced", lambda uid, p: marked.append((uid, p)))

    result = await coros_sync.persist(user_id=7, adapter=EmptyAdapter(), days=30)

    assert result == {"activities": 0, "daily_metrics": 0}
    assert marked == [(7, "coros")]


@pytest.mark.asyncio
async def test_access_token_requires_reconnect_when_refresh_token_missing():
    """coros_callback stores refresh_token_enc=None whenever COROS's token
    exchange returned no refresh_token. _access_token must raise a clear,
    typed error instead of crashing on token_crypto.decrypt_token(None) once
    the access token is near expiry and there is nothing to refresh with."""
    connection = {
        "user_id": 7,
        "token_expires_at": datetime.now(UTC) - timedelta(minutes=1),
        "refresh_token_enc": None,
        "access_token_enc": "irrelevant",
        "scopes": "openid mcp.tools offline_access",
        "provider_user_id": None,
    }

    with pytest.raises(coros_sync.CorosReconnectRequired):
        await coros_sync._access_token(connection)


@pytest.mark.asyncio
async def test_access_token_requires_reconnect_when_refresh_token_cannot_be_decrypted(monkeypatch):
    """A rotated TOKEN_ENCRYPTION_KEY means the stored ciphertext can no
    longer be read back -- functionally identical to having no refresh token
    at all, so this must surface as CorosReconnectRequired (the honest,
    typed reason the athlete needs to reconnect), not an unhandled
    TokenDecryptionError bubbling up as a 500."""
    connection = {
        "user_id": 7,
        "token_expires_at": datetime.now(UTC) - timedelta(minutes=1),
        "refresh_token_enc": "undecryptable-ciphertext",
        "access_token_enc": "irrelevant",
        "scopes": "openid mcp.tools offline_access",
        "provider_user_id": None,
    }

    def raise_decryption_error(ciphertext, key=None):
        raise token_crypto.TokenDecryptionError("Stored token could not be decrypted.")

    monkeypatch.setattr(coros_sync.token_crypto, "decrypt_token", raise_decryption_error)

    with pytest.raises(coros_sync.CorosReconnectRequired):
        await coros_sync._access_token(connection)


@pytest.mark.asyncio
async def test_access_token_requires_reconnect_when_access_token_cannot_be_decrypted(monkeypatch):
    """Same rotated-key scenario, but hitting the still-valid (non-expiring)
    access token path instead of the refresh path."""
    connection = {
        "user_id": 7,
        "token_expires_at": datetime.now(UTC) + timedelta(hours=1),
        "refresh_token_enc": "irrelevant",
        "access_token_enc": "undecryptable-ciphertext",
        "scopes": "openid mcp.tools offline_access",
        "provider_user_id": None,
    }

    def raise_decryption_error(ciphertext, key=None):
        raise token_crypto.TokenDecryptionError("Stored token could not be decrypted.")

    monkeypatch.setattr(coros_sync.token_crypto, "decrypt_token", raise_decryption_error)

    with pytest.raises(coros_sync.CorosReconnectRequired):
        await coros_sync._access_token(connection)
