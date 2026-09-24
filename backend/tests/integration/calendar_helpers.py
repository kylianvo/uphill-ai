"""Raw fixtures for calendar/proposal integration tests. Dates are relative to
the server's UTC today so tests don't rot."""

import datetime as dt

from sqlalchemy import text

import db


def server_today() -> dt.date:
    return dt.datetime.now(dt.UTC).date()


def this_monday() -> dt.date:
    today = server_today()
    return today - dt.timedelta(days=today.weekday())


def make_plan(user_id: int, *, start_date: dt.date | str | None, total_weeks: int = 12) -> int:
    return db.create_plan(
        user_id=user_id,
        race_name="Proposal Test 50K",
        race_date="2027-06-01",
        goal_type="finish",
        target_time_hours=None,
        total_weeks=total_weeks,
        start_date=str(start_date) if start_date else None,
        plan_status="active",
    )


def add_workout(
    plan_id: int,
    week: int,
    day: str,
    *,
    title: str = "Easy Run",
    type_: str = "Easy",
    zone: str = "Zone 2",
    minutes: float = 45,
    completed: int = 0,
    missed: int = 0,
    approved: bool = True,
    slot: str = "main",
) -> int:
    with db.engine.connect() as conn:
        wid = conn.execute(
            text(
                """
                INSERT INTO workouts (plan_id, week_number, day_of_week, phase, title, type,
                    duration_minutes, target_zone, is_completed, is_missed, session_slot, approved_at)
                VALUES (:pid, :wk, :day, 'base', :title, :type, :mins, :zone, :done, :missed, :slot,
                    CASE WHEN :approved THEN NOW() ELSE NULL END)
                RETURNING id
                """
            ),
            {
                "pid": plan_id,
                "wk": week,
                "day": day,
                "title": title,
                "type": type_,
                "mins": minutes,
                "zone": zone,
                "done": completed,
                "missed": missed,
                "slot": slot,
                "approved": approved,
            },
        ).scalar()
        conn.commit()
    return wid


def match_activity(user_id: int, workout_id: int) -> int:
    with db.engine.connect() as conn:
        aid = conn.execute(
            text(
                """
                INSERT INTO activities (user_id, source_provider, activity_type, start_time,
                    duration_seconds, matched_workout_id)
                VALUES (:uid, 'manual', 'run', NOW(), 2700, :wid)
                RETURNING id
                """
            ),
            {"uid": user_id, "wid": workout_id},
        ).scalar()
        conn.commit()
    return aid


def link_coach(athlete_id: int) -> None:
    coach = db.create_or_get_user("coach-4a@uphill.ai", "Coach 4a", "mock", "mock-coach-4a")
    with db.engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO coach_athletes (coach_id, athlete_id, status, responded_at) "
                "VALUES (:c, :a, 'active', NOW())"
            ),
            {"c": coach["id"], "a": athlete_id},
        )
        conn.commit()
