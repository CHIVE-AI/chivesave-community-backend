import os
import shutil
import logging
import aiofiles
from fastapi import UploadFile, HTTPException, status
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = "artifacts"
CURRENT_ACTIVE_ARTIFACT_DIR = "current_active_artifact"

# Create directories if they don't exist
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
os.makedirs(CURRENT_ACTIVE_ARTIFACT_DIR, exist_ok=True)

# Use a ThreadPoolExecutor for synchronous file operations like shutil.copy
# This prevents blocking the event loop for potentially large file copies.
executor = ThreadPoolExecutor(max_workers=4)

async def save_artifact_file(file: UploadFile, unique_filename: str) -> str:
    """
    Saves an uploaded artifact file to the artifacts directory.
    """
    file_path = os.path.join(ARTIFACTS_DIR, unique_filename)
    try:
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(await file.read())
        logger.info(f"Artifact file saved to: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save artifact file {unique_filename}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save artifact file: {e}")

async def restore_artifact_file(source_path: str) -> Optional[str]:
    """
    Restores an artifact by copying it to the current active directory.
    """
    # Use run_in_threadpool for synchronous file system operations
    # This ensures the FastAPI event loop is not blocked.
    try:
        # Clear the current active directory
        await os.get_event_loop().run_in_executor(executor, lambda: [
            os.unlink(os.path.join(CURRENT_ACTIVE_ARTIFACT_DIR, f))
            for f in os.listdir(CURRENT_ACTIVE_ARTIFACT_DIR)
            if os.path.isfile(os.path.join(CURRENT_ACTIVE_ARTIFACT_DIR, f))
        ])
        logger.info(f"Cleared directory: {CURRENT_ACTIVE_ARTIFACT_DIR}")

        # Copy the artifact to the current active directory
        destination_path = os.path.join(CURRENT_ACTIVE_ARTIFACT_DIR, os.path.basename(source_path))
        await os.get_event_loop().run_in_executor(executor, shutil.copy, source_path, destination_path)
        logger.info(f"Artifact copied from {source_path} to {destination_path}")
        return destination_path
    except Exception as e:
        logger.error(f"Error restoring artifact from {source_path}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to restore artifact: {e}")
