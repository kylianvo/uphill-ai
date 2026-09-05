"""Unit tests for McpClient -- transport is mocked, no network."""

import json

import httpx
import pytest

from services.mcp_client import McpClient, McpError

ENDPOINT = "https://mcp.example.com/mcp"


def _transport(handler):
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_call_tool_returns_concatenated_text_content():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if body["method"] == "initialize":
            return httpx.Response(
                200, json={"jsonrpc": "2.0", "id": body["id"], "result": {}}, headers={"Mcp-Session-Id": "sess-1"}
            )
        if body["method"] == "notifications/initialized":
            return httpx.Response(202)
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": body["id"],
                "result": {"content": [{"type": "text", "text": "Hello "}, {"type": "text", "text": "world"}]},
            },
        )

    client = McpClient(ENDPOINT, "tok", transport=_transport(handler))
    await client.initialize()
    assert await client.call_tool("queryUserInfo", {}) == "Hello world"


@pytest.mark.asyncio
async def test_sends_bearer_token_on_every_request():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("authorization"))
        body = json.loads(request.content)
        if body["method"] == "notifications/initialized":
            return httpx.Response(202)
        return httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": body.get("id"), "result": {"content": []}},
            headers={"Mcp-Session-Id": "s"},
        )

    client = McpClient(ENDPOINT, "tok-abc", transport=_transport(handler))
    await client.initialize()
    await client.call_tool("queryDevices", {})
    assert seen and all(h == "Bearer tok-abc" for h in seen)


@pytest.mark.asyncio
async def test_parses_a_server_sent_events_response():
    payload = {"jsonrpc": "2.0", "id": 2, "result": {"content": [{"type": "text", "text": "sse-ok"}]}}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if body["method"] == "initialize":
            return httpx.Response(
                200, json={"jsonrpc": "2.0", "id": body["id"], "result": {}}, headers={"Mcp-Session-Id": "s"}
            )
        if body["method"] == "notifications/initialized":
            return httpx.Response(202)
        return httpx.Response(
            200, text=f"event: message\ndata: {json.dumps(payload)}\n\n", headers={"content-type": "text/event-stream"}
        )

    client = McpClient(ENDPOINT, "tok", transport=_transport(handler))
    await client.initialize()
    assert await client.call_tool("querySportRecords", {}) == "sse-ok"


@pytest.mark.asyncio
async def test_raises_mcp_error_when_the_server_returns_an_error():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if body["method"] == "notifications/initialized":
            return httpx.Response(202)
        if body["method"] == "initialize":
            return httpx.Response(
                200, json={"jsonrpc": "2.0", "id": body["id"], "result": {}}, headers={"Mcp-Session-Id": "s"}
            )
        return httpx.Response(
            200, json={"jsonrpc": "2.0", "id": body["id"], "error": {"code": -32000, "message": "rate limited"}}
        )

    client = McpClient(ENDPOINT, "tok", transport=_transport(handler))
    await client.initialize()
    with pytest.raises(McpError, match="rate limited"):
        await client.call_tool("downloadActivityFitFiles", {})


@pytest.mark.asyncio
async def test_context_manager_closes_the_transport_when_initialize_fails():
    # A non-2xx status must surface as McpError, not the raw httpx exception --
    # McpError is the only exception type the per-item isolation guards in
    # services/providers/coros.py catch, so an httpx.HTTPStatusError escaping
    # here would bypass them and abort whatever batch is in flight.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    client = McpClient(ENDPOINT, "tok", transport=_transport(handler))
    with pytest.raises(McpError, match="401"):
        async with client:
            pass
    assert client._client.is_closed is True


@pytest.mark.asyncio
async def test_a_timeout_also_surfaces_as_mcp_error():
    # A slow/rate-limited COROS response must not escape as httpx.TimeoutException
    # -- that would bypass the (CorosParseError, McpError) isolation guards in
    # services/providers/coros.py and discard an entire in-flight batch.
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    client = McpClient(ENDPOINT, "tok", transport=_transport(handler))
    with pytest.raises(McpError):
        await client.initialize()


@pytest.mark.asyncio
async def test_a_transport_failure_on_the_initialized_notification_also_surfaces_as_mcp_error():
    # initialize() runs on every sync (unlike the one-shot detail/daily-metric
    # calls this transport failure resembles), so a raw httpx exception
    # escaping from its trailing notifications/initialized POST would surface
    # as a bare 500 on POST /coros/sync and get miscategorised as "other"
    # rather than "transient_failed" in scripts/sync_devices.py's summary.
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if body["method"] == "initialize":
            return httpx.Response(
                200, json={"jsonrpc": "2.0", "id": body["id"], "result": {}}, headers={"Mcp-Session-Id": "s"}
            )
        raise httpx.TimeoutException("timed out", request=request)

    client = McpClient(ENDPOINT, "tok", transport=_transport(handler))
    with pytest.raises(McpError):
        await client.initialize()


@pytest.mark.asyncio
async def test_call_tool_skips_notification_frames_ahead_of_the_matching_response():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if body["method"] == "initialize":
            return httpx.Response(
                200, json={"jsonrpc": "2.0", "id": body["id"], "result": {}}, headers={"Mcp-Session-Id": "s"}
            )
        if body["method"] == "notifications/initialized":
            return httpx.Response(202)
        notification = {"jsonrpc": "2.0", "method": "notifications/progress", "params": {}}
        response_frame = {
            "jsonrpc": "2.0",
            "id": body["id"],
            "result": {"content": [{"type": "text", "text": "real-answer"}]},
        }
        sse_body = (
            f"event: message\ndata: {json.dumps(notification)}\n\n"
            f"event: message\ndata: {json.dumps(response_frame)}\n\n"
        )
        return httpx.Response(200, text=sse_body, headers={"content-type": "text/event-stream"})

    client = McpClient(ENDPOINT, "tok", transport=_transport(handler))
    await client.initialize()
    assert await client.call_tool("queryUserInfo", {}) == "real-answer"


@pytest.mark.asyncio
async def test_raises_mcp_error_when_no_sse_frame_matches_the_request_id():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if body["method"] == "initialize":
            return httpx.Response(
                200, json={"jsonrpc": "2.0", "id": body["id"], "result": {}}, headers={"Mcp-Session-Id": "s"}
            )
        if body["method"] == "notifications/initialized":
            return httpx.Response(202)
        mismatched = {"jsonrpc": "2.0", "id": body["id"] + 999, "result": {"content": []}}
        return httpx.Response(
            200,
            text=f"event: message\ndata: {json.dumps(mismatched)}\n\n",
            headers={"content-type": "text/event-stream"},
        )

    client = McpClient(ENDPOINT, "tok", transport=_transport(handler))
    await client.initialize()
    with pytest.raises(McpError, match="no frame matching request id"):
        await client.call_tool("queryUserInfo", {})
