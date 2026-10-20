from services.plan_rules import missed_reason_rules, repeated_miss_days, weeks_off


def _missed(day, reason):
    return {"day_of_week": day, "is_missed": 1, "missed_reason": reason, "type": "Easy"}


def _text(lines):
    return "\n".join(lines)


def test_no_misses_no_rules():
    assert missed_reason_rules([{"type": "Easy", "is_completed": 1}]) == ([], None)


def test_busy_never_makes_up_and_does_not_cap():
    lines, cap = missed_reason_rules([_missed("Wednesday", "busy")])
    assert "never make up" in _text(lines) and "[UA-R2]" in _text(lines)
    assert cap is None


def test_unreasoned_miss_still_gets_the_no_make_up_rule():
    lines, cap = missed_reason_rules([_missed("Wednesday", None)])
    assert "[UA-R1]" in _text(lines) and cap is None


def test_two_sick_days_give_n_equals_two_and_a_no_progression_ceiling():
    lines, cap = missed_reason_rules([_missed("Monday", "sick"), _missed("Tuesday", "sick")])
    assert "first 2 training day(s) back" in _text(lines)
    assert "50% of their planned duration" in _text(lines)
    assert cap == 1.0


def test_pain_adds_cross_training_and_our_own_physio_note():
    lines, cap = missed_reason_rules([_missed("Monday", "pain")])
    assert "non-impact" in _text(lines) and "physio" in _text(lines)
    assert cap == 1.0


def test_tired_removes_long_run_and_caps_at_the_hard_band():
    lines, cap = missed_reason_rules([_missed("Monday", "tired")])
    assert "remove the long run" in _text(lines)
    assert cap == 0.90


def test_weather_substitutes_and_keeps_volume():
    lines, cap = missed_reason_rules([_missed("Monday", "weather")])
    assert "treadmill" in _text(lines) and cap is None


def test_gap_caps_three_weeks_and_five_weeks():
    assert missed_reason_rules([], weeks_off_count=3)[1] == 0.80
    assert missed_reason_rules([], weeks_off_count=5)[1] == 0.50


def test_final_two_weeks_before_race_forbid_added_quality():
    lines, _ = missed_reason_rules([_missed("Monday", "busy")], days_to_race=10)
    assert "[UA-R17]" in _text(lines)
    lines, _ = missed_reason_rules([_missed("Monday", "busy")], days_to_race=30)
    assert "[UA-R17]" not in _text(lines)


def test_sick_and_five_weeks_off_takes_the_lowest_cap():
    _, cap = missed_reason_rules([_missed("Monday", "sick")], weeks_off_count=5)
    assert cap == 0.50


def test_elevated_resting_hr_adds_a_recovery_day_rule():
    lines, _ = missed_reason_rules([], rhr_elevated=True)
    assert "[UA-R9]" in _text(lines)


def test_weeks_off_counts_trailing_weeks_with_nothing_completed():
    wos = [{"week_number": w, "type": "Easy", "is_completed": 0} for w in (1, 2, 3)]
    wos.append({"week_number": 0, "type": "Easy", "is_completed": 1})
    assert weeks_off(wos, 4) == 3
    wos[1]["is_completed"] = 1
    assert weeks_off(wos, 4) == 1


def test_repeated_miss_days_needs_two_different_weeks():
    wos = [
        {"week_number": 2, "day_of_week": "Wednesday", "is_missed": 1},
        {"week_number": 3, "day_of_week": "Wednesday", "is_missed": 1},
        {"week_number": 3, "day_of_week": "Friday", "is_missed": 1},
    ]
    assert repeated_miss_days(wos, 4) == ["Wednesday"]
