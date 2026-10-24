"""Processes one Garmin push body, after the webhook has already answered 200.

Garmin times a push out after 30 s and retries anything that is not a 200, so the
webhook acknowledges first and this runs in the background. Every step is
idempotent: Garmin re-sends, and activities upsert on their Garmin activityId.
"""

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

import db
from log_utils import get_logger
from services.matching import runner as matching_runner
from services.providers import garmin

logger = get_logger(__name__)


def _log(event: str, **fields: Any) -> None:
    logger.info(f"garmin {event}", extra={"fields": {"service": "garmin_ingest", "event": event, **fields}})


async def process(body: dict[str, Any]) -> None:
    for key, items in body.items():
        if not isinstance(items, list):
            continue
        if key in garmin.ACTIVITY_KEYS:
            await _activities(items)
        elif key == "deregistrations":
            _deregistrations(items)
        elif key == "userPermissionsChange":
            _permissions(items)
        else:
            # A summary type we have not built for yet (enabled in API Tools by mistake, or Phase 2).
            _log("ignored_summary_type", summary_type=key, count=len(items))


def _connection(item: dict[str, Any]) -> dict[str, Any] | None:
    user_id = item.get("userId")
    return db.get_connection_by_provider_user(garmin.PROVIDER, str(user_id)) if user_id else None


async def _activities(items: list[dict[str, Any]]) -> None:
    stored: dict[int, list[tuple[date, int | None]]] = defaultdict(list)
    for item in items:
        connection = _connection(item)
        if connection is None:
            _log("unknown_user_dropped")
            continue
        activity = garmin.to_activity(item)
        if activity is None:
            continue
        db.upsert_activity(connection["user_id"], activity)
        stored[connection["user_id"]].append((activity.start_time.date(), garmin.offset_minutes(item)))
    for user_id, days in stored.items():
        db.mark_connection_synced(user_id, garmin.PROVIDER)
        since = min(d for d, _ in days) - timedelta(days=1)
        try:
            await matching_runner.match_user(user_id, since, date.today(), tz_offset_minutes=days[-1][1])
        except Exception:
            # The activities are stored; the next push re-runs matching.
            logger.exception("garmin matching failed")
        _log("activities_stored", user_id=user_id, count=len(days))


def _deregistrations(items: list[dict[str, Any]]) -> None:
    """The athlete removed Uphill AI in Garmin Connect: delete everything Garmin sent us."""
    for item in items:
        connection = _connection(item)
        if connection is not None:
            db.delete_provider_data(connection["user_id"], garmin.PROVIDER)
            _log("deregistered", user_id=connection["user_id"])


def _permissions(items: list[dict[str, Any]]) -> None:
    """The athlete switched a data-sharing toggle in Garmin Connect after connecting."""
    for item in items:
        connection = _connection(item)
        if connection is not None:
            permissions = item.get("permissions") or []
            db.set_connection_scopes(connection["user_id"], garmin.PROVIDER, " ".join(sorted(permissions)))
            _log("permissions_changed", user_id=connection["user_id"], permissions=sorted(permissions))
