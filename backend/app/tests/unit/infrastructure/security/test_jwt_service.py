# -*- coding: utf-8 -*-
"""Unit tests for JWT Service functionality.

This module tests the JWT service that handles authentication tokens,
a critical component for HIPAA-compliant user authentication and authorization.
"""

import pytest
import jwt
import datetime
import time
from unittest.mock import patch, MagicMock
from freezegun import freeze_time

from app.infrastructure.security.jwt_service import (
    JWTService,
    JWTConfig,
    TokenStatus,
    TokenValidationResult,
    TokenType,
    TokenPair,
    InvalidTokenError,
    ExpiredTokenError,
    RevokedTokenError,
    MissingClaimError,
    InvalidSignatureError,
    TokenValidationError
)


@pytest.fixture
def jwt_config():
    """Create a JWT service configuration for testing."""
    return JWTConfig(
        secret_key="test-jwt-secret-key-must-be-at-least-32-chars-long",
        algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_token_expire_minutes=60 * 24 * 7,  # 7 days
        token_issuer="novamind-auth",
        token_audience="novamind-api",
        refresh_token_rotation=True,
        check_revoked_tokens=True,
        claim_namespace="https://novamind.io/",
        enable_auto_refresh=True
    )


@pytest.fixture
def mock_token_store():
    """Create a mock token store for testing."""
    mock_store = MagicMock()
    
    # Setup mock storage methods
    mock_store.is_token_revoked.return_value = False
    mock_store.add_token_to_revocation_list.return_value = None
    mock_store.get_refresh_token_family.return_value = []
    mock_store.add_refresh_token.return_value = None
    
    return mock_store


@pytest.fixture
def jwt_service(jwt_config, mock_token_store):
    """Create a JWT service for testing."""
    service = JWTService(config=jwt_config)
    service.token_store = mock_token_store
    return service


@pytest.fixture
def user_claims():
    """Create test user claims."""
    return {
        "sub": "user123",
        "name": "Dr. Jane Smith",
        "email": "jane.smith@example.com",
        "roles": ["psychiatrist"],
        "permissions": ["read:patient", "write:clinical_note", "prescribe:medication"]
    }


@pytest.fixture
def token_pair(jwt_service, user_claims):
    """Create a test token pair (access and refresh tokens)."""
    return jwt_service.create_token_pair(user_claims)


