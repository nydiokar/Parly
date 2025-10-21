"""
Database connection and session management for FastAPI.

This module provides database connectivity for the Parly API,
reusing the existing database schema and connection from db_setup.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from contextlib import contextmanager
from typing import Generator

from config import settings

# Create engine with connection pooling for API using centralized config
engine = create_engine(
    settings.database.url,
    connect_args={"check_same_thread": False},  # Needed for SQLite with FastAPI
    pool_pre_ping=True,  # Verify connections before using
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    pool_recycle=settings.database.pool_recycle
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[SQLAlchemySession, None, None]:
    """
    Dependency for FastAPI routes to get database sessions.

    Usage in routes:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
            pass

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions outside of FastAPI.

    Usage:
        with get_db_context() as db:
            # Use db here
            pass

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
