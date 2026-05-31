from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TransactionType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


# --- Account Schemas ---

class AccountCreate(BaseModel):
    owner_name: str = Field(..., example="Rafael Trindade")
    document: str = Field(..., example="000.000.000-00")
    initial_balance: float = Field(default=0.0, ge=0)


class AccountResponse(BaseModel):
    id: str
    owner_name: str
    document: str
    balance: float
    created_at: datetime

    class Config:
        from_attributes = True


# --- Transaction Schemas ---

class TransactionCreate(BaseModel):
    account_id: str
    type: TransactionType
    amount: float = Field(..., gt=0, example=100.00)
    description: Optional[str] = Field(None, example="Pagamento de fatura")


class TransactionResponse(BaseModel):
    id: str
    account_id: str
    type: TransactionType
    amount: float
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Statement Schema ---

class DailyBalance(BaseModel):
    date: str
    total_credits: float
    total_debits: float
    net_balance: float


class StatementResponse(BaseModel):
    account_id: str
    owner_name: str
    current_balance: float
    transactions: List[TransactionResponse]
    daily_summary: List[DailyBalance]
