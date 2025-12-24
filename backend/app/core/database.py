"""SQLAlchemy database setup with optional DB support.

DB is optional - app can start without DATABASE_URL.
Health check has hard timeout to prevent blocking.
"""
import asyncio
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

Base = declarative_base()

# Global engine and session (None if no DB_URL)
engine: Optional[create_engine] = None
SessionLocal: Optional[sessionmaker] = None


class ServiceState(Base):
    """Minimal service state table (GDPR compliant - no content fields)."""

    __tablename__ = "service_state"

    id = Column(Integer, primary_key=True)
    service_name = Column(String, unique=True, nullable=False)
    last_heartbeat = Column(DateTime, nullable=True)

    # NO content fields - GDPR compliance


def init_db(database_url: str) -> None:
    """Initialize database connection and session factory.

    Args:
        database_url: PostgreSQL connection URL
    """
    global engine, SessionLocal

    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Verify connections before using
        echo=False,  # Set to True for SQL logging
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables (Alembic handles migrations, but this ensures Base is ready)
    Base.metadata.create_all(bind=engine)


def _check_db_health_sync() -> bool:
    """Synchronous DB health check (runs in thread).

    Returns:
        True if DB is healthy, False otherwise.
    """
    if not engine:
        return False

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False


async def check_db_health() -> bool:
    """Check database health with hard timeout.

    Returns:
        True if DB is healthy, False on timeout/error.
    """
    if not engine:
        return False

    try:
        # Run sync DB check in thread with timeout
        result = await asyncio.wait_for(
            asyncio.to_thread(_check_db_health_sync),
            timeout=settings.db_health_timeout_seconds,
        )
        return result
    except (asyncio.TimeoutError, Exception):
        return False


@contextmanager
def get_db():
    """Get database session (context manager).

    Yields:
        Database session

    Raises:
        RuntimeError: If database not initialized
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

