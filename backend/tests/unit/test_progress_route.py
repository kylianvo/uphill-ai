"""GET /api/progress with the database stubbed out -- no DB, no network."""

from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import integrations, progress
from services import progress_cards

app = FastAPI()
app.include_router(progress.router, prefix="/api")
client = TestClient(app)
TODAY = date.today()


@pytest.fixture()
def stub_db(monkeypatch):
    state = {"plan": None, "workouts": [], "activities": [], "metrics": [], "connection": None, "checkpoints": []}
    d = progress_cards.db
    monkeypatch.setattr(d, "get_active_plan", lambda uid: state["plan"])
    monkeypatch.setattr(d, "get_user_by_id", lambda uid: {"id": uid, "aet_hr": None})
    monkeypatch.setattr(d, "get_plan_workouts_with_match", lambda pid: state["workouts"])
    monkeypatch.setattr(d, "get_activities_for_pace", lambda uid, since, until: state["activities"])
    monkeypatch.setattr(d, "get_daily_metrics", lambda uid, since: state["metrics"])
    monkeypatch.setattr(d, "get_connection", lambda uid, p: state["connection"])
    monkeypatch.setattr(d, "get_fitness_checkpoints", lambda pid: state["checkpoints"])
    app.dependency_overrides[integrations.get_current_user] = lambda: {"id": 7}
    yield state
    app.dependency_overrides.pop(integrations.get_current_user, None)


def _metric(days_ago, provider, **fields):
    return {"metric_date": TODAY - timedelta(days=days_ago), "source_provider": provider, **fields}


def test_progress_for_brand_new_user(stub_db):
    for section in ("training", "health"):
        res = client.get(f"/api/progress?section={section}")
        assert res.status_code == 200
        body = res.json()
        assert body["cards"] == [] and body["connected"] is False and body["has_plan"] is False


def test_health_cards_from_single_provider(stub_db):
    # Apple Health synced today; COROS's rows are older, so Apple is the one source.
    stub_db["metrics"] = [_metric(i, "apple_health", sleep_minutes=420, resting_hr=52) for i in range(10)]
    stub_db["metrics"] += [_metric(i + 1, "coros", hrv_ms=60.0) for i in range(20)]
    body = client.get("/api/progress?section=health").json()
    keys = [c["key"] for c in body["cards"]]
    assert keys == ["coach_read", "sleep", "resting_hr"]
    assert {c["source"] for c in body["cards"][1:]} == {"apple_health"}
    assert body["connected"] is True
    assert body["pending"] == [{"key": "hrv", "needs": 14, "have": 0}]


def test_days_90_widens_series(stub_db):
    stub_db["metrics"] = [_metric(i, "coros", sleep_minutes=420) for i in range(60)]
    short = client.get("/api/progress?section=health").json()
    long = client.get("/api/progress?section=health&days=90").json()
    assert len(short["cards"][1]["series"]) == 28 and len(long["cards"][1]["series"]) == 60


def test_days_other_value_is_422(stub_db):
    assert client.get("/api/progress?section=health&days=30").status_code == 422


def test_training_order_and_goal_marker(stub_db):
    monday = TODAY - timedelta(days=TODAY.weekday() + 21)
    stub_db["plan"] = {"id": 3, "user_id": 7, "start_date": monday.isoformat(), "total_weeks": 12}
    stub_db["workouts"] = [
        {
            "week_number": w,
            "type": "Easy Run",
            "is_completed": 1,
            "matched_activity_id": None,
            "distance_km": 8.0,
            "elevation_gain_m": 50.0,
        }
        for w in (1, 2, 3)
    ]
    stub_db["activities"] = [
        {
            "start_time": datetime.combine(TODAY - timedelta(days=3 * i), datetime.min.time(), tzinfo=UTC),
            "duration_seconds": 7200,
            "hr_drift_pct": 2.0,
            "workout_type": None,
            "distance_km": 20.0,
            "elevation_gain_m": 400.0,
        }
        for i in range(3)
    ]
    body = client.get("/api/progress?section=training").json()
    assert body["has_plan"] is True and body["plan_id"] == 3
    assert [c["key"] for c in body["cards"]] == ["goal", "consistency", "volume", "durability"]
    assert {p["key"] for p in body["pending"]} == {"aerobic_speed", "load"}


def test_bad_section_is_422(stub_db):
    assert client.get("/api/progress?section=sleep").status_code == 422


def test_requires_auth():
    assert TestClient(app).get("/api/progress?section=health").status_code == 401
