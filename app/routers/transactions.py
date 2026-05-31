from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models.models import Account, Transaction, TransactionType
from app.schemas.schemas import TransactionCreate, TransactionResponse, StatementResponse, DailyBalance
from typing import List, Optional
from datetime import datetime

router = APIRouter()


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    """Registra uma transação e atualiza o saldo da conta."""
    account = db.query(Account).filter(Account.id == payload.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")

    if payload.type == TransactionType.DEBIT and account.balance < payload.amount:
        raise HTTPException(status_code=400, detail="Saldo insuficiente.")

    transaction = Transaction(
        account_id=payload.account_id,
        type=payload.type,
        amount=payload.amount,
        description=payload.description,
    )

    if payload.type == TransactionType.CREDIT:
        account.balance += payload.amount
    else:
        account.balance -= payload.amount

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/statement/{account_id}", response_model=StatementResponse)
def get_statement(
    account_id: str,
    start_date: Optional[str] = Query(None, example="2026-01-01"),
    end_date: Optional[str] = Query(None, example="2026-12-31"),
    db: Session = Depends(get_db),
):
    """
    Retorna extrato consolidado com saldo diário.
    extrair saldo diário consolidado de tabela com milhões de registros.
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")

    # Query SQL eficiente com agregação diária
    daily_sql = text("""
        SELECT
            DATE(created_at) as date,
            SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END) as total_credits,
            SUM(CASE WHEN type = 'debit'  THEN amount ELSE 0 END) as total_debits,
            SUM(CASE WHEN type = 'credit' THEN amount ELSE -amount END) as net_balance
        FROM transactions
        WHERE account_id = :account_id
          AND (:start_date IS NULL OR DATE(created_at) >= :start_date)
          AND (:end_date   IS NULL OR DATE(created_at) <= :end_date)
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """)

    rows = db.execute(
        daily_sql,
        {"account_id": account_id, "start_date": start_date, "end_date": end_date},
    ).fetchall()

    daily_summary = [
        DailyBalance(
            date=str(row.date),
            total_credits=row.total_credits,
            total_debits=row.total_debits,
            net_balance=row.net_balance,
        )
        for row in rows
    ]

    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .order_by(Transaction.created_at.desc())
        .limit(50)
        .all()
    )

    return StatementResponse(
        account_id=account_id,
        owner_name=account.owner_name,
        current_balance=account.balance,
        transactions=transactions,
        daily_summary=daily_summary,
    )
