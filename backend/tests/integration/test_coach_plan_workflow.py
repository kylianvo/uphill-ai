"""Integration tests for Phase 3: coach-triggered plan generation, draft
review, workout edit/add, and approval. See
docs/superpowers/specs/2026-07-20-coach-role-design.md and
docs/superpowers/plans/2026-07-20-coach-role-phase3-plan-workflow.md."""

from sqlalchemy import text

from db import create_plan, engine, get_active_plan, get_plan_by_id, get_recent_plans


def _create_user(email: str) -> int:
    from db import create_or_get_user

    return create_or_get_user(email, email.split("@")[0].capitalize(), "mock", f"mock-{email}")["id"]


class TestSchemaAndPlanStatusFilter:
    def test_create_plan_defaults_to_active_status_and_owner_as_creator(self):
        user_id = _create_user("schema-plan-owner@uphill.ai")
        plan_id = create_plan(
            user_id=user_id,
            race_name="Test 50K",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
        )
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT plan_status, created_by_user_id, approved_by_user_id, approved_at "
                    "FROM plans WHERE id = :id"
                ),
                {"id": plan_id},
            ).fetchone()
        assert row.plan_status == "active"
        assert row.created_by_user_id == user_id
        assert row.approved_by_user_id is None
        assert row.approved_at is None

    def test_create_plan_accepts_explicit_draft_status_and_creator(self):
        athlete_id = _create_user("schema-athlete@uphill.ai")
        coach_id = _create_user("schema-coach@uphill.ai")
        plan_id = create_plan(
            user_id=athlete_id,
            race_name="Coach Draft 50K",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
            created_by_user_id=coach_id,
            plan_status="draft",
        )
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT plan_status, created_by_user_id, user_id FROM plans WHERE id = :id"), {"id": plan_id}
            ).fetchone()
        assert row.plan_status == "draft"
        assert row.created_by_user_id == coach_id
        assert row.user_id == athlete_id

    def test_get_active_plan_ignores_draft_plans(self):
        athlete_id = _create_user("schema-athlete2@uphill.ai")
        create_plan(
            user_id=athlete_id,
            race_name="Draft Only",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
            plan_status="draft",
        )
        assert get_active_plan(athlete_id) is None

    def test_get_active_plan_returns_the_active_plan_even_with_a_newer_draft(self):
        athlete_id = _create_user("schema-athlete3@uphill.ai")
        active_id = create_plan(
            user_id=athlete_id,
            race_name="Active Plan",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
        )
        create_plan(
            user_id=athlete_id,
            race_name="Newer Draft",
            race_date="2027-06-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
            plan_status="draft",
        )
        active = get_active_plan(athlete_id)
        assert active["id"] == active_id

    def test_get_recent_plans_excludes_drafts(self):
        athlete_id = _create_user("schema-athlete4@uphill.ai")
        create_plan(
            user_id=athlete_id,
            race_name="Active",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
        )
        create_plan(
            user_id=athlete_id,
            race_name="Draft",
            race_date="2027-06-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
            plan_status="draft",
        )
        plans = get_recent_plans(athlete_id, limit=10)
        assert len(plans) == 1
        assert plans[0]["race_name"] == "Active"

    def test_workouts_default_source_is_ai_generated(self):
        athlete_id = _create_user("schema-athlete5@uphill.ai")
        plan_id = create_plan(
            user_id=athlete_id,
            race_name="Test",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
        )
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO workouts (plan_id, week_number, day_of_week, phase, title, type,
                        duration_minutes, target_zone)
                    VALUES (:pid, 1, 'Monday', 'Base', 'Easy Run', 'run', 45, 'zone2')
                """),
                {"pid": plan_id},
            )
            conn.commit()
            row = conn.execute(
                text("SELECT source, last_edited_by_user_id FROM workouts WHERE plan_id = :pid"), {"pid": plan_id}
            ).fetchone()
        assert row.source == "ai_generated"
        assert row.last_edited_by_user_id is None


class TestGetPlanById:
    def test_returns_the_plan_regardless_of_status(self):
        athlete_id = _create_user("planbyid-athlete@uphill.ai")
        draft_id = create_plan(
            user_id=athlete_id,
            race_name="Draft Lookup",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
            plan_status="draft",
        )
        plan = get_plan_by_id(draft_id)
        assert plan["id"] == draft_id
        assert plan["plan_status"] == "draft"

    def test_returns_none_for_unknown_id(self):
        assert get_plan_by_id(999999) is None


def _admin_headers(client):
    resp = client.post("/api/auth/mock-login", json={"email": "admin@uphill.ai"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def _make_coach(client, email="make-coach@uphill.ai"):
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


def _link_coach_and_athlete(client, coach_headers, athlete_email):
    athlete_resp = client.post("/api/auth/mock-login", json={"email": athlete_email})
    athlete_headers = {"Authorization": f"Bearer {athlete_resp.json()['session_token']}"}
    athlete_id = athlete_resp.json()["user"]["id"]
    invite = client.post("/api/coaching/invite", json={"athlete_email": athlete_email}, headers=coach_headers).json()
    client.post(f"/api/coaching/invites/{invite['id']}/accept", headers=athlete_headers)
    return athlete_headers, athlete_id


def _generate_plan_payload(race_name="Test 50K"):
    return {
        "goal_type": "finish",
        "race_name": race_name,
        "race_date": "2027-05-01",
        "plan_start_date": "2027-03-15",
        "days_per_week": 4,
    }


class TestCoachGeneratePlanEndpoint:
    def test_self_serve_generate_plan_is_unaffected(self, client, mock_plan_generation, auth_headers):
        """Regression guard for the _generate_plan_for_athlete extraction:
        the self-serve endpoint's response shape and plan_status must be
        byte-for-byte the same as before the refactor."""
        resp = client.post("/api/coach/generate-plan", json=_generate_plan_payload(), headers=auth_headers["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["active"] is True
        assert body["plan"]["race_name"] == "Test 50K"
        assert "job_id" in body

        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT plan_status, created_by_user_id FROM plans WHERE id = :id"), {"id": body["plan"]["id"]}
            ).fetchone()
        assert row.plan_status == "active"
        assert row.created_by_user_id == auth_headers["user_id"]

    def test_coach_can_generate_a_draft_plan_for_an_athlete(self, client, mock_plan_generation):
        coach_headers, coach_id = _make_coach(client, "genplan-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "genplan-athlete1@uphill.ai")

        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/generate-plan",
            json=_generate_plan_payload("Coach Draft 50K"),
            headers=coach_headers,
        )
        assert resp.status_code == 200, resp.text
        plan_id = resp.json()["plan"]["id"]

        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT plan_status, created_by_user_id, user_id FROM plans WHERE id = :id"), {"id": plan_id}
            ).fetchone()
        assert row.plan_status == "draft"
        assert row.created_by_user_id == coach_id
        assert row.user_id == athlete_id

    def test_draft_plan_does_not_appear_as_the_athletes_active_plan(self, client, mock_plan_generation):
        coach_headers, _ = _make_coach(client, "genplan-coach2@uphill.ai")
        athlete_headers, athlete_id = _link_coach_and_athlete(client, coach_headers, "genplan-athlete2@uphill.ai")
        client.post(
            f"/api/coaching/athletes/{athlete_id}/generate-plan",
            json=_generate_plan_payload("Hidden Draft"),
            headers=coach_headers,
        )

        self_serve = client.get("/api/coach/active-plan", headers=athlete_headers)
        assert self_serve.json() == {"active": False}

        coach_view = client.get(f"/api/coaching/athletes/{athlete_id}/active-plan", headers=coach_headers)
        assert coach_view.json() == {"active": False}

    def test_non_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "genplan-coach3@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/generate-plan",
            json=_generate_plan_payload(),
            headers=coach_headers,
        )
        assert resp.status_code == 403


class TestDraftReviewEndpoint:
    def test_returns_no_draft_when_none_exists(self, client):
        coach_headers, _ = _make_coach(client, "draft-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "draft-athlete1@uphill.ai")
        resp = client.get(f"/api/coaching/athletes/{athlete_id}/plans/draft", headers=coach_headers)
        assert resp.status_code == 200
        assert resp.json() == {"draft": False}

    def test_coach_can_review_the_draft_they_generated(self, client, mock_plan_generation):
        coach_headers, _ = _make_coach(client, "draft-coach2@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "draft-athlete2@uphill.ai")
        client.post(
            f"/api/coaching/athletes/{athlete_id}/generate-plan",
            json=_generate_plan_payload("Review Me"),
            headers=coach_headers,
        )

        resp = client.get(f"/api/coaching/athletes/{athlete_id}/plans/draft", headers=coach_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["draft"] is True
        assert body["plan"]["race_name"] == "Review Me"
        assert isinstance(body["workouts"], list)

    def test_athlete_can_also_see_their_own_draft_via_this_endpoint(self, client, mock_plan_generation):
        """Athletes are technically allowed to call athlete-scoped coaching
        routes on themselves (require_athlete_access grants self-access) --
        and a draft they didn't create and hasn't been approved still shows
        up here if they do, since 'draft' status alone (not who created it)
        is what this endpoint surfaces. Documenting the intentional
        behavior rather than leaving it untested."""
        coach_headers, _ = _make_coach(client, "draft-coach3@uphill.ai")
        athlete_headers, athlete_id = _link_coach_and_athlete(client, coach_headers, "draft-athlete3@uphill.ai")
        client.post(
            f"/api/coaching/athletes/{athlete_id}/generate-plan",
            json=_generate_plan_payload("Self View"),
            headers=coach_headers,
        )
        resp = client.get(f"/api/coaching/athletes/{athlete_id}/plans/draft", headers=athlete_headers)
        assert resp.status_code == 200
        assert resp.json()["draft"] is True

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "draft-coach4@uphill.ai")
        resp = client.get(f"/api/coaching/athletes/{auth_headers['user_id']}/plans/draft", headers=coach_headers)
        assert resp.status_code == 403


def _seed_workout(plan_id: int, **overrides) -> int:
    fields = {
        "week_number": 1,
        "day_of_week": "Monday",
        "phase": "Base",
        "title": "Easy Run",
        "type": "run",
        "duration_minutes": 45,
        "target_zone": "zone2",
    }
    fields.update(overrides)
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                INSERT INTO workouts (plan_id, week_number, day_of_week, phase, title, type,
                    duration_minutes, target_zone)
                VALUES (:pid, :week_number, :day_of_week, :phase, :title, :type,
                    :duration_minutes, :target_zone)
                RETURNING id
            """),
            {"pid": plan_id, **fields},
        )
        conn.commit()
        return row.scalar()


