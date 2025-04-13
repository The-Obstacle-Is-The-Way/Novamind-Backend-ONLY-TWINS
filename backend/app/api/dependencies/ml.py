"""
ML service dependencies for FastAPI routes.

This module provides FastAPI dependency functions for ML services,
including the PAT service for actigraphy analysis, digital twin services,
and other ML-based services.
"""

from functools import lru_cache
from typing import Dict, Any

from fastapi import Depends

from app.core.config import get_settings
settings = get_settings()
from app.core.services.ml.pat.factory import PATServiceFactory
from app.core.services.ml.pat.interface import PATInterface
from app.infrastructure.ml.digital_twin_integration_service import DigitalTwinIntegrationService
from app.domain.services.mentalllama_service import MentalLLaMAService


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


def get_pat_factory() -> PATServiceFactory:
    """Get a PAT service factory instance.
    
    Returns:
        PAT service factory instance
    """
    return PATServiceFactory()


def get_pat_service(
    config: Dict[str, Any] = Depends(get_pat_config)
) -> PATInterface:
    """Get a configured instance of the PAT service.
    
    This dependency function returns a PAT service instance that can be used
    by API route handlers to analyze actigraphy data. The implementation is
    determined by the configuration (mock or AWS).
    
    Args:
        config: Configuration for the PAT service
        
    Returns:
        Configured PAT service instance
    """
    factory = get_pat_factory()
    return factory.create_service()


def get_digital_twin_service() -> DigitalTwinIntegrationService:
    """Get a digital twin integration service instance.
    
    This dependency function returns a digital twin service that can be used
    by API route handlers to interact with the digital twin model.
    
    Returns:
        Digital Twin Integration Service instance
    """
    return DigitalTwinIntegrationService()


def get_mentallama_service() -> MentalLLaMAService:
    """Get a MentalLLaMA service instance.
    
    This dependency function returns a MentalLLaMA service that can be used
    by API route handlers for advanced NLP and clinical text analysis.
    
    Returns:
        MentalLLaMA Service instance
    """
    return MentalLLaMAService()