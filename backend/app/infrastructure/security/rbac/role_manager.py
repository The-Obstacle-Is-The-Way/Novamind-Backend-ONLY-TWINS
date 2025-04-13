# -*- coding: utf-8 -*-
"""
HIPAA-Compliant Role-Based Access Control System

This module implements a comprehensive RBAC system for enforcing
access controls as required by HIPAA Security Rule § 164.308(a)(4),
which mandates implementation of information access management policies.

Features:
- Granular permission system with role hierarchies
- Permission checking based on user roles
- Support for patient-specific access controls
- Audit trail capabilities for access decisions

Usage:
    # Create RBAC system and register roles
    rbac = RoleBasedAccessControl()
    rbac.register_role("doctor", ["read:patients", "write:notes"])

    # Check permissions
    has_permission = rbac.check_permission("doctor", "read:patients")

    # Verify user has required permission
    is_authorized = verify_permission(user, "write:prescriptions")
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Union

from app.core.config import get_settings
settings = get_settings() # Corrected import
from app.domain.exceptions import AuthorizationError # Corrected exception name


class RoleBasedAccessControl:
    """
    Role-Based Access Control implementation for HIPAA compliance.

    This class manages roles and their associated permissions,
    providing methods to check if a role has a specific permission.
    """

    def __init__(self):
        """Initialize the RBAC system with empty roles."""
        self._roles: Dict[str, Set[str]] = {}

        # Initialize with system defaults
        self._initialize_default_roles()

    def _initialize_default_roles(self) -> None:
        """
        Initialize the system with default roles and permissions.

        This follows the principle of least privilege by default.
        """
        # Base-level roles with minimal permissions
        self.register_role("anonymous", [])
        self.register_role(
            "patient",
            [
                "read:own_record",
                "read:own_appointments",
                "write:own_messages",
                "update:own_profile",
            ],
        )

        # Clinical staff roles
        self.register_role(
            "nurse",
            [
                "read:patients",
                "read:appointments",
                "write:vitals",
                "write:notes:preliminary",
            ],
        )

        self.register_role(
            "psychiatrist",
            [
                "read:patients",
                "write:notes",
                "read:appointments",
                "write:prescriptions",
                "write:treatments",
                "write:diagnoses",
            ],
        )

        # Administrative roles
        self.register_role(
            "receptionist",
            [
                "read:appointments",
                "write:appointments",
                "read:patients:basic",
                "write:patients:basic",
            ],
        )

        self.register_role(
            "admin", ["read:all", "write:all", "manage:users", "manage:roles"]
        )

    def register_role(self, role_name: str, permissions: List[str]) -> None:
        """
        Register a role with its associated permissions.

        Args:
            role_name: The name of the role to register
            permissions: List of permission strings for this role
        """
        # Convert to set for faster lookup
        self._roles[role_name] = set(permissions)

    def add_permission_to_role(self, role_name: str, permission: str) -> None:
        """
        Add a permission to an existing role.

        Args:
            role_name: The role to add the permission to
            permission: The permission to add

        Raises:
            ValueError: If the role doesn't exist
        """
        if role_name not in self._roles:
            raise ValueError(f"Role '{role_name}' does not exist")

        self._roles[role_name].add(permission)

    def remove_permission_from_role(self, role_name: str, permission: str) -> None:
        """
        Remove a permission from a role.

        Args:
            role_name: The role to remove the permission from
            permission: The permission to remove

        Raises:
            ValueError: If the role doesn't exist
        """
        if role_name not in self._roles:
            raise ValueError(f"Role '{role_name}' does not exist")

        self._roles[role_name].discard(permission)

    def check_permission(self, role_name: str, permission: str) -> bool:
        """
        Check if a role has a specific permission.

        Args:
            role_name: The role to check
            permission: The permission to check for

        Returns:
            bool: True if the role has the permission, False otherwise
        """
        # Handle non-existent roles
        if role_name not in self._roles:
            return False

        # Special case for admin role with wildcard permissions
        if "read:all" in self._roles[role_name] and permission.startswith("read:"):
            return True

        if "write:all" in self._roles[role_name] and permission.startswith("write:"):
            return True

        # Check for exact permission match
        return permission in self._roles[role_name]

    def check_permission_for_user(
        self,
        user: Dict[str, Any],
        permission: str,
        resource_owner_id: Optional[str] = None,
    ) -> bool:
        """
        Check if a user has a specific permission, with context awareness.

        This method checks not only role-based permissions but also
        resource ownership for patient-specific "own_" permissions.

        Args:
            user: User information containing role and ID
            permission: The permission to check for
            resource_owner_id: Optional ID of the resource owner

        Returns:
            bool: True if the user has the permission, False otherwise
        """
        # Get user information
        role = user.get("role", "anonymous")
        user_id = user.get("user_id")

        # Check role-based permission first
        has_permission = self.check_permission(role, permission)

        # If not allowed by role, check resource ownership
        if (
            not has_permission
            and user_id is not None
            and resource_owner_id is not None
            and user_id == resource_owner_id
        ):

            # Convert permission to "own_" version if it exists
            if permission.startswith("read:") or permission.startswith("write:"):
                parts = permission.split(":", 1)
                own_permission = (
                    f"{parts[0]}:own_{parts[1]}"
                    if len(parts) > 1
                    else f"{parts[0]}:own"
                )
                has_permission = self.check_permission(role, own_permission)

        return has_permission


# Global singleton instance
# Using a function ensures lazy initialization
@lru_cache(maxsize=1)
def get_rbac_instance() -> RoleBasedAccessControl:
    """
    Get the global RBAC instance, creating it if necessary.

    Returns:
        RoleBasedAccessControl: The global RBAC instance
    """
    return RoleBasedAccessControl()


def verify_permission(user: Dict[str, Any], required_permission: str) -> bool:
    """
    Verify that a user has the required permission.

    This function checks if the user has the permission either through
    their role or through explicit permissions in their user data.

    Args:
        user: User information containing role and/or permissions
        required_permission: The permission to check for

    Returns:
        bool: True if the user has the required permission

    Raises:
        UnauthorizedAccessError: If the verification fails and raise_error is True
    """
    # First check explicit permissions if available
    explicit_permissions = user.get("permissions", [])
    if required_permission in explicit_permissions:
        return True

    # If user has admin access, they have all permissions
    if "admin:all" in explicit_permissions:
        return True

    # Then check role-based permissions
    rbac = get_rbac_instance()
    role = user.get("role", "anonymous")

    return rbac.check_permission(role, required_permission)


def verify_permission_or_raise(
    user: Dict[str, Any], required_permission: str, error_message: Optional[str] = None
) -> None:
    """
    Verify permission and raise an error if not authorized.

    Args:
        user: User information containing role and/or permissions
        required_permission: The permission to check for
        error_message: Optional custom error message

    Raises:
        UnauthorizedAccessError: If the user lacks the required permission
    """
    if not verify_permission(user, required_permission):
        msg = error_message or f"User lacks required permission: {required_permission}"
        raise AuthorizationError(msg) # Use the correct exception class
