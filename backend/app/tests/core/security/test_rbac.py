# -*- coding: utf-8 -*-
"""
Role-Based Access Control Tests

This module contains tests for the RBAC component, ensuring
proper role and permission management for security.
"""

import unittest
from app.core.security.rbac import RoleBasedAccessControl


class TestRoleBasedAccessControl(unittest.TestCase):
    """Test suite for Role-Based Access Control functionality."""
    
    def setUp(self):
        """Set up test environment with fresh RBAC instance."""
        self.rbac = RoleBasedAccessControl()
        
        # Configure test roles and permissions
        self.rbac.add_role('user')
        self.rbac.add_role('clinician')
        self.rbac.add_role('admin')
        
        # User permissions
        self.rbac.add_role_permission('user', 'read:own_data')
        self.rbac.add_role_permission('user', 'update:own_data')
        
        # Clinician permissions
        self.rbac.add_role_permission('clinician', 'read:patient_data')
        self.rbac.add_role_permission('clinician', 'update:patient_data')
        self.rbac.add_role_permission('clinician', 'read:clinical_notes')
        
        # Admin permissions
        self.rbac.add_role_permission('admin', 'read:all_data')
        self.rbac.add_role_permission('admin', 'update:all_data')
        self.rbac.add_role_permission('admin', 'delete:all_data')
    
    def test_add_role(self):
        """Test adding a new role."""
        # Add new role
        self.rbac.add_role('researcher')
        
        # Verify it exists with empty permissions
        self.assertEqual(self.rbac.get_role_permissions('researcher'), set())
    
    def test_add_role_permission(self):
        """Test adding a permission to a role."""
        # Add new permission to existing role
        self.rbac.add_role_permission('user', 'delete:own_data')
        
        # Verify permission was added
        user_permissions = self.rbac.get_role_permissions('user')
        self.assertIn('delete:own_data', user_permissions)
        
        # Verify other permissions still exist
        self.assertIn('read:own_data', user_permissions)
        self.assertIn('update:own_data', user_permissions)
    
    def test_remove_role_permission(self):
        """Test removing a permission from a role."""
        # Remove existing permission
        self.rbac.remove_role_permission('clinician', 'update:patient_data')
        
        # Verify permission was removed
        clinician_permissions = self.rbac.get_role_permissions('clinician')
        self.assertNotIn('update:patient_data', clinician_permissions)
        
        # Verify other permissions still exist
        self.assertIn('read:patient_data', clinician_permissions)
        self.assertIn('read:clinical_notes', clinician_permissions)
    
    def test_has_permission_single_role(self):
        """Test permission check with a single role."""
        # User role permissions
        self.assertTrue(self.rbac.has_permission(['user'], 'read:own_data'))
        self.assertTrue(self.rbac.has_permission(['user'], 'update:own_data'))
        self.assertFalse(self.rbac.has_permission(['user'], 'read:patient_data'))
        
        # Clinician role permissions
        self.assertTrue(self.rbac.has_permission(['clinician'], 'read:patient_data'))
        self.assertFalse(self.rbac.has_permission(['clinician'], 'read:own_data'))
        
        # Admin role permissions
        self.assertTrue(self.rbac.has_permission(['admin'], 'delete:all_data'))
        self.assertFalse(self.rbac.has_permission(['admin'], 'read:clinical_notes'))
    
    def test_has_permission_multiple_roles(self):
        """Test permission check with multiple roles."""
        # User + Clinician roles
        roles = ['user', 'clinician']
        self.assertTrue(self.rbac.has_permission(roles, 'read:own_data'))       # from user
        self.assertTrue(self.rbac.has_permission(roles, 'read:patient_data'))   # from clinician
        self.assertFalse(self.rbac.has_permission(roles, 'delete:all_data'))    # not in either
        
        # User + Admin roles
        roles = ['user', 'admin']
        self.assertTrue(self.rbac.has_permission(roles, 'read:own_data'))       # from user
        self.assertTrue(self.rbac.has_permission(roles, 'delete:all_data'))     # from admin
        self.assertFalse(self.rbac.has_permission(roles, 'read:clinical_notes')) # not in either
    
    def test_has_permission_nonexistent_role(self):
        """Test permission check with non-existent role."""
        self.assertFalse(self.rbac.has_permission(['nonexistent'], 'read:own_data'))
    
    def test_has_permission_nonexistent_permission(self):
        """Test checking for a non-existent permission."""
        self.assertFalse(self.rbac.has_permission(['user'], 'nonexistent:permission'))
    
    def test_get_role_permissions(self):
        """Test getting all permissions for a role."""
        # Check admin permissions
        admin_permissions = self.rbac.get_role_permissions('admin')
        expected = {'read:all_data', 'update:all_data', 'delete:all_data'}
        self.assertEqual(admin_permissions, expected)
        
        # Check nonexistent role
        self.assertEqual(self.rbac.get_role_permissions('nonexistent'), set())
    
    def test_get_roles_with_permission(self):
        """Test getting all roles with a specific permission."""
        # Multiple roles with read permissions
        self.rbac.add_role_permission('researcher', 'read:patient_data')
        
        # Get roles with specific permission
        roles = self.rbac.get_roles_with_permission('read:patient_data')
        self.assertIn('clinician', roles)
        self.assertIn('researcher', roles)
        self.assertNotIn('user', roles)
        self.assertNotIn('admin', roles)
        
        # Check nonexistent permission
        self.assertEqual(self.rbac.get_roles_with_permission('nonexistent'), [])


if __name__ == "__main__":
    unittest.main()