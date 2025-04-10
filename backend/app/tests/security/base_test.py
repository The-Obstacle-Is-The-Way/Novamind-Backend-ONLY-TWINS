"""
Base test class for security-related tests in Novamind Digital Twin Platform.

This module provides base test functionality for all security-related tests,
including authentication, authorization, and data protection.
"""

import unittest
import uuid
from unittest import mock
from typing import Dict, List, Any, Optional


class BaseSecurityTest(unittest.TestCase):
    """Base class for all security-related tests."""
    
    def setUp(self) -> None:
        """Set up test fixtures for security tests."""
        # Set up test user with synthetic test data
        self.test_user_id = str(uuid.uuid4())
        self.test_roles = ["clinician", "researcher"]
        self.test_permissions = ["read:patient", "write:notes", "read:analytics"]
        
        # Setup auth mocks
        self.setup_auth_mocks()
        
        # Set up audit logging mock
        self.audit_logger_patcher = mock.patch(
            "app.core.utils.logging.AuditLogger"
        )
        self.mock_audit_logger = self.audit_logger_patcher.start()
    
    def tearDown(self) -> None:
        """Tear down test fixtures for security tests."""
        # Stop patchers
        self.auth_patcher.stop()
        self.audit_logger_patcher.stop()
    
    def setup_auth_mocks(self) -> None:
        """Set up authentication and authorization mocks."""
        # Mock auth service
        self.auth_patcher = mock.patch(
            "app.infrastructure.security.jwt_service.JWTService"
        )
        self.mock_auth_service = self.auth_patcher.start()
    
        # Setup auth service behavior
        self.mock_auth_service.return_value.verify_token.return_value = {
            "user_id": self.test_user_id,
            "roles": self.test_roles
        }
        
        self.mock_auth_service.return_value.create_token.return_value = "mock.jwt.token"
        self.mock_auth_service.return_value.has_permission.return_value = True
    
    def set_user_roles(self, roles: List[str]) -> None:
        """
        Update the test user roles.
        
        Args:
            roles: New roles for the test user
        """
        self.test_roles = roles
        self.mock_auth_service.return_value.verify_token.return_value = {
            "user_id": self.test_user_id,
            "roles": self.test_roles
        }
    
    def set_user_permissions(self, permissions: List[str]) -> None:
        """
        Update the test user permissions.
        
        Args:
            permissions: New permissions for the test user
        """
        self.test_permissions = permissions
        
        # Update the has_permission mock to check against the new permissions list
        def has_permission_side_effect(permission: str, *args, **kwargs) -> bool:
            return permission in self.test_permissions
            
        self.mock_auth_service.return_value.has_permission.side_effect = has_permission_side_effect
    
    def assert_audit_logged(self, action: str, resource_type: str, user_id: Optional[str] = None) -> None:
        """
        Assert that an audit log was created.
        
        Args:
            action: Expected audit log action
            resource_type: Expected audit log resource type
            user_id: Expected user ID (defaults to test_user_id)
        """
        if not user_id:
            user_id = self.test_user_id
            
        # Check if the appropriate audit log method was called
        if action == "access":
            self.mock_audit_logger.return_value.log_access.assert_called_with(
                user_id=user_id, 
                resource_type=resource_type,
                mock.ANY
            )
        elif action == "modify":
            self.mock_audit_logger.return_value.log_modification.assert_called_with(
                user_id=user_id, 
                resource_type=resource_type,
                mock.ANY
            )
        elif action == "delete":
            self.mock_audit_logger.return_value.log_deletion.assert_called_with(
                user_id=user_id, 
                resource_type=resource_type,
                mock.ANY
            )