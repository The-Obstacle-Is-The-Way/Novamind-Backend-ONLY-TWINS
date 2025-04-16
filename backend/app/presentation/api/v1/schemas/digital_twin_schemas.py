# -*- coding: utf-8 -*-
"""
Digital Twin API schemas.

This module provides Pydantic schemas for the Digital Twin API endpoints,
handling input validation and response serialization.
"""

from datetime import datetime, UTC
from app.domain.utils.datetime_utils import UTC
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict, field_validator


class DigitalTwinFeatureSchema(BaseModel):
    """Schema for Digital Twin Feature."""
    
    name: str = Field(..., description="Feature name")
    value: Any = Field(..., description="Feature value (any serializable data)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when feature was recorded")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "heart_rate",
                "value": 72,
                "timestamp": "2025-03-28T04:00:00"
            }
        }
    )


class TreatmentOutcomeSchema(BaseModel):
    """Schema for Treatment Outcome."""
    
    id: Optional[str] = Field(None, description="Unique ID for outcome record")
    digital_twin_id: Optional[str] = Field(None, description="ID of associated digital twin")
    treatment: str = Field(..., description="Treatment administered")
    outcome: str = Field(..., description="Observed outcome")
    effectiveness: str = Field(..., description="Treatment effectiveness")
    notes: Optional[str] = Field(None, description="Additional notes")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when outcome was recorded")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "12345678-1234-5678-1234-567812345678",
                "digital_twin_id": "98765432-9876-5432-9876-987654321098",
                "treatment": "Cognitive Behavioral Therapy",
                "outcome": "Reduced anxiety symptoms",
                "effectiveness": "Moderate improvement",
                "notes": "Patient reported feeling less anxious in social situations",
                "timestamp": "2025-03-28T04:00:00"
            }
        }
    )


class TreatmentPredictionSchema(BaseModel):
    """Schema for Treatment Prediction."""
    
    id: Optional[str] = Field(None, description="Unique ID for prediction")
    digital_twin_id: Optional[str] = Field(None, description="ID of associated digital twin")
    treatment: str = Field(..., description="Treatment being predicted")
    condition: Optional[str] = Field(None, description="Condition being treated")
    likelihood: str = Field(..., description="Likelihood of positive response")
    timeline: str = Field(..., description="Expected timeline for response")
    obstacles: List[str] = Field(default_factory=list, description="Potential obstacles to treatment")
    influencing_factors: List[str] = Field(default_factory=list, description="Factors influencing treatment response")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for prediction")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when prediction was made")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "12345678-1234-5678-1234-567812345678",
                "digital_twin_id": "98765432-9876-5432-9876-987654321098",
                "treatment": "Selective Serotonin Reuptake Inhibitor",
                "condition": "Major Depressive Disorder",
                "likelihood": "High",
                "timeline": "4-6 weeks",
                "obstacles": ["Medication adherence", "Side effects"],
                "influencing_factors": ["Age", "Symptom severity", "Co-occurring conditions"],
                "confidence": 0.85,
                "timestamp": "2025-03-28T04:00:00"
            }
        }
    )


class DigitalTwinSchema(BaseModel):
    """Schema for Digital Twin."""
    
    id: Optional[str] = Field(None, description="Unique ID for digital twin")
    patient_id: Optional[str] = Field(None, description="ID of associated patient")
    name: Optional[str] = Field(None, description="Name of digital twin")
    description: Optional[str] = Field(None, description="Description of digital twin")
    features: List[DigitalTwinFeatureSchema] = Field(default_factory=list, description="Features of digital twin")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when digital twin was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when digital twin was last updated")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "98765432-9876-5432-9876-987654321098",
                "patient_id": "ab123456-ab12-cd34-ef56-ab1234567890",
                "name": "Primary Clinical Model",
                "description": "Comprehensive clinical model for treatment planning",
                "features": [
                    {
                        "name": "diagnosis_primary",
                        "value": "Major Depressive Disorder",
                        "timestamp": "2025-03-28T04:00:00"
                    }
                ],
                "created_at": "2025-03-28T04:00:00",
                "updated_at": "2025-03-28T04:00:00"
            }
        }
    )


# Request schemas

class CreateDigitalTwinRequest(BaseModel):
    """Request schema for creating a digital twin."""
    
    patient_id: str = Field(..., description="ID of associated patient")
    name: Optional[str] = Field(None, description="Name of digital twin")
    description: Optional[str] = Field(None, description="Description of digital twin")
    initial_features: List[DigitalTwinFeatureSchema] = Field(default_factory=list, description="Initial features of digital twin")


