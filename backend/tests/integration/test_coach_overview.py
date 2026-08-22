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
        assert data["athletes"][0]["adherence_pct"] is None
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
        assert athlete["adherence_pct"] == 0.8

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

    def test_missed_streak_skips_unresolved_future_workout(self):
        coach_id = _create_user("overview-coach3b@uphill.ai")
        athlete_id = _create_user("overview-athlete3b@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = _make_plan_with_workouts(athlete_id, current_week=5)

        past_workouts = [w for w in get_plan_workouts(plan_id) if w["week_number"] <= 5]
        # Mark the two most recent as missed, but leave the very last (most
        # recent, "hasn't happened yet") workout completely untouched --
        # it should be skipped over, not treated as a streak-breaking resolution.
        update_workout_log(past_workouts[-2]["id"], is_missed=1)
        update_workout_log(past_workouts[-3]["id"], is_missed=1)

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

    def test_roster_data_does_not_leak_across_coaches(self):
        coach_a_id = _create_user("overview-coach10a@uphill.ai")
        coach_b_id = _create_user("overview-coach10b@uphill.ai")
        athlete_a_id = _create_user("overview-athlete10a@uphill.ai")
        athlete_b_id = _create_user("overview-athlete10b@uphill.ai")
        _link_active(coach_a_id, athlete_a_id)
        _link_active(coach_b_id, athlete_b_id)

        create_plan(
            user_id=athlete_b_id,
            race_name="Coach B Draft Race",
            race_date="2027-01-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=10,
            plan_status="draft",
        )

        data = get_roster_overview_data(coach_a_id)

        assert len(data["athletes"]) == 1
        assert data["athletes"][0]["athlete_id"] == athlete_a_id
        assert all(a["athlete_id"] != athlete_b_id for a in data["athletes"])
        assert all(p["race_name"] != "Coach B Draft Race" for p in data["action_items"]["draft_plans"])

    def test_empty_roster_returns_empty_shape(self):
        coach_id = _create_user("overview-coach9@uphill.ai")

        data = get_roster_overview_data(coach_id)
        assert data == {
            "athletes": [],
            "action_items": {"draft_plans": [], "pending_workout_approvals": []},
            "phase_alerts": [],
            "workout_type_mix": [],
            "adherence_trend": [],
            "missed_by_day": [],
        }

    def test_runner_level_boundaries(self):
        from db import runner_level

        assert runner_level(19.9) == "beginner"
        assert runner_level(20.0) == "intermediate"
        assert runner_level(49.9) == "intermediate"
        assert runner_level(50.0) == "advanced"
        assert runner_level(89.9) == "advanced"
        assert runner_level(90.0) == "elite"
        assert runner_level(None) == "intermediate"  # falls back to the 30.0 default

    def test_athlete_entries_include_runner_level_and_needs_attention(self):
        coach_id = _create_user("levels-coach1@uphill.ai")
        athlete_id = _create_user("levels-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)
        with engine.connect() as conn:
            conn.execute(text("UPDATE users SET current_weekly_km = 95 WHERE id = :id"), {"id": athlete_id})
            conn.commit()

        data = get_roster_overview_data(coach_id)
        athlete = data["athletes"][0]
        assert athlete["runner_level"] == "elite"
        assert athlete["needs_attention"] is False  # no plan, no alerts, no action items

    def test_needs_attention_true_for_draft_plan_only(self):
        coach_id = _create_user("levels-coach2@uphill.ai")
        athlete_id = _create_user("levels-athlete2@uphill.ai")
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

        data = get_roster_overview_data(coach_id)
        assert data["athletes"][0]["needs_attention"] is True

    def test_needs_attention_true_for_pending_approval_only(self):
        coach_id = _create_user("levels-coach3@uphill.ai")
        athlete_id = _create_user("levels-athlete3@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = create_plan(
            user_id=athlete_id,
            race_name="Active Race",
            race_date="2027-01-01",
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
        assert data["athletes"][0]["needs_attention"] is True

    def test_needs_attention_true_for_missed_streak_only(self):
        # Do NOT use _make_plan_with_workouts: it always tags current_week+1 as 'taper',
        # which would trip has_phase_alert and confound this test. Instead, build a plan
        # directly with all weeks tagged 'build' (non-alert phase).
        coach_id = _create_user("levels-coach4@uphill.ai")
        athlete_id = _create_user("levels-athlete4@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = create_plan(
            user_id=athlete_id,
            race_name="Missed Streak Race",
            race_date="2026-12-01",
            goal_type="finish",
            target_time_hours=8.0,
            total_weeks=12,
            plan_status="active",
        )
        with engine.connect() as conn:
            conn.execute(text("UPDATE plans SET current_week = 5 WHERE id = :pid"), {"pid": plan_id})
            conn.commit()
        # All weeks in and around the window tagged 'build' -- no peak/taper/race phase anywhere.
        workouts = [
            {
                "week_number": wk,
                "day_of_week": d,
                "phase": "build",
                "title": "Run",
                "type": "easy_run",
                "duration_minutes": 45,
                "target_zone": "Z2",
            }
            for wk in (4, 5, 6)
            for d in ("Monday", "Tuesday", "Wednesday")
        ]
        save_workouts(plan_id, workouts, auto_approve=True)
        # Mark the most recent workout from the past (week 5 or earlier) as missed.
        all_workouts = get_plan_workouts(plan_id)
        past_workouts = [w for w in all_workouts if w["week_number"] <= 5]
        update_workout_log(past_workouts[-1]["id"], is_missed=1)

        data = get_roster_overview_data(coach_id)
        assert data["athletes"][0]["needs_attention"] is True

    def test_needs_attention_true_for_phase_alert_only(self):
        # Test the phase-alert case directly: active plan with taper/peak/race phase
        # this week or next week, but no draft plan, no pending approval, and no missed streak.
        coach_id = _create_user("levels-coach4b@uphill.ai")
        athlete_id = _create_user("levels-athlete4b@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = create_plan(
            user_id=athlete_id,
            race_name="Phase Alert Race",
            race_date="2026-12-01",
            goal_type="finish",
            target_time_hours=8.0,
            total_weeks=12,
            plan_status="active",
        )
        with engine.connect() as conn:
            conn.execute(text("UPDATE plans SET current_week = 5 WHERE id = :pid"), {"pid": plan_id})
            conn.commit()
        # Weeks 4 and 5 are 'build', but week 6 (next_week) is tagged 'taper' (alert phase).
        workouts = [
            {
                "week_number": wk,
                "day_of_week": d,
                "phase": "taper" if wk == 6 else "build",
                "title": "Run",
                "type": "easy_run",
                "duration_minutes": 45,
                "target_zone": "Z2",
            }
            for wk in (4, 5, 6)
            for d in ("Monday", "Tuesday", "Wednesday")
        ]
        save_workouts(plan_id, workouts, auto_approve=True)
        for w in get_plan_workouts(plan_id):
            update_workout_log(w["id"], is_completed=1)

        data = get_roster_overview_data(coach_id)
        assert data["athletes"][0]["needs_attention"] is True

    def test_needs_attention_false_for_healthy_athlete(self):
        # Deliberately does NOT use _make_plan_with_workouts: that helper always
        # tags the current_week+1 week 'taper', which would always trip the
        # phase-alert condition and make this test's own assertion wrong.
        coach_id = _create_user("levels-coach5@uphill.ai")
        athlete_id = _create_user("levels-athlete5@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = create_plan(
            user_id=athlete_id,
            race_name="Healthy Race",
            race_date="2026-12-01",
            goal_type="finish",
            target_time_hours=8.0,
            total_weeks=12,
            plan_status="active",
        )
        with engine.connect() as conn:
            conn.execute(text("UPDATE plans SET current_week = 5 WHERE id = :pid"), {"pid": plan_id})
            conn.commit()
        # All weeks in and around the window tagged 'build' -- no peak/taper/race phase anywhere.
        workouts = [
            {
                "week_number": wk,
                "day_of_week": d,
                "phase": "build",
                "title": "Run",
                "type": "easy_run",
                "duration_minutes": 45,
                "target_zone": "Z2",
            }
            for wk in (4, 5, 6)
            for d in ("Monday", "Tuesday", "Wednesday")
        ]
        save_workouts(plan_id, workouts, auto_approve=True)
        for w in get_plan_workouts(plan_id):
            update_workout_log(w["id"], is_completed=1)

        data = get_roster_overview_data(coach_id)
        assert data["athletes"][0]["needs_attention"] is False

    def test_default_days_matches_previous_fixed_two_week_window(self):
        coach_id = _create_user("window-coach1@uphill.ai")
        athlete_id = _create_user("window-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = _make_plan_with_workouts(athlete_id, current_week=5)
        window_workouts = [w for w in get_plan_workouts(plan_id) if w["week_number"] in (4, 5)]
        for w in window_workouts[:4]:
            update_workout_log(w["id"], is_completed=1)
        update_workout_log(window_workouts[4]["id"], is_missed=1)

        data = get_roster_overview_data(coach_id)  # no days arg -> default 14
        assert data["athletes"][0]["adherence_pct"] == 0.8

    def test_days_30_widens_the_window_beyond_two_weeks(self):
        coach_id = _create_user("window-coach2@uphill.ai")
        athlete_id = _create_user("window-athlete2@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = create_plan(
            user_id=athlete_id,
            race_name="Test 50K",
            race_date="2026-12-01",
            goal_type="finish",
            target_time_hours=8.0,
            total_weeks=12,
            plan_status="active",
        )
        with engine.connect() as conn:
            conn.execute(text("UPDATE plans SET current_week = :w WHERE id = :pid"), {"w": 5, "pid": plan_id})
            conn.commit()
        # Weeks 1-5: one workout each, all completed. days=30 -> window_weeks = ceil(30/7) = 5 -> weeks 1-5.
        # days=14 -> window_weeks = 2 -> weeks 4-5 only.
        workouts = [
            {
                "week_number": wk,
                "day_of_week": "Monday",
                "phase": "build",
                "title": "Run",
                "type": "easy_run",
                "duration_minutes": 45,
                "target_zone": "Z2",
            }
            for wk in range(1, 6)
        ]
        save_workouts(plan_id, workouts, auto_approve=True)
        for w in get_plan_workouts(plan_id):
            update_workout_log(w["id"], is_completed=1)

        data_14 = get_roster_overview_data(coach_id, days=14)
        data_30 = get_roster_overview_data(coach_id, days=30)
        assert data_14["athletes"][0]["adherence_pct"] == 1.0
        assert data_30["athletes"][0]["adherence_pct"] == 1.0

    def test_adherence_trend_has_one_entry_per_week_with_resolved_data(self):
        coach_id = _create_user("trend-coach1@uphill.ai")
        athlete_id = _create_user("trend-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = _make_plan_with_workouts(athlete_id, current_week=5)
        # Week 4: mark all 3 completed. Week 5: mark 1 completed, 1 missed, leave 1 unresolved.
        by_week = {}
        for w in get_plan_workouts(plan_id):
            by_week.setdefault(w["week_number"], []).append(w)
        for w in by_week[4]:
            update_workout_log(w["id"], is_completed=1)
        update_workout_log(by_week[5][0]["id"], is_completed=1)
        update_workout_log(by_week[5][1]["id"], is_missed=1)

        data = get_roster_overview_data(coach_id, days=14)
        trend = {row["week_number"]: row["adherence_pct"] for row in data["adherence_trend"]}
        assert trend[4] == 1.0
        assert trend[5] == 0.5  # 1 completed / 2 resolved (1 unresolved excluded)

    def test_missed_by_day_counts_only_missed_workouts_in_window(self):
        coach_id = _create_user("missedday-coach1@uphill.ai")
        athlete_id = _create_user("missedday-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = _make_plan_with_workouts(athlete_id, current_week=5)
        by_day = {(w["week_number"], w["day_of_week"]): w for w in get_plan_workouts(plan_id)}
        update_workout_log(by_day[(5, "Monday")]["id"], is_missed=1)
        update_workout_log(by_day[(4, "Monday")]["id"], is_missed=1)
        update_workout_log(by_day[(5, "Wednesday")]["id"], is_completed=1)  # not missed -> excluded

        data = get_roster_overview_data(coach_id, days=14)
        by_day_result = {row["day_of_week"]: row["count"] for row in data["missed_by_day"]}
        assert by_day_result["Monday"] == 2
        assert "Wednesday" not in by_day_result


def _admin_headers(client):
    resp = client.post("/api/auth/mock-login", json={"email": "admin@uphill.ai"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def _make_coach(client, email="overview-make-coach@uphill.ai"):
    resp = client.post("/api/auth/mock-login", json={"email": email})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    user_id = data["user"]["id"]
    headers = {"Authorization": f"Bearer {data['session_token']}"}
    promote = client.post(
        f"/api/admin/users/{user_id}/coach-status", json={"is_coach": True}, headers=_admin_headers(client)
    )
    assert promote.status_code == 200, promote.text
    return headers, user_id


class TestOverviewEndpoint:
    def test_returns_200_with_expected_top_level_shape(self, client):
        coach_headers, coach_id = _make_coach(client, "overview-endpoint-coach1@uphill.ai")
        athlete_id = _create_user("overview-endpoint-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)

        resp = client.get("/api/coaching/overview", headers=coach_headers)

        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {
            "athletes",
            "action_items",
            "phase_alerts",
            "workout_type_mix",
            "adherence_trend",
            "missed_by_day",
        }
        assert len(body["athletes"]) == 1
        assert body["athletes"][0]["athlete_id"] == athlete_id

    def test_non_coach_gets_403(self, client):
        resp = client.post("/api/auth/mock-login", json={"email": "overview-endpoint-noncoach@uphill.ai"})
        headers = {"Authorization": f"Bearer {resp.json()['session_token']}"}

        resp = client.get("/api/coaching/overview", headers=headers)

        assert resp.status_code == 403

    def test_get_coaching_overview_endpoint_accepts_days_param(self, client):
        coach_headers, coach_id = _make_coach(client, "window-endpoint-coach1@uphill.ai")
        athlete_id = _create_user("window-endpoint-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)

        resp = client.get("/api/coaching/overview?days=30", headers=coach_headers)

        assert resp.status_code == 200
        assert "athletes" in resp.json()
