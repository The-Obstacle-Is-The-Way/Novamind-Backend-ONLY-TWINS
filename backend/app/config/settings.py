"""
Application configuration management for the NovaMind Digital Twin system.

This module handles configuration settings for various environments (development,
testing, production) in a secure and consistent way, supporting HIPAA compliance.
"""

import os
from functools import lru_cache
from typing import Optional, Dict, Any, List, Union
import json # Ensure json is imported for the validator

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator, PostgresDsn, SecretStr, HttpUrl, ConfigDict


# --- ML Settings Sub-Models ---

class MentalLlamaSettings(BaseSettings):
    model_config = ConfigDict(env_prefix='MENTALLAMA_') # Prefix for env vars

    provider: str = Field(default="openai", json_schema_extra={"env": "PROVIDER"}) # openai, azure, local, custom
    openai_api_key: Optional[SecretStr] = Field(default=None, json_schema_extra={"env": "OPENAI_API_KEY"})
    openai_organization: Optional[str] = Field(default=None, json_schema_extra={"env": "OPENAI_ORGANIZATION"})
    azure_api_key: Optional[SecretStr] = Field(default=None, json_schema_extra={"env": "AZURE_API_KEY"})
    azure_endpoint: Optional[str] = Field(default=None, json_schema_extra={"env": "AZURE_ENDPOINT"}) # Store as str, validate if needed
    azure_deployment: Optional[str] = Field(default=None, json_schema_extra={"env": "AZURE_DEPLOYMENT"})
    azure_api_version: Optional[str] = Field(default="2023-05-15", json_schema_extra={"env": "AZURE_API_VERSION"})
    local_url: Optional[str] = Field(default=None, json_schema_extra={"env": "LOCAL_URL"}) # Store as str, validate if needed
    custom_url: Optional[str] = Field(default=None, json_schema_extra={"env": "CUSTOM_URL"}) # Store as str, validate if needed
    custom_api_key: Optional[SecretStr] = Field(default=None, json_schema_extra={"env": "CUSTOM_API_KEY"})
    request_timeout: int = Field(default=60, json_schema_extra={"env": "REQUEST_TIMEOUT"})
    # Example: {"mentallama-clinical": "gpt-4", "mentallama-psychiatry": "azure-deployment-name"}
    model_mappings: Dict[str, str] = Field(default_factory=dict, json_schema_extra={"env": "MODEL_MAPPINGS"}) # Need validation if env var is string

    @field_validator("model_mappings", mode='before')
    @classmethod
    def parse_model_mappings(cls, v: Union[str, Dict]) -> Dict[str, str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON string for MENTALLAMA_MODEL_MAPPINGS")
        return v

class PATSettings(BaseSettings):
    model_config = ConfigDict(env_prefix='PAT_')

    model_path: str = Field(default="/models/pat/pat-medium", json_schema_extra={"env": "MODEL_PATH"})
    cache_dir: str = Field(default="/cache/pat", json_schema_extra={"env": "CACHE_DIR"})
    use_gpu: bool = Field(default=True, json_schema_extra={"env": "USE_GPU"})
    results_storage_path: str = Field(default="/storage/pat_results", json_schema_extra={"env": "RESULTS_STORAGE_PATH"})

class XGBoostSettings(BaseSettings):
    model_config = ConfigDict(env_prefix='XGBOOST_')

    # Example: Define paths for different XGBoost models
    treatment_response_model_path: str = Field(default="/models/xgboost/treatment_response.xgb", json_schema_extra={"env": "TREATMENT_RESPONSE_MODEL_PATH"})
    outcome_prediction_model_path: str = Field(default="/models/xgboost/outcome_prediction.xgb", json_schema_extra={"env": "OUTCOME_PREDICTION_MODEL_PATH"})
    risk_prediction_model_path: str = Field(default="/models/xgboost/risk_prediction.xgb", json_schema_extra={"env": "RISK_PREDICTION_MODEL_PATH"})

class LSTMSettings(BaseSettings):
    model_config = ConfigDict(env_prefix='LSTM_')

    biometric_correlation_model_path: str = Field(default="/models/lstm/biometric_correlation.pkl", json_schema_extra={"env": "BIOMETRIC_CORRELATION_MODEL_PATH"})

class PHIDetectionSettings(BaseSettings):
    model_config = ConfigDict(env_prefix='PHI_DETECTION_') # Changed prefix to avoid clash

    patterns_file: str = Field(default="app/infrastructure/security/phi/phi_patterns.yaml", json_schema_extra={"env": "PATTERNS_FILE"})
    default_redaction_format: str = Field(default="[{category}]", json_schema_extra={"env": "DEFAULT_REDACTION_FORMAT"})
    parallel_processing: bool = Field(default=True, json_schema_extra={"env": "PARALLEL_PROCESSING"})
    # Add other Presidio/PHI settings if needed

class MLSettings(BaseSettings):
    """Container for all ML model settings."""
    # General ML paths (can be overridden by specific model settings if needed)
    models_path: str = Field(default="/models", json_schema_extra={"env": "ML_MODELS_PATH"})
    cache_path: str = Field(default="/cache", json_schema_extra={"env": "ML_CACHE_PATH"})
    storage_path: str = Field(default="/storage", json_schema_extra={"env": "ML_STORAGE_PATH"})

    # Specific model settings
    mentallama: MentalLlamaSettings = Field(default_factory=MentalLlamaSettings)
    pat: PATSettings = Field(default_factory=PATSettings)
    xgboost: XGBoostSettings = Field(default_factory=XGBoostSettings)
    lstm: LSTMSettings = Field(default_factory=LSTMSettings)
    phi_detection: PHIDetectionSettings = Field(default_factory=PHIDetectionSettings)


# --- Main Settings Class ---

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    API_V1_STR: str = Field(default="/api/v1", json_schema_extra={"env": "API_V1_STR"})
    API_V2_STR: str = Field(default="/api/v2", json_schema_extra={"env": "API_V2_STR"}) # Placeholder for future API version
    PROJECT_NAME: str = Field(default="Novamind Digital Twin", json_schema_extra={"env": "PROJECT_NAME"})
    # Environment
    ENVIRONMENT: str = Field(default="development", json_schema_extra={"env": "ENVIRONMENT"})
    APP_DESCRIPTION: str = Field(default="NovaMind Digital Twin API - Powering the future of psychiatric digital twins.", json_schema_extra={"env": "APP_DESCRIPTION"})
    VERSION: str = Field(default="0.1.0", json_schema_extra={"env": "VERSION"}) # Default application version
    
    # Optional Feature Flags
    ENABLE_ANALYTICS: bool = Field(default=False, json_schema_extra={"env": "ENABLE_ANALYTICS"})
    # PHI Auditing Legacy Flag
    ENABLE_PHI_AUDITING: bool = Field(default=True, json_schema_extra={"env": "ENABLE_PHI_AUDITING"})

    # Optional Static File Serving
    STATIC_DIR: Optional[str] = Field(default=None, json_schema_extra={"env": "STATIC_DIR"})

    # Security settings
    SECRET_KEY: SecretStr = Field(
        ..., # Remove default, force loading from env/.env
        json_schema_extra={"env": "SECRET_KEY"}
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, json_schema_extra={"env": "ACCESS_TOKEN_EXPIRE_MINUTES"})
    ALGORITHM: str = Field(default="HS256", json_schema_extra={"env": "ALGORITHM"})
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, json_schema_extra={"env": "JWT_REFRESH_TOKEN_EXPIRE_DAYS"})
    
    # MFA Settings
    MFA_SECRET_KEY: SecretStr = Field(
        default="dev_mfa_secret", 
        json_schema_extra={"env": "MFA_SECRET_KEY"}
    )
    MFA_ISSUER_NAME: str = Field(default="NovaMind Psychiatry", json_schema_extra={"env": "MFA_ISSUER_NAME"})
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        json_schema_extra={"env": "BACKEND_CORS_ORIGINS"}
    )
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from environment variable."""
        if isinstance(v, str):
            # Handle comma-separated string
            if v.startswith('[') and v.endswith(']'):
                 try:
                     # Try parsing as JSON list
                     return json.loads(v)
                 except json.JSONDecodeError:
                     # Fallback to comma-separated if JSON fails
                     return [origin.strip() for origin in v.strip('[]').split(",") if origin.strip()]
            else:
                 # Assume comma-separated without brackets
                 return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        raise ValueError(f"Invalid BACKEND_CORS_ORIGINS: {v}")
    
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
    
    @field_validator("PHI_WHITELIST_PATTERNS", mode='before')
    @classmethod
    def parse_phi_whitelist(cls, v: Union[str, Dict, None]) -> Optional[Dict[str, List[str]]]:
         if isinstance(v, str):
             try:
                 return json.loads(v)
             except json.JSONDecodeError:
                 raise ValueError("Invalid JSON string for PHI_WHITELIST_PATTERNS")
         return v

    @field_validator("PHI_EXCLUDE_PATHS", mode='before')
    @classmethod
    def parse_phi_exclude(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith('[') and v.endswith(']'):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [path.strip() for path in v.strip('[]').split(',') if path.strip()]
            else:
                return [path.strip() for path in v.split(',') if path.strip()]
        elif isinstance(v, list):
             return v
        raise ValueError(f"Invalid PHI_EXCLUDE_PATHS: {v}")

    # Database
    DATABASE_URL: Optional[str] = Field(default=None, json_schema_extra={"env": "DATABASE_URL"}) # Store as str for flexibility
    POSTGRES_SERVER: str = Field(default="localhost", json_schema_extra={"env": "POSTGRES_SERVER"})
    POSTGRES_USER: str = Field(default="postgres", json_schema_extra={"env": "POSTGRES_USER"})
    POSTGRES_PASSWORD: SecretStr = Field(default="postgres", json_schema_extra={"env": "POSTGRES_PASSWORD"}) # Use SecretStr
    POSTGRES_DB: str = Field(default="novamind", json_schema_extra={"env": "POSTGRES_DB"})
    POSTGRES_PORT: int = Field(default=5432, json_schema_extra={"env": "POSTGRES_PORT"})
    DB_POOL_SIZE: int = Field(default=5, json_schema_extra={"env": "DB_POOL_SIZE"})
    DB_MAX_OVERFLOW: int = Field(default=10, json_schema_extra={"env": "DB_MAX_OVERFLOW"})
    DATABASE_ECHO: bool = Field(default=False, json_schema_extra={"env": "DATABASE_ECHO"}) # Added DB Echo
    DATABASE_SSL_MODE: Optional[str] = Field(default=None, json_schema_extra={"env": "DATABASE_SSL_MODE"}) # Added SSL
    DATABASE_SSL_CA: Optional[str] = Field(default=None, json_schema_extra={"env": "DATABASE_SSL_CA"})
    
    @model_validator(mode="after")
    def _set_debug_env(cls, values):  # type: ignore
        """Set DEBUG env var for testing environment."""
        try:
            env = values.ENVIRONMENT
        except Exception:
            env = os.getenv("ENVIRONMENT")
        if env == "testing" or os.getenv("TESTING") == "1":
            os.environ["DEBUG"] = "1"
        # Support legacy CORS_ORIGINS env var for tests
        cors_env = os.getenv("CORS_ORIGINS")
        if cors_env:
            # Parse comma-separated or JSON list
            try:
                if cors_env.startswith('[') and cors_env.endswith(']'):
                    parsed = json.loads(cors_env)
                else:
                    parsed = [origin.strip() for origin in cors_env.split(',') if origin.strip()]
                values.BACKEND_CORS_ORIGINS = parsed
            except Exception:
                # leave default if parse fails
                pass
        return values
    
    @property
    def CORS_ORIGINS(self) -> list[str]:
        """Alias for BACKEND_CORS_ORIGINS"""
        return self.BACKEND_CORS_ORIGINS
    # SQLAlchemy compatibility
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> Optional[str]:
        """Alias for DATABASE_URL for compatibility."""
        return self.DATABASE_URL
    DATABASE_SSL_VERIFY: Optional[bool] = Field(default=None, json_schema_extra={"env": "DATABASE_SSL_VERIFY"})
    DATABASE_ENCRYPTION_ENABLED: bool = Field(default=False, json_schema_extra={"env": "DATABASE_ENCRYPTION_ENABLED"})
    DATABASE_AUDIT_ENABLED: bool = Field(default=False, json_schema_extra={"env": "DATABASE_AUDIT_ENABLED"})

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Union[str, None], info: Any) -> Union[str, None]:
        if isinstance(v, str) and v:
            # If DATABASE_URL is explicitly set, use it directly
            return v
        values = info.data
        # Construct DSN only if components are present and DATABASE_URL wasn't set
        if all(k in values for k in ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_SERVER", "POSTGRES_PORT", "POSTGRES_DB"]):
             # Use pydantic's PostgresDsn just for validation/building, but store as string
             dsn = PostgresDsn.build(
                 scheme="postgresql+asyncpg",
                 username=values["POSTGRES_USER"],
                 password=str(values["POSTGRES_PASSWORD"]), # Convert SecretStr
                 host=values["POSTGRES_SERVER"],
                 port=values["POSTGRES_PORT"],
                 path=f"/{values['POSTGRES_DB']}", # Ensure path starts with /
             )
             return str(dsn)
        # If DATABASE_URL wasn't set and components are missing, return None
        return None

    # Encryption Settings
    ENCRYPTION_KEY: Optional[SecretStr] = Field(default=None, json_schema_extra={"env": "ENCRYPTION_KEY"}) # Use SecretStr
    PREVIOUS_ENCRYPTION_KEY: Optional[SecretStr] = Field(default=None, json_schema_extra={"env": "PREVIOUS_ENCRYPTION_KEY"}) # Use SecretStr
    ENCRYPTION_SALT: str = Field(default="novamind-salt", json_schema_extra={"env": "ENCRYPTION_SALT"})
    
    # Other settings
    ENVIRONMENT: str = Field(default="development", json_schema_extra={"env": "ENVIRONMENT"})
    DEBUG: bool = Field(default=False, json_schema_extra={"env": "DEBUG"}) # General debug flag moved here
    TESTING: bool = Field(default=False, json_schema_extra={"env": "TESTING"}) # Add TESTING flag
    
    # Audit Log Settings
    AUDIT_LOG_LEVEL: str = Field(default="INFO", json_schema_extra={"env": "AUDIT_LOG_LEVEL"})
    AUDIT_LOG_TO_FILE: bool = Field(default=False, json_schema_extra={"env": "AUDIT_LOG_TO_FILE"})
    AUDIT_LOG_FILE: str = Field(default="audit.log", json_schema_extra={"env": "AUDIT_LOG_FILE"})
    EXTERNAL_AUDIT_ENABLED: bool = Field(default=False, json_schema_extra={"env": "EXTERNAL_AUDIT_ENABLED"})
    
    # --- Nested ML Settings ---
    ml: MLSettings = Field(default_factory=MLSettings)

    @model_validator(mode='before')
    @classmethod
    def assemble_database_url(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Assemble DATABASE_URL from components if DATABASE_URL is not explicitly set."""
        # Check if DATABASE_URL is missing and if postgres components are provided
        if values.get('DATABASE_URL') is None and values.get('POSTGRES_DB'):
            try:
                password = values.get("POSTGRES_PASSWORD")
                password_str = password.get_secret_value() if isinstance(password, SecretStr) else None

                # Construct the postgresql+asyncpg URL
                dsn = PostgresDsn.build(
                    scheme="postgresql+asyncpg", # Use asyncpg driver
                    username=values.get("POSTGRES_USER"),
                    password=password_str,
                    host=values.get("POSTGRES_SERVER"),
                    port=str(values.get("POSTGRES_PORT", 5432)),
                    path=f"{values.get('POSTGRES_DB') or ''}",
                )
                url_parts = [str(dsn)]
                # Optional: Add SSL parameters if provided
                ssl_mode = values.get('DATABASE_SSL_MODE')
                if ssl_mode and ssl_mode != 'disable':
                     url_parts.append(f"sslmode={ssl_mode}")
                     # Add handling for other SSL params like sslrootcert if needed

                values['DATABASE_URL'] = "?".join(url_parts) if len(url_parts) > 1 else url_parts[0]
                print(f"Constructed DATABASE_URL from components: {values['DATABASE_URL']}") # Debugging
            except Exception as e:
                print(f"Error assembling DATABASE_URL from components: {e}") # Debugging
                pass # Allow None if assembly fails

        # Remove the old URI field if it exists, ensuring clean output
        values.pop('SQLALCHEMY_DATABASE_URI', None)
        return values

    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env.test",
        env_file_encoding="utf-8",
        env_nested_delimiter='__'
    )


