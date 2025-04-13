# -*- coding: utf-8 -*-
"""
Machine Learning Configuration Settings.

This module provides configuration settings for machine learning models,
services, and integrations in the application.
"""

import os
from typing import Dict, List, Optional, Union
from functools import lru_cache

from pydantic import BaseModel, Field, field_validator


class XGBoostSettings(BaseModel):
    """XGBoost model configuration settings."""
    
    model_config = {"protected_namespaces": ()}
    
    model_path: str = Field(
        default="models/xgboost",
        description="Path to XGBoost model files"
    )
    
    prediction_threshold: float = Field(
        default=0.75,
        description="Threshold for positive prediction"
    )
    
    feature_importance_count: int = Field(
        default=10,
        description="Number of top features to show in importance visualization"
    )


class MentalLLaMASettings(BaseModel):
    """MentalLLaMA integration settings."""
    
    api_key: Optional[str] = Field(
        default=None,
        description="API key for MentalLLaMA service"
    )
    
    api_endpoint: str = Field(
        default="https://api.mentallama.com/v1",
        description="API endpoint for MentalLLaMA service"
    )
    
    timeout_seconds: int = Field(
        default=30,
        description="Timeout for API requests in seconds"
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed API requests"
    )
    
    default_model: str = Field(
        default="mentallama-7b",
        description="Default LLM model to use"
    )
    
    temperature: float = Field(
        default=0.7,
        description="Temperature for model inference"
    )
    
    @field_validator("api_key")
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate API key by checking environment variables if not set."""
        if v is None:
            return os.environ.get("MENTALLAMA_API_KEY")
        return v


class PHIDetectionSettings(BaseModel):
    """PHI detection configuration settings."""
    
    pattern_file: str = Field(
        default="phi_patterns.yaml",
        description="Path to PHI detection patterns file"
    )
    
    enable_ml_detection: bool = Field(
        default=True,
        description="Whether to use ML-based detection in addition to regex patterns"
    )
    
    detection_threshold: float = Field(
        default=0.8,
        description="Confidence threshold for ML-based PHI detection"
    )
    
    sensitivity_level: str = Field(
        default="high",
        description="Sensitivity level for PHI detection (low, medium, high)"
    )
    
    @field_validator("sensitivity_level")
    def validate_sensitivity_level(cls, v: str) -> str:
        """Validate sensitivity level is one of the allowed values."""
        allowed_levels = ["low", "medium", "high"]
        if v.lower() not in allowed_levels:
            raise ValueError(f"Sensitivity level must be one of: {', '.join(allowed_levels)}")
        return v.lower()


class DigitalTwinSettings(BaseModel):
    """Digital Twin integration settings."""
    
    enable_interactive_brain: bool = Field(
        default=True,
        description="Whether to enable interactive 3D brain visualization"
    )
    
    brain_regions_file: str = Field(
        default="models/brain_regions.json",
        description="Path to brain regions definition file"
    )
    
    default_rendering_quality: str = Field(
        default="medium",
        description="Default rendering quality (low, medium, high)"
    )
    
    max_concurrent_users: int = Field(
        default=50,
        description="Maximum number of concurrent users for real-time visualization"
    )


class MLSettings(BaseModel):
    """Machine learning configuration settings."""
    
    xgboost: XGBoostSettings = Field(default_factory=XGBoostSettings)
    mentallama: MentalLLaMASettings = Field(default_factory=MentalLLaMASettings)
    phi_detection: PHIDetectionSettings = Field(default_factory=PHIDetectionSettings)
    digital_twin: DigitalTwinSettings = Field(default_factory=DigitalTwinSettings)
    
    enable_ml_features: bool = Field(
        default=True,
        description="Master switch to enable/disable all ML features"
    )
    
    log_ml_performance: bool = Field(
        default=True,
        description="Whether to log ML model performance metrics"
    )
    
    enable_batch_processing: bool = Field(
        default=True,
        description="Whether to enable batch processing for ML tasks"
    )
    
    batch_size: int = Field(
        default=32,
        description="Batch size for ML processing"
    )


@lru_cache()
def get_ml_settings() -> MLSettings:
    """
    Get machine learning settings.
    
    This function returns the ML settings singleton, cached for efficiency.
    
    Returns:
        ML settings object
    """
    return MLSettings()


# Create singleton instance
ml_settings = get_ml_settings()