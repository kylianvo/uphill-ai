"""Fixtures are the weeks the prod coach review found (Vietnam Highlands Trail test plans)."""

from services.athlete_tier import TIER_PROFILES
from services.plan_lint import Prefs, lint_week, lint_weeks

REC = TIER_PROFILES["recreational"]
NOV = TIER_PROFILES["novice"]
SUB = TIER_PROFILES["sub_elite"]


def s(week, day, type_, minutes, zone="Zone 2", gain=0, dist=None, phase="Base", title=None):
    return {
        "week_number": week,
        "day_of_week": day,
        "type": type_,
        "duration_minutes": minutes,
        "target_zone": zone,
        "elevation_gain_m": gain,
        "distance_km": minutes / 6 if dist is None else dist,
        "phase": phase,
        "title": title or f"{type_} {day[:3]}",
    }


def filler(week, minutes, gain=0, phase="Base"):
    """A week reduced to its totals, for context before the week under test."""
    return [s(week, "Tuesday", "Easy", minutes, gain=gain, phase=phase)]


def codes(issues):
    return sorted({i.code for i in issues})


def test_plan_c_saturday_strength_24h_before_the_sunday_long_run():
    w1 = [
        s(1, "Tuesday", "Easy", 55),
        s(1, "Saturday", "Muscular Endurance", 45, "Zone 1"),
        s(1, "Sunday", "Long Run", 95),
    ]
    issues = lint_week(w1, 1, NOV)
    me = [i for i in issues if i.code == "ME_SPACING"]
    assert me and "24 h" in me[0].message and "Saturday" in me[0].message and "48 hours" in me[0].message


def test_strength_two_days_before_the_long_run_is_fine_and_same_day_doubles_are_ignored():
    wk = [
        s(1, "Tuesday", "Interval", 70, gain=220),
        s(1, "Thursday", "Muscular Endurance", 55, "Zone 1"),
        s(1, "Thursday", "Recovery", 35, "Zone 1"),
        s(1, "Sunday", "Long Run", 95),
    ]
    assert "ME_SPACING" not in codes(lint_week(wk, 1, SUB))


def test_plan_a_week_6_stacks_hard_days_spikes_vert_and_skips_recovery():
    ctx = (
        filler(1, 445, 1824) + filler(2, 390, 1619) + filler(3, 395, 1515) + filler(4, 405, 1666) + filler(5, 420, 1817)
    )
    w6 = [
        s(6, "Tuesday", "Interval", 70, gain=420),
        s(6, "Wednesday", "Tempo", 75, "Zone 3", 650),
        s(6, "Thursday", "Muscular Endurance", 55, "Zone 1"),
        s(6, "Thursday", "Easy", 35, gain=188),
        s(6, "Friday", "Easy", 50, gain=266),
        s(6, "Saturday", "Easy", 55, gain=324),
        s(6, "Sunday", "Long Run", 115, gain=679),
    ]
    got = codes(lint_week(ctx + w6, 6, SUB))
    assert {"HARD_ADJACENT", "ME_SPACING", "VERT_JUMP", "RECOVERY_DUE"} <= set(got)
    assert "VOLUME_JUMP" not in got  # +8% is inside the 10% cap


def test_week_5_of_the_same_plan_is_clean():
    ctx = filler(1, 445, 1824) + filler(2, 390, 1619) + filler(3, 395, 1515) + filler(4, 405, 1666)
    w5 = [
        s(5, "Tuesday", "Easy", 70, gain=376),
        s(5, "Wednesday", "Easy", 65, gain=345),
        s(5, "Thursday", "Muscular Endurance", 55, "Zone 1"),
        s(5, "Friday", "Easy", 45, gain=240),
        s(5, "Saturday", "Easy", 50, gain=266),
        s(5, "Sunday", "Long Run", 100, gain=590),
    ]
    assert lint_week(ctx + w5, 5, SUB) == []


def test_plan_b_week_2_jumps_volume_and_loads_the_weekend():
    w1 = [
        s(1, "Tuesday", "Interval", 55),
        s(1, "Thursday", "Muscular Endurance", 55, "Zone 1"),
        s(1, "Saturday", "Easy", 65),
        s(1, "Sunday", "Long Run", 95),
    ]
    w2 = [
        s(2, "Tuesday", "Interval", 70),
        s(2, "Thursday", "Muscular Endurance", 55, "Zone 1"),
        s(2, "Saturday", "Easy", 105),
        s(2, "Sunday", "Long Run", 115),
    ]
    got = lint_week(w1 + w2, 2, REC)
    assert {"VOLUME_JUMP", "BACK_TO_BACK"} <= set(codes(got))
    # 33% long run is inside the recreational cap (33% + tolerance): the generic 25% is not the rule here
    assert "LONG_SHARE" not in codes(got)
    jump = next(i for i in got if i.code == "VOLUME_JUMP")
    assert "28%" in jump.message and "cap the increase at 10%" in jump.message.lower()


