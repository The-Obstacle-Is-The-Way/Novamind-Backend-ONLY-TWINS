"""
Application settings module.

This module contains the application settings loaded from environment variables
and configuration files, using Pydantic for validation.
"""

import os
import secrets
import tempfile
from typing import List, Union, Optional, Dict, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.
    
    This class uses Pydantic to load and validate configuration 
    from environment variables and .env files.
    """
    
    # API settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    ALGORITHM: str = "HS256"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./app.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_SSL_MODE: str = "verify-full"
    DATABASE_SSL_CA: Optional[str] = None
    DATABASE_SSL_VERIFY: bool = True
    DATABASE_SSL_ENABLED: bool = False
    DATABASE_ENCRYPTION_ENABLED: bool = True
    DATABASE_AUDIT_ENABLED: bool = True
    
    # Security settings
    SECURITY_PASSWORD_SALT: str = Field(default_factory=lambda: secrets.token_hex(16))
    USE_REDIS_RATE_LIMITER: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    # Digital Twin settings
    ENABLE_BIOMETRIC_INTEGRATION: bool = True
    ENABLE_ENHANCED_ANALYTICS: bool = True
    
    # ML settings
    ML_MODEL_PATH: str = "./models"
    MENTALLLAMA_ENABLED: bool = False
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # HIPAA compliance
    PHI_AUDIT_ENABLED: bool = True
    PHI_ENCRYPTION_KEY: str = Field(default_factory=lambda: secrets.token_hex(32))
    
    # Encryption settings
    ENCRYPTION_KEY: str = Field(default_factory=lambda: secrets.token_hex(32))
    PREVIOUS_ENCRYPTION_KEY: Optional[str] = None
    ENCRYPTION_SALT: str = Field(default_factory=lambda: secrets.token_hex(16))
    
    # Audit logging
    AUDIT_LOG_DIR: str = Field(default_factory=lambda: os.path.join(tempfile.gettempdir(), "novamind_audit"))
    AUDIT_LOG_RETENTION_DAYS: int = 365  # HIPAA requires 6 years, but we set 1 year as default
    AUDIT_LOG_FORMAT: str = "%(asctime)s [AUDIT] [%(levelname)s] %(message)s"
    
    # Enhanced security settings
    ENABLE_FIELD_LEVEL_ENCRYPTION: bool = True
    ENABLE_FILE_ENCRYPTION: bool = True
    ENABLE_KEY_ROTATION: bool = True
    KEY_ROTATION_INTERVAL_DAYS: int = 90  # HIPAA best practice
    
    @field_validator("BACKEND_CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """
        Parse CORS origins from string or list.
        
        Args:
            v: String or list of origins
            
        Returns:
            List of origins or "*"
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True
    )


# Create a global settings instance
settings = Settings()