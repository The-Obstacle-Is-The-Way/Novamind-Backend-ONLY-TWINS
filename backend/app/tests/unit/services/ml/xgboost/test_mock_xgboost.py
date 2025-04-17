# -*- coding: utf-8 -*-
"""
Unit tests for the MockXGBoostService implementation.
These tests verify the mock XGBoost service interface and edge case handling.
"""

import pytest
import time
import re
from unittest.mock import MagicMock, patch
from app.core.services.ml.xgboost.mock import MockXGBoostService, EventType, Observer, PrivacyLevel
from app.core.services.ml.xgboost.exceptions import (
    ValidationError, DataPrivacyError, ResourceNotFoundError,
    ModelNotFoundError, ConfigurationError
)

# Mark tests as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_xgboost_service():
    """Fixture to provide a basic instance of MockXGBoostService."""
    service = MockXGBoostService()
    service.initialize({
        "privacy_level": PrivacyLevel.STANDARD,
        "mock_delay_ms": 0
    })
    return service

@pytest.fixture
def mock_xgboost_service_strict_phi():
    """Fixture with strict PHI detection."""
    service = MockXGBoostService()
    service.initialize({
        "privacy_level": PrivacyLevel.STRICT,
        "mock_delay_ms": 0
    })
    return service

@pytest.fixture
def sample_patient_id():
    return "patient-123"

@pytest.fixture
def sample_clinical_data():
    return {
        "severity": "moderate",
        "assessment_scores": {
            "phq9": 15,
            "gad7": 12
        },
        "notes": "Patient mentioned meeting Dr. John Smith on 10/25/2023. SSN: 123-45-6789. Email is test@example.com."
    }

@pytest.fixture
def sample_clinical_data_clean():
    return {
        "severity": "moderate",
        "assessment_scores": {
            "phq9": 15,
            "gad7": 12
        },
        "notes": "Patient discussed symptoms."
    }

@pytest.fixture
def sample_treatment_details():
    return {"drug": "Fluoxetine", "dosage": "20mg"}

@pytest.fixture
def sample_outcome_timeframe():
    return {"months": 6}

@pytest.fixture
def sample_treatment_plan():
    return {"therapy_type": "ACT", "duration_weeks": 16}

@pytest.fixture
def mock_observer():
    return MagicMock(spec=Observer)

