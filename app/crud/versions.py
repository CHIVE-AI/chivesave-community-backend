import logging
import asyncpg
from typing import List, Optional, Dict, Any
from psycopg2.extras import Json

from app.models.version import VersionCreate, Version
from fastapi import HTTPException, status

# Configure logging
logger = logging.getLogger(__name__)

async def create_version(conn: asyncpg.Connection, version: VersionCreate, artifact_filename: str, artifact_base_path: str) -> Version:
    """
    Creates a new version entry in the database.
    """
    artifact_path = f"{artifact_base_path}/{artifact_filename}"
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create version in database.")
    except asyncpg.exceptions.UniqueViolationError as e:
        logger.error(f"Duplicate version name attempted: {version.name} - {e}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Version with name '{version.name}' already exists.")
    except Exception as e:
        logger.error(f"Error creating version in DB: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error during version creation: {e}")


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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error during version retrieval: {e}")


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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error during versions listing: {e}")
