import logging
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from asyncpg import Connection

from app.db.connection import get_db_connection_from_pool
from app.core.security import decode_access_token
from app.crud import users as users_crud
from app.models.user import UserInDB, TokenData

# Configure logging
logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/token")

async def get_db(conn: Connection = Depends(get_db_connection_from_pool)) -> AsyncGenerator[Connection, None]:
    """Dependency that provides an asynchronous database connection from the pool."""
    yield conn

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_conn: Connection = Depends(get_db)
) -> UserInDB:
    """Retrieves the current authenticated user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except Exception as e:
        logger.warning(f"Token decoding failed: {e}")
        raise credentials_exception

    user = await users_crud.get_user_by_username(db_conn, username=token_data.username)
    if user is None:
        logger.warning(f"Authenticated user '{token_data.username}' not found in DB.")
        raise credentials_exception
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
