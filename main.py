import os
import uuid
import json
import logging
import aiofiles
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status, APIRouter
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional, Dict, Any, List
from asyncpg import Connection

from models import VersionCreate, Version, User, UserCreate, Token, TokenData, UserInDB
from crud import create_version, get_version, get_versions, restore_version, ARTIFACTS_DIR
from database import connect_to_db, close_db_connection, get_db_connection, init_db_schema
from auth import oauth2_scheme, decode_access_token, verify_password, create_access_token
from users import get_user_by_username, create_user as create_db_user, get_users as get_all_users

# Configure logging for the application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChiveSave AI Versioning Backend",
    description="A self-hosted Python backend for AI artifact versioning using FastAPI and PostgreSQL, with authentication.",
    version="1.0.0",
    on_startup=[connect_to_db, init_db_schema], # Connect and initialize DB on startup
    on_shutdown=[close_db_connection] # Close DB connection on shutdown
)

# --- Dependency for current user ---
async def get_current_user(token: str = Depends(oauth2_scheme), db_conn: Connection = Depends(get_db_connection)) -> UserInDB:
    """Retrieves the current authenticated user from the token."""
    token_data = decode_access_token(token)
    username = token_data.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user_by_username(db_conn, username=username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Ensures the current user is active (not disabled)."""
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
    """Ensures the current user has 'admin' role."""
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user

# --- API Versioning Router ---
api_v1_router = APIRouter(prefix="/v1")

# --- Authentication Endpoints ---
@api_v1_router.post("/token", response_model=Token, summary="Authenticate and get an access token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_conn: Connection = Depends(get_db_connection)
):
    """
    Authenticates a user with username and password, returning an access token.
    """
    user = await get_user_by_username(db_conn, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30) # Use config setting
    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles}, expires_delta=access_token_expires
    )
    logger.info(f"User '{user.username}' successfully logged in.")
    return {"access_token": access_token, "token_type": "bearer"}

@api_v1_router.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED, summary="Register a new user (Admin only)")
async def create_user_endpoint(
    user: UserCreate,
    db_conn: Connection = Depends(get_db_connection),
    current_user: UserInDB = Depends(get_current_admin_user) # Only admin can create users
):
    """
    Registers a new user in the system. Requires admin privileges.
    """
    db_user = await get_user_by_username(db_conn, user.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    return await create_db_user(db_conn, user)

@api_v1_router.get("/users/me/", response_model=User, summary="Get current authenticated user's details")
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Retrieves details of the currently authenticated user.
    """
    return User(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        disabled=current_user.disabled,
        roles=current_user.roles
    )

@api_v1_router.get("/users/", response_model=List[User], summary="List all users (Admin only)")
async def read_users(
    db_conn: Connection = Depends(get_db_connection),
    current_user: UserInDB = Depends(get_current_admin_user) # Only admin can list users
):
    """
    Lists all registered users in the system. Requires admin privileges.
    """
    return await get_all_users(db_conn)

# --- ChiveSave Versioning Endpoints (Protected) ---
@api_v1_router.post(
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
    db_conn: Connection = Depends(get_db_connection),
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
        file_path = os.path.join(ARTIFACTS_DIR, unique_filename)

        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(await file.read())
        logger.info(f"Artifact file saved to: {file_path}")

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
        new_version = await create_version(db_conn, version_create, unique_filename)
        logger.info(f"User '{current_user.username}' successfully saved new version: {new_version.id} - {new_version.name}")
        return new_version
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred during save_artifact_version for {name} by user {current_user.username}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save version: {e}")

@api_v1_router.get(
    "/versions/{version_id}",
    response_model=Version,
    summary="Preview: Get details of a specific version",
    description="Retrieves the metadata and details for a specific AI artifact version by its ID. Requires authentication."
)
async def get_artifact_version(
    version_id: int,
    db_conn: Connection = Depends(get_db_connection),
    current_user: UserInDB = Depends(get_current_active_user) # Protect this endpoint
):
    """
    **Preview** allows you to inspect the details of a specific AI artifact version.
    This includes its name, description, storage path, creation timestamp, and any associated metadata.
    """
    logger.info(f"User '{current_user.username}' received request to get version ID: {version_id}")
    version = await get_version(db_conn, version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Version with ID {version_id} not found.")
    logger.info(f"User '{current_user.username}' successfully retrieved version ID: {version_id}")
    return version

@api_v1_router.get(
    "/versions",
    response_model=list[Version],
    summary="List all AI artifact versions",
    description="Lists all stored AI artifact versions, ordered by creation date (most recent first). Requires authentication."
)
async def list_artifact_versions(
    db_conn: Connection = Depends(get_db_connection),
    current_user: UserInDB = Depends(get_current_active_user) # Protect this endpoint
):
    """
    Retrieves a comprehensive list of all AI artifact versions currently stored in the system.
    Results are ordered by their creation timestamp, with the newest versions appearing first.
    """
    logger.info(f"User '{current_user.username}' received request to list all versions.")
    versions = await get_versions(db_conn)
    logger.info(f"User '{current_user.username}' returning {len(versions)} versions.")
    return versions

@api_v1_router.post(
    "/versions/restore/{version_id}",
    summary="Restore: Activate a specific version",
    description="Restores a specific AI artifact version by copying it to the 'current_active_artifact' directory, simulating activation. Requires authentication."
)
async def restore_artifact_version(
    version_id: int,
    db_conn: Connection = Depends(get_db_connection),
    current_user: UserInDB = Depends(get_current_active_user) # Protect this endpoint
):
    """
    **Restore** functionality allows you to activate a specific AI artifact version.
    This is achieved by copying the artifact file associated with the given `version_id`
    into a designated `current_active_artifact/` directory. Your AI application
    can then be configured to load the currently active artifact from this location.
    """
    logger.info(f"User '{current_user.username}' received request to restore version ID: {version_id}")
    restored_path = await restore_version(db_conn, version_id)
    if not restored_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Version with ID {version_id} not found or failed to restore.")
    logger.info(f"User '{current_user.username}' successfully restored version {version_id} to {restored_path}")
    return JSONResponse(content={"message": f"Version {version_id} restored successfully to {restored_path}"})

@api_v1_router.get(
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

# Include the versioned API router
app.include_router(api_v1_router)
