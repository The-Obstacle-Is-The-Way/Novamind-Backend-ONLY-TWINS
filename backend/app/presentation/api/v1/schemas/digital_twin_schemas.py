# -*- coding: utf-8 -*-
"""
Digital Twin API schemas for the v1 API.

This module provides Pydantic schemas for digital twin endpoints, focusing on 
status responses, insights, forecasting, and treatment recommendations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class ComponentStatus(BaseModel):
    """Status of a digital twin component."""
    
    has_model: bool = Field(..., description="Whether a model exists for this component")
    last_updated: str = Field(..., description="ISO timestamp of last update")
    
    
class ServiceInfo(BaseModel):
    """Information about a service."""
    
    version: str = Field(..., description="Service version")


class ComponentServiceStatus(BaseModel):
    """Status of a service component."""
    
    service_available: bool = Field(..., description="Whether the service is available")
    service_info: ServiceInfo = Field(..., description="Service information")


class DigitalTwinStatusResponse(BaseModel):
    """Response schema for digital twin status."""
    
    patient_id: str = Field(..., description="Patient ID")
    status: str = Field(..., description="Overall status of the digital twin")
    completeness: int = Field(..., description="Percentage of completeness")
    components: Dict[str, Union[ComponentStatus, ComponentServiceStatus]] = Field(
        ..., description="Status of individual components"
    )
    last_checked: str = Field(..., description="ISO timestamp of last check")


class TrendingSymptom(BaseModel):
    """Information about a trending symptom."""
    
    symptom: str = Field(..., description="Name of the symptom")
    trend: str = Field(..., description="Trend direction (increasing, decreasing, stable)")
    confidence: float = Field(..., description="Confidence in the trend")
    insight_text: str = Field(..., description="Text insight about the trend")


class RiskAlert(BaseModel):
    """Information about a risk alert."""
    
    symptom: str = Field(..., description="Name of the symptom")
    risk_level: str = Field(..., description="Level of risk (low, moderate, high)")
    alert_text: str = Field(..., description="Text alert about the risk")
    importance: float = Field(..., description="Importance of the alert")


class SymptomForecastingInsights(BaseModel):
    """Symptom forecasting insights."""
    
    trending_symptoms: List[TrendingSymptom] = Field(..., description="Trending symptoms")
    risk_alerts: List[RiskAlert] = Field(..., description="Risk alerts")


class BiometricCorrelation(BaseModel):
    """Information about a biometric correlation."""
    
    biometric_type: str = Field(..., description="Type of biometric data")
    mental_health_indicator: str = Field(..., description="Mental health indicator correlated with")
    correlation_strength: float = Field(..., description="Strength of correlation")
    direction: str = Field(..., description="Direction of correlation (positive, negative)")
    insight_text: str = Field(..., description="Text insight about the correlation")
    p_value: float = Field(..., description="P-value of the correlation")


class BiometricCorrelationInsights(BaseModel):
    """Biometric correlation insights."""
    
    strong_correlations: List[BiometricCorrelation] = Field(..., description="Strong correlations")


class MedicationResponsePrediction(BaseModel):
    """Information about a medication response prediction."""
    
    medication: str = Field(..., description="Name of medication")
    predicted_response: str = Field(..., description="Predicted response")
    confidence: float = Field(..., description="Confidence in prediction")


class MedicationResponsePredictions(BaseModel):
    """Medication response predictions."""
    
    predictions: List[MedicationResponsePrediction] = Field(..., description="Medication response predictions")


class PharmacogenomicsInsights(BaseModel):
    """Pharmacogenomics insights."""
    
    medication_responses: MedicationResponsePredictions = Field(..., description="Medication response predictions")


class Recommendation(BaseModel):
    """Information about a recommendation."""
    
    source: str = Field(..., description="Source of recommendation")
    type: str = Field(..., description="Type of recommendation")
    recommendation: str = Field(..., description="Recommendation text")
    importance: float = Field(..., description="Importance of recommendation")


class PatientInsightsResponse(BaseModel):
    """Response schema for patient insights."""
    
    patient_id: str = Field(..., description="Patient ID")
    generated_at: str = Field(..., description="ISO timestamp of generation")
    symptom_forecasting: SymptomForecastingInsights = Field(..., description="Symptom forecasting insights")
    biometric_correlation: BiometricCorrelationInsights = Field(..., description="Biometric correlation insights")
    pharmacogenomics: PharmacogenomicsInsights = Field(..., description="Pharmacogenomics insights")
    integrated_recommendations: List[Recommendation] = Field(..., description="Integrated recommendations")


class ForecastPoint(BaseModel):
    """A point in a symptom forecast."""
    
    date: str = Field(..., description="Date of forecast")
    symptom: str = Field(..., description="Name of symptom")
    severity: float = Field(..., description="Predicted severity")
    confidence_low: float = Field(..., description="Lower bound of confidence interval")
    confidence_high: float = Field(..., description="Upper bound of confidence interval")


class SymptomForecastResponse(BaseModel):
    """Response schema for symptom forecast."""
    
    patient_id: str = Field(..., description="Patient ID")
    forecast_days: int = Field(..., description="Number of days in forecast")
    generated_at: str = Field(..., description="ISO timestamp of generation")
    forecast_points: List[ForecastPoint] = Field(..., description="Forecast points")
    trending_symptoms: List[TrendingSymptom] = Field(..., description="Trending symptoms")
    risk_alerts: List[RiskAlert] = Field(..., description="Risk alerts")


class Anomaly(BaseModel):
    """Information about a data anomaly."""
    
    data_type: str = Field(..., description="Type of data")
    description: str = Field(..., description="Description of anomaly")
    severity: float = Field(..., description="Severity of anomaly")
    detected_at: str = Field(..., description="ISO timestamp of detection")


class DataQuality(BaseModel):
    """Information about data quality."""
    
    completeness: float = Field(..., description="Completeness of data")
    consistency: float = Field(..., description="Consistency of data")


class BiometricCorrelationResponse(BaseModel):
    """Response schema for biometric correlations."""
    
    patient_id: str = Field(..., description="Patient ID")
    window_days: int = Field(..., description="Number of days in window")
    generated_at: str = Field(..., description="ISO timestamp of generation")
    strong_correlations: List[BiometricCorrelation] = Field(..., description="Strong correlations")
    anomalies: List[Anomaly] = Field(..., description="Data anomalies")
    data_quality: DataQuality = Field(..., description="Data quality information")


class GeneticFactor(BaseModel):
    """Information about a genetic factor."""
    
    gene: str = Field(..., description="Gene name")
    variant: str = Field(..., description="Gene variant")
    impact: str = Field(..., description="Impact of variant")


class MedicationPrediction(BaseModel):
    """Information about a medication prediction."""
    
    medication: str = Field(..., description="Name of medication")
    predicted_response: str = Field(..., description="Predicted response")
    confidence: float = Field(..., description="Confidence in prediction")
    potential_side_effects: List[str] = Field(..., description="Potential side effects")
    genetic_factors: List[GeneticFactor] = Field(..., description="Genetic factors")


class Insight(BaseModel):
    """Information about an insight."""
    
    insight_text: str = Field(..., description="Insight text")
    importance: float = Field(..., description="Importance of insight")


class MedicationResponsePredictionResponse(BaseModel):
    """Response schema for medication response predictions."""
    
    patient_id: str = Field(..., description="Patient ID")
    generated_at: str = Field(..., description="ISO timestamp of generation")
    predictions: List[MedicationPrediction] = Field(..., description="Medication predictions")
    insights: List[Insight] = Field(..., description="Insights")


class TreatmentRecommendation(BaseModel):
    """Information about a treatment recommendation."""
    
    type: str = Field(..., description="Type of recommendation")
    recommendation_text: str = Field(..., description="Recommendation text")
    importance: float = Field(..., description="Importance of recommendation")
    evidence_level: str = Field(..., description="Level of evidence")
    genetic_basis: Optional[List[GeneticFactor]] = Field(None, description="Genetic basis")


class PersonalizationFactor(BaseModel):
    """Information about a personalization factor."""
    
    factor: str = Field(..., description="Factor name")
    impact: str = Field(..., description="Impact level")
    description: str = Field(..., description="Description of impact")


class TreatmentRecommendations(BaseModel):
    """Treatment recommendations."""
    
    medications: List[TreatmentRecommendation] = Field(..., description="Medication recommendations")
    therapy: List[TreatmentRecommendation] = Field(..., description="Therapy recommendations")
    lifestyle: List[TreatmentRecommendation] = Field(..., description="Lifestyle recommendations")
    summary: List[TreatmentRecommendation] = Field(..., description="Summary recommendations")


class TreatmentPlanResponse(BaseModel):
    """Response schema for treatment plan."""
    
    patient_id: str = Field(..., description="Patient ID")
    diagnosis: str = Field(..., description="Diagnosis")
    generated_at: str = Field(..., description="ISO timestamp of generation")
    recommendations: TreatmentRecommendations = Field(..., description="Treatment recommendations")
    personalization_factors: List[PersonalizationFactor] = Field(..., description="Personalization factors")