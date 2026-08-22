"""Integration tests for the coach roster overview aggregation
(get_roster_overview_data / GET /api/coaching/overview). See
docs/superpowers/specs/2026-08-22-coach-dashboard-overview-design.md."""

from sqlalchemy import text

from db import create_plan, engine, get_plan_workouts, get_roster_overview_data, save_workouts, update_workout_log


def _create_user(email: str) -> int:
    from db import create_or_get_user

    return create_or_get_user(email, email.split("@")[0].capitalize(), "mock", f"mock-{email}")["id"]


def _link_active(coach_id: int, athlete_id: int) -> None:
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO coach_athletes (coach_id, athlete_id, status) VALUES (:c, :a, 'active')"),
            {"c": coach_id, "a": athlete_id},
        )
        conn.commit()


def _make_plan_with_workouts(athlete_id: int, current_week: int, total_weeks: int = 12) -> int:
    """A plan at `current_week` with one workout per day for weeks
    current_week-1 and current_week (the adherence/mix window), plus a
    week current_week+1 workout tagged 'taper' for phase-alert tests."""
    plan_id = create_plan(
        user_id=athlete_id,
        race_name="Test 50K",
        race_date="2026-12-01",
        goal_type="finish",
        target_time_hours=8.0,
        total_weeks=total_weeks,
        plan_status="active",
    )
    with engine.connect() as conn:
        conn.execute(text("UPDATE plans SET current_week = :w WHERE id = :pid"), {"w": current_week, "pid": plan_id})
        conn.commit()
    days = ["Monday", "Tuesday", "Wednesday"]
    workouts = []
    for week in [max(1, current_week - 1), current_week, current_week + 1]:
        for day in days:
            workouts.append(
                {
                    "week_number": week,
                    "day_of_week": day,
                    "phase": "taper" if week == current_week + 1 else "build",
                    "title": f"{day} run",
                    "type": "easy_run" if day != "Wednesday" else "tempo",
                    "duration_minutes": 45,
                    "target_zone": "Z2",
                }
            )
    save_workouts(plan_id, workouts, auto_approve=True)
    return plan_id


