# -*- coding: utf-8 -*-
"""
Unit tests for Role-Based Access Control (RBAC) Manager.

These tests verify that our role-based access control system meets HIPAA
security requirements for proper separation of access controls.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.infrastructure.security.rbac.role_manager import (
    RoleManager, 
    RoleDefinition,
    Role, 
    Permission
)


@pytest.fixture
def role_manager():
    """
    Create a role manager instance for testing.
    
    Returns:
        RoleManager instance with default roles
    """
    return RoleManager()


@pytest.mark.venv_only
class TestRoleManager:
    """Test suite for role-based access control manager."""
    
    @pytest.mark.venv_only
def test_init_default_roles(self, role_manager):
        """Test that default roles are created during initialization."""
        # Assert
        roles = role_manager.get_all_roles()
        
        # Verify standard roles exist
        assert Role.PATIENT in roles
        assert Role.PROVIDER in roles
        assert Role.ADMIN in roles
        assert Role.NURSE in roles
        assert Role.BILLING_STAFF in roles
        assert Role.RECEPTIONIST in roles
        assert Role.SYSTEM in roles
        
        # Verify each role has appropriate permissions
        assert len(roles[Role.PATIENT].permissions) > 0
        assert len(roles[Role.PROVIDER].permissions) > 0
        assert len(roles[Role.ADMIN].permissions) > 0
    
    @pytest.mark.venv_only
def test_patient_role_permissions(self, role_manager):
        """Test that patient role has appropriate permissions."""
        # Get patient permissions
        patient_perms = role_manager.get_role_permissions(Role.PATIENT)
        
        # Assert patient has access to their own data
        assert Permission.VIEW_OWN_PROFILE in patient_perms
        assert Permission.EDIT_OWN_PROFILE in patient_perms
        assert Permission.VIEW_OWN_MEDICAL_RECORDS in patient_perms
        assert Permission.VIEW_OWN_APPOINTMENTS in patient_perms
        assert Permission.SCHEDULE_OWN_APPOINTMENT in patient_perms
        
        # Assert patient does not have access to other patients' data
        assert Permission.VIEW_ASSIGNED_PATIENTS not in patient_perms
        assert Permission.VIEW_PATIENT_MEDICAL_RECORDS not in patient_perms
        assert Permission.VIEW_ALL_APPOINTMENTS not in patient_perms
    
    @pytest.mark.venv_only
def test_provider_role_permissions(self, role_manager):
        """Test that provider role has appropriate permissions."""
        # Get provider permissions
        provider_perms = role_manager.get_role_permissions(Role.PROVIDER)
        
        # Assert provider has access to patient data
        assert Permission.VIEW_ASSIGNED_PATIENTS in provider_perms
        assert Permission.EDIT_ASSIGNED_PATIENTS in provider_perms
        assert Permission.VIEW_PATIENT_MEDICAL_RECORDS in provider_perms
        assert Permission.EDIT_PATIENT_MEDICAL_RECORDS in provider_perms
        assert Permission.CREATE_MEDICAL_NOTES in provider_perms
        assert Permission.CREATE_PRESCRIPTION in provider_perms
        
        # Assert provider does not have admin permissions
        assert Permission.MANAGE_USERS not in provider_perms
        assert Permission.ADMIN_ALL not in provider_perms
    
    @pytest.mark.venv_only
def test_admin_role_permissions(self, role_manager):
        """Test that admin role has appropriate permissions."""
        # Get admin permissions
        admin_perms = role_manager.get_role_permissions(Role.ADMIN)
        
        # Assert admin has full access
        assert Permission.ADMIN_ALL in admin_perms
        assert Permission.MANAGE_USERS in admin_perms
        assert Permission.MANAGE_ROLES in admin_perms
        assert Permission.VIEW_AUDIT_LOGS in admin_perms
    
    @pytest.mark.venv_only
def test_has_permission_valid(self, role_manager):
        """Test permission check for valid permissions."""
        # Assert
        assert role_manager.has_permission(Role.PATIENT, Permission.VIEW_OWN_PROFILE) is True
        assert role_manager.has_permission(Role.PROVIDER, Permission.EDIT_PATIENT_MEDICAL_RECORDS) is True
        assert role_manager.has_permission(Role.ADMIN, Permission.MANAGE_USERS) is True
    
    @pytest.mark.venv_only
def test_has_permission_invalid(self, role_manager):
        """Test permission check for invalid permissions."""
        # Assert
        assert role_manager.has_permission(Role.PATIENT, Permission.EDIT_PATIENT_MEDICAL_RECORDS) is False
        assert role_manager.has_permission(Role.NURSE, Permission.CREATE_PRESCRIPTION) is False
        assert role_manager.has_permission(Role.RECEPTIONIST, Permission.MANAGE_USERS) is False
    
    @pytest.mark.venv_only
def test_has_permission_nonexistent_role(self, role_manager):
        """Test permission check for nonexistent role."""
        # Assert
        assert role_manager.has_permission("nonexistent_role", Permission.VIEW_OWN_PROFILE) is False
    
    @pytest.mark.venv_only
def test_has_permission_admin_all(self, role_manager):
        """Test that ADMIN_ALL permission grants all other permissions."""
        # Admin role has ADMIN_ALL permission
        
        # Check a permission not explicitly granted to admin
        assert role_manager.has_permission(Role.ADMIN, Permission.VIEW_OWN_PRESCRIPTIONS) is True
        
        # Check a few more permissions
        assert role_manager.has_permission(Role.ADMIN, Permission.CREATE_PRESCRIPTION) is True
        assert role_manager.has_permission(Role.ADMIN, Permission.VIEW_PATIENT_MEDICAL_RECORDS) is True
    
    @pytest.mark.venv_only
def test_add_role(self, role_manager):
        """Test adding a new role."""
        # Arrange
        new_role = RoleDefinition(
            name="researcher",
            description="Medical researcher with limited access",
            permissions={
                Permission.VIEW_PATIENT_MEDICAL_RECORDS,
                Permission.VIEW_AUDIT_LOGS
            }
        )
        
        # Act
        role_manager.add_role(new_role)
        
        # Assert
        roles = role_manager.get_all_roles()
        assert "researcher" in roles
        assert roles["researcher"].description == "Medical researcher with limited access"
        assert len(roles["researcher"].permissions) == 2
        assert Permission.VIEW_PATIENT_MEDICAL_RECORDS in roles["researcher"].permissions
        assert Permission.VIEW_AUDIT_LOGS in roles["researcher"].permissions
    
    @pytest.mark.venv_only
def test_add_existing_role(self, role_manager):
        """Test adding a role with an existing name raises error."""
        # Arrange
        duplicate_role = RoleDefinition(
            name=Role.PATIENT,
            description="Duplicate patient role",
            permissions={Permission.VIEW_OWN_PROFILE}
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match=f"Role {Role.PATIENT} already exists"):
            role_manager.add_role(duplicate_role)
    
    @pytest.mark.venv_only
def test_update_role_permissions(self, role_manager):
        """Test updating permissions for a role."""
        # Arrange
        new_permissions = {
            Permission.VIEW_OWN_PROFILE,
            Permission.EDIT_OWN_PROFILE,
            Permission.VIEW_OWN_MEDICAL_RECORDS
        }
        
        # Act
        role_manager.update_role_permissions(Role.RECEPTIONIST, new_permissions)
        
        # Assert
        updated_perms = role_manager.get_role_permissions(Role.RECEPTIONIST)
        assert updated_perms == new_permissions
        assert Permission.SCHEDULE_ANY_APPOINTMENT not in updated_perms
    
    @pytest.mark.venv_only
def test_update_nonexistent_role(self, role_manager):
        """Test updating permissions for a nonexistent role raises error."""
        # Arrange
        new_permissions = {Permission.VIEW_OWN_PROFILE}
        
        # Act & Assert
        with pytest.raises(ValueError, match="Role nonexistent_role does not exist"):
            role_manager.update_role_permissions("nonexistent_role", new_permissions)
    
    @pytest.mark.venv_only
def test_add_permission_to_role(self, role_manager):
        """Test adding a single permission to a role."""
        # Arrange
        # Ensure permission is not already in the role
        role_permissions = role_manager.get_role_permissions(Role.NURSE)
        assert Permission.CREATE_PRESCRIPTION not in role_permissions
        
        # Act
        role_manager.add_permission_to_role(Role.NURSE, Permission.CREATE_PRESCRIPTION)
        
        # Assert
        updated_perms = role_manager.get_role_permissions(Role.NURSE)
        assert Permission.CREATE_PRESCRIPTION in updated_perms
    
    @pytest.mark.venv_only
def test_remove_permission_from_role(self, role_manager):
        """Test removing a permission from a role."""
        # Arrange
        # Ensure permission is in the role
        role_permissions = role_manager.get_role_permissions(Role.PATIENT)
        assert Permission.VIEW_OWN_PROFILE in role_permissions
        
        # Act
        role_manager.remove_permission_from_role(Role.PATIENT, Permission.VIEW_OWN_PROFILE)
        
        # Assert
        updated_perms = role_manager.get_role_permissions(Role.PATIENT)
        assert Permission.VIEW_OWN_PROFILE not in updated_perms
    
    @pytest.mark.venv_only
def test_get_role_permissions_nonexistent(self, role_manager):
        """Test getting permissions for a nonexistent role raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="Role nonexistent_role does not exist"):
            role_manager.get_role_permissions("nonexistent_role")
    
    @pytest.mark.venv_only
