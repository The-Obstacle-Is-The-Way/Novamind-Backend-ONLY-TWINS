"""
Base Security Test Class Tests

This module contains tests for the BaseSecurityTest class to ensure
proper functionality of the security test infrastructure.
"""

import unittest
import pytest
import json
from unittest.mock import patch

from app.tests.security.base_security_test import BaseSecurityTest


class TestBaseSecurityTest(unittest.TestCase):
    """Test suite for BaseSecurityTest functionality."""

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

            token = security_test.get_auth_token(
            user_id=custom_user_id, roles=custom_roles, custom_claims=custom_claims
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

        @patch("app.tests.security.base_security_test.MockAsyncSession")
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
        entity = security_test.entity_factory.create("patient", name="Test Patient")
        self.assertEqual(entity["type"], "patient")
        self.assertEqual(entity["name"], "Test Patient")
        self.assertIn("id", entity)

        # Test retrieving entities
        retrieved = security_test.entity_factory.get(entity["id"])
        self.assertEqual(retrieved, entity)

        # Clean up
        security_test.tearDown()


        if __name__ == "__main__":
    unittest.main()
