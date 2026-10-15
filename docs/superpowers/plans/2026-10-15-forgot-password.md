# Forgot Password Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a user who forgot their password request a 6-digit code by email and set a new password from it, on web and iOS, landing logged in.

**Architecture:** One new table `password_reset_codes` holds hashed codes. Two public FastAPI routes sit beside `/api/auth/login`: `forgot-password` creates a code and emails it in a background task through the domain mailbox over SMTP, and `reset-password` checks the code, sets the password, clears every session in one transaction, and returns a login response. The web `AuthModal` and the iOS `SignInView` each get a two-step form that calls these routes.

**Tech Stack:** FastAPI + SQLAlchemy Core `text()` on Postgres, Alembic, stdlib `smtplib`/`email`/`secrets`/`hashlib`/`hmac`, prometheus_client; Next.js 16 + React + vitest; SwiftUI + Swift Testing (xcodegen project).

**Spec:** `docs/superpowers/specs/2026-10-15-forgot-password-design.md`

## Global Constraints

- Code: 6 digits, `secrets.randbelow(10**6)` zero-padded; stored only as SHA-256 hex; expires 15 minutes after creation.
- A code dies after 5 wrong attempts; a used or superseded code never works again.
- Rate limit per user: 1 code per 60 s, 5 per hour; over-limit requests get the normal 200 and send nothing.
- `POST /api/auth/forgot-password` always returns `200 {"message": "If an account exists for this email, we sent a code."}`.
- Every reset failure except password length returns `400 "Invalid or expired code."`; password length uses `400 "Password must be at least 8 characters."` (same rule as register).
- A successful reset deletes ALL the user's `sessions` rows, then returns `{session_token, expires_at, user}` exactly like `/api/auth/login`.
- SMTP: `smtplib.SMTP_SSL`, 10 s timeout. Prod values `SMTP_HOST=cp02hn.emailserver.net.vn`, `SMTP_PORT=465`, `SMTP_USER=viet.vo@uphill-ai.io.vn`, `MAIL_FROM=Uphill AI <viet.vo@uphill-ai.io.vn>`, `SMTP_PASSWORD` set only by the owner in the server's `backend/.env`, never committed.
- Empty `SMTP_HOST` means "log `email skipped: SMTP not configured` and return".
- Logs never contain the code or any password.
- Schema changes go in BOTH `db.py:init_db()` and a hand-written Alembic migration (`db-migration` skill).
- All user-visible copy ships in EN and VI; review the VI with the `uphill-ai-vietnamese-copy` skill.
- UI work isn't done until there's a real local screenshot (`ui-screenshot-evidence` skill).
- Integration tests TRUNCATE every table: run them only against the scratch `uphill_ai_test` database (local docker Postgres on host port 5433).

## Review Focus

1. **Email typed with different case or spaces** (`"  ADA@Uphill.ai "`): forgot and reset must both find the account. Pinned in Task 3 (`test_email_case_and_spaces_are_ignored`).
2. **Code pasted with surrounding whitespace or with a leading zero** (`" 012345 "`): must work; the code is a string, never an int. Pinned in Task 1 (zero-padding) and Task 3 (`test_code_with_whitespace_works`).
3. **SMTP down or slow:** forgot-password still returns 200, the failure is logged and counted, nothing raises into the request. Pinned in Task 2 (`test_send_failure_is_swallowed_and_counted`).
4. **Old devices after a reset:** a session token issued before the reset must stop working at once. Pinned in Task 3 (`test_reset_signs_in_and_kills_old_sessions`).
5. **Unknown or regional `lang`** (`"fr"`, `"vi-VN"`, missing): falls back to English or picks Vietnamese and never errors. Pinned in Task 2 (`test_reset_email_language`).

---

## File map

| File | Change | Responsibility |
|---|---|---|
| `backend/db.py` | modify | `password_reset_codes` table in `init_db()`; `create_password_reset_code`, `consume_password_reset_code` |
| `backend/alembic/versions/c8e2a4f6d9b1_password_reset_codes.py` | create | migration for the table |
| `backend/tests/integration/conftest.py` | modify | add the table to `ALL_TABLES` |
| `backend/services/auth_service.py` | modify | `generate_reset_code`, `hash_reset_code` |
| `backend/config.py` | modify | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM` |
| `backend/telemetry.py` | modify | `password_reset_email_failures_total` counter |
| `backend/services/email_service.py` | create | `send_email`, `send_password_reset_code` |
| `backend/main.py` | modify | request models + the two routes |
| `backend/tests/unit/test_email_service.py` | create | email + code helper unit tests |
| `backend/tests/integration/test_password_reset.py` | create | db helpers + routes end to end |
| `CLAUDE.md` | modify | document the SMTP env vars |
| `frontend/src/components/ForgotPasswordForm.tsx` | create | two-step form, presentational, callbacks in props |
| `frontend/src/components/ForgotPasswordForm.test.tsx` | create | vitest |
| `frontend/src/hooks/useAppAuth.ts` | modify | `requestPasswordReset`, `resetPassword`, `"forgot"` tab |
| `frontend/src/views/AuthModal.tsx` | modify | "Forgot password?" link, render the form |
| `frontend/src/app/translations.ts` | modify | EN/VI keys |
| `ios-native/UphillAI/Core/Auth/AuthService.swift` | modify | two protocol methods + implementations |
| `ios-native/UphillAITests/Support/FakeAuthService.swift` | modify | conform to the new methods |
| `ios-native/UphillAI/Features/Auth/ForgotPasswordViewModel.swift` | create | state + calls |
| `ios-native/UphillAI/Features/Auth/ForgotPasswordView.swift` | create | sheet UI |
| `ios-native/UphillAI/Features/Auth/SignInViewModel.swift` | modify | `makeForgotPasswordModel()` |
| `ios-native/UphillAI/Features/Auth/SignInView.swift` | modify | "Forgot password?" button + sheet; `inputBox()` made internal |
| `ios-native/UphillAI/Resources/Localizable.xcstrings` | modify | VI strings |
| `ios-native/UphillAITests/Auth/AuthServiceTests.swift` | modify | two endpoint tests |
| `ios-native/UphillAITests/Auth/ForgotPasswordViewModelTests.swift` | create | view model tests |

The unused `handleEmailLogin` in `frontend/src/app/app/page.tsx:1494` is dead code (the modal uses `useAppAuth`). Leave it alone.

---

### Task 1: Schema and code helpers

**Files:**
- Modify: `backend/db.py` (inside `init_db()`, right after the `sessions` CREATE TABLE at ~line 102; helpers after `delete_session` at ~line 3002)
- Create: `backend/alembic/versions/c8e2a4f6d9b1_password_reset_codes.py`
- Modify: `backend/tests/integration/conftest.py` (`ALL_TABLES`)
- Modify: `backend/services/auth_service.py`
- Test: `backend/tests/unit/test_email_service.py` (code helper tests live here, alongside Task 2's)

**Interfaces:**
- Produces: `generate_reset_code() -> str`, `hash_reset_code(code: str) -> str` in `services/auth_service.py`; table `password_reset_codes`.

- [ ] **Step 1: Write the failing helper tests**

Create `backend/tests/unit/test_email_service.py`:

```python
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
```

- [ ] **Step 2: Run to see it fail**

Run: `cd backend && pytest tests/unit/test_email_service.py -q`
Expected: FAIL, `AttributeError: module 'services.auth_service' has no attribute 'secrets'`.

- [ ] **Step 3: Add the helpers**

Edit `backend/services/auth_service.py`: add `import hashlib` and `import secrets` beside the existing `import bcrypt`, then append:

```python
def generate_reset_code() -> str:
    return f"{secrets.randbelow(10**6):06d}"


