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
        await self.initialize()
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
    def _decode(response: httpx.Response) -> dict[str, Any]:
        """Accepts either a plain JSON body or an SSE stream carrying one message."""
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            for line in response.text.splitlines():
                if line.startswith("data:"):
                    return json.loads(line[5:].strip())
            raise McpError("SSE response contained no data frame")
        return response.json()

    async def initialize(self) -> None:
        response = await self._client.post(
            self._endpoint,
            headers=self._headers(),
            json={
                "jsonrpc": "2.0",
                "id": self._rpc_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "uphill-ai", "version": "1.0"},
                },
            },
        )
        response.raise_for_status()
        self._session_id = response.headers.get("Mcp-Session-Id") or self._session_id
        payload = self._decode(response)
        if "error" in payload:
            raise McpError(str(payload["error"].get("message", payload["error"])))

        await self._client.post(
            self._endpoint,
            headers=self._headers(),
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        )

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        response = await self._client.post(
            self._endpoint,
            headers=self._headers(),
            json={
                "jsonrpc": "2.0",
                "id": self._rpc_id(),
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            },
        )
        response.raise_for_status()
        payload = self._decode(response)
        if "error" in payload:
            raise McpError(str(payload["error"].get("message", payload["error"])))

        result = payload.get("result", {})
        if result.get("isError"):
            raise McpError(f"tool {name} reported an error")
        text = "".join(block.get("text", "") for block in result.get("content", []) if block.get("type") == "text")
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
