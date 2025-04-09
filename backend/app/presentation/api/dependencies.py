# -*- coding: utf-8 -*-
"""
API Dependencies Module.

This module provides FastAPI dependency functions for injecting
services and repositories into API routes.
"""

from typing import AsyncGenerator

from fastapi import Depends

from app.core.config.ml_settings import get_ml_settings
from app.infrastructure.ml.phi_detection import PHIDetectionService
from app.infrastructure.ml.mentallama import MentaLLaMAService


# Get ML settings once for all dependencies
ml_settings = get_ml_settings()


# Dependency for PHI Detection Service
async def get_phi_detection_service() -> AsyncGenerator[PHIDetectionService, None]:
    """
    Provide a PHI detection service instance.
    
    This dependency creates and initializes a PHI detection service
    for use in routes that need to detect and anonymize PHI.
    
    Yields:
        PHI detection service instance
    """
    service = PHIDetectionService(
        pattern_file=ml_settings.phi_detection.pattern_file
    )
    
    # Ensure service is initialized
    service.ensure_initialized()
    
    yield service


# Dependency for MentaLLaMA Service
async def get_mentallama_service(
    phi_detection_service: PHIDetectionService = Depends(get_phi_detection_service)
) -> AsyncGenerator[MentaLLaMAService, None]:
    """
    Provide a MentaLLaMA service instance.
    
    This dependency creates and initializes a MentaLLaMA service
    for clinical text analysis, using PHI detection for HIPAA compliance.
    
    Args:
        phi_detection_service: PHI detection service for anonymizing PHI
        
    Yields:
        MentaLLaMA service instance
    """
    service = MentaLLaMAService(
        phi_detection_service=phi_detection_service,
        api_key=ml_settings.mentallama.api_key,
        api_endpoint=ml_settings.mentallama.api_endpoint,
        model_name=ml_settings.mentallama.default_model,
        temperature=ml_settings.mentallama.temperature
    )
    
    try:
        yield service
    finally:
        # Clean up resources
        await service.close()