import os
import uuid
import json
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from asyncpg import Connection

from app.models.version import VersionCreate, Version
from app.crud import versions as versions_crud
from app.services import artifact_storage
from app.core.dependencies import get_db, get_current_active_user
from app.models.user import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/versions/save",
    response_model=Version,
    status_code=status.HTTP_201_CREATED,
    summary="ChiveSave: Save a new AI artifact version",
    description="Uploads an AI artifact (e.g., model, dataset) and saves it as a new version with metadata. Requires authentication."
)
async def save_artifact_version(
    name: str,
    file: UploadFile = File(..., description="The AI artifact file to upload."),
    description: Optional[str] = None,
    metadata: Optional[str] = None,
    db_conn: Connection = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user) # Protect this endpoint
):
    """
    **ChiveSave** allows you to upload an AI artifact (like a trained model or a processed dataset)
    and store it as a new version in the system. Each version is associated with a name,
    an optional description, and custom metadata.
    """
    logger.info(f"User '{current_user.username}' received request to save artifact: {name}")
    try:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # Save the uploaded file using the service
        await artifact_storage.save_artifact_file(file, unique_filename)

        parsed_metadata: Optional[Dict[str, Any]] = None
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                logger.error(f"Invalid metadata JSON provided: {metadata}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid metadata JSON format.")

        version_create = VersionCreate(
            name=name,
            description=description,
            metadata=parsed_metadata
        )
        new_version = await versions_crud.create_version(db_conn, version_create, unique_filename, artifact_storage.ARTIFACTS_DIR)
        logger.info(f"User '{current_user.username}' successfully saved new version: {new_version.id} - {new_version.name}")
        return new_version
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred during save_artifact_version for {name} by user {current_user.username}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save version: {e}")

@router.get(
    "/versions/{version_id}",
    response_model=Version,
    summary="Preview: Get details of a specific version",
    description="Retrieves the metadata and details for a specific AI artifact version by its ID. Requires authentication."
)
async def get_artifact_version(
    version_id: int,
    db_conn: Connection = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user) # Protect this endpoint
):
    """
    **Preview** allows you to inspect the details of a specific AI artifact version.
    This includes its name, description, storage path, creation timestamp, and any associated metadata.
    """
    logger.info(f"User '{current_user.username}' received request to get version ID: {version_id}")
    version = await versions_crud.get_version(db_conn, version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Version with ID {version_id} not found.")
    logger.info(f"User '{current_user.username}' successfully retrieved version ID: {version_id}")
    return version

@router.get(
    "/versions",
    response_model=List[Version],
    summary="List all AI artifact versions",
    description="Lists all stored AI artifact versions, ordered by creation date (most recent first). Requires authentication."
)
async def list_artifact_versions(
    db_conn: Connection = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user) # Protect this endpoint
):
    """
    Retrieves a comprehensive list of all AI artifact versions currently stored in the system.
    Results are ordered by their creation timestamp, with the newest versions appearing first.
    """
    logger.info(f"User '{current_user.username}' received request to list all versions.")
    versions = await versions_crud.get_versions(db_conn)
    logger.info(f"User '{current_user.username}' returning {len(versions)} versions.")
    return versions

@router.post(
    "/versions/restore/{version_id}",
    summary="Restore: Activate a specific version",
    description="Restores a specific AI artifact version by copying it to the 'current_active_artifact' directory, simulating activation. Requires authentication."
)
async def restore_artifact_version(
    version_id: int,
    db_conn: Connection = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user) # Protect this endpoint
):
    """
    **Restore** functionality allows you to activate a specific AI artifact version.
    This is achieved by copying the artifact file associated with the given `version_id`
    into a designated `current_active_artifact/` directory. Your AI application
    can then be configured to load the currently active artifact from this location.
    """
    logger.info(f"User '{current_user.username}' received request to restore version ID: {version_id}")
    version = await versions_crud.get_version(db_conn, version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Version with ID {version_id} not found.")

    restored_path = await artifact_storage.restore_artifact_file(version.artifact_path)
    if not restored_path:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to restore artifact for version {version_id}.")

    logger.info(f"User '{current_user.username}' successfully restored version {version_id} to {restored_path}")
    return JSONResponse(content={"message": f"Version {version_id} restored successfully to {restored_path}"})

@router.get(
    "/refactor-guidance",
    summary="Guidance on Refactor/RefactorEditor integration",
    description="Provides guidance on how to integrate 'Refactor' and 'RefactorEditor' processes with ChiveSave. Requires authentication."
)
async def refactor_guidance(current_user: UserInDB = Depends(get_current_active_user)): # Protect this endpoint
    """
    The **RefactorEditor** and **Refactor** functionalities typically involve external tools
    or scripts that modify an existing AI artifact (e.g., optimizing a model, cleaning a dataset).
    ChiveSave's role is to version control the *output* of these processes.
    """
    logger.info(f"User '{current_user.username}' providing refactor guidance.")
    return JSONResponse(content={
        "message": "For 'Refactor' and 'RefactorEditor' functionalities, your external tools or scripts would perform the refactoring/editing.",
        "next_steps": [
            "After refactoring, use the '/v1/versions/save' endpoint to upload the new, refactored artifact.",
            "Include a descriptive 'description' (e.g., 'Refactored model for performance improvement') and 'metadata' (e.g., {'refactored_from_version_id': <original_id>}) to track the lineage."
        ]
    })
