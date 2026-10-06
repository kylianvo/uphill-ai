"""Seeds a LOCAL-ONLY preview athlete with plans around today, for the native
iOS app's screenshots, fixtures and UI tests.

Usage, from backend/, against the local Docker database only:
    DATABASE_URL=postgresql://uphill:uphill_secret@localhost:5433/uphill_ai python scripts/seed_ios_preview.py

Re-running replaces the preview athlete's plans, and the coach's roster rows and notes.
No other user is touched. The password is a local test credential, also used by
ios-native/UphillAIUITests (the coach and invitee accounts use the same one).

Coach data for the native coach screens: COACH_EMAIL coaches the preview athlete
(one workout awaiting approval, one draft plan, a few notes) and has a pending
invite out to INVITEE_EMAIL, so /api/coaching/{overview,roster,my-invites,...} all
return real, non-empty responses.
"""

import datetime
import os
import sys
from urllib.parse import urlparse

EMAIL = "ios-preview@uphill.ai"
PASSWORD = "uphill-preview-1"
COACH_EMAIL = "ios-coach@uphill.ai"
INVITEE_EMAIL = "ios-invitee@uphill.ai"

# Must run before importing db: db builds its engine from DATABASE_URL at import time.
_host = urlparse(os.environ.get("DATABASE_URL", "")).hostname
if _host not in {"localhost", "127.0.0.1"}:
    sys.exit(f"Refusing to seed database host {_host!r}: local databases only.")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402

import db  # noqa: E402
from services.auth_service import hash_password  # noqa: E402

# (day, title, type, minutes, km, zone, gain_m, priority)
WEEK = [
    ("Monday", "Rest Day", "Rest", 0, None, "Rest", 0, False),
    ("Tuesday", "Hill Repeats", "Hill Repeats", 60, 8.0, "Z4", 350, True),
    ("Wednesday", "Easy Run", "Easy Run", 45, 7.0, "Z2", 80, False),
    ("Thursday", "Rest Day", "Rest", 0, None, "Rest", 0, False),
    ("Friday", "Easy Run + Strides", "Easy Run", 40, 6.5, "Z2", 40, False),
    ("Saturday", "Long Run", "Long Run", 120, 18.0, "Z2", 600, True),
    ("Sunday", "Recovery Jog", "Recovery Run", 30, 4.5, "Z1", 20, False),
]


def _workouts(weeks):
    out = []
    for week in weeks:
        for day, title, wtype, minutes, km, zone, gain, _ in WEEK:
            out.append(
                {
                    "week_number": week,
                    "day_of_week": day,
                    "phase": "Base",
                    "title": title,
                    "type": wtype,
                    "duration_minutes": minutes,
                    "distance_km": km,
                    "target_zone": zone,
                    "target_hr_range": None if wtype == "Rest" else "130-145 bpm",
                    "target_pace": None if wtype == "Rest" else "6:10-6:50 /km",
                    "elevation_gain_m": gain,
                    "description": "Rest and recover." if wtype == "Rest" else f"{title}: keep it controlled.",
                    "fueling_tip": None if minutes < 90 else "Take 40 g carbs per hour after the first 45 minutes.",
                }
            )
    return out


def _ensure_user(email, name):
    user = db.get_user_by_email(email)
    if not user:
        return db.create_user_with_password(email=email, name=name, password_hash=hash_password(PASSWORD))
    db.set_user_password(user["id"], hash_password(PASSWORD))
    return user


