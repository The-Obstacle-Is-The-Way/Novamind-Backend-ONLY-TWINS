"""
Configuration package initialization.

This module provides functions to access application configuration.
"""

from app.core.config.settings import settings


def get_settings():
    """
    Get application settings.
    
    This function provides dependency injection access to the application settings.
    
    Returns:
        Settings instance
    """
    return settings