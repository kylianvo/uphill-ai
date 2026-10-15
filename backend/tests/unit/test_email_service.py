"""Password reset code helpers and the SMTP email service -- no DB, no network."""

import hashlib
import smtplib

import pytest
from prometheus_client import REGISTRY

from config import settings
from services import auth_service, email_service


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


class FakeSMTP:
    instances: list["FakeSMTP"] = []

    def __init__(self, host, port, timeout):
        self.host, self.port, self.timeout = host, port, timeout
        self.logged_in = None
        self.sent = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def login(self, user, password):
        self.logged_in = (user, password)

    def send_message(self, msg):
        self.sent.append(msg)


@pytest.fixture
def smtp(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test", raising=False)
    monkeypatch.setattr(settings, "SMTP_PORT", 465, raising=False)
    monkeypatch.setattr(settings, "SMTP_USER", "viet.vo@uphill-ai.io.vn", raising=False)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "pw", raising=False)
    monkeypatch.setattr(settings, "MAIL_FROM", "Uphill AI <viet.vo@uphill-ai.io.vn>", raising=False)
    monkeypatch.setattr(email_service.smtplib, "SMTP_SSL", FakeSMTP)
    return FakeSMTP


def test_send_email_logs_in_and_sends(smtp):
    email_service.send_email("ada@example.com", "Hi", "Body text")
    [conn] = smtp.instances
    assert (conn.host, conn.port, conn.timeout) == ("smtp.test", 465, 10)
    assert conn.logged_in == ("viet.vo@uphill-ai.io.vn", "pw")
    [msg] = conn.sent
    assert msg["To"] == "ada@example.com"
    assert msg["From"] == "Uphill AI <viet.vo@uphill-ai.io.vn>"
    assert msg["Subject"] == "Hi"
    assert msg.get_content().strip() == "Body text"


def test_send_email_skips_without_smtp_host(smtp, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    email_service.send_email("ada@example.com", "Hi", "Body")
    assert smtp.instances == []


@pytest.mark.parametrize(
    "lang, subject",
    [
        ("en", "Your Uphill AI password reset code"),
        ("vi", "Mã đặt lại mật khẩu Uphill AI"),
        ("vi-VN", "Mã đặt lại mật khẩu Uphill AI"),
        ("fr", "Your Uphill AI password reset code"),
        ("", "Your Uphill AI password reset code"),
    ],
)
def test_reset_email_language(smtp, lang, subject):
    email_service.send_password_reset_code("ada@example.com", "012345", lang)
    [msg] = smtp.instances[0].sent
    assert msg["Subject"] == subject
    assert "012345" in msg.get_content()


def test_send_failure_is_swallowed_and_counted(smtp, monkeypatch, caplog):
    def boom(*a, **k):
        raise smtplib.SMTPException("down")

    monkeypatch.setattr(email_service.smtplib, "SMTP_SSL", boom)
    before = REGISTRY.get_sample_value("password_reset_email_failures_total") or 0
    email_service.send_password_reset_code("ada@example.com", "987654", "en")  # must not raise
    assert REGISTRY.get_sample_value("password_reset_email_failures_total") == before + 1
    assert "987654" not in caplog.text
