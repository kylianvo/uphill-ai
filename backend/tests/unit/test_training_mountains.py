import pytest

from services.training_mountains import MOUNTAINS, default_min_minutes, long_run_climb_rate


@pytest.mark.parametrize(
    "key, rate", [("nui_dinh", 60), ("chau_thoi", 28), ("ba_den", 60), ("ham_lon", 45), (None, None), ("unknown", None)]
)
def test_long_run_climb_rate(key, rate):
    assert long_run_climb_rate(key) == rate


@pytest.mark.parametrize("key, minutes", [("chau_thoi", 180), ("ham_lon", 180), ("sapa", None), (None, None)])
def test_default_min_minutes(key, minutes):
    assert default_min_minutes(key) == minutes


def test_curated_mountain_values():
    assert {key: m.climb_rate for key, m in MOUNTAINS.items()} == {
        "nui_dinh": 60,
        "chau_thoi": 28,
        "chua_chan": 85,
        "ba_den": 176,
        "ham_lon": 45,
        "dalat": 47,
        "sapa": 56,
    }
    assert MOUNTAINS["ba_den"].repeats_only


def test_chau_thoi_is_hcmc_long_run_mountain():
    mountain = MOUNTAINS["chau_thoi"]
    assert mountain.area == "hcmc"
    assert mountain.name_en == mountain.name_vi == "Núi Châu Thới"
    assert not mountain.repeats_only


def test_training_mountains_route_returns_shared_catalog():
    from fastapi.testclient import TestClient

    import main

    response = TestClient(main.app).get("/api/training-mountains")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 7
    assert {row["key"] for row in rows} == set(MOUNTAINS)
    assert next(row for row in rows if row["key"] == "nui_dinh") == {
        "key": "nui_dinh",
        "area": "hcmc",
        "name_en": "Núi Dinh",
        "name_vi": "Núi Dinh",
        "climb_rate": 60,
        "repeats_only": False,
        "default_min_minutes": 180,
    }


def test_schedule_can_explicitly_clear_mountain_and_minimum(monkeypatch):
    from unittest.mock import MagicMock

    import db

    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = None
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn
    monkeypatch.setattr(db, "engine", engine)
    db.update_plan_schedule(1, clear_training_mountain=True, clear_mountain_min_minutes=True)
    statement, params = conn.execute.call_args.args
    assert params["clear_training_mountain"] is True
    assert params["clear_mountain_min_minutes"] is True
    assert "CASE WHEN :clear_training_mountain THEN NULL" in str(statement)
    assert "CASE WHEN :clear_mountain_min_minutes THEN NULL" in str(statement)


@pytest.mark.parametrize("clear", [False, True])
def test_rebuild_distinguishes_omitted_mountain_from_explicit_clear(monkeypatch, clear):
    from services import week_rebuild

    monkeypatch.setattr(week_rebuild.db, "get_user_by_id", lambda _: {"id": 7})
    monkeypatch.setattr(week_rebuild.db, "get_recent_readiness_summary", lambda *a, **kw: None)
    monkeypatch.setattr(week_rebuild.db, "get_user_activity_ceiling", lambda _: None)
    monkeypatch.setattr("services.block_history.get_resting_hr_elevation", lambda _: None)
    monkeypatch.setattr(week_rebuild, "resolve_course_match", lambda *a: (None, None, None))
    plan = {
        "id": 1,
        "start_date": "2026-10-12",
        "total_weeks": 12,
        "training_mountain": "nui_dinh",
        "mountain_min_minutes": 180,
    }
    rng = week_rebuild.RebuildRange(1, "Monday", (), (), frozenset())
    request = week_rebuild.RebuildRequest(
        week_number=1, clear_training_mountain=clear, clear_mountain_min_minutes=clear
    )
    inputs = week_rebuild.build_rebuild_inputs(7, plan, [], rng, request)
    assert inputs.race_info["training_mountain"] == (None if clear else "nui_dinh")
    assert inputs.race_info["mountain_min_minutes"] == (None if clear else 180)