class TestGetRosterOverviewData:
    def test_athlete_with_no_active_plan_has_null_active_plan(self):
        coach_id = _create_user("overview-coach1@uphill.ai")
        athlete_id = _create_user("overview-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)

        data = get_roster_overview_data(coach_id)

        assert len(data["athletes"]) == 1
        assert data["athletes"][0]["athlete_id"] == athlete_id
        assert data["athletes"][0]["active_plan"] is None
        assert data["athletes"][0]["adherence_pct_14d"] is None
        assert data["athletes"][0]["missed_streak"] == 0

    def test_adherence_counts_only_resolved_workouts_in_window(self):
        coach_id = _create_user("overview-coach2@uphill.ai")
        athlete_id = _create_user("overview-athlete2@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = _make_plan_with_workouts(athlete_id, current_week=5)

        window_workouts = [w for w in get_plan_workouts(plan_id) if w["week_number"] in (4, 5)]
        # Mark 4 of the 6 window workouts completed, 1 missed, 1 left unresolved (future).
        for w in window_workouts[:4]:
            update_workout_log(w["id"], is_completed=1)
        update_workout_log(window_workouts[4]["id"], is_missed=1)

        data = get_roster_overview_data(coach_id)
        athlete = data["athletes"][0]
        assert athlete["active_plan"]["plan_id"] == plan_id
        assert athlete["active_plan"]["current_week"] == 5
        # 5 resolved (4 completed + 1 missed), 4 completed -> 4/5
        assert athlete["adherence_pct_14d"] == 0.8

    def test_missed_streak_counts_consecutive_recent_misses_only(self):
        coach_id = _create_user("overview-coach3@uphill.ai")
        athlete_id = _create_user("overview-athlete3@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = _make_plan_with_workouts(athlete_id, current_week=5)

        past_workouts = [w for w in get_plan_workouts(plan_id) if w["week_number"] <= 5]
        # Mark the two most recent (by week/day order) as missed, the third before that completed.
        update_workout_log(past_workouts[-1]["id"], is_missed=1)
        update_workout_log(past_workouts[-2]["id"], is_missed=1)
        update_workout_log(past_workouts[-3]["id"], is_completed=1)

        data = get_roster_overview_data(coach_id)
        assert data["athletes"][0]["missed_streak"] == 2

    def test_last_completed_reports_most_recent_completed_workout(self):
        coach_id = _create_user("overview-coach4@uphill.ai")
        athlete_id = _create_user("overview-athlete4@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = _make_plan_with_workouts(athlete_id, current_week=5)

        all_workouts = get_plan_workouts(plan_id)
        update_workout_log(all_workouts[0]["id"], is_completed=1)  # earliest
        update_workout_log(all_workouts[3]["id"], is_completed=1)  # later -> should win

        data = get_roster_overview_data(coach_id)
        last = data["athletes"][0]["last_completed"]
        assert last["week_number"] == all_workouts[3]["week_number"]
        assert last["day_of_week"] == all_workouts[3]["day_of_week"]

    def test_phase_alerts_flag_this_week_and_next_week(self):
        coach_id = _create_user("overview-coach5@uphill.ai")
        athlete_id = _create_user("overview-athlete5@uphill.ai")
        _link_active(coach_id, athlete_id)
        _make_plan_with_workouts(athlete_id, current_week=5)  # week 6 is tagged 'taper'

        data = get_roster_overview_data(coach_id)
        alerts = data["phase_alerts"]
        assert any(
            a["athlete_id"] == athlete_id and a["phase"] == "taper" and a["starts"] == "next_week" for a in alerts
        )
        assert not any(a["starts"] == "this_week" for a in alerts)  # week 5 is tagged 'build'

    def test_action_items_include_draft_plans_and_pending_approvals(self):
        coach_id = _create_user("overview-coach6@uphill.ai")
        athlete_id = _create_user("overview-athlete6@uphill.ai")
        _link_active(coach_id, athlete_id)
        create_plan(
            user_id=athlete_id,
            race_name="Draft Race",
            race_date="2027-01-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=10,
            plan_status="draft",
        )
        plan_id = create_plan(
            user_id=athlete_id,
            race_name="Pending Race",
            race_date="2027-02-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=10,
            plan_status="active",
        )
        save_workouts(
            plan_id,
            [
                {
                    "week_number": 1,
                    "day_of_week": "Monday",
                    "phase": "base",
                    "title": "Long run",
                    "type": "long_run",
                    "duration_minutes": 60,
                    "target_zone": "Z2",
                }
            ],
            auto_approve=False,
        )

        data = get_roster_overview_data(coach_id)
        assert len(data["action_items"]["draft_plans"]) == 1
        assert data["action_items"]["draft_plans"][0]["race_name"] == "Draft Race"
        assert len(data["action_items"]["pending_workout_approvals"]) == 1
        assert data["action_items"]["pending_workout_approvals"][0]["title"] == "Long run"

    def test_workout_type_mix_only_counts_completed_workouts_in_window(self):
        coach_id = _create_user("overview-coach7@uphill.ai")
        athlete_id = _create_user("overview-athlete7@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = _make_plan_with_workouts(athlete_id, current_week=5)

        window_workouts = [w for w in get_plan_workouts(plan_id) if w["week_number"] in (4, 5)]
        for w in window_workouts:
            if w["type"] == "easy_run":
                update_workout_log(w["id"], is_completed=1)

        data = get_roster_overview_data(coach_id)
        mix = {row["type"]: row for row in data["workout_type_mix"]}
        assert "easy_run" in mix
        assert "tempo" not in mix  # none marked completed
        assert mix["easy_run"]["pct"] == 1.0

    def test_only_active_roster_status_athletes_are_scoped(self):
        coach_id = _create_user("overview-coach8@uphill.ai")
        invited_athlete_id = _create_user("overview-athlete8@uphill.ai")
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO coach_athletes (coach_id, athlete_id, status) VALUES (:c, :a, 'invited')"),
                {"c": coach_id, "a": invited_athlete_id},
            )
            conn.commit()

        data = get_roster_overview_data(coach_id)
        assert data["athletes"] == []

    def test_empty_roster_returns_empty_shape(self):
        coach_id = _create_user("overview-coach9@uphill.ai")

        data = get_roster_overview_data(coach_id)
        assert data == {
            "athletes": [],
            "action_items": {"draft_plans": [], "pending_workout_approvals": []},
            "phase_alerts": [],
            "workout_type_mix": [],
        }
