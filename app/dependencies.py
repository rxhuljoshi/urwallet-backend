# FastAPI deps for auth and DB
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Tuple

from .core.database import get_db
from .core.supabase import verify_supabase_token, get_user_id_from_token, get_email_from_token
from .models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Tuple[str, User]:
    """Verify Supabase token, return (uid, user). Creates user on first login."""
    token = credentials.credentials
    decoded = verify_supabase_token(token)
    
    if not decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = get_user_id_from_token(decoded)
    email = get_email_from_token(decoded)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user id",
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        user = User(id=user_id, email=email or "")
        db.add(user)
        await db.flush()
    
    return user_id, user


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Just get user_id without DB lookup."""
    token = credentials.credentials
    decoded = verify_supabase_token(token)
    
    if not decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = get_user_id_from_token(decoded)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user id",
        )
    
    return user_id
