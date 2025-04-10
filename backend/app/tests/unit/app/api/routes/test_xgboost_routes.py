"""
Unit tests for the XGBoost API routes.
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.routes.xgboost import router
from app.core.services.ml.xgboost.interface import XGBoostInterface, EventType
from app.core.services.ml.xgboost.exceptions import (
    ValidationError,
    DataPrivacyError,
    ResourceNotFoundError,
    ModelNotFoundError,
    PredictionError,
    ServiceConnectionError
)


@pytest.fixture
def mock_xgboost_service():
    """Fixture for mocked XGBoost service."""
    mock_service = MagicMock(spec=XGBoostInterface)
    return mock_service


@pytest.fixture
def mock_user():
    """Fixture for mocked authenticated user."""
    return {
        "sub": "user123",
        "email": "doctor@example.com",
        "groups": ["psychiatrists"],
        "exp": (datetime.now() + timedelta(hours=1)).timestamp()
    }


@pytest.fixture
def app(mock_xgboost_service, mock_user):
    """Create a test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)
    
    # Mock the dependencies
    async def get_mock_xgboost_service():
        return mock_xgboost_service
    
    async def get_mock_user():
        return mock_user
    
    async def verify_mock_psychiatrist():
        return True
    
    app.dependency_overrides = {
        "app.api.routes.xgboost.get_xgboost_service": get_mock_xgboost_service,
        "app.api.routes.xgboost.get_token_user": get_mock_user,
        "app.api.routes.xgboost.verify_psychiatrist": verify_mock_psychiatrist
    }
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return TestClient(app)


@pytest.fixture
def risk_prediction_request():
    """Fixture for risk prediction request data."""
    return {
        "patient_id": "P12345",
        "clinical_data": {
            "symptom_severity": 7,
            "medication_adherence": 0.8,
            "previous_episodes": 2,
            "social_support": 5,
            "stress_level": 6
        },
        "time_frame_days": 30
    }


