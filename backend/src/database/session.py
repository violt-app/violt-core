"""
Violt Core Lite - Database Module

This module handles database connection and session management using SQLAlchemy.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from pathlib import Path
import os
import logging
import asyncio

from ..core.config import settings, DEFAULT_DATA_DIR

logger = logging.getLogger(__name__)  # Add logger

# Create SQLAlchemy base class for models
Base = declarative_base()


# Ensure database URL is properly formatted for cross-platform compatibility
def get_database_url():
    """Get properly formatted database URL for the current platform."""
    db_url = settings.DATABASE_URL

    # Handle SQLite URLs
    if db_url.startswith("sqlite:///"):
        # Extract the path part (remove sqlite:///)
        path_part = db_url[10:]

        # If it's a relative path, make it absolute using the data directory
        if not path_part.startswith("/") and not (
            len(path_part) > 1 and path_part[1] == ":"
        ):
            # It's a relative path, combine with data directory
            db_path = DEFAULT_DATA_DIR / path_part
            # Ensure parent directory exists
            os.makedirs(db_path.parent, exist_ok=True)
            # Create new URL with absolute path
            db_url = f"sqlite:///{db_path}"

    # Convert to aiosqlite for async operations
    return db_url.replace("sqlite:///", "sqlite+aiosqlite:///")


# Create async engine
engine = create_async_engine(
    get_database_url(),
    connect_args=settings.DATABASE_CONNECT_ARGS,
    poolclass=NullPool,
    echo=settings.DEBUG,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """Dependency for getting async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_database_tables():
    """Create all database tables defined by SQLAlchemy models."""
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def initialize_database():
    """Initialize the database, ensuring all tables exist."""
    try:
        await create_database_tables()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise
