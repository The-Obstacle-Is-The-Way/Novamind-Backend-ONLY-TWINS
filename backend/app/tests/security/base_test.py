"""
Base test class for security tests in Novamind Digital Twin Platform.

This class provides enhanced security test fixtures and utilities
specific to security testing concerns.
"""

import os
from typing import Dict, Any, List, Optional
from unittest import mock

from app.tests.base_test import BaseTest


class BaseSecurityTest(BaseTest):
    """Base class for all security tests in the system."""
    
    def setUp(self) -> None:
        """Set up security test fixtures."""
        super().setUp()
        
        # Mock security services and components
        self.setup_auth_mocks()
        self.setup_encryption_mocks()
        self.setup_audit_mocks()
        
        # Initialize standard security test data
        self.test_user_id = "test-security-user"
        self.test_roles = ["user", "clinician"]
        
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
        
    def setup_encryption_mocks(self) -> None:
        """Set up encryption mocks."""
        # Mock encryption service
        self.encryption_patcher = mock.patch(
            "app.infrastructure.security.encryption_service.EncryptionService"
        )
        self.mock_encryption_service = self.encryption_patcher.start()
        
        # Setup encryption service behavior
        self.mock_encryption_service.return_value.encrypt.side_effect = \
            lambda text: f"ENCRYPTED({text})"
        self.mock_encryption_service.return_value.decrypt.side_effect = \
            lambda text: text.replace("ENCRYPTED(", "").replace(")", "")
            
    def setup_audit_mocks(self) -> None:
        """Set up audit logging mocks."""
        # Mock audit service
        self.audit_patcher = mock.patch(
            "app.infrastructure.security.audit.AuditLogger"
        )
        self.mock_audit_service = self.audit_patcher.start()
        
        # Setup audit service behavior
        self.mock_audit_service.return_value.log_phi_access.side_effect = \
            self.mock_audit_log
    
    def tearDown(self) -> None:
        """Tear down security test fixtures."""
        # Stop all patchers
        self.auth_patcher.stop()
        self.encryption_patcher.stop()
        self.audit_patcher.stop()
        
        super().tearDown()
    
    def assert_phi_access_logged(self, resource_type: str, 
                                resource_id: str) -> None:
        """Assert that PHI access was properly logged.
        
        Args:
            resource_type: Type of resource accessed
            resource_id: ID of resource accessed
        """
        matching_events = [
            event for event in self.audit_events
            if (event["action"] == "access" and
                event["resource_type"] == resource_type and
                event["resource_id"] == resource_id)
        ]
        
        self.assertTrue(
            len(matching_events) > 0,
            f"No audit log for PHI access to {resource_type}:{resource_id}"
        )