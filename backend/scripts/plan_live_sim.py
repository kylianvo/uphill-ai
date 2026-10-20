"""Live end-to-end simulation (paid: ~40 Gemini calls). Builds one plan week by week through the real API with
the real model on a SCRATCH database, the athlete completing every week, then lints the whole plan against the
goal's demands and the athlete's preferences. GEMINI_API_KEY must be set; DATABASE_URL must be a scratch db.

    GEMINI_API_KEY=... DATABASE_URL=postgresql://.../scratch python scripts/plan_live_sim.py [--weeks 10]
"""

import argparse
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

import db  # noqa: E402
from main import app  # noqa: E402
from services import goal_demands, plan_journey, plan_lint  # noqa: E402
from services.athlete_tier import get_profile  # noqa: E402
from telemetry import rag_attempts_total  # noqa: E402

START = date(2026, 10, 19)
DAYS = ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def poll(client, headers, job_id, timeout=420):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = client.get(f"/api/coach/plan-status/{job_id}", headers=headers).json()
        if "status" not in r:
            print(f"plan-status gave {str(r)[:200]}")
            time.sleep(5)
            continue
        if r["status"] in ("done", "failed", "error"):
            return r
        time.sleep(3)
    raise SystemExit("timed out waiting for a block")


def used(engine):
    return rag_attempts_total.labels(service="plan_generator", engine=engine, status="used")._value.get()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weeks", type=int, default=10)
    weeks = ap.parse_args().weeks
    with TestClient(app) as client:
        login = client.post("/api/auth/mock-login", json={"email": "zz-live-sim@uphill.ai"}).json()
        headers = {"Authorization": f"Bearer {login['session_token']}"}
        uid = login["user"]["id"]
        from sqlalchemy import text

        with db.engine.begin() as c:
            c.execute(
                text("UPDATE users SET aet_hr=145, ant_hr=168, max_hr=185, resting_hr=55 WHERE id=:u"), {"u": uid}
            )
        body = {
            "goal_type": "time", "race_name": "ZZ VHT 100K (live sim)", "terrain": "trail",
            "race_date": (START + timedelta(weeks=weeks - 1, days=5)).isoformat(), "plan_start_date": START.isoformat(),
            "course_distance_km": 104.2, "course_elevation_gain_m": 5533, "target_time_hours": 14.67,
            "cutoff_time_hours": 29, "current_weekly_km": 65, "days_per_week": 6, "preferred_days": DAYS,
            "long_run_day": "Sunday", "lang": "en",
        }  # fmt: skip
        first = client.post("/api/coach/generate-plan", headers=headers, json=body).json()
        plan_id = first["plan"]["id"]
        total = first["plan"]["total_weeks"]
        before = {e: used(e) for e in ("gemini", "gemini_retry")}
        res = poll(client, headers, first["job_id"]) if first.get("job_id") else {"status": "done"}
        print(f"plan {plan_id} total_weeks={total}; week 1: {res['status']}")
        for week in range(1, weeks + 1):
            if week > 1:
                started = client.post(
                    "/api/coach/generate-next-block",
                    headers=headers,
                    json={"plan_id": plan_id, "block_number": week, "lang": "en"},
                )
                if started.status_code != 200:
                    print(f"week {week}: HTTP {started.status_code} {started.text[:200]}")
                    break
                res = poll(client, headers, started.json()["job_id"])
                print(f"week {week}: {res['status']}")
            for w in db.get_plan_workouts(plan_id):
                if w["week_number"] == week and w["type"] != "Rest":
                    db.update_workout_log(w["id"], is_completed=1)
        ws = db.get_plan_workouts(plan_id)
        plan = db.get_plan_by_id(plan_id)
        d = goal_demands.compute(104.2, 5533, 14.67, 29)
        tier = plan.get("athlete_tier")
        prefs = plan_lint.Prefs(long_run_day="Sunday", days_per_week=6, demands=d, flat_only=True, total_weeks=total)
        issues = plan_lint.lint_weeks(ws, {w["week_number"] for w in ws}, get_profile(tier), prefs)
        print(
            f"\nengines used (model/retry): {used('gemini') - before['gemini']:.0f}/{used('gemini_retry') - before['gemini_retry']:.0f}; tier={tier}"
        )
        print("wk phase        min  long  sess")
        for wk in sorted({w["week_number"] for w in ws}):
            a = [w for w in ws if w["week_number"] == wk and w["type"] != "Rest"]
            long = max((w["duration_minutes"] for w in a if w["type"] == "Long Run"), default=0)
            print(
                f"{wk:2} {a[0]['phase'] if a else '':11} {sum(w['duration_minutes'] for w in a):5.0f} {long:5.0f} {len(a):4}"
            )
        print("lint:", sorted({(i.week, i.code) for i in issues}) or "clean")
        print("milestones:", [(m.key, m.week) for m in plan_journey.milestones(ws, 1)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
