"""Plan type (review | coached) on a coach-athlete link, and the per-week
review columns on plans. See
docs/superpowers/specs/2026-10-23-athletes-tab-coach-workbench-design.md."""

from sqlalchemy import text

from db import create_or_get_user, engine, get_roster_for_coach, set_user_is_coach


def _user(email: str) -> int:
    return create_or_get_user(email, email.split("@")[0].capitalize(), "mock", f"mock-{email}")["id"]


def _link(coach_id: int, athlete_id: int) -> int:
    with engine.connect() as conn:
        link_id = conn.execute(
            text("INSERT INTO coach_athletes (coach_id, athlete_id, status) VALUES (:c, :a, 'active') RETURNING id"),
            {"c": coach_id, "a": athlete_id},
        ).scalar()
        conn.commit()
    return link_id


def _coach_headers(client, email: str) -> tuple[dict, int]:
    data = client.post("/api/auth/mock-login", json={"email": email}).json()
    set_user_is_coach(data["user"]["id"], True)
    return {"Authorization": f"Bearer {data['session_token']}"}, data["user"]["id"]


def test_new_link_defaults_to_review():
    coach, athlete = _user("pt-coach1@uphill.ai"), _user("pt-athlete1@uphill.ai")
    _link(coach, athlete)
    assert get_roster_for_coach(coach)[0]["plan_type"] == "review"


def test_plans_have_review_columns():
    with engine.connect() as conn:
        cols = {
            r[0]
            for r in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'plans'"))
        }
    assert {"coach_reviewed_block", "coach_reviewed_at", "coach_reviewed_by"} <= cols


def test_coach_sets_plan_type(client):
    headers, coach = _coach_headers(client, "pt-coach2@uphill.ai")
    link_id = _link(coach, _user("pt-athlete2@uphill.ai"))
    resp = client.patch(f"/api/coaching/roster/{link_id}", json={"plan_type": "coached"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["plan_type"] == "coached"
    assert client.get("/api/coaching/roster", headers=headers).json()[0]["plan_type"] == "coached"


def test_patch_rejects_unknown_type(client):
    headers, coach = _coach_headers(client, "pt-coach3@uphill.ai")
    link_id = _link(coach, _user("pt-athlete3@uphill.ai"))
    resp = client.patch(f"/api/coaching/roster/{link_id}", json={"plan_type": "vip"}, headers=headers)
    assert resp.status_code == 422


def test_patch_other_coaches_link_404(client):
    headers, _ = _coach_headers(client, "pt-coach4@uphill.ai")
    other_link = _link(_user("pt-coach5@uphill.ai"), _user("pt-athlete5@uphill.ai"))
    resp = client.patch(f"/api/coaching/roster/{other_link}", json={"plan_type": "coached"}, headers=headers)
    assert resp.status_code == 404
