"""Integration tests for block_reviews' Gemini-authored narrative columns
(upsert_block_review_ai_fields / get_block_review_narrative), and their
exposure through get_block_completion. See PlanGenerator.generate_week_narrative
for where the text itself comes from."""

from db import (
    create_or_get_user,
    create_plan,
    get_block_completion,
    get_block_review_narrative,
    save_block_review,
    upsert_block_review_ai_fields,
)


def _create_plan() -> int:
    user = create_or_get_user("ai-narrative-test@uphill.ai", "Ai Narrative Test", "mock", "mock-ai-narrative-test")
    return create_plan(
        user_id=user["id"],
        race_name="Test 50K",
        race_date="2027-05-01",
        goal_type="finish",
        target_time_hours=None,
        total_weeks=12,
        plan_status="active",
    )


def test_upsert_creates_a_new_row_when_none_exists():
    plan_id = _create_plan()
    upsert_block_review_ai_fields(plan_id, 1, ai_this_week_description="Focus on aerobic base this week.")

    narrative = get_block_review_narrative(plan_id, 1)
    assert narrative["ai_this_week_description"] == "Focus on aerobic base this week."
    assert narrative["ai_last_week_review"] is None


def test_upsert_updates_existing_row_without_touching_the_other_ai_field():
    plan_id = _create_plan()
    upsert_block_review_ai_fields(plan_id, 2, ai_this_week_description="Build week focus.")
    upsert_block_review_ai_fields(plan_id, 2, ai_last_week_review="Last week went well.")

    narrative = get_block_review_narrative(plan_id, 2)
    assert narrative["ai_this_week_description"] == "Build week focus."
    assert narrative["ai_last_week_review"] == "Last week went well."


def test_upsert_does_not_clobber_the_athletes_own_rpe_and_notes():
    """save_block_review (athlete-submitted RPE/notes) and upsert_block_review_ai_fields
    (Gemini narrative) must both be able to land on the same block_number without
    either one erasing the other's fields, regardless of which runs first."""
    plan_id = _create_plan()
    save_block_review(plan_id, 3, overall_rpe=7, notes="Felt strong on the long run.")
    upsert_block_review_ai_fields(plan_id, 3, ai_last_week_review="Great consistency, 100% completion.")

    narrative = get_block_review_narrative(plan_id, 3)
    assert narrative["ai_last_week_review"] == "Great consistency, 100% completion."

    # The AI write must not have touched the athlete's own row.
    from db import get_block_reviews

    reviews = [r for r in get_block_reviews(plan_id) if r["block_number"] == 3]
    assert any(r["overall_rpe"] == 7 and r["notes"] == "Felt strong on the long run." for r in reviews)


def test_get_block_completion_surfaces_the_narrative_fields():
    plan_id = _create_plan()
    upsert_block_review_ai_fields(
        plan_id,
        1,
        ai_last_week_review="Reviewed.",
        ai_this_week_description="Described.",
    )

    completion = get_block_completion(plan_id, 1)
    assert completion["ai_last_week_review"] == "Reviewed."
    assert completion["ai_this_week_description"] == "Described."


def test_get_block_completion_returns_none_narrative_when_nothing_recorded():
    plan_id = _create_plan()
    completion = get_block_completion(plan_id, 1)
    assert completion["ai_last_week_review"] is None
    assert completion["ai_this_week_description"] is None


def test_upsert_with_no_fields_is_a_no_op():
    plan_id = _create_plan()
    upsert_block_review_ai_fields(plan_id, 1)  # both fields default to None

    from db import get_block_reviews

    assert get_block_reviews(plan_id) == []
