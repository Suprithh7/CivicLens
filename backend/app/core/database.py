"""
Database configuration and session management.
Uses SQLAlchemy 2.0 with async support.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from app.config import settings


# Use DATABASE_URL directly (supports both SQLite and PostgreSQL)
DATABASE_URL = settings.DATABASE_URL


# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",  # Log SQL in development
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)


# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Declarative base for all models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Dependency for FastAPI endpoints
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Usage in FastAPI endpoints:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database.
    Creates all tables if they don't exist.
    
    Note: In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        # Import all models here to ensure they're registered
        from app.models import policy  # noqa: F401
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    Should be called on application shutdown.
    """
    await engine.dispose()
