"""Per-week plan review and one-tap publish for coaches. See
docs/superpowers/specs/2026-10-23-athletes-tab-coach-workbench-design.md (Phase 3)."""

from sqlalchemy import text

from db import create_or_get_user, create_plan, engine, get_plan_workouts, save_workouts, set_user_is_coach


def _user(email):
    return create_or_get_user(email, email.split("@")[0].capitalize(), "mock", f"mock-{email}")["id"]


def _coach(client, email):
    data = client.post("/api/auth/mock-login", json={"email": email}).json()
    set_user_is_coach(data["user"]["id"], True)
    return {"Authorization": f"Bearer {data['session_token']}"}, data["user"]["id"]


def _link(coach_id, athlete_id):
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO coach_athletes (coach_id, athlete_id, status) VALUES (:c, :a, 'active')"),
            {"c": coach_id, "a": athlete_id},
        )
        conn.commit()


def _week(week, types=("Easy", "Rest", "Long Run")):
    days = ["Monday", "Wednesday", "Saturday"]
    return [
        {
            "week_number": week,
            "day_of_week": d,
            "phase": "base",
            "title": t,
            "type": t,
            "duration_minutes": 0 if t == "Rest" else 60,
            "target_zone": "Z2",
        }
        for d, t in zip(days, types, strict=True)
    ]


def _plan(athlete_id, status="active", created_by=None, approve=True, weeks=(1,)):
    pid = create_plan(
        user_id=athlete_id,
        race_name="Dalat 50K",
        race_date="2027-02-06",
        goal_type="finish",
        target_time_hours=None,
        total_weeks=12,
        plan_status=status,
        created_by_user_id=created_by or athlete_id,
    )
    save_workouts(pid, [w for wk in weeks for w in _week(wk)], auto_approve=approve)
    return pid


def _setup(client, tag):
    headers, coach = _coach(client, f"rp-coach-{tag}@uphill.ai")
    athlete = _user(f"rp-athlete-{tag}@uphill.ai")
    _link(coach, athlete)
    return headers, coach, athlete


def test_review_marks_current_week_and_is_idempotent(client):
    headers, coach, athlete = _setup(client, "a")
    pid = _plan(athlete)
    url = f"/api/coaching/athletes/{athlete}/plans/{pid}/review"
    got = client.get(url, headers=headers).json()
    assert got["generated_block"] == 1 and got["reviewed_block"] is None
    assert isinstance(got["issues"], list)
    first = client.post(url, json={"note": "Looks good, keep Saturday easy."}, headers=headers)
    second = client.post(url, json={"note": None}, headers=headers)
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["reviewed_block"] == second.json()["reviewed_block"] == 1
    assert second.json()["reviewed_by"] == coach
    with engine.connect() as conn:
        notes = conn.execute(
            text("SELECT target_type, target_id FROM coach_notes WHERE athlete_id = :a"), {"a": athlete}
        ).fetchall()
    assert [(n.target_type, n.target_id) for n in notes] == [("plan", pid)]


def test_new_week_reopens_review(client):
    headers, _, athlete = _setup(client, "b")
    pid = _plan(athlete)
    url = f"/api/coaching/athletes/{athlete}/plans/{pid}/review"
    client.post(url, json={}, headers=headers)
    save_workouts(pid, _week(2))
    got = client.get(url, headers=headers).json()
    assert got["generated_block"] == 2 and got["reviewed_block"] == 1


def test_publish_draft_activates_and_approves_all(client):
    headers, coach, athlete = _setup(client, "c")
    pid = _plan(athlete, status="draft", created_by=coach, approve=False)
    resp = client.post(f"/api/coaching/athletes/{athlete}/plans/{pid}/publish", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"plan_id": pid, "plan_status": "active", "approved_count": 3}
    assert all(w["approved_at"] is not None for w in get_plan_workouts(pid))


def test_publish_active_approves_pending_rest_edit(client):
    headers, coach, athlete = _setup(client, "d")
    pid = _plan(athlete, created_by=coach)
    rest = next(w for w in get_plan_workouts(pid) if w["type"] == "Rest")
    with engine.connect() as conn:
        conn.execute(text("UPDATE workouts SET approved_at = NULL WHERE id = :id"), {"id": rest["id"]})
        conn.commit()
    resp = client.post(f"/api/coaching/athletes/{athlete}/plans/{pid}/publish", headers=headers)
    assert resp.json()["approved_count"] == 1 and resp.json()["plan_status"] == "active"


def test_review_other_athletes_plan_404(client):
    headers, _, athlete = _setup(client, "e")
    other_plan = _plan(_user("rp-stranger@uphill.ai"))
    assert client.get(f"/api/coaching/athletes/{athlete}/plans/{other_plan}/review", headers=headers).status_code == 404
    assert (
        client.post(f"/api/coaching/athletes/{athlete}/plans/{other_plan}/publish", headers=headers).status_code == 404
    )


def test_coach_next_block_counts_as_reviewed():
    from db import mark_plan_reviewed

    coach, athlete = _user("rp-coach-f@uphill.ai"), _user("rp-athlete-f@uphill.ai")
    pid = _plan(athlete, weeks=(1, 2))
    assert mark_plan_reviewed(pid, athlete, coach)["coach_reviewed_block"] == 2
