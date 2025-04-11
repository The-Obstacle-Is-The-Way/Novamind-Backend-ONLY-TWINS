"""
Unit tests for the MockXGBoostService implementation.

This module provides comprehensive tests for the mock implementation of the
XGBoost service, ensuring it meets the interface requirements and handles
edge cases appropriately.
"""

import pytest
from unittest.mock import MagicMock

, from app.core.services.ml.xgboost.mock import MockXGBoostService
from app.core.services.ml.xgboost.exceptions import (
    ValidationError,   DataPrivacyError,   ResourceNotFoundError,  
    ModelNotFoundError
)


@pytest.mark.venv_only()
class TestMockXGBoostService:
    """Test case for the MockXGBoostService class."""
    
    @pytest.fixture
    def service(self):
        """Fixture that provides an initialized MockXGBoostService."""
        service = MockXGBoostService()
        service.initialize({
            "data_privacy_level": 2,
            "confidence_threshold": 0.7
        })
        return service
    
    @pytest.fixture
    def sample_patient_id(self):
        """Fixture that provides a sample patient ID."""
        return "patient-123"
    
    @pytest.fixture
    def sample_clinical_data(self):
        """Fixture that provides sample clinical data."""
        return {
            "severity": "moderate",
            "assessment_scores": {
                "phq9": 15,
                "gad7": 12
            }
        }
    
    @pytest.fixture
    def observer(self):
        """Fixture that provides a mock observer."""
        observer = MagicMock()
        observer.notify_prediction = MagicMock()
        return observer
    
    def test_initialization(self):
        """Test initialization of the service."""
        service = MockXGBoostService()
        config = {
            "data_privacy_level": 3,
            "confidence_threshold": 0.8
        }
        
        service.initialize(config)
        
        assert service.config  ==  config
        assert service.phi_detector is not None
        assert service.phi_detector.privacy_level  ==  3
    
    def test_predict_risk_with_valid_data(self, service, sample_patient_id, sample_clinical_data):
        """Test risk prediction with valid data."""
        result = service.predict_risk(
            patient_id=sample_patient_id,
            risk_type="relapse",
            clinical_data=sample_clinical_data
        )
        
        assert result is not None
        assert "prediction_id" in result
        assert result["patient_id"] == sample_patient_id
        assert result["risk_type"] == "relapse"
        assert "risk_level" in result
        assert "risk_score" in result
        assert "confidence" in result
        assert "meets_threshold" in result
        assert "factors" in result
    
    def test_predict_risk_with_phi_detection(self, service, sample_patient_id):
        """Test risk prediction with PHI detection."""
        clinical_data = {
            "severity": "moderate",
            "patient_notes": "Patient John Doe (DOB: 01/15/1980) reports symptoms...",
            "assessment_scores": {
                "phq9": 15
            }
        }
        
        with pytest.raises(DataPrivacyError):
            service.predict_risk(
                patient_id=sample_patient_id,
                risk_type="relapse",
                clinical_data=clinical_data
            )
    
    def test_predict_risk_with_invalid_data(self, service):
        """Test risk prediction with invalid data."""
        with pytest.raises(ValidationError):
            service.predict_risk(
                patient_id="",  # Empty patient ID
                risk_type="relapse",
                clinical_data={}
            )
        
        with pytest.raises(ValidationError):
            service.predict_risk(
                patient_id="patient-123",
                risk_type="",  # Empty risk type
                clinical_data={}
            )
            
        with pytest.raises(ValidationError):
            service.predict_risk(
                patient_id="patient-123",
                risk_type="relapse",
                clinical_data=None  # Missing clinical data
            )
    
    def test_predict_treatment_response(self, service, sample_patient_id, sample_clinical_data):
        """Test treatment response prediction."""
        treatment_details = {
            "medication": "fluoxetine",
            "dosage": "20mg"
        }
        
        result = service.predict_treatment_response(
            patient_id=sample_patient_id,
            treatment_type="ssri",
            treatment_details=treatment_details,
            clinical_data=sample_clinical_data,
            genetic_data=["CYP2D6*1/*1"],
            treatment_history=[
                {
                    "type": "ssri",
                    "name": "sertraline",
                    "response": "partial"
                }
            ]
        )
        
        assert result is not None
        assert "prediction_id" in result
        assert result["patient_id"] == sample_patient_id
        assert result["treatment_type"] == "ssri"
        assert "response_probability" in result
        assert "estimated_efficacy" in result
        assert "time_to_response" in result
        assert "alternative_treatments" in result
    
    def test_predict_outcome(self, service, sample_patient_id, sample_clinical_data):
        """Test outcome prediction."""
        outcome_timeframe = {"weeks": 12}
        treatment_plan = {
            "interventions": ["medication", "therapy"],
            "frequency": "weekly"
        }
        
        result = service.predict_outcome(
            patient_id=sample_patient_id,
            outcome_timeframe=outcome_timeframe,
            clinical_data=sample_clinical_data,
            treatment_plan=treatment_plan,
            social_determinants={"support_level": "medium"},
            comorbidities=["anxiety"]
        )
        
        assert result is not None
        assert "prediction_id" in result
        assert result["patient_id"] == sample_patient_id
        assert "timeframe_weeks" in result
        assert result["timeframe_weeks"] == 12
        assert "success_probability" in result
        assert "predicted_outcomes" in result
        assert "key_factors" in result
    
    def test_get_feature_importance(self, service, sample_patient_id):
        """Test feature importance retrieval."""
        # First make a prediction to get a prediction ID
        prediction = service.predict_risk(
            patient_id=sample_patient_id,
            risk_type="relapse",
            clinical_data={"severity": "moderate"}
        )
        
        prediction_id = prediction["prediction_id"]
        
        result = service.get_feature_importance(
            patient_id=sample_patient_id,
            model_type="risk",
            prediction_id=prediction_id
        )
        
        assert result is not None
        assert "prediction_id" in result
        assert result["prediction_id"] == prediction_id
        assert result["patient_id"] == sample_patient_id
        assert "features" in result
        assert "global_importance" in result
        assert "local_importance" in result
    
    def test_get_feature_importance_not_found(self, service, sample_patient_id):
        """Test feature importance with non-existent prediction ID."""
        with pytest.raises(ResourceNotFoundError):
            service.get_feature_importance(
                patient_id=sample_patient_id,
                model_type="risk",
                prediction_id="non-existent-id"
            )
    
    def test_integrate_with_digital_twin(self, service, sample_patient_id):
        """Test digital twin integration."""
        # First make a prediction to get a prediction ID
        prediction = service.predict_risk(
            patient_id=sample_patient_id,
            risk_type="relapse",
            clinical_data={"severity": "moderate"}
        )
        
        prediction_id = prediction["prediction_id"]
        
        result = service.integrate_with_digital_twin(
            patient_id=sample_patient_id,
            profile_id="profile-456",
            prediction_id=prediction_id
        )
        
        assert result is not None
        assert "integration_id" in result
        assert result["patient_id"] == sample_patient_id
        assert result["profile_id"] == "profile-456"
        assert result["prediction_id"] == prediction_id
        assert "digital_twin_updates" in result
    
    def test_get_model_info(self, service):
        """Test model info retrieval."""
        result = service.get_model_info(model_type="risk_relapse")
        
        assert result is not None
        assert "version" in result
        assert "last_updated" in result
        assert "description" in result
        assert "features" in result
        assert "performance_metrics" in result
    
    def test_get_model_info_not_found(self, service):
        """Test model info with non-existent model type."""
        with pytest.raises(ModelNotFoundError):
            service.get_model_info(model_type="non_existent_model")
    
    def test_observer_pattern(self, service, sample_patient_id, observer):
        """Test observer registration and notification."""
        # Register observer
        observer_id = service.register_prediction_observer(observer)
        
        assert observer_id is not None
        assert observer_id in service.observers
        
        # Make a prediction to trigger notification
        service.predict_risk(
            patient_id=sample_patient_id,
            risk_type="relapse",
            clinical_data={"severity": "moderate"}
        )
        
        # Verify notification was sent
        observer.notify_prediction.assert _called_once()
        
        # Unregister observer
        result = service.unregister_prediction_observer(observer_id)
        
        assert result is True
        assert observer_id not in service.observers
    
    def test_unregister_nonexistent_observer(self, service):
        """Test unregistering a non-existent observer."""
        result = service.unregister_prediction_observer("non-existent-id")
        
        assert result is False
    
    def test_phi_detection(self, service):
        """Test the PHI detection functionality."""
        phi_detector = service.phi_detector
        
        # Test with non-PHI data
        clean_data = "This is clinical information with no PHI"
        result = phi_detector.scan_for_phi(clean_data)
        
        assert result["has_phi"] is False
        assert len(result["matches"]) == 0
        
        # Test with PHI data
        phi_data = "Patient John Smith (SSN: 123-45-6789) reported symptoms"
        result = phi_detector.scan_for_phi(phi_data)
        
        assert result["has_phi"] is True
        assert len(result["matches"]) > 0
        
        # Test with structured data containing PHI keys
        structured_phi = {
            "patient_name": "John Smith",
            "symptoms": ["fatigue", "insomnia"]
        }
        result = phi_detector.scan_for_phi(structured_phi)
        
        assert result["has_phi"] is True
        assert len(result["matches"]) > 0
    
    def test_prediction_sanitization(self, service):
        """Test sanitization of predictions before notifying observers."""
        phi_detector = service.phi_detector
        
        # Create a prediction with potential PHI
        prediction = {
            "prediction_id": "pred-12345",
            "patient_id": "patient-123",
            "patient_name": "John Smith",  # This should be redacted
            "risk_level": "high",
            "notes": "Patient DOB is 01/01/1980",  # This should be redacted
            "factors": [
                {"name": "factor1", "value": "normal"},
                {"name": "ssn", "value": "123-45-6789"}  # This should be redacted
            ]
        }
        
        sanitized = phi_detector.sanitize_prediction(prediction)
        
        # Check that PHI is redacted
        assert sanitized["patient_id"] == "patient-123"  # Not PHI
        assert sanitized["patient_name"] == "[REDACTED]"  # Redacted
        assert "DOB" not in sanitized["notes"]  # Redacted
        assert "123-45-6789" not in str(sanitized)  # Redacted
        
        # Make sure non-PHI data is preserved
        assert sanitized["prediction_id"] == "pred-12345"
        assert sanitized["risk_level"] == "high"
        assert len(sanitized["factors"]) == 2