import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Banco em memória para testes
TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)


# --- Fixtures ---

@pytest.fixture
def sample_account():
    doc = f"doc-{uuid.uuid4()}"
    response = client.post("/accounts/", json={
        "owner_name": "Rafael Trindade",
        "document": doc,
        "initial_balance": 1000.0,
    })
    return response.json()


# --- Health ---

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# --- Accounts ---

def test_create_account():
    response = client.post("/accounts/", json={
        "owner_name": "João Silva",
        "document": "111.222.333-44",
        "initial_balance": 500.0,
    })
    assert response.status_code == 201
    assert response.json()["owner_name"] == "João Silva"
    assert response.json()["balance"] == 500.0


def test_create_account_duplicate_document(sample_account):
    response = client.post("/accounts/", json={
        "owner_name": "Outro Nome",
        "document": sample_account["document"],  # mesmo documento do fixture
        "initial_balance": 0.0,
    })
    assert response.status_code == 400
    assert "Documento já cadastrado" in response.json()["detail"]


def test_get_account(sample_account):
    account_id = sample_account["id"]
    response = client.get(f"/accounts/{account_id}")
    assert response.status_code == 200
    assert response.json()["id"] == account_id


def test_get_account_not_found():
    response = client.get("/accounts/id-inexistente")
    assert response.status_code == 404


# --- Transactions ---

def test_create_credit_transaction(sample_account):
    account_id = sample_account["id"]
    response = client.post("/transactions/", json={
        "account_id": account_id,
        "type": "credit",
        "amount": 200.0,
        "description": "Depósito",
    })
    assert response.status_code == 201
    assert response.json()["type"] == "credit"

    # Verifica se saldo foi atualizado
    account = client.get(f"/accounts/{account_id}").json()
    assert account["balance"] == 1200.0


def test_create_debit_transaction(sample_account):
    account_id = sample_account["id"]
    response = client.post("/transactions/", json={
        "account_id": account_id,
        "type": "debit",
        "amount": 300.0,
        "description": "Saque",
    })
    assert response.status_code == 201

    account = client.get(f"/accounts/{account_id}").json()
    assert account["balance"] == 700.0


def test_debit_insufficient_balance(sample_account):
    account_id = sample_account["id"]
    response = client.post("/transactions/", json={
        "account_id": account_id,
        "type": "debit",
        "amount": 9999.0,
    })
    assert response.status_code == 400
    assert "Saldo insuficiente" in response.json()["detail"]


def test_get_statement(sample_account):
    account_id = sample_account["id"]
    response = client.get(f"/transactions/statement/{account_id}")
    assert response.status_code == 200
    assert response.json()["account_id"] == account_id
    assert "daily_summary" in response.json()
