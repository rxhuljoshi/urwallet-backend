# User settings routes
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..schemas.user import UserSettings, UserResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["user"])


@router.put("/settings", response_model=UserResponse)
async def update_settings(
    settings: UserSettings,
    user_data: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    firebase_uid, user = user_data
    
    update_data = settings.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if value is not None:
            setattr(user, field, value)
    
    if "currency" in update_data and update_data["currency"] is not None:
        user.is_currency_set = True
    
    await db.flush()
    
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
