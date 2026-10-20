"""Fixtures are the weeks the prod coach review found (Vietnam Highlands Trail test plans)."""

from services.athlete_tier import TIER_PROFILES
from services.plan_lint import lint_week, lint_weeks

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
