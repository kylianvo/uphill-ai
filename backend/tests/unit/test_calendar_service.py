"""Tests for CalendarService.generate_ics_string — used by the public
/api/coach/export-ics endpoint."""

from services.calendar_service import CalendarService


def make_workout(**overrides):
    wo = {
        "plan_id": 1,
        "week_number": 1,
        "day_of_week": "Monday",
        "title": "Easy Run",
        "type": "Easy",
        "phase": "Base",
        "duration_minutes": 45,
        "treadmill_incline": "0",
        "treadmill_speed": "0",
    }
    wo.update(overrides)
    return wo


class TestGenerateIcsString:
    def test_default_treadmill_fields_do_not_crash_export(self):
        # Regression test: treadmill_incline/treadmill_speed are TEXT range
        # strings (default "0"), not numbers. A numeric comparison against
        # the default here previously raised TypeError on every export.
        out = CalendarService.generate_ics_string("2026-09-01", [make_workout()])
        assert "Treadmill" not in out

    def test_treadmill_range_string_is_included_in_description(self):
        workouts = [make_workout(title="Hill Sprints", treadmill_incline="7.3-9.3", treadmill_speed="8.2-9.2")]
        out = CalendarService.generate_ics_string("2026-09-01", workouts)
        unfolded = out.replace("\r\n ", "")
        assert "Treadmill: Incline 7.3-9.3% | Speed 8.2-9.2 kph" in unfolded

    def test_missing_treadmill_fields_do_not_crash_export(self):
        workouts = [make_workout(title="Rest Day", type="Rest", duration_minutes=0)]
        del workouts[0]["treadmill_incline"]
        del workouts[0]["treadmill_speed"]
        out = CalendarService.generate_ics_string("2026-09-01", workouts)
        assert "Treadmill" not in out
