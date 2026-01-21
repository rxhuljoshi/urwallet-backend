# FastAPI app entry point
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.database import init_db, close_db
from .routers import auth, user, transactions, dashboard, ai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting urWallet API...")
    await init_db()
    logger.info("DB initialized")
    
    yield
    
    logger.info("Shutting down...")
    await close_db()


app = FastAPI(
    title="urWallet API",
    description="Personal expense tracking with AI-powered insights",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(ai.router, prefix="/api")


@app.get("/api/")
async def root():
    return {"message": "urWallet API", "status": "healthy"}
