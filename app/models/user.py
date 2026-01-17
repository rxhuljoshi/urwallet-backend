# User model
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Float, DateTime

from ..core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Firebase UID
    email = Column(String, unique=True, nullable=False)
    currency = Column(String, nullable=True)
    dark_mode = Column(Boolean, default=True, nullable=False)
    budget = Column(Float, nullable=True)
    ai_insights_enabled = Column(Boolean, default=True, nullable=False)
    is_currency_set = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "currency": self.currency,
            "dark_mode": self.dark_mode,
            "budget": self.budget,
            "ai_insights_enabled": self.ai_insights_enabled,
            "is_currency_set": self.is_currency_set,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
