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

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Use the new canonical config location
from app.config.settings import get_settings
            
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_instance, get_db_session
from app.presentation.api.routes import api_router, setup_routers  # Import from the new location

# Import Middleware and Services
from app.presentation.middleware.authentication_middleware import AuthenticationMiddleware
from app.presentation.middleware.rate_limiting_middleware import setup_rate_limiting
from app.presentation.middleware.phi_middleware import add_phi_middleware # Updated import path

# Import necessary types for middleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable, Awaitable

# Remove direct imports of handlers/repos if not needed elsewhere in main
# from app.infrastructure.security.password.password_handler import PasswordHandler
# from app.domain.repositories.user_repository import UserRepository
# from unittest.mock import MagicMock

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
    # Ensure create_all is awaited if it's an async operation
    if hasattr(db_instance, 'create_all') and callable(getattr(db_instance, 'create_all')):
        await db_instance.create_all()
    
    # Yield control to the application
    logger.info("ASGI lifespan startup complete.")
    yield
    
    # Shutdown events
    logger.info("ASGI lifespan shutdown starting.")
    # Close database connections
    await db_instance.dispose()
    logger.info("ASGI lifespan shutdown complete.")


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
        
    # 2. Error Handling Middleware (Outermost)
    # app.add_middleware(ErrorHandlingMiddleware)

    # 3. Security Headers
    # app.add_middleware(SecurityHeadersMiddleware)

    # 4. Authentication Middleware 
    app.add_middleware(
        AuthenticationMiddleware, # Pass the class 
        # Explicitly pass only the intended kwarg
        public_paths={
            "/openapi.json",
            "/docs",
            "/api/v1/auth/refresh",
            "/health", 
        }
    )
    
    # 5. PHI Sanitization/Auditing Middleware (Processes after auth)
    add_phi_middleware(
        app,
        exclude_paths=settings.PHI_EXCLUDE_PATHS, # Configure via settings
        whitelist_patterns=settings.PHI_WHITELIST_PATTERNS, # Configure via settings
        audit_mode=settings.PHI_AUDIT_MODE # Configure via settings
    )

    # 6. Rate Limiting Middleware (Applies limits after auth & PHI handling)
    setup_rate_limiting(app)

    # 7. Security Headers Middleware (Adds headers to the final response using decorator style)
    @app.middleware("http")
    async def security_headers_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Add basic security headers to all responses."""
        logger.info(f"---> SecurityHeadersMiddleware: Executing for path: {request.url.path}") # DEBUG log
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        logger.info(f"---> SecurityHeadersMiddleware: Set X-Content-Type-Options header for path: {request.url.path}") # DEBUG log
        # Add other security headers here if needed, e.g.:
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # response.headers["X-Frame-Options"] = "DENY"
        return response
    
    # --- Setup Routers ---
    setup_routers() # Initialize API routers
    
    api_prefix = settings.API_V1_STR
    if api_prefix.endswith('/'):
        api_prefix = api_prefix[:-1]
    
    app.include_router(api_router, prefix=api_prefix)
    
    # --- Static Files (Optional) ---
    static_dir = settings.STATIC_DIR
    if static_dir:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    return app

# Create the main FastAPI application instance using the factory function
# COMMENTED OUT: Avoid module-level app creation which interferes with test fixture setup.
# The app instance should be created within fixtures (like in conftest.py) or entry points.
# app = create_application()

# Entry point for running the application directly (e.g., with `python app/main.py`)
# This is typically used for local development/debugging.
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting application directly using uvicorn for development.")
    # Load settings to get host and port for uvicorn
    # Ensure settings are loaded correctly here for direct execution
    try:
        run_settings = get_settings()
        uvicorn.run(
            # Point uvicorn to the location of the factory function or the app instance
            # If using the factory pattern, it's often cleaner to point to the factory:
            "app.main:create_application", 
            # Or if you need the instance (ensure it's created only here):
            # app, 
            host=run_settings.HOST,
            port=run_settings.PORT,
            reload=run_settings.RELOAD, # Enable reload based on settings
            factory=True # Indicate that the import string points to a factory
        )
    except Exception as e:
        logger.critical(f"Failed to start uvicorn: {e}", exc_info=True)
        # Optionally, exit with an error code
        # import sys
        # sys.exit(1)