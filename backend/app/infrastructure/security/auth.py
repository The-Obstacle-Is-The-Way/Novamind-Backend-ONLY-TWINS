# -*- coding: utf-8 -*-
"""
Authentication and Authorization Models and Exceptions

This module defines models and exceptions related to authentication
and authorization in the Novamind Digital Twin platform.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union


class TokenAuthorizationError(Exception):
    """
    Exception raised when a token is valid but lacks required permissions.
    
    This exception is distinct from authentication errors, as it occurs when
    a user is authenticated but lacks authorization for a specific resource.
    """
    def __init__(self, message: str = "Insufficient permissions"):
        self.message = message
        super().__init__(self.message)


class PermissionType(str, Enum):
    """Types of permissions that can be granted."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class RolePermission:
    """
    Defines role-based permissions for resources.
    
    This class maps roles to specific permissions on resources, enabling
    fine-grained access control throughout the system.
    """
    def __init__(
        self, 
        role_name: str,
        permissions: Dict[str, List[PermissionType]],
        description: Optional[str] = None
    ):
        """
        Initialize a new role permission mapping.
        
        Args:
            role_name: The name of the role (e.g., "psychiatrist", "admin")
            permissions: A dictionary mapping resource paths to permission types
            description: Optional description of the role's responsibilities
        """
        self.role_name = role_name
        self.permissions = permissions
        self.description = description
    
    def has_permission(
        self, 
        resource_path: str, 
        permission_type: Union[PermissionType, str]
    ) -> bool:
        """
        Check if the role has a specific permission for a resource.
        
        Args:
            resource_path: The path to the resource (e.g., "/patients")
            permission_type: The type of permission to check
            
        Returns:
            bool: True if the role has the permission, False otherwise
        """
        # Allow string or enum for permission type
        if isinstance(permission_type, str):
            permission_type = PermissionType(permission_type)
            
        # If the role has admin permission for this resource, it has all permissions
        if PermissionType.ADMIN in self.permissions.get(resource_path, []):
            return True
            
        # Check if the role has the specific permission for the resource
        return permission_type in self.permissions.get(resource_path, [])


class AuthorizationScope:
    """
    Defines a scope of authorization for specific operations.
    
    Authorization scopes provide a granular way to define what operations
    a token is allowed to perform, independent of the user's role.
    """
    def __init__(
        self,
        name: str,
        description: str,
        resources: List[str],
        operations: List[str]
    ):
        """
        Initialize a new authorization scope.
        
        Args:
            name: The scope name (e.g., "read:patients")
            description: Human-readable description of the scope
            resources: List of resources this scope applies to
            operations: List of operations allowed on these resources
        """
        self.name = name
        self.description = description
        self.resources = resources
        self.operations = operations