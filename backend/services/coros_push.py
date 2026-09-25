"""Send the next ~4 weeks of an athlete's Uphill plan to COROS (COROS push, phase 1).

The mirror is ONE COROS training plan per athlete, updated in place: standalone
scheduled workouts can't be moved or deleted over MCP, but updateTrainingPlan
replaces whole days (a rest entry clears one). Lifecycle per push:

- no live linked plan  -> createTrainingPlan starting today, 4 weeks
- live plan, window fits in <= 16 weeks -> updateTrainingPlan (extend totalWeeks if needed)
- window would exceed 16 weeks -> shorten the old plan to end this Sunday, and
  create a new 4-week plan from next Monday (rollover)

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
    WINDOW_WEEKS,
    PushWindow,
    build_window,
    course_list,
    day_hashes,
    has_run,
    monday_of,
    natural_weeks,
    periodization,
    rows_by_date,
    window_end,
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


def _summary(windows: list[PushWindow], end: dt.date) -> dict[str, Any]:
    return {
        "days_sent": sum(len(w.days) for w in windows),
        "workouts_sent": sum(1 for w in windows for d in w.days for c in d.courses if c["sportType"] != SPORT_REST),
        "left_in_uphill": sum(w.left_in_uphill for w in windows),
        "locked_days": sum(len(w.locked_dates) for w in windows),
        "invalid": sum(w.invalid for w in windows),
        "window_end": end.isoformat(),
    }


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
                **{k: v for k, v in result["summary"].items() if k != "window_end"},
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


async def _push_locked(user_id, plan, connection, today, lang, client_factory) -> dict[str, Any]:
    by_date = rows_by_date(plan, db.get_plan_workouts_with_match(plan["id"]))
    window = build_window(by_date, today, window_end(today), lang)
    if not has_run(window, window.start, window.end):
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
        return await _sync(client, user_id, plan, by_date, window, today, lang)
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


async def _sync(client, user_id, plan, by_date, window, today, lang) -> dict[str, Any]:
    name = plan_name(plan)
    records = await _library(client)
    link = db.get_coros_plan_link(user_id)
    target = _live(records, plan_id=link["coros_plan_id"] if link else None) or _live(records, name=name)
    if target is None:
        return await _create(client, user_id, plan, by_date, window, today, lang, name)
    needed = natural_weeks(target.start, window.end)
    if needed <= MAX_PLAN_WEEKS:
        return await _update(client, user_id, plan, by_date, window, today, target, needed)
    return await _rollover(client, user_id, plan, by_date, today, lang, target, name)


async def _create_plan(client, by_date, window, anchor, lang, name) -> str:
    """createTrainingPlan for `window` anchored at `anchor`; returns the new COROS plan id."""
    if not has_run(window, monday_of(window.end), window.end):
        raise PushError("PLAN_too_short", 409, {"weeks": WINDOW_WEEKS})
    text = await client.call_tool(
        "createTrainingPlan",
        {
            "planInfo": {
                "planName": name,
                "planOverview": _OVERVIEW.get(lang, _OVERVIEW["en"]),
                "planStartDate": ymd(anchor),
                "totalWeeks": WINDOW_WEEKS,
            },
            "courseList": course_list(window, anchor),
            "phaseInfo": {"periodization": periodization(by_date, anchor, WINDOW_WEEKS)},
        },
    )
    new_id = created_plan_id(text, await _library(client), name)
    if new_id is None:
        # Created, but its id can't be read back; the next push adopts it by name.
        raise PushError("COROS_unavailable", 504)
    return new_id


async def _create(client, user_id, plan, by_date, window, today, lang, name) -> dict[str, Any]:
    new_id = await _create_plan(client, by_date, window, today, lang, name)
    return _save(user_id, plan, new_id, today, WINDOW_WEEKS, window.end, by_date, today, [window], partial=False)


async def _update(client, user_id, plan, by_date, window, today, target, needed) -> dict[str, Any]:
    total = target.weeks or needed
    args: dict[str, Any] = {"planInfo": {"planId": target.plan_id}, "courseList": course_list(window, target.start)}
    if needed > total:
        args["planInfo"]["totalWeeks"] = needed
        args["phaseInfo"] = {"periodization": periodization(by_date, target.start, needed)}
        total = needed
    await client.call_tool("updateTrainingPlan", args)
    return _save(
        user_id, plan, target.plan_id, target.start, total, window.end, by_date, today, [window], partial=False
    )


async def _rollover(client, user_id, plan, by_date, today, lang, target, name) -> dict[str, Any]:
    this_sunday = monday_of(today) + dt.timedelta(days=6)
    keep = natural_weeks(target.start, this_sunday)
    this_week = build_window(by_date, today, this_sunday, lang)
    args: dict[str, Any] = {
        "planInfo": {"planId": target.plan_id, "totalWeeks": keep},
        "phaseInfo": {"periodization": periodization(by_date, target.start, keep)},
    }
    courses = course_list(this_week, target.start)
    if courses:
        args["courseList"] = courses
    await client.call_tool("updateTrainingPlan", args)  # failure here: nothing changed

    next_monday = this_sunday + dt.timedelta(days=1)
    ahead = build_window(by_date, next_monday, window_end(next_monday), lang)
    try:
        new_id = await _create_plan(client, by_date, ahead, next_monday, lang, name)
    except (McpError, PushError):
        return _save(
            user_id, plan, target.plan_id, target.start, keep, this_sunday, by_date, today, [this_week], partial=True
        )
    return _save(
        user_id, plan, new_id, next_monday, WINDOW_WEEKS, ahead.end, by_date, today, [this_week, ahead], partial=False
    )


def _save(user_id, plan, coros_plan_id, start, total_weeks, end, by_date, today, windows, *, partial) -> dict[str, Any]:
    summary = _summary(windows, end)
    db.save_coros_plan_link(
        user_id,
        plan_id=plan["id"],
        coros_plan_id=coros_plan_id,
        coros_start_date=start,
        total_weeks=total_weeks,
        window_end=end,
        day_hashes=day_hashes(by_date, today, end),
        last_summary=summary,
        partial=partial,
    )
    link = db.get_coros_plan_link(user_id)
    return {
        "status": "partial" if partial else "sent",
        "summary": summary,
        "last_pushed_at": link["last_pushed_at"].isoformat() if link and link.get("last_pushed_at") else None,
    }


def push_status(user_id: int, today: dt.date) -> dict[str, Any]:
    connection = db.get_connection(user_id, PROVIDER)
    if not connection or connection.get("status") != "active":
        return {"connected": False}
    link = db.get_coros_plan_link(user_id)
    if not link:
        return {"connected": True, "last_pushed_at": None, "out_of_date": False, "partial": False, "last_summary": None}
    plan = db.get_active_plan(user_id)
    out_of_date = False
    if plan and plan["id"] != link.get("plan_id"):
        out_of_date = True
    elif plan and today <= link["window_end"]:
        current = day_hashes(rows_by_date(plan, db.get_plan_workouts_with_match(plan["id"])), today, link["window_end"])
        stored = link.get("day_hashes") or {}
        out_of_date = any(stored.get(k) != v for k, v in current.items())
    return {
        "connected": True,
        "last_pushed_at": link["last_pushed_at"].isoformat() if link.get("last_pushed_at") else None,
        "out_of_date": out_of_date,
        "partial": bool(link.get("partial")),
        "last_summary": link.get("last_summary"),
    }
