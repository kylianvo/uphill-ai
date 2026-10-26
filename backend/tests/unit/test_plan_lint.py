"""Fixtures are the weeks the prod coach review found (Vietnam Highlands Trail test plans)."""

from services.athlete_tier import TIER_PROFILES, for_race
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
    assert (
        "35%" in jump.message
    )  # ME is not volume: 290 run minutes vs 215 and "cap the increase at 10%" in jump.message.lower()


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


def test_specificity_runs_on_the_last_pre_taper_week_when_no_peak_phase_is_labelled():
    # an 11-week plan: Base 1-4, Build 5-8, Taper 9, Race 10, Recovery 11; the model never writes "Peak"
    plan = []
    for wk in range(1, 9):
        phase = "Base" if wk <= 4 else "Build"
        plan += [
            s(wk, "Sunday", "Long Run", 120, gain=0, dist=20, phase=phase),
            s(wk, "Tuesday", "Easy", 60, phase=phase),
        ]
    prefs = Prefs(days_per_week=6, demands=D100, flat_only=True, total_weeks=11)
    got = codes(lint_weeks(plan, {8}, SUB, prefs))
    assert "TIME_ON_FEET" in got
    assert "TIME_ON_FEET" not in codes(lint_weeks(plan, {5}, SUB, prefs))  # earlier weeks are not judged yet


# --- ultra specificity: down weeks, back-to-back weekends, climbing load ----------------------------

D100_ULTRA = goal_demands.compute(104.2, 5533, 14.67, 29)


def _week(wk, rows, phase="Build"):
    return [
        s(wk, day, kind, minutes, zone=zone, phase=phase, title=title or kind)
        for day, kind, minutes, zone, title in rows
    ]


def test_a_hard_session_in_a_recovery_week_is_flagged_but_not_in_a_build_week():
    build = _week(
        3,
        [
            ("Tuesday", "Easy", 80, "Zone 2", None),
            ("Friday", "Tempo", 55, "Zone 3", None),
            ("Sunday", "Long Run", 150, "Zone 2", None),
        ],
    )
    deload = _week(
        4,
        [
            ("Tuesday", "Easy", 60, "Zone 2", None),
            ("Friday", "Tempo", 55, "Zone 3", None),
            ("Sunday", "Long Run", 105, "Zone 2", None),
        ],
    )
    plan = build + deload
    assert "HARD_IN_DOWN_WEEK" in codes(lint_weeks(plan, {4}, SUB, Prefs()))
    assert "HARD_IN_DOWN_WEEK" not in codes(lint_weeks(plan, {3}, SUB, Prefs()))


def test_ultra_back_to_back_weekend_is_allowed_in_the_last_build_weeks_with_a_larger_long_run_share():
    rows5 = [
        ("Tuesday", "Easy", 90, "Zone 2", None),
        ("Wednesday", "Easy", 80, "Zone 2", None),
        ("Thursday", "Easy", 80, "Zone 2", None),
        ("Saturday", "Easy", 120, "Zone 2", None),
        ("Sunday", "Long Run", 175, "Zone 2", None),
    ]
    rows6 = [
        ("Tuesday", "Easy", 80, "Zone 2", None),
        ("Wednesday", "Easy", 70, "Zone 2", None),
        ("Thursday", "Easy", 60, "Zone 2", None),
        ("Saturday", "Easy", 150, "Zone 2", None),
        ("Sunday", "Long Run", 240, "Zone 2", None),
    ]
    plan = _week(5, rows5) + _week(6, rows6)
    prefs = Prefs(demands=D100_ULTRA, total_weeks=11)
    got = codes(lint_weeks(plan, {6}, SUB, prefs))
    assert "BACK_TO_BACK" not in got and "LONG_SHARE" not in got
    early = codes(lint_weeks(plan, {6}, SUB, Prefs(demands=D100_ULTRA, total_weeks=20)))
    assert "BACK_TO_BACK" in early  # far from the race it is still a defect


def test_every_build_me_session_is_climbing_work_for_a_steep_race_without_hills():
    gym = _week(
        6,
        [
            ("Wednesday", "Muscular Endurance", 50, "Zone 2", "Gym ME box step-ups"),
            ("Sunday", "Long Run", 150, "Zone 2", None),
        ],
    )
    prefs = Prefs(days_per_week=6, demands=D100_ULTRA, total_weeks=11, flat_only=True)
    assert "CLIMB_SPECIFICITY" in codes(lint_weeks(gym, {6}, SUB, prefs))
    stairs = [{**w, "title": "Weighted stair climbing laps"} if w["type"] == "Muscular Endurance" else w for w in gym]
    assert "CLIMB_SPECIFICITY" not in codes(lint_weeks(stairs, {6}, SUB, prefs))
    assert "CLIMB_SPECIFICITY" not in codes(
        lint_weeks(gym, {6}, SUB, Prefs(days_per_week=6, demands=D100_ULTRA, total_weeks=11))
    )  # hills nearby
    base = _week(2, [("Wednesday", "Muscular Endurance", 50, "Zone 2", "Gym ME")], phase="Base")
    assert "CLIMB_SPECIFICITY" not in codes(lint_weeks(base, {2}, SUB, prefs))  # gym ME is right early in the base


