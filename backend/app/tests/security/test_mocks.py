"""
Mock classes and utilities for security testing.

This module provides mock implementations of various security-related classes
to facilitate testing without requiring actual database connections or external services.
"""
import uuid
from typing import Any, Dict, List, Optional


class MockAsyncSession:
    """Mock implementation of an async database session."""

    def __init__(self):
        """Initialize the mock session."""
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.queries = []
        self.entities = {}

        async def commit(self):
        """Mock commit operation."""
        self.committed = True
        return True

        async def rollback(self):
        """Mock rollback operation."""
        self.rolled_back = True
        return True

        async def close(self):
        """Mock close operation."""
        self.closed = True
        return True

        async def execute(self, query, params=None):
        """Mock query execution."""
        self.queries.append((query, params))
        return MockResult([])

        async def scalar(self, query, params=None):
        """Mock scalar query execution."""
        self.queries.append((query, params))
        return None

        class MockResult:
    """Mock result from a database query."""

    def __init__(self, data):
        """Initialize with result data."""
        self.data = data

        def fetchall(self):
        """Return all results."""
        return self.data

        def fetchone(self):
        """Return first result or None."""
        return self.data[0] if self.data else None

        class MockEntityFactory:
    """Mock factory for creating test entities."""

    def __init__(self):
        """Initialize the entity factory."""
        self.entities = {}

        def create(self, entity_type: str, **kwargs) -> Dict[str, Any]:
        """Create a mock entity with the given attributes."""
        entity_id = str(uuid.uuid4())
        entity = {"id": entity_id, "type": entity_type, **kwargs}
        self.entities[entity_id] = entity
        return entity

        def get(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get an entity by ID."""
        return self.entities.get(entity_id)

        def list(self, entity_type: str = None) -> List[Dict[str, Any]]:
        """List all entities, optionally filtered by type."""
        if entity_type:
            return [e for e in self.entities.values() if e.get("type")
                    == entity_type]
            return list(self.entities.values())

            def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        if entity_id in self.entities:
            del self.entities[entity_id]
            return True
            return False

            class RoleBasedAccessControl:
    """Mock role-based access control for testing."""

    def __init__(self):
        """Initialize the RBAC system."""
        self.role_permissions = {}

        def add_role_permission(self, role: str, permission: str) -> None:
        """Add a permission to a role."""
        if role not in self.role_permissions:
            self.role_permissions[role] = set()
            self.role_permissions[role].add(permission)

            def remove_role_permission(
                    self, role: str, permission: str) -> None:
        """Remove a permission from a role."""
        if role in self.role_permissions and permission in self.role_permissions[role]:
            self.role_permissions[role].remove(permission)

            def has_permission(self, role: str, permission: str) -> bool:
        """Check if a role has a specific permission."""
        return (
            role in self.role_permissions and permission in self.role_permissions[role])

    def get_role_permissions(self, role: str) -> List[str]:
        """Get all permissions for a role."""
        return list(self.role_permissions.get(role, set()))
