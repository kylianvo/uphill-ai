"""Send an athlete's next four weeks of runs to their Garmin calendar (Training API).

One Garmin workout plus one schedule entry per Uphill run, the same runs COROS's
standalone mode sends (coros_plan_window.standalone_window). A day whose workouts
changed since the last send is deleted on Garmin and recreated; a day that no longer
has a run is deleted. Garmin allows deletes, so nothing stale is left behind.

Limits (Starter): 100 calls per app per minute and 200 per athlete per day. Calls are
paced app-wide and sends are capped per athlete per day. Progress is saved even when a
send stops part-way, so a retry never duplicates a workout.
"""

import asyncio
import datetime as dt
import time
from collections import defaultdict
from typing import Any

import db
from config import settings
from log_utils import get_logger
from services import coros_push, garmin_oauth, garmin_workouts
from services.coros_plan_window import day_hashes_for, standalone_window, window_end
from services.providers.garmin import PROVIDER

logger = get_logger(__name__)

API = "https://apis.garmin.com"
# About 90 calls a minute across the app, under Garmin's 100 (OAuth refreshes count too).
CALL_SPACING_SECONDS = 0.65
_pace_lock = asyncio.Lock()
_last_call = 0.0
# shortcut: per-process locks, correct while prod runs one uvicorn worker; move to a
# Postgres advisory lock before adding workers.
_user_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)


class PushError(coros_push.PushError):
    """A send refused or failed; `code` is what the UI explains."""


async def _call(method: str, path: str, token: str, body: dict | None = None, transport=None) -> Any:
    global _last_call
    async with _pace_lock:
        wait = _last_call + CALL_SPACING_SECONDS - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _last_call = time.monotonic()
    response = await garmin_oauth.api(method, f"{API}{path}", token, body, transport)
    return response.json() if response.content else None


def _id(payload: Any, key: str) -> str:
    """Garmin answers a create with the object (or, for a schedule, possibly a bare id)."""
    value = payload.get(key) if isinstance(payload, dict) else payload
    if value is None:
        raise garmin_oauth.GarminAuthError(f"Garmin create returned no {key}")
    return str(value)


async def _delete(pair: list[str | None], token: str, transport) -> None:
    workout_id, schedule_id = pair
    for path in (f"/training-api/schedule/{schedule_id}" if schedule_id else None,
                 f"/training-api/workout/v2/{workout_id}"):  # fmt: skip
        if path is None:
            continue
        try:
            await _call("DELETE", path, token, transport=transport)
        except garmin_oauth.GarminAuthError as exc:
            if exc.status != 404:  # already gone in Garmin Connect: nothing to do
                raise


async def _delete_day(scheduled: dict[str, list], key: str, token: str, transport) -> None:
    """Deletes a day's workouts one by one, forgetting each only once Garmin has dropped it."""
    pairs = scheduled.get(key, [])
    while pairs:
        await _delete(pairs[0], token, transport)
        pairs.pop(0)
    scheduled.pop(key, None)


async def _create(course: dict[str, Any], day: dt.date, pairs: list, token: str, transport) -> None:
    """Creates the workout, then its schedule entry. The pair is recorded as soon as the
    workout exists, so a failed schedule call still leaves something a retry can delete."""
    workout = await _call("POST", "/workoutportal/workout/v2", token, garmin_workouts.to_workout(course), transport)
    pair: list[str | None] = [_id(workout, "workoutId"), None]
    pairs.append(pair)
    body = {"workoutId": int(pair[0]), "date": day.isoformat()}
    pair[1] = _id(await _call("POST", "/training-api/schedule/", token, body, transport), "scheduleId")


def _link_for(user_id: int, plan: dict[str, Any]) -> dict[str, Any]:
    """The stored send state, unless it belongs to another Uphill plan (then Garmin still holds
    that plan's workouts, which this send deletes)."""
    link = db.get_garmin_push_link(user_id) or {}
    return {
        "same_plan": link.get("plan_id") == plan["id"],
        "day_hashes": link.get("day_hashes") or {},
        "scheduled": link.get("scheduled") or {},
    }


def _plan_window(plan: dict[str, Any], today: dt.date, lang: str):
    st = coros_push._state(plan)
    return st, standalone_window(st.by_date, today, window_end(today), lang, st.hr_zones)


async def push(user_id: int, today: dt.date, lang: str, transport=None) -> dict[str, Any]:
    connection = db.get_connection(user_id, PROVIDER)
    if not connection or connection.get("status") != "active":
        raise PushError("GARMIN_not_connected", 409)
    if "WORKOUT_IMPORT" not in (connection.get("scopes") or "").split():
        raise PushError("GARMIN_no_workout_permission", 409)
    plan = db.get_active_plan(user_id)
    if not plan:
        raise PushError("NOTHING_to_push", 409)
    lock = _user_locks[user_id]
    if lock.locked():
        raise PushError("PUSH_in_progress", 409)
    async with lock:
        return await _push_locked(user_id, plan, connection, today, lang, transport)


