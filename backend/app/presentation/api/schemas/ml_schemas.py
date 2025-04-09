# -*- coding: utf-8 -*-
"""
ML API Schemas.

This module provides pydantic schemas for machine learning endpoints,
including clinical text analysis and digital twin functionality.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, UUID4, Field, validator


class AnalysisType(str, Enum):
    """Types of clinical analysis available."""
    
    DIAGNOSTIC_IMPRESSION = "diagnostic_impression"
    RISK_ASSESSMENT = "risk_assessment"
    TREATMENT_RECOMMENDATION = "treatment_recommendation"
    OUTCOME_PREDICTION = "outcome_prediction"
    CLINICAL_SUMMARY = "clinical_summary"
    MEDICATION_ANALYSIS = "medication_analysis"
    SYMPTOM_EXTRACTION = "symptom_extraction"


class ClinicalAnalysisRequest(BaseModel):
    """Request model for clinical text analysis."""
    
    text: str = Field(
        ...,
        description="Clinical text to analyze",
        min_length=10
    )
    
    analysis_type: AnalysisType = Field(
        ..., 
        description="Type of analysis to perform"
    )
    
    patient_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional context about the patient (e.g., age, gender, history)"
    )
    
    @validator("text")
    def text_not_empty(cls, v: str) -> str:
        """Validate text is not empty or just whitespace."""
        if v.strip() == "":
            raise ValueError("Text cannot be empty or just whitespace")
        return v


class ClinicalAnalysisResponse(BaseModel):
    """Response model for clinical text analysis."""
    
    analysis_type: str = Field(
        ...,
        description="Type of analysis performed"
    )
    
    result: Dict[str, Any] = Field(
        ...,
        description="Analysis results"
    )
    
    confidence_score: float = Field(
        ...,
        description="Confidence score (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    analysis_id: str = Field(
        ...,
        description="Unique identifier for this analysis"
    )
    
    processed_at: datetime = Field(
        ...,
        description="Timestamp when analysis was processed"
    )


class PHIEntity(BaseModel):
    """Detected PHI entity information."""
    
    entity_type: str = Field(
        ...,
        description="Type of PHI entity (e.g., NAME, ADDRESS, SSN)"
    )
    
    text: Optional[str] = Field(
        None,
        description="Original text (only included if not anonymized)"
    )
    
    position: Dict[str, int] = Field(
        ...,
        description="Position of entity in text (start and end indices)"
    )
    
    confidence: float = Field(
        ...,
        description="Confidence score (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    replacement: Optional[str] = Field(
        None,
        description="Replacement text (if anonymized)"
    )


class PHIDetectionResponse(BaseModel):
    """Response model for PHI detection."""
    
    anonymized_text: Optional[str] = Field(
        None,
        description="Anonymized text with PHI replaced (if anonymization requested)"
    )
    
    entities: List[PHIEntity] = Field(
        default_factory=list,
        description="List of detected PHI entities"
    )
    
    detection_id: str = Field(
        ...,
        description="Unique identifier for this detection operation"
    )
    
    processed_at: datetime = Field(
        ...,
        description="Timestamp when detection was processed"
    )
    
    phi_count: int = Field(
        ...,
        description="Total number of PHI entities detected"
    )


class DigitalTwinCreateRequest(BaseModel):
    """Request model for creating a digital twin."""
    
    patient_id: str = Field(
        ...,
        description="Patient ID to create the digital twin for"
    )
    
    clinical_data: Dict[str, Any] = Field(
        ...,
        description="Clinical data for twin creation (e.g., diagnoses, medications, assessments)"
    )
    
    demographic_data: Dict[str, Any] = Field(
        ...,
        description="Demographic data for twin creation (e.g., age, gender)"
    )
    
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional parameters for twin creation"
    )


class DigitalTwinUpdateRequest(BaseModel):
    """Request model for updating a digital twin."""
    
    clinical_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated clinical data"
    )
    
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated parameters"
    )
    
    @validator("clinical_data", "parameters")
    def at_least_one_field(cls, v: Optional[Dict[str, Any]], values: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate at least one field is provided."""
        if not v and not any(values.values()):
            raise ValueError("At least one of clinical_data or parameters must be provided")
        return v


class DigitalTwinResponse(BaseModel):
    """Response model for digital twin operations."""
    
    twin_id: UUID4 = Field(
        ...,
        description="Unique ID of the digital twin"
    )
    
    patient_id: str = Field(
        ...,
        description="ID of the patient this twin represents"
    )
    
    created_at: datetime = Field(
        ...,
        description="Timestamp when the twin was created"
    )
    
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the twin was last updated"
    )
    
    state: Dict[str, Any] = Field(
        ...,
        description="Current state of the digital twin"
    )
    
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters of the digital twin"
    )
    
    version: int = Field(
        ...,
        description="Version number of the digital twin"
    )


class SimulationRequest(BaseModel):
    """Request model for running a simulation on a digital twin."""
    
    scenario: str = Field(
        ...,
        description="Simulation scenario (e.g., 'medication_change', 'therapy_response')"
    )
    
    parameters: Dict[str, Any] = Field(
        ...,
        description="Simulation parameters"
    )
    
    duration: Optional[int] = Field(
        None,
        description="Simulation duration in days",
        gt=0
    )


class SimulationTimepoint(BaseModel):
    """Data for a single timepoint in a simulation."""
    
    day: int = Field(
        ...,
        description="Day of simulation"
    )
    
    state: Dict[str, Any] = Field(
        ...,
        description="State of the digital twin at this timepoint"
    )
    
    metrics: Dict[str, float] = Field(
        ...,
        description="Metrics at this timepoint"
    )


class SimulationResponse(BaseModel):
    """Response model for simulation results."""
    
    simulation_id: UUID4 = Field(
        ...,
        description="Unique ID of the simulation"
    )
    
    twin_id: UUID4 = Field(
        ...,
        description="ID of the digital twin that was simulated"
    )
    
    scenario: str = Field(
        ...,
        description="Simulation scenario that was run"
    )
    
    start_time: datetime = Field(
        ...,
        description="When the simulation started"
    )
    
    duration: int = Field(
        ...,
        description="Duration of the simulation in days"
    )
    
    timepoints: List[SimulationTimepoint] = Field(
        ...,
        description="Data for each timepoint in the simulation"
    )
    
    summary: Dict[str, Any] = Field(
        ...,
        description="Summary of simulation results"
    )
    
    confidence_score: float = Field(
        ...,
        description="Overall confidence score for the simulation",
        ge=0.0,
        le=1.0
    )