def hash_reset_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()
```

- [ ] **Step 4: Run the tests**

Run: `cd backend && pytest tests/unit/test_email_service.py -q`
Expected: 3 passed.

- [ ] **Step 5: Add the table to `init_db()`**

In `backend/db.py`, directly after the `conn.execute(text("""CREATE TABLE IF NOT EXISTS sessions (...)"""))` call, add:

```python
        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS password_reset_codes (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            code_hash   TEXT NOT NULL,
            expires_at  TIMESTAMPTZ NOT NULL,
            attempts    INTEGER NOT NULL DEFAULT 0,
            used_at     TIMESTAMPTZ,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_password_reset_codes_user_created "
                "ON password_reset_codes (user_id, created_at)"
            )
        )
```

- [ ] **Step 6: Write the migration**

Confirm the current head first: `cd backend && alembic heads` → expect `b3d9f1a6c2e4 (head)`. If it differs, use that value as `down_revision`.

Create `backend/alembic/versions/c8e2a4f6d9b1_password_reset_codes.py`:

```python
"""password_reset_codes: hashed 6-digit codes for forgot-password

Revision ID: c8e2a4f6d9b1
Revises: b3d9f1a6c2e4
Create Date: 2026-10-15 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c8e2a4f6d9b1"
down_revision: str | Sequence[str] | None = "b3d9f1a6c2e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "password_reset_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_password_reset_codes_user_created", "password_reset_codes", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_password_reset_codes_user_created", table_name="password_reset_codes")
    op.drop_table("password_reset_codes")
```

- [ ] **Step 7: Register the table for test truncation**

In `backend/tests/integration/conftest.py`, add `"password_reset_codes",` to `ALL_TABLES` on the line directly above `"sessions",`.

- [ ] **Step 8: Verify the migration applies on a scratch DB**

Run (local docker Postgres on 5433, scratch DB only):
```bash
cd backend && DATABASE_URL=postgresql://uphill:uphill_secret@localhost:5433/uphill_ai_test alembic upgrade head && alembic heads
```
Expected: `c8e2a4f6d9b1 (head)`, a single head. If `uphill_ai_test` was built by `init_db()` and the upgrade collides with existing tables, stamp it instead (`alembic stamp b3d9f1a6c2e4` then `alembic upgrade head`); the goal is to prove the migration file runs.

- [ ] **Step 9: Commit**

```bash
git add backend/db.py backend/alembic/versions/c8e2a4f6d9b1_password_reset_codes.py backend/tests/integration/conftest.py backend/services/auth_service.py backend/tests/unit/test_email_service.py
git commit -m "feat(auth): password_reset_codes table and code helpers"
```

---

### Task 2: SMTP email service

**Files:**
- Modify: `backend/config.py` (inside `class Config`, near `GOOGLE_CLIENT_ID`)
- Modify: `backend/telemetry.py`
- Create: `backend/services/email_service.py`
- Modify: `CLAUDE.md` (Environment Variables list, after the `TAVILY_API_KEY` bullet)
- Test: `backend/tests/unit/test_email_service.py`

**Interfaces:**
- Produces: `send_email(to: str, subject: str, body: str) -> None` (raises on SMTP error), `send_password_reset_code(to: str, code: str, lang: str) -> None` (never raises), and counter `password_reset_email_failures_total`.

- [ ] **Step 1: Write the failing tests**

Add to the import block at the top of `backend/tests/unit/test_email_service.py` (keep ruff's import order):

```python
import smtplib

import pytest
from prometheus_client import REGISTRY

from config import settings
from services import email_service
```

Then append:

```python
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
```

- [ ] **Step 2: Run to see them fail**

Run: `cd backend && pytest tests/unit/test_email_service.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'services.email_service'`.

- [ ] **Step 3: Add config, counter and service**

In `backend/config.py`, inside `class Config` after `GOOGLE_CLIENT_ID`:

```python
    # Outbound email (password reset codes). Empty SMTP_HOST = log and skip sending.
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "")
```

Append to `backend/telemetry.py`:

```python
password_reset_email_failures_total = Counter(
    "password_reset_email_failures_total", "Password reset emails that failed to send"
)
```

Create `backend/services/email_service.py`:

```python
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
```

- [ ] **Step 4: Run the tests**

Run: `cd backend && pytest tests/unit/test_email_service.py -q`
Expected: all pass (3 + 8).

- [ ] **Step 5: Review the VI email copy**

Invoke the `uphill-ai-vietnamese-copy` skill on the `"vi"` entry of `RESET_EMAIL`. If it changes the subject, update the parametrized test's VI subject to match, and re-run Step 4.

- [ ] **Step 6: Document the env vars**

In `CLAUDE.md`, after the `TAVILY_API_KEY` bullet in "Environment Variables", add:

```markdown
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM` — outbound email for password reset codes (`services/email_service.py`, implicit TLS via `smtplib.SMTP_SSL`). Prod sends from the domain mailbox `viet.vo@uphill-ai.io.vn` through `cp02hn.emailserver.net.vn:465`. Empty `SMTP_HOST` logs and skips sending (local dev, tests); failures count in `password_reset_email_failures_total`
```

- [ ] **Step 7: Lint and commit**

```bash
cd backend && ruff check services/email_service.py tests/unit/test_email_service.py config.py telemetry.py && ruff format services/email_service.py tests/unit/test_email_service.py
cd .. && git add backend/config.py backend/telemetry.py backend/services/email_service.py backend/tests/unit/test_email_service.py CLAUDE.md
git commit -m "feat(auth): SMTP email service for password reset codes"
```

---

### Task 3: Reset data access and API routes

**Files:**
- Modify: `backend/db.py` (add `import hmac` to the top-level imports; helpers after `delete_session`)
- Modify: `backend/main.py` (models after `SetPasswordRequest` ~line 412; routes after `auth_set_password` ~line 1052; imports)
- Test: `backend/tests/integration/test_password_reset.py`

**Interfaces:**
- Consumes: `generate_reset_code`, `hash_reset_code` (Task 1); `send_password_reset_code(to, code, lang)` (Task 2).
- Produces:
  - `create_password_reset_code(user_id: int, code_hash: str, ttl_minutes: int = 15) -> bool`: False means rate-limited and nothing stored.
  - `consume_password_reset_code(user_id: int, code_hash: str, new_password_hash: str) -> bool`
  - `POST /api/auth/forgot-password {email, lang="en"}` → `200 {"message": ...}`
  - `POST /api/auth/reset-password {email, code, new_password}` → `200 {session_token, expires_at, user}` | `400 {"detail": ...}`

- [ ] **Step 1: Write the failing integration tests**

Create `backend/tests/integration/test_password_reset.py`:

```python
"""Forgot-password / reset-password end to end against the scratch DB.

