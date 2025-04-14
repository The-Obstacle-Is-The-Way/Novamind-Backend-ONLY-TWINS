# -*- coding: utf-8 -*-
"""
Unit tests for JWT Token Handler.

These tests verify that our JWT token generation, validation, and handling
meet HIPAA security requirements.
"""

import pytest
import time
from datetime import datetime, timedelta, timezone # Corrected import
from unittest.mock import patch, MagicMock

from jose import jwt, JWTError

from app.infrastructure.security.jwt.token_handler import JWTHandler, TokenPayload
from app.domain.exceptions import AuthenticationError # Assuming correct exception name

# Define UTC if not imported elsewhere (Python 3.11+)
try:
    from datetime import UTC # Use standard UTC if available
except ImportError:
    UTC = timezone.utc # Fallback for older Python versions


@pytest.fixture
def jwt_handler():
    """
    Create a JWT handler with test settings.

    Returns:
        JWTHandler instance with test configuration
    """
    return JWTHandler(
        secret_key="testkey12345678901234567890123456789", # Ensure sufficient length
        algorithm="HS256",
        access_token_expire_minutes=15
    )

# Removed misplaced decorator @pytest.mark.db_required() from class definition
class TestJWTHandler:
    """Test suite for JWT token handler."""

    def test_init_with_valid_settings(self):
        """Test initialization with valid settings."""
        handler = JWTHandler(
            secret_key="testkey12345678901234567890123456789",
            algorithm="HS256",
            access_token_expire_minutes=15
        )
        assert handler.secret_key == "testkey12345678901234567890123456789"
        assert handler.algorithm == "HS256"
        assert handler.access_token_expire_minutes == 15

    def test_init_with_invalid_secret_key(self):
        """Test initialization with invalid secret key."""
        with pytest.raises(ValueError, match="JWT secret key is missing or too short"):
            JWTHandler(secret_key="short", algorithm="HS256")

    def test_create_access_token(self, jwt_handler: JWTHandler):
        """Test creating an access token."""
        # Arrange
        user_id = "user123"
        role = "patient"
        permissions = ["read:profile", "update:profile"]
        session_id = "session123"

        # Act
        token = jwt_handler.create_access_token(
            user_id=user_id,
            role=role,
            permissions=permissions,
            session_id=session_id
        )

        # Assert
        decoded = jwt.decode(
            token,
            jwt_handler.secret_key,
            algorithms=[jwt_handler.algorithm]
        )
        assert decoded["sub"] == user_id
        assert decoded["role"] == role
        assert decoded["permissions"] == permissions
        assert decoded["session_id"] == session_id
        assert "exp" in decoded
        assert "iat" in decoded

    def test_create_access_token_with_custom_expiry(self, jwt_handler: JWTHandler):
        """Test creating an access token with custom expiration."""
        # Arrange
        user_id = "user123"
        role = "doctor"
        permissions = ["read:patients", "update:patients"]
        session_id = "session456"
        expires_delta = timedelta(hours=1)

        # Act
        token = jwt_handler.create_access_token(
            user_id=user_id,
            role=role,
            permissions=permissions,
            session_id=session_id,
            expires_delta=expires_delta
        )

        # Assert
        decoded = jwt.decode(
            token,
            jwt_handler.secret_key,
            algorithms=[jwt_handler.algorithm]
        )
        # Verify expiration is approximately 1 hour from now
        exp_time = datetime.fromtimestamp(decoded["exp"], UTC) # Use UTC timezone
        now = datetime.now(UTC)
        # Corrected assertion syntax
        assert abs((exp_time - now).total_seconds() - 3600) < 10  # Within 10 seconds of 1 hour

    def test_verify_token_valid(self, jwt_handler: JWTHandler):
        """Test verifying a valid token."""
        # Arrange
        user_id = "user123"
        role = "patient"
        permissions = ["read:profile"]
        session_id = "session123"
        token = jwt_handler.create_access_token(
            user_id=user_id,
            role=role,
            permissions=permissions,
            session_id=session_id
        )

        # Act
        token_data = jwt_handler.verify_token(token)

        # Assert
        assert isinstance(token_data, TokenPayload) # Check type
        assert token_data.sub == user_id
        assert token_data.role == role
        assert token_data.permissions == permissions
        assert token_data.session_id == session_id

    def test_verify_token_expired(self, jwt_handler: JWTHandler):
        """Test verifying an expired token."""
        # Arrange
        user_id = "user123"
        role = "patient"
        permissions = ["read:profile"]
        session_id = "session123"
        # Create payload with expiration in the past
        to_encode = {
            "sub": user_id,
            "exp": datetime.now(UTC) - timedelta(minutes=5),
            "iat": datetime.now(UTC) - timedelta(minutes=10),
            "role": role,
            "permissions": permissions,
            "session_id": session_id
        }
        # Create token directly using jose.jwt.encode
        token = jwt.encode(
            to_encode,
            jwt_handler.secret_key,
            algorithm=jwt_handler.algorithm
        )

        # Act & Assert
        with pytest.raises(AuthenticationError, match="Token has expired"):
            jwt_handler.verify_token(token)

    def test_verify_token_invalid_signature(self, jwt_handler: JWTHandler):
        """Test verifying a token with invalid signature."""
        # Arrange
        user_id = "user123"
        role = "patient"
        permissions = ["read:profile"]
        session_id = "session123"
        wrong_key = "wrongkey123456789012345678901234567" # Different key
        to_encode = {
            "sub": user_id,
            "exp": datetime.now(UTC) + timedelta(minutes=15),
            "iat": datetime.now(UTC),
            "role": role,
            "permissions": permissions,
            "session_id": session_id
        }
        # Encode with the wrong key
        token = jwt.encode(to_encode, wrong_key, algorithm="HS256")

        # Act & Assert
        with pytest.raises(AuthenticationError, match="Invalid authentication token"):
            jwt_handler.verify_token(token)

    def test_verify_token_malformed(self, jwt_handler: JWTHandler):
        """Test verifying a malformed token."""
        # Arrange
        token = "not.a.valid.token"

        # Act & Assert
        with pytest.raises(AuthenticationError, match="Invalid authentication token"):
            jwt_handler.verify_token(token)

    def test_refresh_token(self, jwt_handler: JWTHandler):
        """Test refreshing a token."""
        # Arrange
        user_id = "user123"
        role = "patient"
        permissions = ["read:profile"]
        session_id = "session123"
        original_token = jwt_handler.create_access_token(
            user_id=user_id,
            role=role,
            permissions=permissions,
            session_id=session_id
        )
        # Wait a second to ensure timestamps differ
        time.sleep(1)

        # Act
        new_token = jwt_handler.refresh_token(original_token, extend_minutes=30)

        # Decode both tokens
        original_payload = jwt.decode(
            original_token,
            jwt_handler.secret_key,
            algorithms=[jwt_handler.algorithm]
        )
        new_payload = jwt.decode(
            new_token,
            jwt_handler.secret_key,
            algorithms=[jwt_handler.algorithm]
        )

        # Assert
        assert new_payload["sub"] == original_payload["sub"]
        assert new_payload["role"] == original_payload["role"]
        assert new_payload["permissions"] == original_payload["permissions"]
        assert new_payload["session_id"] == original_payload["session_id"]
        assert new_payload["exp"] > original_payload["exp"]
        assert new_payload["iat"] > original_payload["iat"]
        # Check new expiry is roughly 30 mins from original expiry
        original_exp_dt = datetime.fromtimestamp(original_payload["exp"], UTC)
        new_exp_dt = datetime.fromtimestamp(new_payload["exp"], UTC)
        assert abs((new_exp_dt - original_exp_dt).total_seconds() - (30 * 60)) < 10


    def test_refresh_token_expired(self, jwt_handler: JWTHandler):
        """Test refreshing an expired token."""
        # Arrange
        user_id = "user123"
        role = "patient"
        permissions = ["read:profile"]
        session_id = "session123"
        to_encode = {
            "sub": user_id,
            "exp": datetime.now(UTC) - timedelta(minutes=5), # Expired
            "iat": datetime.now(UTC) - timedelta(minutes=10),
            "role": role,
            "permissions": permissions,
            "session_id": session_id
        }
        token = jwt.encode(
            to_encode,
            jwt_handler.secret_key,
            algorithm=jwt_handler.algorithm
        )

        # Act & Assert
        with pytest.raises(AuthenticationError, match="Token has expired"):
            jwt_handler.refresh_token(token)

    def test_get_user_id_from_token(self, jwt_handler: JWTHandler):
        """Test extracting user ID from token."""
        # Arrange
        user_id = "user123"
        role = "patient"
        permissions = ["read:profile"]
        session_id = "session123"
        token = jwt_handler.create_access_token(
            user_id=user_id,
            role=role,
            permissions=permissions,
            session_id=session_id
        )

        # Act
        extracted_user_id = jwt_handler.get_user_id_from_token(token)

        # Assert
        assert extracted_user_id == user_id

    def test_get_permissions_from_token(self, jwt_handler: JWTHandler):
        """Test extracting permissions from token."""
        # Arrange
        user_id = "user123"
        role = "doctor"
        permissions = ["read:patients", "update:patients", "read:billing"]
        session_id = "session123"
        token = jwt_handler.create_access_token(
            user_id=user_id,
            role=role,
            permissions=permissions,
            session_id=session_id
        )

        # Act
        extracted_permissions = jwt_handler.get_permissions_from_token(token)

        # Assert
        assert extracted_permissions == permissions

    def test_get_role_from_token(self, jwt_handler: JWTHandler):
        """Test extracting role from token."""
        # Arrange
        user_id = "user123"
        role = "admin"
        permissions = ["read:all", "update:all"]
        session_id = "session123"
        token = jwt_handler.create_access_token(
            user_id=user_id,
            role=role,
            permissions=permissions,
            session_id=session_id
        )

        # Act
        extracted_role = jwt_handler.get_role_from_token(token)

        # Assert
        assert extracted_role == role

    @patch('app.infrastructure.security.jwt.token_handler.logger')
    def test_logging_behavior(self, mock_logger: MagicMock, jwt_handler: JWTHandler):
        """Test that sensitive information is not logged."""
        # Arrange
        user_id = "user123"
        role = "patient"
        permissions = ["read:profile"]
        session_id = "session123"

        # Act
        token = jwt_handler.create_access_token(
            user_id=user_id,
            role=role,
            permissions=permissions,
            session_id=session_id
        )
        # Call verify which might log
        try:
            jwt_handler.verify_token(token)
        except AuthenticationError:
            pass # Ignore potential errors for logging test

        # Assert logger was called (if logging is implemented) but didn't contain the token
        # This depends heavily on the actual logging implementation
        # Example: Check if info was called
        # mock_logger.info.assert_called()
        # Example: Check log messages don't contain the full token
        for call_args in mock_logger.info.call_args_list:
            log_message = call_args[0][0] # Get the first argument of the call
            assert token not in log_message
            # Assert that user_id might be present if intended
            # assert user_id in log_message
