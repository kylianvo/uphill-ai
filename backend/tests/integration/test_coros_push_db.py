"""coros_plan_links / coros_push_usage schema and helpers. Needs a live Postgres."""

import datetime as dt

import pytest
from sqlalchemy import text

import db
from db import engine


def _user(client) -> int:
    resp = client.post("/api/auth/mock-login", json={"email": "coros-push@uphill.ai"})
    assert resp.status_code == 200, resp.text
    return resp.json()["user"]["id"]


def _columns(table: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = :t"), {"t": table}
        ).fetchall()
    return {r[0] for r in rows}


def test_tables_have_expected_columns():
    assert {
        "user_id",
        "plan_id",
        "coros_plan_id",
        "coros_start_date",
        "total_weeks",
        "window_end",
        "day_hashes",
        "mode",
        "scheduled",
        "last_pushed_at",
        "last_summary",
        "partial",
        "created_at",
    } <= _columns("coros_plan_links")
    assert {"user_id", "usage_date", "pushes"} <= _columns("coros_push_usage")


def test_save_and_get_link_roundtrip(client):
    uid = _user(client)
    assert db.get_coros_plan_link(uid) is None
    db.save_coros_plan_link(
        uid,
        plan_id=None,
        coros_plan_id="467917012245594132",
        coros_start_date=dt.date(2027, 4, 7),
        total_weeks=4,
        window_end=dt.date(2027, 5, 2),
        day_hashes={"2027-04-07": "abc"},
        last_summary={"courses": 3},
        partial=False,
    )
    link = db.get_coros_plan_link(uid)
    assert link["coros_plan_id"] == "467917012245594132"
    assert link["coros_start_date"] == dt.date(2027, 4, 7)
    assert link["window_end"] == dt.date(2027, 5, 2)
    assert link["day_hashes"] == {"2027-04-07": "abc"}
    assert link["last_summary"] == {"courses": 3}
    assert link["last_pushed_at"] is not None

    db.save_coros_plan_link(
        uid,
        plan_id=None,
        coros_plan_id="99",
        coros_start_date=dt.date(2027, 4, 7),
        total_weeks=5,
        window_end=dt.date(2027, 5, 9),
        day_hashes={},
        last_summary={},
        partial=True,
    )
    link = db.get_coros_plan_link(uid)
    assert (link["coros_plan_id"], link["total_weeks"], link["partial"]) == ("99", 5, True)
    assert (link["mode"], link["scheduled"]) == ("plan", {})


def test_standalone_link_has_no_plan_fields(client):
    uid = _user(client)
    db.save_coros_plan_link(
        uid,
        plan_id=None,
        coros_plan_id=None,
        coros_start_date=None,
        total_weeks=None,
        window_end=dt.date(2027, 5, 2),
        day_hashes={"2027-04-08": "h"},
        last_summary={},
        partial=False,
        mode="standalone",
        scheduled={"2027-04-08": ["123", "456"]},
    )
    link = db.get_coros_plan_link(uid)
    assert (link["mode"], link["coros_plan_id"], link["total_weeks"]) == ("standalone", None, None)
    assert link["scheduled"] == {"2027-04-08": ["123", "456"]}


def test_claim_push_slot_enforces_daily_limit(client):
    uid = _user(client)
    day = dt.date(2027, 4, 7)
    assert [db.claim_coros_push_slot(uid, day, 2) for _ in range(3)] == [True, True, False]
    assert db.claim_coros_push_slot(uid, day + dt.timedelta(days=1), 2) is True


def test_push_lock_is_exclusive_per_user(client):
    uid = _user(client)
    with db.coros_push_lock(uid):
        with pytest.raises(db.CorosPushInProgressError):
            with db.coros_push_lock(uid):
                pass
    with db.coros_push_lock(uid):  # released after exit
        pass


def test_disconnect_deletes_link_and_usage(client):
    uid = _user(client)
    db.save_coros_plan_link(
        uid,
        plan_id=None,
        coros_plan_id="1",
        coros_start_date=dt.date(2027, 4, 7),
        total_weeks=4,
        window_end=dt.date(2027, 5, 2),
        day_hashes={},
        last_summary={},
        partial=False,
    )
    db.claim_coros_push_slot(uid, dt.date(2027, 4, 7), 10)
    db.delete_provider_data(uid, "coros")
    assert db.get_coros_plan_link(uid) is None
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM coros_push_usage WHERE user_id = :u"), {"u": uid}).scalar() == 0
