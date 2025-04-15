"""
Integration tests for XGBoost API endpoints.

These tests verify that the XGBoost API endpoints correctly validate input,
handle authentication, and pass data to and from the service layer.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from fastapi import FastAPI
from datetime import datetime, timezone
from fastapi import status

from app.main import app
from app.infrastructure.di.container import Container
from app.core.services.ml.xgboost.interface import XGBoostInterface
from app.core.services.ml.xgboost.exceptions import (
    ValidationError, DataPrivacyError, ResourceNotFoundError,
    ModelNotFoundError, ServiceUnavailableError
)

# Local app and client fixtures removed; tests will use client from conftest.py

from typing import Generator, Dict, Any

@pytest.fixture
def mock_xgboost_service() -> Generator[MagicMock, None, None]:
    """
    Create a mock XGBoost service.

    This patch replaces the get_xgboost_service dependency in the routes
    with a mock implementation that can be controlled in tests.
    """
    mock_service = MagicMock(spec=XGBoostInterface)

    # Setup default successful responses
    mock_service.predict_risk.return_value = {
        "prediction_id": "risk-123",
        "patient_id": "test-patient-123",
        "risk_type": "relapse",
        "risk_level": "moderate",
        "risk_score": 0.45,
        "confidence": 0.8,
        "factors": [
            {"name": "phq9_score", "importance": 0.7, "value": 12},
            {"name": "medication_adherence", "importance": 0.5, "value": 0.8}
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    mock_service.predict_treatment_response.return_value = {
        "prediction_id": "treatment-123",
        "patient_id": "test-patient-123",
        "treatment_type": "medication",
        "response_probability": 0.72,
        "estimated_efficacy": 0.68,
        "time_to_response": {
            "estimated_weeks": 4,
            "range": {"min": 2, "max": 6},
            "confidence": 0.75
        },
        "alternative_treatments": [
            {
                "treatment": "Alternative medication",
                "type": "medication",
                "probability": 0.65,
                "description": "Alternative medication option"
            }
        ],
        "confidence": 0.78,
        "factors": [
            {"name": "previous_response", "importance": 0.8, "value": "positive"},
            {"name": "symptom_duration", "importance": 0.6, "value": 12}
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    mock_service.predict_outcome.return_value = {
        "prediction_id": "outcome-123",
        "patient_id": "test-patient-123",
        "timeframe": {"weeks": 12},
        "success_probability": 0.65,
        "predicted_outcomes": {
            "timeframe_weeks": 12,
            "symptom_reduction": {
                "percent_improvement": 60,
                "confidence": 0.75
            },
            "functional_improvement": {
                "percent_improvement": 55,
                "confidence": 0.72
            },
            "relapse_risk": {
                "probability": 0.25,
                "confidence": 0.8
            }
        },
        "key_factors": [
            {"name": "treatment_adherence", "importance": 0.85, "value": "high"},
            {"name": "social_support", "importance": 0.75, "value": "moderate"}
        ],
        "recommendations": [
            {
                "category": "medication",
                "recommendation": "Continue current medication regimen"
            },
            {
                "category": "therapy",
                "recommendation": "Increase therapy frequency"
            }
        ],
        "confidence": 0.7,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    mock_service.get_feature_importance.return_value = {
        "prediction_id": "risk-123",
        "patient_id": "test-patient-123",
        "model_type": "risk",
        "features": [
            {"name": "phq9_score", "importance": 0.7, "value": 12},
            {"name": "medication_adherence", "importance": 0.5, "value": 0.8}
        ],
        "global_importance": {
            "phq9_score": 0.7,
            "medication_adherence": 0.5
        },
        "local_importance": {
            "phq9_score": 0.75,
            "medication_adherence": 0.45
        },
        "interactions": [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    mock_service.integrate_with_digital_twin.return_value = {
        "integration_id": "integration-123",
        "patient_id": "test-patient-123",
        "profile_id": "profile-123",
        "prediction_id": "risk-123",
        "status": "completed",
        "details": {
            "integration_type": "digital_twin",
            "synchronized_attributes": ["risk_level", "treatment_response"],
            "synchronization_date": datetime.now(timezone.utc).isoformat()
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    mock_service.get_model_info.return_value = {
        "model_type": "relapse_risk",
        "version": "1.0.0",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "performance_metrics": {
            "accuracy": 0.82,
            "precision": 0.80,
            "recall": 0.78,
            "f1_score": 0.79,
            "auc_roc": 0.85
        },
        "features": [
            {"name": "phq9_score", "importance": 0.7},
            {"name": "medication_adherence", "importance": 0.5}
        ],
        "description": "Relapse risk prediction model based on XGBoost"
    }

    with patch("app.api.routes.xgboost.get_xgboost_service", return_value=mock_service):
        yield mock_service

@pytest.fixture
def psychiatrist_auth_headers() -> Dict[str, str]:
    """Get authentication headers for a psychiatrist role."""
    with patch("app.api.routes.xgboost.get_current_user") as mock_auth:
        mock_auth.return_value = {
            "sub": "auth0|psychiatrist123",
            "name": "Dr. Smith",
            "email": "dr.smith@example.com",
            "role": "psychiatrist"
        }
        return {"Authorization": "Bearer psychiatrist-token"}

@pytest.fixture
def provider_auth_headers() -> Dict[str, str]:
    """Get authentication headers for a provider role."""
    with patch("app.api.routes.xgboost.get_current_user") as mock_auth:
        mock_auth.return_value = {
            "sub": "auth0|provider123",
            "name": "Provider Name",
            "email": "provider@example.com",
            "role": "provider"
        }
        return {"Authorization": "Bearer provider-token"}

@pytest.fixture
def patient_auth_headers() -> Dict[str, str]:
    """Get authentication headers for a patient role."""
    with patch("app.api.routes.xgboost.get_current_user") as mock_auth:
        mock_auth.return_value = {
            "sub": "auth0|patient123",
            "name": "Patient Name",
            "email": "patient@example.com",
            "role": "patient"
        }
        return {"Authorization": "Bearer patient-token"}

@pytest.fixture
def valid_risk_prediction_data() -> Dict[str, Any]:
    """Valid data for risk prediction request."""
    return {
        "patient_id": "test-patient-123",
        "risk_type": "relapse",
        "clinical_data": {
            "phq9_score": 12,
            "gad7_score": 9,
            "symptom_duration_weeks": 8,
            "previous_episodes": 2,
            "medication_adherence": 0.8
        },
        "demographic_data": {
            "age": 35,
            "gender": "female",
            "education_level": "college"
        },
        "confidence_threshold": 0.7
    }

@pytest.fixture
def valid_treatment_response_data() -> Dict[str, Any]:
    """Valid data for treatment response prediction request."""
    return {
        "patient_id": "test-patient-123",
        "treatment_type": "medication",
        "treatment_details": {
            "medication_class": "SSRI",
            "dosage": "20mg",
            "frequency": "daily",
            "duration_weeks": 12
        },
        "clinical_data": {
            "phq9_score": 15,
            "gad7_score": 11,
            "symptom_duration_weeks": 12,
            "previous_episodes": 1
        },
        "genetic_data": ["CYP2D6*1/*2", "CYP2C19*1/*1"],
        "treatment_history": [
            {
                "medication": "Sertraline",
                "dosage": "50mg",
                "duration_weeks": 8,
                "response": "partial",
                "side_effects": ["nausea", "insomnia"]
            }
        ]
    }

@pytest.fixture
def valid_outcome_prediction_data() -> Dict[str, Any]:
    """Valid data for outcome prediction request."""
    return {
        "patient_id": "test-patient-123",
        "outcome_timeframe": {
            "weeks": 12
        },
        "clinical_data": {
            "phq9_score": 14,
            "gad7_score": 10,
            "symptom_duration_weeks": 10,
            "previous_episodes": 2
        },
        "treatment_plan": {
            "type": "combined",
            "intensity": "moderate",
            "medications": ["fluoxetine"],
            "therapy_type": "CBT",
            "session_frequency": "weekly"
        },
        "social_determinants": {
            "social_support": "moderate",
            "employment_status": "employed",
            "financial_stability": "stable"
        },
        "comorbidities": ["hypertension", "insomnia"]
    }

class TestXGBoostAPIIntegration:
    """Integration tests for XGBoost API endpoints."""

    async def test_predict_risk_success(
        self,
        client: TestClient,
        mock_xgboost_service: MagicMock,
        psychiatrist_auth_headers: Dict[str, str],
        valid_risk_prediction_data: Dict[str, Any]
    ):
        """Test successful risk prediction."""
        # Set up mock service return value
        mock_response = {
            "prediction_id": "risk-123",
            "patient_id": "test-patient-123",
            "risk_type": "relapse",
            "risk_level": "moderate",
            "risk_score": 0.45,
            "confidence": 0.8,
            "factors": [
                {"name": "phq9_score", "importance": 0.7, "value": 12},
                {"name": "medication_adherence", "importance": 0.5, "value": 0.8}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        mock_xgboost_service.predict_risk.return_value = mock_response

        # Make API request
        response = client.post(
            "/api/v1/ml/xgboost/risk",
            json=valid_risk_prediction_data,
            headers=psychiatrist_auth_headers
        )

        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["prediction_id"] == "risk-123"
        assert result["patient_id"] == "test-patient-123"
        assert result["risk_type"] == "relapse"
        assert result["risk_level"] == "moderate"
        assert result["risk_score"] == 0.45
        assert result["confidence"] == 0.8
        assert len(result["factors"]) == 2

        # Verify service was called with correct data
        mock_xgboost_service.predict_risk.assert_called_once_with(
            patient_id="test-patient-123",
            risk_type="relapse",
            clinical_data=valid_risk_prediction_data["clinical_data"],
            demographic_data=valid_risk_prediction_data["demographic_data"],
            temporal_data=None,
            confidence_threshold=0.7
        )

    async def test_predict_risk_validation_error(
        self,
        client: TestClient,
        mock_xgboost_service: MagicMock,
        psychiatrist_auth_headers: Dict[str, str]
    ):
        """Test risk prediction with validation error."""
        # Set up mock service to raise ValidationError
        mock_xgboost_service.predict_risk.side_effect = ValidationError(
            "Invalid risk type"
        )

        # Make API request with invalid data
        response = client.post(
            "/api/v1/ml/xgboost/risk",
            json={
                "patient_id": "test-patient-123",
                "risk_type": "invalid_risk_type",  # Invalid risk type
                "clinical_data": {"phq9_score": 12}
            },
            headers=psychiatrist_auth_headers
        )

        # Verify response
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "Invalid risk type" in result["detail"]

    async def test_predict_risk_phi_detection(
        self,
        client: TestClient,
        mock_xgboost_service: MagicMock,
        psychiatrist_auth_headers: Dict[str, str]
    ):
        """Test risk prediction with PHI detection."""
        # Set up mock service to raise DataPrivacyError
        mock_xgboost_service.predict_risk.side_effect = DataPrivacyError(
            "Potential PHI detected in field value",
            {"field": "demographic_data.address", "pattern": "address"}
        )

        # Make API request with PHI data
        response = client.post(
            "/api/v1/ml/xgboost/risk",
            json={
                "patient_id": "test-patient-123",
                "risk_type": "relapse",
                "clinical_data": {"phq9_score": 12},
                "demographic_data": {
                    "age": 35,
                    "address": "123 Main St"  # Contains PHI
                }
            },
            headers=psychiatrist_auth_headers
        )

        # Verify response
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "sensitive information" in result["detail"]

    async def test_predict_risk_unauthorized(
        self,
        client: TestClient,
        mock_xgboost_service: MagicMock,
        patient_auth_headers: Dict[str, str],
        valid_risk_prediction_data: Dict[str, Any]
    ):
        """Test risk prediction with unauthorized role."""
        # Mock the validate_permissions function to raise an exception
        with patch("app.api.routes.xgboost.validate_permissions") as mock_validate:
            mock_validate.side_effect = Exception("Permission denied")

            # Make API request with patient role
            response = client.post(
                "/api/v1/ml/xgboost/risk",
                json=valid_risk_prediction_data,
                headers=patient_auth_headers
            )

            # Verify response
            assert response.status_code in [401, 403]

    async def test_predict_treatment_response_success(
        self,
        client: TestClient,
        mock_xgboost_service: MagicMock,
        psychiatrist_auth_headers: Dict[str, str],
        valid_treatment_response_data: Dict[str, Any]
    ):
        """Test successful treatment response prediction."""
        # Set up mock service return value
        mock_response = {
            "prediction_id": "treatment-123",
            "patient_id": "test-patient-123",
            "treatment_type": "medication",
            "response_probability": 0.72,
            "estimated_efficacy": 0.68,
            "time_to_response": {
                "estimated_weeks": 4,
                "range": {"min": 2, "max": 6},
                "confidence": 0.75
            },
            "alternative_treatments": [
                {
                    "treatment": "Alternative medication",
                    "type": "medication",
                    "probability": 0.65,
                    "description": "Alternative medication option"
                }
            ],
            "confidence": 0.78,
            "factors": [
                {"name": "previous_response", "importance": 0.8, "value": "positive"},
                {"name": "symptom_duration", "importance": 0.6, "value": 12}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        mock_xgboost_service.predict_treatment_response.return_value = mock_response

        # Make API request
        response = client.post(
            "/api/v1/ml/xgboost/treatment-response",
            json=valid_treatment_response_data,
            headers=psychiatrist_auth_headers
        )

        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["prediction_id"] == "treatment-123"
        assert result["patient_id"] == "test-patient-123"
        assert result["treatment_type"] == "medication"
        assert result["response_probability"] == 0.72
        assert result["estimated_efficacy"] == 0.68
        assert "time_to_response" in result
        assert "alternative_treatments" in result
        assert len(result["factors"]) == 2

        # Verify service was called with correct data
        mock_xgboost_service.predict_treatment_response.assert_called_once_with(
            patient_id="test-patient-123",
            treatment_type="medication",
            treatment_details=valid_treatment_response_data["treatment_details"],
            clinical_data=valid_treatment_response_data["clinical_data"],
            genetic_data=valid_treatment_response_data["genetic_data"],
            treatment_history=valid_treatment_response_data["treatment_history"]
        )

    async def test_predict_outcome_success(
        self,
        client: TestClient,
        mock_xgboost_service: MagicMock,
        provider_auth_headers: Dict[str, str],
        valid_outcome_prediction_data: Dict[str, Any]
    ):
        """Test successful outcome prediction."""
        # Set up mock service return value
        mock_response = {
            "prediction_id": "outcome-123",
            "patient_id": "test-patient-123",
            "timeframe": {"weeks": 12},
            "success_probability": 0.65,
            "predicted_outcomes": {
                "timeframe_weeks": 12,
                "symptom_reduction": {
                    "percent_improvement": 60,
                    "confidence": 0.75
                },
                "functional_improvement": {
                    "percent_improvement": 55,
                    "confidence": 0.72
                },
                "relapse_risk": {
                    "probability": 0.25,
                    "confidence": 0.8
                }
            },
            "key_factors": [
                {"name": "treatment_adherence", "importance": 0.85, "value": "high"},
                {"name": "social_support", "importance": 0.75, "value": "moderate"}
            ],
            "recommendations": [
                {
                    "category": "medication",
                    "recommendation": "Continue current medication regimen"
                },
                {
                    "category": "therapy",
                    "recommendation": "Increase therapy frequency"
                }
            ],
            "confidence": 0.7,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        mock_xgboost_service.predict_outcome.return_value = mock_response

        # Make API request
        response = client.post(
            "/api/v1/ml/xgboost/outcome",
            json=valid_outcome_prediction_data,
            headers=provider_auth_headers
        )

        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["prediction_id"] == "outcome-123"
        assert result["patient_id"] == "test-patient-123"
        assert result["timeframe"] == {"weeks": 12}
        assert result["success_probability"] == 0.65
        assert "predicted_outcomes" in result
        assert len(result["key_factors"]) == 2
        assert len(result["recommendations"]) == 2

        # Verify service was called with correct data
        mock_xgboost_service.predict_outcome.assert_called_once_with(
            patient_id="test-patient-123",
            outcome_timeframe=valid_outcome_prediction_data["outcome_timeframe"],
            clinical_data=valid_outcome_prediction_data["clinical_data"],
            treatment_plan=valid_outcome_prediction_data["treatment_plan"],
            social_determinants=valid_outcome_prediction_data["social_determinants"],
            comorbidities=valid_outcome_prediction_data["comorbidities"]
        )

    async def test_get_feature_importance_success(
        self,
        client: TestClient,
        mock_xgboost_service: MagicMock,
        psychiatrist_auth_headers: Dict[str, str]
    ):
        """Test successful feature importance retrieval."""
        # Set up mock service return value
        mock_response = {
            "prediction_id": "risk-123",
            "patient_id": "test-patient-123",
            "model_type": "risk",
            "features": [
                {"name": "phq9_score", "importance": 0.7, "value": 12},
                {"name": "medication_adherence", "importance": 0.5, "value": 0.8}
            ],
            "global_importance": {
                "phq9_score": 0.7,
                "medication_adherence": 0.5
            },
            "local_importance": {
                "phq9_score": 0.75,
                "medication_adherence": 0.45
            },
            "interactions": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        mock_xgboost_service.get_feature_importance.return_value = mock_response

        # Make API request
        response = client.post(
            "/api/v1/ml/xgboost/feature-importance",
            json={
                "patient_id": "test-patient-123",
                "model_type": "risk",
                "prediction_id": "risk-123"
            },
            headers=psychiatrist_auth_headers
        )

        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["prediction_id"] == "risk-123"
        assert result["patient_id"] == "test-patient-123"
        assert result["model_type"] == "risk"
        assert len(result["features"]) == 2
        assert "global_importance" in result
        assert "local_importance" in result

        # Verify service was called with correct data
        mock_xgboost_service.get_feature_importance.assert_called_once_with(
            patient_id="test-patient-123",
            model_type="risk",
            prediction_id="risk-123"
        )

    async def test_get_feature_importance_not_found(
        self,
        client: TestClient,
        mock_xgboost_service: MagicMock,
        psychiatrist_auth_headers: Dict[str, str]
    ):
        """Test feature importance retrieval with not found error."""
        # Set up mock service to raise ResourceNotFoundError
        mock_xgboost_service.get_feature_importance.side_effect = ResourceNotFoundError(
            "Feature importance not found for prediction nonexistent-id"
        )

        # Make API request
        response = client.post(
            "/api/v1/ml/xgboost/feature-importance",
            json={
                "patient_id": "test-patient-123",
                "model_type": "risk",
                "prediction_id": "nonexistent-id"
            },
            headers=psychiatrist_auth_headers
        )

        # Verify response
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"]

    async def test_integrate_with_digital_twin_success(
        self,
        client: TestClient,
        mock_xgboost_service: MagicMock,
        psychiatrist_auth_headers: Dict[str, str]
    ):
        """Test successful digital twin integration."""
        # Set up mock service return value
        mock_response = {
            "integration_id": "integration-123",
            "patient_id": "test-patient-123",
            "profile_id": "profile-123",
            "prediction_id": "risk-123",
            "status": "completed",
            "details": {
                "integration_type": "digital_twin",
                "synchronized_attributes": ["risk_level", "treatment_response"],
                "synchronization_date": datetime.now(timezone.utc).isoformat()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        mock_xgboost_service.integrate_with_digital_twin.return_value = mock_response

        # Make API request
        response = client.post(
            "/api/v1/ml/xgboost/digital-twin-integration",
            json={
                "patient_id": "test-patient-123",
                "profile_id": "profile-123",
                "prediction_id": "risk-123"
            },
            headers=psychiatrist_auth_headers
        )

        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["integration_id"] == "integration-123"
        assert result["patient_id"] == "test-patient-123"
        assert result["profile_id"] == "profile-123"
        assert result["prediction_id"] == "risk-123"
        assert result["status"] == "completed"
        assert "details" in result

        # Verify service was called with correct data
        mock_xgboost_service.integrate_with_digital_twin.assert_called_once_with(
            patient_id="test-patient-123",
            profile_id="profile-123",
            prediction_id="risk-123"
        )

    async def test_get_model_info_success(
        self,
        client: TestClient,
        mock_xgboost_service: MagicMock,
        patient_auth_headers: Dict[str, str]
    ):
        """Test successful model info retrieval."""
        # Set up mock service return value
        mock_response = {
            "model_type": "relapse_risk",
            "version": "1.0.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "performance_metrics": {
                "accuracy": 0.82,
                "precision": 0.80,
                "recall": 0.78,
                "f1_score": 0.79,
                "auc_roc": 0.85
            },
            "features": [
                {"name": "phq9_score", "importance": 0.7},
                {"name": "medication_adherence", "importance": 0.5}
            ],
            "description": "Relapse risk prediction model based on XGBoost"
        }
        mock_xgboost_service.get_model_info.return_value = mock_response

        # Make API request
        response = client.post(
            "/api/v1/ml/xgboost/model-info",
            json={"model_type": "relapse_risk"},
            headers=patient_auth_headers
        )

        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["model_type"] == "relapse_risk"
        assert result["version"] == "1.0.0"
        assert "performance_metrics" in result
        assert len(result["features"]) == 2
        assert "description" in result

        # Verify service was called with correct data
        mock_xgboost_service.get_model_info.assert_called_once_with(
            model_type="relapse_risk"
        )

    async def test_get_model_info_not_found(
        self,
        client: TestClient,
        mock_xgboost_service: MagicMock,
        psychiatrist_auth_headers: Dict[str, str]
    ):
        """Test model info retrieval with not found error."""
        # Set up mock service to raise ModelNotFoundError
        mock_xgboost_service.get_model_info.side_effect = ModelNotFoundError(
            "Model type nonexistent_model not found"
        )

        # Make API request
        response = client.post(
            "/api/v1/ml/xgboost/model-info",
            json={"model_type": "nonexistent_model"},
            headers=psychiatrist_auth_headers
        )

        # Verify response
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"]

    async def test_service_unavailable(
        self,
        client: TestClient,
        mock_xgboost_service: MagicMock,
        psychiatrist_auth_headers: Dict[str, str],
        valid_risk_prediction_data: Dict[str, Any]
    ):
        """Test handling of service unavailable error."""
        # Set up mock service to raise ServiceUnavailableError
        mock_xgboost_service.predict_risk.side_effect = ServiceUnavailableError(
            "Prediction service is currently unavailable"
        )

        # Make API request
        response = client.post(
            "/api/v1/ml/xgboost/risk",
            json=valid_risk_prediction_data,
            headers=psychiatrist_auth_headers
        )

        # Verify response
        assert response.status_code == 503
        result = response.json()
        assert "detail" in result
        assert "unavailable" in result["detail"]
