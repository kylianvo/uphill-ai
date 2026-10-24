"""Device-integration endpoints (COROS today; Garmin when their developer
program reopens to new applicants).

Two facts from the COROS API Reference V2.0.6 shape the webhook handler below:

  * The workout-data receiving endpoint is documented as an "Https service
    interface that accepts workout data and allows duplicate data" -- COROS
    may deliver the same summary more than once, so the handler must be
    idempotent.
  * The service-status-check API is validated with a GET, and passes purely on
    "http status code is 200". `/api/health` already satisfies that and is what
    the form declares; the GET here is a convenience for probing this path.
"""

import html
import json
import logging
import re
import secrets
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal
from urllib.parse import urlencode, urlparse

import httpx
from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, Header, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field, ValidationError

import db
from config import settings
from db import verify_session
from log_utils import get_logger
from services import coros_oauth, coros_push, coros_sync, garmin_ingest, garmin_oauth, recovery_baseline, token_crypto
from services.calendar_rules import resolve_today
from services.matching import runner as matching_runner
from services.matching.quality_scorer import score_workout_quality
from services.mcp_client import McpError
from services.plan_generator import PlanGenerator
from services.providers.base import CanonicalActivity, CanonicalDailyMetric
from services.providers.coros import PROVIDER, CorosDailyMetricsUnavailableError
from services.providers.coros_parsers import CorosParseError
from services.providers.garmin import PROVIDER as GARMIN
from services.week_context import attach_week_context

router = APIRouter(prefix="/integrations", tags=["integrations"])
logger = get_logger(__name__)


class _RedactGarminWebhookToken(logging.Filter):
    """The Garmin webhook URL carries a secret path segment; keep it out of access logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        # uvicorn.access args: (client_addr, method, full_path, http_version, status_code)
        if isinstance(record.args, tuple) and len(record.args) > 2 and "/garmin/webhook/" in str(record.args[2]):
            args = list(record.args)
            args[2] = re.sub(r"(/garmin/webhook/)[^/?]+", r"\1[redacted]", str(args[2]))
            record.args = tuple(args)
        return True


logging.getLogger("uvicorn.access").addFilter(_RedactGarminWebhookToken())


@router.get("/coros/webhook")
async def coros_webhook_probe() -> dict[str, str]:
    """Liveness probe for the push endpoint.

    COROS validates a partner interface with a GET expecting HTTP 200. The form
    declares `/api/health` for that check; this exists so the push path itself
    also answers a probe rather than 404ing.
    """
    return {"status": "ok"}


@router.post("/coros/webhook")
async def coros_webhook(request: Request) -> dict[str, str]:
    """Accept a COROS workout-summary push.

    Stub: acknowledges and discards. Always returns 200 -- including on a
    malformed body -- because a non-2xx would make COROS retry a payload we have
    no way to process yet, and a partner interface that errors under load is
    what their status check is designed to catch.

    Logs only the shape of the payload, never its content: these bodies carry
    real athlete training and health data (see log_utils).
    """
    raw = await request.body()
    keys: list[str] = []
    try:
        parsed: Any = await request.json()
        if isinstance(parsed, dict):
            keys = sorted(parsed.keys())
    except Exception:
        # Body may be form-encoded or malformed; the shape log is best-effort.
        pass

    logger.info(
        "coros webhook received",
        extra={
            "fields": {
                "service": "integrations",
                "provider": "coros",
                "event": "webhook_received",
                "status": "stubbed",
                "bytes": len(raw),
                "top_level_keys": keys,
            }
        },
    )
    return {"message": "ok"}


async def get_current_user(authorization: str | None = Header(None)) -> dict[str, Any]:
    """Local copy of main.py's dependency.

    Deliberately NOT imported from main: main.py imports this router, so
    importing back would be circular. routers/analytics.py solves the same
    problem the same way. Both call db.verify_session, so behaviour cannot drift.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication token missing or invalid.")
    user = verify_session(authorization.split(" ")[1])
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid.")
    return user


# state -> (user_id, pkce_verifier, created_at). In-process and short-lived: an
# unfinished authorization simply has to be restarted after a deploy, which is
# acceptable. created_at (time.monotonic()) backs _prune_pending_auth below --
# without it, a user who starts /coros/connect and never completes the redirect
# (closed tab, denied consent, anything) would leave an entry here forever, since
# nothing else ever removes one. Deployment today is a single uvicorn process
# with no --workers and no --reload (see backend/Dockerfile's CMD), so this dict
# is not split across processes in production; it would need to move to a shared
# store (e.g. the DB) before this could run behind multiple workers or replicas.
_PENDING_AUTH: dict[str, tuple[int, str, float]] = {}
_PENDING_AUTH_TTL_SECONDS = 600  # 10 minutes -- generous for a redirect round trip

# Native (iOS/Android app) flows can't use the state cookie: consent happens in
# a system browser session whose cookie jar is separate from the app's WebView,
# so the cookie set by /connect never reaches /callback. Instead the callback
# parks the code here and hands a one-time completion token to the browser that
# consented, which returns it to the app via uphillai://<provider>/callback; the app then
# presents it on /coros/complete with its own session. An attacker who started
# the flow never sees the token, and the victim's app fails the user_id check.
# state -> (user_id, verifier, code, completion_token, created_at)
NATIVE_CALLBACK_URL = "uphillai://coros/callback"
PROVIDER_NAMES = {"coros": "COROS", "garmin": "Garmin"}
_NATIVE_COMPLETIONS: dict[str, tuple[int, str, str, str, float]] = {}

# The cookie that binds an authorization attempt to the browser that started
# it (see coros_connect / coros_callback below -- RFC 6749 section 10.12
# client CSRF). Scoped to the callback path only so it isn't sent on every
# request to the API.
COROS_OAUTH_STATE_COOKIE = "coros_oauth_state"
COROS_CALLBACK_PATH = "/api/integrations/coros/callback"


