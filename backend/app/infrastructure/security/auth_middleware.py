# -*- coding: utf-8 -*-
"""
HIPAA-Compliant Authentication Middleware

This module provides middleware for enforcing authentication, authorization,
and audit logging for all PHI access in accordance with HIPAA requirements.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

# Import the RoleBasedAccessControl class from rbac module
from app.infrastructure.security.rbac import RoleBasedAccessControl

# Re-export RoleBasedAccessControl for backward compatibility
__all__ = ["AuthMiddleware", "JWTAuthMiddleware", "get_auth_middleware", "RoleBasedAccessControl"]

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import settings
from app.domain.exceptions import AuthenticationError, TokenExpiredError
from app.infrastructure.logging.audit_logger import get_audit_logger
from app.infrastructure.logging.phi_logger import get_phi_logger
from app.infrastructure.security.jwt_service import JWTService

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Global audit logger for tracking PHI access
audit_logger = get_audit_logger()

# PHI logger for sanitized logging
phi_logger = get_phi_logger("auth_middleware")


def verify_token(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify

    Returns:
        Dict[str, Any]: Decoded token payload

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Use dependency injection to get jwt_service
        jwt_service = get_jwt_service()
        payload = jwt_service.verify_token(token)
        return payload
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get the current authenticated user from the token.

    Args:
        token: JWT token

    Returns:
        Dict[str, Any]: User data from token
    """
    return verify_token(token)


