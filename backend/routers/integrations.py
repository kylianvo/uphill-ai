"""Device-integration endpoints (COROS today; Garmin when their developer
program reopens to new applicants).

Currently a STUB. It exists so that every URL declared on the COROS API
application form resolves before the application is reviewed -- see
docs/integrations/coros-api-application.md, form questions 13 and 14.

Two facts from the COROS API Reference V2.0.6 shape this file:

  * The workout-data receiving endpoint is documented as an "Https service
    interface that accepts workout data and allows duplicate data" -- COROS
    may deliver the same summary more than once, so the real handler must be
    idempotent. The stub is trivially idempotent because it persists nothing.
  * The service-status-check API is validated with a GET, and passes purely on
    "http status code is 200". `/api/health` already satisfies that and is what
    the form declares; the GET here is a convenience for probing this path.

TODO before go-live (needs COROS API Reference section 5.3, plus the clientId /
clientSecret issued on approval):
  - Confirm the acknowledgement body COROS expects; this stub returns 200 with a
    minimal JSON body on the assumption that the status code is what is checked.
  - Verify the push request's authenticity before trusting it.
  - Persist the payload to the durable `sync_events` queue rather than dropping
    it, and let the drain worker normalise and match it.
  - Link the pushed `planWorkoutId` back to the originating workouts row -- COROS
    echoes it for sessions started from a synced training plan, which removes the
    matching guesswork for those activities entirely.
"""

import secrets
import time
from datetime import date, datetime, timedelta
from typing import Any

import httpx
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

import db
from config import settings
from db import verify_session
from log_utils import get_logger
from services import coros_oauth, coros_sync, token_crypto
from services.matching import runner as matching_runner
from services.matching.quality_scorer import score_workout_quality
from services.mcp_client import McpError
from services.plan_generator import PlanGenerator
from services.providers.coros import PROVIDER, CorosDailyMetricsUnavailableError
from services.providers.coros_parsers import CorosParseError

router = APIRouter(prefix="/integrations", tags=["integrations"])
logger = get_logger(__name__)


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
    expired = [s for s, (_, _, created_at) in _PENDING_AUTH.items() if created_at < cutoff]
    for s in expired:
        _PENDING_AUTH.pop(s, None)


def _pop_pending_auth(state: str | None) -> tuple[int, str] | None:
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
    user_id, verifier, created_at = entry
    if created_at < time.monotonic() - _PENDING_AUTH_TTL_SECONDS:
        return None
    return user_id, verifier


def _error_redirect() -> RedirectResponse:
    """Every failure path out of /coros/callback ends here, and the one-shot
    CSRF cookie is always cleared on the way out -- success or failure -- so it
    can never be replayed against a later attempt."""
    response = RedirectResponse(url=f"{settings.FRONTEND_URL}/?coros=error")
    response.delete_cookie(key=COROS_OAUTH_STATE_COOKIE, path=COROS_CALLBACK_PATH)
    return response


@router.get("/coros/connect")
async def coros_connect(response: Response, user: dict[str, Any] = Depends(get_current_user)):
    # Both must be set before an athlete is sent to COROS: without
    # TOKEN_ENCRYPTION_KEY, the callback can exchange the code but cannot
    # store the resulting tokens (encrypt_token raises TokenEncryptionUnconfigured),
    # which would otherwise only surface AFTER the athlete has granted consent.
    if not settings.COROS_CLIENT_ID or not settings.TOKEN_ENCRYPTION_KEY:
        raise HTTPException(status_code=503, detail="COROS integration is not configured.")
    _prune_pending_auth()
    verifier, challenge = coros_oauth.make_pkce_pair()
    state = secrets.token_urlsafe(32)
    _PENDING_AUTH[state] = (user["id"], verifier, time.monotonic())
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
        key=COROS_OAUTH_STATE_COOKIE,
        value=state,
        max_age=_PENDING_AUTH_TTL_SECONDS,
        path=COROS_CALLBACK_PATH,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return {"authorize_url": coros_oauth.build_authorize_url(state, challenge)}


@router.get("/coros/callback")
async def coros_callback(
    code: str | None = None,
    state: str | None = None,
    state_cookie: str | None = Cookie(default=None, alias=COROS_OAUTH_STATE_COOKIE),
):
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
            "coros callback state mismatch",
            extra={
                "fields": {
                    "service": "integrations",
                    "provider": "coros",
                    "event": "callback_state_mismatch",
                }
            },
        )
        return _error_redirect()

    if not state_cookie:
        logger.warning(
            "coros callback state cookie absent",
            extra={
                "fields": {
                    "service": "integrations",
                    "provider": "coros",
                    "event": "callback_state_cookie_absent",
                }
            },
        )
        if getattr(settings, "COROS_REQUIRE_STATE_COOKIE", True):
            return _error_redirect()

    pending = _pop_pending_auth(state)
    if not code or not pending:
        return _error_redirect()

    user_id, verifier = pending
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
        return _error_redirect()

    db.save_connection(
        user_id=user_id,
        provider=PROVIDER,
        access_token_enc=access_token_enc,
        refresh_token_enc=refresh_token_enc,
        token_expires_at=tokens.expires_at,
        scopes=coros_oauth.SCOPES,
    )
    response = RedirectResponse(url=f"{settings.FRONTEND_URL}/?coros=connected")
    response.delete_cookie(key=COROS_OAUTH_STATE_COOKIE, path=COROS_CALLBACK_PATH)
    return response


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


@router.get("/status")
async def integration_status(user: dict[str, Any] = Depends(get_current_user)):
    connection = db.get_connection(user["id"], PROVIDER)
    profile = db.get_user_by_id(user["id"]) or user
    return {
        "coros": {
            "connected": bool(connection and connection.get("status") == "active"),
            "last_sync_at": connection.get("last_sync_at") if connection else None,
            "threshold_pace": profile.get("threshold_pace"),
            "coros_vo2max": profile.get("coros_vo2max"),
            "coros_running_level": profile.get("coros_running_level"),
            "pace_zone_model": profile.get("pace_zone_model") or "5_zone",
        }
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
