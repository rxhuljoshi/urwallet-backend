# Dashboard summary routes
from collections import defaultdict
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..models.transaction import Transaction
from ..dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    month: int,
    year: int,
    user_data: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    firebase_uid, user = user_data
    
    result = await db.execute(
        select(Transaction).where(Transaction.user_id == firebase_uid)
    )
    all_transactions = result.scalars().all()
    
    month_str = f"{year}-{month:02d}"
    month_txns = [t for t in all_transactions if t.date.startswith(month_str)]
    
    expenses = sum(t.amount for t in month_txns if t.category not in ["Savings", "Investment"])
    savings = sum(t.amount for t in month_txns if t.category == "Savings")
    investments = sum(t.amount for t in month_txns if t.category == "Investment")
    
    category_breakdown: Dict[str, float] = defaultdict(float)
    for t in month_txns:
        category_breakdown[t.category] += t.amount
    
    return {
        "expenses": expenses,
        "savings": savings,
        "investments": investments,
        "category_breakdown": dict(category_breakdown),
        "budget": user.budget,
        "transactions": [t.to_dict() for t in month_txns],
    }
