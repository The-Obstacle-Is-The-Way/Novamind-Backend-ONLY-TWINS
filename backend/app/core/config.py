"""
Application configuration settings.

This module contains settings for the entire application, loaded from
environment variables and default values. It follows the 12-factor app
methodology for configuration.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    This uses pydantic for validation and loading from .env files.
    """
    # Project info
    PROJECT_NAME: str = "Novamind Digital Twin"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_THIS_TO_A_PROPER_SECRET_IN_PRODUCTION")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Backend URLs
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origin setting from comma-separated string."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "")
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Assemble database URI from components."""
        if isinstance(v, str):
            return v
        
        server = values.data.get("POSTGRES_SERVER")
        user = values.data.get("POSTGRES_USER")
        password = values.data.get("POSTGRES_PASSWORD")
        db = values.data.get("POSTGRES_DB")
        
        if all([server, user, password, db]):
            # PostgreSQL connection string
            return f"postgresql+asyncpg://{user}:{password}@{server}/{db}"
            # For tests (defaults to using async drivers)
        
        # Default to SQLite for development
        base_dir = Path(__file__).resolve().parent.parent.parent
        return f"sqlite+aiosqlite:///{base_dir}/novamind.db"
    
    # HIPAA Settings
    AUDIT_LOG_ENABLED: bool = True
    PHI_ANONYMIZATION_ENABLED: bool = True
    SESSION_TIMEOUT_MINUTES: int = 30  # Auto-logout for inactivity
    
    # Digital Twin settings
    DEFAULT_TIME_SERIES_DAYS: int = 90
    DEFAULT_TIME_STEP_HOURS: int = 24
    
    # AWS Cognito (optional, for production)
    COGNITO_USER_POOL_ID: Optional[str] = None
    COGNITO_APP_CLIENT_ID: Optional[str] = None
    COGNITO_REGION: str = "us-east-1"
    
    # XGBoost model settings
    XGBOOST_MODEL_PATH: Optional[str] = None
    
    # LLM settings
    MENTALLLAMA_API_URL: Optional[str] = None
    MENTALLLAMA_API_KEY: Optional[str] = None
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Create a global settings object
settings = Settings()
