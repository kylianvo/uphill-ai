"""Send an athlete's Uphill plan to COROS (COROS push, phases 1 and 1b).

Race goals ("plan" mode) mirror into ONE COROS training plan anchored on race
day, updated in place: updateTrainingPlan replaces whole days (a rest entry
clears one). Uphill generates weeks one block at a time and COROS needs a
workout in a plan's final week, so race day carries the anchor -- the generated
race-day run, else a placeholder -- and weeks are added as Uphill generates
them. Lifecycle per push:

- no live linked plan -> createTrainingPlan from today (or up to 14 days later
  for a far race) through race week
- live plan, race week within 16 weeks of its start -> updateTrainingPlan
  (resizing totalWeeks when the race moved)
- race moved past that -> shorten the old plan to end this Sunday and create a
  new one from next Monday (rollover)

Non-race goals ("standalone" mode) have no event to anchor a plan on and push
standalone scheduled workouts instead (_sync_standalone).

Pure mapping lives in coros_workouts / coros_plan_window; this module is I/O.
Workout text and tokens are never logged.
"""

import datetime as dt
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import db
import telemetry
from config import settings
from log_utils import get_logger
from services import coros_sync
from services.coros_plan_window import (
    MAX_PLAN_WEEKS,
    MIN_PLAN_WEEKS,
    GeometryRefusal,
    PlanGeometry,
    PushWindow,
    build_window,
    clear_dates,
    course_list,
    day_hashes_for,
    is_race_goal,
    last_generated_date,
    last_run_date,
    monday_of,
    natural_weeks,
    periodization,
    plan_geometry,
    race_date_of,
    rows_by_date,
    send_dates,
    standalone_window,
    window_end,
    with_race_day,
    ymd,
)
from services.coros_workouts import SPORT_REST
from services.mcp_client import McpClient, McpError, McpToolError
from services.providers.coros import PROVIDER

logger = get_logger(__name__)

PLAN_NAME_MAX = 90
REASON_LOG_MAX = 300
_OVERVIEW = {
    "en": (
        "Synced from Uphill AI. Change your plan in Uphill AI and press Send to COROS again; "
        "edits made to this plan in COROS are overwritten on the next send."
    ),
    "vi": (
        "Đồng bộ từ Uphill AI. Hãy chỉnh plan trong Uphill AI rồi bấm Gửi sang COROS lần nữa; "
        "các thay đổi làm trực tiếp trên COROS sẽ bị ghi đè ở lần gửi tiếp theo."
    ),
}


