# Transaction CRUD routes
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..core.database import get_db
from ..models.transaction import Transaction
from ..models.user import User
from ..schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from ..dependencies import get_current_user
from ..services.ai import get_ai_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=List[TransactionResponse])
async def get_transactions(
    sort: Optional[str] = Query("latest", regex="^(latest|oldest|amount_asc|amount_desc)$"),
    type_filter: Optional[str] = Query(None, regex="^(income|expense)$"),
    category: Optional[str] = None,
    user_data: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    firebase_uid, user = user_data
    
    query = select(Transaction).where(Transaction.user_id == firebase_uid)
    
    # Apply type filter
    if type_filter:
        query = query.where(Transaction.type == type_filter)
    
    # Apply category filter
    if category:
        query = query.where(Transaction.category == category)
    
    # Apply sorting
    if sort == "latest":
        query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Transaction.date.asc(), Transaction.created_at.asc())
    elif sort == "amount_asc":
        query = query.order_by(Transaction.amount.asc())
    elif sort == "amount_desc":
        query = query.order_by(Transaction.amount.desc())
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return [
        TransactionResponse(
            id=str(t.id),
            user_id=t.user_id,
            amount=t.amount,
            currency=t.currency,
            category=t.category,
            remarks=t.remarks,
            date=t.date,
            type=t.type or "expense",
            source=t.source,
            created_at=t.created_at,
        )
        for t in transactions
    ]


@router.post("", response_model=TransactionResponse)
async def create_transaction(
    txn_data: TransactionCreate,
    user_data: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    firebase_uid, user = user_data
    
    # AI categorization if category is empty or "Other"
    category = txn_data.category
    if (not category or category == "Other") and txn_data.remarks:
        ai_service = get_ai_service()
        category = await ai_service.categorize_transaction(txn_data.amount, txn_data.remarks)
    
    # Default to user's currency if not provided
    currency = txn_data.currency or user.currency or "USD"
    
    # Handle income/expense logic
    source = None
    if txn_data.type == "expense":
        source = txn_data.source or "budget"
        
        # Validate savings balance if spending from savings
        if source == "savings" and user.savings_balance < txn_data.amount:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient savings balance. Available: {user.savings_balance}"
            )
        
        # Deduct from savings if source is savings
        if source == "savings":
            user.savings_balance -= txn_data.amount
            
    elif txn_data.type == "income":
        # Add to savings if requested
        if txn_data.add_to_savings:
            user.savings_balance += txn_data.amount
            category = "Savings"  # Override category for savings income
    
    transaction = Transaction(
        user_id=firebase_uid,
        amount=txn_data.amount,
        currency=currency,
        category=category,
        remarks=txn_data.remarks,
        date=txn_data.date,
        type=txn_data.type,
        source=source,
    )
    
    db.add(transaction)
    await db.flush()
    
    return TransactionResponse(
        id=str(transaction.id),
        user_id=transaction.user_id,
        amount=transaction.amount,
        currency=transaction.currency,
        category=transaction.category,
        remarks=transaction.remarks,
        date=transaction.date,
        type=transaction.type,
        source=transaction.source,
        created_at=transaction.created_at,
    )


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    txn_data: TransactionUpdate,
    user_data: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    firebase_uid, user = user_data
    
    try:
        txn_uuid = UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID")
    
    result = await db.execute(
        select(Transaction)
        .where(Transaction.id == txn_uuid, Transaction.user_id == firebase_uid)
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Handle savings balance changes if source is being modified
    old_source = transaction.source
    old_amount = transaction.amount
    old_type = transaction.type
    
    update_data = txn_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(transaction, field, value)
    
    # Adjust savings if needed
    if old_type == "expense" and old_source == "savings":
        # Return old amount to savings
        user.savings_balance += old_amount
    
    if transaction.type == "expense" and transaction.source == "savings":
        # Deduct new amount from savings
        if user.savings_balance < transaction.amount:
            raise HTTPException(status_code=400, detail="Insufficient savings balance")
        user.savings_balance -= transaction.amount
    
    await db.flush()
    
    return TransactionResponse(
        id=str(transaction.id),
        user_id=transaction.user_id,
        amount=transaction.amount,
        currency=transaction.currency,
        category=transaction.category,
        remarks=transaction.remarks,
        date=transaction.date,
        type=transaction.type or "expense",
        source=transaction.source,
        created_at=transaction.created_at,
    )


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    user_data: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    firebase_uid, user = user_data
    
    try:
        txn_uuid = UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID")
    
    # First get the transaction to check if we need to adjust savings
    result = await db.execute(
        select(Transaction)
        .where(Transaction.id == txn_uuid, Transaction.user_id == firebase_uid)
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Restore savings if this was an expense from savings
    if transaction.type == "expense" and transaction.source == "savings":
        user.savings_balance += transaction.amount
    
    # Remove savings if this was income added to savings
    if transaction.type == "income" and transaction.category == "Savings":
        user.savings_balance -= transaction.amount
    
    await db.execute(
        delete(Transaction).where(Transaction.id == txn_uuid)
    )
    
    return {"message": "Transaction deleted"}