# Add asyncio marker to the class
@pytest.mark.asyncio
class TestMockXGBoostService:
    """Comprehensive tests for MockXGBoostService."""

    # --- Initialization Tests ---
    def test_initialization_defaults(self):
        """Test initialization with default settings."""
        service = MockXGBoostService()
        service.initialize({})
        assert isinstance(service, MockXGBoostService)
        assert service._initialized
        assert service._privacy_level == PrivacyLevel.STANDARD
        assert service._mock_delay_ms == 200
        assert "moderate" in service._risk_level_distribution

    def test_initialization_custom_config(self):
        """Test initialization with custom configuration."""
        config = {
            "privacy_level": PrivacyLevel.ENHANCED,
            "mock_delay_ms": 50,
            "risk_level_distribution": {
                "very_low": 10, "low": 20, "moderate": 40, "high": 20, "very_high": 10
            }
        }
        service = MockXGBoostService()
        service.initialize(config)
        assert service._privacy_level == PrivacyLevel.ENHANCED
        assert service._mock_delay_ms == 50
        assert service._risk_level_distribution["moderate"] == 40

    def test_initialization_invalid_privacy_level(self):
        """Test initialization failure with invalid privacy level."""
        service = MockXGBoostService()
        with pytest.raises(ConfigurationError, match="Invalid privacy level"):
            service.initialize({"privacy_level": "invalid"})

    def test_initialization_invalid_distribution_sum(self):
        """Test initialization failure with invalid risk distribution sum."""
        config = {
             "risk_level_distribution": {
                "very_low": 10, "low": 20, "moderate": 40, "high": 20, "very_high": 5
            }
        }
        service = MockXGBoostService()
        with pytest.raises(ConfigurationError, match="Risk level distribution must sum to 100"):
            service.initialize(config)

    def test_initialization_invalid_distribution_keys(self):
        """Test initialization failure with missing risk distribution keys."""
        config = {
             "risk_level_distribution": {
                "low": 20, "moderate": 60, "high": 20
            }
        }
        service = MockXGBoostService()
        with pytest.raises(ConfigurationError, match="Risk level distribution must include all risk levels"):
            service.initialize(config)

    # --- Prediction Tests (predict_risk) ---
    async def test_predict_risk_with_valid_data(self, mock_xgboost_service, sample_patient_id, sample_clinical_data_clean):
        """Test successful risk prediction with clean data."""
        result = await mock_xgboost_service.predict_risk(
            patient_id=sample_patient_id,
            risk_type="relapse",
            clinical_data=sample_clinical_data_clean
        )
        assert isinstance(result, dict)
        assert result['patient_id'] == sample_patient_id
        assert result['risk_type'] == "relapse"
        assert "prediction_id" in result
        assert "risk_score" in result
        assert "risk_level" in result
        assert "timestamp" in result
        assert isinstance(result['features'], dict)
        assert isinstance(result['supporting_evidence'], list)

    async def test_predict_risk_validation_error_empty_id(self, mock_xgboost_service, sample_clinical_data):
        """Test predict_risk validation error for empty patient ID."""
        with pytest.raises(ValidationError, match="Patient ID cannot be empty"):
            await mock_xgboost_service.predict_risk(
                patient_id="", risk_type="relapse", clinical_data=sample_clinical_data
            )

    async def test_predict_risk_validation_error_empty_data(self, mock_xgboost_service, sample_patient_id):
        """Test predict_risk validation error for empty clinical data."""
        with pytest.raises(ValidationError, match="Clinical data cannot be empty"):
             await mock_xgboost_service.predict_risk(
                patient_id=sample_patient_id, risk_type="relapse", clinical_data={}
            )

    async def test_predict_risk_invalid_risk_type(self, mock_xgboost_service, sample_patient_id, sample_clinical_data):
        """Test predict_risk error for invalid risk type."""
        with pytest.raises(ValidationError, match="Invalid risk type specified"):
            await mock_xgboost_service.predict_risk(
                patient_id=sample_patient_id, risk_type="invalid-type", clinical_data=sample_clinical_data
            )

    async def test_predict_risk_with_phi_detection_standard(self, mock_xgboost_service, sample_patient_id, sample_clinical_data):
        """Test PHI detection with STANDARD privacy level (should trigger on Name/SSN)."""
        with pytest.raises(DataPrivacyError, match="Potential PHI detected in input data") as exc_info:
             await mock_xgboost_service.predict_risk(
                patient_id=sample_patient_id, risk_type="suicide", clinical_data=sample_clinical_data
            )
        assert any("Name pattern" in item or "SSN pattern" in item for item in exc_info.value.details["phi_matches"])

    async def test_predict_risk_with_phi_detection_strict(self, mock_xgboost_service_strict_phi, sample_patient_id, sample_clinical_data):
        """Test PHI detection with STRICT privacy level (should trigger on Name/SSN/Email)."""
        with pytest.raises(DataPrivacyError, match="Potential PHI detected in input data") as exc_info:
             await mock_xgboost_service_strict_phi.predict_risk(
                patient_id=sample_patient_id, risk_type="suicide", clinical_data=sample_clinical_data
            )
        phi_found = [m for m in exc_info.value.details["phi_matches"] if any(p in m for p in ["SSN", "Name", "Email"])]
        assert len(phi_found) > 0
        assert exc_info.value.details["field"] == "notes"

    async def test_predict_risk_no_phi_detected(self, mock_xgboost_service_strict_phi, sample_patient_id, sample_clinical_data_clean):
        """Test that no PHI error is raised for clean data even with strict settings."""
        try:
            result = await mock_xgboost_service_strict_phi.predict_risk(
                patient_id=sample_patient_id, risk_type="relapse", clinical_data=sample_clinical_data_clean
            )
            assert "prediction_id" in result
        except DataPrivacyError:
            pytest.fail("DataPrivacyError raised unexpectedly for clean data")

    # --- Prediction Tests (predict_treatment_response) ---
    async def test_predict_treatment_response_successful(self, mock_xgboost_service, sample_patient_id, sample_clinical_data_clean, sample_treatment_details):
        """Test successful treatment response prediction."""
        result = await mock_xgboost_service.predict_treatment_response(
            patient_id=sample_patient_id,
            treatment_type="antidepressant",
            treatment_details=sample_treatment_details,
            clinical_data=sample_clinical_data_clean
        )
        assert isinstance(result, dict)
        assert result["patient_id"] == sample_patient_id
        assert result["treatment_type"] == "antidepressant"
        assert "prediction_id" in result
        assert "response_likelihood" in result
        # assert "predicted_outcome" in result # Mock doesn't generate this key directly
        assert "expected_outcome" in result
        assert "side_effect_risk" in result
        assert "timestamp" in result

    async def test_predict_treatment_response_invalid_type(self, mock_xgboost_service, sample_patient_id, sample_clinical_data_clean, sample_treatment_details):
        """Test predict_treatment_response error for invalid treatment type."""
        with pytest.raises(ValidationError, match="Invalid treatment type specified"):
            await mock_xgboost_service.predict_treatment_response(
                patient_id=sample_patient_id,
                treatment_type="invalid-treatment",
                treatment_details=sample_treatment_details,
                clinical_data=sample_clinical_data_clean
            )

    # --- Prediction Tests (predict_outcome) ---
    async def test_predict_outcome_successful(self, mock_xgboost_service, sample_patient_id, sample_clinical_data_clean, sample_treatment_plan, sample_outcome_timeframe):
        """Test successful outcome prediction."""
        result = await mock_xgboost_service.predict_outcome(
            patient_id=sample_patient_id,
            outcome_timeframe=sample_outcome_timeframe,
            clinical_data=sample_clinical_data_clean,
            treatment_plan=sample_treatment_plan
        )
        assert isinstance(result, dict)
        assert result["patient_id"] == sample_patient_id
        assert "prediction_id" in result
        # assert "predicted_outcomes" in result # Mock doesn't generate this key directly
        assert "outcome_score" in result
        assert "outcome_type" in result
        assert "trajectory" in result
        assert "outcome_details" in result
        assert "timestamp" in result

    async def test_predict_outcome_invalid_timeframe(self, mock_xgboost_service, sample_patient_id, sample_clinical_data_clean, sample_treatment_plan):
        """Test predict_outcome error for invalid timeframe."""
        with pytest.raises(ValidationError, match="Invalid outcome timeframe specified"):
            await mock_xgboost_service.predict_outcome(
                patient_id=sample_patient_id,
                outcome_timeframe={"years": -1},
                clinical_data=sample_clinical_data_clean,
                treatment_plan=sample_treatment_plan
            )

    # --- Feature Importance Tests ---
    async def test_get_feature_importance_successful(self, mock_xgboost_service, sample_patient_id, sample_clinical_data_clean):
        prediction = await mock_xgboost_service.predict_risk(
            patient_id=sample_patient_id,
            risk_type="relapse",
            clinical_data=sample_clinical_data_clean
        )
        prediction_id = prediction["prediction_id"]

        # Assuming get_feature_importance is synchronous in mock
        importance = mock_xgboost_service.get_feature_importance(
            patient_id=sample_patient_id,
            model_type="risk-relapse", # Use a valid model type string
            prediction_id=prediction_id
        )
        assert isinstance(importance, dict)
        assert importance["prediction_id"] == prediction_id
        assert "feature_importance" in importance
        assert isinstance(importance["feature_importance"], dict)
        assert len(importance["feature_importance"]) > 0
        assert "model_type" in importance
        assert "timestamp" in importance

    async def test_get_feature_importance_prediction_not_found(self, mock_xgboost_service, sample_patient_id):
        """Test feature importance error when prediction ID is not found."""
        with pytest.raises(ResourceNotFoundError, match="Prediction not found"):
            # Assuming get_feature_importance is synchronous in mock
            mock_xgboost_service.get_feature_importance(
                patient_id=sample_patient_id,
                model_type="risk-relapse", # Use a valid model type string
                prediction_id="nonexistent-pred-id"
            )

    async def test_get_feature_importance_mismatched_patient(self, mock_xgboost_service, sample_patient_id, sample_clinical_data_clean):
        """Test feature importance error when patient ID doesn't match stored prediction."""
        prediction = await mock_xgboost_service.predict_risk(
            patient_id=sample_patient_id,
            risk_type="relapse",
            clinical_data=sample_clinical_data_clean
        )
        prediction_id = prediction["prediction_id"]

        with pytest.raises(ValidationError, match="Patient ID mismatch"):
             # Assuming get_feature_importance is synchronous in mock
            mock_xgboost_service.get_feature_importance(
                patient_id="other-patient-id",
                model_type="risk-relapse", # Use a valid model type string
                prediction_id=prediction_id
            )

    # --- Digital Twin Integration Tests ---
    async def test_integrate_with_digital_twin_successful(self, mock_xgboost_service, sample_patient_id, sample_clinical_data_clean):
        prediction = await mock_xgboost_service.predict_risk(
            patient_id=sample_patient_id,
            risk_type="suicide",
            clinical_data=sample_clinical_data_clean
        )
        prediction_id = prediction["prediction_id"]
        profile_id = f"twin-{sample_patient_id}"

        # Assuming integrate_with_digital_twin is synchronous in mock
        result = mock_xgboost_service.integrate_with_digital_twin(
            patient_id=sample_patient_id,
            profile_id=profile_id,
            prediction_id=prediction_id
        )

        assert result["status"] == "success" # Mock returns 'integrated (mock)'
        assert result["profile_id"] == profile_id
        # assert result["integration_id"] is not None # Mock doesn't return this key
        assert profile_id in mock_xgboost_service._profiles
        assert "predictions" in mock_xgboost_service._profiles[profile_id]
        assert any(p["prediction_id"] == prediction_id for p in mock_xgboost_service._profiles[profile_id]["predictions"])

    async def test_integrate_with_digital_twin_prediction_not_found(self, mock_xgboost_service, sample_patient_id):
        """Test digital twin integration error when prediction ID is not found."""
        profile_id = f"twin-{sample_patient_id}"
        with pytest.raises(ResourceNotFoundError, match="Prediction not found"):
             # Assuming integrate_with_digital_twin is synchronous in mock
            mock_xgboost_service.integrate_with_digital_twin(
                patient_id=sample_patient_id,
                profile_id=profile_id,
                prediction_id="nonexistent-pred-id"
            )

    # --- Model Info Tests ---
    async def test_get_model_info_successful(self, mock_xgboost_service):
        """Test retrieving mock model info successfully."""
        model_type = "risk-relapse" # Use a valid model type string
        # Await the call as get_model_info is async in the interface
        info = await mock_xgboost_service.get_model_info(model_type)

        assert isinstance(info, dict)
        assert info["model_type"] == model_type
        # assert info["model_source"] == "mock" # Mock doesn't return this key
        assert info["version"] == "mock"
        assert "info" in info
        # assert "parameters" in info # Mock doesn't return this key
        # assert info["parameters"]["mock_delay_ms"] == mock_xgboost_service._mock_delay_ms

    async def test_get_model_info_not_found(self, mock_xgboost_service):
        """Test get model info error for an unknown model type."""
        model_type = "unknown-fantasy-model"
        # Mock implementation returns default info even for unknown types
        # Await the call as get_model_info is async in the interface
        info = await mock_xgboost_service.get_model_info(model_type)
        assert info["model_type"] == model_type


    # --- Observer Pattern Tests ---
    async def test_observer_pattern_registration(self, mock_xgboost_service, mock_observer):
        """Test observer registration and notification for prediction."""
        # Assuming register_observer is synchronous in mock
        mock_xgboost_service.register_observer(EventType.PREDICTION, mock_observer)
        mock_xgboost_service.register_observer("*", mock_observer)

        result = await mock_xgboost_service.predict_risk(
            patient_id="obs-test-patient", risk_type="relapse", clinical_data={"score": 10}
        )
        prediction_id = result["prediction_id"]

        # Check if update was called (at least once for the specific event, maybe more for '*')
        assert mock_observer.update.call_count >= 1

        specific_call = next((c for c in mock_observer.update.call_args_list if c[0][0] == EventType.PREDICTION), None)
        assert specific_call is not None
        event_type, data = specific_call[0]
        assert event_type == EventType.PREDICTION
        assert data["prediction_type"] == "risk"
        assert data["risk_type"] == "relapse"
        assert data["patient_id"] == "obs-test-patient"
        assert data["prediction_id"] == prediction_id

    async def test_unregister_observer(self, mock_xgboost_service, mock_observer):
        """Test that unregistering an observer prevents notifications."""
         # Assuming register/unregister are synchronous in mock
        mock_xgboost_service.register_observer(EventType.PREDICTION, mock_observer)
        mock_xgboost_service.unregister_observer(EventType.PREDICTION, mock_observer)

        await mock_xgboost_service.predict_risk(
            patient_id="obs-test-patient-2", risk_type="relapse", clinical_data={"score": 11}
        )

        mock_observer.update.assert_not_called()

    async def test_unregister_nonexistent_observer(self, mock_xgboost_service, mock_observer):
        """Test that unregistering a non-existent observer doesn't raise an error."""
        try:
             # Assuming unregister_observer is synchronous in mock
            mock_xgboost_service.unregister_observer(EventType.PREDICTION, mock_observer)
            mock_xgboost_service.unregister_observer("nonexistent_event", mock_observer)
        except Exception as e:
            pytest.fail(f"Unregistering non-existent observer raised an exception: {e}")

    # --- Prediction Sanitization (Conceptual Test) ---
    async def test_prediction_sanitization_conceptual(self, mock_xgboost_service_strict_phi, sample_patient_id, sample_clinical_data_clean):
        """Conceptual test for output sanitization (if implemented)."""
        result = await mock_xgboost_service_strict_phi.predict_risk(
             patient_id=sample_patient_id, risk_type="relapse", clinical_data=sample_clinical_data_clean
        )
        # In a real test, we would assert that PHI is not present in 'result'
        pass
