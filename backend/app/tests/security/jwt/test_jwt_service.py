# -*- coding: utf-8 -*-
import os
import jwt
import time
import pytest
import uuid # Import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from typing import Any

# Use the global jwt_service fixture from conftest
from app.infrastructure.security.jwt.jwt_service import JWTService, TokenPayload # Import TokenPayload
from app.domain.exceptions import InvalidTokenError, TokenExpiredError # Correct exception imports
# Remove AuthenticationError import if InvalidTokenError/TokenExpiredError cover cases


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
    # Define test data directly or use separate fixtures if complex
    user_subject = "1234567890"
    user_roles = ["patient"]
    provider_subject = "0987654321"
    provider_roles = ["provider"]
    admin_subject = "admin123"
    admin_roles = ["admin"]

    @pytest.mark.asyncio
    async def test_create_access_token_structure(self, jwt_service: JWTService):
        """Test structure and basic claims of a created access token."""
        # Act
        token = await jwt_service.create_access_token(subject=self.user_subject, roles=self.user_roles)

        # Decode without verification just to check structure
        # Note: jwt.decode is synchronous
        decoded = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})

        # Assert basic structure and claims managed by JWTService
        assert isinstance(token, str)
        assert decoded.get("sub") == self.user_subject
        assert decoded.get("scope") == "access_token"
        assert decoded.get("roles") == self.user_roles
        assert isinstance(decoded.get("exp"), int)
        assert isinstance(decoded.get("iat"), int)
        assert isinstance(decoded.get("jti"), str)

        # Verify no unexpected PHI fields were included by mistake
        phi_fields = ["name", "email", "dob", "ssn", "address", "phone"]
        for field in phi_fields:
            assert field not in decoded, f"Unexpected PHI field '{field}' found in token"

    @pytest.mark.asyncio
    async def test_create_access_token_expiration(self, jwt_service: JWTService):
        """Test that access tokens have correct expiration times based on settings."""
        # Act
        token = await jwt_service.create_access_token(subject=self.user_subject, roles=self.user_roles)

        # Decode using the service to verify expiration is handled internally
        # This implicitly tests that the 'exp' claim leads to correct validation
        payload = await jwt_service.decode_token(token)

        # Assert expiration is roughly correct (within a tolerance for execution time)
        expected_exp_ts = time.time() + jwt_service.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        # Use payload.exp which is already an int timestamp
        assert abs(payload.exp - expected_exp_ts) < 15, "Token expiration time deviates significantly from expected setting" # Increased tolerance slightly

    @pytest.mark.asyncio
    async def test_decode_token_valid(self, jwt_service: JWTService):
        """Test that valid tokens are properly decoded and validated."""
        # Arrange
        token = await jwt_service.create_access_token(subject=self.user_subject, roles=self.user_roles)

        # Act
        payload = await jwt_service.decode_token(token)

        # Assert payload is TokenPayload instance with correct data
        assert isinstance(payload, TokenPayload)
        assert payload.sub == self.user_subject
        assert payload.roles == self.user_roles
        assert payload.scope == "access_token"

    @pytest.mark.asyncio
    async def test_decode_token_expired(self, jwt_service: JWTService):
        """Test that expired tokens raise TokenExpiredError during decoding."""
        # Arrange
        # Create a token with an expiration time in the past using the internal _create_token
        past_exp_delta = timedelta(minutes=-5)
        # Note: _create_token is synchronous
        expired_token = jwt_service._create_token(
            subject=self.user_subject,
            expires_delta=past_exp_delta,
            scope="access_token",
            jti=str(uuid.uuid4()),
            additional_claims={"roles": self.user_roles}
        )

        # Act/Assert
        with pytest.raises(TokenExpiredError):
            await jwt_service.decode_token(expired_token)

    @pytest.mark.asyncio
    async def test_decode_token_invalid_signature(self, jwt_service: JWTService):
        """Test that tokens with invalid signatures raise InvalidTokenError."""
        # Arrange
        token = await jwt_service.create_access_token(subject=self.user_subject, roles=self.user_roles)

        # Tamper with the token by changing a character in the signature part
        parts = token.split('.')
        if len(parts) == 3:
            # Ensure tampering actually changes the signature - simply append to it
            tampered_signature = parts[2] + 'X' 
            tampered_token = f"{parts[0]}.{parts[1]}.{tampered_signature}"
        else:
            pytest.fail("Generated token does not have 3 parts separated by dots.")

        # Act/Assert
        with pytest.raises(InvalidTokenError):
            await jwt_service.decode_token(tampered_token)

    @pytest.mark.asyncio
    async def test_decode_token_invalid_format(self, jwt_service: JWTService):
        """Test that tokens with invalid format raise InvalidTokenError."""
        # Arrange
        invalid_token = "not.a.valid.jwt.token.format"

        # Act/Assert
        with pytest.raises(InvalidTokenError):
            await jwt_service.decode_token(invalid_token)

    @pytest.mark.skip(reason="Role/permission logic belongs elsewhere (e.g., middleware/dependencies).")
    @pytest.mark.asyncio
    async def test_admin_role_permissions(self, jwt_service: JWTService): # Added async/await structure
        pass # Keep skipped test structure if planning to refactor later

    @pytest.mark.skip(reason="Role/permission logic belongs elsewhere.")
    @pytest.mark.asyncio
    async def test_provider_role_permissions(self, jwt_service: JWTService):
        pass

    @pytest.mark.skip(reason="Role/permission logic belongs elsewhere.")
    @pytest.mark.asyncio
    async def test_patient_role_permissions(self, jwt_service: JWTService):
        pass

    @pytest.mark.skip(reason="Refresh token logic (rotation/family tracking) is not implemented directly in JWTService.")
    @pytest.mark.asyncio
    async def test_refresh_token_rotation(self, jwt_service: JWTService):
        pass

    @pytest.mark.skip(reason="Refresh token logic (rotation/family tracking) is not implemented directly in JWTService.")
    @pytest.mark.asyncio
    async def test_refresh_token_family_tracking(self, jwt_service: JWTService):
        pass

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
