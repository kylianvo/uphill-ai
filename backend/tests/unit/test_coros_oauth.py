"""Unit tests for coros_oauth -- HTTP is mocked, no network."""

import base64
import hashlib
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from services import coros_oauth


def test_make_pkce_pair_produces_a_valid_s256_challenge():
    verifier, challenge = coros_oauth.make_pkce_pair()
    expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    assert challenge == expected
    assert 43 <= len(verifier) <= 128


def test_authorize_url_requests_offline_access_so_we_can_sync_in_the_background():
    url = coros_oauth.build_authorize_url(state="st", code_challenge="ch")
    scopes = parse_qs(urlparse(url).query)["scope"][0].split()
    assert "offline_access" in scopes
    assert "mcp.tools" in scopes


def test_authorize_url_uses_pkce_s256():
    q = parse_qs(urlparse(coros_oauth.build_authorize_url(state="st", code_challenge="ch")).query)
    assert q["code_challenge_method"] == ["S256"]
    assert q["code_challenge"] == ["ch"]
    assert q["response_type"] == ["code"]


@pytest.mark.asyncio
async def test_exchange_code_returns_tokens_with_an_absolute_expiry():
    def handler(request: httpx.Request) -> httpx.Response:
        assert b"grant_type=authorization_code" in request.content
        return httpx.Response(200, json={"access_token": "at", "refresh_token": "rt", "expires_in": 3600})

    tokens = await coros_oauth.exchange_code("the-code", "the-verifier", transport=httpx.MockTransport(handler))
    assert tokens.access_token == "at"
    assert tokens.refresh_token == "rt"
    assert tokens.expires_at is not None


@pytest.mark.asyncio
async def test_refresh_keeps_the_old_refresh_token_when_the_server_omits_one():
    # Some servers rotate refresh tokens, some don't. Dropping the old one on a
    # non-rotating server would silently disconnect the athlete.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": "new-at", "expires_in": 3600})

    tokens = await coros_oauth.refresh("old-rt", transport=httpx.MockTransport(handler))
    assert tokens.access_token == "new-at"
    assert tokens.refresh_token == "old-rt"


@pytest.mark.asyncio
async def test_exchange_code_raises_on_an_oauth_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "invalid_grant"})

    with pytest.raises(coros_oauth.CorosAuthError, match="invalid_grant"):
        await coros_oauth.exchange_code("bad", "v", transport=httpx.MockTransport(handler))
