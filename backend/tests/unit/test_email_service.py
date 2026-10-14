"""Password reset code helpers and the SMTP email service -- no DB, no network."""

import hashlib

from services import auth_service


def test_reset_code_is_six_digits_zero_padded(monkeypatch):
    monkeypatch.setattr(auth_service.secrets, "randbelow", lambda n: 42)
    assert auth_service.generate_reset_code() == "000042"


def test_reset_code_is_random_six_digit_string():
    codes = {auth_service.generate_reset_code() for _ in range(50)}
    assert all(len(c) == 6 and c.isdigit() for c in codes)
    assert len(codes) > 1


def test_hash_reset_code_is_sha256_hex():
    assert auth_service.hash_reset_code("012345") == hashlib.sha256(b"012345").hexdigest()
    assert auth_service.hash_reset_code("012345") != auth_service.hash_reset_code("012346")
