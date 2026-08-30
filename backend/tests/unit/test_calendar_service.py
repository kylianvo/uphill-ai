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

    def test_anchors_from_plan_start_date_when_provided(self):
        # Regression test: a block-generated plan only has the FIRST couple
        # weeks of workouts loaded (no "Race"-tagged workout yet, since
        # that's in the final block) -- the legacy race-date-backward math
        # then silently anchored week 1 to right before race_date instead of
        # the plan's actual start, producing wildly wrong exported dates for
        # any in-progress plan. plan_start_date_str must anchor forward
        # instead, exactly like the app's own getWorkoutDateObj.
        workouts = [make_workout(week_number=1, day_of_week="Thursday", title="Aerobic Base Incline Run")]
        out = CalendarService.generate_ics_string(
            "2026-10-28",
            workouts,
            plan_start_date_str="2026-08-27",  # a Thursday
        )
        assert "DTSTART;VALUE=DATE:20260827" in out

    def test_falls_back_to_race_date_anchoring_when_no_plan_start_date(self):
        # Legacy plans (created before plan_start_date was stored) keep the
        # old race-date-backward behavior.
        workouts = [
            make_workout(week_number=1, day_of_week="Monday"),
            make_workout(week_number=2, day_of_week="Saturday", title="Target Event", type="Race"),
        ]
        out = CalendarService.generate_ics_string("2026-09-06", workouts)  # a Sunday
        # The race workout's day_of_week gets relabeled to race_date's actual
        # weekday (Sunday) first, so race week's Monday is race_date - 6 days;
        # week 1 Monday is a further 7 days before that.
        assert "DTSTART;VALUE=DATE:20260824" in out