async def _push_locked(user_id, plan, connection, today, lang, transport) -> dict[str, Any]:
    st, window = _plan_window(plan, today, lang)
    link = _link_for(user_id, plan)
    stored = link["day_hashes"] if link["same_plan"] else {}
    # Future days only: what is already behind the athlete stays as it was on Garmin.
    scheduled = {k: v for k, v in link["scheduled"].items() if k >= today.isoformat()}
    desired = {d.date.isoformat(): d.courses for d in window.days}
    current = day_hashes_for(st.by_date, [dt.date.fromisoformat(k) for k in desired])
    changed = [
        k for k in sorted(desired) if stored.get(k) != current[k] or len(scheduled.get(k, [])) != len(desired[k])
    ]
    dropped = [k for k in sorted(scheduled) if k not in desired]
    if not desired and not dropped:
        raise PushError("NOTHING_to_push", 409)

    limit = settings.GARMIN_DAILY_PUSH_LIMIT
    if not db.claim_garmin_push_slot(user_id, today, limit):
        raise PushError("PUSH_limit", 429, {"limit": limit})
    try:
        token = await garmin_oauth.access_token(connection)
    except garmin_oauth.GarminAuthError as exc:
        raise PushError("GARMIN_not_connected", 409) from exc

    hashes = {k: v for k, v in stored.items() if k >= today.isoformat() and k in desired}
    sent = 0
    partial = False
    try:
        for key in dropped:
            await _delete_day(scheduled, key, token, transport)
        for key in changed:
            await _delete_day(scheduled, key, token, transport)
            pairs: list[list[str | None]] = []
            scheduled[key] = pairs
            for course in desired[key]:
                await _create(course, dt.date.fromisoformat(key), pairs, token, transport)
                sent += 1
            hashes[key] = current[key]
    except garmin_oauth.GarminAuthError as exc:
        if exc.status == 412:
            raise PushError("GARMIN_no_workout_permission", 409) from exc
        if not sent and exc.status != 429:
            raise PushError("GARMIN_unavailable", 504) from exc
        partial = True
        logger.warning(
            "garmin push stopped part-way",
            extra={
                "fields": {"service": "garmin_push", "event": "push_partial", "user_id": user_id, "status": exc.status}
            },
        )
    finally:
        summary = {
            "mode": "standalone",
            "days_sent": len([k for k in changed if k in hashes]),
            "workouts_sent": sum(len(v) for v in scheduled.values()),
            "left_in_uphill": window.left_in_uphill,
            "locked_days": len(window.locked_dates),
            "invalid": window.invalid,
            "window_end": window.end.isoformat(),
        }
        db.save_garmin_push_link(
            user_id, plan_id=plan["id"], day_hashes=hashes, scheduled=scheduled, last_summary=summary, partial=partial
        )
    logger.info(
        "garmin push done",
        extra={
            "fields": {
                "service": "garmin_push",
                "event": "push_done",
                "user_id": user_id,
                "sent": sent,
                "partial": partial,
            }
        },
    )
    link_now = db.get_garmin_push_link(user_id) or {}
    return {
        "status": "partial" if partial else "sent",
        "summary": summary,
        "last_pushed_at": link_now["last_pushed_at"].isoformat() if link_now.get("last_pushed_at") else None,
    }


def push_status(user_id: int, today: dt.date) -> dict[str, Any]:
    """The same shape as coros_push.push_status, so the Send button works for both watches."""
    connection = db.get_connection(user_id, PROVIDER)
    if not connection or connection.get("status") != "active":
        return {"connected": False}
    link = db.get_garmin_push_link(user_id)
    if not link or not link.get("last_pushed_at"):
        return {"connected": True, "last_pushed_at": None, "out_of_date": False, "partial": False, "last_summary": None}
    plan = db.get_active_plan(user_id)
    out_of_date = False
    if plan:
        st, window = _plan_window(plan, today, "en")
        stored = (link.get("day_hashes") or {}) if link.get("plan_id") == plan["id"] else {}
        desired = [d.date for d in window.days]
        current = day_hashes_for(st.by_date, desired)
        out_of_date = link.get("plan_id") != plan["id"] or any(stored.get(k) != v for k, v in current.items())
    return {
        "connected": True,
        "last_pushed_at": link["last_pushed_at"].isoformat(),
        "out_of_date": out_of_date,
        "partial": bool(link.get("partial")),
        "last_summary": link.get("last_summary"),
    }
