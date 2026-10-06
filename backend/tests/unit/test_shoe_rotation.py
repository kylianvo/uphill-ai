"""Shoe Rotation: the /api/shoe-rotation routes and the db helpers behind them."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

import db
import main

client = TestClient(main.app)
AUTH = {"Authorization": "Bearer tok"}
PEG = {"slot": "daily", "brand": "Nike", "model": "Pegasus 41", "distance_km": 12.5}


@pytest.fixture
def sqlite_db(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE user_shoes (user_id INTEGER, slot TEXT, brand TEXT, model TEXT, "
                "distance_km REAL DEFAULT 0, max_distance_km REAL DEFAULT 700, is_retired BOOLEAN DEFAULT 0, "
                "notes TEXT, PRIMARY KEY (user_id, slot))"
            )
        )
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(main, "verify_session", lambda tok: {"id": 7, "email": "a@b.c", "role": "user"})
    monkeypatch.setattr(main, "get_shoe_rotation", db.get_shoe_rotation)
    monkeypatch.setattr(main, "replace_shoe_rotation", db.replace_shoe_rotation)


def test_requires_auth():
    assert client.get("/api/shoe-rotation").status_code == 401


def test_empty_rotation_for_new_user(sqlite_db):
    assert client.get("/api/shoe-rotation", headers=AUTH).json() == {"shoes": []}


def test_put_replaces_whole_rotation_and_round_trips(sqlite_db):
    trail = {"slot": "trail", "brand": "Hoka", "model": "Speedgoat 6", "is_retired": True}
    resp = client.put("/api/shoe-rotation", headers=AUTH, json={"shoes": [PEG, trail]})
    assert resp.status_code == 200
    shoes = {s["slot"]: s for s in resp.json()["shoes"]}
    assert shoes["daily"]["distance_km"] == 12.5 and shoes["daily"]["max_distance_km"] == 700
    assert shoes["trail"]["is_retired"] is True

    client.put("/api/shoe-rotation", headers=AUTH, json={"shoes": [PEG]})
    assert [s["slot"] for s in client.get("/api/shoe-rotation", headers=AUTH).json()["shoes"]] == ["daily"]


def test_rotation_is_per_user(sqlite_db):
    db.replace_shoe_rotation(99, [{**PEG, "max_distance_km": 700, "is_retired": False, "notes": None}])
    assert client.get("/api/shoe-rotation", headers=AUTH).json() == {"shoes": []}


@pytest.mark.parametrize(
    "shoes",
    [
        [PEG, {**PEG, "model": "Pegasus 40"}],  # two shoes in one slot
        [{**PEG, "slot": "recovery"}],  # unknown slot
        [{**PEG, "distance_km": -1}],
        [{**PEG, "brand": ""}],
    ],
)
def test_rejects_invalid_rotation(sqlite_db, shoes):
    assert client.put("/api/shoe-rotation", headers=AUTH, json={"shoes": shoes}).status_code in (400, 422)
