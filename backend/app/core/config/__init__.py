"""
Configuration package for the Novamind Digital Twin Backend.

This package contains configuration management functionality, including
environment variable parsing, application settings, and secrets management.
"""

from app.core.config.settings import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]