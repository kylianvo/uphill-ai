"""Scheduled device sync. Run from host cron against the running container:

    0 * * * * docker exec uphill-ai-backend-backend-1 python scripts/sync_devices.py

Mirrors the cron-driven pattern deploy_dw.sh already uses -- no Airflow, no new
container, because production runs only db, backend and grafana and cannot pull
new images. The crontab entry above is deliberately a single line: standard
cron (vixie-cron/cronie) has no line-continuation syntax, so a wrapped
multi-line entry parses each line independently and either fails to schedule
or runs a bare `flock` with no command -- this repo's own precedent
(deploy_dw.sh) installs its crontab entry programmatically as one line for
the same reason.

Guards itself against overlapping runs, entirely inside the script rather
than the crontab line: a sweep normally finishes in seconds, but if one ever
stalls (a hung MCP connection, a slow COROS endpoint) past the top of the
next hour, cron fires again regardless. __main__ takes a non-blocking
exclusive `fcntl.flock` on LOCK_PATH before starting a sweep; if a previous
run still holds it, this process logs one line and exits 0 -- not a failure,
since an overlapping run under a fixed schedule is expected behaviour, not
an error, and a non-zero exit would generate cron mail noise every hour a
sweep runs long. Putting the guard in the script (rather than recommending
`flock -n` be wrapped around the crontab command) means it works no matter
how the script gets invoked, and doesn't depend on every crontab entry being
copied exactly right.

Each connection's own writes were already safe without this -- upsert_activity/
upsert_daily_metric are idempotent under the unique index on (user_id,
source_provider, external_id) -- but two overlapping sweeps still double the
request volume against COROS for every connection, and can race the same
connection's token refresh (services.coros_sync._access_token) against
itself.

Failures are split into two buckets an operator can act on from the summary
line alone, without reading individual per-user log lines:

  - reconnect_required: the athlete's stored refresh token is gone (COROS
    never issued one, or it was revoked). No retry fixes this -- the athlete
    has to reconnect their COROS account from Profile settings.
  - transient_failed: an MCP transport/tool failure, or a total outage across
    all three COROS daily-metric sources. Both are COROS-side hiccups that
    typically clear up on their own by the next hourly run.

Anything else (a DB persistence outage, a connection that went inactive
mid-sweep, or a genuinely unexpected error) still counts toward `failed` so
the totals stay honest, but isn't claimed as either bucket above -- read that
user's own "device sync failed" log line for the exception type and message.
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db  # noqa: E402
from log_utils import get_logger  # noqa: E402
from services import coros_sync  # noqa: E402
from services.mcp_client import McpError  # noqa: E402
from services.providers.coros import PROVIDER, CorosDailyMetricsUnavailableError  # noqa: E402

logger = get_logger(__name__)

# Both are COROS-side outages (transport/tool failure, or every daily-metrics
# source down) rather than something the athlete or an operator needs to act
# on -- see the module docstring.
TRANSIENT_EXCEPTIONS = (McpError, CorosDailyMetricsUnavailableError)

LOCK_PATH = "/tmp/uphill-sync-devices.lock"


async def sync_all_active(limit: int | None = None) -> dict[str, int]:
    connections = db.list_active_connections(PROVIDER)
    if limit is not None:
        connections = connections[:limit]

    totals = {
        "succeeded": 0,
        "failed": 0,
        "activities": 0,
        "daily_metrics": 0,
        "reconnect_required": 0,
        "transient_failed": 0,
    }
    for connection in connections:
        user_id = connection["user_id"]
        try:
            result = await coros_sync.sync_user(user_id)
            totals["succeeded"] += 1
            totals["activities"] += result["activities"]
            totals["daily_metrics"] += result["daily_metrics"]
        except Exception as exc:
            # One athlete's failure -- of any kind -- must not stop the sweep
            # from reaching the rest of the connections, so this is caught and
            # logged per-connection rather than left to propagate.
            totals["failed"] += 1
            if isinstance(exc, coros_sync.CorosReconnectRequired):
                totals["reconnect_required"] += 1
                category = "reconnect_required"
                log = logger.warning
            elif isinstance(exc, TRANSIENT_EXCEPTIONS):
                totals["transient_failed"] += 1
                category = "transient"
                log = logger.warning
            else:
                category = "other"
                log = logger.error
            log(
                "device sync failed",
                extra={
                    "fields": {
                        "service": "sync_devices",
                        "event": "sync_failed",
                        "provider": PROVIDER,
                        "user_id": user_id,
                        "category": category,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                },
            )
    logger.info(
        f"device sync sweep complete: {totals['succeeded']} succeeded, {totals['failed']} failed "
        f"({totals['reconnect_required']} need reconnect, {totals['transient_failed']} transient)",
        extra={"fields": {"service": "sync_devices", "event": "sweep_complete", **totals}},
    )
    return totals


def _try_acquire_lock(path: str = LOCK_PATH):
    """Returns an open, exclusively-locked file handle, or None if another
    sweep already holds the lock.

    Deliberately kept out of sync_all_active and called only from main() --
    sync_all_active must stay directly callable/testable without touching the
    filesystem; only this thin, __main__-only wrapper does I/O.
    """
    import fcntl

    lock_file = open(path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock_file.close()
        return None
    return lock_file


def main() -> int:
    """Entry point for __main__ -- also directly callable from tests without
    spawning a subprocess. Returns the process exit code."""
    lock_file = _try_acquire_lock()
    if lock_file is None:
        logger.info(
            "device sync sweep skipped -- a previous run is still holding the lock",
            extra={"fields": {"service": "sync_devices", "event": "sweep_skipped_locked"}},
        )
        # Exit 0: an overlapping run under a fixed hourly schedule is expected
        # behaviour, not a failure -- a non-zero exit here would generate cron
        # mail noise every hour a previous sweep happens to still be running.
        return 0
    try:
        asyncio.run(sync_all_active())
    finally:
        lock_file.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
