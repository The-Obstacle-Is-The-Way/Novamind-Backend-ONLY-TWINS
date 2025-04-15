"""
Role-Based Access Control (RBAC) module for the Novamind Digital Twin Backend.

This module provides role and permission management for restricting 
access to resources based on user roles.
"""

from app.infrastructure.security.rbac.rbac import RoleBasedAccessControl
from app.infrastructure.security.rbac.role_access import RoleAccessManager
from app.infrastructure.security.rbac.role_manager import RoleManager

__all__ = ['RoleBasedAccessControl']
