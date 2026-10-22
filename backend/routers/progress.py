"""The Progress tab: Training and Health cards that have enough data to show (services/progress_cards.py)."""

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException

from routers.integrations import get_current_user
from services import progress_cards

router = APIRouter()


@router.get("/progress")
async def get_progress(
    section: Literal["training", "health"],
    days: int = 28,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if days not in progress_cards.HISTORY_DAYS:
        raise HTTPException(status_code=422, detail=f"days must be one of {progress_cards.HISTORY_DAYS}")
    return progress_cards.build(user, section, days=days)
