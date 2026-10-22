"""Live persona matrix (PAID: ~15 Gemini calls per persona). Builds one plan per persona week by week through the
real API with the real model on a SCRATCH database, the athlete completing every week, then checks the whole plan
against doctrine rules, the athlete's preferences, and persona-specific expectations (the Vietnamese mountain cases
from #142 included). Writes <out>/<persona>.json (plan + checks) and prints a summary table.

    GEMINI_API_KEY=... DATABASE_URL=postgresql://.../scratch QDRANT_URL=http://localhost:6333 \
        python scripts/plan_live_personas.py --out /tmp/personas [--only novice,quang] [--list]
"""

import argparse
import json
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

import db  # noqa: E402
from main import app  # noqa: E402
from services import goal_demands, plan_lint  # noqa: E402
from services.athlete_tier import for_race, get_profile  # noqa: E402

START = date(2026, 10, 19)  # a Monday
ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
USER_COLUMNS = {
    "aet_hr",
    "ant_hr",
    "max_hr",
    "resting_hr",
    "zone2_pace_min",
    "zone2_pace_max",
    "threshold_pace",
    "age",
    "gender",
}
VI_BANNED = [
    "kiến tạo",
    "bảo chứng",
    "bứt phá",
    "nâng tầm",
    "vượt trội",
    "tối ưu hóa",
    "chuyên sâu",
    "đột phá",
    "giáo án",
    "sinh lý",
    "thể tích",
]

