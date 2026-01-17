# Auth routes
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.user import UserResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserResponse)
async def get_me(user_data: tuple = Depends(get_current_user)):
    """Get current user. Creates user on first login."""
    firebase_uid, user = user_data
    return UserResponse(
        id=user.id,
        email=user.email,
        currency=user.currency,
        dark_mode=user.dark_mode,
        budget=user.budget,
        ai_insights_enabled=user.ai_insights_enabled,
        is_currency_set=user.is_currency_set,
        created_at=user.created_at,
    )
