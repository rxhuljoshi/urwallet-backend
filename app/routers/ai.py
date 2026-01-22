# AI-powered features routes
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..models.transaction import Transaction, MonthlySummary
from ..schemas.transaction import CategorizeRequest
from ..dependencies import get_current_user
from ..services.ai import get_ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/insights")
async def get_insights(
    month: int,
    year: int,
    user_data: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    firebase_uid, user = user_data
    
    if not user.ai_insights_enabled:
        return {"insights": "AI insights are disabled in settings."}
    
    # Check cache first
    result = await db.execute(
        select(MonthlySummary)
        .where(
            MonthlySummary.user_id == firebase_uid,
            MonthlySummary.month == month,
            MonthlySummary.year == year,
        )
    )
    cached = result.scalar_one_or_none()
    
    if cached:
        return {"insights": cached.ai_insights}
    
    txn_result = await db.execute(
        select(Transaction).where(Transaction.user_id == firebase_uid)
    )
    all_txns = txn_result.scalars().all()
    
    month_str = f"{year}-{month:02d}"
    month_txns = [t for t in all_txns if t.date.startswith(month_str)]
    
    if not month_txns:
        return {"insights": "No transactions for this month yet."}
    
    ai_service = get_ai_service()
    insights = await ai_service.generate_monthly_insights(
        user_id=firebase_uid,
        month=month,
        year=year,
        transactions=[t.to_dict() for t in month_txns],
        budget=user.budget,
        currency=user.currency or "USD",
    )
    
    # Cache it
    summary = MonthlySummary(
        user_id=firebase_uid,
        month=month,
        year=year,
        ai_insights=insights,
    )
    db.add(summary)
    await db.flush()
    
    return {"insights": insights}


@router.post("/categorize")
async def categorize_expense(
    data: CategorizeRequest,
    user_data: tuple = Depends(get_current_user),
):
    ai_service = get_ai_service()
    category = await ai_service.categorize_transaction(data.amount, data.remarks)
    return {"category": category}


@router.get("/spike-detection")
async def spike_detection(
    user_data: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    firebase_uid, user = user_data
    
    now = datetime.now(timezone.utc)
    current_month = now.month
    current_year = now.year
    
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_year = current_year if current_month > 1 else current_year - 1
    
    result = await db.execute(
        select(Transaction).where(Transaction.user_id == firebase_uid)
    )
    all_txns = result.scalars().all()
    
    current_str = f"{current_year}-{current_month:02d}"
    prev_str = f"{prev_year}-{prev_month:02d}"
    
    current_txns = [t.to_dict() for t in all_txns if t.date.startswith(current_str)]
    prev_txns = [t.to_dict() for t in all_txns if t.date.startswith(prev_str)]
    
    ai_service = get_ai_service()
    warning = await ai_service.detect_spending_spike(current_txns, prev_txns)
    
    return {"warning": warning}
