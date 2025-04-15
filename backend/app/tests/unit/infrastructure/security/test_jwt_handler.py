# -*- coding: utf-8 -*-
"""
Unit tests for the JWT service.

Reflects the refactored JWTService using decode_token and domain exceptions.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import time # Import time for timestamp checks
from jose import jwt
from app.domain.exceptions import InvalidTokenError, TokenExpiredError
from app.infrastructure.security.jwt.jwt_service import JWTService, TokenPayload
from app.config.settings import get_settings

# Define UTC if not imported elsewhere (Python 3.11+)
try:
    from datetime import UTC # Use standard UTC if available
except ImportError:
    UTC = timezone.utc # Fallback for older Python versions

# Use the fixture from conftest.py directly
@pytest.fixture(scope="module")
def jwt_service_instance(jwt_service: JWTService):
    return jwt_service

# Fixture for a sample user ID
@pytest.fixture(scope="module")
def user_id():
    return str(uuid4())

# Fixture for a sample JTI (JWT ID)
@pytest.fixture(scope="module")
def jti():
    return str(uuid4())

# Test class for organization
class TestJWTService:
    """Test suite for the refactored JWTService."""

    # --- Initialization Tests (implicitly tested by fixture) ---
    def test_init_with_valid_settings(self, jwt_service_instance: JWTService, mock_settings):
        """Test initialization uses the injected mock settings."""
        # The jwt_service fixture should inject mock_settings.
        # We verify that the service instance is indeed using the mock settings object.
        assert jwt_service_instance.settings is mock_settings
        # We can also check a specific value that MockSettings provides directly
        assert jwt_service_instance.settings.ALGORITHM == mock_settings.ALGORITHM

    # --- Access Token Creation ---
    def test_create_access_token_success(self, jwt_service_instance: JWTService, user_id: str):
        """Test successful creation of a basic access token."""
        token = jwt_service_instance.create_access_token(subject=user_id)
        assert isinstance(token, str)
        # Decode to check basic structure and claims
        payload = jwt_service_instance.decode_token(token)
        assert payload.sub == user_id
        assert payload.scope == "access_token"
        assert payload.roles is None # No roles specified
        assert payload.permissions is None # No permissions specified
        assert payload.session_id is None # No session specified

    def test_create_access_token_with_claims(self, jwt_service_instance: JWTService, user_id: str):
        """Test creating an access token with roles, permissions, and session ID."""
        roles = ["admin", "editor"]
        permissions = ["read:all", "write:posts"]
        session_id = str(uuid4())
        token = jwt_service_instance.create_access_token(
            subject=user_id,
            roles=roles,
            permissions=permissions,
            session_id=session_id
        )
        payload = jwt_service_instance.decode_token(token)
        assert payload.sub == user_id
        assert payload.scope == "access_token"
        assert payload.roles == roles
        assert payload.permissions == permissions
        assert payload.session_id == session_id

    # --- Refresh Token Creation ---
    def test_create_refresh_token_success(self, jwt_service_instance: JWTService, user_id: str, jti: str):
        """Test successful creation of a refresh token."""
        token = jwt_service_instance.create_refresh_token(subject=user_id, jti=jti)
        assert isinstance(token, str)
        # Decode to check structure and claims
        payload = jwt_service_instance.decode_token(token)
        assert payload.sub == user_id
        assert payload.scope == "refresh_token"
        assert payload.jti == jti # Critical check for refresh token

    # --- Token Decoding and Validation ---
    def test_decode_valid_access_token(self, jwt_service_instance: JWTService, user_id: str):
        """Test decoding a valid access token returns correct payload."""
        roles = ["user"]
        token = jwt_service_instance.create_access_token(subject=user_id, roles=roles)
        payload = jwt_service_instance.decode_token(token)

        assert isinstance(payload, TokenPayload)
        assert payload.sub == user_id
        assert payload.scope == "access_token"
        assert payload.roles == roles
        assert payload.exp > datetime.now(timezone.utc).timestamp() # Check expiry

    def test_decode_valid_refresh_token(self, jwt_service_instance: JWTService, user_id: str, jti: str):
        """Test decoding a valid refresh token returns correct payload."""
        token = jwt_service_instance.create_refresh_token(subject=user_id, jti=jti)
        payload = jwt_service_instance.decode_token(token)

        assert isinstance(payload, TokenPayload)
        assert payload.sub == user_id
        assert payload.scope == "refresh_token"
        assert payload.jti == jti
        assert payload.exp > datetime.now(timezone.utc).timestamp() # Check expiry

    def test_decode_expired_token_raises_error(self, jwt_service_instance: JWTService, user_id: str):
        """Test decoding an expired token raises TokenExpiredError."""
        settings = get_settings()
        # Use internal _create_token to set a past expiry
        expired_delta = timedelta(seconds=-10)
        expired_token = jwt_service_instance._create_token(
            subject=user_id,
            expires_delta=expired_delta,
            scope="access_token", # Scope doesn't matter for expiry check
            jti=str(uuid4())
        )
        with pytest.raises(TokenExpiredError):
            jwt_service_instance.decode_token(expired_token)

    def test_decode_invalid_signature_raises_error(self, jwt_service_instance: JWTService):
        """Test decoding a token with an invalid signature raises InvalidTokenError."""
        # Create a token with a different secret key
        # We need the jwt library directly for this, not the service instance
        settings = get_settings()
        wrong_key = settings.SECRET_KEY + "_make_it_different"
        payload_data = {
            "sub": "test_user",
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
            "iat": int(datetime.now(UTC).timestamp()),
            "jti": str(uuid4()),
            "scope": "access_token"
        }
        # Encode using the *wrong* key
        invalid_signature_token = jwt.encode(
            payload_data,
            wrong_key, # Use the modified key
            algorithm=settings.ALGORITHM
        )

        # Attempt to decode using the *correct* key via the service
        with pytest.raises(InvalidTokenError): # Expect InvalidTokenError
            jwt_service_instance.decode_token(invalid_signature_token)

    def test_decode_malformed_token_raises_error(self, jwt_service_instance: JWTService):
        """Test decoding a malformed token string raises InvalidTokenError."""
        malformed_token = "this.is.clearly.not.a.jwt"
        with pytest.raises(InvalidTokenError):
            jwt_service_instance.decode_token(malformed_token)

    def test_decode_token_missing_required_claims_raises_error(self, jwt_service_instance: JWTService, user_id: str):
        """Test decoding a token missing required claims (like exp) raises InvalidTokenError."""
        settings = get_settings()
        # Manually create a payload missing 'exp', 'iat', 'jti', 'scope'
        payload_data = {
            "sub": user_id,
            # Missing other required fields per TokenPayload model
        }
        # Encode this incomplete payload
        token_missing_claims = jwt.encode(
            payload_data,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        # Decoding should fail Pydantic validation within decode_token
        with pytest.raises(InvalidTokenError):
            jwt_service_instance.decode_token(token_missing_claims)

    def test_decode_token_wrong_scope(self, jwt_service_instance: JWTService, user_id: str, jti: str):
        """Test decoding works regardless of scope, but scope is preserved."""
        # Create an access token
        access_token = jwt_service_instance.create_access_token(subject=user_id)
        # Create a refresh token
        refresh_token = jwt_service_instance.create_refresh_token(subject=user_id, jti=jti)

        # Decode both
        access_payload = jwt_service_instance.decode_token(access_token)
        refresh_payload = jwt_service_instance.decode_token(refresh_token)

        # Verify scopes are correct after decoding
        assert access_payload.scope == "access_token"
        assert refresh_payload.scope == "refresh_token"
        # Application logic would typically check the scope after decoding

    # --- Timestamp Verification ---
    def test_token_timestamps_are_correct(self, jwt_service_instance: JWTService, user_id: str):
        """Verify 'iat' and 'exp' timestamps are set correctly and within tolerance."""
        now_ts = int(time.time()) # Use time.time() for basic comparison ts
        settings = get_settings()

        # Test Access Token Timestamps
        access_token = jwt_service_instance.create_access_token(subject=user_id)
        access_payload = jwt_service_instance.decode_token(access_token)
        expected_exp_delta_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        # Check 'iat' (issued at) is very close to now
        assert abs(access_payload.iat - now_ts) < 5 # Allow 5s tolerance for execution time

        # Check 'exp' (expiration) is approximately 'iat' + expiry duration
        assert abs(access_payload.exp - (access_payload.iat + expected_exp_delta_seconds)) < 5

        # Test Refresh Token Timestamps
        refresh_jti = str(uuid4())
        refresh_token = jwt_service_instance.create_refresh_token(subject=user_id, jti=refresh_jti)
        refresh_payload = jwt_service_instance.decode_token(refresh_token)
        expected_refresh_exp_delta_seconds = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

        # Check 'iat' (issued at) is very close to now
        assert abs(refresh_payload.iat - now_ts) < 5 # Allow 5s tolerance

        # Check 'exp' (expiration) is approximately 'iat' + expiry duration
        assert abs(refresh_payload.exp - (refresh_payload.iat + expected_refresh_exp_delta_seconds)) < 5

    # --- Edge Cases ---
    def test_token_creation_with_non_uuid_subject(self, jwt_service_instance: JWTService):
        """Test creating tokens with a simple string subject (e.g., username)."""
        subject = "testuser@example.com"
        jti_for_refresh = str(uuid4())

        access_token = jwt_service_instance.create_access_token(subject=subject)
        refresh_token = jwt_service_instance.create_refresh_token(subject=subject, jti=jti_for_refresh)

        access_payload = jwt_service_instance.decode_token(access_token)
        refresh_payload = jwt_service_instance.decode_token(refresh_token)

        assert access_payload.sub == subject
        assert refresh_payload.sub == subject
        assert refresh_payload.jti == jti_for_refresh
