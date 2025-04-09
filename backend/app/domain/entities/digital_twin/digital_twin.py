# -*- coding: utf-8 -*-
# app/domain/entities/digital_twin/digital_twin.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from app.domain.entities.digital_twin_enums import ClinicalInsight
from app.domain.entities.digital_twin.twin_model import DigitalTwinModel


@dataclass(frozen=True)
class DigitalTwin:
    """
    Core entity representing a patient's digital twin model.
    Immutable by design to ensure state transitions are tracked.
    """

    id: UUID
    patient_id: UUID
    created_at: datetime
    updated_at: datetime
    version: int
    confidence_score: float
    models: List[DigitalTwinModel]
    clinical_insights: List[ClinicalInsight]
    last_calibration: datetime

    @classmethod
    def create(
        cls,
        patient_id: UUID,
        models: List[DigitalTwinModel],
        confidence_score: float = 0.0,
    ) -> "DigitalTwin":
        """Factory method to create a new DigitalTwin"""
        now = datetime.now()
        return cls(
            id=uuid4(),
            patient_id=patient_id,
            created_at=now,
            updated_at=now,
            version=1,
            confidence_score=confidence_score,
            models=models,
            clinical_insights=[],
            last_calibration=now,
        )

    def add_clinical_insight(self, insight: ClinicalInsight) -> "DigitalTwin":
        """
        Adds a clinical insight to the digital twin, returning a new instance.

        Args:
            insight: The clinical insight to add

        Returns:
            A new DigitalTwin instance with the updated insights
        """
        return DigitalTwin(
            id=self.id,
            patient_id=self.patient_id,
            created_at=self.created_at,
            updated_at=datetime.now(),
            version=self.version + 1,
            confidence_score=self.confidence_score,
            models=self.models.copy(),
            clinical_insights=[*self.clinical_insights, insight],
            last_calibration=self.last_calibration,
        )

    def recalibrate(
        self, models: List[DigitalTwinModel], confidence_score: float
    ) -> "DigitalTwin":
        """
        Recalibrates the digital twin with updated models.

        Args:
            models: Updated model list
            confidence_score: New overall confidence score

        Returns:
            A new DigitalTwin instance with updated models
        """
        return DigitalTwin(
            id=self.id,
            patient_id=self.patient_id,
            created_at=self.created_at,
            updated_at=datetime.now(),
            version=self.version + 1,
            confidence_score=confidence_score,
            models=models,
            clinical_insights=self.clinical_insights.copy(),
            last_calibration=datetime.now(),
        )
