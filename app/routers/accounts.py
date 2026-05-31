from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Account
from app.schemas.schemas import AccountCreate, AccountResponse
from typing import List

router = APIRouter()


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    """Cria uma nova conta bancária."""
    existing = db.query(Account).filter(Account.document == payload.document).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Documento já cadastrado.",
        )
    account = Account(
        owner_name=payload.owner_name,
        document=payload.document,
        balance=payload.initial_balance,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/", response_model=List[AccountResponse])
def list_accounts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Lista todas as contas com paginação."""
    return db.query(Account).offset(skip).limit(limit).all()


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: str, db: Session = Depends(get_db)):
    """Retorna uma conta pelo ID."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: str, db: Session = Depends(get_db)):
    """Remove uma conta."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")
    db.delete(account)
    db.commit()
