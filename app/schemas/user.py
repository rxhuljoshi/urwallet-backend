# User request/response schemas
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserSettings(BaseModel):
    currency: Optional[str] = None
    dark_mode: Optional[bool] = None
    budget: Optional[float] = None
    ai_insights_enabled: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    currency: Optional[str] = None
    dark_mode: bool = True
    budget: Optional[float] = None
    ai_insights_enabled: bool = True
    is_currency_set: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
