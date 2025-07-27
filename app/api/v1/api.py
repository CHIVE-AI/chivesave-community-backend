from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, versions

api_router = APIRouter()

api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(users.router, tags=["Users"])
api_router.include_router(versions.router, tags=["Versions"])
