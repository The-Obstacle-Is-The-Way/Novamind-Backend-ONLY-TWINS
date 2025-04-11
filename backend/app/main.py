# -*- coding: utf-8 -*-
"""
NOVAMIND FastAPI Application

This is the main application entry point for the NOVAMIND backend API.
It configures the FastAPI application, registers routes, middleware, and
event handlers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_instance
from app.api.routes import api_router, setup_routers  # Import the setup_routers function
from app.presentation.api.routes.analytics_endpoints import router as analytics_router
from app.presentation.middleware.rate_limiting_middleware import setup_rate_limiting


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    This handles application startup and shutdown events, including database initialization
    and connection cleanup.
    
    Args:
        app: FastAPI application instance
    """
    # Startup events
    logger.info("Starting NOVAMIND application")
    
    # Initialize database
    db_instance = get_db_instance()
    await db_instance.create_all()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown events
    logger.info("Shutting down NOVAMIND application")
    
    # Any cleanup code goes here
    
    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    app = FastAPI(
        title=getattr(settings, 'PROJECT_NAME', 'Novamind Digital Twin'),
        description=getattr(settings, 'APP_DESCRIPTION', 'Advanced psychiatric digital twin platform for mental health analytics and treatment optimization'),
        version=getattr(settings, 'VERSION', '1.0.0'),
        lifespan=lifespan,
    )
    
    # Set up CORS middleware
    # Default to empty list if BACKEND_CORS_ORIGINS not defined in settings
    origins = getattr(settings, 'BACKEND_CORS_ORIGINS', [])
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in origins],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Set up rate limiting middleware
    setup_rate_limiting(app)
    # Setup routers lazily to prevent FastAPI from analyzing AsyncSession dependencies
    # during router setup, which causes issues with test collection and OpenAPI generation
    setup_routers()
    
    # Get API prefix and ensure it doesn't end with a slash
    api_prefix = getattr(settings, 'API_PREFIX', '/api/v1')
    if api_prefix.endswith('/'):
        api_prefix = api_prefix[:-1]
    
    # Include API router after lazy setup
    app.include_router(api_router, prefix=api_prefix)
    
    # Include analytics router if analytics are enabled
    if getattr(settings, "ENABLE_ANALYTICS", False):
        app.include_router(analytics_router, prefix=api_prefix)
    
    
    # Mount static files if STATIC_DIR is defined in settings
    static_dir = getattr(settings, "STATIC_DIR", None)
    if static_dir:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    return app


app = create_application()