def test_check_user_permission_basic(self, role_manager):
        """Test basic user permission check."""
        # Act & Assert
        assert role_manager.check_user_permission(
            Role.PROVIDER, 
            Permission.EDIT_PATIENT_MEDICAL_RECORDS,
            None
        ) is True
        
        assert role_manager.check_user_permission(
            Role.PATIENT, 
            Permission.EDIT_PATIENT_MEDICAL_RECORDS,
            None
        ) is False
    
    @pytest.mark.venv_only
def test_check_user_permission_with_resource(self, role_manager):
        """Test user permission check with resource ID."""
        # Act & Assert
        # Provider should have access to patient records
        assert role_manager.check_user_permission(
            Role.PROVIDER, 
            Permission.VIEW_PATIENT_MEDICAL_RECORDS,
            "patient123"  # Resource ID
        ) is True
        
        # Patient should not have access to other patients
        assert role_manager.check_user_permission(
            Role.PATIENT, 
            Permission.VIEW_PATIENT_MEDICAL_RECORDS,
            "patient123"  # Resource ID
        ) is False
    
    @patch('app.infrastructure.security.rbac.role_manager.logger')
    @pytest.mark.venv_only
def test_logging_behavior(self, mock_logger, role_manager):
        """Test that appropriate logging occurs for security events."""
        # Act
        role_manager.has_permission(Role.PROVIDER, Permission.EDIT_PATIENT_MEDICAL_RECORDS)
        role_manager.has_permission(Role.PATIENT, Permission.EDIT_PATIENT_MEDICAL_RECORDS)
        
        # Assert logging behavior
        # Should log successful permission
        mock_logger.debug.assert_any_call(
            f"Role {Role.PROVIDER} has permission: {Permission.EDIT_PATIENT_MEDICAL_RECORDS}"
        )
        
        # Should log denied permission
        mock_logger.warning.assert_any_call(
            f"Role {Role.PATIENT} denied permission: {Permission.EDIT_PATIENT_MEDICAL_RECORDS}"
        )