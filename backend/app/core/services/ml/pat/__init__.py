# -*- coding: utf-8 -*-
"""
Patient Assessment Tool (PAT) Package.

This package provides a service for patient assessments and clinical evaluations.
"""

from app.core.services.ml.pat.pat_interface import PATInterface
from app.core.services.ml.pat.pat_service import PATService
from app.core.services.ml.pat.mock import MockPATService
from app.core.services.ml.pat.factory import PATServiceFactory
from app.core.services.ml.pat.exceptions import (
    PATServiceError,
    InitializationError,
    ValidationError,
    AuthorizationError,
    EmbeddingError,
    AnalysisError,
    DataPrivacyError,
    ResourceNotFoundError,
    AnalysisNotFoundError,
    ServiceConnectionError,
    ConfigurationError,
    IntegrationError
)

__all__ = [
    # Interfaces
    "PATInterface",
    
    # Implementations
    "PATService",
    
    # Mock implementations for testing
    "MockPATService",
    
    # Factory
    "PATServiceFactory",
    
    # Exceptions
    "PATServiceError",
    "InitializationError",
    "ValidationError",
    "AnalysisError",
    "DataPrivacyError",
    "ResourceNotFoundError",
    "AnalysisNotFoundError",
    "ServiceConnectionError",
    "ConfigurationError",
    "IntegrationError",
    "AuthorizationError",
    "EmbeddingError"
]