@lru_cache()
def get_settings() -> Settings:
    """Return the singleton Settings instance, loading based on pydantic-settings defaults.

    Relies on the Pydantic Settings logic to find and load the correct .env file
    (e.g., .env by default, or potentially .env.test if managed externally like in conftest.py).
    """
    print("Attempting to load settings (expecting .env or .env.test if overridden)...")
    try:
        # Settings class automatically loads from .env based on its model_config
        settings = Settings()
        # Crucial: Check if DATABASE_URL is None *after* loading and assembly attempt
        if settings.DATABASE_URL is None:
             print("CRITICAL WARNING: DATABASE_URL is None after settings load. Check .env files and assembly logic.")
             # Decide whether to raise an error here or let the DB connection fail later
             # raise ValueError("DATABASE_URL is not configured.")
        else:
             print(f"Settings loaded. DATABASE_URL resolved to: {settings.DATABASE_URL}")
        return settings
    except Exception as e:
        print(f"CRITICAL ERROR loading settings: {e}")
        raise RuntimeError(f"Failed to load application settings: {e}")

# Optional: Add a main block to print settings for verification during development
# if __name__ == "__main__":
#     settings = get_settings()
#     print("Loaded Settings:")
#     # Use model_dump for Pydantic V2, exclude sensitive fields if needed
#     print(settings.model_dump_json(indent=2))
