# -*- coding: utf-8 -*-
"""
NOVAMIND FastAPI Application

This is the main application entry point for the NOVAMIND backend API.
It configures the FastAPI application, registers routes, middleware, and
event handlers.
"""

import logging
from contextlib import asynccontextmanager
import asyncio
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Use the new canonical config location
from app.config.settings import get_settings
            
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_instance, AsyncSessionLocal
from app.api.routes import api_router, setup_routers  # Import the setup_routers function
from app.presentation.api.routes.analytics_endpoints import router as analytics_router

# Import Middleware and Services
from app.presentation.middleware.authentication_middleware import AuthenticationMiddleware
from app.presentation.middleware.rate_limiting_middleware import setup_rate_limiting
from app.infrastructure.security.auth.authentication_service import AuthenticationService
from app.infrastructure.security.jwt.jwt_service import JWTService
from app.infrastructure.persistence.sqlalchemy.repositories.user_repository import UserRepository
from app.presentation.middleware.phi_middleware import add_phi_middleware # Updated import path

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
    # Ensure create_all is awaited if it's async
    if hasattr(db_instance, 'create_all') and asyncio.iscoroutinefunction(db_instance.create_all):
        await db_instance.create_all()
    elif hasattr(db_instance, 'create_all'):
        db_instance.create_all() # Assuming synchronous if not async
        
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
    # Get settings values with fallbacks
    settings = get_settings()
    project_name = settings.PROJECT_NAME
    app_description = settings.APP_DESCRIPTION
    version = settings.VERSION
    
    app = FastAPI(
        title=project_name,
        description=app_description,
        version=version,
        lifespan=lifespan, # Use the defined lifespan manager
    )
    
    # --- Instantiate Services ---
    # Note: Ideally, use dependency injection framework for cleaner service management
    async def get_db_session():
        async with AsyncSessionLocal() as session:
            yield session
            
    # Instantiate necessary services here, potentially using a DI container later
    jwt_service = JWTService()
    # AuthenticationService might need a UserRepository, which needs a db session
    # This setup implies services might need request-scoped dependencies (like db session)
    # which middleware setup doesn't easily handle. 
    # For now, let's assume AuthenticationService can be instantiated without a session,
    # or we adjust its get_user_by_id to accept a session.
    # TEMP: Instantiate Auth Service - REVISIT DEPENDENCY INJECTION
    # Assuming AuthenticationService can get a session itself or is adapted
    auth_service = AuthenticationService(user_repository=UserRepository()) # Simplified, needs review

    # --- Add Middleware (Order Matters!) ---
    
    # 1. CORS Middleware (Handles cross-origin requests first)
    origins = settings.BACKEND_CORS_ORIGINS
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in origins],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
    # 2. Authentication Middleware (Processes token, sets request.state.user)
    app.add_middleware(
        AuthenticationMiddleware, 
        auth_service=auth_service, 
        jwt_service=jwt_service
    )
    
    # 3. PHI Sanitization/Auditing Middleware (Processes after auth)
    add_phi_middleware(
        app,
        exclude_paths=settings.PHI_EXCLUDE_PATHS, # Configure via settings
        whitelist_patterns=settings.PHI_WHITELIST_PATTERNS, # Configure via settings
        audit_mode=settings.PHI_AUDIT_MODE # Configure via settings
    )

    # 4. Rate Limiting Middleware (Applies limits after auth & PHI handling)
    setup_rate_limiting(app)
    
    # --- Setup Routers ---
    setup_routers() # Initialize API routers
    
    api_prefix = settings.API_V1_STR
    if api_prefix.endswith('/'):
        api_prefix = api_prefix[:-1]
    
    app.include_router(api_router, prefix=api_prefix)
    
    if settings.ENABLE_ANALYTICS:
        app.include_router(analytics_router, prefix=api_prefix)
    
    # --- Static Files (Optional) ---
    static_dir = settings.STATIC_DIR
    if static_dir:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    return app

app = create_application()