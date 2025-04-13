# -*- coding: utf-8 -*-
"""
NOVAMIND Authentication Utility
==============================
JWT token generation and validation with role-based access control.
Implements HIPAA-compliant authentication for the NOVAMIND platform.
"""

import hashlib
import os
import time
import uuid
from datetime import datetime, , UTC, timedelta
from app.domain.utils.datetime_utils import UTC
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import jwt

from ..config import settings
from .encryption import EncryptionService


class Role:
    """User roles for role-based access control."""

    ADMIN = "admin"
    PROVIDER = "provider"
    PATIENT = "patient"
    STAFF = "staff"
    RESEARCHER = "researcher"


class Permission:
    """Permission types for fine-grained access control."""

    # Patient data permissions
    VIEW_PATIENT = "view_patient"
    EDIT_PATIENT = "edit_patient"
    CREATE_PATIENT = "create_patient"
    DELETE_PATIENT = "delete_patient"

    # Provider permissions
    VIEW_PROVIDER = "view_provider"
    EDIT_PROVIDER = "edit_provider"
    CREATE_PROVIDER = "create_provider"
    DELETE_PROVIDER = "delete_provider"

    # Medical record permissions
    VIEW_RECORD = "view_record"
    EDIT_RECORD = "edit_record"
    CREATE_RECORD = "create_record"
    DELETE_RECORD = "delete_record"

    # Prescription permissions
    VIEW_PRESCRIPTION = "view_prescription"
    EDIT_PRESCRIPTION = "edit_prescription"
    CREATE_PRESCRIPTION = "create_prescription"
    DELETE_PRESCRIPTION = "delete_prescription"

    # Administrative permissions
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    VIEW_AUDIT_LOGS = "view_audit_logs"

    # Research permissions
    ACCESS_ANONYMIZED_DATA = "access_anonymized_data"
    RUN_ANALYTICS = "run_analytics"


# Role to permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.VIEW_PATIENT,
        Permission.EDIT_PATIENT,
        Permission.CREATE_PATIENT,
        Permission.DELETE_PATIENT,
        Permission.VIEW_PROVIDER,
        Permission.EDIT_PROVIDER,
        Permission.CREATE_PROVIDER,
        Permission.DELETE_PROVIDER,
        Permission.VIEW_RECORD,
        Permission.EDIT_RECORD,
        Permission.CREATE_RECORD,
        Permission.DELETE_RECORD,
        Permission.VIEW_PRESCRIPTION,
        Permission.EDIT_PRESCRIPTION,
        Permission.CREATE_PRESCRIPTION,
        Permission.DELETE_PRESCRIPTION,
        Permission.MANAGE_USERS,
        Permission.MANAGE_SYSTEM,
        Permission.VIEW_AUDIT_LOGS,
        Permission.ACCESS_ANONYMIZED_DATA,
        Permission.RUN_ANALYTICS,
    ],
    Role.PROVIDER: [
        Permission.VIEW_PATIENT,
        Permission.EDIT_PATIENT,
        Permission.CREATE_PATIENT,
        Permission.VIEW_PROVIDER,
        Permission.VIEW_RECORD,
        Permission.EDIT_RECORD,
        Permission.CREATE_RECORD,
        Permission.VIEW_PRESCRIPTION,
        Permission.EDIT_PRESCRIPTION,
        Permission.CREATE_PRESCRIPTION,
        Permission.ACCESS_ANONYMIZED_DATA,
        Permission.RUN_ANALYTICS,
    ],
    Role.PATIENT: [
        Permission.VIEW_PATIENT,  # Can only view their own data
        Permission.VIEW_RECORD,  # Can only view their own records
        Permission.VIEW_PRESCRIPTION,  # Can only view their own prescriptions
    ],
    Role.STAFF: [
        Permission.VIEW_PATIENT,
        Permission.EDIT_PATIENT,
        Permission.CREATE_PATIENT,
        Permission.VIEW_PROVIDER,
        Permission.VIEW_RECORD,
        Permission.VIEW_PRESCRIPTION,
    ],
    Role.RESEARCHER: [Permission.ACCESS_ANONYMIZED_DATA, Permission.RUN_ANALYTICS],
}


