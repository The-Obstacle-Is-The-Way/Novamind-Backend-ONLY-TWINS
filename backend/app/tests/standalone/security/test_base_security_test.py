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

    @pytest.mark.standalone()
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

    @pytest.mark.standalone()
    def test_has_permission(self):
        """Test permission checking functionality."""
        security_test = BaseSecurityTest()
        security_test.setUp()

        # Test permissions with default roles
        self.assertTrue(security_test.has_permission("read:own_data"))
        self.assertTrue(security_test.has_permission("read:patient_data"))
        self.assertFalse(security_test.has_permission("delete:all_data"))

        # Test with explicit roles
        self.assertTrue(security_test.has_permission("delete:all_data", roles=["admin"]))
        self.assertFalse(security_test.has_permission("delete:all_data", roles=["user"]))

        # Clean up
        security_test.tearDown()

    @pytest.mark.standalone()
    def test_generate_auth_token(self):
        """Test JWT token generation."""
        security_test = BaseSecurityTest()
        security_test.setUp()

        # Get a token with default claims
        token = security_test.get_auth_token()

        # Token should be a string
        self.assertIsInstance(token, str)

        # Token should have three parts (header, payload, signature)
        parts = token.split('.')
        self.assertEqual(len(parts), 3)

        # Test with custom claims
        custom_claims = {
            "sub": "test_subject",
            "permissions": ["read:all", "write:all"]
        }
        token = security_test.get_auth_token(custom_claims)

        # Decode payload and verify claims
        import base64
        import json

        # Padding might be needed for base64 decoding
        padded_payload = parts[1] + '=' * (-len(parts[1]) % 4)
        payload = json.loads(base64.b64decode(padded_payload).decode('utf-8'))

        # Check claims are present
        self.assertIn("sub", payload)
        self.assertIn("permissions", payload)

        # Clean up
        security_test.tearDown()

    @pytest.mark.standalone()
    def test_get_auth_headers(self):
        """Test generating authorization headers."""
        security_test = BaseSecurityTest()
        security_test.setUp()

        # Test headers with default token
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
    @pytest.mark.standalone()
    def test_db_session_setup(self, mock_session_class):
        """Test database session is properly set up."""
        security_test = BaseSecurityTest()
        security_test.setUp()

        # Verify session is initialized
        self.assertIsNotNone(security_test.db_session)

        # Clean up
        security_test.tearDown()

    @pytest.mark.standalone()
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