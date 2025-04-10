"""
Application configuration settings.

This module provides the settings for the application, loaded from environment
variables with defaults for development. For production, all settings should be
configured through environment variables.
"""

import os
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, HttpUrl, PostgresDsn, validator


class Settings(BaseSettings):
    """Application settings.
    
    This class uses Pydantic's BaseSettings to load settings from environment
    variables. Default values are provided for development, but should be
    overridden in production using environment variables.
    """
    
    # API settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    SERVER_NAME: str = os.getenv("SERVER_NAME", "localhost")
    SERVER_HOST: AnyHttpUrl = os.getenv("SERVER_HOST", "http://localhost:8000")
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from environment variable.
        
        Args:
            v: CORS origins as a string or list of strings
            
        Returns:
            Parsed CORS origins
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database settings
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "app")
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Assemble database connection string.
        
        Args:
            v: Database connection string
            values: Settings values
            
        Returns:
            Assembled database connection string
        """
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # Security settings
    ALGORITHM: str = "HS256"
    USERS_OPEN_REGISTRATION: bool = bool(os.getenv("USERS_OPEN_REGISTRATION", "False") == "True")
    
    # AWS settings
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_PROFILE: Optional[str] = os.getenv("AWS_PROFILE")
    
    # AWS Cognito settings
    COGNITO_USER_POOL_ID: Optional[str] = os.getenv("COGNITO_USER_POOL_ID")
    COGNITO_CLIENT_ID: Optional[str] = os.getenv("COGNITO_CLIENT_ID")
    COGNITO_USER_POOL_DOMAIN: Optional[str] = os.getenv("COGNITO_USER_POOL_DOMAIN")
    
    # AWS S3 settings
    S3_BUCKET: str = os.getenv("S3_BUCKET", "novamind-app-data")
    S3_KEY_PREFIX: str = os.getenv("S3_KEY_PREFIX", "app-data")
    
    # AWS KMS settings
    KMS_KEY_ID: Optional[str] = os.getenv("KMS_KEY_ID")
    
    # Email settings
    EMAILS_ENABLED: bool = bool(os.getenv("EMAILS_ENABLED", "False") == "True")
    EMAIL_TEST_USER: str = os.getenv("EMAIL_TEST_USER", "test@example.com")
    EMAILS_FROM_EMAIL: str = os.getenv("EMAILS_FROM_EMAIL", "info@example.com")
    EMAILS_FROM_NAME: str = os.getenv("EMAILS_FROM_NAME", "NovaMind Support")
    
    # AWS SES settings
    AWS_SES_REGION: str = os.getenv("AWS_SES_REGION", "us-east-1")
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    # ML service settings
    ML_SERVICE_PROVIDER: str = os.getenv("ML_SERVICE_PROVIDER", "mock")
    ML_SERVICE_ENDPOINT: Optional[HttpUrl] = os.getenv("ML_SERVICE_ENDPOINT")
    ML_SERVICE_API_KEY: Optional[str] = os.getenv("ML_SERVICE_API_KEY")
    
    # PAT service settings
    PAT_PROVIDER: str = os.getenv("PAT_PROVIDER", "mock")
    PAT_STORAGE_PATH: str = os.getenv("PAT_STORAGE_PATH", "actigraphy-data")
    PAT_BUCKET_NAME: str = os.getenv("PAT_BUCKET_NAME", "novamind-pat-data")
    PAT_TABLE_NAME: str = os.getenv("PAT_TABLE_NAME", "novamind-pat-analyses")
    PAT_KMS_KEY_ID: str = os.getenv("PAT_KMS_KEY_ID", "")
    PAT_MODEL_ID: str = os.getenv("PAT_MODEL_ID", "amazon.titan-embed-text-v1")
    
    # Feature flags
    ENABLE_ACTIGRAPHY_ANALYSIS: bool = bool(os.getenv("ENABLE_ACTIGRAPHY_ANALYSIS", "True") == "True")
    ENABLE_DIGITAL_TWIN_INTEGRATION: bool = bool(os.getenv("ENABLE_DIGITAL_TWIN_INTEGRATION", "True") == "True")
    
    # Twilio settings for HIPAA-compliant SMS
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_MESSAGING_SERVICE_SID: Optional[str] = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
    TWILIO_FROM_NUMBER: Optional[str] = os.getenv("TWILIO_FROM_NUMBER")
    
    class Config:
        """Pydantic configuration for Settings."""
        
        case_sensitive = True
        env_file = ".env"


# Create global settings instance
settings = Settings()