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
