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
    
    # Calculate totals based on transaction type
    income = sum(t.amount for t in month_txns if t.type == "income")
    expenses = sum(t.amount for t in month_txns if t.type == "expense")
    
    # For backwards compatibility, also calculate by category
    savings_contributions = sum(t.amount for t in month_txns if t.category == "Savings" and t.type == "income")
    investments = sum(t.amount for t in month_txns if t.category == "Investment")
    
    # Expenses by source
    expenses_from_budget = sum(t.amount for t in month_txns if t.type == "expense" and (t.source == "budget" or t.source is None))
    expenses_from_savings = sum(t.amount for t in month_txns if t.type == "expense" and t.source == "savings")
    
    category_breakdown: Dict[str, float] = defaultdict(float)
    for t in month_txns:
        if t.type == "expense":
            category_breakdown[t.category] += t.amount
    
    # Sort transactions by date descending (latest first)
    sorted_txns = sorted(month_txns, key=lambda t: (t.date, t.created_at.isoformat() if t.created_at else ""), reverse=True)
    
    return {
        "income": income,
        "expenses": expenses,
        "savings": savings_contributions,
        "investments": investments,
        "savings_balance": user.savings_balance,
        "expenses_from_budget": expenses_from_budget,
        "expenses_from_savings": expenses_from_savings,
        "category_breakdown": dict(category_breakdown),
        "budget": user.budget,
        "transactions": [t.to_dict() for t in sorted_txns],
    }
