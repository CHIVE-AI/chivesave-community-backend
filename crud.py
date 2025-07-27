import os
import shutil
import logging
import asyncpg
import aiofiles
from typing import List, Optional, Dict, Any
from datetime import datetime
from psycopg2.extras import Json  # Still useful for type hinting Json in asyncpg

from models import VersionCreate, Version
from fastapi import HTTPException
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = "artifacts"
CURRENT_ACTIVE_ARTIFACT_DIR = "current_active_artifact"

# Create directories if they don't exist
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
os.makedirs(CURRENT_ACTIVE_ARTIFACT_DIR, exist_ok=True)

# Use a ThreadPoolExecutor for synchronous file operations like shutil.copy
# This prevents blocking the event loop for potentially large file copies.
executor = ThreadPoolExecutor(max_workers=4)


async def create_version(conn: asyncpg.Connection, version: VersionCreate, artifact_filename: str) -> Version:
    """
    Creates a new version entry in the database.
    """
    artifact_path = os.path.join(ARTIFACTS_DIR, artifact_filename)
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO versions (name, description, artifact_path, metadata)
            VALUES ($1, $2, $3, $4::jsonb) RETURNING id, name, description, artifact_path, created_at, metadata;
            """,
            version.name, version.description, artifact_path, Json(version.metadata)
        )
        if row:
            logger.info(f"Version '{version.name}' created with ID: {row['id']}")
            return Version(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                artifact_path=row['artifact_path'],
                created_at=row['created_at'],
                metadata=row['metadata']
            )
        raise HTTPException(status_code=500, detail="Failed to create version in database.")
    except asyncpg.exceptions.UniqueViolationError as e:
        logger.error(f"Duplicate version name attempted: {version.name} - {e}")
        raise HTTPException(status_code=409, detail=f"Version with name '{version.name}' already exists.")
    except Exception as e:
        logger.error(f"Error creating version in DB: {e}")
        raise HTTPException(status_code=500, detail=f"Database error during version creation: {e}")


async def get_version(conn: asyncpg.Connection, version_id: int) -> Optional[Version]:
    """
    Retrieves a specific version by its ID from the database.
    """
    try:
        row = await conn.fetchrow(
            """
            SELECT id, name, description, artifact_path, created_at, metadata
            FROM versions WHERE id = $1;
            """,
            version_id
        )
        if row:
            logger.info(f"Retrieved version ID: {version_id}")
            return Version(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                artifact_path=row['artifact_path'],
                created_at=row['created_at'],
                metadata=row['metadata']
            )
        logger.warning(f"Version with ID {version_id} not found.")
        return None
    except Exception as e:
        logger.error(f"Error retrieving version {version_id} from DB: {e}")
        raise HTTPException(status_code=500, detail=f"Database error during version retrieval: {e}")


async def get_versions(conn: asyncpg.Connection) -> List[Version]:
    """
    Retrieves all versions from the database, ordered by creation date.
    """
    try:
        rows = await conn.fetch(
            """
            SELECT id, name, description, artifact_path, created_at, metadata
            FROM versions ORDER BY created_at DESC;
            """
        )
        logger.info(f"Retrieved {len(rows)} versions from DB.")
        return [
            Version(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                artifact_path=row['artifact_path'],
                created_at=row['created_at'],
                metadata=row['metadata']
            ) for row in rows
        ]
    except Exception as e:
        logger.error(f"Error retrieving all versions from DB: {e}")
        raise HTTPException(status_code=500, detail=f"Database error during versions listing: {e}")


async def restore_version(conn: asyncpg.Connection, version_id: int) -> Optional[str]:
    """
    Restores a specific version by copying its artifact to the current active directory.
    """
    version = await get_version(conn, version_id)
    if not version:
        logger.warning(f"Attempted to restore non-existent version ID: {version_id}")
        return None

    # Use run_in_threadpool for synchronous file system operations
    # This ensures the FastAPI event loop is not blocked.
    try:
        # Clear the current active directory
        await conn.loop.run_in_executor(executor, lambda: [
            os.unlink(os.path.join(CURRENT_ACTIVE_ARTIFACT_DIR, f))
            for f in os.listdir(CURRENT_ACTIVE_ARTIFACT_DIR)
            if os.path.isfile(os.path.join(CURRENT_ACTIVE_ARTIFACT_DIR, f))
        ])
        logger.info(f"Cleared directory: {CURRENT_ACTIVE_ARTIFACT_DIR}")

        # Copy the artifact to the current active directory
        destination_path = os.path.join(CURRENT_ACTIVE_ARTIFACT_DIR, os.path.basename(version.artifact_path))
        await conn.loop.run_in_executor(executor, shutil.copy, version.artifact_path, destination_path)
        logger.info(f"Version {version_id} artifact copied to {destination_path}")
        return destination_path
    except Exception as e:
        logger.error(f"Error restoring artifact for version {version_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restore artifact: {e}")
