"""
Domain entity representing a Symptom Assessment.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from enum import Enum

from app.domain.entities.base_entity import BaseEntity

class AssessmentType(str, Enum):
    PHQ9 = "PHQ-9"
    GAD7 = "GAD-7"
    CUSTOM = "Custom"
    # Add other standard scales (e.g., BDI, MADRS, YBOCS)

@dataclass
class SymptomAssessment(BaseEntity):
    """Symptom Assessment entity."""
    id: UUID = field(default_factory=uuid4)
    patient_id: UUID
    assessment_type: AssessmentType
    assessment_date: datetime # Date/time the assessment was completed
    scores: Dict[str, Any] # e.g., {"total_score": 15, "q1": 2, "q2": 3, ...} or {"custom_symptom": "severity_level"}
    source: Optional[str] = None # e.g., "Patient Reported", "Clinician Administered"
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow) # Usually same as created_at for assessments

    def __post_init__(self):
        # Call BaseEntity's post_init if it exists
        if hasattr(super(), '__post_init__'):
            super().__post_init__()
        # Add validation if needed (e.g., score range for known types)

    def touch(self):
        """Update the last_updated timestamp."""
        self.last_updated = datetime.utcnow() # Should ideally not change post-creation

