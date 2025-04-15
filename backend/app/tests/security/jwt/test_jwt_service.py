# -*- coding: utf-8 -*-
import os
import jwt
import time
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from typing import Any

from app.config.settings import get_settings
from app.infrastructure.security.jwt.jwt_service import JWTService
from app.domain.exceptions import AuthenticationError, TokenExpiredError


@pytest.mark.venv_only()
class TestJWTService:
    """
    Tests for the JWT Service implementation to ensure HIPAA compliance.

    These tests verify:
        1. Proper token creation with minimal PHI
        2. Strict expiration enforcement
        3. Proper role-based permissions
        4. Token validation security
        5. Refresh token handling
    """
    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()
        # Provide a test secret key for JWTService
        self.jwt_service = JWTService(secret_key="test-secret-key-1234567890-abcdef")

    @pytest.fixture
    def user_data(self):
        """Mock user data for token creation."""
        return {
            "user_id": "1234567890",
            "role": "patient",
            # Intentionally excluding PHI like name, email, phone
        }

    @pytest.fixture
    def provider_data(self):
        """Mock provider data for token creation."""
        return {
            "user_id": "0987654321",
            "role": "provider",
            # No PHI included
        }

    def test_create_access_token_no_phi(self):
        """Test that created tokens contain no PHI."""
        # Act
        token = self.jwt_service.create_access_token(self.user_data)

        # Decode without verification to check contents
        decoded = jwt.decode(token, options={"verify_signature": False})

        # Assert
        assert decoded["sub"] == self.user_data["user_id"]
        assert decoded["role"] == self.user_data["role"]
        assert "exp" in decoded

        # Verify no PHI fields were included
        phi_fields = ["name", "email", "dob", "ssn", "address", "phone"]
        for field in phi_fields:
            assert field not in decoded

    def test_create_access_token_expiration(self):
        """Test that tokens have proper expiration times."""
        # Act
        token = self.jwt_service.create_access_token(self.user_data)

        # Decode without verification to check contents
        decoded = jwt.decode(token, options={"verify_signature": False})

        # Assert expiration is properly set (15 minutes from now, +/- 10 seconds for test timing)
        expected_exp = datetime.now(settings.timezone) + timedelta(minutes=15)
        actual_exp = datetime.utcfromtimestamp(decoded["exp"])
        difference = abs((expected_exp - actual_exp).total_seconds())

        assert difference < 10, "Token expiration should be ~15 minutes"

    def test_verify_token_valid(self):
        """Test that valid tokens are properly verified."""
        # Arrange
        token = self.jwt_service.create_access_token(self.user_data)

        # Act
        payload = self.jwt_service.verify_token(token)

        # Assert
        assert payload["sub"] == self.user_data["user_id"]
        assert payload["role"] == self.user_data["role"]

    def test_verify_token_expired(self):
        """Test that expired tokens are rejected."""
        # Arrange
        # Create a token that's already expired by setting a custom exp
        with patch.object(self.jwt_service, '_get_expiration_time') as mock_exp:
            # Set expiration to 1 second ago
            mock_exp.return_value = datetime.now(settings.timezone) - timedelta(seconds=1)
            expired_token = self.jwt_service.create_access_token(self.user_data)

        # Act/Assert
        with pytest.raises(TokenExpiredError):
            self.jwt_service.verify_token(expired_token)

    def test_verify_token_invalid_signature(self):
        """Test that tokens with invalid signatures are rejected."""
        # Arrange
        token = self.jwt_service.create_access_token(self.user_data)

        # Tamper with the token by changing a character
        tampered_token = token[:-5] + "X" + token[-4:]

        # Act/Assert
        with pytest.raises(AuthenticationError):
            self.jwt_service.verify_token(tampered_token)

    def test_verify_token_invalid_format(self):
        """Test that tokens with invalid format are rejected."""
        # Arrange
        invalid_token = "not.a.token"

        # Act/Assert
        with pytest.raises(AuthenticationError):
            self.jwt_service.verify_token(invalid_token)

    def test_admin_role_permissions(self):
        """Test that admin tokens contain appropriate permissions."""
        # Arrange
        admin_data = {
            "user_id": "admin123",
            "role": "admin"
        }

        # Act
        token = self.jwt_service.create_access_token(admin_data)
        payload = self.jwt_service.verify_token(token)

        # Assert
        assert payload["role"] == "admin"
        assert self.jwt_service.has_role(token, "admin")
        # Admin inherits provider permissions
        assert self.jwt_service.has_role(token, "provider")
        # Admin inherits patient permissions
        assert self.jwt_service.has_role(token, "patient")

    def test_provider_role_permissions(self):
        """Test that provider tokens have appropriate permissions."""
        # Act
        token = self.jwt_service.create_access_token(self.provider_data)

        # Assert
        assert self.jwt_service.has_role(token, "provider")
        # Providers can access patient resources
        assert self.jwt_service.has_role(token, "patient")
        # Providers can't access admin resources
        assert not self.jwt_service.has_role(token, "admin")

    def test_patient_role_permissions(self):
        """Test that patient tokens have limited permissions."""
        # Act
        token = self.jwt_service.create_access_token(self.user_data)

        # Assert
        assert self.jwt_service.has_role(token, "patient")
        # Patients can't access provider resources
        assert not self.jwt_service.has_role(token, "provider")
        # Patients can't access admin resources
        assert not self.jwt_service.has_role(token, "admin")

    def test_refresh_token_rotation(self):
        """Test that refresh tokens are properly rotated for security."""
        # Arrange
        refresh_token = self.jwt_service.create_refresh_token(self.user_data)

        # Act
        new_tokens = self.jwt_service.refresh_tokens(refresh_token)

        # Assert
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["refresh_token"] != refresh_token  # Verify rotation

        # Verify old refresh token is invalidated
        with pytest.raises(AuthenticationError):
            self.jwt_service.refresh_tokens(refresh_token)

    def test_refresh_token_family_tracking(self):
        """Test that refresh token families are tracked for breach detection."""
        # This test ensures we're following NIST recommendations for detecting
        # token theft by tracking token families

        # Arrange
        refresh_token = self.jwt_service.create_refresh_token(self.user_data)

        # Act - Create a chain of refresh tokens
        new_tokens1 = self.jwt_service.refresh_tokens(refresh_token)
        new_tokens2 = self.jwt_service.refresh_tokens(new_tokens1["refresh_token"])

        # Assert - Verify parallel use of any token in chain is rejected
        # (indicates theft)
        with pytest.raises(AuthenticationError):
            self.jwt_service.refresh_tokens(refresh_token)

        with pytest.raises(AuthenticationError):
            self.jwt_service.refresh_tokens(new_tokens1["refresh_token"])

        # Only the most recent token should work
        assert self.jwt_service.refresh_tokens(new_tokens2["refresh_token"]) is not None

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
