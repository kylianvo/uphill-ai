from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text

from db import create_plan, engine, get_plan_workouts, save_workouts


def test_ready_event_rolls_back_with_workouts(auth_headers):
    from services.notification_store import finish_generation, start_generation

    plan = create_plan(auth_headers["user_id"], "Race", "2026-12-20", "finish", None, 12)
    request_id = str(uuid4())
    with engine.begin() as conn:
        start_generation(conn, dict(id=request_id, user_id=auth_headers["user_id"], plan_id=plan, coverage=1))
    with pytest.raises(RuntimeError):
        with engine.begin() as conn:
            save_workouts(
                plan,
                [
                    dict(
                        week_number=1,
                        day_of_week="Monday",
                        phase="Base",
                        title="Easy",
                        type="Easy",
                        duration_minutes=45,
                        target_zone="Z2",
                    )
                ],
                conn=conn,
            )
            finish_generation(conn, request_id, {"kind": "plan", "plan_id": plan}, datetime.now(UTC))
            raise RuntimeError()
    assert get_plan_workouts(plan) == []
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM notification_events")).scalar() == 0


def test_ready_result_preserves_target_week(auth_headers):
    from services.notification_store import finish_generation, start_generation

    plan = create_plan(auth_headers["user_id"], "Race", "2026-12-20", "finish", None, 12)
    request_id = str(uuid4())
    with engine.begin() as conn:
        start_generation(conn, dict(id=request_id, user_id=auth_headers["user_id"], plan_id=plan, coverage=4))
        finish_generation(conn, request_id, {"kind": "plan", "plan_id": plan}, datetime.now(UTC))
        target = conn.execute(text("SELECT destination FROM notification_events")).scalar()
    assert target["week_number"] == 4
    assert target["intent"] == "result"
