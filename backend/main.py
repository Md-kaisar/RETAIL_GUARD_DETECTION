from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from database import connect_db, close_db
from routes import auth, transactions, cases, alerts, users, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="RetailGuard API",
    description="Fraud Detection and Prevention Suite",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "RetailGuard API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
