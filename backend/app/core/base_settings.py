# -*- coding: utf-8 -*-
"""
Base Settings.

This module provides the base settings class for all application settings.
"""

from typing import Any, Dict, Optional, Tuple, Type
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic import validator


class BaseSettings(PydanticBaseSettings):
    """
    Base settings class for all application settings.
    
    This class extends Pydantic's settings management to provide common
    functionality for all setting classes in the application.
    """
    
    class Config:
        """Configuration for base settings."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in environment
        validate_assignment = True  # Validate when assigning new values
        
    def get_section(self, section_name: str) -> Dict[str, Any]:
        """
        Get a section of settings with a common prefix.
        
        This method helps retrieve grouped settings for specific components
        or services based on a common prefix.
        
        Args:
            section_name: The prefix for settings to retrieve
            
        Returns:
            Dictionary of settings in the specified section
        """
        return {
            k.replace(f"{section_name}_", ""): v
            for k, v in self.dict().items()
            if k.startswith(f"{section_name}_")
        }
        
    @classmethod
    def get_validators(cls) -> Dict[str, classmethod]:
        """
        Get all validators defined in this class.
        
        Returns:
            Dictionary mapping field names to validator methods
        """
        validators = {}
        for name, method in cls.__dict__.items():
            if hasattr(method, "__is_validator__"):
                validators[name] = method
        return validators
    
    @classmethod
    def validate_field(
        cls, field_name: str, value: Any, validator_name: Optional[str] = None
    ) -> Any:
        """
        Validate a field using the class validators.
        
        This method helps test validation rules for individual fields
        outside of the normal Pydantic validation flow.
        
        Args:
            field_name: The name of the field to validate
            value: The value to validate
            validator_name: Optional name of specific validator to use
            
        Returns:
            The validated value
            
        Raises:
            ValueError: If validation fails
        """
        validators = cls.get_validators()
        
        if validator_name:
            if validator_name not in validators:
                raise ValueError(f"Validator {validator_name} not found")
            return validators[validator_name](cls, value)
        
        # Find validators that might apply to this field
        for name, validator_method in validators.items():
            # Check if validator applies to this field
            if hasattr(validator_method, "fields") and field_name in validator_method.fields:
                value = validator_method(cls, value)
                
        return value