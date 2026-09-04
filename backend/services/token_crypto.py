"""Symmetric encryption for third-party OAuth tokens at rest.

A leaked refresh token grants standing access to an athlete's health data, so
these are encrypted in `athlete_connections` rather than stored as plaintext
(COROS API Agreement 11.2(c) requires encryption at rest).

Uses Fernet (AES-128-CBC + HMAC) from `cryptography`, which is already present
in the production image. Generate a key once with `generate_key()` and set it as
TOKEN_ENCRYPTION_KEY in backend/.env; losing it means every athlete must
reconnect their device account.
"""

from cryptography.fernet import Fernet, InvalidToken

from config import settings


class TokenEncryptionUnconfigured(RuntimeError):
    """TOKEN_ENCRYPTION_KEY is missing or empty."""


class TokenDecryptionError(RuntimeError):
    """Ciphertext could not be decrypted with the supplied key."""


def generate_key() -> str:
    """Returns a new url-safe base64 key. Run once, store in .env, never rotate
    casually -- rotation invalidates every stored token."""
    return Fernet.generate_key().decode()


def _fernet(key: str | None) -> Fernet:
    resolved = key if key is not None else settings.TOKEN_ENCRYPTION_KEY
    if not resolved:
        raise TokenEncryptionUnconfigured(
            "TOKEN_ENCRYPTION_KEY is not set; device account tokens cannot be stored. "
            "Generate one with services.token_crypto.generate_key()."
        )
    return Fernet(resolved.encode() if isinstance(resolved, str) else resolved)


def encrypt_token(plaintext: str, key: str | None = None) -> str:
    return _fernet(key).encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str, key: str | None = None) -> str:
    try:
        return _fernet(key).decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise TokenDecryptionError("Stored token could not be decrypted.") from exc
