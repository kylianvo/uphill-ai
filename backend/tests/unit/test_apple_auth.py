"""Unit tests for Sign in with Apple identity-token verification. No network:
a local RSA key stands in for Apple's JWKS."""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from services import apple_auth

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class _FakeJwkClient:
    def get_signing_key_from_jwt(self, token):
        class _Key:
            key = _KEY.public_key()

        return _Key()


def _token(**overrides):
    now = int(time.time())
    claims = {
        "iss": "https://appleid.apple.com",
        "aud": "ai.uphill.app",
        "sub": "001234.abcd",
        "email": "ana@privaterelay.appleid.com",
        "email_verified": "true",
        "iat": now,
        "exp": now + 600,
    }
    claims.update(overrides)
    return jwt.encode(claims, _KEY, algorithm="RS256", headers={"kid": "k1"})


def test_valid_token_returns_claims():
    claims = apple_auth.verify_identity_token(_token(), ["ai.uphill.app"], jwk_client=_FakeJwkClient())
    assert claims["sub"] == "001234.abcd"


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "com.other.app"},
        {"iss": "https://evil.example"},
        {"exp": int(time.time()) - 10},
        {"sub": ""},
    ],
)
def test_rejects_bad_claims(overrides):
    with pytest.raises(apple_auth.AppleTokenError):
        apple_auth.verify_identity_token(_token(**overrides), ["ai.uphill.app"], jwk_client=_FakeJwkClient())


def test_rejects_garbage():
    with pytest.raises(apple_auth.AppleTokenError):
        apple_auth.verify_identity_token("not-a-jwt", ["ai.uphill.app"], jwk_client=_FakeJwkClient())