def _prune_pending_auth() -> None:
    """Drops expired pending-authorization entries so the dict cannot grow
    without bound across abandoned connect attempts. Called opportunistically
    on every new connect rather than on a timer -- there is no background
    scheduler in this process."""
    cutoff = time.monotonic() - _PENDING_AUTH_TTL_SECONDS
    expired = [s for s, entry in _PENDING_AUTH.items() if entry[2] < cutoff]
    for s in expired:
        _PENDING_AUTH.pop(s, None)
    for s in [s for s, entry in _NATIVE_COMPLETIONS.items() if entry[4] < cutoff]:
        _NATIVE_COMPLETIONS.pop(s, None)


def _pop_pending_auth(state: str | None) -> tuple[int, str, str | None] | None:
    """Consumes a pending authorization exactly once. Returns None for a
    missing, unknown, replayed, or expired state -- an attacker-supplied code
    paired with a state that doesn't resolve to a live pending flow must not
    create a connection, and all of those cases have to look identical to the
    caller."""
    if not state:
        return None
    entry = _PENDING_AUTH.pop(state, None)
    if entry is None:
        return None
    user_id = entry[0]
    verifier = entry[1]
    created_at = entry[2]
    return_url = entry[3] if len(entry) > 3 else None
    if created_at < time.monotonic() - _PENDING_AUTH_TTL_SECONDS:
        return None
    return user_id, verifier, return_url