def test_the_second_ultra_window_week_asks_for_a_back_to_back_weekend_when_none_happened():
    def quiet(wk):
        return _week(
            wk,
            [
                ("Tuesday", "Easy", 80, "Zone 2", None),
                ("Wednesday", "Easy", 70, "Zone 2", None),
                ("Saturday", "Easy", 60, "Zone 2", None),
                ("Sunday", "Long Run", 150, "Zone 2", None),
            ],
        )

    plan = quiet(6) + quiet(7)
    prefs = Prefs(demands=D100_ULTRA, total_weeks=11)
    assert "B2B_MISSING" in codes(lint_weeks(plan, {7}, SUB, prefs))
    assert "B2B_MISSING" not in codes(lint_weeks(plan, {6}, SUB, prefs))  # the first week may still do it
    done = _week(
        6,
        [
            ("Tuesday", "Easy", 80, "Zone 2", None),
            ("Saturday", "Easy", 150, "Zone 2", None),
            ("Sunday", "Long Run", 240, "Zone 2", None),
        ],
    ) + quiet(7)
    assert "B2B_MISSING" not in codes(lint_weeks(done, {7}, SUB, prefs))


# --- findings from the persona runs ---------------------------------------------------------------------


def test_sub_elite_hundred_milers_may_run_an_eight_hour_day_everyone_else_stays_at_five_hours():
    from services.athlete_tier import session_cap_minutes

    mile100 = goal_demands.compute(161, 8000, None, 36)
    assert session_cap_minutes(SUB, 161) == 480 and session_cap_minutes(SUB, 104) == 300
    assert session_cap_minutes(REC, 161) == 300
    week = _week(
        10,
        [
            ("Tuesday", "Easy", 70, "Zone 2", None),
            ("Saturday", "Long Run", 400, "Zone 2", None),
            ("Sunday", "Long Run", 180, "Zone 2", None),
        ],
    )
    prefs = Prefs(demands=mile100, total_weeks=16)
    assert "SESSION_TOO_LONG" not in codes(lint_weeks(week, {10}, SUB, prefs))
    assert "SESSION_TOO_LONG" in codes(lint_weeks(week, {10}, REC, prefs))
    assert "SESSION_TOO_LONG" in codes(
        lint_weeks(
            _week(10, [("Saturday", "Long Run", 400, "Zone 2", None)]),
            {10},
            SUB,
            Prefs(demands=D100_ULTRA, total_weeks=16),
        )
    )


def test_the_taper_week_must_be_lighter_and_may_keep_a_larger_long_run_share():
    build = _week(
        9,
        [
            ("Tuesday", "Easy", 80, "Zone 2", None),
            ("Thursday", "Easy", 80, "Zone 2", None),
            ("Sunday", "Long Run", 180, "Zone 2", None),
        ],
    )
    heavy = _week(
        10,
        [
            ("Tuesday", "Easy", 80, "Zone 2", None),
            ("Thursday", "Easy", 80, "Zone 2", None),
            ("Sunday", "Long Run", 170, "Zone 2", None),
        ],
        phase="Taper",
    )
    assert "TAPER_NOT_LIGHT" in codes(lint_weeks(build + heavy, {10}, REC, Prefs()))
    light = _week(
        10,
        [
            ("Tuesday", "Easy", 55, "Zone 2", None),
            ("Thursday", "Easy", 50, "Zone 2", None),
            ("Sunday", "Long Run", 72, "Zone 2", None),
        ],
        phase="Taper",
    )
    got = codes(lint_weeks(build + light, {10}, REC, Prefs()))
    assert "TAPER_NOT_LIGHT" not in got and "LONG_SHARE" not in got  # 95/180 = 53%: taper weeks may hold more


def test_vietnamese_climbing_words_count_as_climbing_work():
    gym = _week(6, [("Wednesday", "Muscular Endurance", 50, "Zone 2", "ME bước lên bục")], "Build")
    stairs = _week(6, [("Wednesday", "Muscular Endurance", 50, "Zone 2", "ME leo cầu thang mang tạ")], "Build")
    prefs = Prefs(demands=D100_ULTRA, total_weeks=11, flat_only=True)
    assert "CLIMB_SPECIFICITY" in codes(lint_weeks(gym, {6}, SUB, prefs))
    assert "CLIMB_SPECIFICITY" not in codes(lint_weeks(stairs, {6}, SUB, prefs))


