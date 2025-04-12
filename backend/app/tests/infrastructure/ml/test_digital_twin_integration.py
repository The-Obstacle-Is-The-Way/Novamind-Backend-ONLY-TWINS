# -*- coding: utf-8 -*-
"""
Tests for the Digital Twin Integration Service.

This module contains tests for the Digital Twin Integration Service, which
coordinates all ML microservices and provides a unified interface for the
domain layer, following Clean Architecture principles and ensuring HIPAA compliance.
"""
import pytest
import os
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from uuid import UUID, uuid4

from app.infrastructure.ml.digital_twin_integration_service import (
    DigitalTwinIntegrationService,
)
from app.domain.exceptions import ModelInferenceError, ValidationError


@pytest.fixture
def mock_symptom_forecasting_service():
    """Create a mock symptom forecasting service."""
    service = AsyncMock()
    service.forecast_symptoms = AsyncMock(
        return_value={
            "forecasts": {"anxiety": [5, 4, 3, 4, 5], "depression": [3, 3, 2, 2, 3]},
            "risk_levels": {
                "anxiety": ["medium", "medium", "low", "medium", "medium"],
                "depression": ["low", "low", "low", "low", "low"],
            },
            "confidence_intervals": {
                "anxiety": {"lower": [4, 3, 2, 3, 4], "upper": [6, 5, 4, 5, 6]},
                "depression": {"lower": [2, 2, 1, 1, 2], "upper": [4, 4, 3, 3, 4]},
            },
            "trending_symptoms": [
                {
                    "symptom": "anxiety",
                    "trend": "stable",
                    "insight_text": "Anxiety levels remain stable",
                    "importance": 0.7,
                }
            ],
            "risk_alerts": [],
        }
    )
    return service


@pytest.fixture
def mock_biometric_correlation_service():
    """Create a mock biometric correlation service."""
    service = AsyncMock()
    service.analyze_correlations = AsyncMock(
        return_value={
            "key_indicators": [
                {
                    "biometric": "heart_rate",
                    "correlation": 0.75,
                    "mental_health_indicator": "anxiety",
                }
            ],
            "lag_correlations": [
                {
                    "biometric": "sleep_quality",
                    "lag_days": 2,
                    "mental_health_indicator": "depression",
                    "correlation": 0.65,
                }
            ],
            "insights": [
                {
                    "insight_text": "Heart rate strongly correlates with anxiety levels",
                    "importance": 0.8,
                }
            ],
            "monitoring_plan": {
                "primary_metrics": ["heart_rate", "sleep_quality"],
                "monitoring_frequency": "daily",
            },
        }
    )
    return service


@pytest.fixture
def mock_pharmacogenomics_service():
    """Create a mock pharmacogenomics service."""
    service = AsyncMock()
    service.predict_medication_responses = AsyncMock(
        return_value={
            "medication_predictions": {
                "fluoxetine": {
                    "response_probability": {"good": 0.7, "moderate": 0.2, "poor": 0.1},
                    "side_effect_risk": {"low": 0.6, "moderate": 0.3, "high": 0.1},
                },
                "sertraline": {
                    "response_probability": {"good": 0.5, "moderate": 0.3, "poor": 0.2},
                    "side_effect_risk": {"low": 0.4, "moderate": 0.4, "high": 0.2},
                },
            },
            "recommendations": {
                "primary_recommendations": [
                    {
                        "medication": "fluoxetine",
                        "rationale": "High probability of good response with low side effect risk",
                    }
                ],
                "alternative_recommendations": [
                    {
                        "medication": "sertraline",
                        "rationale": "Moderate probability of good response",
                    }
                ],
            },
            "genetic_insights": [
                {
                    "gene": "CYP2D6",
                    "variant": "Normal metabolizer",
                    "insight": "Standard dosing appropriate",
                }
            ],
        }
    )
    return service


@pytest.fixture
def integration_service(
    mock_symptom_forecasting_service,
    mock_biometric_correlation_service,
    mock_pharmacogenomics_service,
):
    """Create a Digital Twin Integration Service with mock microservices."""
    service = DigitalTwinIntegrationService(
        model_base_dir="./test_models",
        symptom_forecasting_service=mock_symptom_forecasting_service,
        biometric_correlation_service=mock_biometric_correlation_service,
        pharmacogenomics_service=mock_pharmacogenomics_service,
    )
    return service


