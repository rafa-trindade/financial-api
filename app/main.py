from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import accounts, transactions
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial API",
    description="API para gerenciamento de contas e transações bancárias",
    version="1.0.0",
    contact={"name": "Rafael Trindade", "email": "rafatrindade.exe@gmail.com"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "financial-api"}


#from mangum import Mangum
#handler = Mangum(app)