def _validate_return_url(url: str | None) -> str | None:
    """Validates that a return URL has an origin explicitly permitted by ALLOWED_ORIGINS
    or matches FRONTEND_URL to prevent open redirect vulnerabilities."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return None
        origin = f"{parsed.scheme}://{parsed.netloc}"
        allowed = {a.rstrip("/") for a in settings.ALLOWED_ORIGINS if a}
        if settings.FRONTEND_URL:
            allowed.add(settings.FRONTEND_URL.rstrip("/"))
        if origin in allowed:
            path = parsed.path.rstrip("/")
            return f"{origin}{path}" if path else origin
    except Exception:
        pass
    return None


def _state_cookie(provider: str) -> str:
    return f"{provider}_oauth_state"


def _callback_path(provider: str) -> str:
    return f"/api/integrations/{provider}/callback"


def _error_redirect(return_url: str | None = None, provider: str = PROVIDER) -> RedirectResponse:
    """Every failure path out of a provider's /callback ends here, and the one-shot
    CSRF cookie is always cleared on the way out -- success or failure -- so it
    can never be replayed against a later attempt."""
    base = _validate_return_url(return_url) or settings.FRONTEND_URL
    response = RedirectResponse(url=f"{base.rstrip('/')}/?{provider}=error")
    response.delete_cookie(key=_state_cookie(provider), path=_callback_path(provider))
    return response


@router.get("/coros/connect")
async def coros_connect(
    request: Request,
    response: Response,
    return_url: str | None = None,
    platform: str | None = None,
    user: dict[str, Any] = Depends(get_current_user),
):
    # Both must be set before an athlete is sent to COROS: without
    # TOKEN_ENCRYPTION_KEY, the callback can exchange the code but cannot
    # store the resulting tokens (encrypt_token raises TokenEncryptionUnconfigured),
    # which would otherwise only surface AFTER the athlete has granted consent.
    if not settings.COROS_CLIENT_ID or not settings.TOKEN_ENCRYPTION_KEY:
        raise HTTPException(status_code=503, detail="COROS integration is not configured.")
    return _start_connect(PROVIDER, coros_oauth.build_authorize_url, request, response, return_url, platform, user)


def _start_connect(
    provider: str,
    build_authorize_url: Callable[[str, str], str],
    request: Request,
    response: Response,
    return_url: str | None,
    platform: str | None,
    user: dict[str, Any],
) -> dict[str, str]:
    _prune_pending_auth()
    verifier, challenge = coros_oauth.make_pkce_pair()
    state = secrets.token_urlsafe(32)

    if platform == "native":
        _PENDING_AUTH[state] = (user["id"], verifier, time.monotonic(), None, True)
        return {"authorize_url": build_authorize_url(state, challenge)}

    safe_return_url = _validate_return_url(return_url)
    if not safe_return_url and request.headers.get("referer"):
        safe_return_url = _validate_return_url(request.headers.get("referer"))

    _PENDING_AUTH[state] = (user["id"], verifier, time.monotonic(), safe_return_url)
    # Binds this authorization attempt to the browser that started it (RFC 6749
    # section 10.12, OAuth client CSRF): state alone is unguessable and single-use,
    # so it can't be forged, but without this cookie an attacker could start their
    # own /connect, get back a legitimate authorize URL bound to *their* user_id,
    # and lure a victim into completing COROS consent on it -- binding the
    # victim's COROS account (sleep, HRV, training data) to the attacker's Uphill
    # account. SameSite=Lax is sufficient because /coros/callback is only ever hit
    # by a top-level GET navigation (the redirect back from COROS), which carries
    # a Lax cookie; a cross-site POST or subresource load would not.
    # Secure is set unconditionally rather than gated on an environment flag:
    # COROS_REDIRECT_URI is always https in every environment that actually talks
    # to COROS, and browsers additionally treat http://localhost (this repo's
    # local-dev origin) as a secure context, so an unconditional Secure flag never
    # silently drops the cookie in an environment this app actually runs in.
    response.set_cookie(
        key=_state_cookie(provider),
        value=state,
        max_age=_PENDING_AUTH_TTL_SECONDS,
        path=_callback_path(provider),
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return {"authorize_url": build_authorize_url(state, challenge)}


@router.get("/coros/callback")
async def coros_callback(
    code: str | None = None,
    state: str | None = None,
    state_cookie: str | None = Cookie(default=None, alias=COROS_OAUTH_STATE_COOKIE),
):
    return await _handle_callback(PROVIDER, code, state, state_cookie, _exchange_and_save)


async def _handle_callback(
    provider: str,
    code: str | None,
    state: str | None,
    state_cookie: str | None,
    exchange_and_save: Callable[[str, str, int], Awaitable[bool]],
):
    entry = _PENDING_AUTH.get(state) if state else None
    if entry is not None and len(entry) > 4 and entry[4]:
        pending = _pop_pending_auth(state)
        if not code or not pending:
            return _native_return_page({"result": "error"}, provider)
        user_id, verifier, _ = pending
        token = secrets.token_urlsafe(32)
        _NATIVE_COMPLETIONS[state] = (user_id, verifier, code, token, time.monotonic())
        return _native_return_page({"state": state, "token": token}, provider)

    # Check the CSRF-binding cookie before touching _PENDING_AUTH at all. An
    # attacker who replays or guesses someone else's `state` from a different
    # browser (no cookie, or the wrong one) must not be able to consume -- and
    # thereby invalidate -- the real athlete's still-pending entry; that would
    # let the attacker grief a legitimate connect attempt even if they can't
    # complete it themselves.
    if state_cookie and (not state or not secrets.compare_digest(state_cookie, state)):
        # A cookie was present but didn't match (or `state` was missing from
        # the query string) -- this is the shape a genuine CSRF attempt takes.
        logger.warning(
            "oauth callback state mismatch",
            extra={
                "fields": {
                    "service": "integrations",
                    "provider": provider,
                    "event": "callback_state_mismatch",
                }
            },
        )
        return _error_redirect(provider=provider)

    if not state_cookie:
        logger.warning(
            "oauth callback state cookie absent",
            extra={
                "fields": {
                    "service": "integrations",
                    "provider": provider,
                    "event": "callback_state_cookie_absent",
                }
            },
        )
        if getattr(settings, "COROS_REQUIRE_STATE_COOKIE", True):
            return _error_redirect(provider=provider)

    pending = _pop_pending_auth(state)
    if not code or not pending:
        return _error_redirect(provider=provider)

    user_id, verifier, return_url = pending
    if not await exchange_and_save(code, verifier, user_id):
        return _error_redirect(return_url, provider)
    base = _validate_return_url(return_url) or settings.FRONTEND_URL
    response = RedirectResponse(url=f"{base.rstrip('/')}/?{provider}=connected")
    response.delete_cookie(key=_state_cookie(provider), path=_callback_path(provider))
    return response


class CorosCompleteRequest(BaseModel):
    state: str
    token: str


@router.post("/coros/complete")
async def coros_complete(
    body: CorosCompleteRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    return await _complete_native(PROVIDER, body, user, _exchange_and_save)


async def _complete_native(
    provider: str,
    body: CorosCompleteRequest,
    user: dict[str, Any],
    exchange_and_save: Callable[[str, str, int], Awaitable[bool]],
) -> dict[str, bool]:
    # Popped unconditionally: a completion token is single-use even when the
    # attempt fails, so it can't be retried or brute-forced.
    entry = _NATIVE_COMPLETIONS.pop(body.state, None)
    if (
        entry is None
        or entry[4] < time.monotonic() - _PENDING_AUTH_TTL_SECONDS
        or not secrets.compare_digest(entry[3], body.token)
        or entry[0] != user["id"]
    ):
        logger.warning(
            "oauth native completion rejected",
            extra={
                "fields": {
                    "service": "integrations",
                    "provider": provider,
                    "event": "native_completion_rejected",
                }
            },
        )
        raise HTTPException(status_code=400, detail=f"{PROVIDER_NAMES[provider]} connection could not be completed.")
    user_id, verifier, code, _, _ = entry
    if not await exchange_and_save(code, verifier, user_id):
        raise HTTPException(status_code=502, detail=f"{PROVIDER_NAMES[provider]} connection could not be completed.")
    return {"connected": True}


def _native_return_page(params: dict[str, str], provider: str = PROVIDER) -> HTMLResponse:
    """Sends the system browser back to the app. An HTML page rather than a
    302 because Android browsers may refuse to follow a redirect into another
    app; the link is the manual fallback when the script's navigation is blocked."""
    target = f"uphillai://{provider}/callback?{urlencode(params)}"
    page = (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Uphill AI</title></head>'
        '<body style="font-family:-apple-system,system-ui,sans-serif;text-align:center;padding:48px 24px">'
        f'<p><a href="{html.escape(target, quote=True)}">Return to Uphill AI / Quay lại Uphill AI</a></p>'
        f"<script>window.location.replace({json.dumps(target)});</script>"
        "</body></html>"
    )
    return HTMLResponse(page, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})