# name: dict(user=..., plan=..., weeks=N (plan weeks until race week), expect=...)
PERSONAS: dict[str, dict] = {
    "novice_trail_half": dict(
        user=dict(aet_hr=140, ant_hr=160, max_hr=190, resting_hr=62, zone2_pace_min="7:30", zone2_pace_max="6:45"),
        plan=dict(
            goal_type="finish",
            terrain="trail",
            course_distance_km=21.1,
            course_elevation_gain_m=600,
            current_weekly_km=20,
            days_per_week=3,
            preferred_days=["Tuesday", "Thursday", "Sunday"],
            long_run_day="Sunday",
            cutoff_time_hours=4,
            stair_access=True,
        ),
        weeks=12,
        expect=dict(no_intensity=True, max_long_run_min=120),
    ),
    "recreational_50k": dict(
        user=dict(aet_hr=148, ant_hr=168, max_hr=186, resting_hr=55, zone2_pace_min="6:30", zone2_pace_max="5:50"),
        plan=dict(
            goal_type="time",
            terrain="trail",
            course_distance_km=50,
            course_elevation_gain_m=2400,
            current_weekly_km=45,
            days_per_week=5,
            preferred_days=["Tuesday", "Wednesday", "Friday", "Saturday", "Sunday"],
            long_run_day="Sunday",
            target_time_hours=8.5,
            cutoff_time_hours=11,
            use_treadmill=True,
            treadmill_max_incline=15,
        ),
        weeks=12,
        expect={},
    ),
    "elite_100k": dict(
        user=dict(
            aet_hr=152,
            ant_hr=172,
            max_hr=190,
            resting_hr=44,
            zone2_pace_min="5:20",
            zone2_pace_max="4:45",
            threshold_pace="3:55",
        ),
        plan=dict(
            goal_type="time",
            terrain="trail",
            course_distance_km=100,
            course_elevation_gain_m=5000,
            current_weekly_km=120,
            days_per_week=6,
            preferred_days=ALL_DAYS[1:],
            long_run_day="Saturday",
            target_time_hours=11.5,
            cutoff_time_hours=24,
            training_environment="hilly",
        ),
        weeks=12,
        expect=dict(b2b=True),
    ),
    "ultra_100_miles": dict(
        user=dict(aet_hr=145, ant_hr=165, max_hr=185, resting_hr=52, zone2_pace_min="6:10", zone2_pace_max="5:30"),
        plan=dict(
            goal_type="finish",
            terrain="trail",
            course_distance_km=161,
            course_elevation_gain_m=8000,
            current_weekly_km=90,
            days_per_week=6,
            preferred_days=["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            long_run_day="Sunday",
            cutoff_time_hours=36,
            training_mountain="nui_dinh",
            mountain_days=["Saturday", "Sunday"],
            mountain_min_minutes=180,
        ),
        weeks=16,
        expect=dict(b2b=True, min_longest_session=240),
    ),
    "road_marathon": dict(
        user=dict(aet_hr=150, ant_hr=170, max_hr=188, resting_hr=54, zone2_pace_min="6:00", zone2_pace_max="5:20"),
        plan=dict(
            goal_type="time",
            terrain="road",
            course_distance_km=42.2,
            course_elevation_gain_m=150,
            current_weekly_km=40,
            days_per_week=5,
            preferred_days=["Monday", "Wednesday", "Thursday", "Saturday", "Sunday"],
            long_run_day="Sunday",
            target_time_hours=3.75,
        ),
        weeks=14,
        expect=dict(zero_vert=True, max_long_run_min=200),
    ),
    "busy_3day_50k": dict(
        user=dict(aet_hr=146, ant_hr=166, max_hr=186, resting_hr=57, zone2_pace_min="6:40", zone2_pace_max="6:00"),
        plan=dict(
            goal_type="finish",
            terrain="trail",
            course_distance_km=50,
            course_elevation_gain_m=2000,
            current_weekly_km=35,
            days_per_week=3,
            preferred_days=["Tuesday", "Thursday", "Sunday"],
            long_run_day="Sunday",
            cutoff_time_hours=12,
            athlete_notes="Work is heavy: weekday runs must be 50 minutes or less. Weekends are free.",
            use_treadmill=True,
            treadmill_max_incline=15,
        ),
        weeks=14,
        expect=dict(max_weekday_min=60),
    ),
    # Quang (#142, plan 108): Aptrc 80 km, fast HCMC runner, flat zone 2 4:54-4:30, mountain days on weekends at Núi Dinh.
    "quang_aptrc80": dict(
        user=dict(
            aet_hr=150,
            ant_hr=170,
            max_hr=190,
            resting_hr=48,
            zone2_pace_min="4:54",
            zone2_pace_max="4:30",
            threshold_pace="3:57",
        ),
        plan=dict(
            goal_type="time",
            terrain="trail",
            course_distance_km=80,
            course_elevation_gain_m=3600,
            current_weekly_km=85,
            days_per_week=6,
            preferred_days=["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            long_run_day="Sunday",
            target_time_hours=10.5,
            cutoff_time_hours=16,
            training_environment="flat",
            training_mountain="nui_dinh",
            mountain_days=["Saturday", "Sunday"],
            mountain_min_minutes=180,
            has_gym_access=True,
            use_treadmill=True,
        ),
        weeks=12,
        expect=dict(mountain=True, min_mountain_long_run=180),
    ),
    "vn_hcmc_chau_thoi_50k_vi": dict(
        user=dict(aet_hr=150, ant_hr=170, max_hr=188, resting_hr=56, zone2_pace_min="6:20", zone2_pace_max="5:40"),
        plan=dict(
            goal_type="finish",
            terrain="trail",
            course_distance_km=50,
            course_elevation_gain_m=2500,
            current_weekly_km=40,
            days_per_week=5,
            preferred_days=["Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"],
            long_run_day="Sunday",
            cutoff_time_hours=12,
            training_environment="flat",
            training_mountain="chau_thoi",
            mountain_days=["Saturday", "Sunday"],
            mountain_min_minutes=180,
            lang="vi",
        ),
        weeks=12,
        expect=dict(mountain=True, min_mountain_long_run=180, vietnamese=True),
    ),
    "vn_hanoi_ham_lon_100k_vi": dict(
        user=dict(aet_hr=148, ant_hr=168, max_hr=186, resting_hr=53, zone2_pace_min="6:00", zone2_pace_max="5:20"),
        plan=dict(
            goal_type="time",
            terrain="trail",
            course_distance_km=100,
            course_elevation_gain_m=5000,
            current_weekly_km=60,
            days_per_week=6,
            preferred_days=["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            long_run_day="Sunday",
            target_time_hours=16,
            cutoff_time_hours=30,
            training_environment="flat",
            training_mountain="ham_lon",
            mountain_days=["Saturday", "Sunday"],
            mountain_min_minutes=180,
            lang="vi",
        ),
        weeks=14,
        expect=dict(mountain=True, min_mountain_long_run=180, vietnamese=True, b2b=True),
    ),
    "vn_flat_city_treadmill_only": dict(
        user=dict(aet_hr=147, ant_hr=167, max_hr=187, resting_hr=55, zone2_pace_min="6:30", zone2_pace_max="5:50"),
        plan=dict(
            goal_type="finish",
            terrain="trail",
            course_distance_km=70,
            course_elevation_gain_m=3500,
            current_weekly_km=50,
            days_per_week=5,
            preferred_days=["Monday", "Tuesday", "Thursday", "Saturday", "Sunday"],
            long_run_day="Sunday",
            cutoff_time_hours=20,
            training_environment="flat",
            use_treadmill=True,
            treadmill_max_incline=15,
            has_gym_access=True,
            lang="vi",
        ),
        weeks=12,
        expect=dict(zero_outdoor_vert=True, climbing_me=True, vietnamese=True),
    ),
    # HCMC review pack for Quang (2026-10-22): recreational vs sub-elite, 50 km vs 100 km, Núi Dinh / Chứa Chan
    # weekends, and one city runner who reaches the mountain only now and then.
    "hcm_rec_50k_dinh": dict(
        user={
            "aet_hr": 145,
            "ant_hr": 166,
            "max_hr": 188,
            "resting_hr": 56,
            "zone2_pace_min": "6:40",
            "zone2_pace_max": "6:00",
            "threshold_pace": "5:10",
        },
        plan=dict(
            goal_type="time",
            terrain="trail",
            course_distance_km=50,
            course_elevation_gain_m=2500,
            current_weekly_km=40,
            days_per_week=5,
            preferred_days=["Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"],
            long_run_day="Sunday",
            target_time_hours=9,
            cutoff_time_hours=13,
            training_environment="flat",
            training_mountain="nui_dinh",
            mountain_days=["Sunday"],
            mountain_min_minutes=180,
            use_treadmill=True,
            treadmill_max_incline=15,
        ),
        weeks=14,
        expect=dict(mountain=True, min_mountain_long_run=180),
    ),
    "hcm_rec_100k_dinh": dict(
        user={
            "aet_hr": 145,
            "ant_hr": 166,
            "max_hr": 188,
            "resting_hr": 56,
            "zone2_pace_min": "6:40",
            "zone2_pace_max": "6:00",
            "threshold_pace": "5:10",
        },
        plan=dict(
            goal_type="finish",
            terrain="trail",
            course_distance_km=100,
            course_elevation_gain_m=5000,
            current_weekly_km=65,
            days_per_week=6,
            preferred_days=ALL_DAYS[1:],
            long_run_day="Saturday",
            cutoff_time_hours=28,
            training_environment="flat",
            training_mountain="nui_dinh",
            mountain_days=["Saturday"],
            mountain_min_minutes=180,
            use_treadmill=True,
            treadmill_max_incline=15,
            has_gym_access=True,
        ),
        weeks=16,
        expect=dict(mountain=True, min_mountain_long_run=180, b2b=True),
    ),
    "hcm_subelite_50k_dinh": dict(
        user={
            "aet_hr": 156,
            "ant_hr": 174,
            "max_hr": 190,
            "resting_hr": 45,
            "zone2_pace_min": "5:10",
            "zone2_pace_max": "4:40",
            "threshold_pace": "4:00",
        },
        plan=dict(
            goal_type="time",
            terrain="trail",
            course_distance_km=50,
            course_elevation_gain_m=2500,
            current_weekly_km=90,
            days_per_week=6,
            preferred_days=ALL_DAYS[1:],
            long_run_day="Saturday",
            target_time_hours=6,
            cutoff_time_hours=13,
            training_environment="flat",
            training_mountain="nui_dinh",
            mountain_days=["Saturday"],
            mountain_min_minutes=180,
            use_treadmill=True,
            treadmill_max_incline=15,
            has_gym_access=True,
        ),
        weeks=12,
        expect=dict(mountain=True, min_mountain_long_run=180),
    ),
    "hcm_subelite_100k_dinh": dict(
        user={
            "aet_hr": 156,
            "ant_hr": 174,
            "max_hr": 190,
            "resting_hr": 45,
            "zone2_pace_min": "5:10",
            "zone2_pace_max": "4:40",
            "threshold_pace": "4:00",
        },
        plan=dict(
            goal_type="time",
            terrain="trail",
            course_distance_km=100,
            course_elevation_gain_m=5000,
            current_weekly_km=100,
            days_per_week=6,
            preferred_days=ALL_DAYS[1:],
            long_run_day="Saturday",
            target_time_hours=13,
            cutoff_time_hours=28,
            training_environment="flat",
            training_mountain="nui_dinh",
            mountain_days=["Saturday"],
            mountain_min_minutes=180,
            use_treadmill=True,
            treadmill_max_incline=15,
            has_gym_access=True,
        ),
        weeks=16,
        expect=dict(mountain=True, min_mountain_long_run=180, b2b=True),
    ),
    "hcm_rec_50k_city_sometimes": dict(
        user={
            "aet_hr": 145,
            "ant_hr": 166,
            "max_hr": 188,
            "resting_hr": 56,
            "zone2_pace_min": "6:40",
            "zone2_pace_max": "6:00",
            "threshold_pace": "5:10",
        },
        plan=dict(
            goal_type="finish",
            terrain="trail",
            course_distance_km=50,
            course_elevation_gain_m=2500,
            current_weekly_km=40,
            days_per_week=5,
            preferred_days=["Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"],
            long_run_day="Sunday",
            cutoff_time_hours=13,
            training_environment="flat",
            use_treadmill=True,
            treadmill_max_incline=15,
            stair_access=True,
            has_gym_access=True,
        ),
        weeks=14,
        # Trail preferences change when each new week is generated: Núi Dinh on Sunday every other week.
        week_overrides={
            wk: (
                dict(training_mountain="nui_dinh", mountain_days=["Sunday"], mountain_min_minutes=180)
                if wk % 2 == 0
                else dict(training_mountain=None, mountain_days=[], mountain_min_minutes=None)
            )
            for wk in range(2, 14)
        },
        expect=dict(climbing_me=True),
    ),
}


def poll(client, headers, job_id, timeout=480):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = client.get(f"/api/coach/plan-status/{job_id}", headers=headers).json()
        if "status" in r and r["status"] in ("done", "failed", "error"):
            return r
        time.sleep(4)
    return {"status": "timeout"}


def _mins(w):
    return float(w.get("duration_minutes") or 0)


def evaluate(name: str, persona: dict, ws: list[dict], plan: dict, feasibility: dict | None = None) -> list[dict]:
    """(check, ok, detail) rows."""
    exp, p = persona["expect"], persona["plan"]
    rows: list[dict] = []

    def add(check, ok, detail=""):
        rows.append({"check": check, "ok": bool(ok), "detail": detail})

    tier = plan.get("athlete_tier") or "recreational"
    dist, gain = p["course_distance_km"], p["course_elevation_gain_m"]
    demands = goal_demands.compute(dist, gain, p.get("target_time_hours"), p.get("cutoff_time_hours"))
    venues_flat = not (
        p.get("training_mountain") or p.get("mountain_days") or p.get("training_environment") in ("hilly", "mixed")
    )
    prefs = plan_lint.Prefs(
        long_run_day=p.get("long_run_day"), days_per_week=p.get("days_per_week"), demands=demands,
        flat_only=venues_flat, total_weeks=plan["total_weeks"],
    )  # fmt: skip
    weeks = sorted({w["week_number"] for w in ws})
    issues = plan_lint.lint_weeks(ws, set(weeks), for_race(get_profile(tier), dist), prefs)
    hard = {
        "ME_SPACING",
        "HARD_ADJACENT",
        "SESSION_TOO_LONG",
        "LONG_RUN_DAY",
        "DAYS_SHORT",
        "HARD_IN_DOWN_WEEK",
        "LONG_SHARE",
    }
    # The #142 mountain minimum (and a week that cannot hold the goal) legitimately breaks the long-run share: the
    # verdict must then say so (lever fewer_mountain_minimum / unsupported) instead.
    share_excused = (exp.get("mountain") and "fewer_mountain_minimum" in (feasibility or {}).get("levers", [])) or (
        (feasibility or {}).get("verdict") == "unsupported"
    )
    bad = sorted(
        {
            (i.week, i.code)
            for i in issues
            if i.code in hard and i.week < plan["total_weeks"] - 1 and not (i.code == "LONG_SHARE" and share_excused)
        }
    )
    add("no hard-rule lint (weeks before race week)", not bad, str(bad))
    soft = sorted({(i.week, i.code) for i in issues if i.code not in hard})
    add("soft lint (informational)", True, str(soft) or "clean")

    by = plan_lint._by_week(ws)
    active = {wk: [w for w in by[wk] if w["type"] != "Rest"] for wk in weeks}
    minutes = {wk: sum(_mins(w) for w in active[wk]) for wk in weeks}
    phases = {wk: (active[wk][0].get("phase") if active[wk] else "") for wk in weeks}
    build = [wk for wk in weeks if phases[wk] in ("Base", "Build", "Peak")]
    peak = max((minutes[wk] for wk in build), default=0)
    capacity_min = ((feasibility or {}).get("capacity_h") or 0) * 60
    at_capacity = bool(capacity_min) and minutes[weeks[0]] >= 0.9 * capacity_min  # nothing left to progress into
    add(
        "progression: peak week >= 1.15 x week 1 (or week 1 already at the athlete's capacity)",
        peak >= 1.15 * minutes[weeks[0]] or at_capacity or (bool(capacity_min) and peak >= 0.9 * capacity_min),
        f"wk1 {minutes[weeks[0]]:.0f} -> peak {peak:.0f} min (capacity {capacity_min:.0f})",
    )
    taper = [wk for wk in weeks if phases[wk] == "Taper"]
    add(
        "taper present and lighter than peak",
        bool(taper) and all(minutes[wk] <= 0.8 * peak for wk in taper),
        f"taper {[round(minutes[wk]) for wk in taper]}",
    )
    race = [w for w in ws if w["type"] == "Race"]
    add("race on race week", bool(race), "")
    if p.get("long_run_day"):
        on_day = {w["week_number"] for w in ws if w["type"] == "Long Run" and w["day_of_week"] == p["long_run_day"]}
        wrong = [
            w["week_number"]
            for w in ws
            if w["type"] == "Long Run"
            and w["day_of_week"] != p["long_run_day"]
            and w["week_number"] not in on_day  # a Saturday long run in a back-to-back weekend is fine
            and phases.get(w["week_number"]) not in ("Recovery",)
        ]
        add("long run on the athlete's day", not wrong, str(wrong[:5]))
    if exp.get("no_intensity"):
        hot = [
            (w["week_number"], w["type"])
            for w in ws
            if w["type"] in ("Interval", "Tempo", "Threshold") or w.get("target_zone") in ("Zone 4", "Zone 5")
        ]
        add("novice: no Zone 4+/Interval/Tempo", not hot, str(hot[:5]))
    if exp.get("max_long_run_min"):
        longest = max((_mins(w) for w in ws if w["type"] == "Long Run"), default=0)
        add(f"long run <= {exp['max_long_run_min']} min", longest <= exp["max_long_run_min"], f"longest {longest:.0f}")
    if exp.get("min_longest_session"):
        longest = max((_mins(w) for w in ws if w["type"] != "Race"), default=0)
        add(
            f"longest session >= {exp['min_longest_session']} min",
            longest >= exp["min_longest_session"],
            f"longest {longest:.0f}",
        )
    if exp.get("max_weekday_min"):
        wk_days = [
            w for w in ws if w["type"] not in ("Rest", "Race") and w["day_of_week"] not in ("Saturday", "Sunday")
        ]
        over = [(w["week_number"], round(_mins(w))) for w in wk_days if _mins(w) > exp["max_weekday_min"]]
        add(f"weekday sessions <= {exp['max_weekday_min']} min (athlete notes)", not over, str(over[:6]))
    if exp.get("b2b"):
        b2b = [wk for wk in weeks if plan_lint.is_b2b_week(by[wk])]
        add("back-to-back weekend in the last build weeks", bool(b2b), str(b2b))
    if exp.get("zero_vert"):
        add("road: no climbing", not any(float(w.get("elevation_gain_m") or 0) > 0 for w in ws), "")
    if exp.get("zero_outdoor_vert"):
        out = [
            w["week_number"]
            for w in ws
            if w["type"] in ("Easy", "Long Run", "Tempo")
            and float(w.get("elevation_gain_m") or 0) > 0
            and str(w.get("treadmill_incline") or "0").split("-")[0] in ("0", "0.0", "")
        ]
        add("no invented outdoor climbing", not out, str(out[:5]))
    if exp.get("climbing_me"):
        build_me = [
            w for w in ws if w["type"] == "Muscular Endurance" and phases.get(w["week_number"]) in ("Build", "Peak")
        ]
        add(
            "build-phase ME is climbing work (stairs/incline/carries)",
            bool(build_me)
            and all(plan_lint._climbs(w) or float(w.get("treadmill_incline") or 0) > 0 for w in build_me),
            f"{len(build_me)} ME sessions",
        )
    if exp.get("mountain"):
        mdays = set(p.get("mountain_days") or [])
        ml = [
            w
            for w in ws
            if w["type"] == "Long Run"
            and w["day_of_week"] in mdays
            and phases.get(w["week_number"]) in ("Base", "Build", "Peak")
        ]
        short = [
            (w["week_number"], round(_mins(w)))
            for w in ml
            if _mins(w) < exp.get("min_mountain_long_run", 0) and w.get("mountain_mode") in (None, "mountain")
        ]
        add(
            f"mountain long runs >= {exp.get('min_mountain_long_run')} min (the #142 minimum)",
            bool(ml) and not short,
            f"{len(ml)} mountain long runs, short: {short[:5]}",
        )
        rates = [w for w in ml if w.get("mountain_climb_rate")]
        add("mountain long runs carry a climb rate", len(rates) >= max(1, len(ml) // 2), f"{len(rates)}/{len(ml)}")
    if exp.get("vietnamese"):
        blob = " ".join(f"{w.get('title','')} {w.get('description','')}" for w in ws).lower()
        blob = blob.replace("thể tích tâm thu", "")  # stroke volume is physiology, not training volume
        found = [b for b in VI_BANNED if b in blob]
        add("Vietnamese copy: no banned words", not found, str(found))
        add(
            "Vietnamese copy: text is Vietnamese", bool(re.search(r"[ăâđêôơưáàảãạéèẻẽẹíìỉĩịóòỏõọúùủũụýỳỷỹỵ]", blob)), ""
        )
    return rows


def run_persona(name: str, out: Path) -> dict:
    persona = PERSONAS[name]
    p = dict(persona["plan"])
    weeks = persona["weeks"]
    with TestClient(app) as client:
        login = client.post("/api/auth/mock-login", json={"email": f"zz-persona-{name}@uphill.ai"}).json()
        headers = {"Authorization": f"Bearer {login['session_token']}"}
        uid = login["user"]["id"]
        cols = {k: v for k, v in persona["user"].items() if k in USER_COLUMNS}
        with db.engine.begin() as c:
            c.execute(
                text("UPDATE users SET " + ", ".join(f"{k}=:{k}" for k in cols) + " WHERE id=:u"), {**cols, "u": uid}
            )
        body = {
            "race_name": f"ZZ {name}",
            "race_date": (START + timedelta(weeks=weeks - 2, days=5)).isoformat(),
            "plan_start_date": START.isoformat(),
            "lang": "en",
            **p,
        }
        first = client.post("/api/coach/generate-plan", headers=headers, json=body).json()
        plan_id, total = first["plan"]["id"], first["plan"]["total_weeks"]
        if first.get("job_id"):
            poll(client, headers, first["job_id"])
        status = {}
        for week in range(1, total):  # through the race week
            if week > 1:
                started = client.post(
                    "/api/coach/generate-next-block",
                    headers=headers,
                    json={
                        "plan_id": plan_id,
                        "block_number": week,
                        "lang": p.get("lang", "en"),
                        **persona.get("week_overrides", {}).get(week, {}),
                    },
                )
                if started.status_code != 200:
                    status[week] = f"HTTP {started.status_code}"
                    break
                status[week] = poll(client, headers, started.json()["job_id"]).get("status")
            for w in db.get_plan_workouts(plan_id):
                if w["week_number"] == week and w["type"] != "Rest":
                    db.update_workout_log(w["id"], is_completed=1)
        ws = db.get_plan_workouts(plan_id)
        plan = db.get_plan_by_id(plan_id)
        journey = client.get(f"/api/plans/{plan_id}/journey", headers=headers).json()
        goal = client.get(f"/api/plans/{plan_id}/goal?lang=en", headers=headers).json()
        checks = evaluate(name, persona, ws, plan, goal.get("feasibility"))
    result = {"persona": name, "plan": {k: plan.get(k) for k in ("id", "total_weeks", "athlete_tier", "race_name", "race_date")},
              "weeks_status": status, "checks": checks, "feasibility": goal.get("feasibility"), "journey": {k: journey.get(k) for k in ("phases", "milestones", "deviations")},
              "workouts": ws}  # fmt: skip
    (out / f"{name}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str))
    return result


MODEL_FIELDS = (
    "week_number day_of_week phase title type duration_minutes target_zone target_hr_range target_pace distance_km "
    "elevation_gain_m grade_percent treadmill_incline treadmill_speed description fueling_tip is_priority"
).split()


def install_replay(dirs: list[Path]) -> None:
    """FREE mode: the Gemini client returns the model rows saved by an earlier paid run (week by week, read from
    the 'weeks X through Y' line of the prompt), so the model's own numbers run through today's post-processing.
    Any other model call (briefs, summaries) fails, which those features already tolerate."""
    from types import SimpleNamespace

    from google import genai

    saved: dict[str, list[dict]] = {}
    for d in dirs:  # earlier directories win
        for f in d.glob("*.json"):
            saved.setdefault(f.stem, json.loads(f.read_text())["workouts"])

    class _Models:
        def generate_content(self, model=None, contents="", config=None):
            m = re.search(r"weeks (\d+) through (\d+)", str(contents))
            persona = next((n for n in PERSONAS if f"ZZ {n}" in str(contents)), None)
            if not m or not persona or persona not in saved:
                raise RuntimeError("replay: no saved rows for this call")
            lo, hi = int(m.group(1)), int(m.group(2))
            rows = [{k: w[k] for k in MODEL_FIELDS if k in w} for w in saved[persona] if lo <= w["week_number"] <= hi]
            return SimpleNamespace(text=json.dumps(rows), usage_metadata=None)

    class _Client:
        def __init__(self, *a, **k):
            self.models = _Models()

    genai.Client = _Client


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/personas")
    ap.add_argument("--only", default="")
    ap.add_argument("--list", action="store_true")
    ap.add_argument(
        "--replay", default="", help="comma-separated dirs of saved paid runs: FREE replay of their model rows"
    )
    args = ap.parse_args()
    if args.replay:
        install_replay([Path(d) for d in args.replay.split(",")])
    if args.list:
        print("\n".join(PERSONAS))
        return 0
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    names = [n for n in PERSONAS if not args.only or any(o in n for o in args.only.split(","))]
    sys.stdout.reconfigure(line_buffering=True)
    for n in names:
        r = run_persona(n, out)
        fails = [c for c in r["checks"] if not c["ok"]]
        print(
            f"\n== {n}: tier={r['plan']['athlete_tier']} feasibility={(r['feasibility'] or {}).get('verdict')} fails={len(fails)}"
        )
        for c in r["checks"]:
            print(f"   {'PASS' if c['ok'] else 'FAIL'} {c['check']}: {c['detail']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
