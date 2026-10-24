"""OAuth 2.0 PKCE against Garmin Connect, plus the partner-gateway user calls.

Token calls must come from this backend: Garmin has no secretless (public-client)
flow. Access tokens last a day; the refresh token rotates on every refresh, so the
new one must always be stored.
"""

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

import db
from config import settings
from services import token_crypto
from services.coros_oauth import TokenSet

AUTHORIZE_URL = "https://connect.garmin.com/oauth2Confirm"
TOKEN_URL = "https://diauth.garmin.com/di-oauth2-service/oauth/token"
GATEWAY = "https://apis.garmin.com/partner-gateway/rest/user"
PROVIDER = "garmin"
# Garmin advises refreshing well ahead of expiry to absorb network trouble.
REFRESH_MARGIN = timedelta(minutes=10)


class GarminAuthError(RuntimeError):
    """Garmin rejected an authorization, token or gateway request. `status` is the HTTP
    status when Garmin answered, None when it never did."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


def build_authorize_url(state: str, code_challenge: str) -> str:
    return (
        AUTHORIZE_URL
        + "?"
        + urlencode(
            {
                "response_type": "code",
                "client_id": settings.GARMIN_CLIENT_ID,
                "redirect_uri": settings.GARMIN_REDIRECT_URI,
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        )
    )


async def _post_token(data: dict[str, str], transport: httpx.BaseTransport | None) -> TokenSet:
    async with httpx.AsyncClient(transport=transport, timeout=30.0) as client:
        response = await client.post(
            TOKEN_URL,
            data=data,
            auth=(settings.GARMIN_CLIENT_ID, settings.GARMIN_CLIENT_SECRET),
        )
    if response.status_code >= 400:
        raise GarminAuthError(f"Garmin token endpoint returned HTTP {response.status_code}", response.status_code)
    try:
        payload = response.json()
    except ValueError as exc:
        raise GarminAuthError(f"Garmin token endpoint returned a non-JSON body (HTTP {response.status_code})") from exc
    if "access_token" not in payload:
        raise GarminAuthError("Garmin token response had no access_token")
    expires_in = payload.get("expires_in")
    return TokenSet(
        access_token=payload["access_token"],
        refresh_token=payload.get("refresh_token"),
        expires_at=datetime.now(UTC) + timedelta(seconds=int(expires_in)) if expires_in else None,
    )


async def exchange_code(code: str, code_verifier: str, transport: httpx.BaseTransport | None = None) -> TokenSet:
    return await _post_token(
        {
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": settings.GARMIN_REDIRECT_URI,
        },
        transport,
    )


async def refresh(refresh_token: str, transport: httpx.BaseTransport | None = None) -> TokenSet:
    return await _post_token({"grant_type": "refresh_token", "refresh_token": refresh_token}, transport)


async def _gateway(
    method: str, path: str, access_token: str, transport: httpx.BaseTransport | None = None
) -> httpx.Response:
    async with httpx.AsyncClient(transport=transport, timeout=30.0) as client:
        response = await client.request(
            method, f"{GATEWAY}/{path}", headers={"Authorization": f"Bearer {access_token}"}
        )
    if response.status_code >= 400:
        raise GarminAuthError(f"Garmin {path} returned HTTP {response.status_code}", response.status_code)
    return response


async def fetch_user_id(access_token: str, transport: httpx.BaseTransport | None = None) -> str:
    """The stable Garmin user id every push is keyed by."""
    return str((await _gateway("GET", "id", access_token, transport)).json()["userId"])


async def fetch_permissions(access_token: str, transport: httpx.BaseTransport | None = None) -> list[str]:
    return list((await _gateway("GET", "permissions", access_token, transport)).json().get("permissions") or [])


async def delete_registration(access_token: str, transport: httpx.BaseTransport | None = None) -> None:
    """Required whenever the user disconnects from inside our app."""
    await _gateway("DELETE", "registration", access_token, transport)


async def access_token(connection: dict, transport: httpx.BaseTransport | None = None) -> str:
    """A usable access token for a stored connection, refreshing (and storing the rotated
    refresh token) when it is near expiry."""
    expires_at = connection.get("token_expires_at")
    if not expires_at or expires_at > datetime.now(UTC) + REFRESH_MARGIN:
        return token_crypto.decrypt_token(connection["access_token_enc"])
    if not connection.get("refresh_token_enc"):
        raise GarminAuthError("No Garmin refresh token on file; the athlete must reconnect.")
    tokens = await refresh(token_crypto.decrypt_token(connection["refresh_token_enc"]), transport)
    db.save_connection(
        user_id=connection["user_id"],
        provider=PROVIDER,
        access_token_enc=token_crypto.encrypt_token(tokens.access_token),
        refresh_token_enc=token_crypto.encrypt_token(tokens.refresh_token) if tokens.refresh_token else None,
        token_expires_at=tokens.expires_at,
        scopes=connection.get("scopes") or "",
    )
    return tokens.access_token
