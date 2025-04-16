"""
Integration tests for HIPAA security boundaries.

These tests verify that our security components work together correctly
to enforce proper authentication and authorization boundaries.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.infrastructure.security.jwt.jwt_service import JWTHandler
from app.infrastructure.security.password.password_handler import PasswordHandler
from app.infrastructure.security.rbac.rbac_service import RBACService
from app.domain.entities.security.role import Role
from app.domain.entities.security.permission import Permission


@pytest.fixture
def security_components():
    """
    Create the core security components needed for testing.

    Returns:
        Tuple of (jwt_handler, password_handler, role_manager)
    """
    jwt_handler = JWTHandler(
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
        assert role_manager.has_permission(token_data.role, Permission.VIEW_OWN_MEDICAL_RECORDS)
        assert not role_manager.has_permission(token_data.role, Permission.VIEW_ALL_MEDICAL_RECORDS)

    def test_token_expiration(self, security_components):
        """Test token expiration handling."""
        # Unpack components
        jwt_handler, _, _ = security_components
        
        # Create a token with very short expiration
        short_lived_jwt = JWTHandler(
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
                Permission.VIEW_OWN_MEDICAL_RECORDS,
                Permission.UPDATE_OWN_PROFILE
            ],
            Role.DOCTOR: [
                Permission.VIEW_PATIENT_MEDICAL_RECORDS,
                Permission.CREATE_MEDICAL_RECORD,
                Permission.UPDATE_MEDICAL_RECORD
            ],
            Role.ADMIN: [
                Permission.VIEW_ALL_MEDICAL_RECORDS,
                Permission.MANAGE_USERS,
                Permission.SYSTEM_CONFIGURATION
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
        
        # Admin should have access to everything via ADMIN_ALL permission
        assert role_manager.has_permission(admin_data.role, Permission.VIEW_PATIENT_MEDICAL_RECORDS)
        assert role_manager.has_permission(admin_data.role, Permission.CREATE_PRESCRIPTION)
        assert role_manager.has_permission(admin_data.role, Permission.PROCESS_PAYMENTS)
        
        # Nurse should have limited permissions
        assert role_manager.has_permission(nurse_data.role, Permission.VIEW_PATIENT_MEDICAL_RECORDS)
        assert not role_manager.has_permission(nurse_data.role, Permission.CREATE_PRESCRIPTION)
        assert not role_manager.has_permission(nurse_data.role, Permission.PROCESS_PAYMENTS)