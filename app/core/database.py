# Postgres connection via SQLAlchemy async
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator

from .config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        
        # Convert asyncpg URL to psycopg if needed
        db_url = settings.database_url
        if "postgresql+asyncpg://" in db_url:
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
        elif "postgresql://" in db_url and "+psycopg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://")
        
        print(f"DEBUG: Connecting to DB: {db_url.split('@')[-1]}")
        
        # Use NullPool - pgbouncer handles connection pooling
        # psycopg doesn't use prepared statements by default, so pgbouncer works!
        _engine = create_async_engine(
            db_url,
            echo=settings.debug,
            poolclass=NullPool,
        )
    return _engine


def session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """DB session for FastAPI dependency injection."""
    factory = session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
