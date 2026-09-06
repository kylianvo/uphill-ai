"""Minimal Model Context Protocol client over Streamable HTTP.

Deliberately hand-rolled on httpx rather than pulling in the MCP SDK: this
project treats new pip dependencies as a production risk (three past outages
came from requirements.txt gaps), and we need exactly three JSON-RPC methods.

Tool results are returned as raw text. Parsing is the caller's job because
COROS returns formatted prose for most tools and raw JSON for others.
"""

import json
from typing import Any

import httpx

from log_utils import get_logger

logger = get_logger(__name__)

PROTOCOL_VERSION = "2025-06-18"


class McpError(RuntimeError):
    """The MCP server returned a JSON-RPC error or an unusable response."""


class McpClient:
    def __init__(
        self,
        endpoint: str,
        access_token: str,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 60.0,
    ) -> None:
        self._endpoint = endpoint
        self._token = access_token
        self._session_id: str | None = None
        self._next_id = 0
        self._client = httpx.AsyncClient(transport=transport, timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "McpClient":
        try:
            await self.initialize()
        except BaseException:
            await self.aclose()
            raise
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL_VERSION,
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        return headers

    def _rpc_id(self) -> int:
        self._next_id += 1
        return self._next_id

    @staticmethod
    def _decode(response: httpx.Response, expected_id: int) -> dict[str, Any]:
        """Accepts either a plain JSON body or an SSE stream carrying one message.

        An SSE stream may legitimately interleave notification frames (e.g.
        notifications/progress) ahead of the actual JSON-RPC response, and a
        single frame's data may legally be split across multiple `data:`
        lines. So: split the body into events on blank lines, join each
        event's `data:` lines with "\\n" before parsing, skip frames that
        fail to parse or lack a matching `id` (notifications have no `id`
        at all), and return the first frame whose `id` equals `expected_id`.
        If none match -- including the case where there was no data frame
        at all -- raise McpError.
        """
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            for event in response.text.split("\n\n"):
                data_lines = [line[len("data:") :].strip() for line in event.splitlines() if line.startswith("data:")]
                if not data_lines:
                    continue
                try:
                    frame = json.loads("\n".join(data_lines))
                except json.JSONDecodeError:
                    continue
                if frame.get("id") == expected_id:
                    return frame
            raise McpError(f"SSE response contained no frame matching request id {expected_id}")
        return response.json()

    async def _post(self, label: str, json_body: dict[str, Any]) -> httpx.Response:
        """POSTs one JSON-RPC message and translates every transport-level
        failure into McpError: a non-2xx response (httpx.HTTPStatusError) and
        any other httpx.HTTPError (timeout, connect failure, etc.) alike.

        This is the client's only network boundary, so no httpx exception
        should ever escape McpClient -- the per-item isolation guards in
        services/providers/coros.py catch (CorosParseError, McpError) only,
        and a transport failure that instead surfaced as a bare httpx
        exception would bypass them entirely, aborting whatever batch is in
        flight. `label` identifies the failing call for debugging; the
        message never includes the request body or the bearer token.
        """
        try:
            response = await self._client.post(self._endpoint, headers=self._headers(), json=json_body)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise McpError(f"MCP request '{label}' failed with HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise McpError(f"MCP request '{label}' failed: {type(exc).__name__}") from exc
        return response

    async def initialize(self) -> None:
        request_id = self._rpc_id()
        response = await self._post(
            "initialize",
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "uphill-ai", "version": "1.0"},
                },
            },
        )
        self._session_id = response.headers.get("Mcp-Session-Id") or self._session_id
        payload = self._decode(response, request_id)
        if "error" in payload:
            raise McpError(str(payload["error"].get("message", payload["error"])))

        await self._post(
            "notifications/initialized",
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
        )

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        request_id = self._rpc_id()
        response = await self._post(
            name,
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            },
        )
        payload = self._decode(response, request_id)
        if "error" in payload:
            raise McpError(str(payload["error"].get("message", payload["error"])))

        result = payload.get("result", {})
        if result.get("isError"):
            raise McpError(f"tool {name} reported an error")
        text_blocks: list[str] = []
        for block in result.get("content", []):
            if block.get("type") == "text":
                block_text = block.get("text", "")
                if isinstance(block_text, str):
                    stripped = block_text.strip()
                    if stripped.startswith('"') and stripped.endswith('"') and len(stripped) >= 2:
                        try:
                            unquoted = json.loads(stripped)
                            if isinstance(unquoted, str):
                                block_text = unquoted
                        except json.JSONDecodeError:
                            pass
                    text_blocks.append(block_text)
        text = "".join(text_blocks)
        stripped_full = text.strip()
        if stripped_full.startswith('"') and stripped_full.endswith('"') and len(stripped_full) >= 2:
            try:
                unquoted = json.loads(stripped_full)
                if isinstance(unquoted, str):
                    text = unquoted
            except json.JSONDecodeError:
                pass
        logger.info(
            "mcp tool called",
            extra={
                "fields": {
                    "service": "mcp_client",
                    "event": "tool_called",
                    "tool": name,
                    "chars": len(text),
                }
            },
        )
        return text
