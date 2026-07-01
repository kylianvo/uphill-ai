"""Integration tests for the core plan read/generate/select endpoints.

Every test in this file that calls _generate_plan must also depend on the
mock_plan_generation fixture (it's what actually neutralizes the background
Gemini/NotebookLM call -- see conftest.py's docstring for why it has to be a
fixture with test-scoped lifetime rather than a `with patch(...)` block
around just the POST call).
"""

import time

FAR_FUTURE_START_DATE = "2027-03-15"


def _generate_plan(client, headers, **overrides):
    payload = {
        "goal_type": "finish",
        "race_name": "Test 50K",
        "race_date": "2027-05-01",
        "plan_start_date": FAR_FUTURE_START_DATE,
        "days_per_week": 4,
    }
    payload.update(overrides)
    return client.post("/api/coach/generate-plan", headers=headers, json=payload)


class TestGeneratePlan:
    def test_uses_submitted_plan_start_date_not_today(self, client, auth_headers, mock_plan_generation):
        """Twin regression test: /api/coach/generate-plan has a second,
        near-duplicate implementation of the same plan_start_date handling
        as /api/auth/onboarding (main.py's generate_training_plan). Covering
        it independently guards against this copy regressing on its own."""
        from datetime import date

        from db import get_active_plan

        resp = _generate_plan(client, auth_headers["headers"])
        assert resp.status_code == 200, resp.text

        plan = get_active_plan(auth_headers["user_id"])
        assert plan["start_date"] == FAR_FUTURE_START_DATE
        assert plan["start_date"] != date.today().strftime("%Y-%m-%d")

    def test_missing_race_date_is_rejected_for_race_goal(self, client, auth_headers):
        resp = _generate_plan(client, auth_headers["headers"], race_date=None)
        assert resp.status_code == 400

    def test_returns_a_pollable_job_id(self, client, auth_headers, mock_plan_generation):
        resp = _generate_plan(client, auth_headers["headers"])
        assert resp.status_code == 200
        assert resp.json()["job_id"]


class TestPlanStatusPolling:
    def test_job_reaches_done_status(self, client, auth_headers, mock_plan_generation):
        gen_resp = _generate_plan(client, auth_headers["headers"])
        job_id = gen_resp.json()["job_id"]

        # The background task is neutralized to an AsyncMock returning [] by
        # mock_plan_generation, so it resolves almost immediately.
        status = None
        for _ in range(20):
            poll = client.get(f"/api/coach/plan-status/{job_id}", headers=auth_headers["headers"])
            status = poll.json()["status"]
            if status == "done":
                break
            time.sleep(0.05)
        assert status == "done"

    def test_unknown_job_id_returns_404(self, client, auth_headers):
        resp = client.get("/api/coach/plan-status/not-a-real-job-id", headers=auth_headers["headers"])
        assert resp.status_code == 404

    def test_another_users_job_is_not_visible(self, client, auth_headers, mock_plan_generation):
        gen_resp = _generate_plan(client, auth_headers["headers"])
        job_id = gen_resp.json()["job_id"]

        other_login = client.post("/api/auth/mock-login", json={"email": "other-user@uphill.ai"})
        other_headers = {"Authorization": f"Bearer {other_login.json()['session_token']}"}

        resp = client.get(f"/api/coach/plan-status/{job_id}", headers=other_headers)
        assert resp.status_code == 403


class TestActiveAndRecentPlans:
    def test_active_plan_is_false_when_none_exists(self, client, auth_headers):
        resp = client.get("/api/coach/active-plan", headers=auth_headers["headers"])
        assert resp.status_code == 200
        assert resp.json()["active"] is False

    def test_active_plan_reflects_the_most_recently_created_plan(self, client, auth_headers, mock_plan_generation):
        _generate_plan(client, auth_headers["headers"])
        resp = client.get("/api/coach/active-plan", headers=auth_headers["headers"])
        assert resp.json()["active"] is True
        assert resp.json()["plan"]["start_date"] == FAR_FUTURE_START_DATE

    def test_recent_plans_lists_created_plans(self, client, auth_headers, mock_plan_generation):
        _generate_plan(client, auth_headers["headers"], race_name="Race A")
        _generate_plan(client, auth_headers["headers"], race_name="Race B")
        resp = client.get("/api/coach/recent-plans", headers=auth_headers["headers"])
        assert resp.status_code == 200
        names = {p["race_name"] for p in resp.json()["plans"]}
        assert {"Race A", "Race B"}.issubset(names)


class TestSelectPlan:
    def test_selecting_a_plan_makes_it_active(self, client, auth_headers, mock_plan_generation):
        first = _generate_plan(client, auth_headers["headers"], race_name="Older Plan")
        first_plan_id = first.json()["plan"]["id"]
        _generate_plan(client, auth_headers["headers"], race_name="Newer Plan")

        resp = client.post("/api/coach/select-plan", headers=auth_headers["headers"], json={"plan_id": first_plan_id})
        assert resp.status_code == 200
        assert resp.json()["plan"]["id"] == first_plan_id

    def test_selecting_another_users_plan_is_rejected(self, client, auth_headers, mock_plan_generation):
        gen_resp = _generate_plan(client, auth_headers["headers"])
        plan_id = gen_resp.json()["plan"]["id"]

        other_login = client.post("/api/auth/mock-login", json={"email": "select-plan-other@uphill.ai"})
        other_headers = {"Authorization": f"Bearer {other_login.json()['session_token']}"}

        resp = client.post("/api/coach/select-plan", headers=other_headers, json={"plan_id": plan_id})
        assert resp.status_code == 404
