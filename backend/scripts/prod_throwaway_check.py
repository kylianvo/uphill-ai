"""Real-model check of the deployed plan pipeline on THROWAWAY plans (paid: ~35 Gemini calls).

Creates plans named 'ZZ TEST ... (delete me)' on the account of PROD_TOKEN, drives them through the real API,
prints what came out, and deletes every plan it created (never any other plan). The token comes from the
environment (PROD_TOKEN) and is never stored.

    PROD_TOKEN=... python scripts/prod_throwaway_check.py --base https://api.uphill-ai.io.vn [--weeks 10]
"""

import argparse
import os
import sys
import time
from datetime import date, timedelta

import requests

DAYS = ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class Api:
    def __init__(self, base: str, token: str):
        self.base, self.h = base.rstrip("/"), {"Authorization": f"Bearer {token}"}

    def call(self, method: str, path: str, **kw):
        r = requests.request(method, self.base + path, headers=self.h, timeout=120, **kw)
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, {"raw": r.text[:200]}

    def poll(self, job_id: str, timeout: int = 600) -> dict:
        t0 = time.time()
        while time.time() - t0 < timeout:
            code, r = self.call("GET", f"/api/coach/plan-status/{job_id}")
            if code == 200 and r.get("status") in ("done", "failed", "error"):
                return r
            time.sleep(4)
        raise SystemExit("timed out waiting for a job")


def body(name: str, start: date, weeks: int, **extra) -> dict:
    race = start + timedelta(weeks=weeks - 2, days=5)
    return {
        "goal_type": "time", "race_name": name, "terrain": "trail", "race_date": race.isoformat(),
        "plan_start_date": start.isoformat(), "course_distance_km": 104.2, "course_elevation_gain_m": 5533,
        "target_time_hours": 14.67, "cutoff_time_hours": 29, "current_weekly_km": 65, "days_per_week": 6,
        "preferred_days": DAYS, "long_run_day": "Sunday", "lang": "en", **extra,
    }  # fmt: skip


def table(workouts: list[dict]) -> None:
    print("wk phase        min  long  sess")
    for wk in sorted({w["week_number"] for w in workouts}):
        a = [w for w in workouts if w["week_number"] == wk and w["type"] != "Rest"]
        long = max((w["duration_minutes"] for w in a if w["type"] == "Long Run"), default=0)
        print(
            f"{wk:2} {(a[0].get('phase') or '') if a else '':11} {sum(w['duration_minutes'] for w in a):5.0f} {long:5.0f} {len(a):4}"
        )


def active_workouts(api: Api, plan_id: int) -> list[dict]:
    code, r = api.call("GET", "/api/coach/active-plan")
    plan = (r or {}).get("plan") or {}
    if plan.get("id") != plan_id:
        api.call("POST", "/api/coach/select-plan", json={"plan_id": plan_id})
        code, r = api.call("GET", "/api/coach/active-plan")
    return r.get("workouts") or []


def main() -> int:
    import signal

    sys.stdout.reconfigure(line_buffering=True)
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))  # so `finally` cleans up
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--weeks", type=int, default=10)
    ap.add_argument("--dump", default="", help="write the generated plans (workouts, journey, goal) to this JSON file")
    args = ap.parse_args()
    token = os.environ.get("PROD_TOKEN") or sys.exit("Set PROD_TOKEN")
    api = Api(args.base, token)
    created: list[int] = []
    code, before = api.call("GET", "/api/coach/active-plan")
    keep = ((before or {}).get("plan") or {}).get("id")
    print(f"active plan before: {keep} (will be restored, never deleted)")
    try:
        # A: a full plan, week by week, the athlete completing each week.
        start = date(2026, 10, 19)
        code, first = api.call(
            "POST", "/api/coach/generate-plan", json=body("ZZ TEST 100K full (delete me)", start, args.weeks)
        )
        if code != 200:
            print("generate-plan failed", code, first)
            return 1
        plan_a = first["plan"]["id"]
        created.append(plan_a)
        api.poll(first["job_id"]) if first.get("job_id") else None
        for week in range(1, args.weeks + 1):
            if week > 1:
                code, started = api.call(
                    "POST",
                    "/api/coach/generate-next-block",
                    json={"plan_id": plan_a, "block_number": week, "lang": "en"},
                )
                if code != 200:
                    print(f"week {week}: HTTP {code} {str(started)[:160]}")
                    break
                res = api.poll(started["job_id"])
                print(f"week {week}: {res.get('status')}")
            for w in active_workouts(api, plan_a):
                if w["week_number"] == week and w["type"] != "Rest":
                    api.call("PATCH", "/api/coach/workouts/log", json={"workout_id": w["id"], "is_completed": 1})
        ws = active_workouts(api, plan_a)
        dump: dict = {"plan_a_workouts": ws}
        print("\nPLAN A (full 100K, real prod model + KB)")
        table(ws)
        for ep in ("journey", "goal?lang=en"):
            code, r = api.call("GET", f"/api/plans/{plan_a}/{ep}")
            dump[f"plan_a_{ep.split('?')[0]}"] = r
            print(
                ep.split("?")[0],
                code,
                {k: r.get(k) for k in ("feasibility", "path", "deviations", "milestones") if k in r},
            )

        # B: an older plan on the athlete's REAL synced runs: aerobic-speed path + coach message.
        start_b = date(2026, 8, 31)
        code, second = api.call("POST", "/api/coach/generate-plan", json=body("ZZ TEST path (delete me)", start_b, 20))
        plan_b = second["plan"]["id"]
        created.append(plan_b)
        api.poll(second["job_id"]) if second.get("job_id") else None
        code, goal = api.call("GET", f"/api/plans/{plan_b}/goal?lang=en")
        print("\nPLAN B path on real runs:", goal.get("path"), "| feasibility:", goal.get("feasibility"))
        code, nudge = api.call("GET", f"/api/plans/{plan_b}/coach-nudge?lang=en")
        print("coach nudge:", nudge)
        code, nudge_vi = api.call("GET", f"/api/plans/{plan_b}/coach-nudge?lang=vi")
        print("coach nudge vi:", nudge_vi)
        dump.update(plan_b_goal=goal, plan_b_nudge=nudge, plan_b_nudge_vi=nudge_vi)
        if args.dump:
            import json

            with open(args.dump, "w") as fh:
                json.dump(dump, fh, ensure_ascii=False, indent=1, default=str)
    finally:
        for pid in created:
            code, r = api.call("DELETE", f"/api/coach/plans/{pid}")
            print(f"deleted plan {pid}: {code}")
        if keep:
            api.call("POST", "/api/coach/select-plan", json={"plan_id": keep})
            code, after = api.call("GET", "/api/coach/active-plan")
            print("active plan after:", ((after or {}).get("plan") or {}).get("id"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