def verify_patient_access(
    token_data: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Verify the user has patient access (all roles have patient access).

    Args:
        token_data: The decoded token data

    Returns:
        Dict[str, Any]: Token data if authorized
    """
    # All roles can access patient resources
    return token_data


def verify_provider_access(
    token_data: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Verify the user has provider access.

    Args:
        token_data: The decoded token data

    Returns:
        Dict[str, Any]: Token data if authorized

    Raises:
        HTTPException: If not authorized
    """
    role = token_data.get("role", "")
    if role not in ["provider", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access provider resources",
        )
    return token_data


def verify_admin_access(
    token_data: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Verify the user has admin access.

    Args:
        token_data: The decoded token data

    Returns:
        Dict[str, Any]: Token data if authorized

    Raises:
        HTTPException: If not authorized
    """
    role = token_data.get("role", "")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin resources",
        )
    return token_data


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    HIPAA-compliant authentication middleware for FastAPI.

    Enforces authentication, authorization, and audit logging for
    all PHI access in the application.
    """

    def __init__(self, app, jwt_service=None, config=None):
        """
        Initialize the middleware with application settings.

        Args:
            app: The FastAPI application
            jwt_service: Optional JWTService instance for dependency injection
            config: Optional config object for testing
        """
        super().__init__(app)
        self.settings = config or settings
        self.logger = logging.getLogger("app.infrastructure.security.auth_middleware")
        # Allow dependency injection of jwt_service for testing
        self.jwt_service = jwt_service or JWTService(self.settings.jwt_secret_key if hasattr(self.settings, 'jwt_secret_key') else self.settings.SECRET_KEY)

        # Routes that don't require authentication
        self.public_paths = [
            "/api/v1/auth/token",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/public",  # Added for tests
        ]

        # Rate limiting tracker - in production this would be Redis-backed
        self._request_counters = {}
        self._RATE_LIMIT_WINDOW = 60  # seconds
        self._RATE_LIMIT_MAX_REQUESTS = 100  # max requests per window

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the request through the middleware.

        Args:
            request: The incoming request
            call_next: Function to call the next middleware/endpoint

        Returns:
            Response: The processed response
        """
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Check for rate limiting
        client_ip = str(request.client.host) if request.client else "unknown"
        if self._is_rate_limited(client_ip):
            return Response(
                content=json.dumps({"detail": "Too many requests"}),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )

        # Process the request
        start_time = time.time()

        try:
            # Extract and validate token
            token = self._extract_token(request)
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Decode and validate the token
            try:
                # Use the instance jwt_service with proper DI support
                token_data = self.jwt_service.verify_token(token)
            except TokenExpiredError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except AuthenticationError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Add user data to request state for downstream handlers
            request.state.user = token_data

            # Check for required roles if endpoint is restricted
            self._check_endpoint_permission(request, token_data)

            # Process the request
            response = await call_next(request)

            # Log access if PHI was accessed
            if self._is_phi_access(request.url.path):
                self._log_phi_access(request, token_data, response.status_code)

            return response

        except HTTPException as e:
            # Re-raise HTTP exceptions
            self.logger.warning(f"Authentication error: {e.status_code} - {e.detail}")
            raise

        except Exception as e:
            # Log error without exposing details
            self.logger.error(f"Auth middleware error: {type(e).__name__}")

            # Return standardized error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
        finally:
            # Log request processing time
            elapsed = time.time() - start_time
            self.logger.debug(f"Request processed in {elapsed:.4f} seconds")

    def _is_rate_limited(self, client_ip: str) -> bool:
        """
        Check if the client is rate limited.

        Args:
            client_ip: The client IP address

        Returns:
            bool: True if rate limited
        """
        now = time.time()

        # Clean up old entries
        for ip in list(self._request_counters.keys()):
            if now - self._request_counters[ip]["timestamp"] > self._RATE_LIMIT_WINDOW:
                del self._request_counters[ip]

        # Check if client is in counters
        if client_ip not in self._request_counters:
            self._request_counters[client_ip] = {"count": 1, "timestamp": now}
            return False

        # Check if window has reset
        if (
            now - self._request_counters[client_ip]["timestamp"]
            > self._RATE_LIMIT_WINDOW
        ):
            self._request_counters[client_ip] = {"count": 1, "timestamp": now}
            return False

        # Increment counter
        self._request_counters[client_ip]["count"] += 1

        # Check if limit exceeded
        return (
            self._request_counters[client_ip]["count"] > self._RATE_LIMIT_MAX_REQUESTS
        )

    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from request.

        Args:
            request: The incoming request

        Returns:
            Optional[str]: The JWT token if found, None otherwise
        """
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.replace("Bearer ", "")

        # Check for token in cookies
        token = request.cookies.get("access_token")
        if token:
            return token

        return None

    def _is_public_path(self, path: str) -> bool:
        """
        Check if the path is public (doesn't require authentication).

        Args:
            path: The request path

        Returns:
            bool: True if the path is public
        """
        # Check exact matches
        if path in self.public_paths:
            return True

        # Check path prefixes
        for public_path in self.public_paths:
            if public_path.endswith("*") and path.startswith(public_path[:-1]):
                return True

        return False

    def _check_endpoint_permission(
        self, request: Request, token_data: Dict[str, Any]
    ) -> None:
        """
        Check if the user has permission to access the endpoint.

        Args:
            request: The incoming request
            token_data: The decoded JWT token data

        Raises:
            HTTPException: If the user doesn't have permission
        """
        # Extract user role
        user_role = token_data.get("role")
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Missing role information"
            )

        # Check if the endpoint requires specific roles
        required_roles = self._get_required_roles(request.url.path)
        if required_roles and user_role not in required_roles:
            # Log the unauthorized access attempt
            phi_logger.warning(
                f"Unauthorized access attempt: {user_role} tried to access {request.url.path}"
            )

            # Log the access attempt before raising exception
            audit_logger.log_access_attempt(
                user_id=token_data.get("sub", "unknown"),
                username=token_data.get("username", "unknown"),
                role=user_role,
                resource_path=request.url.path,
                success=False,
                reason="Insufficient role permissions",
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this resource",
            )

    def _get_required_roles(self, path: str) -> Optional[List[str]]:
        """
        Get required roles for a path.

        Args:
            path: The request path

        Returns:
            Optional[List[str]]: List of required roles, or None if no restrictions
        """
        # Admin-only paths
        if path.startswith("/api/v1/admin/") or path.startswith("/admin-only"):
            return ["admin"]

        # Provider-only paths
        if path.startswith("/api/v1/provider/") or path.startswith("/provider-only"):
            return ["provider", "admin"]

        # Patient-specific paths
        if path.startswith("/api/v1/patients/") or path.startswith("/patient-only"):
            return ["patient", "provider", "admin"]

        # Patient-specific data paths
        if path.startswith("/patient-specific/"):
            return ["patient", "provider", "admin"]

        # Default: no role restriction
        return None

    def _is_phi_access(self, path: str) -> bool:
        """
        Check if the path potentially accesses PHI.

        Args:
            path: The request path

        Returns:
            bool: True if the path potentially accesses PHI
        """
        # Any path that might access PHI should be included here
        phi_paths = [
            "/api/v1/patients",
            "/api/v1/appointments",
            "/api/v1/prescriptions",
            "/api/v1/notes",
            "/api/v1/records",
            "/api/v1/billing",
            "/patient-specific",
        ]

        for phi_path in phi_paths:
            if path.startswith(phi_path):
                return True

        return False

    def _log_phi_access(
        self, request: Request, token_data: Dict[str, Any], status_code: int
    ) -> None:
        """
        Log PHI access for HIPAA compliance.

        Args:
            request: The incoming request
            token_data: The decoded JWT token data
            status_code: The response status code
        """
        # Extract user information from token
        user_id = token_data.get("sub", "unknown")
        username = token_data.get("username", "unknown")
        role = token_data.get("role", "unknown")

        # Determine the action based on request method
        action = request.method

        # Extract resource information from path
        path_parts = request.url.path.strip("/").split("/")
        resource_type = path_parts[0] if len(path_parts) > 0 else "unknown"
        resource_id = path_parts[1] if len(path_parts) > 1 else "unknown"

        # Determine if access was successful
        success = status_code < 400

        # Log the access
        audit_logger.log_access(
            user_id=user_id,
            username=username,
            role=role,
            action=action,
            resource_type=resource_type.upper(),
            resource_id=resource_id,
            ip_address=str(request.client.host) if request.client else None,
            success=success,
            failure_reason=f"HTTP {status_code}" if not success else None,
        )


# Alias for backward compatibility
AuthMiddleware = JWTAuthMiddleware


def get_auth_middleware():
    """
    Factory function to get auth middleware instance with proper DI.

    Returns:
        JWTAuthMiddleware: Auth middleware instance
    """
    return JWTAuthMiddleware