def test_long_run_share_uses_the_athletes_own_tier_cap():
    wk = [
        s(3, "Tuesday", "Easy", 70),
        s(3, "Thursday", "Muscular Endurance", 60, "Zone 1"),
        s(3, "Sunday", "Long Run", 130),
    ]
    assert "LONG_SHARE" in codes(lint_week(wk, 3, NOV))  # 50% vs the novice 35% cap
    wide = [
        s(3, "Tuesday", "Easy", 90),
        s(3, "Thursday", "Muscular Endurance", 60, "Zone 1"),
        s(3, "Saturday", "Easy", 60),
        s(3, "Sunday", "Long Run", 110),
    ]
    assert "LONG_SHARE" not in codes(lint_week(wide, 3, REC))  # 34% is inside 33% + tolerance


def test_a_week_after_a_down_week_may_rebuild_past_the_cap():
    ctx = filler(1, 400) + filler(2, 340)  # -15%: a planned down week
    assert "VOLUME_JUMP" not in codes(lint_week(ctx + filler(3, 400), 3, REC))


def test_recovery_due_only_on_the_fourth_consecutive_build_week_and_resets_after_a_down_week():
    ctx = filler(1, 300) + filler(2, 310) + filler(3, 320)
    assert "RECOVERY_DUE" in codes(lint_week(ctx + filler(4, 330), 4, REC))
    assert "RECOVERY_DUE" not in codes(lint_week(ctx + filler(4, 240), 4, REC))  # week 4 IS the recovery week
    assert "RECOVERY_DUE" not in codes(lint_week(ctx + filler(4, 240) + filler(5, 300), 5, REC))
    assert "RECOVERY_DUE" not in codes(lint_week(ctx + filler(4, 330, phase="Taper"), 4, REC))


def test_a_single_session_over_five_hours_is_flagged_and_rest_weeks_are_ignored():
    assert "SESSION_TOO_LONG" in codes(lint_week([s(1, "Sunday", "Long Run", 310)], 1, REC))
    assert lint_week([s(1, "Monday", "Rest", 0)], 1, REC) == []
    assert lint_week([], 1, REC) == []


def test_lint_weeks_reports_only_the_requested_weeks():
    wks = filler(1, 300) + filler(2, 400)  # week 2 jumps, week 1 is context
    assert codes(lint_weeks(wks, {1}, REC)) == []
    assert "VOLUME_JUMP" in codes(lint_weeks(wks, {2}, REC))


def test_plan_124_week_6_moves_the_long_run_jumps_it_and_drops_a_training_day():
    """Prod 100K finish-only plan: long run Sunday -> Saturday at 213 min (was 130), ME the day after, 5 of 6 days."""
    w5 = [
        s(5, "Tuesday", "Easy", 70),
        s(5, "Wednesday", "Easy", 75),
        s(5, "Thursday", "Muscular Endurance", 55, "Zone 1"),
        s(5, "Friday", "Tempo", 65, "Zone 3"),
        s(5, "Saturday", "Easy", 45),
        s(5, "Sunday", "Long Run", 130),
    ]
    w6 = [
        s(6, "Tuesday", "Recovery", 71, "Zone 1"),
        s(6, "Wednesday", "Interval", 71, "Zone 4"),
        s(6, "Thursday", "Easy", 71),
        s(6, "Saturday", "Long Run", 213),
        s(6, "Sunday", "Muscular Endurance", 45, "Zone 1"),
    ]
    got = codes(lint_week(w5 + w6, 6, SUB, Prefs(long_run_day="Sunday", days_per_week=6)))
    assert {"LONG_RUN_DAY", "LONG_RUN_JUMP", "DAYS_SHORT", "ME_SPACING"} <= set(got)


def test_a_week_that_follows_the_athletes_schedule_has_no_preference_issues():
    wk = [s(1, d, "Easy", 50) for d in ("Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")] + [
        s(1, "Sunday", "Long Run", 90)
    ]
    got = codes(lint_week(wk, 1, SUB, Prefs(long_run_day="Sunday", days_per_week=6)))
    assert not {"LONG_RUN_DAY", "DAYS_SHORT", "LONG_RUN_JUMP"} & set(got)


