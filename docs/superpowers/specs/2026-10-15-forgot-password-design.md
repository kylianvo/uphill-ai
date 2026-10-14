# Forgot password — design

Date: 2026-10-15
Status: approved in chat, pending spec review

## Goal

A user who forgot their password can get back into their account on web or iOS without contacting support. Success: they request a code by email, enter it with a new password, and land logged in.

## Decisions

| Question | Decision | Why |
|---|---|---|
| How email is sent | SMTP through the existing domain mailbox `viet.vo@uphill-ai.io.vn` (cPanel host `cp02hn.emailserver.net.vn:465`, implicit TLS) | Already covered by the domain's SPF, so it passes `DMARC p=quarantine` with no DNS change; no new vendor. A new `no-reply@` address can't be created. Prod reachability verified 2026-10-15 (`nc` → OPEN). |
| Link or code | 6-digit code | Works the same on web (static GitHub Pages export) and iOS; no deep links or universal links. |
| Clients | Backend + web + iOS in one release | Both clients have email/password login today. |
| OAuth-only users (no `password_hash`) | Send a code; a successful reset gives them a password | Receiving the code proves inbox ownership, the same trust `set-password` relies on. Their OAuth sign-in keeps working. |

## Data

New table `password_reset_codes`, added in both `db.py:init_db()` and a hand-written Alembic migration (see the `db-migration` skill):

| Column | Type | Notes |
|---|---|---|
| `id` | SERIAL PK | |
| `user_id` | INTEGER NOT NULL | `REFERENCES users(id) ON DELETE CASCADE` |
| `code_hash` | TEXT NOT NULL | SHA-256 hex of the 6-digit code; the code is never stored |
| `expires_at` | TIMESTAMPTZ NOT NULL | created + 15 minutes |
| `attempts` | INTEGER NOT NULL DEFAULT 0 | wrong guesses against this code |
| `used_at` | TIMESTAMPTZ NULL | set on success or when superseded |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | used for rate limiting |

Index on `(user_id, created_at)`.

Codes come from `secrets.randbelow(10**6)`, zero-padded to 6 digits.

## Backend

Both routes live in `backend/main.py` beside `/api/auth/login`, with data access in `db.py`.

### `POST /api/auth/forgot-password`

Body: `{email, lang}` (`lang` is `"en" | "vi"`, default `"en"`).

Always returns `200 {"message": "If an account exists for this email, we sent a code."}`.

When a user with that email exists and is under the rate limit:
1. Set `used_at = now()` on the user's earlier unused codes.
2. Insert a new code row.
3. Queue the email with FastAPI `BackgroundTasks`, so response time doesn't show whether the account exists and a slow SMTP server never blocks the request.

Rate limit, counted from `password_reset_codes.created_at`: at most 1 code per user per 60 s and 5 per hour. Requests over the limit get the same 200 and send no email.

### `POST /api/auth/reset-password`

Body: `{email, code, new_password}`.

1. `new_password` shorter than 8 characters → `400 "Password must be at least 8 characters."` (same rule as register).
2. Look up the user's newest code where `used_at IS NULL AND expires_at > now() AND attempts < 5`. Missing user or missing code → `400 "Invalid or expired code."`
3. Compare `sha256(code)` with `code_hash` using `hmac.compare_digest`. On a mismatch, increment `attempts` and return the same 400.
4. On a match, in one transaction: set `password_hash` (via `hash_password`), set `used_at` on the code, and delete all of the user's `sessions` rows.
5. Create a new session and return the same shape as `/api/auth/login`: `{session_token, expires_at, user}`.

### `services/email_service.py`

One function, `send_email(to: str, subject: str, body: str) -> None`, built on `smtplib.SMTP_SSL` + `email.message.EmailMessage` with a 10 s timeout. The body is plain text, EN or VI by `lang`, and contains the code, the 15-minute expiry, and a line saying they can ignore the email if they didn't ask for it.

New settings in `config.py`:

| Var | Prod value |
|---|---|
| `SMTP_HOST` | `cp02hn.emailserver.net.vn` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | `viet.vo@uphill-ai.io.vn` |
| `SMTP_PASSWORD` | set by the owner in the server's `backend/.env`; never committed |
| `MAIL_FROM` | `Uphill AI <viet.vo@uphill-ai.io.vn>` |

If `SMTP_HOST` is empty (local dev, tests), `send_email` logs `email skipped: SMTP not configured` with the recipient and subject, never the code, and returns.

Errors: SMTP exceptions are caught in the background task, logged with `logger.exception`, and counted in a Prometheus counter `password_reset_email_failures_total`. No retry; the user can press "Resend code".

The logs never contain the code or the password.

## Web (`frontend/`)

- A "Forgot password?" link under the password field on the email login form (the form that uses `useAppAuth`; the duplicate login call in `app/app/page.tsx` is checked during planning).
- A panel with two steps:
  1. Email field → `forgot-password` → step 2 with the generic "If an account exists…" message.
  2. Code (6-digit, `inputMode="numeric"`, `autocomplete="one-time-code"`), new password, and a "Resend code" button that stays disabled for 60 s → `reset-password` → hand the response to the existing session-storing path, which logs the user in.
- All strings go through `translations.ts`, in EN and VI, following the `uphill-ai-vietnamese-copy` skill.

## iOS (`ios-native/`)

- `AuthService` gets `requestPasswordReset(email:lang:)` and `resetPassword(email:code:newPassword:) -> AuthResponse`.
- A "Forgot password?" button on the email login screen opens a sheet with the same two steps, using `.textContentType(.oneTimeCode)` for the code field.
- On success it stores the session the same way `login` does.
- Ships in the next TestFlight build (`YYYYMMDDNN`).

## Testing

Backend unit tests, with SMTP mocked:
- an unknown email gets the same 200 and sends nothing
- a second request inside 60 s sends nothing; the 6th in an hour sends nothing
- the code expires after 15 min
- 5 wrong guesses kill the code even when the 6th is correct
- a code can't be reused
- a new request invalidates the previous code
- a successful reset deletes old sessions and returns a working session
- an OAuth-only user (no `password_hash`) can reset and then log in with email + password
- a password under 8 characters is rejected without consuming the code

Web: component test for the two-step panel, plus a screenshot per the `ui-screenshot-evidence` skill.
iOS: `AuthServiceTests` for both new calls, plus a simulator screenshot of the sheet.
Before merge: one real send from the prod backend to the owner's own address, checking that it lands in the inbox, not spam.

## Out of scope

HTML email templates, a "your password was changed" notice, a password strength meter, CAPTCHA, and per-IP rate limiting.
