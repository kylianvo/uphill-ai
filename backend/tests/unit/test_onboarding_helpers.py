"""Pure-function tests for the onboarding date/age helpers in main.py.

These are the exact functions whose interaction with a wrong "start date"
input caused the plan_start_date production bug: _calculate_total_weeks
takes a start date as an argument and had been silently called with
date.today() instead of the user's chosen date. This file locks down the
math so a future regression can't hide inside it.
"""

from datetime import date

from main import _calculate_total_weeks, _compute_age, _parse_time_hours


class TestCalculateTotalWeeks:
    def test_three_weeks_out_uses_minimum_of_three_plus_two(self):
        # race is less than 3 weeks from start -> weeks_to_race floors at 3
        start = date(2026, 1, 5)  # Monday
        assert _calculate_total_weeks("2026-01-12", start) == 5  # max(1, 3) + 2

    def test_far_future_race_scales_with_weeks_between_mondays(self):
        start = date(2026, 8, 23)  # Sunday
        assert _calculate_total_weeks("2026-12-06", start) == 17

    def test_result_depends_on_start_date_not_a_fixed_reference(self):
        # Same race date, two different start dates -> different totals.
        # This is the exact invariant the production bug violated (start
        # date was ignored and "today" was used for every request).
        race = "2026-12-06"
        weeks_from_july = _calculate_total_weeks(race, date(2026, 7, 1))
        weeks_from_august = _calculate_total_weeks(race, date(2026, 8, 23))
        assert weeks_from_july != weeks_from_august


class TestComputeAge:
    def test_computes_age_from_dob(self):
        assert _compute_age("2000-01-15", 30, date(2026, 6, 1)) == 26

    def test_falls_back_to_default_when_dob_missing(self):
        assert _compute_age(None, 42, date(2026, 6, 1)) == 42

    def test_falls_back_to_default_on_unparseable_dob(self):
        assert _compute_age("not-a-date", 42, date(2026, 6, 1)) == 42


class TestParseTimeHours:
    def test_parses_hh_mm_ss(self):
        assert _parse_time_hours("4:30:00") == 4.5

    def test_parses_h_mm(self):
        # Two-part format is H:MM (hours:minutes), matching expected race
        # finish times like "4:30" -- not MM:SS.
        assert _parse_time_hours("4:30") == 4.5

    def test_returns_none_for_empty_input(self):
        assert _parse_time_hours(None) is None
        assert _parse_time_hours("") is None

    def test_returns_none_for_garbage_input(self):
        assert _parse_time_hours("not-a-time") is None
