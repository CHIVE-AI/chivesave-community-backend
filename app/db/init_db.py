import logging
import asyncpg
from app.db.connection import get_db_connection_from_pool

logger = logging.getLogger(__name__)

async def init_db_schema():
    """Initializes the database schema by creating the 'versions' and 'users' tables if they don't exist."""
    # Acquire a connection from the pool to run schema initialization
    async for conn in get_db_connection_from_pool():
        async with conn.transaction():
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS versions (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
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
        break # Only need to run once
