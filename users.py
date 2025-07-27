import logging
import asyncpg
from typing import Optional, List

from models import UserCreate, UserInDB, User
from auth import get_password_hash
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

async def get_user_by_username(conn: asyncpg.Connection, username: str) -> Optional[UserInDB]:
    """Retrieves a user by username from the database."""
    try:
        row = await conn.fetchrow(
            """
            SELECT id, username, email, hashed_password, disabled, roles
            FROM users WHERE username = $1;
            """,
            username
        )
        if row:
            return UserInDB(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                hashed_password=row['hashed_password'],
                disabled=row['disabled'],
                roles=row['roles']
            )
        return None
    except Exception as e:
        logger.error(f"Error fetching user by username '{username}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error fetching user.")

async def get_user_by_id(conn: asyncpg.Connection, user_id: int) -> Optional[UserInDB]:
    """Retrieves a user by ID from the database."""
    try:
        row = await conn.fetchrow(
            """
            SELECT id, username, email, hashed_password, disabled, roles
            FROM users WHERE id = $1;
            """,
            user_id
        )
        if row:
            return UserInDB(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                hashed_password=row['hashed_password'],
                disabled=row['disabled'],
                roles=row['roles']
            )
        return None
    except Exception as e:
        logger.error(f"Error fetching user by ID '{user_id}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error fetching user.")

async def create_user(conn: asyncpg.Connection, user: UserCreate) -> User:
    """Creates a new user in the database."""
    hashed_password = get_password_hash(user.password)
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO users (username, email, hashed_password)
            VALUES ($1, $2, $3) RETURNING id, username, email, disabled, roles;
            """,
            user.username, user.email, hashed_password
        )
        if row:
            logger.info(f"User '{user.username}' created with ID: {row['id']}")
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                disabled=row['disabled'],
                roles=row['roles']
            )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user in database.")
    except asyncpg.exceptions.UniqueViolationError:
        logger.warning(f"Attempted to create duplicate username: {user.username}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered.")
    except Exception as e:
        logger.error(f"Error creating user '{user.username}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error during user creation: {e}")

async def get_users(conn: asyncpg.Connection) -> List[User]:
    """Retrieves all users from the database."""
    try:
        rows = await conn.fetch(
            """
            SELECT id, username, email, disabled, roles
            FROM users ORDER BY username;
            """
        )
        return [
            User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                disabled=row['disabled'],
                roles=row['roles']
            ) for row in rows
        ]
    except Exception as e:
        logger.error(f"Error fetching all users: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error fetching users.")
