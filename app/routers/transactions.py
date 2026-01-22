# Transaction CRUD routes
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..core.database import get_db
from ..models.transaction import Transaction
from ..schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from ..dependencies import get_current_user
from ..services.ai import get_ai_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=List[TransactionResponse])
async def get_transactions(
    user_data: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    firebase_uid, user = user_data
    
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == firebase_uid)
        .order_by(Transaction.date.desc())
    )
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
    
    category = txn_data.category
    if (not category or category == "Other") and txn_data.remarks:
        ai_service = get_ai_service()
        category = await ai_service.categorize_transaction(txn_data.amount, txn_data.remarks)
    
    # Default to user's currency if not provided
    currency = txn_data.currency or user.currency or "USD"
    
    transaction = Transaction(
        user_id=firebase_uid,
        amount=txn_data.amount,
        currency=currency,
        category=category,
        remarks=txn_data.remarks,
        date=txn_data.date,
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
    
    update_data = txn_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(transaction, field, value)
    
    await db.flush()
    
    return TransactionResponse(
        id=str(transaction.id),
        user_id=transaction.user_id,
        amount=transaction.amount,
        currency=transaction.currency,
        category=transaction.category,
        remarks=transaction.remarks,
        date=transaction.date,
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
    
    result = await db.execute(
        delete(Transaction)
        .where(Transaction.id == txn_uuid, Transaction.user_id == firebase_uid)
        .returning(Transaction.id)
    )
    deleted = result.scalar_one_or_none()
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"message": "Transaction deleted"}