@pytest.fixture
def patient_data():
    """Create sample patient data for testing."""

    return {
        "symptom_history": [
            {"date": "2023-01-01", "anxiety": 5, "depression": 3},
            {"date": "2023-01-02", "anxiety": 6, "depression": 4},
            {"date": "2023-01-03", "anxiety": 4, "depression": 3},
            {"date": "2023-01-04", "anxiety": 5, "depression": 2},
            {"date": "2023-01-05", "anxiety": 5, "depression": 3},
        ],
        "biometric_data": [
            {
                "date": "2023-01-01",
                "heart_rate": 75,
                "sleep_quality": 0.7,
                "activity_level": 0.6,
            },
            {
                "date": "2023-01-02",
                "heart_rate": 80,
                "sleep_quality": 0.6,
                "activity_level": 0.5,
            },
            {
                "date": "2023-01-03",
                "heart_rate": 70,
                "sleep_quality": 0.8,
                "activity_level": 0.7,
            },
            {
                "date": "2023-01-04",
                "heart_rate": 72,
                "sleep_quality": 0.7,
                "activity_level": 0.6,
            },
            {
                "date": "2023-01-05",
                "heart_rate": 74,
                "sleep_quality": 0.7,
                "activity_level": 0.6,
            },
        ],
        "mental_health_indicators": [
            {"date": "2023-01-01", "anxiety_level": 5, "depression_level": 3},
            {"date": "2023-01-02", "anxiety_level": 6, "depression_level": 4},
            {"date": "2023-01-03", "anxiety_level": 4, "depression_level": 3},
            {"date": "2023-01-04", "anxiety_level": 5, "depression_level": 2},
            {"date": "2023-01-05", "anxiety_level": 5, "depression_level": 3},
        ],
        "genetic_markers": {
            "CYP2D6": 0,
            "CYP2C19": 0,
            "CYP2C9": 0,
            "SLC6A4": 1,
            "HTR2A": 0,
        },
    }


@pytest.mark.asyncio()
@pytest.mark.venv_only()
async def test_generate_comprehensive_patient_insights(
    integration_service, patient_data
):
    """Test generating comprehensive patient insights."""
    patient_id = uuid4()

    # Generate insights
    insights = await integration_service.generate_comprehensive_patient_insights(
        patient_id=patient_id, patient_data=patient_data
    )

    # Verify insights structure
    assert "patient_id" in insights
    assert insights["patient_id"] == str(patient_id)
    assert "generated_at" in insights

    # Verify symptom forecasting results
    assert "symptom_forecasting" in insights
    assert "forecasts" in insights["symptom_forecasting"]
    assert "anxiety" in insights["symptom_forecasting"]["forecasts"]
    assert "depression" in insights["symptom_forecasting"]["forecasts"]

    # Verify biometric correlation results
    assert "biometric_correlation" in insights
    assert "key_indicators" in insights["biometric_correlation"]
    assert "monitoring_plan" in insights["biometric_correlation"]

    # Verify pharmacogenomics results
    assert "pharmacogenomics" in insights
    assert "medication_predictions" in insights["pharmacogenomics"]
    assert "recommendations" in insights["pharmacogenomics"]

    # Verify integrated recommendations
    assert "integrated_recommendations" in insights
    assert len(insights["integrated_recommendations"]) > 0


@pytest.mark.asyncio()
async def test_generate_insights_with_missing_data(integration_service):
    """Test generating insights with missing data."""
    patient_id = uuid4()

    # Create patient data with missing components
    incomplete_data = {
        "symptom_history": [
            {"date": "2023-01-01", "anxiety": 5, "depression": 3},
            {"date": "2023-01-02", "anxiety": 6, "depression": 4},
        ]
        # Missing biometric_data, mental_health_indicators, and genetic_markers
    }

    # Generate insights with incomplete data
    insights = await integration_service.generate_comprehensive_patient_insights(
        patient_id=patient_id, patient_data=incomplete_data
    )

    # Verify that only symptom forecasting results are present
    assert "symptom_forecasting" in insights
    assert "biometric_correlation" not in insights
    assert "pharmacogenomics" not in insights

    # Verify that integrated recommendations are still generated
    assert "integrated_recommendations" in insights


@pytest.mark.asyncio()
async def test_generate_insights_with_invalid_data(integration_service):
    """Test generating insights with invalid data."""
    patient_id = uuid4()

    # Create empty patient data
    empty_data = {}

    # Verify that validation error is raised
    with pytest.raises(ValidationError):
        await integration_service.generate_comprehensive_patient_insights(
            patient_id=patient_id, patient_data=empty_data
        )