class PushError(Exception):
    def __init__(self, code: str, status: int, params: dict[str, Any] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.status = status
        self.params = params or {}


@dataclass(frozen=True)
class PlanRecord:
    plan_id: str
    name: str
    role: str
    editable: bool
    start: dt.date | None
    weeks: int | None


_HEAD = re.compile(r"^\d+\.\s+(?P<name>.*?)\s+\[[^\]]+\]", re.M)
_PLAN_ID = re.compile(r"Plan ID:\s*(\d+)")
_ROLE = re.compile(r"Record role:\s*(\w+)")
_EDITABLE = re.compile(r"Editable via MCP:\s*(\w+)")
_DATES = re.compile(r"Dates:\s*(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})")
_WEEKS = re.compile(r"Weeks:\s*(\d+)")


def parse_plan_library(text: str) -> list[PlanRecord]:
    records = []
    for block in re.split(r"\n(?=\d+\.\s)", text or ""):
        head, pid = _HEAD.search(block), _PLAN_ID.search(block)
        if not head or not pid:
            continue
        role, editable = _ROLE.search(block), _EDITABLE.search(block)
        dates, weeks = _DATES.search(block), _WEEKS.search(block)
        records.append(
            PlanRecord(
                plan_id=pid[1],
                name=head["name"].strip(),
                role=role[1].lower() if role else "unknown",
                editable=bool(editable and editable[1].lower() in ("yes", "true")),
                start=dt.date.fromisoformat(dates[1]) if dates else None,
                weeks=int(weeks[1]) if weeks else None,
            )
        )
    return records


def created_plan_id(create_text: str, records: list[PlanRecord], name: str) -> str | None:
    m = _PLAN_ID.search(create_text or "")
    if m:
        return m[1]
    match = next((r for r in records if r.name == name and r.role == "execution" and r.editable), None)
    return match.plan_id if match else None


_ID_IN_PLAN = re.compile(r"idInPlan\W{0,3}(\d+)")


def parse_id_in_plan(text: str) -> str | None:
    """The scheduled workout's id from a create/updateScheduledWorkout result."""
    m = _ID_IN_PLAN.search(text or "")
    return m[1] if m else None


def _live(records: list[PlanRecord], plan_id: str | None = None, name: str | None = None) -> PlanRecord | None:
    for r in records:
        if r.role != "execution" or not r.editable or r.start is None:
            continue
        if (plan_id and r.plan_id == plan_id) or (name and r.name == name):
            return r
    return None


def plan_name(plan: dict[str, Any]) -> str:
    return f"Uphill AI · {plan.get('race_name') or 'Training'}"[:PLAN_NAME_MAX]


def _default_client(token: str) -> McpClient:
    return McpClient(settings.COROS_MCP_ENDPOINT, token)


def _summary(
    windows: list[PushWindow], end: dt.date, *, mode: str, plan_start: dt.date | None = None, stale: int = 0
) -> dict[str, Any]:
    return {
        "mode": mode,
        "days_sent": sum(len(w.days) for w in windows),
        "workouts_sent": sum(1 for w in windows for d in w.days for c in d.courses if c["sportType"] != SPORT_REST),
        "left_in_uphill": sum(w.left_in_uphill for w in windows),
        "locked_days": sum(len(w.locked_dates) for w in windows),
        "invalid": sum(w.invalid for w in windows),
        "stale": stale,
        "window_end": end.isoformat(),
        "plan_start": plan_start.isoformat() if plan_start else None,
    }


@dataclass(frozen=True)
class _State:
    """The Uphill side of a push, computed before any COROS call."""

    by_date: dict[dt.date, list[dict[str, Any]]]  # generated rows plus the race-day placeholder
    race: dt.date | None
    last_generated: dt.date | None
    last_run: dt.date | None


def _state(plan: dict[str, Any]) -> _State:
    raw = rows_by_date(plan, db.get_plan_workouts_with_match(plan["id"]))
    return _State(
        by_date=with_race_day(plan, raw),
        race=race_date_of(plan) if is_race_goal(plan) else None,
        last_generated=last_generated_date(raw),
        last_run=last_run_date(raw),
    )


def _mode(plan: dict[str, Any]) -> str:
    return "plan" if is_race_goal(plan) else "standalone"


def _geometry(st: _State, frm: dt.date) -> PlanGeometry:
    try:
        return plan_geometry(st.race, st.last_run, frm)
    except GeometryRefusal as exc:
        raise PushError(exc.code, 409, exc.params) from exc


def _end_week_monday(st: _State, start: dt.date) -> dt.date:
    """Race week, or a later generated run's week -- but generated weeks never
    stretch a plan past 16 weeks from its start (only the race can)."""
    race_monday = monday_of(st.race)
    if st.last_run is None:
        return race_monday
    cap = monday_of(start) + dt.timedelta(weeks=MAX_PLAN_WEEKS - 1)
    return max(race_monday, min(monday_of(st.last_run), cap))


def _plan_dates(
    st: _State, start: dt.date, end: dt.date, today: dt.date, stored: dict[str, str]
) -> tuple[list[dt.date], list[dt.date]]:
    """(dates to send, previously sent dates to clear) for a COROS plan spanning [start, end]."""
    frm = max(today, start)
    last = min(st.last_generated, end) if st.last_generated else None
    race = st.race if st.race and st.race <= end else None
    dates = send_dates(frm, last, race)
    return dates, clear_dates(stored, dates, frm, end)


async def push_plan(
    user_id: int,
    today: dt.date,
    lang: str,
    *,
    client_factory: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    try:
        result = await _push(user_id, today, lang, client_factory or _default_client)
    except PushError as exc:
        telemetry.coros_push_total.labels(result=exc.code).inc()
        logger.info(
            "coros push refused",
            extra={"fields": {"service": "coros_push", "event": "push_refused", "user_id": user_id, "code": exc.code}},
        )
        raise
    telemetry.coros_push_total.labels(result=result["status"]).inc()
    logger.info(
        "coros push done",
        extra={
            "fields": {
                "service": "coros_push",
                "event": "push_done",
                "user_id": user_id,
                "status": result["status"],
                **{k: v for k, v in result["summary"].items() if k not in ("window_end", "plan_start")},
            }
        },
    )
    return result


async def _push(user_id: int, today: dt.date, lang: str, client_factory: Callable[[str], Any]) -> dict[str, Any]:
    connection = db.get_connection(user_id, PROVIDER)
    if not connection or connection.get("status") != "active":
        raise PushError("COROS_not_connected", 409)
    plan = db.get_active_plan(user_id)
    if not plan:
        raise PushError("NOTHING_to_push", 409)
    try:
        with db.coros_push_lock(user_id):
            return await _push_locked(user_id, plan, connection, today, lang, client_factory)
    except db.CorosPushInProgressError as exc:
        raise PushError("PUSH_in_progress", 409) from exc


def _current_link(user_id: int, plan: dict[str, Any]) -> dict[str, Any] | None:
    """The link row, unless it belongs to another Uphill plan or mode -- then start fresh."""
    link = db.get_coros_plan_link(user_id)
    if link and link.get("plan_id") == plan["id"] and link.get("mode") == _mode(plan):
        return link
    return None


async def _push_locked(user_id, plan, connection, today, lang, client_factory) -> dict[str, Any]:
    st = _state(plan)
    link = _current_link(user_id, plan)
    standalone = None
    if _mode(plan) == "plan":
        if st.race < today:
            raise PushError("NOTHING_to_push", 409)
        if link is None:
            _geometry(st, today)  # refuse a plan COROS can't hold before spending a push or calling COROS
    else:
        standalone = standalone_window(st.by_date, today, window_end(today), lang)
        if not standalone.days:
            raise PushError("NOTHING_to_push", 409)
    limit = settings.COROS_DAILY_PUSH_LIMIT
    if not db.claim_coros_push_slot(user_id, today, limit):
        raise PushError("PUSH_limit", 429, {"limit": limit})
    try:
        token = await coros_sync._access_token(connection)
    except coros_sync.CorosReconnectRequired as exc:
        raise PushError("COROS_not_connected", 409) from exc

    client = client_factory(token)
    try:
        await client.initialize()
        if standalone is not None:
            return await _sync_standalone(client, user_id, plan, st, link, standalone, today)
        return await _sync_plan(client, user_id, plan, st, link, today, lang)
    except McpToolError as exc:
        logger.warning(
            "coros push rejected",
            extra={
                "fields": {
                    "service": "coros_push",
                    "event": "push_rejected",
                    "user_id": user_id,
                    "reason": (exc.reason or str(exc))[:REASON_LOG_MAX],
                }
            },
        )
        raise PushError("COROS_rejected", 502) from exc
    except McpError as exc:
        raise PushError("COROS_unavailable", 504) from exc
    finally:
        await client.aclose()


async def _library(client) -> list[PlanRecord]:
    return parse_plan_library(await client.call_tool("queryTrainingPlanLibrary", {}))


async def _sync_plan(client, user_id, plan, st, link, today, lang) -> dict[str, Any]:
    name = plan_name(plan)
    records = await _library(client)
    target = _live(records, plan_id=link["coros_plan_id"] if link else None) or _live(records, name=name)
    if target is None:
        return await _create(client, user_id, plan, st, _geometry(st, today), today, lang, name)
    stored = link["day_hashes"] if link and link.get("coros_plan_id") == target.plan_id else {}
    needed = natural_weeks(target.start, _end_week_monday(st, target.start))
    if needed > MAX_PLAN_WEEKS:
        return await _rollover(client, user_id, plan, st, target, stored, today, lang, name)
    return await _update(client, user_id, plan, st, target, max(needed, MIN_PLAN_WEEKS), stored, today, lang)


def _window(st, start, end, today, lang, stored) -> tuple[PushWindow, list[dt.date]]:
    """What to send for a COROS plan spanning [start, end], and every date it tracks."""
    dates, clear = _plan_dates(st, start, end, today, stored)
    window = build_window(st.by_date, max(today, start), end, lang, dates=dates, clear=clear)
    return window, sorted({*dates, *clear})


async def _create_plan(client, st, g: PlanGeometry, today, lang, name) -> tuple[str, PushWindow, list[dt.date]]:
    """createTrainingPlan for geometry `g`; returns the new COROS plan id and what was sent."""
    window, tracked = _window(st, g.start, g.end, today, lang, {})
    text = await client.call_tool(
        "createTrainingPlan",
        {
            "planInfo": {
                "planName": name,
                "planOverview": _OVERVIEW.get(lang, _OVERVIEW["en"]),
                "planStartDate": ymd(g.start),
                "totalWeeks": g.weeks,
            },
            "courseList": course_list(window, g.start),
            "phaseInfo": {"periodization": periodization(st.by_date, g.start, g.weeks)},
        },
    )
    new_id = created_plan_id(text, await _library(client), name)
    if new_id is None:
        # Created, but its id can't be read back; the next push adopts it by name.
        raise PushError("COROS_unavailable", 504)
    return new_id, window, tracked


async def _create(client, user_id, plan, st, g, today, lang, name) -> dict[str, Any]:
    new_id, window, tracked = await _create_plan(client, st, g, today, lang, name)
    return _save(user_id, plan, st, new_id, g.start, g.weeks, g.end, tracked, [window], partial=False)


async def _update(client, user_id, plan, st, target, total, stored, today, lang) -> dict[str, Any]:
    end = monday_of(target.start) + dt.timedelta(days=7 * total - 1)
    window, tracked = _window(st, target.start, end, today, lang, stored)
    args: dict[str, Any] = {"planInfo": {"planId": target.plan_id}}
    courses = course_list(window, target.start)
    if courses:
        args["courseList"] = courses
    if total != (target.weeks or total):
        args["planInfo"]["totalWeeks"] = total
        args["phaseInfo"] = {"periodization": periodization(st.by_date, target.start, total)}
    if len(args) > 1:
        await client.call_tool("updateTrainingPlan", args)
    return _save(user_id, plan, st, target.plan_id, target.start, total, end, tracked, [window], partial=False)


async def _rollover(client, user_id, plan, st, target, stored, today, lang, name) -> dict[str, Any]:
    this_sunday = monday_of(today) + dt.timedelta(days=6)
    next_monday = this_sunday + dt.timedelta(days=1)
    g = _geometry(st, next_monday)  # a refusal here leaves the old plan untouched
    keep = natural_weeks(target.start, this_sunday)
    this_week, tracked = _window(st, target.start, this_sunday, today, lang, stored)
    args: dict[str, Any] = {
        "planInfo": {"planId": target.plan_id, "totalWeeks": keep},
        "phaseInfo": {"periodization": periodization(st.by_date, target.start, keep)},
    }
    courses = course_list(this_week, target.start)
    if courses:
        args["courseList"] = courses
    await client.call_tool("updateTrainingPlan", args)  # failure here: nothing changed

    try:
        new_id, ahead, ahead_tracked = await _create_plan(client, st, g, next_monday, lang, name)
    except (McpError, PushError):
        return _save(
            user_id, plan, st, target.plan_id, target.start, keep, this_sunday, tracked, [this_week], partial=True
        )
    return _save(
        user_id,
        plan,
        st,
        new_id,
        g.start,
        g.weeks,
        g.end,
        sorted({*tracked, *ahead_tracked}),
        [this_week, ahead],
        partial=False,
    )


async def _sync_standalone(client, user_id, plan, st, link, window: PushWindow, today) -> dict[str, Any]:
    """One COROS scheduled workout per Uphill run. A changed day is rewritten in
    place (updateScheduledWorkout); scheduled workouts can't be moved or deleted
    over MCP, so a copy Uphill no longer has stays on COROS as `stale` until the
    athlete deletes it -- tracked, and reused if that day gets a run again.
    Progress is saved even when a call fails, so a retry never duplicates."""
    stored = dict(link["day_hashes"]) if link else {}
    scheduled = {k: list(v) for k, v in (link["scheduled"] if link else {}).items() if k >= today.isoformat()}
    desired = {d.date: d.courses for d in window.days}
    current = day_hashes_for(st.by_date, sorted(desired))
    hashes = {k: v for k, v in stored.items() if k >= today.isoformat()}
    sent_days = sent = 0
    partial = False
    try:
        for d, courses in sorted(desired.items()):
            key = d.isoformat()
            ids = scheduled.get(key, [])
            if stored.get(key) == current[key] and len(ids) >= len(courses):
                continue
            for i, course in enumerate(courses):
                args = {"date": str(ymd(d)), "course": course}
                if i < len(ids):
                    text = await client.call_tool("updateScheduledWorkout", {**args, "idInPlan": ids[i]})
                    ids[i] = parse_id_in_plan(text) or ids[i]
                else:
                    new_id = parse_id_in_plan(await client.call_tool("createScheduledWorkout", args))
                    if new_id is None:
                        raise McpError("createScheduledWorkout returned no idInPlan")
                    ids.append(new_id)
                scheduled[key] = ids
                sent += 1
            hashes[key] = current[key]
            sent_days += 1
    except McpError as exc:
        if not sent:
            raise
        partial = True
        logger.warning(
            "coros standalone push stopped part-way",
            extra={
                "fields": {
                    "service": "coros_push",
                    "event": "push_partial",
                    "user_id": user_id,
                    "reason": (getattr(exc, "reason", "") or str(exc))[:REASON_LOG_MAX],
                }
            },
        )
    locked = set(window.locked_dates)
    stale = 0
    for key, ids in scheduled.items():
        d = dt.date.fromisoformat(key)
        if d in locked:
            continue
        extra = len(ids) - len(desired.get(d, []))
        if extra > 0:
            stale += extra
            if d not in desired:
                hashes[key] = day_hashes_for(st.by_date, [d])[key]
    summary = {
        **_summary([window], window.end, mode="standalone", stale=stale),
        "days_sent": sent_days,
        "workouts_sent": sent,
    }
    db.save_coros_plan_link(
        user_id,
        plan_id=plan["id"],
        coros_plan_id=None,
        coros_start_date=None,
        total_weeks=None,
        window_end=window.end,
        day_hashes=hashes,
        last_summary=summary,
        partial=partial,
        mode="standalone",
        scheduled=scheduled,
    )
    return _result(user_id, summary, partial)


def _save(user_id, plan, st, coros_plan_id, start, total_weeks, end, tracked, windows, *, partial) -> dict[str, Any]:
    summary = _summary(windows, end, mode="plan", plan_start=start)
    db.save_coros_plan_link(
        user_id,
        plan_id=plan["id"],
        coros_plan_id=coros_plan_id,
        coros_start_date=start,
        total_weeks=total_weeks,
        window_end=end,
        day_hashes=day_hashes_for(st.by_date, tracked),
        last_summary=summary,
        partial=partial,
        mode="plan",
    )
    return _result(user_id, summary, partial)


def _result(user_id: int, summary: dict[str, Any], partial: bool) -> dict[str, Any]:
    link = db.get_coros_plan_link(user_id)
    return {
        "status": "partial" if partial else "sent",
        "summary": summary,
        "last_pushed_at": link["last_pushed_at"].isoformat() if link and link.get("last_pushed_at") else None,
    }


def _out_of_date(link: dict[str, Any], plan: dict[str, Any], today: dt.date) -> bool:
    if plan["id"] != link.get("plan_id") or _mode(plan) != link.get("mode"):
        return True
    st = _state(plan)
    stored = link.get("day_hashes") or {}
    if link.get("mode") == "standalone":
        end = window_end(today)
        runs = [d.date for d in standalone_window(st.by_date, today, end, "en").days]
        keys = {*runs, *(d for k in stored if today <= (d := dt.date.fromisoformat(k)) <= end)}
        current = day_hashes_for(st.by_date, sorted(keys))
        return any(stored.get(k) != v for k, v in current.items())
    start, end = link.get("coros_start_date") or today, link["window_end"]
    if st.race and st.race > end and st.race >= today:
        return True  # race moved past the COROS plan
    if today > end:
        return False
    dates, clear = _plan_dates(st, start, end, today, stored)
    current = day_hashes_for(st.by_date, sorted({*dates, *clear}))
    return any(stored.get(k) != v for k, v in current.items())


def push_status(user_id: int, today: dt.date) -> dict[str, Any]:
    connection = db.get_connection(user_id, PROVIDER)
    if not connection or connection.get("status") != "active":
        return {"connected": False}
    link = db.get_coros_plan_link(user_id)
    if not link:
        return {"connected": True, "last_pushed_at": None, "out_of_date": False, "partial": False, "last_summary": None}
    plan = db.get_active_plan(user_id)
    return {
        "connected": True,
        "last_pushed_at": link["last_pushed_at"].isoformat() if link.get("last_pushed_at") else None,
        "out_of_date": bool(plan) and _out_of_date(link, plan, today),
        "partial": bool(link.get("partial")),
        "last_summary": link.get("last_summary"),
    }
