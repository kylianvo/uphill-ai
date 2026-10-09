"""Deterministic LOCAL-ONLY landing preview; replaces only its fictional user.

Run from backend/ with DATABASE_URL pointing to the local Docker Uphill database
on localhost (5433 normally, or 5543 for this isolated capture session).
Uses existing schema/helpers; never calls Gemini or COROS.
The plan is frozen for the 9 October 2026 capture date (week 2), with the
user-confirmed Elephant 50 course figures, not the older KB course figures.
Completed sessions and the COROS-imported activity are explicitly test fixtures.
The local credential below must never appear in marketing assets or docs.
"""

import datetime as dt
import os
import sys
from urllib.parse import urlparse

EMAIL = "landing-preview@uphill.ai"
PASSWORD = "uphill-landing-local-2026"
RACE = "Vietnam Highlands Trail by UTMB — Elephant 50"
RACE_DATE = dt.date(2027, 1, 9)
START = RACE_DATE - dt.timedelta(days=14 * 7 + 5)
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
RUN_DAYS = ["Tuesday", "Wednesday", "Friday", "Saturday", "Sunday"]

# Guard before db import: its engine reads DATABASE_URL at import time.
_url = urlparse(os.environ.get("DATABASE_URL", ""))
if _url.hostname not in {"localhost", "127.0.0.1"}:
    sys.exit("Refusing seed: local database hosts only.")
if _url.path != "/uphill_ai":
    sys.exit("Refusing seed: expected the dedicated uphill_ai database.")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402

import db  # noqa: E402
from services.auth_service import hash_password  # noqa: E402
from services.plan_generator import PlanGenerator  # noqa: E402
from services.providers.base import CanonicalActivity  # noqa: E402

# Total running km / vertical metres. Every fourth week steps back; the last
# two weeks taper. Race-day distance/vertical are additional in the last week.
WEEKS = [
    (45, 650),
    (47, 750),
    (50, 850),
    (38, 500),
    (50, 950),
    (52, 1100),
    (55, 1300),
    (42, 800),
    (56, 1500),
    (58, 1700),
    (60, 2000),
    (46, 1200),
    (58, 1900),
    (34, 650),
    (12, 180),
]


