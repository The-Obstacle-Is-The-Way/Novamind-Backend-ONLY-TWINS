"""
Authentication Middleware for FastAPI.

This middleware handles extracting and validating JWT tokens from requests,
retrieving the associated user, and attaching the user object to the request state.
"""

import logging
from typing import Optional, Tuple

from fastapi import Request, HTTPException, status, Depends
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

# Domain Exceptions
from app.domain.exceptions import InvalidTokenError, TokenExpiredError, MissingTokenError
from app.core.exceptions.auth_exceptions import AuthenticationError

# Consolidated services
from app.core.models.token_models import TokenPayload
from app.infrastructure.security.auth.authentication_service import AuthenticationService
from app.domain.entities.user import User
from app.infrastructure.security.jwt.jwt_service import JWTService

# Corrected import path for settings
from app.config.settings import get_settings, Settings

# Corrected import path for logger
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT authentication and user context setting.
    Relies on JWTService for token decoding and AuthenticationService for user retrieval.
    """

    def __init__(
        self,
        app,
        # Only non-default args needed here
        auth_service: AuthenticationService,
        public_paths: set[str],
    ):
        """Initialize the middleware.

        Args:
            app: The ASGI application.
            auth_service: Service for authentication logic (e.g., user retrieval).
            public_paths: A set of URL paths that do not require authentication.
        """
        super().__init__(app)
        self.auth_service = auth_service # Store non-default args
        self.public_paths = public_paths
        logger.info(f"AuthenticationMiddleware initialized. Public paths: {self.public_paths}.")

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request, perform authentication, and call next handler.
        """
        # --- Check for public paths FIRST --- 
        if any(request.url.path.startswith(path) for path in self.public_paths):
            logger.debug(f"Public path accessed: {request.url.path}. Skipping authentication.")
            request.state.user = None # Explicitly set user to None for public paths
            return await call_next(request)

        # --- If not public, proceed with authentication --- 
        try:
            # Attempt to extract token from header or cookies
            scheme, token = self._validate_auth_header(request.headers.get("Authorization"))

            # --- Explicit Dependency Resolution for Settings --- 
            app = request.app
            # Find the correct settings provider (override or original)
            override_settings_provider = app.dependency_overrides.get(get_settings)
            settings_provider = override_settings_provider if override_settings_provider else get_settings
            
            # Call the provider to get the actual settings object
            # NOTE: Assumes settings providers are synchronous. If they were async, we'd need to await.
            current_settings: Settings = settings_provider()
            logger.debug(f"Middleware resolved settings type: {type(current_settings)}, ID: {id(current_settings)}")
            # --- End Explicit Dependency Resolution --- 

            # Instantiate JWTService explicitly passing the resolved settings.
            # The Depends(get_settings) in JWTService.__init__ is effectively ignored for this call.
            jwt_service_instance = JWTService(settings=current_settings)
            logger.debug(f"Dispatch JWTService instance ID: {id(jwt_service_instance)} using explicitly resolved settings.")
            
            # --- Cascade: Added Logging START ---
            logger.debug(f"--- [Middleware] Attempting validation with Settings SECRET_KEY: {current_settings.SECRET_KEY}")
            logger.debug(f"--- [Middleware] JWTService using SECRET_KEY: {current_settings.SECRET_KEY}") # Log key from settings used by JWTService
            logger.debug(f"--- [Middleware] Token Received: {token[:10]}...{token[-10:]}") # Log token snippet
            # --- Cascade: Added Logging END ---
            
            token_data: TokenPayload = await jwt_service_instance.decode_token(token) 
            
            # Token is valid, payload extracted. Fetch the user.
            if not token_data.sub:
                # This case should ideally be caught by TokenPayload validation now
                raise InvalidTokenError("Token is missing required 'sub' claim.")
            
            user: Optional[User] = await self.auth_service.get_user_by_id(str(token_data.sub))

            if user is None:
                # User ID from token not found in DB or user is inactive
                raise AuthenticationError("User not found or inactive for token subject.")

            # --- Authentication Successful ---
            request.state.user = user
            logger.debug(f"User {user.id} authenticated successfully. Roles: {getattr(user, 'roles', 'N/A')}")

            response = await call_next(request)
            return response
            
        except (MissingTokenError, InvalidTokenError, TokenExpiredError, AuthenticationError) as e:
            # Handle all authentication-related domain exceptions
            error_detail = str(e)
            logger.warning(f"Auth failed: {error_detail} for path {request.url.path}")
            # --- Cascade: Added Logging START ---
            # Explicitly log the key used during the FAILED validation attempt
            logger.warning(f"--- [Middleware] Secret Key used for FAILED validation: {current_settings.SECRET_KEY if 'current_settings' in locals() else 'Settings not available'}")
            # --- Cascade: Added Logging END ---
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": error_detail},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
             # Catch unexpected errors during auth process
             logger.error(f"Unexpected error during authentication: {type(e).__name__} - {e}", exc_info=True)
             # --- Cascade: Added Logging START ---
             logger.error(f"--- [Middleware] Secret Key during UNEXPECTED error: {current_settings.SECRET_KEY if 'current_settings' in locals() else 'Settings not available'}")
             # --- Cascade: Added Logging END ---
             return JSONResponse(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 content={"detail": "Internal server error during authentication"},
             )

    def _validate_auth_header(self, header: Optional[str]) -> Tuple[str, str]:
        """Validates the Authorization header and extracts scheme and token."""
        if not header:
            raise MissingTokenError("Not authenticated: Authorization header missing") # Use specific exception

        scheme, token = get_authorization_scheme_param(header)
        if not scheme or scheme.lower() != "bearer":
            # Use specific exception
            raise InvalidTokenError("Not authenticated: Authorization scheme not Bearer or invalid") 
        if not token:
             # Use specific exception
            raise MissingTokenError("Not authenticated: Bearer token missing")
        return scheme, token