class UpdateDigitalTwinRequest(BaseModel):
    """Request schema for updating a digital twin."""
    
    name: Optional[str] = Field(None, description="Name of digital twin")
    description: Optional[str] = Field(None, description="Description of digital twin")


class AddFeatureRequest(BaseModel):
    """Request schema for adding a feature to a digital twin."""
    
    feature: DigitalTwinFeatureSchema = Field(..., description="Feature to add")


class ClinicalTextAnalysisRequest(BaseModel):
    """Request schema for analyzing clinical text."""
    
    text: str = Field(..., description="Clinical text to analyze")
    digital_twin_id: Optional[str] = Field(None, description="ID of associated digital twin")
    patient_id: Optional[str] = Field(None, description="ID of associated patient")
    analysis_type: str = Field("diagnostic_impression", description="Type of analysis to perform")
    detect_phi: bool = Field(True, description="Whether to detect and remove PHI")
    
    @field_validator('text')
    def text_not_empty(cls, v):
        """Validate that text is not empty."""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v
    
    @field_validator('analysis_type')
    def validate_analysis_type(cls, v):
        """Validate analysis type."""
        valid_types = [
            "diagnostic_impression", 
            "risk_assessment", 
            "treatment_recommendation", 
            "clinical_insight"
        ]
        if v not in valid_types:
            raise ValueError(f"Analysis type must be one of: {', '.join(valid_types)}")
        return v


class PersonalizedInsightRequest(BaseModel):
    """Request schema for getting personalized insight."""
    
    query: str = Field(..., description="Query for insight")
    insight_type: str = Field("clinical", description="Type of insight to generate")
    include_historical: bool = Field(True, description="Whether to include historical data")
    
    @field_validator('query')
    def query_not_empty(cls, v):
        """Validate that query is not empty."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v
    
    @field_validator('insight_type')
    def validate_insight_type(cls, v):
        """Validate insight type."""
        valid_types = ["clinical", "behavioral", "therapeutic", "medication"]
        if v not in valid_types:
            raise ValueError(f"Insight type must be one of: {', '.join(valid_types)}")
        return v


class ClinicalRecommendationRequest(BaseModel):
    """Request schema for getting clinical recommendation."""
    
    query: str = Field(..., description="Query for recommendation")
    recommendation_type: str = Field("treatment", description="Type of recommendation to generate")
    include_historical: bool = Field(True, description="Whether to include historical data")
    
    @field_validator('query')
    def query_not_empty(cls, v):
        """Validate that query is not empty."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v
    
    @field_validator('recommendation_type')
    def validate_recommendation_type(cls, v):
        """Validate recommendation type."""
        valid_types = ["treatment", "medication", "therapy", "lifestyle"]
        if v not in valid_types:
            raise ValueError(f"Recommendation type must be one of: {', '.join(valid_types)}")
        return v


class TreatmentPredictionRequest(BaseModel):
    """Request schema for predicting treatment outcome."""
    
    treatment: str = Field(..., description="Treatment to predict outcome for")
    condition: Optional[str] = Field(None, description="Condition being treated")
    time_horizon: str = Field("short_term", description="Time horizon for prediction")
    
    @field_validator('treatment')
    def treatment_not_empty(cls, v):
        """Validate that treatment is not empty."""
        if not v or not v.strip():
            raise ValueError("Treatment cannot be empty")
        return v
    
    @field_validator('time_horizon')
    def validate_time_horizon(cls, v):
        """Validate time horizon."""
        valid_horizons = ["short_term", "medium_term", "long_term"]
        if v not in valid_horizons:
            raise ValueError(f"Time horizon must be one of: {', '.join(valid_horizons)}")
        return v


