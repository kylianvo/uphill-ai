"""Own-account notification preferences and device registration."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import text

from config import settings
from db import engine, verify_session
from services import notification_store as store
from services.notifications import allowlist

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def current_user(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    user = verify_session(authorization[7:])
    if not user:
        raise HTTPException(401, "Session expired")
    return user


class PreferencesPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workouts_enabled: bool | None = None
    coaching_enabled: bool | None = None
    results_enabled: bool | None = None
    workout_time: str | None = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    coaching_time: str | None = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    quiet_start: str | None = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    quiet_end: str | None = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    timezone: str | None = Field(None, max_length=100)
    language: Literal["en", "vi"] | None = None
    distance_unit: Literal["km", "mi"] | None = None
    paused_until: datetime | None = None
    checklist_snoozed_until: datetime | None = None
    muted_kinds: list[str] | None = None

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        if value is not None:
            try:
                ZoneInfo(value)
            except (ValueError, ZoneInfoNotFoundError) as exc:
                raise ValueError("Invalid timezone") from exc
        return value

    @field_validator("paused_until", "checklist_snoozed_until")
    @classmethod
    def aware_time(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError("Timezone required")
        return value


class Installation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=32, max_length=512, pattern=r"^[a-fA-F0-9]+$")
    environment: Literal["sandbox", "production"]
    permission: Literal["authorized", "provisional", "denied", "notDetermined"]


def public_preferences(value):
    # The app hides notification settings until this account can actually receive them.
    return {**{key: value[key] for key in store.PREFERENCE_FIELDS}, "available": value["user_id"] in allowlist()}


@router.get("/preferences")
def preferences(user=Depends(current_user)):
    return public_preferences(store.get_preferences(user["id"]))


@router.patch("/preferences")
def patch_preferences(body: PreferencesPatch, user=Depends(current_user)):
    values = body.model_dump(exclude_unset=True)
    nullable = {"timezone", "paused_until", "checklist_snoozed_until"}
    if any(value is None and key not in nullable for key, value in values.items()):
        raise HTTPException(422, "Preference cannot be null")
    current = store.get_preferences(user["id"])
    # Un-mute only: the list may shrink, never grow (muting goes through /feedback).
    if "muted_kinds" in values and not set(values["muted_kinds"]) <= set(current["muted_kinds"]):
        raise HTTPException(422, "muted_kinds can only be shortened")
    combined = {**current, **values}
    if combined["quiet_start"] == combined["quiet_end"]:
        raise HTTPException(422, "Quiet hours must have different start and end times")
    return public_preferences(store.update_preferences(user["id"], values))


@router.put("/installations/{installation_id}")
def register(installation_id: UUID, body: Installation, user=Depends(current_user)):
    if body.environment not in settings.APNS_ALLOWED_ENVIRONMENTS.split(","):
        raise HTTPException(422, "Unsupported notification environment")
    return store.upsert_installation(
        user["id"], str(installation_id), body.token.lower(), body.environment, body.permission, datetime.now(UTC)
    )


@router.delete("/installations/{installation_id}")
def unregister(installation_id: UUID, user=Depends(current_user)):
    store.remove_installation(user["id"], str(installation_id))
    return {}


class Feedback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    less: Literal[True]


@router.post("/{notification_id}/feedback")
def feedback(notification_id: UUID, body: Feedback, user=Depends(current_user)):
    with engine.connect() as conn:
        kind = conn.execute(
            text("SELECT kind FROM notification_events WHERE id=:id AND user_id=:user"),
            {"id": str(notification_id), "user": user["id"]},
        ).scalar()
    if kind is None:
        raise HTTPException(404, "Notification unavailable")
    store.mute_kind(user["id"], kind)
    return {}


@router.post("/{notification_id}/opened")
def opened(notification_id: UUID, user=Depends(current_user)):
    with engine.begin() as conn:
        row = conn.execute(
            text("""UPDATE notification_events SET opened_at=COALESCE(opened_at,NOW())
            WHERE id=:id AND user_id=:user RETURNING id"""),
            {"id": str(notification_id), "user": user["id"]},
        ).first()
        if not row:
            raise HTTPException(404, "Notification unavailable")
    return {}