@pytest.fixture
def risk_prediction_response():
    """Fixture for risk prediction response data."""
    return {
        "prediction_id": "risk-123456-P12345",
        "prediction_score": 0.7,
        "risk_level": "moderate",
        "confidence": 0.85,
        "factors": ["symptom_severity", "previous_episodes"],
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def treatment_response_request():
    """Fixture for treatment response request data."""
    return {
        "patient_id": "P12345",
        "clinical_data": {
            "symptom_severity": 7,
            "medication_adherence": 0.8,
            "previous_episodes": 2,
            "social_support": 5,
            "stress_level": 6
        },
        "treatment_details": {
            "medication": "Fluoxetine",
            "dosage": "20mg",
            "frequency": "daily",
            "duration_weeks": 8
        },
        "prediction_horizon": "8_weeks"
    }


@pytest.fixture
def treatment_response_response():
    """Fixture for treatment response response data."""
    return {
        "prediction_id": "treatment-123456-P12345",
        "response_probability": 0.65,
        "response_level": "moderate",
        "confidence": 0.8,
        "time_to_response_weeks": 4,
        "factors": ["symptom_severity", "previous_treatment_response"],
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def outcome_prediction_request():
    """Fixture for outcome prediction request data."""
    return {
        "patient_id": "P12345",
        "clinical_data": {
            "symptom_severity": 7,
            "medication_adherence": 0.8,
            "previous_episodes": 2,
            "social_support": 5,
            "stress_level": 6
        },
        "treatment_plan": {
            "medications": [
                {
                    "name": "Fluoxetine",
                    "dosage": "20mg",
                    "frequency": "daily",
                    "duration_weeks": 8
                }
            ],
            "therapy": {
                "type": "CBT",
                "frequency": "weekly",
                "duration_weeks": 12
            },
            "lifestyle_changes": [
                "Regular exercise",
                "Sleep hygiene",
                "Stress management"
            ]
        },
        "outcome_timeframe": {
            "weeks": 8
        }
    }


@pytest.fixture
def outcome_prediction_response():
    """Fixture for outcome prediction response data."""
    return {
        "prediction_id": "outcome-123456-P12345",
        "outcome_score": 0.75,
        "outcome_category": "Remission",
        "confidence": 0.85,
        "projected_changes": {
            "symptom_reduction": 0.6,
            "functioning_improvement": 0.5
        },
        "factors": ["baseline_severity", "treatment_adherence"],
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def feature_importance_request():
    """Fixture for feature importance request data."""
    return {
        "patient_id": "P12345",
        "model_type": "relapse-risk",
        "prediction_id": "risk-123456-P12345"
    }


@pytest.fixture
def feature_importance_response():
    """Fixture for feature importance response data."""
    return {
        "features": [
            {"name": "symptom_severity", "importance": 0.35},
            {"name": "previous_episodes", "importance": 0.25},
            {"name": "medication_adherence", "importance": 0.2},
            {"name": "social_support", "importance": 0.15},
            {"name": "stress_level", "importance": 0.05}
        ],
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def digital_twin_integration_request():
    """Fixture for digital twin integration request data."""
    return {
        "patient_id": "P12345",
        "profile_id": "DP67890",
        "prediction_id": "risk-123456-P12345"
    }


@pytest.fixture
def digital_twin_integration_response():
    """Fixture for digital twin integration response data."""
    return {
        "integration_id": "integration-123456",
        "status": "success",
        "details": {
            "updated_regions": ["amygdala", "prefrontal_cortex"],
            "confidence": 0.85
        },
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def model_info_response():
    """Fixture for model info response data."""
    return {
        "model_type": "relapse-risk",
        "version": "1.2.0",
        "last_updated": datetime.now().isoformat(),
        "description": "XGBoost model for relapse risk prediction",
        "features": [
            "symptom_severity",
            "medication_adherence",
            "previous_episodes",
            "social_support",
            "stress_level"
        ],
        "performance_metrics": {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.80,
            "f1_score": 0.81,
            "auc_roc": 0.88
        },
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 5,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8
        },
        "status": "active"
    }


class TestRiskPredictionEndpoint:
    """Test suite for the risk prediction endpoint."""
    
    def test_predict_risk_success(
        self,
        client,
        mock_xgboost_service,
        risk_prediction_request,
        risk_prediction_response
    ):
        """Test successful risk prediction."""
        # Mock the service method
        mock_xgboost_service.predict_risk.return_value = risk_prediction_response
        
        # Make the request
        response = client.post(
            f"/api/v1/xgboost/risk/relapse",
            json=risk_prediction_request
        )
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert "prediction_id" in response.json()
        assert "risk_level" in response.json()
        assert "confidence" in response.json()
        assert "factors" in response.json()
        
        # Check that the service was called correctly
        mock_xgboost_service.predict_risk.assert_called_once_with(
            patient_id=risk_prediction_request["patient_id"],
            risk_type="relapse",
            clinical_data=risk_prediction_request["clinical_data"],
            time_frame_days=risk_prediction_request["time_frame_days"]
        )
    
    def test_predict_risk_validation_error(
        self,
        client,
        mock_xgboost_service,
        risk_prediction_request
    ):
        """Test risk prediction with validation error."""
        # Mock the service method to raise an error
        mock_xgboost_service.predict_risk.side_effect = ValidationError(
            "Invalid clinical data",
            field="clinical_data"
        )
        
        # Make the request
        response = client.post(
            f"/api/v1/xgboost/risk/relapse",
            json=risk_prediction_request
        )
        
        # Check response
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error_type" in response.json()
        assert response.json()["error_type"] == "ValidationError"
    
    def test_predict_risk_data_privacy_error(
        self,
        client,
        mock_xgboost_service,
        risk_prediction_request
    ):
        """Test risk prediction with data privacy error."""
        # Mock the service method to raise an error
        mock_xgboost_service.predict_risk.side_effect = DataPrivacyError(
            "PHI detected in clinical data",
            pattern_types=["SSN"]
        )
        
        # Make the request
        response = client.post(
            f"/api/v1/xgboost/risk/relapse",
            json=risk_prediction_request
        )
        
        # Check response
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "error_type" in response.json()
        assert response.json()["error_type"] == "DataPrivacyError"
    
    def test_predict_risk_model_not_found(
        self,
        client,
        mock_xgboost_service,
        risk_prediction_request
    ):
        """Test risk prediction with model not found error."""
        # Mock the service method to raise an error
        mock_xgboost_service.predict_risk.side_effect = ModelNotFoundError(
            "Model not found: relapse",
            model_type="relapse"
        )
        
        # Make the request
        response = client.post(
            f"/api/v1/xgboost/risk/relapse",
            json=risk_prediction_request
        )
        
        # Check response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error_type" in response.json()
        assert response.json()["error_type"] == "ModelNotFoundError"


class TestTreatmentResponseEndpoint:
    """Test suite for the treatment response endpoint."""
    
    def test_predict_treatment_response_success(
        self,
        client,
        mock_xgboost_service,
        treatment_response_request,
        treatment_response_response
    ):
        """Test successful treatment response prediction."""
        # Mock the service method
        mock_xgboost_service.predict_treatment_response.return_value = treatment_response_response
        
        # Make the request
        response = client.post(
            f"/api/v1/xgboost/treatment/medication_ssri",
            json=treatment_response_request
        )
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert "prediction_id" in response.json()
        assert "response_probability" in response.json()
        assert "response_level" in response.json()
        assert "confidence" in response.json()
        assert "time_to_response_weeks" in response.json()
        
        # Check that the service was called correctly
        mock_xgboost_service.predict_treatment_response.assert_called_once_with(
            patient_id=treatment_response_request["patient_id"],
            treatment_type="medication_ssri",
            treatment_details=treatment_response_request["treatment_details"],
            clinical_data=treatment_response_request["clinical_data"],
            prediction_horizon=treatment_response_request["prediction_horizon"]
        )
    
    def test_predict_treatment_response_validation_error(
        self,
        client,
        mock_xgboost_service,
        treatment_response_request
    ):
        """Test treatment response prediction with validation error."""
        # Mock the service method to raise an error
        mock_xgboost_service.predict_treatment_response.side_effect = ValidationError(
            "Invalid treatment details",
            field="treatment_details"
        )
        
        # Make the request
        response = client.post(
            f"/api/v1/xgboost/treatment/medication_ssri",
            json=treatment_response_request
        )
        
        # Check response
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error_type" in response.json()
        assert response.json()["error_type"] == "ValidationError"


class TestOutcomePredictionEndpoint:
    """Test suite for the outcome prediction endpoint."""
    
    def test_predict_outcome_success(
        self,
        client,
        mock_xgboost_service,
        outcome_prediction_request,
        outcome_prediction_response
    ):
        """Test successful outcome prediction."""
        # Mock the service method
        mock_xgboost_service.predict_outcome.return_value = outcome_prediction_response
        
        # Make the request
        response = client.post(
            f"/api/v1/xgboost/outcome/symptom",
            json=outcome_prediction_request
        )
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert "prediction_id" in response.json()
        assert "outcome_score" in response.json()
        assert "outcome_category" in response.json()
        assert "confidence" in response.json()
        assert "projected_changes" in response.json()
        
        # Check that the service was called correctly
        mock_xgboost_service.predict_outcome.assert_called_once_with(
            patient_id=outcome_prediction_request["patient_id"],
            outcome_timeframe=outcome_prediction_request["outcome_timeframe"],
            clinical_data=outcome_prediction_request["clinical_data"],
            treatment_plan=outcome_prediction_request["treatment_plan"],
            outcome_type="symptom"
        )
    
    def test_predict_outcome_validation_error(
        self,
        client,
        mock_xgboost_service,
        outcome_prediction_request
    ):
        """Test outcome prediction with validation error."""
        # Mock the service method to raise an error
        mock_xgboost_service.predict_outcome.side_effect = ValidationError(
            "Invalid outcome timeframe",
            field="outcome_timeframe"
        )
        
        # Make the request
        response = client.post(
            f"/api/v1/xgboost/outcome/symptom",
            json=outcome_prediction_request
        )
        
        # Check response
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error_type" in response.json()
        assert response.json()["error_type"] == "ValidationError"


class TestFeatureImportanceEndpoint:
    """Test suite for the feature importance endpoint."""
    
    def test_get_feature_importance_success(
        self,
        client,
        mock_xgboost_service,
        feature_importance_request,
        feature_importance_response
    ):
        """Test successful feature importance retrieval."""
        # Mock the service method
        mock_xgboost_service.get_feature_importance.return_value = feature_importance_response
        
        # Make the request
        response = client.post(
            f"/api/v1/xgboost/feature-importance",
            json=feature_importance_request
        )
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert "features" in response.json()
        assert len(response.json()["features"]) > 0
        
        # Check that the service was called correctly
        mock_xgboost_service.get_feature_importance.assert_called_once_with(
            patient_id=feature_importance_request["patient_id"],
            model_type=feature_importance_request["model_type"],
            prediction_id=feature_importance_request["prediction_id"]
        )
    
    def test_get_feature_importance_not_found(
        self,
        client,
        mock_xgboost_service,
        feature_importance_request
    ):
        """Test feature importance retrieval with resource not found error."""
        # Mock the service method to raise an error
        mock_xgboost_service.get_feature_importance.side_effect = ResourceNotFoundError(
            "Prediction not found: risk-123456-P12345",
            resource_type="prediction",
            resource_id="risk-123456-P12345"
        )
        
        # Make the request
        response = client.post(
            f"/api/v1/xgboost/feature-importance",
            json=feature_importance_request
        )
        
        # Check response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error_type" in response.json()
        assert response.json()["error_type"] == "ResourceNotFoundError"


class TestDigitalTwinIntegrationEndpoint:
    """Test suite for the digital twin integration endpoint."""
    
    def test_integrate_with_digital_twin_success(
        self,
        client,
        mock_xgboost_service,
        digital_twin_integration_request,
        digital_twin_integration_response
    ):
        """Test successful digital twin integration."""
        # Mock the service method
        mock_xgboost_service.integrate_with_digital_twin.return_value = digital_twin_integration_response
        
        # Make the request
        response = client.post(
            f"/api/v1/xgboost/digital-twin/integrate",
            json=digital_twin_integration_request
        )
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert "integration_id" in response.json()
        assert "status" in response.json()
        assert "details" in response.json()
        
        # Check that the service was called correctly
        mock_xgboost_service.integrate_with_digital_twin.assert_called_once_with(
            patient_id=digital_twin_integration_request["patient_id"],
            profile_id=digital_twin_integration_request["profile_id"],
            prediction_id=digital_twin_integration_request["prediction_id"]
        )
    
    def test_integrate_with_digital_twin_not_found(
        self,
        client,
        mock_xgboost_service,
        digital_twin_integration_request
    ):
        """Test digital twin integration with resource not found error."""
        # Mock the service method to raise an error
        mock_xgboost_service.integrate_with_digital_twin.side_effect = ResourceNotFoundError(
            "Profile not found: DP67890",
            resource_type="profile",
            resource_id="DP67890"
        )
        
        # Make the request
        response = client.post(
            f"/api/v1/xgboost/digital-twin/integrate",
            json=digital_twin_integration_request
        )
        
        # Check response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error_type" in response.json()
        assert response.json()["error_type"] == "ResourceNotFoundError"


class TestModelInfoEndpoint:
    """Test suite for the model info endpoint."""
    
    def test_get_model_info_success(
        self,
        client,
        mock_xgboost_service,
        model_info_response
    ):
        """Test successful model info retrieval."""
        # Mock the service method
        mock_xgboost_service.get_model_info.return_value = model_info_response
        
        # Make the request
        response = client.get(f"/api/v1/xgboost/models/relapse-risk")
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert "model_type" in response.json()
        assert "version" in response.json()
        assert "features" in response.json()
        assert "performance_metrics" in response.json()
        assert "hyperparameters" in response.json()
        assert "status" in response.json()
        
        # Check that the service was called correctly
        mock_xgboost_service.get_model_info.assert_called_once_with("relapse_risk")
    
    def test_get_model_info_not_found(
        self,
        client,
        mock_xgboost_service
    ):
        """Test model info retrieval with model not found error."""
        # Mock the service method to raise an error
        mock_xgboost_service.get_model_info.side_effect = ModelNotFoundError(
            "Model not found: unknown_model",
            model_type="unknown_model"
        )
        
        # Make the request
        response = client.get(f"/api/v1/xgboost/models/unknown_model")
        
        # Check response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error_type" in response.json()
        assert response.json()["error_type"] == "ModelNotFoundError"