# -*- coding: utf-8 -*-
"""
Base Security Test Case

This module provides a base test case for security-related tests with
proper authentication setup and user role management.
"""

import uuid
from unittest import TestCase
from typing import Dict, List, Optional, Set, Union

import pytest
from app.core.security import RoleBasedAccessControl
from app.tests.fixtures.mock_db_fixture import MockAsyncSession


class MockEntityFactory:
    """Mock factory for generating test entities."""
    
    def __init__(self):
        self.entities = {}

    def create(self, entity_type, **kwargs):
        """Create a mock entity."""
        entity_id = kwargs.get('id', str(uuid.uuid4()))
        self.entities[entity_id] = {
            'id': entity_id,
            'type': entity_type,
            **kwargs
        }
        return self.entities[entity_id]
    
    def get(self, entity_id):
        """Retrieve a mock entity by ID."""
        return self.entities.get(entity_id)


class BaseSecurityTest(TestCase):
    """
    Base test case for security and authentication tests.
    
    This class provides common functionality for security tests including:
    - Authentication setup with test user ID and roles
    - Mock database session management
    - Authorization and role-based access control testing
    """
    
    def setUp(self) -> None:
        """Set up the test environment with authentication details and mocks."""
        super().setUp()
        
        # Initialize authentication attributes
        self.test_user_id = str(uuid.uuid4())
        self.test_roles = ['user', 'clinician']
        
        # Set up mock database and entities
        self.db_session = MockAsyncSession()
        self.entity_factory = MockEntityFactory()
        
        # Set up role-based access control for testing
        self.rbac = RoleBasedAccessControl()
        self._configure_test_rbac()
    
    def _configure_test_rbac(self) -> None:
        """Configure role-based access control with test permissions."""
        # Default role configuration for tests
        self.rbac.add_role_permission('user', 'read:own_data')
        self.rbac.add_role_permission('user', 'update:own_data')
        
        self.rbac.add_role_permission('clinician', 'read:patient_data')
        self.rbac.add_role_permission('clinician', 'update:patient_data')
        self.rbac.add_role_permission('clinician', 'read:clinical_notes')
        
        self.rbac.add_role_permission('admin', 'read:all_data')
        self.rbac.add_role_permission('admin', 'update:all_data')
        self.rbac.add_role_permission('admin', 'delete:all_data')
    
    def has_permission(self, permission: str, roles: Optional[List[str]] = None) -> bool:
        """
        Check if the specified roles have the given permission.
        
        Args:
            permission: The permission to check
            roles: The roles to check. If None, uses the test_roles
            
        Returns:
            bool: True if the roles have the permission, False otherwise
        """
        check_roles = roles if roles is not None else self.test_roles
        return self.rbac.has_permission(check_roles, permission)
    
    def get_auth_token(self, 
                       user_id: Optional[str] = None, 
                       roles: Optional[List[str]] = None,
                       custom_claims: Optional[Dict[str, any]] = None) -> str:
        """
        Generate a mock authentication token for testing.
        
        Args:
            user_id: The user ID to include in the token. Default is test_user_id.
            roles: The roles to include in the token. Default is test_roles.
            custom_claims: Additional claims to include in the token.
            
        Returns:
            str: A mock authentication token
        """
        claims = {
            'sub': user_id or self.test_user_id,
            'roles': roles or self.test_roles,
            **(custom_claims or {})
        }
        # Mock token is just the string representation of the claims for testing
        return f"mock_token.{str(claims)}"
    
    def get_auth_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """
        Generate mock authentication headers for testing.
        
        Args:
            token: The token to include in the headers. Default is generated 
                   with get_auth_token().
                   
        Returns:
            Dict[str, str]: Mock authorization headers
        """
        auth_token = token or self.get_auth_token()
        return {"Authorization": f"Bearer {auth_token}"}
    
    def tearDown(self) -> None:
        """Clean up resources after each test."""
        super().tearDown()
        
        # Clean up mock database resources
        self.db_session = None
        self.entity_factory = None
        self.rbac = None


# Define a pytest fixture for easy reuse in pytest-based tests
@pytest.fixture
def security_test_base():
    """Pytest fixture that provides a configured security test base."""
    test_base = BaseSecurityTest()
    test_base.setUp()
    yield test_base
    test_base.tearDown()


@pytest.fixture
def mock_auth_headers(security_test_base):
    """Pytest fixture that provides mock authentication headers."""
    return security_test_base.get_auth_headers()


@pytest.fixture
def mock_db_session():
    """Pytest fixture that provides a mock database session."""
    session = MockAsyncSession()
    yield session