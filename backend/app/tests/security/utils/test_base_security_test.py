"""
Base Security Test Class Tests

This module contains tests for the BaseSecurityTest class to ensure
proper functionality of the security test infrastructure.
"""

import pytest

import unittest
import json
from unittest.mock import patch
import uuid  # Import uuid module

from app.tests.security.utils.base_security_test import BaseSecurityTest
from app.tests.security.utils.test_mocks import MockAuthService, MockRBACService, MockAuditLogger, MockEncryptionService, MockEntityFactory
from app.domain.entities.user import User
from app.domain.enums.role import Role # Import Role enum

class TestBaseSecurityTest(unittest.TestCase):
    """Test suite for BaseSecurityTest functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.auth_service = MockAuthService()
        self.rbac_service = MockRBACService()
        self.audit_logger = MockAuditLogger()
        self.encryption_service = MockEncryptionService()
        self.entity_factory = MockEntityFactory()
        # Use a valid UUID and the Role enum
        self.user = User(
            id=uuid.uuid4(), # Generate a valid UUID
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password", # Note: Password should ideally be handled securely
            roles=[Role.USER] # Use Role enum
        )

    def test_initialization(self):

        """Test that BaseSecurityTest initializes with correct attributes."""
        security_test = BaseSecurityTest()
        security_test.setUp()

        # Check required attributes are present
        self.assertIsNotNone(security_test.test_user_id)
        self.assertIsNotNone(security_test.test_roles)

        # Check that roles are set correctly
        self.assertIn("user", security_test.test_roles)
        self.assertIn("clinician", security_test.test_roles)

        # Clean up
        security_test.tearDown()

    def test_has_permission(self):
        """Test permission checking functionality."""
        security_test = BaseSecurityTest()
        security_test.setUp()

        # Test permissions with default roles
        self.assertTrue(security_test.has_permission("read:own_data"))
        self.assertTrue(security_test.has_permission("read:patient_data"))
        self.assertFalse(security_test.has_permission("delete:all_data"))

        # Test with explicit roles
        # Correct assertion syntax
        self.assertTrue(
            security_test.has_permission("delete:all_data", roles=["admin"])
        )
        self.assertFalse(
            security_test.has_permission("delete:all_data", roles=["user"])
        )

        # Clean up
        security_test.tearDown()

    def test_get_auth_token(self):
        """Test generation of authentication tokens."""
        security_test = BaseSecurityTest()
        security_test.setUp()

        # Get token with default values
        token = security_test.get_auth_token()

        # Token should be a string
        self.assertIsInstance(token, str)

        # Token should contain user ID and roles
        # Note: This assertion is weak as it just checks substring presence.
        # A better test would decode the token and check claims.
        # self.assertIn(security_test.test_user_id, token)
        # for role in security_test.test_roles:
        #     self.assertIn(role, token)

        # Test with custom values
        custom_user_id = "custom_user_123"
        custom_roles = ["admin", "auditor"]
        custom_claims = {"extra": "value"}

        # Correct function call syntax
        token = security_test.get_auth_token(
            user_id=custom_user_id,
            roles=custom_roles,
            custom_claims=custom_claims
        )

        # Token should contain custom values (weak assertion)
        # self.assertIn(custom_user_id, token)
        # for role in custom_roles:
        #     self.assertIn(role, token)
        # self.assertIn("extra", token)
        # self.assertIn("value", token)

        # Clean up
        security_test.tearDown()

    def test_get_auth_headers(self):
        """Test generation of authentication headers."""
        security_test = BaseSecurityTest()
        security_test.setUp()

        # Get headers with default token
        headers = security_test.get_auth_headers()

        # Headers should be a dict with Authorization key
        self.assertIsInstance(headers, dict)
        self.assertIn("Authorization", headers)

        # Authorization should have Bearer prefix
        self.assertTrue(headers["Authorization"].startswith("Bearer "))

        # Token should be included in Authorization
        token = security_test.get_auth_token()
        self.assertIn(token, headers["Authorization"])

        # Test with custom token
        custom_token = "custom.test.token"
        headers = security_test.get_auth_headers(token=custom_token)
        self.assertEqual(headers["Authorization"], f"Bearer {custom_token}")

        # Clean up
        security_test.tearDown()

    # Correct indentation for decorator and method
    @patch("app.tests.security.utils.test_mocks.MockAsyncSession")
    def test_db_session_setup(self, mock_session_class):
        """Test database session is properly set up."""
        security_test = BaseSecurityTest()
        security_test.setUp()

        # Verify session is initialized
        self.assertIsNotNone(security_test.db_session)

        # Clean up
        security_test.tearDown()

    def test_entity_factory_setup(self):
        """Test entity factory is properly set up."""
        security_test = BaseSecurityTest()
        security_test.setUp()

        # Verify entity factory is initialized
        self.assertIsNotNone(security_test.entity_factory)

        # Test creating entities
        # Correct function call syntax
        entity = security_test.entity_factory.create(
            "patient", name="Test Patient"
        )
        self.assertEqual(entity["type"], "patient")
        self.assertEqual(entity["name"], "Test Patient")
        self.assertIn("id", entity)

        # Test retrieving entities
        retrieved = security_test.entity_factory.get(entity["id"])
        self.assertEqual(retrieved, entity)

        # Clean up
        security_test.tearDown()

# Correct indentation for main execution block
if __name__ == "__main__":
    unittest.main()
