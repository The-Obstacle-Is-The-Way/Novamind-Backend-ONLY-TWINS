# -*- coding: utf-8 -*-
"""
API Dependencies Module.

This module provides FastAPI dependency functions for injecting
services and repositories into API routes.
"""

from typing import AsyncGenerator, Dict, Any, List

from fastapi import Depends

from app.core.config.ml_settings import get_ml_settings
from app.infrastructure.ml.phi_detection import PHIDetectionService
from app.infrastructure.ml.mentallama import MentaLLaMAService
from app.infrastructure.ml.digital_twin_integration_service import DigitalTwinIntegrationService


# Get ML settings once for all dependencies
ml_settings = get_ml_settings()


# Dependency for PHI Detection Service
async def get_phi_detection_service() -> AsyncGenerator[PHIDetectionService, None]:
    """
    Provide a PHI detection service instance.
    
    This dependency creates and initializes a PHI detection service
    for use in routes that need to detect and anonymize PHI.
    
    Yields:
        PHI detection service instance
    """
    service = PHIDetectionService(
        pattern_file=ml_settings.phi_detection.pattern_file
    )
    
    # Ensure service is initialized
    service.ensure_initialized()
    
    yield service


# Dependency for MentaLLaMA Service
async def get_mentallama_service(
    phi_detection_service: PHIDetectionService = Depends(get_phi_detection_service)
) -> AsyncGenerator[MentaLLaMAService, None]:
    """
    Provide a MentaLLaMA service instance.
    
    This dependency creates and initializes a MentaLLaMA service
    for clinical text analysis, using PHI detection for HIPAA compliance.
    
    Args:
        phi_detection_service: PHI detection service for anonymizing PHI
        
    Yields:
        MentaLLaMA service instance
    """
    service = MentaLLaMAService(
        phi_detection_service=phi_detection_service,
        api_key=ml_settings.mentallama.api_key,
        api_endpoint=ml_settings.mentallama.api_endpoint,
        model_name=ml_settings.mentallama.default_model,
        temperature=ml_settings.mentallama.temperature
    )
    
    try:
        yield service
    finally:
        # Clean up resources
        await service.close()


# Mock repositories and services for testing
class MockPatientRepository:
    """Mock patient repository for testing."""
    
    async def get_by_id(self, patient_id: str) -> Dict[str, Any]:
        """Get patient by ID."""
        return {
            "id": patient_id,
            "conditions": ["Major Depressive Disorder", "Generalized Anxiety Disorder"],
            "medications": [
                {"name": "Fluoxetine", "dosage": "20mg", "frequency": "daily"},
                {"name": "Clonazepam", "dosage": "0.5mg", "frequency": "as needed"}
            ]
        }


class MockSymptomForecastingService:
    """Mock symptom forecasting service for testing."""
    
    async def generate_forecast(self, patient_id: str, days: int = 14, historical_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a symptom forecast."""
        return {
            "patient_id": patient_id,
            "forecast_days": days,
            "predictions": [
                {"day": 1, "depression_severity": 0.7, "anxiety_severity": 0.6},
                {"day": 2, "depression_severity": 0.65, "anxiety_severity": 0.55},
                {"day": 3, "depression_severity": 0.6, "anxiety_severity": 0.5}
            ]
        }


class MockBiometricCorrelationService:
    """Mock biometric correlation service for testing."""
    
    async def analyze_correlations(self, patient_id: str, lookback_days: int = 30) -> Dict[str, Any]:
        """Analyze biometric correlations."""
        return {
            "patient_id": patient_id,
            "correlations": [
                {"biometric": "heart_rate", "symptom": "anxiety", "correlation": 0.75, "lag_hours": 8},
                {"biometric": "sleep_duration", "symptom": "depression", "correlation": -0.8, "lag_hours": 24}
            ]
        }


class MockMedicationResponseService:
    """Mock medication response service for testing."""
    
    async def predict_medication_response(self, patient_id: str) -> Dict[str, Any]:
        """Predict medication response."""
        return {
            "patient_id": patient_id,
            "medications": [
                {"name": "Fluoxetine", "predicted_efficacy": 0.72, "side_effects": ["nausea", "insomnia"]},
                {"name": "Sertraline", "predicted_efficacy": 0.68, "side_effects": ["dizziness", "dry_mouth"]},
                {"name": "Escitalopram", "predicted_efficacy": 0.65, "side_effects": ["headache"]}
            ]
        }


# Dependency for Digital Twin Service
async def get_digital_twin_service(
    mentallama_service: MentaLLaMAService = Depends(get_mentallama_service)
) -> AsyncGenerator[DigitalTwinIntegrationService, None]:
    """
    Provide a Digital Twin integration service instance.
    
    This dependency creates and initializes a Digital Twin integration service
    for patient-specific neural network modeling and simulation.
    
    Args:
        mentallama_service: MentaLLaMA service instance
        
    Yields:
        Digital Twin integration service instance
    """
    # Create mock services for testing
    # In production, these would be real service instances from other dependencies
    symptom_forecasting_service = MockSymptomForecastingService()
    biometric_correlation_service = MockBiometricCorrelationService()
    medication_response_service = MockMedicationResponseService()
    patient_repository = MockPatientRepository()
    
    # Create Digital Twin service
    service = DigitalTwinIntegrationService(
        symptom_forecasting_service=symptom_forecasting_service,
        biometric_correlation_service=biometric_correlation_service,
        medication_response_service=medication_response_service,
        patient_repository=patient_repository
    )
    
    # Initialize service
    await service.initialize()
    
    try:
        yield service
    finally:
        # Clean up resources
        await service.close()