from services import ultra_rules as u
from services.athlete_tier import taper_weeks
from services.plan_generator import PlanGenerator


def test_band_edges():
    assert u.band_for(44.9) is None
    assert u.band_for(45) == "50k" and u.band_for(89.99) == "50k"
    assert u.band_for(90) == "100k" and u.band_for(98) == "100k" and u.band_for(139.9) == "100k"
    assert u.band_for(140) == "100mi" and u.band_for(None) is None


def test_applies_needs_a_mountain_day():
    assert u.applies(100, ()) is None
    assert u.applies(100, ("Saturday",)) == "100k"


def test_100k_ladder_20_weeks():
    lad = u.ladder("100k", False, 20)  # peak_week = 20 - 3 - 1 = 16; deloads 4, 8, 12 and 15 (before the peak)
    assert [lad[w] for w in (1, 2, 3, 5)] == [180, 180, 240, 240]
    assert lad[4] == 180 and lad[8] == lad[12] == lad[15] == 240  # a rung below the last build week, 4 h at most
    assert lad[14] == 360 and lad[16] == 420
    assert set(lad) == set(range(1, 17))


def test_100mi_advanced_peaks_at_8h_and_50k_at_5h():
    assert u.ladder("100mi", True, 20)[16] == 480
    assert u.ladder("100mi", False, 20)[16] == 420
    lad = u.ladder("50k", False, 16)  # peak 12, recovery week 11
    assert lad[12] == 300 and lad[10] == 270 and lad[11] == 180 and lad[1] == 180 and lad[4] == 180


def test_short_plan_enters_late_and_never_jumps_more_than_an_hour():
    lad = u.ladder("100k", False, 8)  # peak_week 5
    assert lad[5] == 420 and lad[1] >= 180
    assert u.long_run_target("100k", False, 5, 8, recent_longest=240) == 300
    assert u.long_run_target("100k", False, 6, 8, recent_longest=240) is None


def test_deload_matches_plan_generator():
    for total in range(6, 30):
        for w in range(1, total + 1):
            for km in (None, 56.4, 104.2):
                assert u.is_deload(w, total, km) == PlanGenerator.is_deload_week(w, total, km)


def test_numbers():
    assert u.session_cap("50k", True) == 300 and u.session_cap("100k", False) == 420
    assert u.session_cap("100mi", False) == 420 and u.session_cap("100mi", True) == 480
    assert u.weekday_minutes("50k", False) == (45, 90)
    assert u.weekday_minutes("100k", True) == (60, 90)
    assert u.weekday_minutes("100mi", True) == (60, 150)
    assert u.quality_per_week(False, False) == 1 and u.quality_per_week(True, False) == 2
    assert u.quality_per_week(True, True) == 1
    assert u.quality_work_minutes(True, False) == (40, 60) and u.quality_work_minutes(True, True) == (20, 30)
    assert [u.other_day_minutes(m) for m in (180, 240, 300, 360, 420)] == [90, 90, 60, 45, 45]


def test_quality_window_is_8_weeks_to_peak_without_deloads():
    assert u.quality_weeks(20) == frozenset({9, 10, 11, 13, 14, 16})  # peak 16, deloads 12 and 15
    assert u.quality_weeks(8) == frozenset({1, 2, 3, 5})  # short plan: the whole build, deload 4


def test_prompt_block_peak_week():
    text = u.prompt_block("100k", False, {16: 420}, 20, False, "en")
    assert "420" in text and "back-to-back" in text.lower()
    assert "1 session" in text and "20-30" in text


def test_prompt_block_gated_advanced_gets_one_minimum_dose_session():
    text = u.prompt_block("100k", True, {16: 420}, 20, True, "en")
    assert "1 session" in text and "20-30" in text and "no zone 4" in text.lower()


def test_prompt_block_outside_the_window_has_no_zone3():
    text = u.prompt_block("100k", False, {5: 240}, 20, False, "en")
    assert "no zone 3" in text.lower()


def test_prompt_block_vietnamese():
    assert "420" in u.prompt_block("100k", False, {16: 420}, 20, False, "vi")


def test_13_week_100k_recovery_weeks_step_down_a_rung():
    """Plan 131 (13 weeks): the first recovery week drops to 3 h instead of repeating week 3's 4 h; the 7 h peak
    (Quang: 6-7 h for finishers too) comes after the week-8 recovery week, not straight after the 6 h week."""
    lad = u.ladder("100k", False, 13)
    assert lad == {1: 180, 2: 180, 3: 240, 4: 180, 5: 240, 6: 300, 7: 360, 8: 240, 9: 420}


def test_back_to_back_split_adds_up_to_more_than_the_single_day():
    assert u.b2b_split(420) == (300, 165)
    assert u.b2b_split(360) == (240, 150)
    assert u.b2b_split(300) is None
    day1, day2 = u.b2b_split(420)
    assert day1 + day2 > 420


def test_prompt_block_states_the_back_to_back_weekend_only_when_chosen():
    single = u.prompt_block("100k", False, {9: 420}, 13, True, "en")
    b2b = u.prompt_block("100k", False, {9: 420}, 13, True, "en", back_to_back=True)
    assert "Long Run 420 min" in single and "No back-to-back weekend" in single
    assert "Long Run 300 min on the mountain day, then 165 min" in b2b and "No other back-to-back" in b2b
    assert "60-90 g carbs per hour" in single


def test_a_100k_short_plan_tapers_two_weeks_and_keeps_the_7h_rung():
    # 10 training weeks + recovery week: the 7 h run lands 3 weeks before the race, not 13 days
    assert taper_weeks(11, 104.2) == 2 and taper_weeks(11, 56.4) == 1
    assert u.ladder("100k", False, 11, 104.2) == {1: 180, 2: 240, 3: 240, 4: 180, 5: 300, 6: 360, 7: 420}


def test_a_short_ladder_drops_its_earliest_rungs_not_the_filler():
    # 9 training weeks: the 4 h step stays, so 3 h -> 5 h never needs the step cap to fill a 1.5 h gap
    assert u.ladder("50k", False, 10, 56.4) == {1: 180, 2: 180, 3: 180, 4: 180, 5: 240, 6: 270, 7: 300}


def test_a_peak_on_a_fourth_week_gets_its_recovery_week_just_before_it():
    # 12-week 100 km plan, peak week 8: weeks 5-8 would load four weeks in a row into the peak
    assert [w for w in range(1, 13) if u.is_deload(w, 12, 104.2)] == [4, 7]
    assert u.ladder("100k", False, 12, 104.2) == {1: 180, 2: 240, 3: 240, 4: 180, 5: 300, 6: 360, 7: 240, 8: 420}
    # 10-week 50 km plan, peak week 8: 4 h, 4 h 30, recovery, then the 5 h peak
    assert u.ladder("50k", False, 11, 56.4) == {1: 180, 2: 180, 3: 180, 4: 180, 5: 240, 6: 270, 7: 180, 8: 300}


def test_no_plan_loads_more_than_three_weeks_in_a_row_before_its_peak():
    for total in range(9, 31):
        for km in (21.1, 56.4, 104.2):
            peak = u.peak_week(total, km)
            last = max([w for w in range(1, peak) if u.is_deload(w, total, km)], default=0)
            assert peak - last <= 3 or last == 0, (total, km, peak, last)
