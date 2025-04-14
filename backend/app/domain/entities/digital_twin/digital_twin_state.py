"""
Digital Twin State entity for the Digital Twin system.

This module contains the DigitalTwinState class, which represents the current
physiological and psychological state of a patient's digital twin.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.domain.utils.datetime_utils import UTC
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .brain_region import BrainRegion
from .neurotransmitter import Neurotransmitter


class DigitalTwinState(BaseModel):
    """Model representing the current state of a patient's digital twin."""
    
    id: UUID = Field(default_factory=uuid4)
    patient_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # Neurotransmitter levels
    neurotransmitter_levels: dict[str, float] = Field(
        default_factory=dict,
        description="Normalized neurotransmitter levels (-1.0 to 1.0)"
    )
    
    # Brain region activity
    brain_region_activity: dict[str, float] = Field(
        default_factory=dict,
        description="Normalized brain region activity levels (-1.0 to 1.0)"
    )
    
    # Physiological metrics
    physiological_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Various physiological metrics (normalized values)"
    )
    
    # Psychological metrics
    psychological_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Various psychological metrics (normalized values)"
    )
    
    # Risk factors
    risk_factors: dict[str, float] = Field(
        default_factory=dict,
        description="Risk factors and their severity (0.0-1.0)"
    )
    
    # Treatment response predictions
    treatment_responses: dict[str, float] = Field(
        default_factory=dict,
        description="Predicted responses to treatments (0.0-1.0)"
    )
    
    # Current symptoms
    symptoms: dict[str, float] = Field(
        default_factory=dict,
        description="Current symptoms and their severity (0.0-1.0)"
    )
    
    # Meta information
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Overall confidence in this state assessment (0.0-1.0)"
    )
    
    source: str = Field(
        default="model",
        description="Source of this state data (e.g., 'model', 'interpolated', 'extrapolated')"
    )
    
    meta: dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        validate_assignment=True
    )
    
    @field_validator('neurotransmitter_levels')
    def validate_neurotransmitter_levels(cls, v, info):
        """Validate neurotransmitter levels are within range."""
        for nt, level in v.items():
            if level < -1.0 or level > 1.0:
                raise ValueError(f"Neurotransmitter level for {nt} must be between -1.0 and 1.0")
        return v
    
    @field_validator('brain_region_activity')
    def validate_brain_activity(cls, v, info):
        """Validate brain activity levels are within range."""
        for region, level in v.items():
            if level < -1.0 or level > 1.0:
                raise ValueError(f"Brain activity level for {region} must be between -1.0 and 1.0")
        return v
    
    def get_neurotransmitter_level(self, neurotransmitter: Neurotransmitter) -> float:
        """Get the level of a specific neurotransmitter."""
        return self.neurotransmitter_levels.get(neurotransmitter, 0.0)
    
    def get_brain_region_activity(self, region: BrainRegion) -> float:
        """Get the activity level of a specific brain region."""
        return self.brain_region_activity.get(region, 0.0)
    
    def get_risk_level(self, risk_type: str) -> float:
        """Get the level of a specific risk factor."""
        return self.risk_factors.get(risk_type, 0.0)
    
    def get_symptom_severity(self, symptom: str) -> float:
        """Get the severity of a specific symptom."""
        return self.symptoms.get(symptom, 0.0)
    
    def get_treatment_response(self, treatment: str) -> float:
        """Get the predicted response to a specific treatment."""
        return self.treatment_responses.get(treatment, 0.0)
    
    def get_high_risk_factors(self, threshold: float = 0.7) -> dict[str, float]:
        """Get risk factors above a certain threshold."""
        return {k: v for k, v in self.risk_factors.items() if v >= threshold}
    
    def get_severe_symptoms(self, threshold: float = 0.7) -> dict[str, float]:
        """Get symptoms above a certain severity threshold."""
        return {k: v for k, v in self.symptoms.items() if v >= threshold}