@pytest.mark.asyncio()
async def test_run_symptom_forecasting(integration_service, patient_data):
    """Test running symptom forecasting independently."""
    patient_id = uuid4()

    # Run symptom forecasting
    results = await integration_service._run_symptom_forecasting(
        patient_id=patient_id, patient_data=patient_data
    )

    # Verify results
    assert "symptom_forecasting" in results
    assert "symptom_forecasting_insights" in results
    assert len(results["symptom_forecasting_insights"]) > 0


@pytest.mark.asyncio()
async def test_run_biometric_correlation(integration_service, patient_data):
    """Test running biometric correlation independently."""
    patient_id = uuid4()

    # Run biometric correlation
    results = await integration_service._run_biometric_correlation(
        patient_id=patient_id, patient_data=patient_data
    )

    # Verify results
    assert "biometric_correlation" in results
    assert "biometric_correlation_insights" in results
    assert len(results["biometric_correlation_insights"]) > 0


@pytest.mark.asyncio()
async def test_run_pharmacogenomics(integration_service, patient_data):
    """Test running pharmacogenomics independently."""
    patient_id = uuid4()

    # Run pharmacogenomics
    results = await integration_service._run_pharmacogenomics(
        patient_id=patient_id, patient_data=patient_data
    )

    # Verify results
    assert "pharmacogenomics" in results
    assert "pharmacogenomics_insights" in results
    assert len(results["pharmacogenomics_insights"]) > 0


@pytest.mark.asyncio()
async def test_generate_integrated_recommendations(integration_service):
    """Test generating integrated recommendations."""
    # Create mock results from individual microservices
    results = [
        {
            "symptom_forecasting": {"forecasts": {"anxiety": [5, 4, 3, 4, 5]}},
            "symptom_forecasting_insights": [
                {
                    "source": "symptom_forecasting",
                    "insight": "Anxiety levels remain stable",
                    "importance": 0.7,
                }
            ],
        },
        {
            "biometric_correlation": {
                "key_indicators": [{"biometric": "heart_rate", "correlation": 0.75}]
            },
            "biometric_correlation_insights": [
                {
                    "source": "biometric_correlation",
                    "insight": "Heart rate correlates with anxiety",
                    "importance": 0.8,
                }
            ],
        },
        {
            "pharmacogenomics": {
                "recommendations": {
                    "primary_recommendations": [{"medication": "fluoxetine"}]
                }
            },
            "pharmacogenomics_insights": [
                {
                    "source": "pharmacogenomics",
                    "insight": "Good predicted response to fluoxetine",
                    "importance": 0.9,
                }
            ],
        },
    ]

    # Generate integrated recommendations
    recommendations = await integration_service._generate_integrated_recommendations(
        results
    )

    # Verify recommendations
    assert len(recommendations) > 0
    assert "clinical_recommendations" in recommendations
    assert "monitoring_recommendations" in recommendations
    assert "treatment_recommendations" in recommendations

    # Verify that recommendations are sorted by importance
    clinical_recs = recommendations["clinical_recommendations"]
    assert len(clinical_recs) > 0
    if len(clinical_recs) > 1:
        assert clinical_recs[0]["importance"] >= clinical_recs[1]["importance"]

        @pytest.mark.asyncio()
        async def test_handle_microservice_failure(
                integration_service, patient_data):
    """Test handling of microservice failures."""
    patient_id = uuid4()

    # Make symptom forecasting service fail
    integration_service.symptom_forecasting_service.forecast_symptoms.side_effect = (
        ModelInferenceError("Test error"))

    # Generate insights despite the failure
    insights = await integration_service.generate_comprehensive_patient_insights(
        patient_id=patient_id, patient_data=patient_data
    )

    # Verify that other services still produced results
    assert "symptom_forecasting" not in insights
    assert "biometric_correlation" in insights
    assert "pharmacogenomics" in insights
    assert "integrated_recommendations" in insights


@pytest.mark.asyncio()
async def test_sanitize_patient_data(integration_service, patient_data):
    """Test sanitization of patient data for HIPAA compliance."""
    # Add PHI to patient data
    patient_data_with_phi = patient_data.copy()
    patient_data_with_phi["name"] = "John Doe"
    patient_data_with_phi["email"] = "john.doe@example.com"
    patient_data_with_phi["ssn"] = "123-45-6789"

    # Sanitize data
    sanitized_data = integration_service._sanitize_patient_data(
        patient_data_with_phi)

    # Verify that PHI is removed
    assert "name" not in sanitized_data
    assert "email" not in sanitized_data
    assert "ssn" not in sanitized_data

    # Verify that non-PHI data is preserved
    assert "symptom_history" in sanitized_data
    assert "biometric_data" in sanitized_data
    assert "mental_health_indicators" in sanitized_data
    assert "genetic_markers" in sanitized_data