class TestEditWorkoutEndpoint:
    def test_coach_can_edit_a_workout_on_the_athletes_plan(self, client):
        coach_headers, coach_id = _make_coach(client, "editwo-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "editwo-athlete1@uphill.ai")
        plan_id = create_plan(
            user_id=athlete_id,
            race_name="Edit Target",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
        )
        workout_id = _seed_workout(plan_id)

        resp = client.put(
            f"/api/coaching/athletes/{athlete_id}/plans/{plan_id}/workouts/{workout_id}",
            json={"title": "Coach-Adjusted Long Run", "duration_minutes": 90},
            headers=coach_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["title"] == "Coach-Adjusted Long Run"
        assert body["duration_minutes"] == 90
        assert body["source"] == "coach_edited"
        assert body["last_edited_by_user_id"] == coach_id

    def test_edit_404s_when_workout_does_not_belong_to_the_plan(self, client):
        coach_headers, _ = _make_coach(client, "editwo-coach2@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "editwo-athlete2@uphill.ai")
        plan_id = create_plan(
            user_id=athlete_id,
            race_name="Plan A",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
        )
        other_plan_id = create_plan(
            user_id=athlete_id,
            race_name="Plan B",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
        )
        workout_id = _seed_workout(other_plan_id)

        resp = client.put(
            f"/api/coaching/athletes/{athlete_id}/plans/{plan_id}/workouts/{workout_id}",
            json={"title": "Should Not Apply"},
            headers=coach_headers,
        )
        assert resp.status_code == 404

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "editwo-coach3@uphill.ai")
        plan_id = create_plan(
            user_id=auth_headers["user_id"],
            race_name="No Link",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
        )
        workout_id = _seed_workout(plan_id)
        resp = client.put(
            f"/api/coaching/athletes/{auth_headers['user_id']}/plans/{plan_id}/workouts/{workout_id}",
            json={"title": "Nope"},
            headers=coach_headers,
        )
        assert resp.status_code == 403


class TestAddWorkoutEndpoint:
    def test_coach_can_add_a_new_workout_to_the_athletes_plan(self, client):
        coach_headers, coach_id = _make_coach(client, "addwo-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "addwo-athlete1@uphill.ai")
        plan_id = create_plan(
            user_id=athlete_id,
            race_name="Add Target",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
        )

        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/plans/{plan_id}/workouts",
            json={
                "week_number": 2,
                "day_of_week": "Wednesday",
                "phase": "Base",
                "title": "Hill Repeats",
                "type": "interval",
                "duration_minutes": 60,
                "target_zone": "zone4",
            },
            headers=coach_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["title"] == "Hill Repeats"
        assert body["source"] == "coach_created"
        assert body["last_edited_by_user_id"] == coach_id
        assert body["plan_id"] == plan_id

        workouts = client.get(
            f"/api/coaching/athletes/{athlete_id}/plans/{plan_id}/workouts", headers=coach_headers
        ).json()["workouts"]
        assert any(w["title"] == "Hill Repeats" for w in workouts)

    def test_add_404s_when_plan_does_not_belong_to_athlete(self, client):
        coach_headers, _ = _make_coach(client, "addwo-coach2@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "addwo-athlete2@uphill.ai")
        other_athlete_id = _create_user("addwo-other-athlete@uphill.ai")
        other_plan_id = create_plan(
            user_id=other_athlete_id,
            race_name="Not This Athlete",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
        )

        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/plans/{other_plan_id}/workouts",
            json={
                "week_number": 1,
                "day_of_week": "Monday",
                "phase": "Base",
                "title": "Should Not Insert",
                "type": "run",
                "duration_minutes": 30,
                "target_zone": "zone2",
            },
            headers=coach_headers,
        )
        assert resp.status_code == 404

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "addwo-coach3@uphill.ai")
        plan_id = create_plan(
            user_id=auth_headers["user_id"],
            race_name="No Link",
            race_date="2027-05-01",
            goal_type="finish",
            target_time_hours=None,
            total_weeks=8,
        )
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/plans/{plan_id}/workouts",
            json={
                "week_number": 1,
                "day_of_week": "Monday",
                "phase": "Base",
                "title": "Nope",
                "type": "run",
                "duration_minutes": 30,
                "target_zone": "zone2",
            },
            headers=coach_headers,
        )
        assert resp.status_code == 403
