"""Unit tests for token_crypto -- no DB, no network."""

import pytest

from services import token_crypto


def test_round_trips_a_token():
    key = token_crypto.generate_key()
    enc = token_crypto.encrypt_token("refresh-abc-123", key=key)
    assert token_crypto.decrypt_token(enc, key=key) == "refresh-abc-123"


def test_ciphertext_does_not_contain_the_plaintext():
    key = token_crypto.generate_key()
    enc = token_crypto.encrypt_token("refresh-abc-123", key=key)
    assert "refresh-abc-123" not in enc


def test_same_plaintext_encrypts_differently_each_time():
    # Fernet includes a random IV; identical tokens must not produce identical
    # ciphertext, or the database leaks which users share a value.
    key = token_crypto.generate_key()
    assert token_crypto.encrypt_token("same", key=key) != token_crypto.encrypt_token("same", key=key)


def test_decrypting_with_the_wrong_key_raises():
    enc = token_crypto.encrypt_token("secret", key=token_crypto.generate_key())
    with pytest.raises(token_crypto.TokenDecryptionError):
        token_crypto.decrypt_token(enc, key=token_crypto.generate_key())


def test_encrypting_without_a_configured_key_raises_a_clear_error():
    with pytest.raises(token_crypto.TokenEncryptionUnconfigured):
        token_crypto.encrypt_token("secret", key="")
