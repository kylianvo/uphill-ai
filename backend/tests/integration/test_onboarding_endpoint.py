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
from unittest.mock import patch

from db import get_active_plan, get_user_by_id
from services.race_matcher import MatchedRace

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


def test_onboarding_non_race_goal_never_calls_race_matcher(client, auth_headers, mock_plan_generation):
    """Non-race onboarding goals (start_running/return/recovery) fall back to
    a generic default race_name (e.g. "My Running Journey" via
    _default_plan_name). Unlike the PlannerView plan-creation site (guarded
    by is_race_or_dist), nothing should let one of these generic names
    coincidentally fuzzy-match a curated race in the KB -- the is_event
    guard in the onboarding handler must suppress the race-matcher call
    entirely for non-race goals."""
    fake_match = MatchedRace(
        race_name="Vietnam Mountain Marathon",
        distance_label="50km",
        distance_km=46.7,
        elevation_gain_m=2800,
        terrain=["rice terraces"],
        course_context="Course prose here.",
        confidence=100.0,
    )
    with patch("services.race_matcher.match_race", return_value=fake_match) as mock_match_race:
        resp = client.post(
            "/api/auth/onboarding",
            headers=auth_headers["headers"],
            json={
                "goal_type": "start_running",
                "days_per_week": 4,
            },
        )

    assert resp.status_code == 200, resp.text
    mock_match_race.assert_not_called()

    plan = get_active_plan(auth_headers["user_id"])
    assert plan is not None
    assert plan["course_distance_km"] is None
    assert plan["course_elevation_gain_m"] is None


