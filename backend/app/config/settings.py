"""
Application configuration management for the NovaMind Digital Twin system.

This module handles configuration settings for various environments (development,
testing, production) in a secure and consistent way, supporting HIPAA compliance.
"""

import os
from functools import lru_cache
from typing import Optional, Dict, Any, List
import json # Ensure json is imported for the validator

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, PostgresDsn, SecretStr
from pydantic import ConfigDict


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
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, json_schema_extra={"env": "JWT_REFRESH_TOKEN_EXPIRE_DAYS"})
    
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
    
    # PHI Middleware Configuration
    PHI_EXCLUDE_PATHS: List[str] = Field(
        default=["/docs", "/openapi.json", "/health", "/static"],
        json_schema_extra={"env": "PHI_EXCLUDE_PATHS"}
    )
    PHI_WHITELIST_PATTERNS: Optional[Dict[str, List[str]]] = Field(
        default=None, 
        json_schema_extra={"env": "PHI_WHITELIST_PATTERNS"}
    )
    PHI_AUDIT_MODE: bool = Field(
        default=False, 
        json_schema_extra={"env": "PHI_AUDIT_MODE"}
    )
    
    @field_validator("PHI_EXCLUDE_PATHS", mode="before")
    @classmethod
    def assemble_phi_exclude_paths(cls, v: str | list[str]) -> list[str]:
        """Parse PHI exclude paths from environment variable."""
        if isinstance(v, str):
            # Handle potential JSON list string or comma-separated string
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    # Fallback to comma-separated if JSON parsing fails
                    return [i.strip() for i in v.strip("[]").split(",") if i.strip()]
            else:
                return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
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
    def assemble_db_connection(cls, v: str | None, info: Any) -> PostgresDsn:
        """Assemble database connection string from components."""
        if isinstance(v, str):
            return v
        values = info.data
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values["POSTGRES_USER"],
            password=values["POSTGRES_PASSWORD"],
            host=values["POSTGRES_SERVER"],
            port=int(values["POSTGRES_PORT"]),
            path=f"{values['POSTGRES_DB'] or ''}",
        )
    
    # Encryption Settings
    ENCRYPTION_KEY: Optional[str] = Field(default=None, json_schema_extra={"env": "ENCRYPTION_KEY"})
    PREVIOUS_ENCRYPTION_KEY: Optional[str] = Field(default=None, json_schema_extra={"env": "PREVIOUS_ENCRYPTION_KEY"})
    ENCRYPTION_SALT: str = Field(default="novamind-salt", json_schema_extra={"env": "ENCRYPTION_SALT"})
    
    # Other settings
    ENVIRONMENT: str = Field(default="development", json_schema_extra={"env": "ENVIRONMENT"})
    
    # Audit Log Settings
    AUDIT_LOG_LEVEL: str = Field(default="INFO", json_schema_extra={"env": "AUDIT_LOG_LEVEL"})
    AUDIT_LOG_TO_FILE: bool = Field(default=False, json_schema_extra={"env": "AUDIT_LOG_TO_FILE"})
    AUDIT_LOG_FILE: str = Field(default="audit.log", json_schema_extra={"env": "AUDIT_LOG_FILE"})
    EXTERNAL_AUDIT_ENABLED: bool = Field(default=False, json_schema_extra={"env": "EXTERNAL_AUDIT_ENABLED"})
    
    # Use ConfigDict for Pydantic V2 configuration
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings.
    
    Returns:
        Settings instance with values loaded from environment.
    """
    return Settings()
