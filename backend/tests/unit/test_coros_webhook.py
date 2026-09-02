"""Unit tests for the COROS integration stub -- no DB and no live COROS needed.

The stub's contract comes from the COROS API Reference V2.0.6: the receiving
endpoint must accept duplicate deliveries, and a partner interface is judged
healthy on an HTTP 200. These tests pin the behaviour the application form
promises, so a later refactor cannot silently start returning non-2xx.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers.integrations import router

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)

WEBHOOK = "/api/integrations/coros/webhook"


def test_get_probe_returns_200():
    resp = client.get(WEBHOOK)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_post_accepts_workout_summary():
    resp = client.post(WEBHOOK, json={"openId": "abc", "sportDataList": []})
    assert resp.status_code == 200
    assert resp.json() == {"message": "ok"}


def test_post_is_idempotent_for_duplicate_delivery():
    """COROS documents the endpoint as one that 'allows duplicate data'."""
    payload = {"openId": "abc", "sportDataList": [{"labelId": "1"}]}
    first = client.post(WEBHOOK, json=payload)
    second = client.post(WEBHOOK, json=payload)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


def test_post_returns_200_on_malformed_body():
    """A non-2xx would make COROS retry a payload the stub cannot process."""
    resp = client.post(WEBHOOK, content=b"not json", headers={"content-type": "application/json"})
    assert resp.status_code == 200


def test_post_accepts_form_encoded_body():
    """COROS states all interface calls use application/x-www-form-urlencoded."""
    resp = client.post(WEBHOOK, data={"openId": "abc"})
    assert resp.status_code == 200
