import os
import logging
import asyncpg
from asyncpg.pool import Pool
from typing import AsyncGenerator, Optional

from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Dependency that provides an asynchronous database connection from the pool.
    The connection is released back to the pool after the request.
    """
    if not _db_pool:
        logger.error("Database pool not initialized.")
        raise RuntimeError("Database pool not initialized.")
    async with _db_pool.acquire() as connection:
        yield connection

async def init_db_schema():
    """Initializes the database schema by creating the 'versions' and 'users' tables if they don't exist."""
    async with _db_pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS versions (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE, -- Added UNIQUE constraint
                    description TEXT,
                    artifact_path VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) NOT NULL UNIQUE,
                    email VARCHAR(255),
                    hashed_password VARCHAR(255) NOT NULL,
                    disabled BOOLEAN DEFAULT FALSE,
                    roles TEXT[] DEFAULT ARRAY['user']
                );
            """)
            logger.info("Database schema initialized successfully (versions and users tables).")

if __name__ == "__main__":
    # This block is for direct execution to initialize the schema
    import asyncio
    async def main():
        await connect_to_db()
        await init_db_schema()
        await close_db_connection()
    asyncio.run(main())
