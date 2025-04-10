# -*- coding: utf-8 -*-
# app/domain/value_objects/address.py
"""Address value object."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Address:
    """
    Immutable value object representing a physical address.
    
    Follows HIPAA best practices for storing address information.
    """
    
    street: str
    city: str
    state: str
    zip_code: str
    country: Optional[str] = "USA"
    
    def __post_init__(self) -> None:
        """Validate address after initialization."""
        if not self.street:
            raise ValueError("Street is required")
        
        if not self.city:
            raise ValueError("City is required")
        
        if not self.state:
            raise ValueError("State is required")
        
        if not self.zip_code:
            raise ValueError("ZIP code is required")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country
        }
    
    def __str__(self) -> str:
        """Get string representation."""
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"
