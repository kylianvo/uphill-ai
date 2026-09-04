"""Unit tests for the sync orchestration -- DB and adapter are stubbed."""

from datetime import UTC, date, datetime

import pytest

from services import coros_sync
from services.providers.base import CanonicalActivity, CanonicalDailyMetric


class StubAdapter:
    def __init__(self):
        self.activities = [
            CanonicalActivity(
                external_id="a1",
                provider="coros",
                activity_type="trail_run",
                start_time=datetime(2026, 8, 29, tzinfo=UTC),
                duration_seconds=5434.0,
                distance_km=15.03,
            )
        ]
        self.metrics = [CanonicalDailyMetric(date(2026, 9, 4), "coros", resting_hr=57)]

    async def fetch_activities(self, since, until):
        return self.activities

    async def fetch_daily_metrics(self, days=7):
        return self.metrics


@pytest.mark.asyncio
async def test_sync_persists_activities_and_metrics_and_reports_counts(monkeypatch):
    saved_activities, saved_metrics = [], []
    monkeypatch.setattr(coros_sync.db, "upsert_activity", lambda uid, a: saved_activities.append(a) or 1)
    monkeypatch.setattr(coros_sync.db, "upsert_daily_metric", lambda uid, m: saved_metrics.append(m) or 1)
    monkeypatch.setattr(coros_sync.db, "mark_connection_synced", lambda uid, p: None)

    result = await coros_sync.persist(user_id=7, adapter=StubAdapter(), days=30)

    assert result == {"activities": 1, "daily_metrics": 1}
    assert len(saved_activities) == 1
    assert len(saved_metrics) == 1


@pytest.mark.asyncio
async def test_sync_continues_when_one_activity_fails_to_persist(monkeypatch):
    # One malformed activity must not abandon the rest of the sync.
    adapter = StubAdapter()
    adapter.activities = adapter.activities * 3
    calls = {"n": 0}

    def flaky(uid, activity):
        calls["n"] += 1
        if calls["n"] == 2:
            raise ValueError("bad row")
        return calls["n"]

    monkeypatch.setattr(coros_sync.db, "upsert_activity", flaky)
    monkeypatch.setattr(coros_sync.db, "upsert_daily_metric", lambda uid, m: 1)
    monkeypatch.setattr(coros_sync.db, "mark_connection_synced", lambda uid, p: None)

    result = await coros_sync.persist(user_id=7, adapter=adapter, days=30)
    assert result["activities"] == 2
