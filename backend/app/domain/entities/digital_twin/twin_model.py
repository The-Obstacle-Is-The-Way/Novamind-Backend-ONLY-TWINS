# -*- coding: utf-8 -*-
# app/domain/entities/digital_twin/twin_model.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ModelParameters:
    """Value object for model parameters"""

    parameters: Dict[str, Any]


@dataclass(frozen=True)
class DigitalTwinModel(ABC):
    """Base abstract class for all digital twin models"""

    id: UUID
    name: str
    version: str
    created_at: datetime
    last_trained: Optional[datetime]
    accuracy: float
    parameters: ModelParameters

    @abstractmethod
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make prediction using the model

        Args:
            input_data: Input data for the prediction

        Returns:
            Prediction results
        """
        pass

    @classmethod
    def create_model_id(cls) -> UUID:
        """Generate a new model ID"""
        return uuid4()
