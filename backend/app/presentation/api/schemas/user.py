# -*- coding: utf-8 -*-
"""
Pydantic schemas for User related data.
"""

from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, EmailStr

class UserResponseSchema(BaseModel):
    """Schema for representing a user in API responses."""
    id: UUID
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    roles: List[str] = []
    is_active: bool = True

    class Config:
        orm_mode = True # Kept for potential future ORM integration
        # Use alias for consistency if needed, e.g., alias_generator = to_camel