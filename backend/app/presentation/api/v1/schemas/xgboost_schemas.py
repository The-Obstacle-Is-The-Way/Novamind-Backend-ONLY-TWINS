# -*- coding: utf-8 -*-
"""
Minimal placeholder XGBoost schemas for integration tests.
Replace with real schemas as needed for production.
"""
from pydantic import BaseModel, Field
from typing import Any

class RiskPredictionRequest(BaseModel):
    patient_id: str = Field(...)
    features: Any = Field(...)

class TreatmentResponseRequest(BaseModel):
    patient_id: str = Field(...)
    treatment_type: str = Field(...)
    treatment_details: Any = Field(...)
    clinical_data: Any = Field(...)
