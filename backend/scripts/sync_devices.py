"""Scheduled device sync. Run from host cron against the running container:

    0 * * * * flock -n /tmp/uphill-sync-devices.lock \
        docker exec uphill-ai-backend-backend-1 python scripts/sync_devices.py

Mirrors the cron-driven pattern deploy_dw.sh already uses -- no Airflow, no new
container, because production runs only db, backend and grafana and cannot pull
new images. The `flock -n` guard is a recommendation, not yet wired into any
deploy script: a sweep normally finishes in seconds, but if a run ever stalls
(a hung MCP connection, a slow COROS endpoint) past the top of the next hour,
cron fires again regardless. Each connection's own writes stay safe either way
-- upsert_activity/upsert_daily_metric are idempotent under the unique index
on (user_id, source_provider, external_id) -- but two overlapping sweeps still
double the request volume against COROS for every connection, and can race
the same connection's token refresh (services.coros_sync._access_token) against
itself. flock costs nothing and removes the risk outright; see the Task 9
report for the full analysis.

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


if __name__ == "__main__":
    asyncio.run(sync_all_active())