def _seed_coach(athlete_id, active_plan_id, start, total_weeks):
    coach_id = _ensure_user(COACH_EMAIL, "Coach Kylian")["id"]
    invitee_id = _ensure_user(INVITEE_EMAIL, "Pending Invitee")["id"]
    with db.engine.connect() as conn:
        conn.execute(
            text("UPDATE users SET is_coach = TRUE, onboarding_complete = TRUE WHERE id = :c"), {"c": coach_id}
        )
        conn.execute(text("UPDATE users SET onboarding_complete = TRUE WHERE id = :i"), {"i": invitee_id})
        # 42 km/week lands the athlete in the "intermediate" level; the rest fills the coach's profile view.
        conn.execute(
            text(
                "UPDATE users SET current_weekly_km = 42, age = 34, max_hr = 188, resting_hr = 52, "
                "aet_hr = 151, ant_hr = 172, long_run_day = 'Saturday', "
                'preferred_run_days = \'["Tuesday", "Wednesday", "Friday", "Saturday", "Sunday"]\', '
                "injury_history = 'Mild Achilles tightness after long technical descents; eccentric calf drops help.', "
                "athlete_notes = 'Targeting a strong finish at VMM 42K. Wants better uphill pacing and fueling.' "
                "WHERE id = :a"
            ),
            {"a": athlete_id},
        )
        conn.execute(text("DELETE FROM coach_notes WHERE coach_id = :c"), {"c": coach_id})
        conn.execute(text("DELETE FROM coach_athletes WHERE coach_id = :c"), {"c": coach_id})
        conn.execute(
            text(
                "INSERT INTO coach_athletes (coach_id, athlete_id, status, invited_at, responded_at) "
                "VALUES (:c, :a, 'active', NOW() - INTERVAL '30 days', NOW() - INTERVAL '29 days')"
            ),
            {"c": coach_id, "a": athlete_id},
        )
        conn.execute(
            text(
                "INSERT INTO coach_athletes (coach_id, athlete_id, status, invited_at) VALUES (:c, :i, 'invited', NOW())"
            ),
            {"c": coach_id, "i": invitee_id},
        )
        # A coach-added workout the coach still has to approve (approved_at NULL = pending).
        pending_id = conn.execute(
            text(
                "UPDATE workouts SET approved_at = NULL, source = 'coach', last_edited_by_user_id = :c "
                "WHERE plan_id = :p AND week_number = 3 AND day_of_week = 'Tuesday' RETURNING id"
            ),
            {"c": coach_id, "p": active_plan_id},
        ).scalar()
        conn.commit()

    # A draft plan the coach has not released yet: its workouts are all pending.
    draft_id = db.create_plan(
        user_id=athlete_id,
        race_name="Dalat Ultra Trail 50K",
        race_date=(start + datetime.timedelta(days=(total_weeks + 10) * 7 + 5)).isoformat(),
        goal_type="finish",
        target_time_hours=None,
        total_weeks=16,
        course_distance_km=50.0,
        course_elevation_gain_m=2800.0,
        start_date=(start + datetime.timedelta(days=total_weeks * 7)).isoformat(),
        created_by_user_id=coach_id,
        plan_status="draft",
    )
    db.save_workouts(draft_id, _workouts([1]), auto_approve=False)

    db.create_coach_note(
        coach_id, athlete_id, "general", None, "Knees felt fine after the long run. Keep the Saturday climbs steady."
    )
    db.create_coach_note(
        coach_id, athlete_id, "plan", active_plan_id, "Hold the weekly volume until the Friday run is back on."
    )
    db.create_coach_note(
        coach_id,
        athlete_id,
        "workout",
        pending_id,
        "Added an extra hill session for week 3. Approve once the legs feel fresh.",
    )
    print(
        f"Seeded coach {COACH_EMAIL} (user {coach_id}): roster athlete {athlete_id}, draft plan {draft_id}, pending workout {pending_id}, invitee {INVITEE_EMAIL}."
    )


def main():
    today = datetime.date.today()
    this_monday = today - datetime.timedelta(days=today.weekday())
    start = this_monday - datetime.timedelta(days=7)  # today falls in week 2
    total_weeks = 12
    race = start + datetime.timedelta(days=(total_weeks - 1) * 7 + 5)  # Saturday of week 12

    user = db.get_user_by_email(EMAIL)
    if not user:
        user = db.create_user_with_password(email=EMAIL, name="Preview Runner", password_hash=hash_password(PASSWORD))
    else:
        db.set_user_password(user["id"], hash_password(PASSWORD))
    uid = user["id"]

    with db.engine.connect() as conn:
        conn.execute(text("DELETE FROM plans WHERE user_id = :u"), {"u": uid})
        conn.execute(text("UPDATE users SET onboarding_complete = TRUE WHERE id = :u"), {"u": uid})
        conn.commit()

    older = db.create_plan(
        user_id=uid,
        race_name="Sky Race 25K",
        race_date=(race - datetime.timedelta(days=70)).isoformat(),
        goal_type="finish",
        target_time_hours=None,
        total_weeks=8,
        start_date=(start - datetime.timedelta(days=28)).isoformat(),
    )
    db.save_workouts(older, _workouts([1]))

    plan_id = db.create_plan(
        user_id=uid,
        race_name="Vietnam Mountain Marathon 42K",
        race_date=race.isoformat(),
        goal_type="time",
        target_time_hours=6.5,
        total_weeks=total_weeks,
        course_distance_km=42.0,
        course_elevation_gain_m=2400.0,
        start_date=start.isoformat(),
    )
    db.save_workouts(plan_id, _workouts([1, 2, 3]))
    db.set_plan_active(uid, plan_id)

    priority_titles = [title for _, title, *_rest, prio in WEEK if prio]
    with db.engine.connect() as conn:
        conn.execute(
            text("UPDATE workouts SET is_priority = TRUE WHERE plan_id = :p AND title = ANY(:t)"),
            {"p": plan_id, "t": priority_titles},
        )
        # Week 1: everything done except Friday, which was missed.
        conn.execute(
            text(
                "UPDATE workouts SET is_completed = 1 WHERE plan_id = :p AND week_number = 1 "
                "AND type <> 'Rest' AND day_of_week <> 'Friday'"
            ),
            {"p": plan_id},
        )
        conn.execute(
            text("UPDATE workouts SET is_missed = 1 WHERE plan_id = :p AND week_number = 1 AND day_of_week = 'Friday'"),
            {"p": plan_id},
        )
        # Week 2 (this week): days before today are done.
        done_days = [WEEK[i][0] for i in range(today.weekday())]
        if done_days:
            conn.execute(
                text(
                    "UPDATE workouts SET is_completed = 1, rpe = 5 WHERE plan_id = :p AND week_number = 2 "
                    "AND type <> 'Rest' AND day_of_week = ANY(:d)"
                ),
                {"p": plan_id, "d": done_days},
            )
        conn.commit()

    print(f"Seeded {EMAIL} (user {uid}): active plan {plan_id}, older plan {older}. Week 1 starts {start}.")
    _seed_coach(uid, plan_id, start, total_weeks)


if __name__ == "__main__":
    main()
