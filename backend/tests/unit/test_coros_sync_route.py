"""Unit tests for POST /coros/sync's exception-to-HTTP-status mapping -- no
DB, no live COROS. coros_sync.sync_user is monkeypatched to raise each
failure type the orchestration layer can produce.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import integrations
from services import coros_sync
from services.mcp_client import McpError
from services.providers.coros import CorosDailyMetricsUnavailableError
from services.providers.coros_parsers import CorosParseError

app = FastAPI()
app.include_router(integrations.router, prefix="/api")
client = TestClient(app)

SYNC = "/api/integrations/coros/sync"


@pytest.fixture(autouse=True)
def _authed_user():
    app.dependency_overrides[integrations.get_current_user] = lambda: {"id": 7}
    yield
    app.dependency_overrides.pop(integrations.get_current_user, None)


def _raiser(exc: Exception):
    async def raise_it(user_id, days=30):
        raise exc

    return raise_it


def test_reconnect_required_maps_to_400(monkeypatch):
    monkeypatch.setattr(
        coros_sync, "sync_user", _raiser(coros_sync.CorosReconnectRequired("the athlete must reconnect"))
    )
    resp = client.post(SYNC)
    assert resp.status_code == 400


def test_no_active_connection_value_error_maps_to_400(monkeypatch):
    monkeypatch.setattr(coros_sync, "sync_user", _raiser(ValueError("No active COROS connection for this athlete.")))
    resp = client.post(SYNC)
    assert resp.status_code == 400
    assert "No active COROS connection" in resp.text


def test_mcp_error_maps_to_502_not_500(monkeypatch):
    # A transport failure (rate limit, timeout) escaping McpClient must not
    # 500 -- it is an upstream/provider failure, not something the athlete or
    # this app did wrong.
    monkeypatch.setattr(
        coros_sync, "sync_user", _raiser(McpError("MCP request 'getActivityDetail' failed with HTTP 429"))
    )
    resp = client.post(SYNC)
    assert resp.status_code == 502


def test_persist_error_maps_to_502_not_500(monkeypatch):
    monkeypatch.setattr(
        coros_sync, "sync_user", _raiser(coros_sync.CorosSyncPersistError("all 3 activities failed to persist"))
    )
    resp = client.post(SYNC)
    assert resp.status_code == 502


def test_daily_metrics_unavailable_maps_to_502_not_500(monkeypatch):
    monkeypatch.setattr(
        coros_sync, "sync_user", _raiser(CorosDailyMetricsUnavailableError("all COROS daily-metric sources failed"))
    )
    resp = client.post(SYNC)
    assert resp.status_code == 502


def test_parse_error_maps_to_502_and_does_not_leak_the_internal_parser_string(monkeypatch):
    # CorosParseError subclasses ValueError -- it must be caught before the
    # generic ValueError arm, or a COROS response-shape change is reported to
    # the athlete as a 400 client error carrying an internal parser string as
    # `detail`, e.g. "querySportRecords output missing its 'Sport Records'
    # header". That is a vendor-side fault mis-reported as the athlete's
    # fault, and it leaks internals.
    internal_detail = "querySportRecords output missing its 'Sport Records' header"
    monkeypatch.setattr(coros_sync, "sync_user", _raiser(CorosParseError(internal_detail)))

    resp = client.post(SYNC)

    assert resp.status_code == 502
    assert resp.status_code != 400
    assert "Sport Records" not in resp.text
    assert "querySportRecords" not in resp.text


def test_matching_routes_return_404_when_plan_does_not_belong_to_user(monkeypatch):
    monkeypatch.setattr(integrations.db, "get_plan_by_id", lambda plan_id: {"id": plan_id, "user_id": 999})
    resp_get = client.get("/api/integrations/matching?plan_id=42")
    assert resp_get.status_code == 404

    resp_post = client.post("/api/integrations/matching/run?plan_id=42")
    assert resp_post.status_code == 404


def test_matching_routes_scope_by_plan_window(monkeypatch):
    plan_data = {
        "id": 42,
        "user_id": 7,
        "start_date": "2026-08-01",
        "race_date": "2026-09-20",
    }
    monkeypatch.setattr(integrations.db, "get_plan_by_id", lambda plan_id: plan_data)

    # Track calls to get_matches_for_review
    review_calls = []
    monkeypatch.setattr(
        integrations.db,
        "get_matches_for_review",
        lambda u, since, until, plan_id=None: review_calls.append({"since": since, "until": until, "plan_id": plan_id})
        or [],
    )

    resp_get = client.get("/api/integrations/matching?plan_id=42")
    assert resp_get.status_code == 200
    assert len(review_calls) == 1
    assert review_calls[0]["plan_id"] == 42
    # Monday of week containing 2026-08-01 (Saturday) is 2026-07-27
    assert str(review_calls[0]["since"]) == "2026-07-27"
    # race_date 2026-09-20 + 2 days = 2026-09-22
    assert str(review_calls[0]["until"]) == "2026-09-22"
