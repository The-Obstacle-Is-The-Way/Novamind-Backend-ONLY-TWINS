# -*- coding: utf-8 -*-
"""
Role-Based Access Control (RBAC) for HIPAA Compliance

This module provides RBAC functionality for the Novamind Digital Twin platform,
ensuring proper authorization for all resource access.
"""

from typing import Dict, List, Optional, Any


class RoleBasedAccessControl:
    """
    Role-Based Access Control (RBAC) implementation for HIPAA compliance.
    
    This class provides methods for enforcing role-based access control
    across the application, ensuring that users can only access resources
    they are authorized for.
    """
    
    def __init__(self, role_permissions: Optional[Dict[str, List[str]]] = None):
        """
        Initialize the RBAC system with role permissions.
        
        Args:
            role_permissions: Dict mapping roles to permissions
        """
        self._role_permissions = role_permissions or {
            "admin": ["read", "write", "delete", "manage_users", "manage_system"],
            "provider": ["read", "write", "delete"],
            "patient": ["read_own", "write_own"],
            "researcher": ["read_anonymized"],
            "auditor": ["read_logs", "read_audit"],
        }
        
    def has_permission(self, role: str, permission: str) -> bool:
        """
        Check if a role has a specific permission.
        
        Args:
            role: The user's role
            permission: The permission to check
            
        Returns:
            bool: True if the role has the permission
        """
        if role not in self._role_permissions:
            return False
            
        return permission in self._role_permissions[role]
        
    def can_access_resource(self, role: str, resource_type: str, action: str, is_owner: bool = False) -> bool:
        """
        Check if a user can access a specific resource.
        
        Args:
            role: The user's role
            resource_type: Type of resource being accessed
            action: Action being performed (read, write, delete)
            is_owner: Whether the user owns the resource
            
        Returns:
            bool: True if the user can access the resource
        """
        # Admin can do anything
        if role == "admin":
            return True
            
        # Provider can access most resources
        if role == "provider":
            if resource_type in ["patient", "appointment", "record", "note", "prescription"]:
                return True
                
        # Patients can only access their own resources
        if role == "patient" and is_owner:
            if action == "read" and resource_type in ["appointment", "record", "note", "prescription"]:
                return True
            if action == "write" and resource_type in ["appointment"]:
                return True
                
        # Researchers can access anonymized data
        if role == "researcher" and action == "read":
            if resource_type in ["anonymized_data", "statistics"]:
                return True
                
        return False
        
    def get_role_permissions(self, role: str) -> List[str]:
        """
        Get all permissions for a role.
        
        Args:
            role: The role to get permissions for
            
        Returns:
            list: List of permissions for the role
        """
        return self._role_permissions.get(role, [])
        
    def add_permission_to_role(self, role: str, permission: str) -> bool:
        """
        Add a permission to a role.
        
        Args:
            role: The role to add permission to
            permission: The permission to add
            
        Returns:
            bool: True if added successfully
        """
        if role not in self._role_permissions:
            self._role_permissions[role] = []
            
        if permission not in self._role_permissions[role]:
            self._role_permissions[role].append(permission)
            return True
            
        return False
        
    def add_role_permission(self, role: str, permission: str) -> bool:
        """
        Add a permission to a role. Alias for add_permission_to_role for test compatibility.
        
        Args:
            role: The role to add permission to
            permission: The permission to add
            
        Returns:
            bool: True if added successfully
        """
        return self.add_permission_to_role(role, permission)