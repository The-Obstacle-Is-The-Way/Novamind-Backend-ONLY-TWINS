"""
Role-Based Access Control (RBAC) module for the Novamind Digital Twin Backend.

This module provides utilities for authorizing users based on their roles
and enforcing access control throughout the application.
"""
from typing import List, Optional
from fastapi import HTTPException, Request, status

from app.domain.entities.user import User
from app.domain.enums.role import Role


def check_permission(user: User, required_roles: List[Role]) -> bool:
    """
    Check if a user has any of the required roles.
    
    Args:
        user: The user to check
        required_roles: List of roles that grant permission
        
    Returns:
        True if user has permission, raises HTTPException otherwise
        
    Raises:
        HTTPException: If user doesn't have the required roles
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Check if user has any of the required roles
    for role in required_roles:
        if role in user.roles:
            return True
    
    # If we get here, user doesn't have permission
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions",
    )


class RBACMiddleware:
    """
    Middleware for enforcing role-based access control in FastAPI.
    
    This middleware can be used both as a dependency and at the application level.
    """
    
    def __init__(self):
        """Initialize the RBAC middleware."""
        pass  # No initialization needed
    
    async def __call__(self, request: Request) -> None:
        """
        Process a request and check permissions.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            None
            
        Raises:
            HTTPException: If user doesn't have access
        """
        # Get path and method for endpoint-specific rules
        path = request.url.path
        method = request.method
        
        # Apply endpoint-specific rules
        # This would typically be configured from a database or config
        if path.startswith("/api/v1/admin") and not self._has_admin_role(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator access required",
            )
            
        # PHI access audit for sensitive endpoints
        if self._endpoint_contains_phi(path, method):
            self._audit_phi_access(request)
    
    def check_access(self, request: Request, required_roles: List[Role]) -> bool:
        """
        Check if the user in the request has the required roles.
        
        Args:
            request: FastAPI request object
            required_roles: List of roles that grant access
            
        Returns:
            True if user has access, raises HTTPException otherwise
            
        Raises:
            HTTPException: If user doesn't have access
        """
        user = getattr(request.state, "user", None)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return check_permission(user, required_roles)
    
    def _has_admin_role(self, request: Request) -> bool:
        """Check if the user has the admin role."""
        user = getattr(request.state, "user", None)
        if user is None:
            return False
        return Role.ADMIN in user.roles
    
    def _endpoint_contains_phi(self, path: str, method: str) -> bool:
        """Determine if an endpoint involves PHI access."""
        # Define endpoints that contain PHI
        phi_endpoints = [
            "/api/v1/patients",
            "/api/v1/clinical-notes",
            "/api/v1/assessments",
            "/api/v1/medical-records",
            "/api/v1/diagnoses"
        ]
        
        return any(path.startswith(endpoint) for endpoint in phi_endpoints)
    
    def _audit_phi_access(self, request: Request) -> None:
        """Record PHI access for auditing purposes."""
        user = getattr(request.state, "user", None)
        if user is None:
            return
        
        # In a real implementation, this would log to a secure audit trail
        # For testing, we'll just pass
        pass