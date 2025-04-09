"""
User entity for authentication and authorization.

This module defines the User domain entity which is used for authentication,
authorization, and tracking user actions in the system.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID


class User:
    """
    User domain entity.
    
    This class represents a user in the system, which could be a clinician,
    administrator, or patient. It contains the essential user data required
    for authentication and authorization.
    """
    
    def __init__(
        self,
        id: UUID,
        email: str,
        first_name: str,
        last_name: str,
        hashed_password: str,
        is_active: bool = True,
        roles: List[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        Initialize a User entity.
        
        Args:
            id: Unique identifier for the user
            email: User's email address
            first_name: User's first name
            last_name: User's last name
            hashed_password: Securely hashed password
            is_active: Whether the user account is active
            roles: List of roles assigned to the user
            created_at: When the user was created
            updated_at: When the user was last updated
        """
        self.id = id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.hashed_password = hashed_password
        self.is_active = is_active
        self.roles = roles or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def has_role(self, role: str) -> bool:
        """
        Check if the user has a specific role.
        
        Args:
            role: Role to check
            
        Returns:
            True if the user has the specified role
        """
        return role in self.roles
    
    def add_role(self, role: str) -> None:
        """
        Add a role to the user.
        
        Args:
            role: Role to add
        """
        if role not in self.roles:
            self.roles.append(role)
            self.updated_at = datetime.utcnow()
    
    def remove_role(self, role: str) -> None:
        """
        Remove a role from the user.
        
        Args:
            role: Role to remove
        """
        if role in self.roles:
            self.roles.remove(role)
            self.updated_at = datetime.utcnow()
