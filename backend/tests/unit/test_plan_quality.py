from services import plan_quality


def _wo(week, day, minutes, zone="Zone 2", typ="Easy", **kw):
    return {
        "week_number": week, "day_of_week": day, "type": typ, "target_zone": zone, "duration_minutes": float(minutes),
        "description": "", "target_pace": "", "distance_km": 0.0, "elevation_gain_m": 0.0, **kw,
    }  # fmt: skip


RACE = {
    "course_distance_km": 50, "course_elevation_gain_m": 2500, "goal_type": "finish", "outdoor_climbing": True,
    "threshold_source": "field", "aet_hr": 150, "ant_hr": 160,
}  # fmt: skip


def _plan(weeks=12, long_min=240, climb=1200, taper=(0.8, 0.5)):
    rows = []
    for w in range(1, weeks + 1):
        scale = {weeks - 2: taper[0], weeks - 1: taper[1]}.get(w, 1.0)
        rows.append(
            _wo(w, "Tuesday", 60 * scale, mountain_climb_rate=None, treadmill_incline="10", elevation_gain_m=climb)
        )
        rows.append(_wo(w, "Sunday", long_min * scale, typ="Long Run"))
    rows.append(_wo(weeks, "Saturday", 480, typ="Race", target_pace="9:00 - 10:00 /km"))
    return rows


def _by_name(checks):
    return {c.name.split(":")[0]: c.ok for c in checks}


def test_a_sound_plan_passes_every_check():
    checks = plan_quality.assess(_plan(), RACE, "6:30 - 5:50")
    assert all(c.ok for c in checks), [c for c in checks if not c.ok]


def test_no_climbing_prep_is_flagged():
    checks = plan_quality.assess(_plan(climb=0), RACE, "6:30 - 5:50")
    assert not next(c for c in checks if c.name.startswith("climbing prep")).ok


def test_a_one_step_taper_is_flagged():
    checks = plan_quality.assess(_plan(taper=(1.0, 0.5)), RACE, "6:30 - 5:50")
    assert not next(c for c in checks if c.name.startswith("two-step taper")).ok


def test_a_zone_4_race_pace_on_a_finish_goal_is_flagged():
    rows = _plan()
    rows[-1]["target_pace"] = "4:57 - 4:31 /km"
    checks = plan_quality.assess(rows, RACE, "6:30 - 5:50")
    assert not next(c for c in checks if c.name.startswith("finish-only race pace")).ok


def test_long_zone_3_and_zone_4_sessions_are_flagged():
    rows = _plan() + [_wo(5, "Wednesday", 130, zone="Zone 3", typ="Tempo")]
    checks = plan_quality.assess(rows, RACE, "6:30 - 5:50")
    assert not next(c for c in checks if c.name.startswith("no long Zone 3")).ok


def test_unmeasured_thresholds_need_the_week_one_drift_test():
    race = {**RACE, "threshold_source": "unknown"}
    plan = _plan()
    assert not next(c for c in plan_quality.assess(plan, race, "6:30 - 5:50") if "drift test" in c.name).ok
    plan[0]["title"] = "AeT Drift Test (Zone 2)"
    assert next(c for c in plan_quality.assess(plan, race, "6:30 - 5:50") if "drift test" in c.name).ok


def test_a_week_above_80_percent_of_race_climbing_is_flagged():
    checks = plan_quality.assess(_plan(climb=2100), RACE, "6:30 - 5:50")
    assert not next(c for c in checks if c.name.startswith("no week above 80%")).ok
