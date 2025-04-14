#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIPAA-Compliant JWT Authentication Service

This service handles secure authentication using JWT tokens, following HIPAA
security requirements (§164.312(a)(2)(i) - Unique user identification).

Features:
- Secure token creation and validation
- Role-based access control
- Refresh token mechanism
- HIPAA-compliant error handling (no PHI leakage)
- Secure token transmission
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from app.domain.utils.datetime_utils import UTC
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from app.infrastructure.security.jwt_service import JWTService


class AuthenticationError(Exception):
    """Exception raised for authentication-related errors."""
    pass


class TokenValidationError(Exception):
    """Exception raised for token validation errors."""
    pass


class JWTAuthService:
    """
    HIPAA-compliant JWT authentication service adapter.

    This class adapts the JWTService to the interface expected by the HIPAA security tests.
    It delegates most operations to the underlying JWTService.
    """

    def __init__(self):
        """Initialize the JWT auth service."""
        self.jwt_service = JWTService()

    def create_token(self, payload: Dict[str, Any]) -> str:
        """
        Create a JWT token with the given payload.

        Args:
            payload: Token payload data

        Returns:
            str: Encoded JWT token
        """
        # Extract user_id from sub if present
        user_id = payload.get("sub", None)
        if user_id:
            payload["user_id"] = user_id

        # Use the core JWTService to create the token
        return self.jwt_service.create_access_token(payload)

    def decode_token(self, token: str, verify: bool = True) -> Dict[str, Any]:
        """
        Decode a JWT token.

        Args:
            token: JWT token to decode
            verify: Whether to verify the token signature

        Returns:
            Dict[str, Any]: Decoded token payload
        """
        if verify:
            return self.jwt_service.decode_token(token)
        else:
            # For the test case where we just want to decode without verification
            import jwt

            return jwt.decode(token, options={"verify_signature": False})

    def validate_token(self, token: str, leeway: int = 0) -> Dict[str, Any]:
        """
        Validate a JWT token.

        Args:
            token: JWT token to validate
            leeway: Time leeway in seconds for expiration checking

        Returns:
            Dict[str, Any]: Validation result with is_valid flag
        """
        try:
            # Try to verify the token
            token_data = self.jwt_service.verify_token(token)

            return {
                "is_valid": True,
                "user_id": token_data.get("sub"),
                "role": token_data.get("role"),
                "permissions": token_data.get("permissions", []),
            }
        except Exception as e:
            # Return structured error information
            error_message = str(e)
            error_type = "expired" if "expired" in error_message.lower() else "invalid"

            return {"is_valid": False, "error": error_message, "error_type": error_type}

    def check_resource_access(
        self,
        request: Request,
        resource_path: str,
        resource_owner_id: Optional[str] = None,
    ) -> bool:
        """
        Check if the user has access to a resource.

        Args:
            request: FastAPI request object
            resource_path: Path to the resource
            resource_owner_id: ID of the resource owner (for ownership checks)

        Returns:
            bool: True if access is allowed, False otherwise
        """
        # Extract token from request
        token = self.extract_token_from_request(request)
        if not token:
            return False

        # Validate the token
        validation = self.validate_token(token)
        if not validation["is_valid"]:
            return False

        # Extract user data
        user_id = validation["user_id"]
        role = validation["role"]
        permissions = validation["permissions"]

        # Handle resource path-based access control
        if "patients" in resource_path:
            if role == "admin":
                return True
            elif role == "doctor" and "read:patients" in permissions:
                return True
            elif (
                role == "patient" and resource_owner_id and user_id == resource_owner_id
            ):
                return True
        elif "medical_records" in resource_path:
            if role == "admin":
                return True
            elif role == "doctor" and "write:medical_records" in permissions:
                return True
            elif (
                role == "patient" and resource_owner_id and user_id == resource_owner_id
            ):
                return True
        elif "billing" in resource_path:
            if role == "admin":
                return True
            elif resource_owner_id and user_id == resource_owner_id:
                return True
        elif "system_settings" in resource_path:
            return role == "admin"

        return False

    def extract_token_from_request(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from request.

        Args:
            request: FastAPI request object

        Returns:
            Optional[str]: Extracted token or None if not found
        """
        # Try to get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.replace("Bearer ", "")

        # Try to get token from cookies
        token = request.cookies.get("access_token")
        if token:
            return token

        return None

    def create_unauthorized_response(
        self, error_type: str, message: str
    ) -> JSONResponse:
        """
        Create standardized unauthorized response.

        Args:
            error_type: Type of error (token_expired, invalid_token, insufficient_permissions)
            message: Error message

        Returns:
            JSONResponse: JSON response with appropriate status code
        """
        status_code = 401  # Default to unauthorized
        if error_type == "insufficient_permissions":
            status_code = 403  # Forbidden

        # Create HIPAA-compliant response (no user details, generic errors)
        return JSONResponse(
            status_code=status_code,
            content={
                "error": message,
                "error_type": error_type,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    def create_refresh_token(self, user_id: str) -> str:
        """
        Create a refresh token.

        Args:
            user_id: User ID to create token for

        Returns:
            str: Refresh token
        """
        # Create a payload for refresh token
        payload = {
            "user_id": user_id,
            "token_type": "refresh",
            "family_id": str(uuid.uuid4()),
        }

        # Create refresh token
        return self.jwt_service.create_refresh_token(payload)

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token.

        Args:
            refresh_token: Refresh token

        Returns:
            Dict[str, Any]: Success flag and new access token
        """
        try:
            # Validate the refresh token
            payload = self.jwt_service.validate_refresh_token(refresh_token)

            # Create new access token
            tokens = self.jwt_service.refresh_tokens(refresh_token)

            return {"success": True, "access_token": tokens["access_token"]}
        except Exception as e:
            return {"success": False, "error": str(e)}