class RecordTreatmentOutcomeRequest(BaseModel):
    """Request schema for recording treatment outcome."""
    
    treatment: str = Field(..., description="Treatment administered")
    outcome: str = Field(..., description="Outcome observed")
    effectiveness: str = Field(..., description="Treatment effectiveness")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('treatment', 'outcome', 'effectiveness')
    def not_empty(cls, v, info):
        """Validate that field is not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v


# Response schemas

class ClinicalTextAnalysisResponse(BaseModel):
    """Response schema for clinical text analysis."""
    
    analysis_id: str = Field(..., description="Unique ID for analysis")
    digital_twin_id: Optional[str] = Field(None, description="ID of associated digital twin")
    analysis_type: str = Field(..., description="Type of analysis performed")
    result: Dict[str, Any] = Field(..., description="Analysis result")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for analysis")
    timestamp: datetime = Field(..., description="Timestamp when analysis was performed")
    phi_detected: bool = Field(..., description="Whether PHI was detected in the text")


class PersonalizedInsightResponse(BaseModel):
    """Response schema for personalized insight."""
    
    insight_id: str = Field(..., description="Unique ID for insight")
    digital_twin_id: str = Field(..., description="ID of associated digital twin")
    query: str = Field(..., description="Query used for insight")
    insight_type: str = Field(..., description="Type of insight generated")
    insight: str = Field(..., description="Generated insight")
    key_points: List[str] = Field(..., description="Key points from the insight")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for insight")
    timestamp: datetime = Field(..., description="Timestamp when insight was generated")


class ClinicalRecommendationResponse(BaseModel):
    """Response schema for clinical recommendation."""
    
    recommendation_id: str = Field(..., description="Unique ID for recommendation")
    digital_twin_id: str = Field(..., description="ID of associated digital twin")
    query: str = Field(..., description="Query used for recommendation")
    recommendation_type: str = Field(..., description="Type of recommendation generated")
    primary_recommendations: List[str] = Field(..., description="Primary recommendations")
    alternative_recommendations: List[str] = Field(..., description="Alternative recommendations")
    implementation: List[str] = Field(..., description="Implementation guidelines")
    monitoring: List[str] = Field(..., description="Monitoring guidelines")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for recommendation")
    timestamp: datetime = Field(..., description="Timestamp when recommendation was generated")


class TreatmentOutcomeResponse(BaseModel):
    """Response schema for recorded treatment outcome."""
    
    outcome_id: str = Field(..., description="Unique ID for outcome record")
    digital_twin_id: str = Field(..., description="ID of associated digital twin")
    treatment: str = Field(..., description="Treatment administered")
    outcome: str = Field(..., description="Outcome observed")
    effectiveness: str = Field(..., description="Treatment effectiveness")
    notes: Optional[str] = Field(None, description="Additional notes")
    timestamp: datetime = Field(..., description="Timestamp when outcome was recorded")


class BiometricCorrelationResponse(BaseModel):
    """Response schema for biometric correlation analysis."""
    
    correlation_id: str = Field(..., description="Unique ID for correlation analysis")
    digital_twin_id: str = Field(..., description="ID of associated digital twin")
    biometric_type: str = Field(..., description="Type of biometric data analyzed")
    correlations: Dict[str, float] = Field(..., description="Correlation coefficients for each factor")
    significance: Dict[str, float] = Field(..., description="Statistical significance of correlations")
    sample_size: int = Field(..., gt=0, description="Sample size used for analysis")
    confidence_interval: List[float] = Field(..., description="Confidence interval for correlations")
    timestamp: datetime = Field(..., description="Timestamp when analysis was performed")


class MedicationResponsePredictionResponse(BaseModel):
    """Response schema for medication response prediction."""
    
    prediction_id: str = Field(..., description="Unique ID for prediction")
    digital_twin_id: str = Field(..., description="ID of associated digital twin")
    medication: str = Field(..., description="Medication being predicted")
    response_likelihood: float = Field(..., ge=0.0, le=1.0, description="Likelihood of positive response")
    potential_side_effects: List[str] = Field(..., description="Potential side effects")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for prediction")
    similar_cases: int = Field(..., ge=0, description="Number of similar cases used for prediction")
    timestamp: datetime = Field(..., description="Timestamp when prediction was generated")


class TreatmentPlanResponse(BaseModel):
    """Response schema for treatment plan generation."""
    
    plan_id: str = Field(..., description="Unique ID for treatment plan")
    digital_twin_id: str = Field(..., description="ID of associated digital twin")
    treatment_goals: List[str] = Field(..., description="Goals of the treatment plan")
    recommended_treatments: List[str] = Field(..., description="Recommended treatments")
    timeline: Dict[str, Any] = Field(..., description="Timeline for treatment implementation")
    monitoring_plan: List[str] = Field(..., description="Plan for monitoring treatment effectiveness")
    adjustments: List[str] = Field(..., description="Potential adjustments based on response")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for plan")
    timestamp: datetime = Field(..., description="Timestamp when plan was generated")