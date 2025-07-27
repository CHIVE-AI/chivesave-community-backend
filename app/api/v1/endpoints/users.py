import logging
from typing import List
from fastapi import APIRouter, Depends, status
from asyncpg import Connection

from app.models.user import User, UserInDB
from app.crud import users as users_crud
from app.core.dependencies import get_db, get_current_active_user, get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/users/me/", response_model=User, summary="Get current authenticated user's details")
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

@router.get("/users/", response_model=List[User], summary="List all users (Admin only)")
async def read_users(
    db_conn: Connection = Depends(get_db),
    current_user: UserInDB = Depends(get_current_admin_user) # Only admin can list users
):
    """
    Lists all registered users in the system. Requires admin privileges.
    """
    logger.info(f"Admin user '{current_user.username}' requested list of all users.")
    return await users_crud.get_users(db_conn)
