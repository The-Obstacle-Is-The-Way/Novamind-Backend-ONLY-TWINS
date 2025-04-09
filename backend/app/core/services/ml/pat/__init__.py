"""
Patient Activity Tracking (PAT) service module.

This package provides components for tracking, analyzing, and interpreting
patient activity data from wearable devices to generate clinical insights.
"""

from app.core.services.ml.pat.base import PATBase
from app.core.services.ml.pat.exceptions import (
    AnalysisError,
    AuthorizationError,
    ConfigurationError,
    EmbeddingError,
    InitializationError,
    IntegrationError,
    PATError,
    ResourceNotFoundError,
    StorageError,
    ValidationError,
)
from app.core.services.ml.pat.factory import PATFactory
from app.core.services.ml.pat.mock import MockPAT

__all__ = [
    "PATBase",
    "PATFactory",
    "MockPAT",
    "PATError",
    "InitializationError",
    "ValidationError",
    "AnalysisError",
    "EmbeddingError",
    "ResourceNotFoundError",
    "AuthorizationError",
    "IntegrationError",
    "ConfigurationError",
    "StorageError",
]