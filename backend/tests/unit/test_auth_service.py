"""Tests for hash_password/verify_password — security-critical, pure bcrypt
wrappers with no DB/network dependency."""

from services.auth_service import hash_password, verify_password


class TestHashPassword:
    def test_hash_differs_from_plaintext(self):
        hashed = hash_password("correct horse battery staple")
        assert hashed != "correct horse battery staple"

    def test_hashing_the_same_password_twice_produces_different_hashes(self):
        # bcrypt salts each hash independently.
        first = hash_password("same-password")
        second = hash_password("same-password")
        assert first != second


class TestVerifyPassword:
    def test_correct_password_verifies(self):
        hashed = hash_password("hunter2")
        assert verify_password("hunter2", hashed) is True

    def test_incorrect_password_fails(self):
        hashed = hash_password("hunter2")
        assert verify_password("wrong-password", hashed) is False

    def test_empty_plain_password_fails_without_raising(self):
        hashed = hash_password("hunter2")
        assert verify_password("", hashed) is False

    def test_empty_hashed_password_fails_without_raising(self):
        assert verify_password("hunter2", "") is False

    def test_malformed_hash_fails_without_raising(self):
        assert verify_password("hunter2", "not-a-bcrypt-hash") is False
