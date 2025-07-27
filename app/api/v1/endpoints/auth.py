import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from asyncpg import Connection

from app.models.user import User, UserCreate, Token
from app.crud import users as users_crud
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_db, get_current_admin_user
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

@router.post("/token", response_model=Token, summary="Authenticate and get an access token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_conn: Connection = Depends(get_db)
):
    """
    Authenticates a user with username and password, returning an access token.
    """
    user = await users_crud.get_user_by_username(db_conn, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles}, expires_delta=access_token_expires
    )
    logger.info(f"User '{user.username}' successfully logged in.")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED, summary="Register a new user (Admin only)")
async def create_user_endpoint(
    user: UserCreate,
    db_conn: Connection = Depends(get_db),
    current_user: User = Depends(get_current_admin_user) # Only admin can create users
):
    """
    Registers a new user in the system. Requires admin privileges.
    """
    db_user = await users_crud.get_user_by_username(db_conn, user.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    return await users_crud.create_user(db_conn, user)
