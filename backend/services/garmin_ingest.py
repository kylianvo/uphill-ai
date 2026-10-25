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
from services import garmin_oauth, recovery_baseline
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
        elif key in garmin.RECOVERY_KEYS:
            _recovery(key, items)
        elif key == "deregistrations":
            await _deregistrations(items)
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


# Garmin's answer when it no longer accepts the athlete's credentials.
_REJECTED = frozenset({400, 401, 403})


def _recovery(key: str, items: list[dict[str, Any]]) -> None:
    """Resting HR, sleep and overnight HRV into daily_metrics. Garmin re-sends a summary
    when more data arrives (a night synced while still asleep), and the newest value wins."""
    days: dict[int, set[date]] = defaultdict(set)
    for item in items:
        connection = _connection(item)
        if connection is None:
            continue
        metric = garmin.to_daily_metric(key, item)
        if metric is None:
            continue
        db.upsert_daily_metric(connection["user_id"], metric)
        days[connection["user_id"]].add(metric.metric_date)
    for user_id, dates in days.items():
        db.mark_connection_synced(user_id, garmin.PROVIDER)
        if key == "hrv":
            # Garmin sends no HRV status; derive it from the athlete's own 28-day baseline.
            recovery_baseline.refresh(user_id, dates, garmin.PROVIDER)
        _log("recovery_stored", user_id=user_id, summary_type=key, days=len(dates))


async def _registration_gone(connection: dict[str, Any]) -> bool | None:
    """True when Garmin rejects the athlete's credentials (deregistered), False when it still
    answers for them, None when we could not tell (5xx, 429, timeout). Token refreshes are
    serialised per athlete (garmin_oauth.access_token), so a rejection is not a rotation race."""
    try:
        await garmin_oauth.fetch_user_id(await garmin_oauth.access_token(connection))
        return False
    except garmin_oauth.GarminAuthError as exc:
        return True if exc.status in _REJECTED else None
    except Exception:
        return None


async def _deregistrations(items: list[dict[str, Any]]) -> None:
    """The athlete removed Uphill AI in Garmin Connect: delete everything Garmin sent us, once
    Garmin confirms the credentials are dead. A forged push (leaked webhook token) or a Garmin
    outage must not be able to wipe an athlete's data."""
    for garmin_user_id in {str(i.get("userId")) for i in items if i.get("userId")}:
        connection = db.get_connection_by_provider_user(garmin.PROVIDER, garmin_user_id)
        if connection is None:
            continue
        gone = await _registration_gone(connection)
        if gone:
            db.delete_provider_data(connection["user_id"], garmin.PROVIDER)
            _log("deregistered", user_id=connection["user_id"])
        else:
            logger.warning(
                "garmin deregistration not confirmed",
                extra={
                    "fields": {
                        "service": "garmin_ingest",
                        "event": "deregistration_unconfirmed" if gone is False else "deregistration_unverified",
                        "user_id": connection["user_id"],
                    }
                },
            )


def _permissions(items: list[dict[str, Any]]) -> None:
    """The athlete switched a data-sharing toggle in Garmin Connect after connecting."""
    for item in items:
        connection = _connection(item)
        if connection is not None:
            permissions = item.get("permissions") or []
            db.set_connection_scopes(connection["user_id"], garmin.PROVIDER, " ".join(sorted(permissions)))
            _log("permissions_changed", user_id=connection["user_id"], permissions=sorted(permissions))
