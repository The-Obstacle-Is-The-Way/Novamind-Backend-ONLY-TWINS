"""
Integration tests for HIPAA security boundaries.

These tests verify that our security components work together correctly
to enforce proper authentication and authorization boundaries.
"""

import pytest
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import uuid
import asyncio

from app.config.settings import get_settings
from app.infrastructure.security.jwt.jwt_service import JWTService, TokenPayload
from app.infrastructure.security.password.password_handler import PasswordHandler
from app.infrastructure.security.rbac.rbac_service import RBACService
from app.domain.enums.role import Role
from app.presentation.api.dependencies.auth import get_current_user
from app.domain.exceptions import InvalidTokenError, TokenExpiredError


@pytest.fixture
def security_components():
    """
    Create the core security components needed for testing.

    Returns:
        Tuple of (jwt_handler, password_handler, role_manager)
    """
    jwt_handler = JWTService(
        secret_key="testkey12345678901234567890123456789",
        algorithm="HS256",
        access_token_expire_minutes=15
    )

    password_handler = PasswordHandler()
    
    role_manager = RoleBasedAccessControl()

    return jwt_handler, password_handler, role_manager


@pytest.mark.db_required
class TestSecurityBoundary:
    """Test suite for integrated security boundaries."""

    def test_complete_auth_flow(self, security_components):
        """Test a complete authentication flow with all security components."""
        # Unpack components
        jwt_handler, password_handler, role_manager = security_components

        # 1. Create secure password and hash it (as would happen during user registration)
        password = password_handler.generate_secure_password()
        hashed_password = password_handler.hash_password(password)

        # 2. Verify password (as would happen during login)
        is_valid = password_handler.verify_password(password, hashed_password)
        assert is_valid is True

        # 3. Generate token upon successful login
        user_id = "patient123"
        role = Role.PATIENT
        permissions = list(role_manager.get_role_permissions(role))
        session_id = "session_abc123"

        token = jwt_handler.create_access_token(
            user_id=user_id,
            role=role,
            permissions=permissions,
            session_id=session_id
        )

        # 4. Verify token (as would happen during API request)
        token_data = jwt_handler.verify_token(token)
        
        # 5. Check token data
        assert token_data.user_id == user_id
        assert token_data.role == role
        assert token_data.session_id == session_id
        
        # 6. Check permissions using role manager
        assert role_manager.has_permission(token_data.role, "view_own_medical_records")
        assert not role_manager.has_permission(token_data.role, "view_all_medical_records")

    def test_token_expiration(self, security_components):
        """Test token expiration handling."""
        # Unpack components
        jwt_handler, _, _ = security_components
        
        # Create a token with very short expiration
        short_lived_jwt = JWTService(
            secret_key="testkey12345678901234567890123456789",
            algorithm="HS256",
            access_token_expire_minutes=0.01  # 0.6 seconds
        )
        
        token = short_lived_jwt.create_access_token(
            user_id="test123",
            role=Role.PATIENT,
            permissions=[],
            session_id="session_test"
        )
        
        # Token should be valid immediately
        token_data = short_lived_jwt.verify_token(token)
        assert token_data is not None
        
        # Wait for token to expire
        time.sleep(1)
        
        # Token should now be expired
        with pytest.raises(Exception) as excinfo:
            short_lived_jwt.verify_token(token)
        
        # Verify it's an expiration error
        assert "expired" in str(excinfo.value).lower()

    def test_role_based_access_control(self, security_components):
        """Test role-based access control with different roles."""
        # Unpack components
        jwt_handler, _, role_manager = security_components
        
        # Create tokens for different roles
        roles_and_permissions = {
            Role.PATIENT: [
                "view_own_medical_records",
                "update_own_profile"
            ],
            Role.DOCTOR: [
                "view_patient_medical_records",
                "create_medical_record",
                "update_medical_record"
            ],
            Role.ADMIN: [
                "view_all_medical_records",
                "manage_users",
                "system_configuration"
            ]
        }
        
        # Test each role's permissions
        for role, expected_permissions in roles_and_permissions.items():
            # Create token for this role
            token = jwt_handler.create_access_token(
                user_id=f"user_{role}",
                role=role,
                permissions=list(role_manager.get_role_permissions(role)),
                session_id=f"session_{role}"
            )
            
            # Verify token
            token_data = jwt_handler.verify_token(token)
            
            # Check that role has expected permissions
            for permission in expected_permissions:
                assert role_manager.has_permission(token_data.role, permission), \
                    f"Role {role} should have permission {permission}"
            
            # Check that role doesn't have unexpected permissions
            all_permissions = set()
            for perms in roles_and_permissions.values():
                all_permissions.update(perms)
            
            unexpected_permissions = all_permissions - set(expected_permissions)
            for permission in unexpected_permissions:
                # Skip admin permissions check since admin might have all permissions
                if role == Role.ADMIN:
                    continue
                assert not role_manager.has_permission(token_data.role, permission), \
                    f"Role {role} should not have permission {permission}"

    def test_password_strength_validation(self, security_components):
        """Test password strength validation."""
        # Unpack components
        _, password_handler, _ = security_components
        
        # Test a strong password
        strong_password = "Str0ng@P4ssw0rd!"
        is_valid, _ = password_handler.validate_password_strength(strong_password)
        assert is_valid is True
        
        # Test various weak passwords and ensure they're rejected
        weak_passwords = [
            "short123!",       # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoSpecialChars123",  # No special characters
            "NoDigits@Here",   # No digits
            "Password12345@",  # Common pattern
        ]
        
        for password in weak_passwords:
            is_valid, error = password_handler.validate_password_strength(password)
            assert is_valid is False
            assert error is not None

    def test_admin_special_privileges(self, security_components):
        """Test admin special privileges that override normal permissions."""
        # Unpack components
        jwt_handler, _, role_manager = security_components
        
        # Create tokens for different roles
        admin_token = jwt_handler.create_access_token(
            user_id="admin123",
            role=Role.ADMIN,
            permissions=list(role_manager.get_role_permissions(Role.ADMIN)),
            session_id="session_admin123"
        )
        
        nurse_token = jwt_handler.create_access_token(
            user_id="nurse456",
            role=Role.NURSE,
            permissions=list(role_manager.get_role_permissions(Role.NURSE)),
            session_id="session_nurse123"
        )
        
        # Decode tokens
        admin_data = jwt_handler.verify_token(admin_token)
        nurse_data = jwt_handler.verify_token(nurse_token)
        
        # Admin should have broad access (adjust permission strings as needed based on roles.py)
        assert role_manager.has_permission(admin_data.role, "view_all_data")
        assert role_manager.has_permission(admin_data.role, "manage_users")
        assert role_manager.has_permission(admin_data.role, "manage_system")
        
        # Nurse should have limited permissions
        assert role_manager.has_permission(nurse_data.role, "view_patient_data")
        assert not role_manager.has_permission(nurse_data.role, "create_prescription")
        assert not role_manager.has_permission(nurse_data.role, "process_payments")

    async def test_token_generation_and_validation(self):
        """Test generating and validating a standard token."""
        settings = get_settings()
        # Use JWTService
        jwt_service = JWTService(settings=settings)
        user_id = str(uuid.uuid4())
        roles = ["admin"]

        # Create token using JWTService
        token = await jwt_service.create_access_token(subject=user_id, roles=roles)

        assert isinstance(token, str)

        # Decode token using JWTService
        payload = await jwt_service.decode_token(token)

        assert payload.sub == user_id
        assert payload.roles == roles
        assert payload.scope == "access_token"
        assert payload.exp > int(datetime.now(timezone.utc).timestamp())

    async def test_expired_token_validation(self):
        """Test that an expired token raises TokenExpiredError."""
        settings = get_settings()
        # Use JWTService
        jwt_service = JWTService(settings=settings)
        user_id = str(uuid.uuid4())
        # Create token that expired 1 hour ago
        past_expiry = timedelta(hours=-1)
        expired_token = jwt_service._create_token(
            subject=user_id, 
            expires_delta=past_expiry, 
            scope="access_token", 
            jti=str(uuid.uuid4())
        )
        
        with pytest.raises(TokenExpiredError):
             await jwt_service.decode_token(expired_token)

    async def test_invalid_token_validation(self):
        """Test that an invalid/tampered token raises InvalidTokenError."""
        settings = get_settings()
        # Use JWTService
        jwt_service = JWTService(settings=settings)
        invalid_token = "this.is.not.a.valid.token"

        with pytest.raises(InvalidTokenError):
            await jwt_service.decode_token(invalid_token)

        # Test token with incorrect signature
        user_id = str(uuid.uuid4())
        token = await jwt_service.create_access_token(subject=user_id)
        tampered_token = token[:-5] + "wrong"
        with pytest.raises(InvalidTokenError):
            await jwt_service.decode_token(tampered_token)
            
    async def test_token_with_minimal_payload(self):
        """Test token validation with only required fields (sub, exp, iat, jti, scope)."""
        settings = get_settings()
        jwt_service = JWTService(settings=settings)
        user_id = str(uuid.uuid4())
        jti = str(uuid.uuid4())
        # Create token using the internal helper with minimal claims
        minimal_token = jwt_service._create_token(
            subject=user_id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            scope="access_token",
            jti=jti,
            additional_claims=None # Explicitly no additional claims
        )
        payload = await jwt_service.decode_token(minimal_token)
        assert payload.sub == user_id
        assert payload.jti == jti
        assert payload.scope == "access_token"
        assert payload.roles is None
        assert payload.permissions is None
        assert payload.session_id is None

    # Test for very short-lived tokens if necessary for specific security contexts
    async def test_short_lived_token_validation(self):
        """Test validation of a very short-lived token (e.g., 1 second)."""
        settings = get_settings()
        # Use JWTService
        short_lived_jwt_service = JWTService(settings=settings)
        user_id = str(uuid.uuid4())
        short_expiry = timedelta(seconds=1)
        short_lived_token = short_lived_jwt_service._create_token(
            subject=user_id,
            expires_delta=short_expiry,
            scope="access_token",
            jti=str(uuid.uuid4())
        )
        
        # Token should be valid immediately after creation
        payload = await short_lived_jwt_service.decode_token(short_lived_token)
        assert payload.sub == user_id
        
        # Wait for slightly longer than expiration and check it fails
        await asyncio.sleep(1.1)
        with pytest.raises(TokenExpiredError):
            await short_lived_jwt_service.decode_token(short_lived_token)