"""Unit tests for the scheduled sync entry point -- DB and sync are stubbed.

sync_all_active's returned dict carries two extra keys beyond the original
four (reconnect_required, transient_failed) so an operator reading the
summary log line can tell "athletes who must reconnect" apart from "COROS
was flaky" without reading every per-user log line -- see the module
docstring on scripts/sync_devices.py. The existing four keys
(succeeded/failed/activities/daily_metrics) keep their original meaning so
nothing downstream that reads them breaks.
"""

import pytest

from scripts import sync_devices
from services.coros_sync import CorosReconnectRequired
from services.mcp_client import McpError


@pytest.mark.asyncio
async def test_syncs_every_active_connection(monkeypatch):
    monkeypatch.setattr(sync_devices.db, "list_active_connections", lambda p: [{"user_id": 1}, {"user_id": 2}])
    synced = []

    async def fake_sync(user_id, days=30):
        synced.append(user_id)
        return {"activities": 1, "daily_metrics": 1}

    monkeypatch.setattr(sync_devices.coros_sync, "sync_user", fake_sync)
    result = await sync_devices.sync_all_active()
    assert synced == [1, 2]
    assert result["succeeded"] == 2


@pytest.mark.asyncio
async def test_one_failing_athlete_does_not_stop_the_others(monkeypatch):
    monkeypatch.setattr(sync_devices.db, "list_active_connections", lambda p: [{"user_id": 1}, {"user_id": 2}])

    async def fake_sync(user_id, days=30):
        if user_id == 1:
            raise RuntimeError("token revoked")
        return {"activities": 3, "daily_metrics": 2}

    monkeypatch.setattr(sync_devices.coros_sync, "sync_user", fake_sync)
    result = await sync_devices.sync_all_active()
    assert result == {
        "succeeded": 1,
        "failed": 1,
        "activities": 3,
        "daily_metrics": 2,
        "reconnect_required": 0,
        "transient_failed": 0,
    }


@pytest.mark.asyncio
async def test_reconnect_required_is_counted_and_logged_separately(monkeypatch):
    """CorosReconnectRequired is a permanent, athlete-actionable condition --
    distinct from a transient MCP hiccup. It must land in its own bucket so
    an operator can see "N athletes must reconnect" in the summary alone."""
    monkeypatch.setattr(sync_devices.db, "list_active_connections", lambda p: [{"user_id": 1}, {"user_id": 2}])

    async def fake_sync(user_id, days=30):
        if user_id == 1:
            raise CorosReconnectRequired("no refresh token on file")
        return {"activities": 1, "daily_metrics": 1}

    monkeypatch.setattr(sync_devices.coros_sync, "sync_user", fake_sync)
    result = await sync_devices.sync_all_active()
    assert result["reconnect_required"] == 1
    assert result["transient_failed"] == 0
    assert result["failed"] == 1
    assert result["succeeded"] == 1


@pytest.mark.asyncio
async def test_transient_mcp_error_is_counted_separately_from_reconnect(monkeypatch):
    """An McpError is a transport/tool hiccup that will likely clear up on its
    own next hour -- it must not be conflated with reconnect_required, which
    needs the athlete to act."""
    monkeypatch.setattr(sync_devices.db, "list_active_connections", lambda p: [{"user_id": 1}])

    async def fake_sync(user_id, days=30):
        raise McpError("upstream timeout")

    monkeypatch.setattr(sync_devices.coros_sync, "sync_user", fake_sync)
    result = await sync_devices.sync_all_active()
    assert result["transient_failed"] == 1
    assert result["reconnect_required"] == 0
    assert result["failed"] == 1
