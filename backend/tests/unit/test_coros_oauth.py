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


@pytest.mark.asyncio
async def test_refresh_raises_coros_auth_error_on_a_non_json_error_body():
    # A proxy sitting in front of COROS can return an HTML error page (a 502)
    # instead of JSON. _post_token must check the status code before parsing
    # the body, or this surfaces as json.JSONDecodeError -- which the
    # background refresh path in coros_sync._access_token does not catch,
    # unlike the callback's broader ValueError net.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, text="<html>Bad Gateway</html>", headers={"content-type": "text/html"})

    with pytest.raises(coros_oauth.CorosAuthError, match="502") as exc_info:
        await coros_oauth.refresh("some-refresh-token", transport=httpx.MockTransport(handler))
    assert "some-refresh-token" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_refresh_raises_coros_auth_error_on_a_non_json_success_body():
    # Belt-and-braces: even a 200 with a non-JSON body (a misconfigured proxy
    # serving a static page) must not raise json.JSONDecodeError.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json", headers={"content-type": "text/plain"})

    with pytest.raises(coros_oauth.CorosAuthError, match="200"):
        await coros_oauth.refresh("some-refresh-token", transport=httpx.MockTransport(handler))