async def _exchange_and_save(code: str, verifier: str, user_id: int) -> bool:
    try:
        tokens = await coros_oauth.exchange_code(code, verifier)
        # Encryption happens inside this try, not after it: on a fresh deploy
        # where TOKEN_ENCRYPTION_KEY was never set, encrypt_token raises
        # TokenEncryptionUnconfigured -- which, outside this block, would
        # surface as a raw 500 AFTER the athlete already granted consent at
        # COROS, since coros_connect's own config guard cannot check
        # TOKEN_ENCRYPTION_KEY at /connect time for a deploy that only broke
        # it after that check ran (or, before that guard existed, at all).
        access_token_enc = token_crypto.encrypt_token(tokens.access_token)
        refresh_token_enc = token_crypto.encrypt_token(tokens.refresh_token) if tokens.refresh_token else None
    except (
        coros_oauth.CorosAuthError,
        httpx.HTTPError,
        ValueError,
        token_crypto.TokenEncryptionUnconfigured,
    ) as exc:
        # Never let a rejected/expired code, a flaky network call to COROS
        # (httpx.HTTPError covers connect/timeout/transport failures), a
        # non-JSON error body from a proxy in front of COROS (json.JSONDecodeError
        # is a ValueError), or a missing TOKEN_ENCRYPTION_KEY surface as a raw
        # 500 to the athlete's browser -- this endpoint is hit by a full-page
        # redirect from COROS, not an API call the frontend can catch, so any
        # unhandled exception here would strand them on a bare error page
        # outside the app shell. Logs only the failure type, never the code,
        # token, or state.
        logger.warning(
            "coros token exchange failed",
            extra={
                "fields": {
                    "service": "integrations",
                    "provider": "coros",
                    "event": "exchange_failed",
                    "user_id": user_id,
                    "error_type": type(exc).__name__,
                }
            },
        )
        return False

    db.save_connection(
        user_id=user_id,
        provider=PROVIDER,
        access_token_enc=access_token_enc,
        refresh_token_enc=refresh_token_enc,
        token_expires_at=tokens.expires_at,
        scopes=coros_oauth.SCOPES,
    )
    return True


def _resolve_plan_window(plan_id: int, user_id: int) -> tuple[date, date]:
    plan = db.get_plan_by_id(plan_id)
    if not plan or plan.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Plan not found.")

    start_str = plan.get("start_date")
    if start_str:
        try:
            if isinstance(start_str, str):
                start_d = datetime.strptime(start_str.split("T")[0], "%Y-%m-%d").date()
            else:
                start_d = start_str
        except Exception:
            start_d = date.today() - timedelta(days=30)
    else:
        start_d = date.today() - timedelta(days=30)

    # Monday of start week
    since = start_d - timedelta(days=start_d.weekday())

    race_str = plan.get("race_date")
    if race_str:
        try:
            if isinstance(race_str, str):
                race_d = datetime.strptime(race_str.split("T")[0], "%Y-%m-%d").date()
            else:
                race_d = race_str
            until = race_d + timedelta(days=2)
        except Exception:
            total_weeks = plan.get("total_weeks") or plan.get("plan_duration_weeks") or 12
            until = since + timedelta(weeks=total_weeks, days=2)
    else:
        total_weeks = plan.get("total_weeks") or plan.get("plan_duration_weeks") or 12
        until = since + timedelta(weeks=total_weeks, days=2)

    return since, until


@router.post("/coros/sync")
async def coros_sync_now(
    days: int = 30,
    plan_id: int | None = None,
    user: dict[str, Any] = Depends(get_current_user),
):
    if plan_id is not None:
        since, _ = _resolve_plan_window(plan_id, user["id"])
        delta = (date.today() - since).days + 1
        days = min(365, max(7, delta))
    try:
        return await coros_sync.sync_user(user["id"], days=days)
    except coros_sync.CorosReconnectRequired as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CorosParseError as exc:
        # CorosParseError subclasses ValueError, so it MUST be caught before
        # the generic ValueError arm below -- otherwise a COROS response-shape
        # change is reported to the athlete as a 400 client error carrying an
        # internal parser string as `detail` (e.g. "querySportRecords output
        # missing its 'Sport Records' header"), which is both a vendor-side
        # fault mis-reported as the athlete's fault and an internals leak.
        # Logged, not returned.
        logger.warning(
            "coros sync failed: unrecognised response shape",
            extra={
                "fields": {
                    "service": "integrations",
                    "provider": "coros",
                    "event": "sync_parse_failed",
                    "user_id": user["id"],
                    "error": str(exc),
                }
            },
        )
        raise HTTPException(status_code=502, detail="COROS sync failed. Please try again shortly.") from exc
    except (McpError, coros_sync.CorosSyncPersistError, CorosDailyMetricsUnavailableError) as exc:
        # All three are upstream/provider failures (a COROS transport error
        # surfaced through McpClient, or a persistence layer that rejected
        # every row in a non-empty batch) rather than anything the athlete did
        # wrong, so this is a 502, not a 400.
        logger.warning(
            "coros sync failed: upstream error",
            extra={
                "fields": {
                    "service": "integrations",
                    "provider": "coros",
                    "event": "sync_upstream_failed",
                    "user_id": user["id"],
                    "error_type": type(exc).__name__,
                }
            },
        )
        raise HTTPException(status_code=502, detail="COROS sync failed. Please try again shortly.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/coros")
async def coros_disconnect(user: dict[str, Any] = Depends(get_current_user)):
    # Agreement 9.5: delete within 24 hours of revocation. We do it immediately.
    db.delete_provider_data(user["id"], PROVIDER)
    return {"status": "disconnected"}


