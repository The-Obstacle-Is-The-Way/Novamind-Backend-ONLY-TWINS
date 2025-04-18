"""
User entity for the Novamind Digital Twin Backend.

This module defines the User entity representing a user in the system
with attributes and behaviors.
"""
# NOTE:  The unit‑test suite sometimes passes a *UUID* instance for the user
# ``id`` field.  Previously the model required a *string*, which caused those
# tests to fail.  To remain permissive we now accept *either* a ``UUID`` or a
# ``str``; the value is coerced to ``str`` so the rest of the codebase
# continues to treat ``id`` uniformly as a string.

from uuid import UUID
from typing import Union, List

# Import ConfigDict for V2 style config
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.domain.enums.role import Role as DomainRole


class User(BaseModel):
    """
    User entity representing a user in the Novamind system.
    
    This is a domain entity containing the core user attributes
    and is independent of persistence concerns.
    """
    # Simplified fields for compatibility with RBAC & API tests
    id: Union[str, UUID] = Field(..., description="Unique identifier for the user")
    username: str | None = Field(default=None, description="Username for login (optional)")
    email: EmailStr = Field(..., description="Email address of the user")
    # Hashed password to satisfy authentication requirements
    hashed_password: str | None = Field(default=None, description="Hashed password for the user")
    # Accept arbitrary role values (e.g., infrastructure Role enums) for authorization
    roles: List[str] = Field(default_factory=list, description="User roles for authorization")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    full_name: str | None = Field(None, description="Full name of the user")
    
    # V2 Config
    model_config = ConfigDict(frozen=True)

    # ---------------------------------------------------------------------
    # Validators / post‑processing
    # ---------------------------------------------------------------------

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, value):  # noqa: D401 – simple coercion helper
        """Coerce UUID → str to keep a consistent internal representation."""
        if isinstance(value, UUID):
            return str(value)
        return value
        
    def has_role(self, role) -> bool:
        """
        Check if the user has a specific role.
        
        Args:
            role: The role to check for
            
        Returns:
            True if the user has the role, False otherwise
        """
        return role in self.roles
    
    def has_any_role(self, roles) -> bool:
        """
        Check if the user has any of the specified roles.
        
        Args:
            roles: List of roles to check for
            
        Returns:
            True if the user has any of the roles, False otherwise
        """
        return any(role in self.roles for role in roles)

    def has_all_roles(self, roles) -> bool:
        """
        Check if the user has all of the specified roles.
        
        Args:
            roles: List of roles to check for
            
        Returns:
            True if the user has all of the roles, False otherwise
        """
        return all(role in self.roles for role in roles)
