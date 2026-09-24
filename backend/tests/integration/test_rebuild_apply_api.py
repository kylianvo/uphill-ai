import asyncio
import datetime as dt
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import text

import db
from services import schedule_proposals, week_rebuild
from services.calendar_rules import DAYS
from tests.integration.calendar_helpers import add_workout, make_plan, server_today, this_monday

TODAY = server_today()


async def _gen(plan_id, user_profile, race_info, total_weeks=12, **kwargs):
    # Every day, so a current-week draft is never empty whatever weekday the suite runs on.
    wk = kwargs["target_week"]
    return [
        {
            "week_number": wk,
            "day_of_week": d,
            "phase": "Base",
            "title": "Rebuilt",
            "type": "Easy",
            "duration_minutes": 30,
            "target_zone": "Zone 2",
            "description": "n",
        }
        for d in DAYS
    ], "recreational"


@pytest.fixture(autouse=True)
def sync_spawn(monkeypatch):
    monkeypatch.setattr(week_rebuild, "spawn", lambda factory: asyncio.run(factory()))


def _proposal(uid, *, start=None, week=2, today=TODAY, generate=True):
    plan_id = make_plan(uid, start_date=start or this_monday())
    for wk in (1, 2, 3):
        add_workout(plan_id, wk, "Monday", title=f"W{wk} Mon")
        add_workout(plan_id, wk, "Tuesday", title=f"W{wk} Tue")
    thread = db.get_or_create_chat_thread(uid)
    mock = AsyncMock(side_effect=_gen) if generate else AsyncMock(side_effect=RuntimeError("x"))
    with patch("services.plan_generator.PlanGenerator.generate_plan_workouts", new=mock):
        out = week_rebuild.request_rebuild(
            user_id=uid,
            thread_id=thread["id"],
            plan_id=plan_id,
            today=today,
            request=week_rebuild.RebuildRequest(week_number=week, fatigue_level="hard"),
            rationale="r",
        )
    mid = db.append_chat_message(thread["id"], "assistant", "drafting")
    db.set_proposals_message_id(thread["id"], [out["proposal_id"]], mid)
    return out["proposal_id"], plan_id


def _apply(client, headers, pid):
    return client.post(
        f"/api/coach/chat/proposals/{pid}/apply", headers=headers, json={"client_today": TODAY.isoformat()}
    )


def test_apply_replaces_the_week_and_is_idempotent(client, auth_headers):
    uid = auth_headers["user_id"]
    pid, plan_id = _proposal(uid)
    first = _apply(client, auth_headers["headers"], pid)
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "applied" and first.json()["result"]["inserted"] == 7
    week2 = [w["title"] for w in first.json()["workouts"] if w["week_number"] == 2]
    assert week2 == ["Rebuilt"] * 7
    assert db.get_plan_by_id(plan_id)["athlete_tier"] == "recreational"
    second = _apply(client, auth_headers["headers"], pid)
    assert second.status_code == 200 and second.json()["result"] == first.json()["result"]


def test_poll_endpoint_returns_the_draft(client, auth_headers):
    uid = auth_headers["user_id"]
    pid, _ = _proposal(uid)
    body = client.get(f"/api/coach/chat/proposals/{pid}", headers=auth_headers["headers"]).json()
    assert body["kind"] == "rebuild" and body["status"] == "proposed" and body["diff"]["week"] == 2


def test_failed_draft_cannot_be_applied(client, auth_headers):
    uid = auth_headers["user_id"]
    pid, _ = _proposal(uid, generate=False)
    resp = _apply(client, auth_headers["headers"], pid)
    assert resp.status_code == 409 and resp.json()["code"] == "NOT_ready" and resp.json()["status"] == "failed"


def test_a_change_to_the_week_makes_it_stale_and_writes_nothing(client, auth_headers):
    uid = auth_headers["user_id"]
    pid, plan_id = _proposal(uid)
    tue = next(w for w in db.get_plan_workouts(plan_id) if w["title"] == "W2 Tue")
    client.patch(
        "/api/coach/workouts/log", headers=auth_headers["headers"], json={"workout_id": tue["id"], "is_completed": 1}
    )
    resp = _apply(client, auth_headers["headers"], pid)
    assert resp.status_code == 409 and resp.json() == {"status": "stale", "stale_reason": "STALE_changed"}
    assert "Rebuilt" not in {w["title"] for w in db.get_plan_workouts(plan_id)}


def test_rollover_makes_a_current_week_draft_stale(client, auth_headers):
    uid = auth_headers["user_id"]
    yesterday = TODAY - dt.timedelta(days=1)
    start = this_monday() - dt.timedelta(days=7)  # week 2 = this week
    cur_yesterday = (yesterday - start).days // 7 + 1
    pid, _ = _proposal(uid, start=start, week=cur_yesterday, today=yesterday)
    resp = _apply(client, auth_headers["headers"], pid)
    assert resp.status_code == 409
    assert resp.json()["stale_reason"] in ("STALE_rolled_over", "G3_past_target")


def test_orphaned_generating_row_reads_as_failed(client, auth_headers, monkeypatch):
    uid = auth_headers["user_id"]
    monkeypatch.setattr(week_rebuild, "spawn", lambda factory: None)  # job never runs
    pid, _ = _proposal(uid)
    with db.engine.connect() as conn:
        conn.execute(
            text("UPDATE chat_proposals SET created_at = NOW() - INTERVAL '10 minutes' WHERE id = :id"), {"id": pid}
        )
        conn.commit()
    body = client.get(f"/api/coach/chat/proposals/{pid}", headers=auth_headers["headers"]).json()
    assert body["status"] == "failed" and body["stale_reason"] == "generation_orphaned"
    thread = client.get("/api/coach/chat/thread", headers=auth_headers["headers"]).json()
    assert thread["proposals"][str(pid)]["status"] == "failed"
    assert thread["proposals"][str(pid)]["kind"] == "rebuild"


def test_discard_while_generating(client, auth_headers, monkeypatch):
    uid = auth_headers["user_id"]
    monkeypatch.setattr(week_rebuild, "spawn", lambda factory: None)
    pid, _ = _proposal(uid)
    resp = client.post(f"/api/coach/chat/proposals/{pid}/discard", headers=auth_headers["headers"])
    assert resp.json() == {"status": "discarded"}


def test_other_user_gets_404(client, auth_headers):
    uid = auth_headers["user_id"]
    pid, _ = _proposal(uid)
    other = client.post("/api/auth/mock-login", json={"email": "rebuild-intruder@uphill.ai"}).json()
    headers = {"Authorization": f"Bearer {other['session_token']}"}
    assert client.get(f"/api/coach/chat/proposals/{pid}", headers=headers).status_code == 404
    assert client.post(f"/api/coach/chat/proposals/{pid}/apply", headers=headers, json={}).status_code == 404


def test_concurrent_applies_write_once(auth_headers):
    uid = auth_headers["user_id"]
    pid, plan_id = _proposal(uid)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: schedule_proposals.apply_proposal(uid, pid, TODAY.isoformat()), range(2)))
    assert [r[0] for r in results] == [200, 200]
    assert sum(1 for w in db.get_plan_workouts(plan_id) if w["title"] == "Rebuilt") == 7
