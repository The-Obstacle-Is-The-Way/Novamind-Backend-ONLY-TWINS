# -*- coding: utf-8 -*-
"""
Role-Based Access Control (RBAC) for Novamind Digital Twin

This module provides a robust RBAC implementation for the Novamind Digital Twin platform,
ensuring proper authorization and access control in accordance with HIPAA requirements.
"""

from typing import Dict, List, Set, Optional, Union, Any
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    """Enumeration of resource types in the system."""
    PATIENT = "patient"
    CLINICIAN = "clinician"
    ANALYSIS = "analysis"
    REPORT = "report"
    TWIN = "digital_twin"
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    ACTIGRAPHY = "actigraphy"
    ADMIN = "admin"


class Permission(str, Enum):
    """Permissions that can be granted to roles."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class Role(str, Enum):
    """System roles available in the platform."""
    PATIENT = "patient"
    PSYCHIATRIST = "psychiatrist"
    THERAPIST = "therapist"
    RESEARCHER = "researcher"
    ADMIN = "admin"
    READONLY = "readonly"
    SYSADMIN = "sysadmin"


class RoleBasedAccessControl:
    """
    Provides role-based access control for the Novamind Digital Twin platform.
    
    This class implements a comprehensive RBAC system that maps roles to permissions
    on different resource types, and enforces access control based on those mappings.
    """
    
    def __init__(self) -> None:
        """Initialize the RBAC system with default role-permission mappings."""
        # Initialize role -> permissions mapping
        self._role_permissions: Dict[str, Dict[str, Set[str]]] = {
            Role.PATIENT: {
                ResourceType.PATIENT: {Permission.READ},
                ResourceType.APPOINTMENT: {Permission.READ},
                ResourceType.MEDICATION: {Permission.READ},
                ResourceType.ANALYSIS: {Permission.READ},
                ResourceType.ACTIGRAPHY: {Permission.READ, Permission.WRITE},
            },
            Role.PSYCHIATRIST: {
                ResourceType.PATIENT: {Permission.READ, Permission.WRITE},
                ResourceType.CLINICIAN: {Permission.READ},
                ResourceType.ANALYSIS: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
                ResourceType.REPORT: {Permission.READ, Permission.WRITE},
                ResourceType.TWIN: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
                ResourceType.MEDICATION: {Permission.READ, Permission.WRITE},
                ResourceType.APPOINTMENT: {Permission.READ, Permission.WRITE},
                ResourceType.ACTIGRAPHY: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
            },
            Role.THERAPIST: {
                ResourceType.PATIENT: {Permission.READ},
                ResourceType.ANALYSIS: {Permission.READ},
                ResourceType.REPORT: {Permission.READ, Permission.WRITE},
                ResourceType.APPOINTMENT: {Permission.READ, Permission.WRITE},
            },
            Role.RESEARCHER: {
                ResourceType.ANALYSIS: {Permission.READ, Permission.EXECUTE},
                ResourceType.TWIN: {Permission.READ, Permission.EXECUTE},
                ResourceType.REPORT: {Permission.READ},
            },
            Role.ADMIN: {
                resource_type.value: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.EXECUTE, Permission.ADMIN}
                for resource_type in ResourceType
            },
            Role.READONLY: {
                resource_type.value: {Permission.READ}
                for resource_type in ResourceType
            },
            Role.SYSADMIN: {
                resource_type.value: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.EXECUTE, Permission.ADMIN}
                for resource_type in ResourceType
            },
        }
        
        # Initialize method -> permissions mapping
        self._method_permissions: Dict[str, str] = {
            "GET": Permission.READ,
            "HEAD": Permission.READ,
            "OPTIONS": Permission.READ,
            "POST": Permission.WRITE,
            "PUT": Permission.WRITE,
            "PATCH": Permission.WRITE,
            "DELETE": Permission.DELETE,
        }
        
        # Special owner relationships (e.g., patients can access their own data)
        self._owner_permissions: Dict[str, Dict[str, Set[str]]] = {
            Role.PATIENT: {
                ResourceType.PATIENT: {Permission.READ, Permission.WRITE},
                ResourceType.ANALYSIS: {Permission.READ},
                ResourceType.REPORT: {Permission.READ},
                ResourceType.MEDICATION: {Permission.READ},
                ResourceType.APPOINTMENT: {Permission.READ, Permission.WRITE},
                ResourceType.ACTIGRAPHY: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
            }
        }
        
        logger.info("Role-Based Access Control system initialized")
    
    def has_permission(self, 
                      user_role: str, 
                      resource_type: str, 
                      permission: str, 
                      is_owner: bool = False) -> bool:
        """
        Check if a user role has a specific permission on a resource type.
        
        Args:
            user_role: The role of the user
            resource_type: The type of resource being accessed
            permission: The permission being checked
            is_owner: Whether the user owns the resource
            
        Returns:
            bool: True if the user has permission, False otherwise
        """
        # Admin always has all permissions
        if user_role == Role.ADMIN or user_role == Role.SYSADMIN:
            return True
            
        # Check owner-specific permissions first
        if is_owner and user_role in self._owner_permissions:
            owner_perms = self._owner_permissions.get(user_role, {})
            if resource_type in owner_perms and permission in owner_perms[resource_type]:
                return True
        
        # Check role-based permissions
        role_perms = self._role_permissions.get(user_role, {})
        if resource_type in role_perms and permission in role_perms[resource_type]:
            return True
            
        return False
    
    def get_allowed_roles(self, resource_type: str, permission: str) -> List[str]:
        """
        Get all roles that have a specific permission on a resource type.
        
        Args:
            resource_type: The type of resource being accessed
            permission: The permission being checked
            
        Returns:
            List[str]: List of roles with the specified permission
        """
        allowed_roles = []
        for role, permissions in self._role_permissions.items():
            if resource_type in permissions and permission in permissions[resource_type]:
                allowed_roles.append(role)
        return allowed_roles
    
    def check_access(self, 
                    user_roles: List[str], 
                    resource_type: str, 
                    http_method: str,
                    is_owner: bool = False) -> bool:
        """
        Check if a user with given roles can access a resource with a specific HTTP method.
        
        Args:
            user_roles: List of user roles
            resource_type: The type of resource being accessed
            http_method: The HTTP method being used (GET, POST, etc.)
            is_owner: Whether the user owns the resource
            
        Returns:
            bool: True if access is allowed, False otherwise
        """
        required_permission = self._method_permissions.get(http_method.upper(), Permission.READ)
        
        # Check each role
        for role in user_roles:
            if self.has_permission(role, resource_type, required_permission, is_owner):
                return True
                
        return False
    
    def map_http_method_to_permission(self, http_method: str) -> str:
        """
        Map an HTTP method to a permission.
        
        Args:
            http_method: The HTTP method (GET, POST, etc.)
            
        Returns:
            str: The corresponding permission
        """
        return self._method_permissions.get(http_method.upper(), Permission.READ)