class AuthenticationService:
    """
    HIPAA-compliant authentication service for the NOVAMIND platform.
    Handles JWT token generation, validation, and access control.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        token_expire_minutes: Optional[int] = None,
        encryption_service: Optional[EncryptionService] = None,
    ):
        """
        Initialize the authentication service.

        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT signing algorithm
            token_expire_minutes: Token expiration time in minutes
            encryption_service: Encryption service for password hashing
        """
        self.secret_key = secret_key or settings.security.JWT_SECRET_KEY
        if not self.secret_key:
            raise ValueError("JWT secret key not provided and not found in settings")

        self.algorithm = algorithm or settings.security.JWT_ALGORITHM
        self.token_expire_minutes = (
            token_expire_minutes or settings.security.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        self.encryption_service = encryption_service or EncryptionService()

    def create_access_token(
        self,
        user_id: str,
        roles: List[str],
        additional_data: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT access token for a user.

        Args:
            user_id: User ID to include in the token
            roles: List of user roles
            additional_data: Additional data to include in the token
            expires_delta: Custom expiration time

        Returns:
            JWT token string
        """
        # Set expiration time
        expires_delta = expires_delta or timedelta(minutes=self.token_expire_minutes)
        expire = datetime.now(UTC) + expires_delta

        # Create token payload
        payload = {
            "sub": str(user_id),
            "roles": roles,
            "exp": expire,
            "iat": datetime.now(UTC),
            "jti": str(uuid.uuid4()),
        }

        # Add additional data if provided
        if additional_data:
            for key, value in additional_data.items():
                if key not in payload:
                    payload[key] = value

        # Create token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        return token

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token to decode

        Returns:
            Decoded token payload

        Raises:
            jwt.PyJWTError: If token is invalid
        """
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a JWT token and return its payload if valid.

        Args:
            token: JWT token to validate

        Returns:
            Tuple of (is_valid, payload)
        """
        try:
            payload = self.decode_token(token)
            return True, payload
        except jwt.PyJWTError:
            return False, None

    def has_role(self, token: str, required_role: str) -> bool:
        """
        Check if a token has a specific role.

        Args:
            token: JWT token to check
            required_role: Role to check for

        Returns:
            True if token has the required role, False otherwise
        """
        is_valid, payload = self.validate_token(token)
        if not is_valid or not payload:
            return False

        roles = payload.get("roles", [])
        return required_role in roles

    def has_permission(self, token: str, required_permission: str) -> bool:
        """
        Check if a token has a specific permission.

        Args:
            token: JWT token to check
            required_permission: Permission to check for

        Returns:
            True if token has the required permission, False otherwise
        """
        is_valid, payload = self.validate_token(token)
        if not is_valid or not payload:
            return False

        roles = payload.get("roles", [])

        # Check if any of the user's roles grant the required permission
        for role in roles:
            if (
                role in ROLE_PERMISSIONS
                and required_permission in ROLE_PERMISSIONS[role]
            ):
                return True

        return False

    def hash_password(self, password: str) -> Tuple[str, bytes]:
        """
        Hash a password securely.

        Args:
            password: Password to hash

        Returns:
            Tuple of (password_hash, salt)
        """
        return self.encryption_service.generate_hash(password)

    def verify_password(self, password: str, password_hash: str, salt: bytes) -> bool:
        """
        Verify a password against a hash.

        Args:
            password: Password to verify
            password_hash: Expected hash
            salt: Salt used for hashing

        Returns:
            True if password matches hash, False otherwise
        """
        return self.encryption_service.verify_hash(password, password_hash, salt)

    def can_access_patient_data(self, token: str, patient_id: str) -> bool:
        """
        Check if a token can access a specific patient's data.

        Args:
            token: JWT token to check
            patient_id: ID of the patient whose data is being accessed

        Returns:
            True if access is allowed, False otherwise
        """
        is_valid, payload = self.validate_token(token)
        if not is_valid or not payload:
            return False

        user_id = payload.get("sub")
        roles = payload.get("roles", [])

        # Patients can only access their own data
        if Role.PATIENT in roles and user_id != patient_id:
            return False

        # Providers, staff, and admins can access any patient data
        if any(role in [Role.PROVIDER, Role.STAFF, Role.ADMIN] for role in roles):
            return True

        # Researchers can only access anonymized data, not specific patient data
        if Role.RESEARCHER in roles:
            return False

        return False


# Create a default authentication service
default_auth_service = AuthenticationService()
