"""
Base security test class for all security tests in Novamind Digital Twin Platform.

This class provides improved handling of security-related test attributes and fixtures
to ensure proper initialization of test data.
"""

import os
from typing import Dict, Any, List, Optional
import logging
from unittest import mock

# Mock the get_settings function before importing audit
# This ensures the audit module can initialize properly during import
settings_patch = mock.patch('app.core.config.get_settings')
mock_settings = settings_patch.start()
mock_settings.return_value = mock.MagicMock(
    AUDIT_LOG_LEVEL=logging.INFO,
    AUDIT_LOG_TO_FILE=False,
    ENVIRONMENT="test",
    EXTERNAL_AUDIT_ENABLED=False,
    AUDIT_LOG_FILE="test_audit.log"
)

# Also patch the AuditLogger class before importing it
audit_logger_patch = mock.patch('app.infrastructure.security.audit.AuditLogger')
mock_audit_logger_class = audit_logger_patch.start()
mock_audit_instance = mock.MagicMock()
mock_audit_logger_class.return_value = mock_audit_instance

# Now it's safe to import
from app.tests.base_test import BaseTest


class BaseSecurityTest(BaseTest):
    """Base class for all security tests in the system."""
    
    # Default values for security testing
    default_test_user_id = "test-security-user-default"
    default_test_roles = ["user", "clinician"]
    
    def setUp(self) -> None:
        """Set up security test fixtures."""
        # Ensure we have proper test data from child classes
        self.test_user_id = getattr(self, 'test_user_id', self.default_test_user_id)
        self.test_roles = getattr(self, 'test_roles', self.default_test_roles)
        
        super().setUp()
        
        # Mock security services and components
        self.setup_auth_mocks()
        self.setup_encryption_mocks()
        self.setup_audit_mocks()
    
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
        # Use the global mock instance that was created before imports
        self.mock_audit_service = mock_audit_instance
        
        # Configure the audit service behavior
        self.mock_audit_service.log_phi_access.side_effect = self.mock_audit_log
        
        # We don't need to start/stop any patchers since they're now global
    
    def tearDown(self) -> None:
        """Tear down security test fixtures."""
        # Stop only the authentication and encryption patchers
        # The audit patchers are global and should not be stopped per test
        self.auth_patcher.stop()
        self.encryption_patcher.stop()
        
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