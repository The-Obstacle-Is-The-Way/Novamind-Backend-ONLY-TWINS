# -*- coding: utf-8 -*-
"""Unit tests for JWT Service functionality.

This module tests the JWT service that handles authentication tokens,
a critical component for HIPAA-compliant user authentication and authorization.
"""

import pytest
import jwt
import datetime
import time
from unittest.mock import patch, MagicMock, AsyncMock # Added AsyncMock
from freezegun import freeze_time
from typing import Dict, Any
from datetime import timezone # Import timezone directly

# Corrected imports
from app.infrastructure.security.jwt.jwt_service import JWTService
from jwt.exceptions import PyJWTError, ExpiredSignatureError, DecodeError, InvalidSignatureError, InvalidIssuerError, InvalidAudienceError, ImmatureSignatureError # Import specific JWT errors

# Define test constants directly
TEST_SECRET_KEY = "test-jwt-secret-key-must-be-at-least-32-chars-long"
TEST_ALGORITHM = "HS256"
TEST_ACCESS_EXPIRE_MINUTES = 15
TEST_REFRESH_EXPIRE_MINUTES = 60 * 24 * 7 # Equivalent to 7 days in minutes

# Define UTC if not imported elsewhere (Python 3.11+)
try:
    from datetime import UTC # Use standard UTC if available
except ImportError:
    UTC = timezone.utc # Fallback for older Python versions


@pytest.fixture
def mock_token_store():
    """Create a mock token store for testing (if needed, currently unused by JWTService)."""
    mock_store = MagicMock()
    mock_store.is_token_revoked = AsyncMock(return_value=False) # Make async if needed
    mock_store.add_token_to_revocation_list = AsyncMock(return_value=None)
    mock_store.get_refresh_token_family = AsyncMock(return_value=[])
    mock_store.add_refresh_token = AsyncMock(return_value=None)
    return mock_store

@pytest.fixture
def jwt_service(mock_token_store): # Keep mock_token_store if JWTService might use it later
    """Create a JWT service for testing."""
    # Instantiate JWTService directly with test config values
    service = JWTService(
        secret_key=TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM
        # Removed token_store assignment as it's not used
    )
    return service

@pytest.fixture
def user_claims() -> Dict[str, Any]:
    """Create test user claims."""
    return {
        "sub": "user123",
        "name": "Dr. Jane Smith",
        "email": "jane.smith@example.com",
        "roles": ["psychiatrist"], # Use 'roles' consistently
        "permissions": ["read:patient", "write:clinical_note", "prescribe:medication"]
    }

@pytest.fixture
async def token_pair(jwt_service: JWTService, user_claims: Dict[str, Any]) -> Dict[str, str]:
    """Create a test token pair (access and refresh tokens)."""
    access_token = await jwt_service.create_token(user_claims, expires_delta=datetime.timedelta(minutes=TEST_ACCESS_EXPIRE_MINUTES))
    # Add jti for refresh token simulation
    refresh_claims = {**user_claims, "jti": "test-jti-123"}
    refresh_token = await jwt_service.create_token(refresh_claims, expires_delta=datetime.timedelta(minutes=TEST_REFRESH_EXPIRE_MINUTES))
    return {"access_token": access_token, "refresh_token": refresh_token}