class TestJWTService:
    """Test suite for the JWT service."""
    
    def test_create_access_token(self, jwt_service, user_claims):
        """Test creating an access token with user claims."""
        # Create an access token
        access_token = jwt_service.create_access_token(user_claims)
        
        # Verify token is created
        assert access_token is not None
        assert isinstance(access_token, str)
        
        # Decode and verify claims
        decoded = jwt.decode(
            access_token,
            jwt_service.config.secret_key,
            algorithms=[jwt_service.config.algorithm],
            audience=jwt_service.config.token_audience,
            issuer=jwt_service.config.token_issuer
        )
        
        # Verify all claims were included
        assert decoded["sub"] == user_claims["sub"]
        assert decoded["name"] == user_claims["name"]
        assert decoded["roles"] == user_claims["roles"]
        
        # Verify token type claim
        assert decoded["token_type"] == "access"
        
        # Verify expiration claim
        assert "exp" in decoded
    
    def test_create_refresh_token(self, jwt_service, user_claims):
        """Test creating a refresh token with user claims."""
        # Create a refresh token
        refresh_token = jwt_service.create_refresh_token(user_claims)
        
        # Verify token is created
        assert refresh_token is not None
        assert isinstance(refresh_token, str)
        
        # Decode and verify claims
        decoded = jwt.decode(
            refresh_token,
            jwt_service.config.secret_key,
            algorithms=[jwt_service.config.algorithm],
            audience=jwt_service.config.token_audience,
            issuer=jwt_service.config.token_issuer
        )
        
        # Verify essential claims were included
        assert decoded["sub"] == user_claims["sub"]
        
        # Verify token type claim
        assert decoded["token_type"] == "refresh"
        
        # Verify expiration claim has longer lifetime
        assert "exp" in decoded
        
        # Verify refresh token has a jti (JWT ID) claim
        assert "jti" in decoded
    
    def test_create_token_pair(self, jwt_service, user_claims):
        """Test creating a pair of access and refresh tokens."""
        # Create a token pair
        token_pair = jwt_service.create_token_pair(user_claims)
        
        # Verify token pair structure
        assert isinstance(token_pair, TokenPair)
        assert token_pair.access_token is not None
        assert token_pair.refresh_token is not None
        
        # Verify access token
        access_decoded = jwt.decode(
            token_pair.access_token,
            jwt_service.config.secret_key,
            algorithms=[jwt_service.config.algorithm],
            audience=jwt_service.config.token_audience,
            issuer=jwt_service.config.token_issuer
        )
        assert access_decoded["token_type"] == "access"
        
        # Verify refresh token
        refresh_decoded = jwt.decode(
            token_pair.refresh_token,
            jwt_service.config.secret_key,
            algorithms=[jwt_service.config.algorithm],
            audience=jwt_service.config.token_audience,
            issuer=jwt_service.config.token_issuer
        )
        assert refresh_decoded["token_type"] == "refresh"
        
        # Verify refresh token was stored
        jwt_service.token_store.add_refresh_token.assert_called_once()
    
    def test_validate_token_valid(self, jwt_service, token_pair):
        """Test validation of a valid token."""
        # Validate the access token
        validation_result = jwt_service.validate_token(token_pair.access_token)
        
        # Verify validation result
        assert validation_result.is_valid is True
        assert validation_result.status == TokenStatus.VALID
        assert validation_result.claims is not None
        assert validation_result.claims["sub"] == "user123"
        assert validation_result.token_type == TokenType.ACCESS
    
    def test_validate_token_invalid_signature(self, jwt_service, token_pair):
        """Test validation of a token with invalid signature."""
        # Tamper with the token by changing a character
        tampered_token = token_pair.access_token[:-5] + "XXXXX"
        
        # Validate the tampered token
        validation_result = jwt_service.validate_token(tampered_token)
        
        # Verify validation result
        assert validation_result.is_valid is False
        assert validation_result.status == TokenStatus.INVALID
        assert isinstance(validation_result.error, InvalidSignatureError)
    
    @freeze_time("2025-03-27 12:00:00")
    def test_validate_token_expired(self, jwt_service, user_claims):
        """Test validation of an expired token."""
        # Create a token that will expire immediately
        with patch.object(jwt_service.config, 'access_token_expire_minutes', 0):
            expired_token = jwt_service.create_access_token(user_claims)
        
        # Fast-forward time to ensure expiration
        with freeze_time("2025-03-27 12:01:00"):
            # Validate the expired token
            validation_result = jwt_service.validate_token(expired_token)
            
            # Verify validation result
            assert validation_result.is_valid is False
            assert validation_result.status == TokenStatus.EXPIRED
            assert isinstance(validation_result.error, ExpiredTokenError)
    
    def test_validate_token_revoked(self, jwt_service, token_pair, mock_token_store):
        """Test validation of a revoked token."""
        # Configure the mock token store to report token as revoked
        mock_token_store.is_token_revoked.return_value = True
        
        # Validate the revoked token
        validation_result = jwt_service.validate_token(token_pair.access_token)
        
        # Verify validation result
        assert validation_result.is_valid is False
        assert validation_result.status == TokenStatus.REVOKED
        assert isinstance(validation_result.error, RevokedTokenError)
    
    def test_validate_token_missing_claim(self, jwt_service, user_claims):
        """Test validation of a token with missing required claim."""
        # Create token with missing required claim
        user_claims_missing_sub = {k: v for k, v in user_claims.items() if k != "sub"}
        
        # Mock the _create_token method to bypass claim validation during creation
        original_create = jwt_service._create_token
        
        def mock_create(claims, token_type, expires_delta=None, **kwargs):
            """Skip claim validation during creation."""
            return original_create(claims, token_type, expires_delta, validate_claims=False)
        
        with patch.object(jwt_service, '_create_token', mock_create):
            token_missing_sub = jwt_service.create_access_token(user_claims_missing_sub)
        
        # Validate token with missing claim
        validation_result = jwt_service.validate_token(token_missing_sub)
        
        # Verify validation result
        assert validation_result.is_valid is False
        assert validation_result.status == TokenStatus.INVALID
        assert isinstance(validation_result.error, MissingClaimError)
    
    def test_token_required_decorator(self, jwt_service, token_pair):
        """Test the token_required decorator."""
        # Define a test function to decorate
        test_executed = False
        
        @jwt_service.token_required
        def test_function(claims):
            nonlocal test_executed
            test_executed = True
            return claims["sub"]
        
        # Call the decorated function with a valid token
        result = test_function(token=token_pair.access_token)
        
        # Verify function was executed and returned expected result
        assert test_executed is True
        assert result == "user123"
        
        # Reset execution flag
        test_executed = False
        
        # Call the decorated function with an invalid token
        tampered_token = token_pair.access_token[:-5] + "XXXXX"
        
        # Should raise an exception
        with pytest.raises(InvalidTokenError):
            test_function(token=tampered_token)
        
        # Verify function was not executed
        assert test_executed is False
    
    def test_refresh_tokens(self, jwt_service, token_pair, mock_token_store):
        """Test refreshing tokens using a valid refresh token."""
        # Setup mock token store
        mock_token_store.is_token_revoked.return_value = False
        
        # Refresh tokens
        new_token_pair = jwt_service.refresh_tokens(token_pair.refresh_token)
        
        # Verify new tokens were created
        assert new_token_pair is not None
        assert new_token_pair.access_token != token_pair.access_token
        assert new_token_pair.refresh_token != token_pair.refresh_token
        
        # Verify old refresh token was revoked
        mock_token_store.add_token_to_revocation_list.assert_called_once()
        
        # Verify new refresh token was stored
        assert mock_token_store.add_refresh_token.call_count == 2  # Once for init, once for refresh
    
    def test_refresh_tokens_without_rotation(self, jwt_config, user_claims):
        """Test refreshing tokens without token rotation enabled."""
        # Create config without refresh token rotation
        no_rotation_config = jwt_config
        no_rotation_config.refresh_token_rotation = False
        
        # Create service with modified config
        mock_store = MagicMock()
        mock_store.is_token_revoked.return_value = False
        
        service = JWTService(config=no_rotation_config)
        service.token_store = mock_store
        
        # Create initial token pair
        token_pair = service.create_token_pair(user_claims)
        
        # Refresh tokens
        new_token_pair = service.refresh_tokens(token_pair.refresh_token)
        
        # Verify access token was refreshed
        assert new_token_pair.access_token != token_pair.access_token
        
        # Verify refresh token stays the same
        assert new_token_pair.refresh_token == token_pair.refresh_token
        
        # Verify old refresh token was not revoked
        mock_store.add_token_to_revocation_list.assert_not_called()
    
    def test_revoke_token(self, jwt_service, token_pair, mock_token_store):
        """Test revoking a token."""
        # Revoke the access token
        jwt_service.revoke_token(token_pair.access_token)
        
        # Verify token was added to revocation list
        mock_token_store.add_token_to_revocation_list.assert_called_once()
    
    def test_revoke_all_refresh_tokens(self, jwt_service, user_claims, mock_token_store):
        """Test revoking all refresh tokens for a user."""
        # Setup mock refresh token family
        mock_token_store.get_refresh_token_family.return_value = ["token1", "token2", "token3"]
        
        # Revoke all refresh tokens
        jwt_service.revoke_all_refresh_tokens(user_claims["sub"])
        
        # Verify token family was retrieved and each token was revoked
        mock_token_store.get_refresh_token_family.assert_called_once_with(user_claims["sub"])
        assert mock_token_store.add_token_to_revocation_list.call_count == 3
    
    def test_extract_claims(self, jwt_service, token_pair):
        """Test extracting claims from a token."""
        # Extract claims
        claims = jwt_service.extract_claims(token_pair.access_token)
        
        # Verify claim extraction
        assert claims is not None
        assert claims["sub"] == "user123"
        assert claims["roles"] == ["psychiatrist"]
        assert claims["token_type"] == "access"
    
    def test_extract_claims_invalid_token(self, jwt_service):
        """Test extracting claims from an invalid token."""
        # Attempt to extract claims from an invalid token
        with pytest.raises(InvalidTokenError):
            jwt_service.extract_claims("invalid.token.string")
    
    def test_validate_token_type(self, jwt_service, token_pair):
        """Test validating token type."""
        # Validate correct token type
        result = jwt_service.validate_token(token_pair.access_token, expected_type=TokenType.ACCESS)
        assert result.is_valid is True
        
        # Validate incorrect token type
        result = jwt_service.validate_token(token_pair.refresh_token, expected_type=TokenType.ACCESS)
        assert result.is_valid is False
        assert result.status == TokenStatus.INVALID
        assert "Expected token type" in str(result.error)
    
    @freeze_time("2025-03-27 12:00:00")
    def test_token_expiry_time(self, jwt_service, user_claims):
        """Test token expiration times."""
        # Create tokens
        access_token = jwt_service.create_access_token(user_claims)
        refresh_token = jwt_service.create_refresh_token(user_claims)
        
        # Decode to get expiration times
        access_decoded = jwt.decode(
            access_token,
            jwt_service.config.secret_key,
            algorithms=[jwt_service.config.algorithm],
            audience=jwt_service.config.token_audience,
            issuer=jwt_service.config.token_issuer
        )
        
        refresh_decoded = jwt.decode(
            refresh_token,
            jwt_service.config.secret_key,
            algorithms=[jwt_service.config.algorithm],
            audience=jwt_service.config.token_audience,
            issuer=jwt_service.config.token_issuer
        )
        
        # Calculate expected expiration times
        expected_access_exp = datetime.datetime(2025, 3, 27, 12, 0).timestamp() + (15 * 60)
        expected_refresh_exp = datetime.datetime(2025, 3, 27, 12, 0).timestamp() + (60 * 24 * 7 * 60)
        
        # Verify expiration times
        assert abs(access_decoded["exp"] - expected_access_exp) < 5  # Allow 5 seconds tolerance
        assert abs(refresh_decoded["exp"] - expected_refresh_exp) < 5  # Allow 5 seconds tolerance
    
    def test_should_refresh_token(self, jwt_service, user_claims):
        """Test token refresh threshold detection."""
        # Create a token that will expire soon
        with patch.object(jwt_service.config, 'access_token_expire_minutes', 10):
            # Token valid for 10 minutes
            token = jwt_service.create_access_token(user_claims)
        
        # Configure auto-refresh threshold to 5 minutes
        jwt_service.config.token_refresh_threshold_seconds = 5 * 60
        
        # Check if token far from expiry should be refreshed
        with freeze_time("2025-03-27 12:01:00"):  # 1 minute after creation, 9 minutes till expiry
            should_refresh = jwt_service.should_refresh_token(token)
            assert should_refresh is False
        
        # Check if token near expiry should be refreshed
        with freeze_time("2025-03-27 12:06:00"):  # 6 minutes after creation, 4 minutes till expiry
            should_refresh = jwt_service.should_refresh_token(token)
            assert should_refresh is True
    
    def test_validate_claims(self, jwt_service, user_claims):
        """Test validation of JWT claims."""
        # Valid claims should pass validation
        jwt_service._validate_claims(user_claims)
        
        # Missing required claim should fail validation
        invalid_claims = {k: v for k, v in user_claims.items() if k != "sub"}
        with pytest.raises(MissingClaimError):
            jwt_service._validate_claims(invalid_claims)
    
    def test_verify_token_not_before(self, jwt_service, user_claims):
        """Test token validation with 'not before' (nbf) claim."""
        # Create claims with nbf in the future
        future_time = int(time.time()) + 3600  # 1 hour in the future
        claims_with_nbf = {**user_claims, "nbf": future_time}
        
        # Create token with future nbf
        token = jwt_service._create_token(
            claims_with_nbf, 
            "access", 
            validate_claims=False  # Skip validation to allow invalid claims
        )
        
        # Validate token with future nbf (should fail)
        validation_result = jwt_service.validate_token(token)
        assert validation_result.is_valid is False
        assert validation_result.status == TokenStatus.INVALID
        assert "The token is not yet valid" in str(validation_result.error)
    
    def test_additional_audience_validation(self, jwt_config, user_claims):
        """Test token validation with multiple audiences."""
        # Create config with multiple audiences
        multi_audience_config = jwt_config
        multi_audience_config.token_audience = ["novamind-api", "novamind-app"]
        
        # Create service with modified config
        service = JWTService(config=multi_audience_config)
        
        # Create tokens with different audiences
        token_api = service._create_token(user_claims, "access", audience="novamind-api")
        token_app = service._create_token(user_claims, "access", audience="novamind-app")
        token_invalid = service._create_token(user_claims, "access", audience="invalid-audience")
        
        # Validate tokens
        assert service.validate_token(token_api).is_valid is True
        assert service.validate_token(token_app).is_valid is True
        assert service.validate_token(token_invalid).is_valid is False
    
    def test_custom_claims(self, jwt_service, user_claims):
        """Test adding custom claims with proper namespacing."""
        # Add custom claims
        custom_claims = {
            f"{jwt_service.config.claim_namespace}patient_id": "PT12345",
            f"{jwt_service.config.claim_namespace}specialization": "depression",
            f"{jwt_service.config.claim_namespace}is_premium": True
        }
        
        # Create token with custom claims
        all_claims = {**user_claims, **custom_claims}
        token = jwt_service.create_access_token(all_claims)
        
        # Validate and extract claims
        validation_result = jwt_service.validate_token(token)
        extracted_claims = validation_result.claims
        
        # Verify custom claims
        assert extracted_claims[f"{jwt_service.config.claim_namespace}patient_id"] == "PT12345"
        assert extracted_claims[f"{jwt_service.config.claim_namespace}specialization"] == "depression"
        assert extracted_claims[f"{jwt_service.config.claim_namespace}is_premium"] is True
    
    def test_token_id_uniqueness(self, jwt_service, user_claims):
        """Test that each token has a unique ID (jti claim)."""
        # Create multiple tokens
        token1 = jwt_service.create_refresh_token(user_claims)
        token2 = jwt_service.create_refresh_token(user_claims)
        
        # Decode tokens
        decoded1 = jwt.decode(
            token1,
            jwt_service.config.secret_key,
            algorithms=[jwt_service.config.algorithm],
            audience=jwt_service.config.token_audience,
            issuer=jwt_service.config.token_issuer
        )
        
        decoded2 = jwt.decode(
            token2,
            jwt_service.config.secret_key,
            algorithms=[jwt_service.config.algorithm],
            audience=jwt_service.config.token_audience,
            issuer=jwt_service.config.token_issuer
        )
        
        # Verify JTIs are unique
        assert "jti" in decoded1
        assert "jti" in decoded2
        assert decoded1["jti"] != decoded2["jti"]
    
    def test_refresh_chain_security(self, jwt_service, token_pair, mock_token_store):
        """Test refresh token rotation security (preventing refresh token reuse)."""
        # Configure token store to track refresh token families
        token_family = [token_pair.refresh_token]
        mock_token_store.get_refresh_token_family.return_value = token_family
        
        # First refresh - should work
        new_tokens = jwt_service.refresh_tokens(token_pair.refresh_token)
        
        # Update token family
        token_family.append(new_tokens.refresh_token)
        mock_token_store.get_refresh_token_family.return_value = token_family
        
        # Now try to reuse the original refresh token, which should fail
        with pytest.raises(RevokedTokenError):
            jwt_service.refresh_tokens(token_pair.refresh_token)
        
        # Verify token was checked against revocation list
        assert mock_token_store.is_token_revoked.call_count >= 2
    
    def test_token_store_integration(self, jwt_service, token_pair, mock_token_store):
        """Test integration with the token store."""
        # Verify token store methods were called during token pair creation
        mock_token_store.add_refresh_token.assert_called_once()
        
        # Verify token is checked against revocation list during validation
        jwt_service.validate_token(token_pair.access_token)
        mock_token_store.is_token_revoked.assert_called()
    
    def test_error_handling(self, jwt_service):
        """Test handling of various error conditions."""
        # Test with non-JWT string
        result = jwt_service.validate_token("not-a-jwt-token")
        assert result.is_valid is False
        assert result.status == TokenStatus.INVALID
        
        # Test with None
        result = jwt_service.validate_token(None)
        assert result.is_valid is False
        assert result.status == TokenStatus.INVALID
    
    def test_encode_decode_asymmetric_keys(self):
        """Test token encoding/decoding with asymmetric keys (RS256)."""
        # Create a JWT config with RSA algorithm
        rsa_config = JWTConfig(
            secret_key="",  # Not used with asymmetric keys
            algorithm="RS256",
            access_token_expire_minutes=15,
            refresh_token_expire_minutes=60 * 24,
            token_issuer="novamind-auth",
            token_audience="novamind-api"
        )
        
        # Mock RSA key pair
        mock_private_key = "mock_private_key"
        mock_public_key = "mock_public_key"
        
        # Create JWT service with RSA config
        service = JWTService(config=rsa_config)
        
        # Mock encoding/decoding with RSA
        with patch('jwt.encode') as mock_encode, \
             patch('jwt.decode') as mock_decode:
            
            # Mock successful encoding
            mock_encode.return_value = "rsa.encoded.token"
            
            # Mock successful decoding
            mock_decode.return_value = {"sub": "user123", "token_type": "access"}
            
            # Mock key loading
            service._load_private_key = MagicMock(return_value=mock_private_key)
            service._load_public_key = MagicMock(return_value=mock_public_key)
            
            # Test token creation (encoding)
            claims = {"sub": "user123"}
            token = service.create_access_token(claims)
            
            # Verify encoding was called with RSA private key
            mock_encode.assert_called_once()
            call_args = mock_encode.call_args[1]
            assert call_args["algorithm"] == "RS256"
            
            # Test token validation (decoding)
            validation_result = service.validate_token(token)
            
            # Verify decoding was called with RSA public key
            mock_decode.assert_called_once()
            call_args = mock_decode.call_args[1]
            assert call_args["algorithms"] == ["RS256"]
            
            # Verify validation result
            assert validation_result.is_valid is True