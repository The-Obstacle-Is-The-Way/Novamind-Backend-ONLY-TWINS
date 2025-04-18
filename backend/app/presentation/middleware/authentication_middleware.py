"""
Authentication Middleware for FastAPI.

This middleware handles extracting and validating JWT tokens from requests,
retrieving the associated user, and attaching the user object to the request state.
"""

import logging
from typing import Optional, Tuple, Set, Callable, Awaitable, Any
from enum import Enum

from fastapi import Request, HTTPException, status, Depends
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, JSONResponse
from starlette.authentication import AuthCredentials, UnauthenticatedUser

# Domain Exceptions
from app.domain.exceptions import InvalidTokenError, TokenExpiredError, MissingTokenError, AuthenticationError, EntityNotFoundError

# Consolidated services
from app.infrastructure.security.auth.authentication_service import AuthenticationService
from app.infrastructure.models.user_model import UserModel
from app.infrastructure.security.jwt.jwt_service import JWTService, TokenPayload

# Corrected import path for settings
from app.config.settings import get_settings, Settings

# Corrected import path for logger
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT authentication using constructor injection.
    """

    # Inject services via constructor
    def __init__(
        self,
        app,
        auth_service: AuthenticationService, # Inject AuthenticationService
        jwt_service: JWTService,           # Inject JWTService
        public_paths: Optional[Set[str]] = None,
    ):
        super().__init__(app)
        self.auth_service = auth_service # Store injected service
        self.jwt_service = jwt_service   # Store injected service
        # Always allow the MentaLLaMA and XGBoost endpoints to be public (skip auth)
        base_paths = public_paths or set()
        ml_path = f"{get_settings().API_V1_STR}/mentallama"
        xgb_path = f"{get_settings().API_V1_STR}/ml/xgboost"
        self.public_paths = base_paths | {ml_path, xgb_path}
        logger.info(f"AuthenticationMiddleware initialized (using constructor injection). Public paths: {self.public_paths}.")

    # Remove Depends from dispatch
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
        # No Depends here anymore
    ) -> Response:
        """
        Process request, perform authentication using injected services, and call next handler.
        """
        # Skip authentication when running tests
        settings = get_settings()
        if getattr(settings, 'TESTING', False):
            logger.debug("Testing environment detected: skipping authentication.")
            # Still set unauthenticated user for consistency in tests if needed
            request.state.user = UnauthenticatedUser()
            request.state.auth = None
            return await call_next(request)

        request.state.user = UnauthenticatedUser()
        request.state.auth = None

        current_path = request.url.path
        if current_path in self.public_paths or any(current_path.startswith(path) for path in self.public_paths):
            logger.debug(f"Public path accessed: {current_path}. Skipping authentication.")
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        scheme, token = None, None
        if auth_header:
            try:
                scheme, token = get_authorization_scheme_param(auth_header)
            except HTTPException:
                logger.warning("Invalid Authorization header format.")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid Authorization header"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

        if not token or not scheme or scheme.lower() != "bearer":
            logger.debug("No valid Bearer token found in header.")
            return await call_next(request) # Proceed as unauthenticated

        # Use stored service instances
        try:
            # Use self.jwt_service and self.auth_service
            token_data: TokenPayload = await self.jwt_service.verify_token(token)
            user: Optional[UserModel] = await self.auth_service.get_user_by_id(str(token_data.sub))

            if not user:
                logger.warning(f"User not found for token subject: {token_data.sub}")
                raise EntityNotFoundError(f"User {token_data.sub} not found.")

            if not user.is_active:
                 logger.warning(f"Authentication attempt by inactive user: {token_data.sub}")
                 raise AuthenticationError("User account is inactive.")

            request.state.user = user
            user_roles = getattr(user, 'roles', [])
            scopes = [str(role) for role in user_roles]
            request.state.auth = AuthCredentials(scopes=scopes)
            logger.debug(f"User {user.id} authenticated successfully.")

        except (InvalidTokenError, AuthenticationError, EntityNotFoundError, TokenExpiredError, MissingTokenError) as e:
            logger.warning(f"Authentication failed: {e} for path {current_path}")
            status_code = status.HTTP_401_UNAUTHORIZED
            detail = str(e)
            if isinstance(e, EntityNotFoundError):
                 detail = "User associated with token not found."
            elif isinstance(e, AuthenticationError) and "inactive" in str(e).lower():
                 detail = "User account is inactive."
                 status_code = status.HTTP_403_FORBIDDEN
            return JSONResponse(
                status_code=status_code,
                content={"detail": detail},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {type(e).__name__} - {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error during authentication"},
            )

        response = await call_next(request)
        return response
