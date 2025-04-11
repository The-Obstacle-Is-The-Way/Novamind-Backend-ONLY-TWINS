# -*- coding: utf-8 -*-
import os
import jwt
import time
import pytest
from datetime import datetime, UTC, UTC, timedelta
from unittest.mock import MagicMock, patch

from app.infrastructure.security.jwt_service import JWTService
, from app.core.config import settings
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
    
    @pytest.fixture
    def jwt_service(self):
        """Create a JWTService instance for testing."""
        return JWTService()
    
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
    
    def test_create_access_token_no_phi(self, jwt_service, user_data):
        """Test that created tokens contain no PHI."""
        # Act
        token = jwt_service.create_access_token(user_data)
        
        # Decode without verification to check contents
        decoded = jwt.decode(
            token, 
            options={"verify_signature": False}
        )
        
        # Assert
        assert decoded["sub"] == user_data["user_id"]
        assert decoded["role"] == user_data["role"]
        assert "exp" in decoded
        
        # Verify no PHI fields were included
        phi_fields = ["name", "email", "dob", "ssn", "address", "phone"]
        for field in phi_fields:
            assert field not in decoded
    
    def test_create_access_token_expiration(self, jwt_service, user_data):
        """Test that tokens have proper expiration times."""
        # Act
        token = jwt_service.create_access_token(user_data)
        
        # Decode without verification to check contents
        decoded = jwt.decode(
            token, 
            options={"verify_signature": False}
        )
        
        # Assert expiration is properly set (15 minutes from now, +/- 10 seconds for test timing)
        expected_exp = datetime.now(UTC) + timedelta(minutes=15)
        actual_exp = datetime.utcfromtimestamp(decoded["exp"])
        difference = abs((expected_exp - actual_exp).total_seconds())
        
        assert difference < 10, "Token expiration should be ~15 minutes"
    
    def test_verify_token_valid(self, jwt_service, user_data):
        """Test that valid tokens are properly verified."""
        # Arrange
        token = jwt_service.create_access_token(user_data)
        
        # Act
        payload = jwt_service.verify_token(token)
        
        # Assert
        assert payload["sub"] == user_data["user_id"]
        assert payload["role"] == user_data["role"]
    
    def test_verify_token_expired(self, jwt_service, user_data):
        """Test that expired tokens are rejected."""
        # Arrange
        # Create a token that's already expired by setting a custom exp
        with patch.object(jwt_service, '_get_expiration_time') as mock_exp:
            # Set expiration to 1 second ago
            mock_exp.return_value = datetime.now(UTC) - timedelta(seconds=1)
            expired_token = jwt_service.create_access_token(user_data)
        
        # Act/Assert
        with pytest.raises(TokenExpiredError):
            jwt_service.verify_token(expired_token)
    
    def test_verify_token_invalid_signature(self, jwt_service, user_data):
        """Test that tokens with invalid signatures are rejected."""
        # Arrange
        token = jwt_service.create_access_token(user_data)
        
        # Tamper with the token by changing a character
        tampered_token = token[:-5] + "X" + token[-4:]
        
        # Act/Assert
        with pytest.raises(AuthenticationError):
            jwt_service.verify_token(tampered_token)
    
    def test_verify_token_invalid_format(self, jwt_service):
        """Test that tokens with invalid format are rejected."""
        # Arrange
        invalid_token = "not.a.token"
        
        # Act/Assert
        with pytest.raises(AuthenticationError):
            jwt_service.verify_token(invalid_token)
    
    def test_admin_role_permissions(self, jwt_service):
        """Test that admin tokens contain appropriate permissions."""
        # Arrange
        admin_data = {
            "user_id": "admin123",
            "role": "admin"
        }
        
        # Act
        token = jwt_service.create_access_token(admin_data)
        payload = jwt_service.verify_token(token)
        
        # Assert
        assert payload["role"] == "admin"
        assert jwt_service.has_role(token, "admin")
        assert jwt_service.has_role(token, "provider")  # Admin inherits provider permissions
        assert jwt_service.has_role(token, "patient")   # Admin inherits patient permissions
    
    def test_provider_role_permissions(self, jwt_service, provider_data):
        """Test that provider tokens have appropriate permissions."""
        # Act
        token = jwt_service.create_access_token(provider_data)
        
        # Assert
        assert jwt_service.has_role(token, "provider")
        assert jwt_service.has_role(token, "patient")  # Providers can access patient resources
        assert not jwt_service.has_role(token, "admin")  # Providers can't access admin resources
    
    def test_patient_role_permissions(self, jwt_service, user_data):
        """Test that patient tokens have limited permissions."""
        # Act
        token = jwt_service.create_access_token(user_data)
        
        # Assert
        assert jwt_service.has_role(token, "patient")
        assert not jwt_service.has_role(token, "provider")  # Patients can't access provider resources
        assert not jwt_service.has_role(token, "admin")     # Patients can't access admin resources
    
    def test_refresh_token_rotation(self, jwt_service, user_data):
        """Test that refresh tokens are properly rotated for security."""
        # Arrange
        refresh_token = jwt_service.create_refresh_token(user_data)
        
        # Act
        new_tokens = jwt_service.refresh_tokens(refresh_token)
        
        # Assert
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["refresh_token"] != refresh_token  # Verify rotation
        
        # Verify old refresh token is invalidated
        with pytest.raises(AuthenticationError):
            jwt_service.refresh_tokens(refresh_token)
    
    def test_refresh_token_family_tracking(self, jwt_service, user_data):
        """Test that refresh token families are tracked for breach detection."""
        # This test ensures we're following NIST recommendations for detecting
        # token theft by tracking token families
        
        # Arrange
        refresh_token = jwt_service.create_refresh_token(user_data)
        
        # Act - Create a chain of refresh tokens
        new_tokens1 = jwt_service.refresh_tokens(refresh_token)
        new_tokens2 = jwt_service.refresh_tokens(new_tokens1["refresh_token"])
        
        # Assert - Verify parallel use of any token in chain is rejected (indicates theft)
        with pytest.raises(AuthenticationError):
            jwt_service.refresh_tokens(refresh_token)
        
        with pytest.raises(AuthenticationError):
            jwt_service.refresh_tokens(new_tokens1["refresh_token"])
        
        # Only the most recent token should work
        assert jwt_service.refresh_tokens(new_tokens2["refresh_token"]) is not None


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])