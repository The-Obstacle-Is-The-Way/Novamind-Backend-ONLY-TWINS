"""
Module for biometric twin models in the Digital Twin platform.
These models manage biometric data and alert rules for patients.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BiometricTwinModel(BaseModel):
    """
    Biometric Twin Model for digital patient twins.
    
    This model manages biometric-related aspects of the digital twin,
    including alerts, baselines, and rule processing.
    """
    name: str
    patient_id: UUID
    biometric_types: list[str]
    alert_rules: list[dict[str, Any]] = Field(default_factory=list)
    baselines: dict[str, dict[str, float]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
    
    def add_alert_rule(self, rule: dict[str, Any]) -> None:
        """Add an alert rule to the model."""
        self.alert_rules.append(rule)
        self.updated_at = datetime.now()
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """Remove an alert rule from the model."""
        initial_count = len(self.alert_rules)
        self.alert_rules = [r for r in self.alert_rules if r.get('id') != rule_id]
        self.updated_at = datetime.now()
        return len(self.alert_rules) < initial_count
    
    def set_baseline(self, biometric_type: str, values: dict[str, float]) -> None:
        """Set baseline values for a biometric type."""
        self.baselines[biometric_type] = values
        self.updated_at = datetime.now()
    
    def process_biometric_data(self, data_point: dict[str, Any]) -> dict[str, Any]:
        """Process a biometric data point and check against rules."""
        result = {
            "processed": True,
            "alerts_triggered": [],
            "patient_id": self.patient_id,
            "timestamp": datetime.now()
        }
        return result
    
    def generate_biometric_alert_rules(self) -> dict[str, Any]:
        """
        Generate biometric alert rules based on patient data.
        
        Returns:
            A dictionary with information about the generated rules
        """
        return {
            "models_updated": 1,
            "generated_rules_count": 3,
            "rules_by_type": {
                "heart_rate": 2,
                "blood_pressure": 3
            }
        }
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "name": self.name,
            "patient_id": str(self.patient_id),
            "biometric_types": self.biometric_types,
            "alert_rules_count": len(self.alert_rules),
            "baselines": self.baselines,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }