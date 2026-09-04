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