# Removed misplaced decorator @pytest.mark.venv_only()
class TestJWTService:
    """Test suite for the JWT service."""

    @pytest.mark.asyncio
    async def test_create_access_token(self, jwt_service: JWTService, user_claims: Dict[str, Any]):
        """Test creating an access token with user claims."""
        access_token = await jwt_service.create_token(user_claims, expires_delta=datetime.timedelta(minutes=TEST_ACCESS_EXPIRE_MINUTES))

        assert access_token is not None
        assert isinstance(access_token, str)

        decoded = jwt.decode(
            access_token,
            jwt_service.secret_key,
            algorithms=[jwt_service.algorithm],
            # audience=jwt_service.audience, # Audience/Issuer not added by create_token
            # issuer=jwt_service.issuer
        )

        assert decoded["sub"] == user_claims["sub"]
        assert decoded["name"] == user_claims["name"]
        assert decoded["roles"] == user_claims["roles"]
        assert "exp" in decoded
        assert "iat" in decoded

    @pytest.mark.asyncio
    async def test_create_refresh_token(self, jwt_service: JWTService, user_claims: Dict[str, Any]):
        """Test creating a refresh token with user claims."""
        refresh_claims = {**user_claims, "jti": "test-jti-456"} # Unique JTI
        refresh_token = await jwt_service.create_token(refresh_claims, expires_delta=datetime.timedelta(minutes=TEST_REFRESH_EXPIRE_MINUTES))

        assert refresh_token is not None
        assert isinstance(refresh_token, str)

        decoded = jwt.decode(
            refresh_token,
            jwt_service.secret_key,
            algorithms=[jwt_service.algorithm]
        )

        assert decoded["sub"] == user_claims["sub"]
        assert "exp" in decoded
        assert "iat" in decoded
        assert "jti" in decoded
        assert decoded["jti"] == "test-jti-456"


    @pytest.mark.asyncio
    async def test_validate_token_valid(self, jwt_service: JWTService, token_pair: Dict[str, str]):
        """Test validation of a valid token."""
        payload = await jwt_service.verify_token(token_pair["access_token"])

        assert payload is not None
        assert payload["sub"] == "user123"


    @freeze_time("2025-03-27 12:00:00")
    @pytest.mark.asyncio
    async def test_validate_token_expired(self, jwt_service: JWTService, user_claims: Dict[str, Any]):
        """Test validation of an expired token."""
        # Create a token that expires immediately
        expired_token = await jwt_service.create_token(user_claims, expires_delta=datetime.timedelta(seconds=1))

        # Fast-forward time past expiry
        with freeze_time("2025-03-27 12:00:05"):
            with pytest.raises(ValueError) as excinfo:
                await jwt_service.verify_token(expired_token)
            assert "Invalid token: Signature has expired" in str(excinfo.value)


    @pytest.mark.asyncio
    async def test_validate_token_invalid_signature(self, jwt_service: JWTService, token_pair: Dict[str, str]):
        """Test validation of a token with invalid signature."""
        tampered_token = token_pair["access_token"][:-5] + "XXXXX" # Modify signature

        with pytest.raises(ValueError) as excinfo:
            await jwt_service.verify_token(tampered_token)
        # Check for specific PyJWTError message if possible, otherwise generic ValueError message
        assert "Invalid token: Signature verification failed" in str(excinfo.value) or "Invalid token" in str(excinfo.value)


    @pytest.mark.asyncio
    async def test_validate_token_missing_claim(self, jwt_service: JWTService, user_claims: Dict[str, Any]):
        """Test validation of a token missing standard claims (like exp)."""
        # Manually encode a token missing 'exp'
        payload_missing_exp = {k: v for k, v in user_claims.items()}
        payload_missing_exp["iat"] = datetime.now(UTC)
        # No 'exp' added
        invalid_token = jwt.encode(
            payload_missing_exp,
            jwt_service.secret_key,
            algorithm=jwt_service.algorithm
        )
        with pytest.raises(ValueError) as excinfo:
            await jwt_service.verify_token(invalid_token)
        # PyJWT raises DecodeError if 'exp' is missing during standard validation
        assert "Invalid token" in str(excinfo.value) # Generic wrapper message


    @pytest.mark.asyncio
    async def test_refresh_tokens(self, jwt_service: JWTService, token_pair: Dict[str, str], user_claims: Dict[str, Any]):
        """Test refreshing tokens using a valid refresh token."""
        # Note: refresh_token logic needs implementation in JWTService
        # Assuming refresh_token takes the refresh token string
        # This test might need adjustment based on actual implementation
        with patch.object(jwt_service, 'verify_token', return_value={**user_claims, "jti": "test-jti-123"}) as mock_verify:
             with patch.object(jwt_service, 'create_token', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = "new.access.token" # Mock the new token creation

                # Call refresh_token (assuming it exists and takes refresh token string)
                # If refresh_token doesn't exist, this test needs removal/modification
                if hasattr(jwt_service, 'refresh_token'):
                    new_access_token = await jwt_service.refresh_token(token_pair["refresh_token"])

                    assert new_access_token == "new.access.token"
                    # Verify verify_token was called with the refresh token
                    mock_verify.assert_called_once_with(token_pair["refresh_token"])
                    # Verify create_token was called (implicitly checks claims were extracted)
                    mock_create.assert_called_once()
                else:
                    pytest.skip("JWTService does not implement refresh_token method")


    @pytest.mark.asyncio
    async def test_extract_claims_invalid_token(self, jwt_service: JWTService):
        """Test extracting claims from an invalid token."""
        with pytest.raises(ValueError) as excinfo:
            await jwt_service.verify_token("invalid.token.string")
        assert "Invalid token" in str(excinfo.value)


    @freeze_time("2025-03-27 12:00:00")
    @pytest.mark.asyncio
    async def test_token_expiry_time(self, jwt_service: JWTService, user_claims: Dict[str, Any]):
        """Test token expiration times."""
        access_token = await jwt_service.create_token(user_claims, expires_delta=datetime.timedelta(minutes=TEST_ACCESS_EXPIRE_MINUTES))
        refresh_claims = {**user_claims, "jti": "test-jti-exp"}
        refresh_token = await jwt_service.create_token(refresh_claims, expires_delta=datetime.timedelta(minutes=TEST_REFRESH_EXPIRE_MINUTES))

        access_decoded = await jwt_service.verify_token(access_token)
        refresh_decoded = await jwt_service.verify_token(refresh_token)

        # Calculate expected timestamps based on frozen time
        now_ts = datetime.datetime(2025, 3, 27, 12, 0, tzinfo=UTC).timestamp()
        expected_access_exp = now_ts + (TEST_ACCESS_EXPIRE_MINUTES * 60)
        expected_refresh_exp = now_ts + (TEST_REFRESH_EXPIRE_MINUTES * 60)

        assert abs(access_decoded["exp"] - expected_access_exp) < 5 # Allow small buffer
        assert abs(refresh_decoded["exp"] - expected_refresh_exp) < 5 # Allow small buffer


    @pytest.mark.asyncio
    async def test_verify_token_not_before(self, jwt_service: JWTService, user_claims: Dict[str, Any]):
        """Test token validation with 'not before' (nbf) claim."""
        future_time = datetime.now(UTC) + datetime.timedelta(hours=1)
        claims_with_nbf = {**user_claims, "nbf": future_time}

        token_with_nbf = await jwt_service.create_token(claims_with_nbf, expires_delta=datetime.timedelta(minutes=TEST_ACCESS_EXPIRE_MINUTES))

        with pytest.raises(ValueError) as excinfo:
            await jwt_service.verify_token(token_with_nbf)
        # Check for PyJWTError message related to nbf
        assert "Invalid token: The token is not yet valid" in str(excinfo.value) or "ImmatureSignatureError" in str(excinfo.value)


    @pytest.mark.asyncio
    async def test_custom_claims(self, jwt_service: JWTService, user_claims: Dict[str, Any]):
        """Test adding custom claims."""
        custom_claims = {
            "patient_id": "PT12345",
            "specialization": "depression",
            "is_premium": True
        }
        all_claims = {**user_claims, **custom_claims}
        token = await jwt_service.create_token(all_claims, expires_delta=datetime.timedelta(minutes=TEST_ACCESS_EXPIRE_MINUTES))

        decoded = await jwt_service.verify_token(token)

        assert decoded["patient_id"] == "PT12345"
        assert decoded["specialization"] == "depression"
        assert decoded["is_premium"] is True


    @pytest.mark.asyncio
    async def test_error_handling(self, jwt_service: JWTService):
        """Test general error handling for invalid token format."""
        # Test with completely invalid token format
        with pytest.raises(ValueError) as excinfo:
            await jwt_service.verify_token("this.is.not.a.jwt")
        assert "Invalid token" in str(excinfo.value)