def test_the_back_to_back_ask_moves_to_the_next_week_when_the_first_fell_on_a_recovery_week():
    def quiet(wk, scale=1.0):
        return _week(
            wk,
            [
                ("Tuesday", "Easy", round(80 * scale), "Zone 2", None),
                ("Wednesday", "Easy", round(70 * scale), "Zone 2", None),
                ("Saturday", "Easy", round(60 * scale), "Zone 2", None),
                ("Sunday", "Long Run", round(150 * scale), "Zone 2", None),
            ],
        )

    prefs = Prefs(demands=D100_ULTRA, total_weeks=13)  # two-step taper: the asks sit one week earlier, 8 and 9
    plan = quiet(7) + quiet(8, 0.7) + quiet(9)  # week 8 is a recovery week
    assert "B2B_MISSING" not in codes(lint_weeks(plan, {8}, SUB, prefs))
    assert "B2B_MISSING" in codes(lint_weeks(plan, {9}, SUB, prefs))


# --- ultras on a mountain day: Quang's ladder (services/ultra_rules.py) ----------------------------

from dataclasses import replace  # noqa: E402

from services.plan_lint import week_minutes  # noqa: E402

REC = TIER_PROFILES["recreational"]
ULTRA_PREFS = Prefs(long_run_day="Saturday", mountain_day=True, total_weeks=20, demands=D100_ULTRA)


def test_me_not_counted_in_week_minutes():
    assert week_minutes([s(1, "Tuesday", "Easy", 60), s(1, "Thursday", "Muscular Endurance", 45)]) == 60


def test_ladder_step_is_not_a_long_run_jump():
    # 180 -> 240 is +33% (over MAX_LONG_RUN_GROWTH 25%, step 60 > 20), and ladder("100k", False, 20)[3] == 240
    wk = filler(2, 300) + [s(2, "Saturday", "Long Run", 180)]
    wk += [s(3, "Tuesday", "Easy", 60), s(3, "Saturday", "Long Run", 240)]
    assert "LONG_RUN_JUMP" not in codes(lint_week(wk, 3, REC, ULTRA_PREFS))


def test_same_jump_without_mountain_day_is_flagged():
    wk = filler(2, 300) + [s(2, "Saturday", "Long Run", 180)]
    wk += [s(3, "Tuesday", "Easy", 60), s(3, "Saturday", "Long Run", 240)]
    assert "LONG_RUN_JUMP" in codes(lint_week(wk, 3, REC, replace(ULTRA_PREFS, mountain_day=False)))


def test_weekday_short_and_ladder_short():
    wk = [s(9, "Tuesday", "Easy", 45, phase="Build"), s(9, "Saturday", "Long Run", 200, phase="Build")]
    got = codes(lint_week(wk, 9, REC, ULTRA_PREFS))
    assert "WEEKDAY_SHORT" in got and "ULTRA_LADDER" in got


def test_short_hill_sprint_run_is_not_a_short_weekday_run():
    sprints = s(9, "Thursday", "Easy", 35, phase="Build")
    sprints["title"] = "Hill Sprints"
    wk = [s(9, "Tuesday", "Easy", 60, phase="Build"), sprints, s(9, "Saturday", "Long Run", 300, phase="Build")]
    assert "WEEKDAY_SHORT" not in codes(lint_week(wk, 9, REC, ULTRA_PREFS))


def test_no_b2b_missing_for_ladder_plans():
    # week 16 of 20 is total - 4 - taper_shift: today's B2B_MISSING ask week
    wk = [s(16, "Tuesday", "Easy", 60, phase="Peak"), s(16, "Saturday", "Long Run", 420, phase="Peak")]
    assert "B2B_MISSING" not in codes(lint_week(wk, 16, REC, ULTRA_PREFS))
    assert "B2B_MISSING" in codes(lint_week(wk, 16, REC, replace(ULTRA_PREFS, mountain_day=False)))


def test_quality_count_only_in_the_window():
    base = [
        s(5, "Tuesday", "Interval", 60, zone="Zone 3", phase="Base"),
        s(5, "Saturday", "Long Run", 240, phase="Base"),
    ]
    assert "QUALITY_COUNT" in codes(lint_week(base, 5, REC, ULTRA_PREFS))  # week 5 is before the window
    window = [s(10, "Thursday", "Easy", 60, phase="Build"), s(10, "Saturday", "Long Run", 300, phase="Build")]
    assert "QUALITY_COUNT" in codes(lint_week(window, 10, REC, ULTRA_PREFS))  # window week with none
    window.append(s(10, "Tuesday", "Interval", 75, zone="Zone 3", phase="Build"))
    assert "QUALITY_COUNT" not in codes(lint_week(window, 10, REC, ULTRA_PREFS))
    sprints = s(5, "Wednesday", "Interval", 30, zone="Zone 5", phase="Base", title="Hill Sprints")
    assert "QUALITY_COUNT" not in codes(lint_week(base[1:] + [sprints], 5, REC, ULTRA_PREFS))