def test_long_run_growth_is_measured_against_the_last_two_weeks_so_a_recovery_dip_is_not_a_trap():
    ctx = [s(1, "Sunday", "Long Run", 120), s(2, "Sunday", "Long Run", 80)] + filler(3, 300)
    assert "LONG_RUN_JUMP" not in codes(lint_week(ctx + [s(3, "Sunday", "Long Run", 125)], 3, SUB))  # +4% on 120
    assert "LONG_RUN_JUMP" in codes(lint_week(ctx + [s(3, "Sunday", "Long Run", 170)], 3, SUB))  # +42% on 120


# --- specificity against the goal's demands -------------------------------------------------

from services import goal_demands  # noqa: E402

D100 = goal_demands.compute(104.2, 5533, 14.67, 29)  # 53 m D+/km, longest session 300 min


def _build(long_min, long_gain, long_dist=None, hard=True, weeks=(1, 2, 3, 4, 5, 6, 7, 8)):
    out = []
    for wk in weeks:
        phase = "Peak" if wk >= 7 else "Build"
        out.append(s(wk, "Saturday", "Long Run", long_min, gain=long_gain, dist=long_dist, phase=phase))
        out.append(s(wk, "Tuesday", "Easy", 60, phase=phase))
        if hard:
            out.append(s(wk, "Wednesday", "Tempo", 50, zone="Zone 3", phase=phase))
    return out


def test_time_on_feet_flags_a_plan_whose_longest_session_stays_short():
    plan = _build(120, 600, long_dist=20)
    issues = lint_weeks(plan, {7, 8}, SUB, Prefs(days_per_week=6, demands=D100))
    assert "TIME_ON_FEET" in codes(issues)
    good = _build(280, 900, long_dist=30)
    assert "TIME_ON_FEET" not in codes(lint_weeks(good, {7, 8}, SUB, Prefs(days_per_week=6, demands=D100)))


def test_time_on_feet_respects_what_the_athletes_days_can_hold():
    plan = _build(70, 600, long_dist=10)  # a 3-day novice cannot do better than this
    issues = lint_weeks(plan, {7, 8}, NOV, Prefs(days_per_week=3, demands=D100))
    assert "TIME_ON_FEET" not in codes(issues)


def test_long_run_gradient_flags_flat_long_runs_on_a_steep_course():
    flat = _build(280, 0, long_dist=30)
    assert "LONG_RUN_GRADIENT" in codes(lint_weeks(flat, {7, 8}, SUB, Prefs(demands=D100)))
    steep = _build(280, 1100, long_dist=30)  # 37 m D+/km >= 60% of 53
    assert "LONG_RUN_GRADIENT" not in codes(lint_weeks(steep, {7, 8}, SUB, Prefs(demands=D100)))


def test_gradient_is_judged_against_the_athletes_training_mountain():
    d = goal_demands.compute(104.2, 5533, 14.67, 29, venue_climb_rate=28.0)  # Núi Châu Thới
    plan = _build(280, 520, long_dist=30)  # 17 m D+/km: below 60% of 28 -> 16.8? just above
    assert "LONG_RUN_GRADIENT" not in codes(lint_weeks(plan, {7, 8}, SUB, Prefs(demands=d)))
    assert "LONG_RUN_GRADIENT" in codes(lint_weeks(_build(280, 200, long_dist=30), {7, 8}, SUB, Prefs(demands=d)))


def test_flat_only_athletes_and_skipped_mountain_days_are_not_a_gradient_defect():
    flat = _build(280, 0, long_dist=30)
    assert "LONG_RUN_GRADIENT" not in codes(lint_weeks(flat, {7, 8}, SUB, Prefs(demands=D100, flat_only=True)))
    skipped = [{**w, "mountain_mode": "skip"} if w["type"] == "Long Run" else w for w in flat]
    assert "LONG_RUN_GRADIENT" not in codes(lint_weeks(skipped, {7, 8}, SUB, Prefs(demands=D100)))


def test_specificity_late_flags_a_build_with_no_hard_or_hill_work():
    plan = _build(280, 0, long_dist=30, hard=False)
    assert "SPECIFICITY_LATE" in codes(lint_weeks(plan, {7, 8}, SUB, Prefs(demands=D100, flat_only=True)))
    assert "SPECIFICITY_LATE" not in codes(lint_weeks(_build(280, 900, long_dist=30), {7, 8}, SUB, Prefs(demands=D100)))


def test_no_demands_no_new_codes_and_blocks_without_a_peak_are_skipped():
    plan = _build(120, 0, long_dist=20)
    new = {"TIME_ON_FEET", "LONG_RUN_GRADIENT", "SPECIFICITY_LATE"}
    assert not new & set(codes(lint_weeks(plan, {7, 8}, SUB, Prefs())))
    assert not new & set(codes(lint_weeks(plan, {1, 2}, SUB, Prefs(demands=D100))))
