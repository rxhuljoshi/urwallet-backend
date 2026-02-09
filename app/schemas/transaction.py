# Transaction request/response schemas
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class TransactionCreate(BaseModel):
    amount: float
    category: str
    remarks: Optional[str] = None
    date: str  # YYYY-MM-DD
    currency: Optional[str] = None  # Defaults to user's currency if not provided
    type: Literal["income", "expense"] = "expense"
    source: Optional[Literal["budget", "savings"]] = None  # Only for expenses
    add_to_savings: bool = False  # Only for income


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    remarks: Optional[str] = None
    date: Optional[str] = None
    currency: Optional[str] = None
    type: Optional[Literal["income", "expense"]] = None
    source: Optional[Literal["budget", "savings"]] = None


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    currency: str
    category: str
    remarks: Optional[str] = None
    date: str
    type: str
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CategorizeRequest(BaseModel):
    amount: float
    remarks: str
