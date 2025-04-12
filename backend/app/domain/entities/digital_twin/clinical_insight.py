"""
Clinical Insight entity models for the Digital Twin system.

This module contains the ClinicalInsight class, which represents insights derived
from patient data analysis, and the ClinicalSignificance enum for categorizing
the importance of insights.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class ClinicalSignificance(str, Enum):
    """Enum representing the clinical significance level of an insight."""
    
    NONE = "none"  # No clinical significance
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    INFORMATIONAL = "informational"
    
    @classmethod
    def get_severity_score(cls, significance: "ClinicalSignificance") -> int:
        """Get numerical severity score for a significance level."""
        scores = {
            cls.CRITICAL: 5,
            cls.HIGH: 4,
            cls.MODERATE: 3,
            cls.LOW: 2,
            cls.INFORMATIONAL: 1,
            cls.NONE: 0
        }
        return scores.get(significance, 0)


class ClinicalInsight(BaseModel):
    """Model representing a clinical insight derived from patient data analysis."""
    
    id: UUID = Field(default_factory=uuid4)
    patient_id: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    title: str
    description: str
    significance: ClinicalSignificance = Field(default=ClinicalSignificance.NONE)
    clinical_significance: ClinicalSignificance = Field(default=ClinicalSignificance.NONE)
    source: str = Field(..., description="Source of the insight (e.g., 'biometric_analysis', 'ml_model')")
    category: str = Field(default="general", description="Category of the insight (e.g., 'medication', 'symptom', 'behavior')")
    confidence: float = Field(
        default=0.5, 
        ge=0.0, 
        le=1.0, 
        description="Confidence level in this insight (0.0-1.0)"
    )
    requires_action: bool = Field(default=False)
    action_description: str | None = None
    related_data: dict[str, Any] = Field(default_factory=dict)
    supporting_evidence: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    brain_regions: list[Any] = Field(default_factory=list, description="Brain regions associated with this insight")
    neurotransmitters: list[Any] = Field(default_factory=list, description="Neurotransmitters associated with this insight")
    acknowledged: bool = Field(default=False)
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        
    @validator('related_data')
    def validate_related_data(cls, v):
        """Validate that related_data can be serialized to JSON."""
        try:
            import json
            json.dumps(v)
            return v
        except (TypeError, ValueError):
            raise ValueError("related_data must be JSON serializable")
    
    def acknowledge(self, user_id: str) -> None:
        """Acknowledge this insight by a user."""
        self.acknowledged = True
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.utcnow()
    
    def get_severity_score(self) -> int:
        """Get numerical severity score based on significance and confidence."""
        base_score = ClinicalSignificance.get_severity_score(self.significance)
        # Adjust score based on confidence
        return int(base_score * self.confidence)
    
    def is_urgent(self) -> bool:
        """Determine if this insight requires urgent attention."""
        return (self.significance in (ClinicalSignificance.CRITICAL, ClinicalSignificance.HIGH) 
                and self.requires_action 
                and not self.acknowledged)