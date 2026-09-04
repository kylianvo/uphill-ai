"""Unit tests for the scheduled sync entry point -- DB and sync are stubbed.

sync_all_active's returned dict carries two extra keys beyond the original
four (reconnect_required, transient_failed) so an operator reading the
summary log line can tell "athletes who must reconnect" apart from "COROS
was flaky" without reading every per-user log line -- see the module
docstring on scripts/sync_devices.py. The existing four keys
(succeeded/failed/activities/daily_metrics) keep their original meaning so
nothing downstream that reads them breaks.

main()'s overlap guard is tested by monkeypatching _try_acquire_lock so no
real file locking happens here -- these tests only prove main() branches
correctly on lock acquired/not-acquired and releases what it was given. They
do not exercise real fcntl.flock semantics (that a second concurrent OS
process actually blocks); see the Task 9 report for what to check manually.
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


def test_main_skips_when_a_previous_sweep_still_holds_the_lock(monkeypatch):
    """A stalled prior run must not be piled on top of -- see the module
    docstring on the overlapping-sweeps risk. main() checks the lock itself,
    so this holds no matter how the script is invoked, unlike a crontab-line
    `flock` that only helps if every entry is copied exactly right."""
    monkeypatch.setattr(sync_devices, "_try_acquire_lock", lambda: None)

    def fail_if_called(*args, **kwargs):
        pytest.fail("sync_all_active must not run while the lock is held elsewhere")

    monkeypatch.setattr(sync_devices, "sync_all_active", fail_if_called)

    exit_code = sync_devices.main()

    # Not a failure: an overlapping run under a fixed hourly schedule is
    # expected behaviour, not an error -- a non-zero exit would generate cron
    # mail noise every hour a previous sweep happens to still be running.
    assert exit_code == 0


def test_main_runs_the_sweep_and_releases_the_lock_when_acquired(monkeypatch):
    monkeypatch.setattr(sync_devices.db, "list_active_connections", lambda p: [])

    class FakeLock:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    fake_lock = FakeLock()
    monkeypatch.setattr(sync_devices, "_try_acquire_lock", lambda: fake_lock)

    exit_code = sync_devices.main()

    assert exit_code == 0
    assert fake_lock.closed is True
