import logging
from fastapi import FastAPI
from app.db.connection import connect_to_db, close_db_connection
from app.db.init_db import init_db_schema
from app.api.v1.api import api_router

# Configure logging for the application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """
    Creates and configures the FastAPI application instance.
    """
    application = FastAPI(
        title="ChiveSave AI Versioning Backend",
        description="A self-hosted Python backend for AI artifact versioning using FastAPI and PostgreSQL, with authentication.",
        version="1.0.0",
        on_startup=[connect_to_db, init_db_schema], # Connect and initialize DB on startup
        on_shutdown=[close_db_connection] # Close DB connection on shutdown
    )
    application.include_router(api_router, prefix="/v1") # Include the versioned API router
    return application

app = create_application()
