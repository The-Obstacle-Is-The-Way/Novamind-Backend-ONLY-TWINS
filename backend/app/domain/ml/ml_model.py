"""
Domain entities related to Machine Learning Models.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID


class ModelType(Enum):
    """Enumeration of supported machine learning model types."""
    XGBOOST = "xgboost"
    LLM = "llm"
    TRANSFORMER = "transformer"
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    RECOMMENDER = "recommender"
    NEURAL_NETWORK = "neural_network"
    PAT = "pat"  # Pretrained Actigraphy Transformer
    OTHER = "other"


@dataclass
class MLModel:
    """Represents metadata and configuration for a machine learning model."""
    # Non-default fields first
    name: str
    version: str
    model_type: ModelType
    
    # Fields with defaults
    model_id: UUID = field(default_factory=uuid.uuid4)
    description: Optional[str] = None
    artifact_path: Optional[str] = None  # Path to model file(s)
    parameters: Dict[str, Any] = field(default_factory=dict)  # Hyperparameters, config
    metrics: Dict[str, float] = field(default_factory=dict)  # Performance metrics
    created_at: datetime = field(default_factory=lambda: datetime.now(datetime.UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(datetime.UTC))
    metadata: Dict[str, Any] = field(default_factory=dict) # Other metadata

    def __post_init__(self):
        if not self.name:
            raise ValueError("Model name cannot be empty.")
        if not self.version:
            raise ValueError("Model version cannot be empty.")
