"""Outbound email over SMTP with implicit TLS (the domain's cPanel mailbox)."""

import smtplib
from email.message import EmailMessage

from config import settings
from log_utils import get_logger
from telemetry import password_reset_email_failures_total

logger = get_logger(__name__)

RESET_EMAIL = {
    "en": (
        "Your Uphill AI password reset code",
        "Your code is {code}. It expires in 15 minutes.\n\n"
        "If you didn't ask to reset your password, ignore this email. Your password stays the same.\n\n"
        "Uphill AI",
    ),
    "vi": (
        "Mã đặt lại mật khẩu Uphill AI",
        "Mã của bạn là {code}. Mã hết hạn sau 15 phút.\n\n"
        "Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này. Mật khẩu của bạn vẫn giữ nguyên.\n\n"
        "Uphill AI",
    ),
}


def send_email(to: str, subject: str, body: str) -> None:
    """Sends a plain-text email; raises on SMTP errors. No-op when SMTP_HOST is unset."""
    if not settings.SMTP_HOST:
        logger.info("email skipped: SMTP not configured (to=%s, subject=%s)", to, subject)
        return
    msg = EmailMessage()
    msg["From"] = settings.MAIL_FROM or settings.SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


def send_password_reset_code(to: str, code: str, lang: str) -> None:
    """Runs as a background task, so it never raises: the user can press Resend."""
    subject, body = RESET_EMAIL["vi" if str(lang).lower().startswith("vi") else "en"]
    try:
        send_email(to, subject, body.format(code=code))
    except Exception:
        logger.exception("password reset email failed")
        password_reset_email_failures_total.inc()
