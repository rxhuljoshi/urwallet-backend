# Transaction models
from datetime import datetime
import uuid
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID

from ..core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    category = Column(String, nullable=False)
    remarks = Column(String, nullable=True)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    type = Column(String, nullable=False, default="expense")  # income | expense
    source = Column(String, nullable=True)  # budget | savings (for expenses only)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "category": self.category,
            "remarks": self.remarks,
            "date": self.date,
            "type": self.type,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MonthlySummary(Base):
    __tablename__ = "monthly_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    ai_insights = Column(Text, nullable=False)
    last_generated = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "month": self.month,
            "year": self.year,
            "ai_insights": self.ai_insights,
            "last_generated": self.last_generated.isoformat() if self.last_generated else None,
        }
