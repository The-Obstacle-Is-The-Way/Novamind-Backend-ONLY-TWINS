# -*- coding: utf-8 -*-
"""
ML Services Package.

This package provides mental health machine learning services including:
- MentaLLaMA: Mental health language model analysis service
- PHI Detection: Protected Health Information detection service
- Digital Twin: Patient digital twin simulation service
- PAT: Patient Assessment Tool for clinical evaluation
"""

from app.core.services.ml.factory import MLServiceFactory, MLServiceCache
from app.core.services.ml.interface import (
    DigitalTwinInterface,
    MentaLLaMAInterface,
    BaseMLInterface as MLService,
    PHIDetectionInterface as PHIDetectionService,
)
from app.core.services.ml.mentalllama import BaseMentaLLaMA
from app.core.services.ml.mock import MockMentaLLaMA
from app.core.services.ml.pat import PATInterface, PATService, MockPATService


__all__ = [
    # Interfaces
    "MLService",
    "MentaLLaMAInterface",
    "PHIDetectionService",
    "DigitalTwinInterface",
    "PATInterface",
    
    # Base implementations
    "BaseMentaLLaMA",
    "PATService",
    
    # Mock implementations
    "MockMentaLLaMA",
    "MockPATService",
    
    # Factory and cache
    "MLServiceFactory",
    "MLServiceCache",
]