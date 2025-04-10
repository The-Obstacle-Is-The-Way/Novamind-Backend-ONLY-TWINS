"""
ML service dependencies for FastAPI routes.

This module provides FastAPI dependency functions for ML services,
including the PAT service for actigraphy analysis.
"""

from functools import lru_cache
from typing import Dict, Any

from fastapi import Depends

from app.core.config import settings
from app.core.services.ml.pat.factory import PATServiceFactory # Corrected class name
from app.core.services.ml.pat.interface import PATInterface


@lru_cache()
def get_pat_config() -> Dict[str, Any]:
    """Get configuration for the PAT service.
    
    Returns:
        Configuration dictionary for PAT service
    """
    # Extract PAT configuration from settings
    return {
        "provider": settings.PAT_PROVIDER,
        "storage_path": settings.PAT_STORAGE_PATH,
        "aws_region": settings.AWS_REGION,
        "bucket_name": settings.PAT_BUCKET_NAME,
        "table_name": settings.PAT_TABLE_NAME,
        "kms_key_id": settings.PAT_KMS_KEY_ID,
        "model_id": settings.PAT_MODEL_ID
    }


def get_pat_service(
    config: Dict[str, Any] = Depends(get_pat_config)
) -> PATInterface:
    """Get a configured instance of the PAT service.
    
    This dependency function returns a PAT service instance that can be used
    by API route handlers to analyze actigraphy data. The implementation is
    determined by the configuration (mock or Bedrock).
    
    Args:
        config: Configuration for the PAT service
        
    Returns:
        Configured PAT service instance
    """
    factory = PATServiceFactory() # Instantiate the factory
    # Pass config to the create_service method, which uses settings internally
    return factory.create_service()