@router.post("/coros/sync-fitness")
async def coros_sync_fitness(user: dict[str, Any] = Depends(get_current_user)):
    try:
        res = await coros_sync.sync_fitness(user["id"])
        updated_user = db.get_user_by_id(user["id"]) or user
        model = updated_user.get("pace_zone_model") or "5_zone"
        threshold = updated_user.get("threshold_pace")
        zones = {}
        if threshold:
            zones = PlanGenerator.calculate_pace_zones_from_threshold(threshold, model=model)
        return {
            **res,
            "pace_zones": zones,
        }
    except coros_sync.CorosReconnectRequired as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except McpError as exc:
        logger.error("coros sync fitness failed: %s", exc)
        raise HTTPException(status_code=502, detail="COROS sync failed. Please try again shortly.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class CorosPushRequest(BaseModel):
    client_today: str | None = None
    lang: Literal["en", "vi"] = "en"


@router.post("/coros/push")
async def coros_push_now(body: CorosPushRequest, user: dict[str, Any] = Depends(get_current_user)):
    """Send the next ~4 weeks of the caller's own active plan to their COROS watch."""
    today = resolve_today(body.client_today, date.today())
    try:
        return await coros_push.push_plan(user["id"], today, body.lang)
    except coros_push.PushError as exc:
        raise HTTPException(status_code=exc.status, detail={"code": exc.code, "params": exc.params}) from exc


@router.get("/coros/push-status")
async def coros_push_status(client_today: str | None = None, user: dict[str, Any] = Depends(get_current_user)):
    return coros_push.push_status(user["id"], resolve_today(client_today, date.today()))


APPLE_HEALTH = "apple_health"
APPLE_HEALTH_TYPES = frozenset({"outdoor_run", "indoor_run", "hike", "strength"})
APPLE_HEALTH_RUN_TYPES = frozenset({"outdoor_run", "indoor_run"})
APPLE_HEALTH_BATCH = 500
# Faster than 2:30/km is a world-record pace held for the whole run: a distance glitch.
MIN_RUN_PACE_SEC_PER_KM = 150
MAX_DURATION_SECONDS = 48 * 3600
APPLE_HEALTH_METRIC_BATCH = 60
METRIC_MAX_AGE_DAYS = 60


class AppleHealthWorkout(BaseModel):
    external_id: str
    activity_type: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    distance_km: float | None = None
    elevation_gain_m: float | None = None
    avg_hr: int | None = None
    max_hr: int | None = None
    calories: int | None = None
    source_name: str | None = None


class AppleHealthSyncRequest(BaseModel):
    workouts: list[AppleHealthWorkout] = Field(default_factory=list, max_length=APPLE_HEALTH_BATCH)
    deleted_ids: list[str] = Field(default_factory=list, max_length=APPLE_HEALTH_BATCH)
    plan_id: int | None = None
    tz_offset_minutes: int | None = None
    # Parsed row by row (AppleHealthDailyMetric) so one malformed row is rejected, not a 422.
    daily_metrics: list[dict[str, Any]] = Field(default_factory=list, max_length=APPLE_HEALTH_METRIC_BATCH)


class AppleHealthDailyMetric(BaseModel):
    date: date
    resting_hr: int | None = None
    hrv_sdnn_ms: float | None = None
    sleep_minutes: int | None = None


def _implausible_metric(m: AppleHealthDailyMetric, today: date) -> str | None:
    if m.resting_hr is None and m.hrv_sdnn_ms is None and m.sleep_minutes is None:
        return "no values"
    if m.date > today + timedelta(days=1) or m.date < today - timedelta(days=METRIC_MAX_AGE_DAYS):
        return "date out of range"
    if m.resting_hr is not None and not 25 <= m.resting_hr <= 120:
        return "resting_hr out of range"
    if m.hrv_sdnn_ms is not None and not 5 <= m.hrv_sdnn_ms <= 300:
        return "hrv out of range"
    if m.sleep_minutes is not None and not 0 <= m.sleep_minutes <= 1080:
        return "sleep out of range"
    return None


def _store_daily_metrics(user_id: int, items: list[dict[str, Any]]) -> dict[str, Any]:
    """Validates and upserts the day rows, then refreshes the HRV baseline. A bad row is
    rejected with a reason; a storage failure is logged and never fails the workout sync."""
    if not settings.APPLE_HEALTH_RECOVERY_ENABLED:
        return {"accepted": 0, "rejected": [], "disabled": True}
    today = date.today()
    valid: dict[date, AppleHealthDailyMetric] = {}
    rejected: list[dict[str, str]] = []
    for item in items:
        try:
            metric = AppleHealthDailyMetric.model_validate(item)
        except ValidationError:
            raw_date = item.get("date") if isinstance(item, dict) else None
            rejected.append({"date": str(raw_date)[:10] if raw_date else "", "reason": "malformed"})
            continue
        reason = _implausible_metric(metric, today)
        if reason:
            rejected.append({"date": metric.date.isoformat(), "reason": reason})
            continue
        valid[metric.date] = metric  # a duplicate date: the last one wins
    accepted = 0
    try:
        for m in valid.values():
            db.upsert_daily_metric(
                user_id,
                CanonicalDailyMetric(
                    metric_date=m.date,
                    provider=APPLE_HEALTH,
                    resting_hr=m.resting_hr,
                    hrv_ms=m.hrv_sdnn_ms,
                    sleep_minutes=m.sleep_minutes,
                ),
            )
            accepted += 1
        recovery_baseline.refresh(user_id, list(valid))
    except Exception:
        logger.exception("apple health daily metrics failed")
    return {"accepted": accepted, "rejected": rejected}


def _implausible(w: AppleHealthWorkout, now: datetime) -> str | None:
    """Why a row from Apple Health can't be trusted, or None. Third-party apps write
    to Health too, so a bad row is skipped rather than failing the athlete's batch."""
    if not 1 <= len(w.external_id) <= 64:
        return "external_id must be 1-64 characters"
    if w.activity_type not in APPLE_HEALTH_TYPES:
        return "unsupported activity_type"
    if w.duration_seconds <= 0:
        return "duration must be positive"
    if (
        (w.distance_km is not None and w.distance_km < 0)
        or (w.elevation_gain_m is not None and w.elevation_gain_m < 0)
        or (w.calories is not None and w.calories < 0)
    ):
        return "negative distance, climb or calories"
    if w.start_time.tzinfo is None or w.end_time.tzinfo is None:
        return "start_time and end_time need a UTC offset"
    if w.end_time <= w.start_time:
        return "end_time is not after start_time"
    if w.duration_seconds > MAX_DURATION_SECONDS:
        return "duration over 48 h"
    if w.start_time > now + timedelta(days=1):
        return "start_time in the future"
    for hr in (w.avg_hr, w.max_hr):
        if hr is not None and not 25 <= hr <= 250:
            return "heart rate out of range"
    if w.avg_hr is not None and w.max_hr is not None and w.avg_hr > w.max_hr:
        return "avg_hr above max_hr"
    if w.activity_type in APPLE_HEALTH_RUN_TYPES and w.distance_km:
        if w.duration_seconds / w.distance_km < MIN_RUN_PACE_SEC_PER_KM:
            return "pace faster than 2:30/km"
    return None


def _to_canonical(w: AppleHealthWorkout) -> CanonicalActivity:
    pace = None
    if w.activity_type in APPLE_HEALTH_RUN_TYPES and w.distance_km and w.distance_km >= 0.1:
        pace = w.duration_seconds / w.distance_km
    return CanonicalActivity(
        external_id=w.external_id,
        provider=APPLE_HEALTH,
        activity_type=w.activity_type,
        start_time=w.start_time,
        end_time=w.end_time,
        duration_seconds=w.duration_seconds,
        distance_km=w.distance_km,
        elevation_gain_m=w.elevation_gain_m,
        avg_hr=w.avg_hr,
        max_hr=w.max_hr,
        avg_pace_sec_per_km=pace,
        calories=w.calories,
        device_model=w.source_name[:100] if w.source_name else None,
    )


@router.post("/apple-health/sync")
async def apple_health_sync(body: AppleHealthSyncRequest, user: dict[str, Any] = Depends(get_current_user)):
    """Stores workout summaries the iOS app read from Apple Health, then matches them.
    Idempotent: a re-sent workout is a no-op (upsert on the HealthKit UUID)."""
    if not settings.APPLE_HEALTH_ENABLED:
        raise HTTPException(status_code=404, detail="Apple Health is not available.")
    user_id = user["id"]
    if db.get_connection(user_id, APPLE_HEALTH) is None:
        # No tokens: HealthKit access lives on the phone, not with us.
        db.save_connection(
            user_id,
            APPLE_HEALTH,
            access_token_enc=None,
            refresh_token_enc=None,
            token_expires_at=None,
            scopes="read",
        )

    now = datetime.now(UTC)
    accepted = 0
    rejected: list[dict[str, str]] = []
    for workout in body.workouts:
        reason = _implausible(workout, now)
        if reason:
            rejected.append({"external_id": workout.external_id[:64], "reason": reason})
            continue
        db.upsert_activity(user_id, _to_canonical(workout))
        accepted += 1
    deleted = db.delete_activities_by_external_ids(user_id, APPLE_HEALTH, body.deleted_ids)
    daily_metrics = _store_daily_metrics(user_id, body.daily_metrics)
    db.mark_connection_synced(user_id, APPLE_HEALTH)
    if rejected:
        logger.info(
            "apple health rows rejected",
            extra={
                "fields": {
                    "service": "integrations",
                    "provider": APPLE_HEALTH,
                    "event": "rows_rejected",
                    "user_id": user_id,
                    "count": len(rejected),
                }
            },
        )

    if body.plan_id is not None:
        since, until = _resolve_plan_window(body.plan_id, user_id)
    else:
        until = date.today()
        since = until - timedelta(days=30)
    try:
        matching = await matching_runner.match_user(
            user_id, since, until, plan_id=body.plan_id, tz_offset_minutes=body.tz_offset_minutes
        )
    except Exception:
        # The workouts are stored; the next sync re-runs matching.
        logger.exception("apple health matching failed")
        matching = None
    return {
        "accepted": accepted,
        "rejected": rejected,
        "deleted": deleted,
        "matching": matching,
        "daily_metrics": daily_metrics,
    }


@router.delete("/apple-health")
async def apple_health_disconnect(user: dict[str, Any] = Depends(get_current_user)):
    db.delete_provider_data(user["id"], APPLE_HEALTH)
    return {"status": "disconnected"}


def _require_garmin() -> None:
    if not settings.GARMIN_ENABLED or not settings.GARMIN_CLIENT_ID or not settings.TOKEN_ENCRYPTION_KEY:
        raise HTTPException(status_code=404, detail="Garmin is not available.")


@router.get("/garmin/connect")
async def garmin_connect(
    request: Request,
    response: Response,
    ai_consent: bool = False,
    return_url: str | None = None,
    platform: str | None = None,
    user: dict[str, Any] = Depends(get_current_user),
):
    _require_garmin()
    # Garmin Agreement s15.10: explicit consent before any Garmin data reaches the AI provider.
    # Every coaching feature is AI, so Garmin is never connected without it.
    if not ai_consent:
        raise HTTPException(status_code=400, detail="Connecting Garmin needs your consent to AI coaching on its data.")
    return _start_connect(GARMIN, garmin_oauth.build_authorize_url, request, response, return_url, platform, user)


@router.get("/garmin/callback")
async def garmin_callback(
    code: str | None = None,
    state: str | None = None,
    state_cookie: str | None = Cookie(default=None, alias="garmin_oauth_state"),
):
    return await _handle_callback(GARMIN, code, state, state_cookie, _garmin_exchange_and_save)


@router.post("/garmin/complete")
async def garmin_complete(body: CorosCompleteRequest, user: dict[str, Any] = Depends(get_current_user)):
    _require_garmin()
    return await _complete_native(GARMIN, body, user, _garmin_exchange_and_save)


async def _garmin_exchange_and_save(code: str, verifier: str, user_id: int) -> bool:
    try:
        tokens = await garmin_oauth.exchange_code(code, verifier)
        garmin_user_id = await garmin_oauth.fetch_user_id(tokens.access_token)
        permissions = await garmin_oauth.fetch_permissions(tokens.access_token)
        access_token_enc = token_crypto.encrypt_token(tokens.access_token)
        refresh_token_enc = token_crypto.encrypt_token(tokens.refresh_token) if tokens.refresh_token else None
    except (
        garmin_oauth.GarminAuthError,
        httpx.HTTPError,
        ValueError,
        KeyError,
        token_crypto.TokenEncryptionUnconfigured,
    ) as exc:
        logger.warning(
            "garmin token exchange failed",
            extra={
                "fields": {
                    "service": "integrations",
                    "provider": GARMIN,
                    "event": "exchange_failed",
                    "user_id": user_id,
                    "error_type": type(exc).__name__,
                }
            },
        )
        return False
    existing = db.get_connection_by_provider_user(GARMIN, garmin_user_id)
    if existing is not None and existing["user_id"] != user_id:
        # One Garmin account feeds one Uphill athlete; pushes are keyed by the Garmin user id.
        logger.warning(
            "garmin account already linked",
            extra={
                "fields": {"service": "integrations", "provider": GARMIN, "event": "already_linked", "user_id": user_id}
            },
        )
        return False
    db.save_connection(
        user_id=user_id,
        provider=GARMIN,
        access_token_enc=access_token_enc,
        refresh_token_enc=refresh_token_enc,
        token_expires_at=tokens.expires_at,
        scopes=" ".join(sorted(permissions)),
        provider_user_id=garmin_user_id,
    )
    # Garmin Agreement s15.11: this athlete's data, and chats built on it, never feed AI evaluation.
    db.mark_ai_eval_excluded(user_id)
    return True


@router.delete("/garmin")
async def garmin_disconnect(user: dict[str, Any] = Depends(get_current_user)):
    """Disconnect, which is also how AI consent is withdrawn. Garmin requires the registration
    to be deleted on their side too; our copy of the data goes either way."""
    connection = db.get_connection(user["id"], GARMIN)
    if connection is not None:
        try:
            await garmin_oauth.delete_registration(await garmin_oauth.access_token(connection))
        except Exception as exc:
            logger.warning(
                "garmin deregistration failed",
                extra={
                    "fields": {
                        "service": "integrations",
                        "provider": GARMIN,
                        "event": "deregistration_failed",
                        "user_id": user["id"],
                        "error_type": type(exc).__name__,
                    }
                },
            )
    db.delete_provider_data(user["id"], GARMIN)
    return {"status": "disconnected"}


@router.post("/garmin/webhook/{token}")
async def garmin_webhook(
    token: str,
    request: Request,
    background: BackgroundTasks,
    garmin_client_id: str | None = Header(default=None),
) -> dict[str, str]:
    """Garmin push endpoint. Answers 200 before processing, as Garmin requires (30 s timeout,
    retries on anything else). Garmin pushes are unsigned, so the secret path token and the
    client-id header are what stop anyone else posting data into an athlete's account."""
    if (
        not settings.GARMIN_ENABLED
        or not settings.GARMIN_WEBHOOK_TOKEN
        or not secrets.compare_digest(token, settings.GARMIN_WEBHOOK_TOKEN)
        or garmin_client_id != settings.GARMIN_CLIENT_ID
    ):
        raise HTTPException(status_code=404, detail="Not found.")
    try:
        body = await request.json()
    except ValueError:
        body = None
    if isinstance(body, dict):
        background.add_task(garmin_ingest.process, body)
    # Shape only: these bodies carry athlete training and health data.
    logger.info(
        "garmin webhook received",
        extra={
            "fields": {
                "service": "integrations",
                "provider": GARMIN,
                "event": "webhook_received",
                "summary_types": sorted(body.keys()) if isinstance(body, dict) else [],
            }
        },
    )
    return {"status": "ok"}


@router.get("/status")
async def integration_status(user: dict[str, Any] = Depends(get_current_user)):
    connection = db.get_connection(user["id"], PROVIDER)
    profile = db.get_user_by_id(user["id"]) or user
    health = db.get_connection(user["id"], "apple_health")
    garmin_conn = db.get_connection(user["id"], GARMIN)
    return {
        "coros": {
            "connected": bool(connection and connection.get("status") == "active"),
            "last_sync_at": connection.get("last_sync_at") if connection else None,
            "threshold_pace": profile.get("threshold_pace"),
            "coros_vo2max": profile.get("coros_vo2max"),
            "coros_running_level": profile.get("coros_running_level"),
            "pace_zone_model": profile.get("pace_zone_model") or "5_zone",
        },
        "apple_health": {
            "enabled": settings.APPLE_HEALTH_ENABLED,
            "recovery_enabled": settings.APPLE_HEALTH_RECOVERY_ENABLED,
            "connected": bool(health and health.get("status") == "active"),
            "last_sync_at": health.get("last_sync_at") if health else None,
        },
        "garmin": {
            "enabled": settings.GARMIN_ENABLED,
            "connected": bool(garmin_conn and garmin_conn.get("status") == "active"),
            "last_sync_at": garmin_conn.get("last_sync_at") if garmin_conn else None,
            "permissions": (garmin_conn.get("scopes") or "").split() if garmin_conn else [],
        },
    }


@router.post("/matching/run")
async def matching_run(
    days: int = 30,
    plan_id: int | None = None,
    tz_offset_minutes: int | None = None,
    user: dict[str, Any] = Depends(get_current_user),
):
    if plan_id is not None:
        since, until = _resolve_plan_window(plan_id, user["id"])
    else:
        if not 1 <= days <= 365:
            raise HTTPException(status_code=400, detail="days must be between 1 and 365.")
        until = date.today()
        since = until - timedelta(days=days)
    return await matching_runner.match_user(
        user["id"], since, until, plan_id=plan_id, tz_offset_minutes=tz_offset_minutes
    )


@router.get("/matching")
async def matching_list(
    days: int = 30,
    plan_id: int | None = None,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Lists the caller's activities in the window with their current match
    state, for the matching-review UI. Raw values only (numbers, an ISO
    start_time) -- no pre-formatted strings, so the frontend can render
    Vietnamese numbers/dates in Vietnamese convention rather than English
    unit strings baked in server-side. See db.get_matches_for_review.
    """
    if plan_id is not None:
        since, until = _resolve_plan_window(plan_id, user["id"])
    else:
        if not 1 <= days <= 365:
            raise HTTPException(status_code=400, detail="days must be between 1 and 365.")
        until = date.today()
        since = until - timedelta(days=days)
        until = until + timedelta(days=1)
    activities = db.get_matches_for_review(user["id"], since, until, plan_id=plan_id)
    attach_week_context(activities)
    return {"activities": activities}


@router.patch("/matching/{activity_id}")
async def matching_override(
    activity_id: int,
    workout_id: int | None = None,
    body: dict[str, Any] | None = None,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Athlete corrects a match. Manual matches are never re-scored automatically.

    workout_id ownership is checked here (and again inside set_manual_match's
    own SQL, as defense in depth) to prevent an athlete from attaching their
    own activity to another athlete's workout by guessing a small integer --
    a permanent cross-user reference, since match_method='manual' is never
    cleared by an automatic run. A foreign workout_id gets the SAME 404/detail
    as a foreign activity_id: a different response would itself confirm the
    workout exists and just belongs to someone else.
    """
    if workout_id is None and body and "workout_id" in body:
        workout_id = body["workout_id"]

    if not db.activity_belongs_to_user(activity_id, user["id"]):
        raise HTTPException(status_code=404, detail="Activity not found.")
    if workout_id is not None and not db.workout_belongs_to_user(workout_id, user["id"]):
        raise HTTPException(status_code=404, detail="Activity not found.")

    quality_score = None
    quality_grade = None
    quality_details = None
    match_details = None
    if workout_id is not None:
        workout = db.get_workout_by_id(workout_id)
        activity = db.get_activity_by_id(activity_id)
        if workout and activity:
            athlete_profile = db.get_user_by_id(user["id"]) or {}

            # Check if this workout already has a matched activity -> combine into a multi-fragment session!
            existing_act = db.get_activity_matched_to_workout(workout_id)
            if existing_act and existing_act["id"] != activity_id:
                prev_ids = (existing_act.get("match_details") or {}).get("bundle_activity_ids") or [existing_act["id"]]
                if activity_id not in prev_ids:
                    prev_ids.append(activity_id)

                member_acts = [db.get_activity_by_id(aid) for aid in prev_ids]
                member_acts = [a for a in member_acts if a]

                primary = max(
                    member_acts,
                    key=lambda a: (float(a.get("distance_km") or 0.0), float(a.get("duration_seconds") or 0.0)),
                )
                primary_id = primary["id"]

                total_dist = round(sum(float(a.get("distance_km") or 0.0) for a in member_acts), 4)
                total_dur = sum(float(a.get("duration_seconds") or 0.0) for a in member_acts)
                total_elev = sum(float(a.get("elevation_gain_m") or 0.0) for a in member_acts)

                hr_weighted = [
                    (a["avg_hr"], float(a.get("duration_seconds") or 0.0)) for a in member_acts if a.get("avg_hr")
                ]
                hr_sum = sum(d for _, d in hr_weighted)
                avg_hr = round(sum(h * d for h, d in hr_weighted) / hr_sum) if hr_sum > 0 else None

                from services.matching.bundler import SessionBundle

                bundle = SessionBundle(
                    start_time=min(a["start_time"] for a in member_acts),
                    duration_seconds=total_dur,
                    distance_km=total_dist,
                    elevation_gain_m=total_elev,
                    avg_hr=avg_hr,
                    activity_ids=[a["id"] for a in member_acts],
                    activity_types={a.get("activity_type", "run") for a in member_acts},
                    primary_activity_id=primary_id,
                )

                q_res = score_workout_quality(workout, bundle, athlete_profile)
                bundle_details = {
                    "fragments": len(member_acts),
                    "bundle_activity_ids": [a["id"] for a in member_acts],
                    "bundle_distance_km": total_dist,
                    "bundle_duration_seconds": total_dur,
                    "bundle_elevation_gain_m": total_elev,
                    "bundle_avg_hr": avg_hr,
                    "fragment_breakdown": [
                        {
                            "activity_id": a["id"],
                            "distance_km": a.get("distance_km"),
                            "duration_seconds": a.get("duration_seconds"),
                            "avg_hr": a.get("avg_hr"),
                            "start_time": (
                                a["start_time"].isoformat()
                                if hasattr(a["start_time"], "isoformat")
                                else str(a["start_time"])
                            ),
                        }
                        for a in member_acts
                    ],
                }

                db.set_manual_match(
                    activity_id=primary_id,
                    workout_id=workout_id,
                    user_id=user["id"],
                    quality_score=q_res.overall_score,
                    quality_grade=q_res.grade,
                    quality_details=q_res.to_dict(),
                    match_details=bundle_details,
                )
                for a in member_acts:
                    if a["id"] != primary_id:
                        db.set_manual_match(
                            activity_id=a["id"],
                            workout_id=None,
                            user_id=user["id"],
                            match_details={"bundle_primary_activity_id": primary_id, "fragments": len(member_acts)},
                        )
                db.update_workout_log(workout_id, is_completed=1)
                return {"status": "ok", "activity_id": activity_id, "workout_id": workout_id, "combined": True}

            q_res = score_workout_quality(workout, activity, athlete_profile)
            quality_score = q_res.overall_score
            quality_grade = q_res.grade
            quality_details = q_res.to_dict()
        db.update_workout_log(workout_id, is_completed=1)

    db.set_manual_match(
        activity_id=activity_id,
        workout_id=workout_id,
        user_id=user["id"],
        quality_score=quality_score,
        quality_grade=quality_grade,
        quality_details=quality_details,
        match_details=match_details,
    )
    return {"status": "ok", "activity_id": activity_id, "workout_id": workout_id}
