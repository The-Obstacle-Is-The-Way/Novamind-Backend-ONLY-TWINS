"""
Settings module for the Novamind Digital Twin Backend.

This module provides application configuration settings loaded from environment
variables and with appropriate defaults. It uses Pydantic for type validation.
"""
import os
from typing import List, Dict, Any, Optional, Union
from pydantic import Field, AnyHttpUrl, PostgresDsn, field_validator, create_model
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables with validation.
    
    This class defines all configuration parameters for the application
    with appropriate defaults and type validation.
    """
    # Base settings
    PROJECT_NAME: str = "Novamind Digital Twin"
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    APP_DESCRIPTION: str = "Advanced psychiatric digital twin platform for mental health analytics and treatment optimization"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Security and authentication
    SECRET_KEY: str = Field(default="NOVAMIND_SUPER_SECRET_KEY_THAT_IS_VERY_SECURE_12345", min_length=32)
    
    # For testing environments, allow a shorter key (only in non-production environments)
    @field_validator("SECRET_KEY", mode="before")
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate the secret key, with different rules for testing."""
        if os.environ.get("TESTING") == "true" and len(v) < 32:
            # In test mode, allow shorter keys
            return "TEST_SECRET_KEY_SECURE_ENOUGH_FOR_TESTING_ONLY_1234567890"
        return v
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql://postgres:postgres@localhost:5432/novamind"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Alias for SQLAlchemy (needed for backward compatibility)
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Alias for DATABASE_URL for SQLAlchemy compatibility."""
        return str(self.DATABASE_URL)
    
    # AWS Settings
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # XGBoost service settings
    XGBOOST_SERVICE_URL: Optional[str] = None
    XGBOOST_API_KEY: Optional[str] = None
    
    # MentalLLaMA service settings
    MENTAL_LLAMA_SERVICE_URL: Optional[str] = None
    MENTAL_LLAMA_API_KEY: Optional[str] = None
    
    # PHI access audit settings
    ENABLE_PHI_AUDITING: bool = True
    PHI_AUDIT_LOG_PATH: str = "logs/phi_access_audit.log"
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_PATH: str = "logs"
    
    # Security settings
    SECURE_SSL_REDIRECT: bool = False  # True in production
    SESSION_COOKIE_SECURE: bool = False  # True in production
    CSRF_COOKIE_SECURE: bool = False  # True in production
    SECURE_HSTS_SECONDS: int = 0  # Set to 31536000 (1 year) in production
    
    # Caching
    CACHE_TTL_SECONDS: int = 60
    
    # Digital Twin visualization settings
    DEFAULT_BRAIN_VIEW: str = "sagittal"
    NEUROTRANSMITTER_SIMULATION_STEPS: int = 100
    
    # Configuration for settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Validation for database URL
    @field_validator("DATABASE_URL", mode="before")
    def validate_database_url(cls, v: Optional[str], info) -> str:
        """Validate and construct the database URL."""
        if isinstance(v, str):
            return v
            
        # Default database URL if not provided
        return PostgresDsn.build(
            scheme="postgresql",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432",
            path=f"/novamind_development",
        )
    
    # Validation for CORS origins
    @field_validator("CORS_ORIGINS", mode="before")
    def validate_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Validate CORS origins, accepting comma-separated string or list.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError("CORS_ORIGINS should be a comma-separated string or a list")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings singleton.
    
    Returns:
        Validated Settings object
    """
    return Settings()


# Create a singleton settings instance
settings = get_settings()