The email background task is replaced by a recorder, so each test can read
the code that would have been mailed."""

import pytest
from sqlalchemy import text

from db import engine

FORGOT = "/api/auth/forgot-password"
RESET = "/api/auth/reset-password"
GENERIC = "If an account exists for this email, we sent a code."


@pytest.fixture
def sent(client, monkeypatch):
    mails = []
    monkeypatch.setattr("main.send_password_reset_code", lambda to, code, lang: mails.append((to, code, lang)))
    return mails


def register(client, email, password="correcthorse"):
    resp = client.post("/api/auth/register", json={"name": "Reset Tester", "email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["session_token"]


def run_sql(sql):
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()


def age_codes(minutes=2):
    run_sql(f"UPDATE password_reset_codes SET created_at = created_at - INTERVAL '{minutes} minutes'")


def test_unknown_email_gets_the_same_answer_and_no_mail(client, sent):
    resp = client.post(FORGOT, json={"email": "nobody@uphill.ai"})
    assert resp.status_code == 200
    assert resp.json() == {"message": GENERIC}
    assert sent == []


def test_known_email_gets_a_six_digit_code(client, sent):
    register(client, "known@uphill.ai")
    resp = client.post(FORGOT, json={"email": "known@uphill.ai", "lang": "vi"})
    assert resp.json() == {"message": GENERIC}
    [(to, code, lang)] = sent
    assert to == "known@uphill.ai" and lang == "vi"
    assert len(code) == 6 and code.isdigit()


def test_email_case_and_spaces_are_ignored(client, sent):
    register(client, "casey@uphill.ai")
    client.post(FORGOT, json={"email": "  CASEY@Uphill.ai "})
    [(to, code, _)] = sent
    assert to == "casey@uphill.ai"
    resp = client.post(RESET, json={"email": " Casey@UPHILL.ai", "code": code, "new_password": "newpassword1"})
    assert resp.status_code == 200, resp.text


def test_second_request_within_a_minute_sends_nothing(client, sent):
    register(client, "fast@uphill.ai")
    client.post(FORGOT, json={"email": "fast@uphill.ai"})
    resp = client.post(FORGOT, json={"email": "fast@uphill.ai"})
    assert resp.json() == {"message": GENERIC}
    assert len(sent) == 1


def test_sixth_request_in_an_hour_sends_nothing(client, sent):
    register(client, "many@uphill.ai")
    for _ in range(6):
        client.post(FORGOT, json={"email": "many@uphill.ai"})
        age_codes(2)
    assert len(sent) == 5


def test_new_request_retires_the_old_code(client, sent):
    register(client, "twice@uphill.ai")
    client.post(FORGOT, json={"email": "twice@uphill.ai"})
    age_codes(2)
    client.post(FORGOT, json={"email": "twice@uphill.ai"})
    old, new = sent[0][1], sent[1][1]
    if old != new:
        bad = client.post(RESET, json={"email": "twice@uphill.ai", "code": old, "new_password": "newpassword1"})
        assert bad.status_code == 400
    good = client.post(RESET, json={"email": "twice@uphill.ai", "code": new, "new_password": "newpassword1"})
    assert good.status_code == 200


def test_reset_signs_in_and_kills_old_sessions(client, sent):
    old_token = register(client, "reset@uphill.ai")
    client.post(FORGOT, json={"email": "reset@uphill.ai"})
    code = sent[0][1]

    resp = client.post(RESET, json={"email": "reset@uphill.ai", "code": code, "new_password": "brandnewpass"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["session_token"] and data["expires_at"]
    assert data["user"]["email"] == "reset@uphill.ai"

    old = client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_token}"})
    assert old.status_code == 401
    new = client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['session_token']}"})
    assert new.status_code == 200

    assert client.post("/api/auth/login", json={"email": "reset@uphill.ai", "password": "correcthorse"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "reset@uphill.ai", "password": "brandnewpass"}).status_code == 200

    again = client.post(RESET, json={"email": "reset@uphill.ai", "code": code, "new_password": "anotherpass1"})
    assert again.status_code == 400
    assert again.json()["detail"] == "Invalid or expired code."


def test_five_wrong_guesses_kill_the_code(client, sent):
    register(client, "guess@uphill.ai")
    client.post(FORGOT, json={"email": "guess@uphill.ai"})
    code = sent[0][1]
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        r = client.post(RESET, json={"email": "guess@uphill.ai", "code": wrong, "new_password": "newpassword1"})
        assert r.status_code == 400
    r = client.post(RESET, json={"email": "guess@uphill.ai", "code": code, "new_password": "newpassword1"})
    assert r.status_code == 400


def test_expired_code_is_rejected(client, sent):
    register(client, "late@uphill.ai")
    client.post(FORGOT, json={"email": "late@uphill.ai"})
    run_sql("UPDATE password_reset_codes SET expires_at = NOW() - INTERVAL '1 second'")
    r = client.post(RESET, json={"email": "late@uphill.ai", "code": sent[0][1], "new_password": "newpassword1"})
    assert r.status_code == 400


def test_short_password_is_rejected_without_using_the_code(client, sent):
    register(client, "short@uphill.ai")
    client.post(FORGOT, json={"email": "short@uphill.ai"})
    code = sent[0][1]
    r = client.post(RESET, json={"email": "short@uphill.ai", "code": code, "new_password": "short"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Password must be at least 8 characters."
    ok = client.post(RESET, json={"email": "short@uphill.ai", "code": code, "new_password": "longenough1"})
    assert ok.status_code == 200


def test_code_with_whitespace_works(client, sent):
    register(client, "space@uphill.ai")
    client.post(FORGOT, json={"email": "space@uphill.ai"})
    r = client.post(RESET, json={"email": "space@uphill.ai", "code": f" {sent[0][1]} ", "new_password": "newpassword1"})
    assert r.status_code == 200


def test_oauth_only_user_can_set_a_password(client, sent):
    register(client, "oauth@uphill.ai")
    run_sql("UPDATE users SET password_hash = NULL WHERE email = 'oauth@uphill.ai'")
    client.post(FORGOT, json={"email": "oauth@uphill.ai"})
    r = client.post(RESET, json={"email": "oauth@uphill.ai", "code": sent[0][1], "new_password": "firstpass1"})
    assert r.status_code == 200
    assert r.json()["user"]["has_password"] is True
    login = client.post("/api/auth/login", json={"email": "oauth@uphill.ai", "password": "firstpass1"})
    assert login.status_code == 200


def test_reset_for_unknown_email_is_generic(client):
    r = client.post(RESET, json={"email": "ghost@uphill.ai", "code": "123456", "new_password": "newpassword1"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid or expired code."
```

- [ ] **Step 2: Run to see them fail**

Run: `cd backend && pytest tests/integration/test_password_reset.py -q`
Expected: FAIL. The `sent` fixture can't patch `main.send_password_reset_code` (attribute missing), and the routes 404/405.

- [ ] **Step 3: Add the data access functions**

In `backend/db.py`, add `import hmac` to the import block (between `import hashlib` and `import json`). After `delete_session`, add:

```python
# ─── Password reset codes ────────────────────────────────────────────────────


def create_password_reset_code(user_id: int, code_hash: str, ttl_minutes: int = 15) -> bool:
    """Stores a new reset code and retires the user's earlier unused ones.

    Returns False and stores nothing when the user is over the rate limit
    (1 code per 60 s, 5 per hour)."""
    with engine.connect() as conn:
        recent = conn.execute(
            text("""
            SELECT COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '60 seconds') AS last_minute,
                   COUNT(*) AS last_hour
            FROM password_reset_codes
            WHERE user_id = :uid AND created_at > NOW() - INTERVAL '1 hour'
        """),
            {"uid": user_id},
        ).fetchone()
        if recent.last_minute >= 1 or recent.last_hour >= 5:
            return False
        conn.execute(
            text("UPDATE password_reset_codes SET used_at = NOW() WHERE user_id = :uid AND used_at IS NULL"),
            {"uid": user_id},
        )
        conn.execute(
            text("""
            INSERT INTO password_reset_codes (user_id, code_hash, expires_at)
            VALUES (:uid, :h, NOW() + make_interval(mins => :ttl))
        """),
            {"uid": user_id, "h": code_hash, "ttl": ttl_minutes},
        )
        conn.commit()
    return True


def consume_password_reset_code(user_id: int, code_hash: str, new_password_hash: str) -> bool:
    """Checks code_hash against the user's newest live code.

    A miss counts an attempt (the 5th kills the code). A hit sets the password,
    retires the code and deletes every session, all in one transaction."""
    with engine.begin() as conn:
        row = conn.execute(
            text("""
            SELECT id, code_hash FROM password_reset_codes
            WHERE user_id = :uid AND used_at IS NULL AND expires_at > NOW() AND attempts < 5
            ORDER BY created_at DESC LIMIT 1
            FOR UPDATE
        """),
            {"uid": user_id},
        ).fetchone()
        if not row:
            return False
        if not hmac.compare_digest(row.code_hash, code_hash):
            conn.execute(
                text("UPDATE password_reset_codes SET attempts = attempts + 1 WHERE id = :id"), {"id": row.id}
            )
            return False
        conn.execute(
            text("UPDATE users SET password_hash = :ph WHERE id = :uid"), {"ph": new_password_hash, "uid": user_id}
        )
        conn.execute(text("UPDATE password_reset_codes SET used_at = NOW() WHERE id = :id"), {"id": row.id})
        conn.execute(text("DELETE FROM sessions WHERE user_id = :uid"), {"uid": user_id})
    return True
```

- [ ] **Step 4: Add the routes**

In `backend/main.py`:

1. Add `consume_password_reset_code,` and `create_password_reset_code,` to the alphabetically sorted `from db import (...)` block.
2. Change line ~115 to `from services.auth_service import generate_reset_code, hash_password, hash_reset_code, verify_password`.
3. Add `from services.email_service import send_password_reset_code` beside the other `from services...` imports.
4. After `class SetPasswordRequest`, add:

```python
class ForgotPasswordRequest(BaseModel):
    email: str
    lang: str = "en"


class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str
```

5. After `auth_set_password`, add:

```python
FORGOT_PASSWORD_MESSAGE = "If an account exists for this email, we sent a code."
INVALID_RESET_CODE = "Invalid or expired code."


@app.post("/api/auth/forgot-password")
async def auth_forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """Emails a 6-digit reset code. Same answer whether or not the account exists."""
    user = get_user_by_email(request.email)
    if user:
        code = generate_reset_code()
        if create_password_reset_code(user["id"], hash_reset_code(code)):
            # Background, so response time doesn't reveal the account and slow SMTP never blocks.
            background_tasks.add_task(send_password_reset_code, user["email"], code, request.lang)
    return {"message": FORGOT_PASSWORD_MESSAGE}


@app.post("/api/auth/reset-password")
async def auth_reset_password(request: ResetPasswordRequest):
    """Sets a new password from an emailed code, signs out every device, and logs in."""
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    pw_hash = hash_password(request.new_password)
    user = get_user_by_email(request.email)
    if not user or not consume_password_reset_code(user["id"], hash_reset_code(request.code.strip()), pw_hash):
        raise HTTPException(status_code=400, detail=INVALID_RESET_CODE)
    session = create_session(user["id"])
    return {
        "session_token": session["session_token"],
        "expires_at": session["expires_at"],
        "user": format_user_response(get_user_by_email(request.email)),
    }
```

- [ ] **Step 5: Run the integration tests**

Run: `cd backend && pytest tests/integration/test_password_reset.py tests/integration/test_auth_flow.py -q`
Expected: all pass.

- [ ] **Step 6: Run the full backend unit suite and lint**

```bash
cd backend && pytest tests/unit -q && ruff check . && ruff format --check db.py main.py tests/integration/test_password_reset.py
```
Expected: pass, no lint errors.

- [ ] **Step 7: Security review**

Dispatch the `security-reviewer` agent on the diff of `backend/main.py`, `backend/db.py`, `backend/services/auth_service.py` and `backend/services/email_service.py` (it's an auth/session change). Fix any confirmed finding, then re-run Step 5.

- [ ] **Step 8: Commit**

```bash
git add backend/db.py backend/main.py backend/tests/integration/test_password_reset.py
git commit -m "feat(auth): forgot-password and reset-password endpoints"
```

---

### Task 4: Web — forgot-password form in the auth modal

**Files:**
- Create: `frontend/src/components/ForgotPasswordForm.tsx`
- Create: `frontend/src/components/ForgotPasswordForm.test.tsx`
- Modify: `frontend/src/app/translations.ts` (`en` block near `auth_sign_in` line 25; `vi` block near line 568)
- Modify: `frontend/src/hooks/useAppAuth.ts`
- Modify: `frontend/src/views/AuthModal.tsx`

**Interfaces:**
- Consumes: the Task 3 routes.
- Produces:
  - `ForgotPasswordForm` props `{ lang: "en" | "vi"; initialEmail: string; onRequestCode: (email: string) => Promise<void>; onReset: (email: string, code: string, newPassword: string) => Promise<void>; onBack: () => void }`
  - `useAppAuth()` additionally returns `requestPasswordReset(email)`, `resetPassword(email, code, newPassword)`; `authTab` widens to `"login" | "register" | "forgot"`.

- [ ] **Step 1: Add translation keys**

In `frontend/src/app/translations.ts`, in the `en` block after `auth_sign_in`:

```ts
    auth_forgot_link: "Forgot password?",
    auth_forgot_title: "Reset password",
    auth_forgot_intro: "Enter your account email and we'll send you a 6-digit code.",
    auth_send_code: "Send code",
    auth_code_sent: "If an account exists for this email, we sent a code. It expires in 15 minutes.",
    auth_code_label: "6-digit code",
    auth_new_password: "New password (8+ characters)",
    auth_reset_submit: "Reset and sign in",
    auth_resend_code: "Resend code",
    auth_resend_in: "Resend code in {s}s",
    auth_back_to_sign_in: "Back to sign in",
    auth_send_failed: "Couldn't send the code. Check your connection and try again.",
    auth_reset_invalid: "That code is wrong or has expired. Request a new one.",
```

In the `vi` block after `auth_sign_in`:

```ts
    auth_forgot_link: "Quên mật khẩu?",
    auth_forgot_title: "Đặt lại mật khẩu",
    auth_forgot_intro: "Nhập email tài khoản, chúng tôi sẽ gửi cho bạn mã 6 chữ số.",
    auth_send_code: "Gửi mã",
    auth_code_sent: "Nếu email này có tài khoản, chúng tôi đã gửi mã. Mã hết hạn sau 15 phút.",
    auth_code_label: "Mã 6 chữ số",
    auth_new_password: "Mật khẩu mới (từ 8 ký tự)",
    auth_reset_submit: "Đặt lại và đăng nhập",
    auth_resend_code: "Gửi lại mã",
    auth_resend_in: "Gửi lại mã sau {s} giây",
    auth_back_to_sign_in: "Quay lại đăng nhập",
    auth_send_failed: "Không gửi được mã. Hãy kiểm tra kết nối rồi thử lại.",
    auth_reset_invalid: "Mã không đúng hoặc đã hết hạn. Hãy yêu cầu mã mới.",
```

Then invoke the `uphill-ai-vietnamese-copy` skill on these VI strings and apply its fixes. Use the same final VI wording in Task 5's `Localizable.xcstrings`.

- [ ] **Step 2: Write the failing component test**

Create `frontend/src/components/ForgotPasswordForm.test.tsx`:

```tsx
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ForgotPasswordForm from "./ForgotPasswordForm";

const setup = (over: Partial<React.ComponentProps<typeof ForgotPasswordForm>> = {}) => {
  const props = {
    lang: "en" as const,
    initialEmail: "",
    onRequestCode: vi.fn().mockResolvedValue(undefined),
    onReset: vi.fn().mockResolvedValue(undefined),
    onBack: vi.fn(),
    ...over,
  };
  render(<ForgotPasswordForm {...props} />);
  return props;
};

describe("ForgotPasswordForm", () => {
  it("sends a code for the trimmed email and moves to the code step", async () => {
    const props = setup({ initialEmail: "  ada@uphill.ai " });
    fireEvent.click(screen.getByRole("button", { name: "Send code" }));
    await waitFor(() => expect(props.onRequestCode).toHaveBeenCalledWith("ada@uphill.ai"));
    expect(await screen.findByLabelText("6-digit code")).toBeDefined();
    expect(screen.getByText(/we sent a code/)).toBeDefined();
    expect((screen.getByRole("button", { name: /Resend code in/ }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("resets with email, trimmed code and new password", async () => {
    const props = setup({ initialEmail: "ada@uphill.ai" });
    fireEvent.click(screen.getByRole("button", { name: "Send code" }));
    fireEvent.change(await screen.findByLabelText("6-digit code"), { target: { value: " 012345 " } });
    fireEvent.change(screen.getByLabelText("New password (8+ characters)"), { target: { value: "brandnewpass" } });
    fireEvent.click(screen.getByRole("button", { name: "Reset and sign in" }));
    await waitFor(() => expect(props.onReset).toHaveBeenCalledWith("ada@uphill.ai", "012345", "brandnewpass"));
  });

  it("shows a translated error when the code is rejected", async () => {
    setup({ initialEmail: "ada@uphill.ai", onReset: vi.fn().mockRejectedValue(new Error("Invalid or expired code.")) });
    fireEvent.click(screen.getByRole("button", { name: "Send code" }));
    fireEvent.change(await screen.findByLabelText("6-digit code"), { target: { value: "000000" } });
    fireEvent.change(screen.getByLabelText("New password (8+ characters)"), { target: { value: "brandnewpass" } });
    fireEvent.click(screen.getByRole("button", { name: "Reset and sign in" }));
    expect(await screen.findByText("That code is wrong or has expired. Request a new one.")).toBeDefined();
  });

  it("shows a send error and stays on the email step", async () => {
    setup({ initialEmail: "ada@uphill.ai", onRequestCode: vi.fn().mockRejectedValue(new Error("offline")) });
    fireEvent.click(screen.getByRole("button", { name: "Send code" }));
    expect(await screen.findByText("Couldn't send the code. Check your connection and try again.")).toBeDefined();
    expect(screen.queryByLabelText("6-digit code")).toBeNull();
  });

  it("renders Vietnamese copy and goes back", () => {
    const props = setup({ lang: "vi" });
    expect(screen.getByRole("button", { name: "Gửi mã" })).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Quay lại đăng nhập" }));
    expect(props.onBack).toHaveBeenCalled();
  });
});
```

If Step 1's VI review changed "Gửi mã" or "Quay lại đăng nhập", use the final strings here.

- [ ] **Step 3: Run to see it fail**

Run: `cd frontend && npx vitest run src/components/ForgotPasswordForm.test.tsx`
Expected: FAIL, cannot resolve `./ForgotPasswordForm`.

- [ ] **Step 4: Write the component**

Create `frontend/src/components/ForgotPasswordForm.tsx`:

```tsx
import React, { useEffect, useState } from "react";
import { translations } from "../app/translations";

type Props = {
  lang: "en" | "vi";
  initialEmail: string;
  onRequestCode: (email: string) => Promise<void>;
  onReset: (email: string, code: string, newPassword: string) => Promise<void>;
  onBack: () => void;
};

const RESEND_SECONDS = 60;
// Same look as the AuthModal fields.
const inputStyle: React.CSSProperties = { borderRadius: "8px", width: "100%", height: "36px", margin: 0, padding: "0 10px", fontSize: "13px", background: "transparent", border: "1px solid var(--border-color)", color: "var(--text-primary)", boxSizing: "border-box" };
const labelStyle: React.CSSProperties = { display: "block", fontSize: "11.5px", fontWeight: 600, color: "var(--text-muted)", marginBottom: "5px" };
const linkStyle: React.CSSProperties = { background: "none", border: "none", color: "var(--accent-primary)", fontSize: "12.5px", fontWeight: 600, cursor: "pointer", minHeight: "44px", padding: 0 };

export default function ForgotPasswordForm({ lang, initialEmail, onRequestCode, onReset, onBack }: Props) {
  const t = (key: keyof typeof translations.en) => translations[lang]?.[key] || translations.en[key];
  const [step, setStep] = useState<"email" | "code">("email");
  const [email, setEmail] = useState(initialEmail);
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [resendIn, setResendIn] = useState(0);

  useEffect(() => {
    if (resendIn <= 0) return;
    const id = setTimeout(() => setResendIn((s) => s - 1), 1000);
    return () => clearTimeout(id);
  }, [resendIn]);

  const sendCode = async () => {
    setBusy(true);
    setError("");
    try {
      await onRequestCode(email.trim());
      setStep("code");
      setResendIn(RESEND_SECONDS);
    } catch {
      setError(t("auth_send_failed"));
    } finally {
      setBusy(false);
    }
  };

  const reset = async () => {
    setBusy(true);
    setError("");
    try {
      await onReset(email.trim(), code.trim(), newPassword);
    } catch {
      setError(t("auth_reset_invalid"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); if (step === "email") sendCode(); else reset(); }}
      style={{ display: "flex", flexDirection: "column", gap: "12px" }}
    >
      <div style={{ fontSize: "15px", fontWeight: 700 }}>{t("auth_forgot_title")}</div>
      <p style={{ margin: 0, fontSize: "12.5px", color: "var(--text-muted)" }}>
        {step === "email" ? t("auth_forgot_intro") : t("auth_code_sent")}
      </p>
      {error && <div role="alert" style={{ color: "#ef4444", fontSize: "12.5px" }}>{error}</div>}

      <div>
        <label htmlFor="forgot-email" style={labelStyle}>Email</label>
        <input id="forgot-email" type="email" style={inputStyle} className="chat-input" value={email}
          onChange={(e) => setEmail(e.target.value)} required readOnly={step === "code"} autoComplete="username" />
      </div>

      {step === "email" ? (
        <button type="submit" className="btn btn-primary" style={{ width: "100%", height: "40px", fontSize: "13.5px" }}
          disabled={busy || !email.trim()}>
          {t("auth_send_code")}
        </button>
      ) : (
        <>
          <div>
            <label htmlFor="forgot-code" style={labelStyle}>{t("auth_code_label")}</label>
            <input id="forgot-code" style={inputStyle} className="chat-input" value={code}
              onChange={(e) => setCode(e.target.value)} inputMode="numeric" autoComplete="one-time-code"
              maxLength={8} required />
          </div>
          <div>
            <label htmlFor="forgot-new-password" style={labelStyle}>{t("auth_new_password")}</label>
            <input id="forgot-new-password" type="password" style={inputStyle} className="chat-input"
              value={newPassword} onChange={(e) => setNewPassword(e.target.value)} minLength={8}
              autoComplete="new-password" required />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: "100%", height: "40px", fontSize: "13.5px" }}
            disabled={busy || code.trim().length !== 6 || newPassword.length < 8}>
            {t("auth_reset_submit")}
          </button>
          <button type="button" style={linkStyle} onClick={sendCode} disabled={busy || resendIn > 0}>
            {resendIn > 0 ? t("auth_resend_in").replace("{s}", String(resendIn)) : t("auth_resend_code")}
          </button>
        </>
      )}

      <button type="button" style={linkStyle} onClick={onBack}>{t("auth_back_to_sign_in")}</button>
    </form>
  );
}
```

- [ ] **Step 5: Run the component tests**

Run: `cd frontend && npx vitest run src/components/ForgotPasswordForm.test.tsx`
Expected: 5 passed.

- [ ] **Step 6: Wire the hook**

In `frontend/src/hooks/useAppAuth.ts`:

1. Add `lang` to the `ctx` destructure: `const { lang, setUser, setAuthModalOpen, ... } = ctx;`
2. Widen the tab state: `const [authTab, setAuthTab] = useState<"login" | "register" | "forgot">("login");`
3. After `handleEmailLogin`, add:

```ts
  const requestPasswordReset = async (email: string) => {
    const response = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, lang }),
    });
    if (!response.ok) throw new Error("Could not send the code.");
  };

  const resetPassword = async (email: string, code: string, newPassword: string) => {
    const response = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code, new_password: newPassword }),
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || "Reset failed.");
    }
    const data = await response.json();
    localStorage.setItem("uphill_session_token", data.session_token);
    setUser(data.user);
    setAuthTab("login");
    setAuthModalOpen(false);
    fetchRecentPlansWithToken(data.session_token);
    fetchActivePlanWithToken(data.session_token);
  };
```

4. Add `requestPasswordReset, resetPassword,` to the hook's returned object.

- [ ] **Step 7: Wire the modal**

In `frontend/src/views/AuthModal.tsx`:

1. Add `import ForgotPasswordForm from "../components/ForgotPasswordForm";` after the `useAppAuth` import.
2. Add `requestPasswordReset, resetPassword` to the `useAppAuth()` destructure.
3. Wrap the whole `{/* Tab switcher */}` `<div>…</div>` block in `{authTab !== "forgot" && ( … )}`.
4. Change `{authTab === "login" ? (` to:

```tsx
          {authTab === "forgot" ? (
            <ForgotPasswordForm
              lang={lang}
              initialEmail={emailInput}
              onRequestCode={requestPasswordReset}
              onReset={resetPassword}
              onBack={() => { setAuthTab("login"); setAuthErrorMsg(""); }}
            />
          ) : authTab === "login" ? (
```

5. In the login form, directly after the password field's closing `</div>` and before the Sign In submit button, add:

```tsx
              <button
                type="button"
                onClick={() => { setAuthTab("forgot"); setAuthErrorMsg(""); }}
                style={{ alignSelf: "flex-end", background: "none", border: "none", color: "var(--accent-primary)", fontSize: "12px", fontWeight: 600, cursor: "pointer", minHeight: "44px", padding: 0, marginTop: "-8px" }}
              >
                {t("auth_forgot_link")}
              </button>
```

- [ ] **Step 8: Type-check, lint, full vitest**

```bash
cd frontend && npx tsc --noEmit && npm run lint && npx vitest run
```
Expected: no type errors, no new lint errors, all tests pass.

- [ ] **Step 9: Screenshot evidence**

Follow the `ui-screenshot-evidence` skill. Run the local backend (with `SMTP_HOST` unset, so the backend log shows `email skipped`) and the frontend, open the auth modal, and capture: (a) the login form with the "Forgot password?" link, (b) the email step, (c) the code step after "Send code". Codes are never logged, so to finish a reset locally, overwrite the live code's hash in the local dev DB: `UPDATE password_reset_codes SET code_hash = encode(sha256('123456'), 'hex') WHERE used_at IS NULL;`, then reset with `123456` and capture (d) the logged-in state. Do this in the local dev DB only. Repeat (b) with the language set to Vietnamese.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/components/ForgotPasswordForm.tsx frontend/src/components/ForgotPasswordForm.test.tsx frontend/src/app/translations.ts frontend/src/hooks/useAppAuth.ts frontend/src/views/AuthModal.tsx
git commit -m "feat(web): forgot password flow in the auth modal"
```

---

### Task 5: iOS — forgot-password sheet

**Files:**
- Modify: `ios-native/UphillAI/Core/Auth/AuthService.swift`
- Modify: `ios-native/UphillAITests/Support/FakeAuthService.swift`
- Create: `ios-native/UphillAI/Features/Auth/ForgotPasswordViewModel.swift`
- Create: `ios-native/UphillAI/Features/Auth/ForgotPasswordView.swift`
- Modify: `ios-native/UphillAI/Features/Auth/SignInViewModel.swift`
- Modify: `ios-native/UphillAI/Features/Auth/SignInView.swift`
- Modify: `ios-native/UphillAI/Resources/Localizable.xcstrings`
- Test: `ios-native/UphillAITests/Auth/AuthServiceTests.swift`, `ios-native/UphillAITests/Auth/ForgotPasswordViewModelTests.swift`

**Interfaces:**
- Consumes: the Task 3 routes. The API client encodes bodies as snake_case (`identityToken` → `identity_token`), so `newPassword` is sent as `new_password`.
- Produces: on `AuthServicing`, `requestPasswordReset(email: String, lang: String) async throws` and `resetPassword(email: String, code: String, newPassword: String) async throws -> AuthResponse`; `ForgotPasswordViewModel`; `SignInViewModel.makeForgotPasswordModel() -> ForgotPasswordViewModel`.

- [ ] **Step 1: Write the failing AuthService tests**

Append inside `struct AuthServiceTests` in `ios-native/UphillAITests/Auth/AuthServiceTests.swift`:

```swift
    @Test func forgotPasswordPostsEmailAndLangWithoutToken() async throws {
        let service = AuthService(client: makeStubClient(token: "stale") { request in
            #expect(request.url?.path() == "/api/auth/forgot-password")
            #expect(request.httpMethod == "POST")
            #expect(request.value(forHTTPHeaderField: "Authorization") == nil)
            #expect(try body(request) == ["email": "a@b.c", "lang": "vi"])
            return (200, Data(#"{"message":"If an account exists for this email, we sent a code."}"#.utf8))
        })
        try await service.requestPasswordReset(email: "a@b.c", lang: "vi")
    }

    @Test func resetPasswordPostsCodeAndNewPassword() async throws {
        let fixture = try Fixture.data("auth_login.json")
        let service = AuthService(client: makeStubClient(token: "stale") { request in
            #expect(request.url?.path() == "/api/auth/reset-password")
            #expect(request.value(forHTTPHeaderField: "Authorization") == nil)
            #expect(try body(request) == ["email": "a@b.c", "code": "012345", "new_password": "secret123"])
            return (200, fixture)
        })
        let response = try await service.resetPassword(email: "a@b.c", code: "012345", newPassword: "secret123")
        #expect(response.sessionToken == "fixture-session-token")
    }
```

- [ ] **Step 2: Add the service methods and the fake**

In `ios-native/UphillAI/Core/Auth/AuthService.swift`, add to `protocol AuthServicing` after `register`:

```swift
    func requestPasswordReset(email: String, lang: String) async throws
    func resetPassword(email: String, code: String, newPassword: String) async throws -> AuthResponse
```

In `struct AuthService`, add the body types beside the others:

```swift
    private struct ForgotBody: Encodable { let email: String; let lang: String }
    private struct ResetBody: Encodable { let email: String; let code: String; let newPassword: String }
```

and the methods after `register`:

```swift
    /// The server answers the same whether or not the account exists.
    func requestPasswordReset(email: String, lang: String) async throws {
        let _: EmptyResponse = try await client.send(.send(.post, "/api/auth/forgot-password",
                                                           body: ForgotBody(email: email, lang: lang), requiresAuth: false))
    }

    func resetPassword(email: String, code: String, newPassword: String) async throws -> AuthResponse {
        try await client.send(.send(.post, "/api/auth/reset-password",
                                    body: ResetBody(email: email, code: code, newPassword: newPassword), requiresAuth: false))
    }
```

In `ios-native/UphillAITests/Support/FakeAuthService.swift`, add after `register`:

```swift
    func requestPasswordReset(email: String, lang: String) async throws {
        calls.withLock { $0.append("forgot \(email) \(lang)") }
        if case .failure(let error) = result { throw error }
    }
    func resetPassword(email: String, code: String, newPassword: String) async throws -> AuthResponse {
        try record("reset \(email) \(code)")
    }
```

- [ ] **Step 3: Write the failing view model tests**

Create `ios-native/UphillAITests/Auth/ForgotPasswordViewModelTests.swift`:

```swift
import Foundation
import Testing
@testable import UphillAI

@MainActor
struct ForgotPasswordViewModelTests {
    private func success() throws -> AuthResponse { try Fixture.decode(AuthResponse.self, "auth_login.json") }
    private let start = Date(timeIntervalSince1970: 1_000_000)

    private func make(_ auth: FakeAuthService, session: SessionStore? = nil) -> ForgotPasswordViewModel {
        ForgotPasswordViewModel(auth: auth, session: session ?? SessionStore(tokenStore: InMemoryTokenStore()),
                                email: "  ana@example.com ", now: { self.start })
    }

    @Test func sendCodeTrimsEmailAndMovesToCodeStep() async throws {
        let auth = FakeAuthService(.success(try success()))
        let model = make(auth)
        await model.sendCode()
        #expect(auth.calls.withLock { $0 } == ["forgot ana@example.com \(AppLanguage.code)"])
        #expect(model.step == .code)
        #expect(model.canResend(at: start.addingTimeInterval(59)) == false)
        #expect(model.canResend(at: start.addingTimeInterval(60)) == true)
    }

    @Test func sendCodeFailureStaysOnEmailStep() async {
        let model = make(FakeAuthService(.failure(.http(status: 500, message: nil, code: nil))))
        await model.sendCode()
        #expect(model.step == .email)
        #expect(model.errorMessage != nil)
    }

    @Test func resetTrimsCodeAndSignsIn() async throws {
        let auth = FakeAuthService(.success(try success()))
        let session = SessionStore(tokenStore: InMemoryTokenStore())
        let model = make(auth, session: session)
        model.step = .code
        model.code = " 012345 "
        model.newPassword = "secret123"
        await model.reset()
        #expect(auth.calls.withLock { $0 } == ["reset ana@example.com 012345"])
        #expect(session.user != nil)
        #expect(model.errorMessage == nil)
    }

    @Test func rejectedCodeShowsInvalidMessage() async {
        let model = make(FakeAuthService(.failure(.http(status: 400, message: "Invalid or expired code.", code: nil))))
        model.step = .code
        model.code = "000000"
        model.newPassword = "secret123"
        await model.reset()
        #expect(model.errorMessage == L("That code is wrong or has expired. Request a new one."))
    }

    @Test func canResetNeedsSixDigitCodeAndEightCharPassword() {
        let model = make(FakeAuthService(.failure(.unauthorized)))
        model.code = "12345"
        model.newPassword = "longenough"
        #expect(model.canReset == false)
        model.code = "123456"
        model.newPassword = "short"
        #expect(model.canReset == false)
        model.newPassword = "longenough"
        #expect(model.canReset == true)
    }
}
```

- [ ] **Step 4: Run to see the tests fail**

Run: `cd ios-native && xcodegen generate && scripts/test.sh`
Expected: build FAILS, `cannot find 'ForgotPasswordViewModel' in scope`.

- [ ] **Step 5: Write the view model**

Create `ios-native/UphillAI/Features/Auth/ForgotPasswordViewModel.swift`:

```swift
import Foundation
import Observation

@Observable
@MainActor
final class ForgotPasswordViewModel {
    enum Step { case email, code }

    var step: Step = .email
    var email: String
    var code = ""
    var newPassword = ""
    private(set) var isBusy = false
    private(set) var errorMessage: String?
    private(set) var resendAvailableAt: Date?

    private let auth: any AuthServicing
    private let session: SessionStore
    private let now: () -> Date

    init(auth: any AuthServicing, session: SessionStore, email: String = "", now: @escaping () -> Date = Date.init) {
        self.auth = auth
        self.session = session
        self.email = email
        self.now = now
    }

    private var trimmedEmail: String { email.trimmingCharacters(in: .whitespacesAndNewlines) }
    private var trimmedCode: String { code.trimmingCharacters(in: .whitespacesAndNewlines) }

    var canSendCode: Bool { !isBusy && trimmedEmail.contains("@") }
    var canReset: Bool { !isBusy && trimmedCode.count == 6 && newPassword.count >= 8 }

    func canResend(at date: Date) -> Bool {
        !isBusy && (resendAvailableAt.map { date >= $0 } ?? true)
    }

    func sendCode() async {
        isBusy = true
        errorMessage = nil
        defer { isBusy = false }
        do {
            try await auth.requestPasswordReset(email: trimmedEmail, lang: AppLanguage.code)
            step = .code
            resendAvailableAt = now().addingTimeInterval(60)
        } catch {
            errorMessage = L("Couldn't send the code. Check your connection and try again.")
        }
    }

    func reset() async {
        isBusy = true
        errorMessage = nil
        defer { isBusy = false }
        do {
            session.didSignIn(try await auth.resetPassword(email: trimmedEmail, code: trimmedCode, newPassword: newPassword))
        } catch APIError.http(status: 400, message: _, code: _) {
            errorMessage = L("That code is wrong or has expired. Request a new one.")
        } catch let error as APIError {
            errorMessage = error.userMessage
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
```

Note: the server's other 400 (password too short) can't happen because `canReset` requires 8+ characters.

- [ ] **Step 6: Run the tests**

Run: `cd ios-native && xcodegen generate && scripts/test.sh`
Expected: all tests pass, including the 2 new AuthService tests and 5 view model tests.

- [ ] **Step 7: Build the sheet and hook it into sign-in**

In `ios-native/UphillAI/Features/Auth/SignInView.swift`, change `private extension View {` (the `inputBox()` extension at the bottom) to `extension View {` so the new sheet can use it.

In `ios-native/UphillAI/Features/Auth/SignInViewModel.swift`, add after `show(_:)`:

```swift
    func makeForgotPasswordModel() -> ForgotPasswordViewModel {
        ForgotPasswordViewModel(auth: auth, session: session, email: trimmedEmail)
    }
```

Create `ios-native/UphillAI/Features/Auth/ForgotPasswordView.swift`:

```swift
import SwiftUI

struct ForgotPasswordView: View {
    @Bindable var model: ForgotPasswordViewModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text(model.step == .email
                         ? L("Enter your account email and we'll send you a 6-digit code.")
                         : L("If an account exists for this email, we sent a code. It expires in 15 minutes."))
                        .font(UH.TextStyle.body)
                        .foregroundStyle(UH.Palette.secondary)

                    if let error = model.errorMessage {
                        Text(error)
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.danger)
                            .accessibilityIdentifier("forgot.error")
                    }

                    TextField("Email", text: $model.email)
                        .textContentType(.username)
                        .keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .disabled(model.step == .code)
                        .inputBox()
                        .accessibilityIdentifier("forgot.email")

                    if model.step == .email {
                        Button(L("Send code")) { Task { await model.sendCode() } }
                            .buttonStyle(.uhPrimary)
                            .disabled(!model.canSendCode)
                            .accessibilityIdentifier("forgot.send")
                    } else {
                        TextField(L("6-digit code"), text: $model.code)
                            .textContentType(.oneTimeCode)
                            .keyboardType(.numberPad)
                            .inputBox()
                            .accessibilityIdentifier("forgot.code")
                        SecureField(L("New password (8+ characters)"), text: $model.newPassword)
                            .textContentType(.newPassword)
                            .inputBox()
                            .accessibilityIdentifier("forgot.newPassword")
                        Button(L("Reset and sign in")) { Task { await model.reset() } }
                            .buttonStyle(.uhPrimary)
                            .disabled(!model.canReset)
                            .accessibilityIdentifier("forgot.reset")
                        TimelineView(.periodic(from: .now, by: 1)) { context in
                            Button(L("Resend code")) { Task { await model.sendCode() } }
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.accentInk)
                                .frame(minHeight: 44)
                                .disabled(!model.canResend(at: context.date))
                        }
                    }
                }
                .padding(UH.Space.medium)
                .disabled(model.isBusy)
            }
            .background(UH.Palette.surface.ignoresSafeArea())
            .navigationTitle(L("Reset password"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button(L("Cancel")) { dismiss() } }
            }
        }
    }
}
```

In `SignInView`, add state `@State private var forgotModel: ForgotPasswordViewModel?` beside `@FocusState`, add this sheet modifier after `.sensoryFeedback(...)` in `scrollContent`:

```swift
        .sheet(item: $forgotModel) { ForgotPasswordView(model: $0) }
```

and in `emailForm`, directly after the `SecureField(...)` chain ending `.accessibilityIdentifier("signin.password")`:

```swift
            if model.mode == .signIn {
                Button(L("Forgot password?")) { forgotModel = model.makeForgotPasswordModel() }
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.accentInk)
                    .frame(maxWidth: .infinity, minHeight: 44, alignment: .trailing)
                    .accessibilityIdentifier("signin.forgot")
            }
```

`.sheet(item:)` needs `Identifiable`: append to `ForgotPasswordViewModel.swift`:

```swift
extension ForgotPasswordViewModel: Identifiable {}
```

(`@Observable` classes get `ObjectIdentifier`-based `id` from `Identifiable`'s default for `AnyObject`.)

When the reset succeeds, `session.didSignIn` swaps the root view away from `SignInView`, which dismisses the sheet with it.

- [ ] **Step 8: Add the Vietnamese strings**

In `ios-native/UphillAI/Resources/Localizable.xcstrings`, add an entry per new key in the same shape as `"Sign in"`, keeping keys sorted. Use the final VI wording from Task 4 Step 1:

| Key | vi |
|---|---|
| `Forgot password?` | Quên mật khẩu? |
| `Reset password` | Đặt lại mật khẩu |
| `Enter your account email and we'll send you a 6-digit code.` | Nhập email tài khoản, chúng tôi sẽ gửi cho bạn mã 6 chữ số. |
| `Send code` | Gửi mã |
| `If an account exists for this email, we sent a code. It expires in 15 minutes.` | Nếu email này có tài khoản, chúng tôi đã gửi mã. Mã hết hạn sau 15 phút. |
| `6-digit code` | Mã 6 chữ số |
| `New password (8+ characters)` | Mật khẩu mới (từ 8 ký tự) |
| `Reset and sign in` | Đặt lại và đăng nhập |
| `Resend code` | Gửi lại mã |
| `Couldn't send the code. Check your connection and try again.` | Không gửi được mã. Hãy kiểm tra kết nối rồi thử lại. |
| `That code is wrong or has expired. Request a new one.` | Mã không đúng hoặc đã hết hạn. Hãy yêu cầu mã mới. |

Skip `Cancel` if it already exists (`grep -n '"Cancel"' ios-native/UphillAI/Resources/Localizable.xcstrings`); otherwise add it as `Hủy`. Validate the JSON: `python3 -m json.tool ios-native/UphillAI/Resources/Localizable.xcstrings > /dev/null`.

- [ ] **Step 9: Run tests and screenshot**

Run: `cd ios-native && xcodegen generate && scripts/test.sh`
Expected: all pass.

Then attach the simulator panel, build and launch the app against the local backend, tap "Forgot password?", and capture screenshots of the email step and the code step, in English and Vietnamese.

- [ ] **Step 10: Commit**

```bash
git add ios-native
git commit -m "feat(ios): forgot password sheet"
```

---

### Task 6: Release (owner-assisted)

No code in this task. Each step needs the owner or touches prod, so confirm before each one.

- [ ] **Step 1: Owner sets the prod env.** On the server, the owner adds the five `SMTP_*`/`MAIL_FROM` values (Global Constraints) to `/opt/uphill-ai-backend/backend/.env`, backing up the file first. The password never goes through chat or git.
- [ ] **Step 2: Deploy the backend before merging.** Web goes live on merge to `main` (GitHub Pages), so the routes must already be in prod. Deploy by hand from this worktree per the memory notes (not `deploy_server.sh`, which overwrites the prod `.env`). Run `alembic upgrade head`, confirm `c8e2a4f6d9b1`, set `LANGFUSE_RELEASE`, and diff the `.env` keys against the backup afterwards.
- [ ] **Step 3: Real send.** `curl -X POST https://<prod-api>/api/auth/forgot-password -H 'Content-Type: application/json' -d '{"email":"<owner's own account email>","lang":"vi"}'`. The owner confirms the mail arrives in the inbox (not spam) within a minute, then completes a reset in the web app. Check the backend logs show no `password reset email failed`.
- [ ] **Step 4: PR and merge.** Open the PR with the spec link and the screenshots from Tasks 4–5, then merge to deploy web.
- [ ] **Step 5: iOS build.** Cut the next TestFlight build (`YYYYMMDDNN`) per the native app release process.
