"""Unit tests for workout date derivation -- no DB, no network.

workouts rows carry week_number + day_of_week but no date. These helpers are
the single source of truth for turning those into a calendar date; both the
matcher and the ICS export must use them, or they can disagree about which day
a session belongs to.
"""

from datetime import date

from services.workout_calendar import plan_start_monday, workout_date


class TestWorkoutDate:
    def test_week_one_monday_is_the_start_monday(self):
        assert workout_date(date(2026, 9, 7), 1, "Monday") == date(2026, 9, 7)

    def test_day_of_week_offsets_within_the_week(self):
        assert workout_date(date(2026, 9, 7), 1, "Saturday") == date(2026, 9, 12)

    def test_later_weeks_advance_by_seven_days(self):
        assert workout_date(date(2026, 9, 7), 3, "Monday") == date(2026, 9, 21)

    def test_unknown_day_name_falls_back_to_monday(self):
        # Plan generation has produced odd day strings before; a bad day name
        # must not raise mid-sync.
        assert workout_date(date(2026, 9, 7), 1, "Funday") == date(2026, 9, 7)


class TestPlanStartMonday:
    def test_uses_plan_start_date_when_present(self):
        # 2026-09-09 is a Wednesday; the plan's week 1 Monday is the 7th.
        assert plan_start_monday("2026-09-09", [], date(2026, 12, 5)) == date(2026, 9, 7)

    def test_falls_back_to_race_anchored_dates_for_legacy_plans(self):
        workouts = [
            {"week_number": 1, "day_of_week": "Monday", "title": "Easy", "type": "EASY"},
            {"week_number": 4, "day_of_week": "Saturday", "title": "Target Event", "type": "RACE"},
        ]
        # Race in week 4 on a Saturday -> start Monday is 3 weeks + 5 days earlier.
        assert plan_start_monday(None, workouts, date(2026, 12, 5)) == date(2026, 11, 9)

    def test_malformed_plan_start_date_falls_back_rather_than_raising(self):
        workouts = [{"week_number": 1, "day_of_week": "Monday", "title": "Easy", "type": "EASY"}]
        assert plan_start_monday("not-a-date", workouts, date(2026, 12, 5)) is not None
