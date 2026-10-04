"""Scheduler request cancellation uses no network or database."""

import asyncio
from types import SimpleNamespace

import pytest

from services import plan_generator


class RequestClient:
    def __init__(self, operation):
        self.aio = self
        self.models = SimpleNamespace(generate_content=operation)
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.closed = True


@pytest.mark.asyncio
async def test_deadline_cancels_the_provider_request_and_closes_the_client(monkeypatch):
    cancelled = False

    async def stalled(**kwargs):
        nonlocal cancelled
        try:
            await asyncio.Event().wait()
        finally:
            cancelled = True

    client = RequestClient(stalled)
    monkeypatch.setattr(plan_generator, "PLAN_REQUEST_TIMEOUT_SECONDS", 0.02, raising=False)
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(
            plan_generator._generate_plan_response(client, model="synthetic", contents="invented", config=None),
            timeout=1,
        )
    assert cancelled
    assert client.closed


@pytest.mark.asyncio
async def test_successful_request_preserves_the_response_and_closes_the_client():
    async def completed(**kwargs):
        assert kwargs == {"model": "synthetic", "contents": "invented", "config": None}
        return {"result": 47}

    client = RequestClient(completed)
    result = await plan_generator._generate_plan_response(client, model="synthetic", contents="invented", config=None)
    assert result == {"result": 47}
    assert client.closed
