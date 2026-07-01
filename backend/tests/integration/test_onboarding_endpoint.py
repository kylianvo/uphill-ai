"""Regression test for the plan_start_date onboarding bug.

POST /api/auth/onboarding used to silently ignore a user-submitted
plan_start_date and always hardcode start_date = date.today() (OnboardingRequest
had no plan_start_date field at all, so Pydantic dropped it, and the handler
in main.py never read it). Fixed by adding the field to OnboardingRequest and
using request.plan_start_date when present.

This test is written first in the integration suite because it validates the
whole pipeline (DB + auth + background-job neutralization) end to end on a
real, understood bug -- everything else in this suite builds on the same
fixtures.
"""

from datetime import date

from db import get_active_plan

FAR_FUTURE_START_DATE = "2027-03-15"  # deliberately far from "today" so a regression is unmistakable


def test_onboarding_uses_submitted_plan_start_date_not_today(client, auth_headers, mock_plan_generation):
    resp = client.post(
        "/api/auth/onboarding",
        headers=auth_headers["headers"],
        json={
            "goal_type": "race",
            "race_name": "Test 50K",
            "race_date": "2027-05-01",
            "days_per_week": 4,
            "plan_start_date": FAR_FUTURE_START_DATE,
        },
    )

    assert resp.status_code == 200, resp.text

    plan = get_active_plan(auth_headers["user_id"])
    assert plan is not None
    assert plan["start_date"] == FAR_FUTURE_START_DATE
    assert plan["start_date"] != date.today().strftime("%Y-%m-%d")


def test_onboarding_defaults_to_today_when_plan_start_date_omitted(client, auth_headers, mock_plan_generation):
    """plan_start_date is optional -- omitting it entirely should still work,
    falling back to today (this is the one case where "today" is correct)."""
    resp = client.post(
        "/api/auth/onboarding",
        headers=auth_headers["headers"],
        json={
            "goal_type": "race",
            "race_name": "Test 50K",
            "race_date": "2027-05-01",
            "days_per_week": 4,
        },
    )

    assert resp.status_code == 200, resp.text
    plan = get_active_plan(auth_headers["user_id"])
    assert plan["start_date"] == date.today().strftime("%Y-%m-%d")


def test_onboarding_recalculates_total_weeks_from_submitted_start_date(client, auth_headers, mock_plan_generation):
    """total_weeks must be derived from the real start date, not always from
    today -- otherwise a correct start_date fix could still ship alongside a
    stale/incorrect week count (this was the second half of the original bug)."""
    resp = client.post(
        "/api/auth/onboarding",
        headers=auth_headers["headers"],
        json={
            "goal_type": "race",
            "race_name": "Test 50K",
            "race_date": "2026-12-06",
            "days_per_week": 4,
            "plan_start_date": "2026-08-23",
        },
    )

    assert resp.status_code == 200, resp.text
    plan = get_active_plan(auth_headers["user_id"])
    assert plan["total_weeks"] == 17  # same math verified in tests/unit/test_onboarding_helpers.py
