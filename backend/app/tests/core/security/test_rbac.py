"""
Role-Based Access Control Tests

This module contains tests for the RBAC component, ensuring
proper role and permission management for security.
"""

import pytest
from unittest import mock

from app.core.security.rbac import check_permission
from app.domain.entities.user import User
from app.domain.enums.role import Role


@pytest.mark.venv_only()
class TestRoleBasedAccessControl:
    """Test suite for Role-Based Access Control functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Create mock users with different roles
        self.admin_user = User(
            id="admin-id",
            email="admin@example.com",
            full_name="Admin User",
            role=Role.ADMIN,
            hashed_password="hashed_password"
        )
        
        self.clinician_user = User(
            id="clinician-id",
            email="clinician@example.com",
            full_name="Clinician User",
            role=Role.CLINICIAN,
            hashed_password="hashed_password"
        )
        
        self.patient_user = User(
            id="patient-id",
            email="patient@example.com",
            full_name="Patient User",
            role=Role.PATIENT,
            hashed_password="hashed_password"
        )
        
        self.researcher_user = User(
            id="researcher-id",
            email="researcher@example.com",
            full_name="Researcher User",
            role=Role.RESEARCHER,
            hashed_password="hashed_password"
        )

    def test_check_permission_admin(self):
        """Test permission check for admin role."""
        # Admin should have all permissions
        assert check_permission(self.admin_user, "read:all_data") is True
        assert check_permission(self.admin_user, "update:all_data") is True
        assert check_permission(self.admin_user, "delete:all_data") is True
        assert check_permission(self.admin_user, "read:patient_data") is True
        assert check_permission(self.admin_user, "manage:users") is True

    def test_check_permission_clinician(self):
        """Test permission check for clinician role."""
        # Clinician should have patient data access but not all admin permissions
        assert check_permission(self.clinician_user, "read:patient_data") is True
        assert check_permission(self.clinician_user, "update:patient_data") is True
        assert check_permission(self.clinician_user, "read:own_data") is True
        
        # Clinician should not have admin-level permissions
        assert check_permission(self.clinician_user, "delete:all_data") is False
        assert check_permission(self.clinician_user, "manage:users") is False

    def test_check_permission_patient(self):
        """Test permission check for patient role."""
        # Patient should only have access to own data
        assert check_permission(self.patient_user, "read:own_data") is True
        assert check_permission(self.patient_user, "update:own_data") is True
        
        # Patient should not have access to other data
        assert check_permission(self.patient_user, "read:all_data") is False
        assert check_permission(self.patient_user, "read:patient_data") is False
        assert check_permission(self.patient_user, "manage:users") is False

    def test_check_permission_researcher(self):
        """Test permission check for researcher role."""
        # Researcher should have read access to anonymized data
        assert check_permission(self.researcher_user, "read:anonymized_data") is True
        assert check_permission(self.researcher_user, "read:own_data") is True
        
        # Researcher should not have access to identifiable patient data or admin functions
        assert check_permission(self.researcher_user, "read:patient_data") is False
        assert check_permission(self.researcher_user, "update:patient_data") is False
        assert check_permission(self.researcher_user, "manage:users") is False

    def test_check_permission_nonexistent_permission(self):
        """Test checking for a non-existent permission."""
        # No role should have a non-existent permission
        assert check_permission(self.admin_user, "nonexistent:permission") is False
        assert check_permission(self.clinician_user, "nonexistent:permission") is False
        assert check_permission(self.patient_user, "nonexistent:permission") is False
        assert check_permission(self.researcher_user, "nonexistent:permission") is False

    def test_check_permission_with_none_user(self):
        """Test permission check with None user."""
        # Should handle None user gracefully
        assert check_permission(None, "read:own_data") is False

    def test_check_permission_with_none_permission(self):
        """Test permission check with None permission."""
        # Should handle None permission gracefully
        assert check_permission(self.admin_user, None) is False

    @mock.patch('app.core.security.rbac.ROLE_PERMISSIONS', {
        Role.ADMIN: {"custom:permission"},
        Role.CLINICIAN: set(),
        Role.PATIENT: set(),
        Role.RESEARCHER: set()
    })
    def test_check_permission_with_custom_permissions(self):
        """Test permission check with custom permissions configuration."""
        # Admin should have the custom permission
        assert check_permission(self.admin_user, "custom:permission") is True
        
        # Other roles should not have the custom permission
        assert check_permission(self.clinician_user, "custom:permission") is False
        assert check_permission(self.patient_user, "custom:permission") is False
        assert check_permission(self.researcher_user, "custom:permission") is False