"""
User entity for the Novamind Digital Twin Backend.

This module defines the User entity representing a user in the system
with attributes and behaviors.
"""
from uuid import UUID

# Import ConfigDict for V2 style config
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.domain.enums.role import Role


class User(BaseModel):
    """
    User entity representing a user in the Novamind system.
    
    This is a domain entity containing the core user attributes
    and is independent of persistence concerns.
    """
    id: UUID = Field(..., description="Unique identifier for the user")
    username: str = Field(..., min_length=3, max_length=50, description="Username for login")
    email: EmailStr = Field(..., description="Email address of the user")
    roles: list[Role] = Field(default_factory=lambda: [Role.USER], description="User roles for authorization")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    full_name: str | None = Field(None, description="Full name of the user")
    
    # V2 Config
    model_config = ConfigDict(frozen=True)
        
    def has_role(self, role: Role) -> bool:
        """
        Check if the user has a specific role.
        
        Args:
            role: The role to check for
            
        Returns:
            True if the user has the role, False otherwise
        """
        return role in self.roles
    
    def has_any_role(self, roles: list[Role]) -> bool:
        """
        Check if the user has any of the specified roles.
        
        Args:
            roles: List of roles to check for
            
        Returns:
            True if the user has any of the roles, False otherwise
        """
        return any(role in self.roles for role in roles)

    def has_all_roles(self, roles: list[Role]) -> bool:
        """
        Check if the user has all of the specified roles.
        
        Args:
            roles: List of roles to check for
            
        Returns:
            True if the user has all of the roles, False otherwise
        """
        return all(role in self.roles for role in roles)
