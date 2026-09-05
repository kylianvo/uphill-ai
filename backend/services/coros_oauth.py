"""OAuth 2.1 authorization-code + PKCE flow against COROS's MCP auth server.

Endpoints confirmed live at
https://mcp.coros.com/.well-known/oauth-authorization-server -- COROS supports
dynamic client registration, so no partner approval is needed. Registration is a
one-off operator step (scripts/register_coros_client.py); the issued client id
and secret live in .env.

`offline_access` is requested because background sync has to run when the
athlete is not present.

Token requests authenticate via `client_secret_post` (client_id/client_secret
in the form body) to match the `token_endpoint_auth_method` requested at
registration time in scripts/register_coros_client.py -- not HTTP Basic auth.
"""

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

from config import settings

AUTHORIZE_URL = "https://mcpus.coros.com/oauth2/authorize"
TOKEN_URL = "https://mcpus.coros.com/oauth2/token"
REGISTRATION_URL = "https://mcpus.coros.com/connect/register"
SCOPES = "openid mcp.tools offline_access"


class CorosAuthError(RuntimeError):
    """COROS rejected an authorization or token request."""


@dataclass(frozen=True)
class TokenSet:
    access_token: str
    refresh_token: str | None
    expires_at: datetime | None


def make_pkce_pair() -> tuple[str, str]:
    """Returns (verifier, challenge). Store the verifier against the state value;
    it must be replayed at code exchange."""
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def build_authorize_url(state: str, code_challenge: str) -> str:
    return (
        AUTHORIZE_URL
        + "?"
        + urlencode(
            {
                "response_type": "code",
                "client_id": settings.COROS_CLIENT_ID,
                "redirect_uri": settings.COROS_REDIRECT_URI,
                "scope": SCOPES,
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        )
    )


async def _post_token(data: dict[str, str], transport: httpx.BaseTransport | None) -> dict:
    # client_secret_post: credentials travel in the form body, matching the
    # token_endpoint_auth_method requested at dynamic-registration time.
    body = {
        **data,
        "client_id": settings.COROS_CLIENT_ID,
        "client_secret": settings.COROS_CLIENT_SECRET,
    }
    async with httpx.AsyncClient(transport=transport, timeout=30.0) as client:
        response = await client.post(
            TOKEN_URL,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    # Check the status before touching the body: a proxy in front of COROS
    # (a 502, an HTML error page) returns a non-JSON body, and calling
    # response.json() first would raise json.JSONDecodeError instead of a
    # message that says what happened. The callback in routers/integrations.py
    # happens to catch ValueError (json.JSONDecodeError's base class) so that
    # path is covered either way, but the background refresh path in
    # coros_sync._access_token is not -- it would otherwise surface a proxy
    # outage to the athlete as a bare "Expecting value: line 1 column 1".
    if response.status_code >= 400:
        try:
            error_payload = response.json()
            detail = error_payload.get("error", response.text)
        except ValueError:
            detail = response.text
        raise CorosAuthError(f"COROS token endpoint returned HTTP {response.status_code}: {detail}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise CorosAuthError(f"COROS token endpoint returned a non-JSON body (HTTP {response.status_code})") from exc
    if "error" in payload:
        raise CorosAuthError(str(payload.get("error", response.text)))
    return payload


def _to_token_set(payload: dict, fallback_refresh: str | None) -> TokenSet:
    expires_in = payload.get("expires_in")
    expires_at = datetime.now(UTC) + timedelta(seconds=int(expires_in)) if expires_in else None
    return TokenSet(
        access_token=payload["access_token"],
        refresh_token=payload.get("refresh_token") or fallback_refresh,
        expires_at=expires_at,
    )


async def exchange_code(code: str, code_verifier: str, transport: httpx.BaseTransport | None = None) -> TokenSet:
    payload = await _post_token(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.COROS_REDIRECT_URI,
            "code_verifier": code_verifier,
        },
        transport,
    )
    return _to_token_set(payload, fallback_refresh=None)


async def refresh(refresh_token: str, transport: httpx.BaseTransport | None = None) -> TokenSet:
    payload = await _post_token(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        transport,
    )
    return _to_token_set(payload, fallback_refresh=refresh_token)
