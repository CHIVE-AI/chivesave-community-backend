import logging
import asyncpg
from asyncpg.pool import Pool
from typing import AsyncGenerator, Optional

from app.core.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

settings = get_settings()
DATABASE_URL = settings.DATABASE_URL
_db_pool: Optional[Pool] = None

async def connect_to_db():
    """Establishes a connection pool to the PostgreSQL database."""
    global _db_pool
    try:
        _db_pool = await asyncpg.create_pool(DATABASE_URL)
        logger.info("Database connection pool created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database connection pool: {e}")
        raise

async def close_db_connection():
    """Closes the database connection pool."""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        logger.info("Database connection pool closed.")

async def get_db_connection_from_pool() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Provides an asynchronous database connection from the pool.
    The connection is released back to the pool after the request.
    """
    if not _db_pool:
        logger.error("Database pool not initialized.")
        raise RuntimeError("Database pool not initialized.")
    async with _db_pool.acquire() as connection:
        yield connection
