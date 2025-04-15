"""
Authentication Middleware for FastAPI.

This middleware handles extracting and validating JWT tokens from requests,
retrieving the associated user, and attaching the user object to the request state.
"""

import logging
from typing import Optional, Tuple

from fastapi import Request, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

# Domain Exceptions
from app.domain.exceptions import InvalidTokenError, TokenExpiredError, MissingTokenError
from app.core.exceptions.auth_exceptions import AuthenticationError # Import the missing exception

# Consolidated services
from app.infrastructure.security.jwt.jwt_service import JWTService, TokenPayload
from app.infrastructure.security.auth.authentication_service import AuthenticationService
from app.domain.entities.user import User # Assuming User entity exists

logger = logging.getLogger(__name__)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle JWT authentication.
    - Extracts token from header or cookies.
    - Validates token using JWTService.
    - Fetches user using AuthenticationService.
    - Attaches `request.state.user`.
    - Handles authentication errors (401).
    """

    def __init__(self, app, auth_service: AuthenticationService, jwt_service: JWTService):
        """Initialize middleware with AuthenticationService and JWTService instances."""
        super().__init__(app)
        self.auth_service = auth_service
        self.jwt_service = jwt_service # Store JWTService instance
        # Define public paths that bypass authentication
        self.public_paths = [
            "/docs", "/openapi.json", "/health", "/metrics",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            # Add other public endpoints like password reset, etc.
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request, perform authentication, and call next handler.
        """
        if any(request.url.path.startswith(path) for path in self.public_paths):
            logger.debug(f"Public path accessed: {request.url.path}. Skipping authentication.")
            request.state.user = None
            return await call_next(request)

        try:
            # Attempt to extract token from header or cookies
            token = self._extract_token(request)
            
            # Attempt to decode and validate token using JWTService instance
            token_data: TokenPayload = self.jwt_service.decode_token(token)
            
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
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": error_detail},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
             # Catch unexpected errors during auth process
             logger.exception(f"Unexpected error during authentication for path {request.url.path}: {e}")
             return JSONResponse(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 content={"detail": "Internal server error during authentication"},
             )

    def _extract_token(self, request: Request) -> str:
        """
        Extracts the JWT token from the Authorization header or cookies.
        
        Raises:
            MissingTokenError: If no token is found in header or cookies.
        """
        # 1. Try Authorization header
        auth_header: Optional[str] = request.headers.get("Authorization")
        if auth_header:
            scheme, param = get_authorization_scheme_param(auth_header)
            if scheme.lower() == "bearer" and param:
                return param # Return token string
        
        # 2. Try cookies (adjust cookie name if needed)
        cookie_token: Optional[str] = request.cookies.get("access_token")
        if cookie_token:
            return cookie_token

        # If neither found, raise specific error
        raise MissingTokenError("Authentication token not found in Authorization header or cookies.")

    # Removed all RBAC logic, dependency generation, JWTHandler, ProtectedRouteHandler etc.
    # Removed handle_error method, letting exceptions propagate or be handled by FastAPI handlers.
