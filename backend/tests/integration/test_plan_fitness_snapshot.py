"""Plan creation builds the fitness snapshot and stores it on plans.fitness_snapshot.

Gemini is mocked to return an empty list, so the generator falls through to the
rule-based schedule -- the tier and snapshot wiring run for real. Scratch DB only.
"""

import dataclasses
import time
from unittest.mock import patch

import pytest
from sqlalchemy import text

from db import engine


def _generate(client, headers, **overrides):
    payload = {
        "goal_type": "finish",
        "race_name": "Synthetic 80K",
        "race_date": "2027-05-01",
        "plan_start_date": "2027-03-15",
        "days_per_week": 6,
        "current_weekly_km": 120,
        "course_distance_km": 80,
        "course_elevation_gain_m": 4000,
    }
    payload.update(overrides)
    return client.post("/api/coach/generate-plan", headers=headers, json=payload)


def _wait_for_job(client, job_id, headers):
    status = None
    for _ in range(200):
        status = client.get(f"/api/coach/plan-status/{job_id}", headers=headers).json()["status"]
        if status != "generating":
            break
        time.sleep(0.05)
    assert status == "done", status


@pytest.fixture
def no_kb():
    with patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]):
        yield


def test_generate_plan_stores_snapshot_and_uses_measured_volume(client, auth_headers, mock_gemini, no_kb, monkeypatch):
    from services import coros_sync, fitness_snapshot

    async def no_refresh(uid, **kw):
        return None

    monkeypatch.setattr(coros_sync, "ensure_fresh_assessment", no_refresh)
    real_build = fitness_snapshot.build
    monkeypatch.setattr(
        fitness_snapshot,
        "build",
        lambda uid, **kw: dataclasses.replace(real_build(uid, **kw), weekly_km=134.0, weekly_km_source="coros"),
    )
    resp = _generate(client, auth_headers["headers"], weekly_km_from_watch=True)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    _wait_for_job(client, body["job_id"], auth_headers["headers"])
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT fitness_snapshot, athlete_tier FROM plans WHERE id=:p"), {"p": body["plan"]["id"]}
        ).one()
    snap = row.fitness_snapshot
    assert snap["weekly_km"] == 134.0
    assert snap["tier"] == "sub_elite" == row.athlete_tier
    assert snap["tier_levels"]["load"] is not None


def test_typed_volume_is_an_override_unless_it_came_from_the_watch(
    client, auth_headers, mock_gemini, no_kb, monkeypatch
):
    from services import coros_sync, fitness_snapshot

    async def no_refresh(uid, **kw):
        return None

    calls = []
    real_build = fitness_snapshot.build

    def spy(uid, **kw):
        calls.append(kw)
        return real_build(uid, **kw)

    monkeypatch.setattr(coros_sync, "ensure_fresh_assessment", no_refresh)
    monkeypatch.setattr(fitness_snapshot, "build", spy)
    body = _generate(client, auth_headers["headers"]).json()
    _wait_for_job(client, body["job_id"], auth_headers["headers"])
    assert calls[-1] == {"typed_weekly_km": 120.0, "typed_is_override": True}


def test_snapshot_failure_never_blocks_the_plan(client, auth_headers, mock_gemini, no_kb, monkeypatch):
    from services import coros_sync

    async def boom(uid, **kw):
        raise RuntimeError("COROS down")

    monkeypatch.setattr(coros_sync, "ensure_fresh_assessment", boom)
    body = _generate(client, auth_headers["headers"]).json()
    _wait_for_job(client, body["job_id"], auth_headers["headers"])
    with engine.connect() as conn:
        snap = conn.execute(
            text("SELECT fitness_snapshot FROM plans WHERE id=:p"), {"p": body["plan"]["id"]}
        ).scalar_one()
    assert snap is None