def test_me_load_on_ladder_plans():
    wk = [
        s(3, "Monday", "Muscular Endurance", 40),
        s(3, "Thursday", "Muscular Endurance", 40),
        s(3, "Saturday", "Long Run", 120),
    ]
    assert "ME_LOAD" not in codes(lint_week(wk, 3, REC, Prefs()))  # non-ladder plans: the prompt sets no ME limit
    assert "ME_LOAD" in codes(lint_week(wk, 3, REC, ULTRA_PREFS))
    ok = [s(3, "Monday", "Muscular Endurance", 30), s(3, "Wednesday", "Easy", 200), s(3, "Saturday", "Long Run", 150)]
    two = [
        s(3, "Monday", "Muscular Endurance", 30),
        s(3, "Wednesday", "Muscular Endurance", 30),
        s(3, "Thursday", "Easy", 300),
        s(3, "Saturday", "Long Run", 300),
    ]
    assert "ME_LOAD" not in codes(lint_week(two, 3, SUB, ULTRA_PREFS))  # advanced, Base: 2 sessions, 60 of 660 min
    assert "ME_LOAD" in codes(lint_week(two, 3, REC, ULTRA_PREFS))
    assert "ME_LOAD" not in codes(lint_week(ok, 3, REC, Prefs()))


def _ladder_prefs(**kw):
    from services import goal_demands

    d = goal_demands.compute(104.2, 5533, 15.75, None)
    return Prefs(long_run_day="Saturday", days_per_week=6, demands=d, total_weeks=20, mountain_day=True, **kw)


def _ladder_week(wk, long_min, b2b=0, phase="Peak"):
    rows = [
        s(wk, "Tuesday", "Easy", 60, phase=phase),
        s(wk, "Wednesday", "Easy", 60, phase=phase),
        s(wk, "Thursday", "Easy", 60, phase=phase),
        s(wk, "Friday", "Easy", 60, phase=phase),
        s(wk, "Saturday", "Long Run", long_min, phase=phase),
    ]
    if b2b:
        rows.append(s(wk, "Sunday", "Easy", b2b, phase=phase, title="Back-to-back day (Zone 2)"))
    return rows


def test_back_to_back_weekend_holds_the_ladder_rung():
    """Week 16 of a 20-week 100K is the 7 h rung; 5 h + 2 h 45 holds it when the athlete chose a back-to-back."""
    ctx = _ladder_week(14, 300) + _ladder_week(15, 360)
    week16 = _ladder_week(16, 300, b2b=165)
    ultra = for_race(REC, 104.2, True)
    found = codes(lint_weeks(ctx + week16, {16}, ultra, _ladder_prefs(back_to_back=True)))
    assert "ULTRA_LADDER" not in found
    week16_single = _ladder_week(16, 300) + [s(16, "Sunday", "Easy", 90, phase="Peak")]  # not a lighter week
    assert "ULTRA_LADDER" in codes(lint_weeks(ctx + week16_single, {16}, ultra, _ladder_prefs()))


def test_mid_week_start_asks_for_the_days_left_in_week_one():
    """A Thursday start leaves 4 days: three run days and a mountain day are a full week 1, not DAYS_SHORT."""
    wk1 = [
        s(1, "Thursday", "Easy", 60),
        s(1, "Friday", "Easy", 60),
        s(1, "Saturday", "Long Run", 180),
        s(1, "Sunday", "Easy", 45),
    ]
    prefs = Prefs(days_per_week=6, start_load_minutes=600, first_week_share=4 / 7)
    assert "DAYS_SHORT" not in codes(lint_weeks(wk1, {1}, REC, prefs))
    assert "DAYS_SHORT" in codes(lint_weeks(wk1[:3], {1}, REC, prefs))


def test_week_after_a_recovery_week_is_held_to_the_week_before_it():
    """The generator measures week 5 against week 3 (week 4 is a recovery week); so does DAYS_SHORT's room."""
    week3 = _ladder_week(3, 240, phase="Build")[1:]  # 3 weekday runs
    week4 = [s(4, "Tuesday", "Easy", 30, phase="Build"), s(4, "Saturday", "Long Run", 180, phase="Build")]
    week5 = _ladder_week(5, 240, phase="Build")[1:]  # held at week 3's rest of the week: no room for a 4th run
    found = lint_weeks(week3 + week4 + week5, {5}, for_race(REC, 104.2, True), _ladder_prefs())
    assert "DAYS_SHORT" not in codes(found)
