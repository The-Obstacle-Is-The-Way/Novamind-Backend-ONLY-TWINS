"""
Application configuration management for the NovaMind Digital Twin system.

This module handles configuration settings for various environments (development,
testing, production) in a secure and consistent way, supporting HIPAA compliance.
"""

import os
from functools import lru_cache
from typing import Optional, Dict, Any, List

from pydantic import BaseSettings, Field, field_validator, PostgresDsn, SecretStr


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    API_V1_STR: str = Field(default="/api/v1", json_schema_extra={"env": "API_V1_STR"})
    API_V2_STR: str = Field(default="/api/v2", json_schema_extra={"env": "API_V2_STR"}) # Placeholder for future API version
    PROJECT_NAME: str = Field(default="NovaMind Digital Twin", json_schema_extra={"env": "PROJECT_NAME"})
    APP_DESCRIPTION: str = Field(default="NovaMind Digital Twin API - Powering the future of psychiatric digital twins.", json_schema_extra={"env": "APP_DESCRIPTION"})
    VERSION: str = Field(default="0.1.0", json_schema_extra={"env": "VERSION"}) # Default application version
    
    # Optional Feature Flags
    ENABLE_ANALYTICS: bool = Field(default=False, json_schema_extra={"env": "ENABLE_ANALYTICS"})

    # Optional Static File Serving
    STATIC_DIR: Optional[str] = Field(default=None, json_schema_extra={"env": "STATIC_DIR"})

    # Security settings
    SECRET_KEY: str = Field(
        default="novamind_development_secret_key_please_change_in_production", 
        json_schema_extra={"env": "SECRET_KEY"}
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, json_schema_extra={"env": "ACCESS_TOKEN_EXPIRE_MINUTES"})
    ALGORITHM: str = Field(default="HS256", json_schema_extra={"env": "ALGORITHM"})
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        json_schema_extra={"env": "BACKEND_CORS_ORIGINS"}
    )
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database
    POSTGRES_SERVER: str = Field(default="localhost", json_schema_extra={"env": "POSTGRES_SERVER"})
    POSTGRES_USER: str = Field(default="postgres", json_schema_extra={"env": "POSTGRES_USER"})
    POSTGRES_PASSWORD: str = Field(default="postgres", json_schema_extra={"env": "POSTGRES_PASSWORD"})
    POSTGRES_DB: str = Field(default="novamind", json_schema_extra={"env": "POSTGRES_DB"})
    POSTGRES_PORT: str = Field(default="5432", json_schema_extra={"env": "POSTGRES_PORT"})
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, values: dict[str, Any]) -> PostgresDsn:
        """Assemble database connection string from components."""
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=int(values.get("POSTGRES_PORT")), 
            path=values.get('POSTGRES_DB')
        )
    
    # Encryption Settings
    ENCRYPTION_KEY: Optional[str] = Field(default=None, json_schema_extra={"env": "ENCRYPTION_KEY"})
    PREVIOUS_ENCRYPTION_KEY: Optional[str] = Field(default=None, json_schema_extra={"env": "PREVIOUS_ENCRYPTION_KEY"})
    ENCRYPTION_SALT: str = Field(default="novamind-salt", json_schema_extra={"env": "ENCRYPTION_SALT"})
    
    # Other settings
    ENVIRONMENT: str = Field(default="development", json_schema_extra={"env": "ENVIRONMENT"})
    
    class Config:
        """Pydantic configuration."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings.
    
    Returns:
        Settings instance with values loaded from environment.
    """
    return Settings()