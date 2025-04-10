# -*- coding: utf-8 -*-
"""
Role-Based Access Control (RBAC) Module

This module implements RBAC functionality to manage permissions and roles
for the Digital Twin system, ensuring proper authorization across the platform.
"""

from typing import Dict, List, Optional, Set


class RoleBasedAccessControl:
    """
    Role-Based Access Control implementation for the Digital Twin platform.
    
    This class manages role-permission relationships and provides
    methods for authorization checks throughout the application.
    """
    
    def __init__(self):
        """Initialize the RBAC system with empty role-permission mappings."""
        self._role_permissions: Dict[str, Set[str]] = {}
    
    def add_role(self, role: str) -> None:
        """
        Add a new role to the RBAC system.
        
        Args:
            role: The name of the role to add
        """
        if role not in self._role_permissions:
            self._role_permissions[role] = set()
    
    def add_role_permission(self, role: str, permission: str) -> None:
        """
        Assign a permission to a role.
        
        Args:
            role: The role to which the permission is assigned
            permission: The permission to assign
        """
        if role not in self._role_permissions:
            self._role_permissions[role] = set()
        
        self._role_permissions[role].add(permission)
    
    def remove_role_permission(self, role: str, permission: str) -> None:
        """
        Remove a permission from a role.
        
        Args:
            role: The role from which the permission is removed
            permission: The permission to remove
        """
        if role in self._role_permissions and permission in self._role_permissions[role]:
            self._role_permissions[role].remove(permission)
    
    def has_permission(self, roles: List[str], permission: str) -> bool:
        """
        Check if any of the provided roles have the specified permission.
        
        Args:
            roles: List of roles to check
            permission: The permission to verify
            
        Returns:
            bool: True if any role has the permission, False otherwise
        """
        for role in roles:
            if role in self._role_permissions and permission in self._role_permissions[role]:
                return True
        
        return False
    
    def get_role_permissions(self, role: str) -> Set[str]:
        """
        Get all permissions assigned to a role.
        
        Args:
            role: The role to query
            
        Returns:
            Set[str]: Set of permissions assigned to the role
        """
        return self._role_permissions.get(role, set()).copy()
    
    def get_roles_with_permission(self, permission: str) -> List[str]:
        """
        Get all roles that have a specific permission.
        
        Args:
            permission: The permission to query
            
        Returns:
            List[str]: List of roles that have the permission
        """
        return [
            role for role, permissions in self._role_permissions.items() 
            if permission in permissions
        ]