def workouts():
    rows = []
    for week, (km, gain) in enumerate(WEEKS, 1):
        phase = "Base" if week <= 5 else "Build" if week <= 10 else "Peak" if week <= 13 else "Taper"
        back_to_back = phase in {"Build", "Peak"}
        shares = [0.18, 0.18, 0.14, 0.36, 0.14] if not back_to_back else [0.16, 0.16, 0.12, 0.36, 0.20]
        distances = [round(km * share, 1) for share in shares]
        distances[-1] = round(km - sum(distances[:-1]), 1)
        elevations = [round(gain * share) for share in [0.25, 0.08, 0.04, 0.50, 0.13]]
        elevations[-1] = gain - sum(elevations[:-1])
        if week == 15:
            distances = [4, 4, 4, 0, 0]
            elevations = [80, 50, 50, 0, 0]
        for day in DAYS:
            row = dict(week_number=week, day_of_week=day, phase=phase, session_slot="main", is_priority=False)
            if day in {"Monday", "Thursday"} or (week == 15 and day in {"Saturday", "Sunday"}):
                row.update(
                    title="Rest & mobility",
                    type="Rest",
                    duration_minutes=0,
                    distance_km=None,
                    target_zone="Rest",
                    elevation_gain_m=0,
                    description="Example plan. Rest from running. Optional gentle mobility; prioritise sleep and recovery.",
                )
            else:
                index = RUN_DAYS.index(day)
                distance, elevation = distances[index], elevations[index]
                hill = day == "Tuesday"
                long = day == "Saturday" or (day == "Sunday" and back_to_back)
                recovery = day == "Sunday" and not back_to_back
                minutes = round(distance * (8.5 if long else 7.8 if hill else 7.0) / 5) * 5
                title = (
                    ("Aerobic hill circuit" if phase == "Base" else "Uphill muscular endurance")
                    if hill
                    else (
                        "Long trail run"
                        if day == "Saturday"
                        else "Back-to-back trail run"
                        if long
                        else "Recovery jog"
                        if recovery
                        else "Easy aerobic run"
                    )
                )
                zone = "Zone 1" if recovery else "Zone 2"
                main = minutes - 20
                process = f"Warm up 10 min easy → {main} min steady {zone} → Cool down 10 min easy"
                if hill and minutes >= 40:
                    # Four controlled climbs, with recoveries included in the
                    # main duration. Muscular load, not an anaerobic interval day.
                    climb = max(3, (main - 12) // 4)
                    easy = main - climb * 4
                    process = (
                        f"Warm up 10 min easy → 4 × {climb} min uphill at controlled Zone 2 "
                        f"→ {easy} min easy walking or jogging between climbs → Cool down 10 min easy"
                    )
                row.update(
                    title=title,
                    type="Muscular Endurance" if hill else "Long Run" if long else "Recovery" if recovery else "Easy",
                    duration_minutes=minutes,
                    distance_km=distance,
                    elevation_gain_m=elevation,
                    target_zone=zone,
                    target_hr_range="120-135 bpm" if recovery else "136-151 bpm",
                    target_pace="7:00-8:00 /km" if recovery else "6:10-7:10 /km",
                    grade_percent=round(elevation / (distance * 10), 1),
                    is_priority=hill or day == "Saturday",
                    description=(
                        f"Process: {process}. / Overall: {title} in this fictional example plan for Đà Lạt. "
                        "Pace is a flat-ground reference; walk steep climbs to hold the target effort. / "
                        f"Reason: {'Step-back week: absorb the previous three weeks.' if week % 4 == 0 else 'Reduce fatigue before race day.' if phase == 'Taper' else 'Build aerobic durability for sustained mountain climbing.'} / "
                        "Benefit: Practise economical climbing and relaxed movement on tired legs. / "
                        "Warning: Avoid hard downhill efforts; stop for pain or unusual fatigue."
                    ),
                    fueling_tip=(
                        "Example practice: 40–60 g carbohydrate per hour, starting early; carry fluid and adjust to heat and thirst. Test race foods in training."
                        if minutes > 90
                        else None
                    ),
                )
                if hill:
                    row["treadmill_incline"], row["treadmill_speed"] = PlanGenerator.resolve_treadmill_settings(
                        {**row, "treadmill_incline": 8},
                        row["target_pace"],
                        max_incline=15,
                    )
            if week == 15 and day == "Saturday":
                row.update(
                    title="Elephant 50 — example race goal",
                    type="Race",
                    duration_minutes=660,
                    distance_km=56.4,
                    elevation_gain_m=2946,
                    target_zone="Zone 1–2",
                    target_hr_range="120-151 bpm",
                    target_pace=None,
                    is_priority=True,
                    description="Example goal, not a recorded result. Start conservatively, hike steep climbs and manage effort through Đà Lạt's sustained descents. Course figures and date supplied by the user; 11 h is a fictional training target.",
                    fueling_tip="Use the carbohydrate and fluid strategy rehearsed in long runs; never try a new product on race day.",
                )
            rows.append(row)
    return rows


def main():
    user = db.get_user_by_email(EMAIL)
    if user is None:
        user = db.create_user_with_password(EMAIL, "Minh Trail", hash_password(PASSWORD))
    else:
        db.set_user_password(user["id"], hash_password(PASSWORD))
    uid = user["id"]
    # Only this script's exact email is selected; no schema initialisation or
    # shared preview/coach accounts are modified.
    with db.engine.begin() as conn:
        plan_ids = conn.execute(text("SELECT id FROM plans WHERE user_id = :u"), {"u": uid}).scalars().all()
        conn.execute(text("DELETE FROM activities WHERE user_id = :u"), {"u": uid})
        conn.execute(text("UPDATE users SET name = 'Minh Trail' WHERE id = :u"), {"u": uid})
    for plan_id in plan_ids:
        db.delete_plan(plan_id, uid)
    db.update_onboarding_profile(
        uid,
        {
            "dob": "1991-06-12",
            "age": 35,
            "gender": "male",
            "height_cm": 172,
            "weight_kg": 65,
            "goal_type": "time",
            "injury_history": "Fictional example athlete; no current injury.",
            "preferred_run_days": RUN_DAYS,
            "long_run_day": "Saturday",
            "days_per_week": 5,
            "current_weekly_km": 45,
            "max_hr": 188,
            "resting_hr": 52,
            "aet_hr": 151,
            "ant_hr": 172,
            "zone2_pace_min": "6:10",
            "zone2_pace_max": "7:10",
            "threshold_source": "manual",
        },
    )
    db.mark_onboarding_complete(uid)
    plan_id = db.create_plan(
        user_id=uid,
        race_name=RACE,
        race_date=RACE_DATE.isoformat(),
        goal_type="time",
        target_time_hours=11,
        total_weeks=15,
        course_distance_km=56.4,
        course_elevation_gain_m=2946,
        preferred_run_days=RUN_DAYS,
        long_run_day="Saturday",
        days_per_week=5,
        start_date=START.isoformat(),
        use_treadmill=True,
        training_environment="trail",
        mountain_days=["Saturday", "Sunday"],
        treadmill_max_incline=15,
        athlete_notes="FICTIONAL EXAMPLE PLAN for landing screenshots. Intermediate runner, 45 km/week. Đà Lạt race target is illustrative, not a result. No actual watch was connected or contacted.",
    )
    db.save_workouts(plan_id, workouts())
    db.set_plan_active(uid, plan_id)
    for row in db.get_plan_workouts(plan_id):
        if row["type"] == "Rest":
            continue
        if row["week_number"] == 1:
            db.update_workout_log(
                row["id"],
                is_completed=int(row["day_of_week"] != "Friday"),
                is_missed=int(row["day_of_week"] == "Friday"),
                rpe=3 if row["day_of_week"] != "Friday" else None,
                notes="Local example completion; not an athlete result.",
            )
        elif row["week_number"] == 2 and row["day_of_week"] in {"Tuesday", "Wednesday"}:
            db.update_workout_log(row["id"], is_completed=1, rpe=3, notes="Local example completion.")
        if row["week_number"] == 2 and row["day_of_week"] == "Wednesday":
            start = dt.datetime.combine(
                START + dt.timedelta(days=9), dt.time(6, 30), dt.timezone(dt.timedelta(hours=7))
            )
            activity_id = db.upsert_activity(
                uid,
                CanonicalActivity(
                    external_id="landing-preview-example-coros",
                    provider="coros",
                    activity_type="run",
                    start_time=start,
                    end_time=start + dt.timedelta(minutes=row["duration_minutes"]),
                    duration_seconds=row["duration_minutes"] * 60,
                    distance_km=row["distance_km"],
                    elevation_gain_m=row["elevation_gain_m"],
                    avg_hr=143,
                    max_hr=150,
                    device_model="COROS — local example",
                    avg_pace_sec_per_km=row["duration_minutes"] * 60 / row["distance_km"],
                ),
            )
            db.save_match(activity_id, row["id"], 1.0, "manual", {"example": True, "source": "local landing fixture"})
    print("Seeded fictional example: 15 weeks, Base → Build → Peak → Taper; one local COROS activity fixture.")
    print(f"Login email: {EMAIL}")


if __name__ == "__main__":
    main()