class TestSkipPlanOnboarding:
    def test_skip_plan_saves_profile_and_completes_onboarding_without_a_plan(self, client, auth_headers):
        resp = client.post(
            "/api/auth/onboarding",
            headers=auth_headers["headers"],
            json={
                "goal_type": "race",
                "race_name": "Test 50K",
                "race_date": "2027-05-01",
                "days_per_week": 4,
                "skip_plan": True,
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "job_id" not in body
        assert "plan" not in body
        assert body["user"]["onboarding_complete"] is True

        assert get_active_plan(auth_headers["user_id"]) is None

        saved_user = get_user_by_id(auth_headers["user_id"])
        assert saved_user["onboarding_complete"] is True
        assert saved_user["goal_type"] == "race"

    def test_skip_plan_defaults_to_false_and_generates_normally(self, client, auth_headers, mock_plan_generation):
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
        assert "job_id" in resp.json()
        assert get_active_plan(auth_headers["user_id"]) is not None


def test_onboarding_keeps_treadmill_separate_from_gym(client, auth_headers, mock_plan_generation):
    for gym, treadmill in [(True, False), (False, True)]:
        resp = client.post(
            "/api/auth/onboarding",
            headers=auth_headers["headers"],
            json={
                "goal_type": "start_running",
                "has_gym_access": gym,
                "use_treadmill": treadmill,
                "current_weekly_km": 0,
            },
        )
        assert resp.status_code == 200, resp.text
        plan = get_active_plan(auth_headers["user_id"])
        assert bool(plan["use_treadmill"]) == treadmill
        assert get_user_by_id(auth_headers["user_id"])["current_weekly_km"] == 0


def test_onboarding_persists_training_zones(client, auth_headers, mock_plan_generation):
    response = client.post(
        "/api/auth/onboarding",
        headers=auth_headers["headers"],
        json={
            "goal_type": "start_running",
            "skip_plan": True,
            "max_hr": 190,
            "resting_hr": 55,
            "aet_hr": 145,
            "ant_hr": 170,
            "threshold_source": "field",
            "zone2_pace_min": "6:40",
            "zone2_pace_max": "5:50",
            "threshold_pace": "4:45",
        },
    )
    assert response.status_code == 200, response.text
    user = get_user_by_id(auth_headers["user_id"])
    for key, value in {
        "aet_hr": 145,
        "ant_hr": 170,
        "threshold_source": "field",
        "zone2_pace_min": "6:40",
        "zone2_pace_max": "5:50",
        "threshold_pace": "4:45",
    }.items():
        assert user[key] == value


def test_onboarding_rejects_invalid_training_zones(client, auth_headers, mock_plan_generation):
    for values in [
        {"zone2_pace_min": "6:99"},
        {"aet_hr": 175, "ant_hr": 160},
        {"zone2_pace_min": "5:30", "zone2_pace_max": "6:30"},
        {"zone2_pace_max": "5:30", "threshold_pace": "6:00"},
        {"threshold_pace": "0:00"},
        {"aet_hr": 250},
        {"max_hr": 250},
        {"resting_hr": -55},
        {"aet_hr": 145, "threshold_source": "field"},
    ]:
        response = client.post(
            "/api/auth/onboarding",
            headers=auth_headers["headers"],
            json={"goal_type": "start_running", "skip_plan": True, **values},
        )
        assert response.status_code == 422, response.text


def test_onboarding_passes_zones_to_first_plan(client, auth_headers, mock_plan_generation):
    import time
    from unittest.mock import AsyncMock

    with patch("main._plan_snapshot", new_callable=AsyncMock, return_value={}):
        response = client.post(
            "/api/auth/onboarding",
            headers=auth_headers["headers"],
            json={
                "goal_type": "start_running",
                "aet_hr": 145,
                "ant_hr": 170,
                "threshold_source": "field",
                "zone2_pace_min": "6:40",
                "zone2_pace_max": "5:50",
                "threshold_pace": "4:45",
            },
        )
        assert response.status_code == 200
        deadline = time.monotonic() + 3
        while not mock_plan_generation.await_args_list and time.monotonic() < deadline:
            time.sleep(0.01)
        assert mock_plan_generation.await_args_list
        profile = mock_plan_generation.await_args.args[1]
        assert profile["aet_hr"] == 145 and profile["ant_hr"] == 170
        assert profile["threshold_source"] == "field"
        assert profile["zone2_pace_min"] == "6:40" and profile["zone2_pace_max"] == "5:50"
        assert profile["threshold_pace"] == "4:45"


def test_onboarding_partial_thresholds_keep_estimated_zones_ordered(client, auth_headers, mock_plan_generation):
    for values in [{"aet_hr": 185}, {"ant_hr": 120}, {"ant_hr": 205}]:
        response = client.post(
            "/api/auth/onboarding",
            headers=auth_headers["headers"],
            json={"goal_type": "race", "skip_plan": True, **values},
        )
        assert response.status_code == 200
        user = get_user_by_id(auth_headers["user_id"])
        assert user["resting_hr"] < user["aet_hr"] < user["ant_hr"] < user["max_hr"]
        for key, value in values.items():
            assert user[key] == value


def test_onboarding_partial_easy_pace_keeps_range_ordered(client, auth_headers, mock_plan_generation):
    from main import _pace_seconds

    for values in [{"zone2_pace_min": "5:00"}, {"zone2_pace_max": "9:00"}]:
        response = client.post(
            "/api/auth/onboarding",
            headers=auth_headers["headers"],
            json={"goal_type": "race", "skip_plan": True, **values},
        )
        assert response.status_code == 200
        user = get_user_by_id(auth_headers["user_id"])
        assert _pace_seconds(user["zone2_pace_min"]) >= _pace_seconds(user["zone2_pace_max"])
        for key, value in values.items():
            assert user[key] == value


def test_new_athlete_seed_values_are_app_defaults(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "New Runner", "email": "new-runner@example.com", "password": "new-runner-pass-1"},
    )
    assert response.status_code == 200
    sources = response.json()["user"]["field_sources"]
    for field in ("max_hr", "resting_hr", "aet_hr", "ant_hr", "zone2_pace_min", "zone2_pace_max"):
        assert sources[field]["source"] == "default"
