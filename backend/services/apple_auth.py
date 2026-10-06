"""Verifies Sign in with Apple identity tokens (RS256 JWTs signed by Apple)."""

from typing import Any

import jwt
from jwt import PyJWKClient

APPLE_ISSUER = "https://appleid.apple.com"
APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"

# Fetches Apple's public keys on first use and caches them.
_jwk_client = PyJWKClient(APPLE_JWKS_URL, cache_keys=True)


class AppleTokenError(Exception):
    pass


def verify_identity_token(token: str, audiences: list[str], jwk_client: Any = None) -> dict[str, Any]:
    client = jwk_client or _jwk_client
    try:
        key = client.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=["RS256"], audience=audiences, issuer=APPLE_ISSUER)
    except jwt.PyJWTError as e:
        raise AppleTokenError(str(e)) from e
    if not claims.get("sub"):
        raise AppleTokenError("Apple identity token has no subject.")
    return claims
