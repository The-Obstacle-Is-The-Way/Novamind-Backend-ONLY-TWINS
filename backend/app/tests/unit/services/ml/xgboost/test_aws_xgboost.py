"""
Unit tests for the AWS XGBoost service implementation.

This module contains unit tests for the AWSXGBoostService class,
verifying its functionality and compliance with the XGBoostInterface
while mocking all AWS services to avoid actual API calls.
"""

import pytest
import json
import boto3
import uuid
from typing import Dict, Any
from unittest.mock import MagicMock, patch
from datetime import datetime
from botocore.exceptions import ClientError

from app.core.services.ml.xgboost.aws import AWSXGBoostService # Removed AWSPhiDetector import
from app.core.services.ml.xgboost.exceptions import (
    ValidationError, DataPrivacyError, ResourceNotFoundError,
    ModelNotFoundError, PredictionError, ServiceConnectionError as ServiceUnavailableError, # Correct name, alias for compatibility
    ThrottlingError, ConfigurationError
)


@pytest.fixture
def mock_boto3_client():
    """Create a mock boto3 client for testing."""
    with patch('boto3.client') as mock_client:
        # Create mock clients for each AWS service
        mock_sagemaker = MagicMock()
        mock_s3 = MagicMock()
        mock_comprehend = MagicMock()
        mock_comprehend_medical = MagicMock()
        
        # Configure boto3.client to return our mocks based on service name
        def get_mock_client(service_name, **kwargs):
            if service_name == 'sagemaker-runtime':
                return mock_sagemaker
            elif service_name == 's3':
                return mock_s3
            elif service_name == 'comprehend':
                return mock_comprehend
            elif service_name == 'comprehendmedical':
                return mock_comprehend_medical
            return MagicMock()
            
        mock_client.side_effect = get_mock_client
        
        # Return all mocks so tests can configure them
        yield {
            'client': mock_client,
            'sagemaker': mock_sagemaker,
            's3': mock_s3,
            'comprehend': mock_comprehend,
            'comprehend_medical': mock_comprehend_medical
        }


class TestAWSPhiDetector:
    """Tests for the AWSPhiDetector class."""
    
    def test_initialize(self, mock_boto3_client):
        """Test initializing the PHI detector."""
        detector = AWSPhiDetector(privacy_level=2, region="us-east-1")
        assert detector.privacy_level == 2
        assert detector.region == "us-east-1"
        
    def test_scan_for_phi_with_phi(self, mock_boto3_client):
        """Test scanning text with PHI."""
        # Configure mock response from Comprehend Medical
        mock_boto3_client['comprehend_medical'].detect_phi.return_value = {
            'Entities': [
                {
                    'Type': 'NAME',
                    'BeginOffset': 8,
                    'EndOffset': 18,
                    'Score': 0.95,
                    'Text': 'John Smith'
                }
            ]
        }
        
        detector = AWSPhiDetector(privacy_level=2)
        text = "Patient John Smith has depression"
        result = detector.scan_for_phi(text)
        
        # Verify result
        assert result["has_phi"] is True
        assert len(result["matches"]) == 1
        assert result["matches"][0]["type"] == "NAME"
        
        # Verify AWS client was called correctly
        mock_boto3_client['comprehend_medical'].detect_phi.assert_called_once_with(
            Text=text
        )
        
    def test_scan_for_phi_without_phi(self, mock_boto3_client):
        """Test scanning text without PHI."""
        # Configure mock response from Comprehend Medical
        mock_boto3_client['comprehend_medical'].detect_phi.return_value = {
            'Entities': []
        }
        
        detector = AWSPhiDetector(privacy_level=2)
        text = "The patient has depression and anxiety."
        result = detector.scan_for_phi(text)
        
        # Verify result
        assert result["has_phi"] is False
        assert len(result["matches"]) == 0
        
    def test_scan_for_phi_aws_error(self, mock_boto3_client):
        """Test handling AWS errors during PHI scanning."""
        # Configure mock to raise a ClientError
        mock_boto3_client['comprehend_medical'].detect_phi.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'Service unavailable'}},
            'detect_phi'
        )
        
        detector = AWSPhiDetector(privacy_level=2)
        
        with pytest.raises(ServiceUnavailableError):
            detector.scan_for_phi("Test text")
            
    def test_sanitize_prediction(self, mock_boto3_client):
        """Test sanitizing a prediction with PHI."""
        # Configure mock for PHI detection
        def mock_detect_phi(Text):
            if "John Smith" in Text:
                return {
                    'Entities': [
                        {
                            'Type': 'NAME',
                            'BeginOffset': Text.find("John Smith"),
                            'EndOffset': Text.find("John Smith") + len("John Smith"),
                            'Score': 0.95,
                            'Text': 'John Smith'
                        }
                    ]
                }
            return {'Entities': []}
        
        # Configure mock for redaction
        mock_boto3_client['comprehend_medical'].detect_phi.side_effect = mock_detect_phi
        
        detector = AWSPhiDetector(privacy_level=2)
        prediction = {
            "patient_id": "12345",
            "patient_name": "John Smith",
            "risk_score": 0.75,
            "factors": ["medication_adherence", "sleep_quality"]
        }
        
        sanitized = detector.sanitize_prediction(prediction)
        
        # PHI fields should be redacted
        assert sanitized["patient_name"] != "John Smith"
        assert "[REDACTED]" in sanitized["patient_name"]
        
        # Non-PHI fields should be unchanged
        assert sanitized["risk_score"] == 0.75
        assert sanitized["factors"] == ["medication_adherence", "sleep_quality"]


class TestAWSXGBoostService:
    """Tests for the AWSXGBoostService class."""
    
    @pytest.fixture
    def aws_config(self):
        """Create a configuration dictionary for AWS XGBoost service."""
        return {
            "aws_region": "us-east-1",
            "endpoint_prefix": "xgboost-psychiatric",
            "model_bucket": "novamind-models",
            "data_privacy_level": 2,
            "confidence_threshold": 0.7
        }
    
    @pytest.fixture
    def xgboost_service(self, mock_boto3_client, aws_config):
        """Create an AWSXGBoostService instance for testing."""
        # Configure mock S3 client to return model info
        s3_response = {
            'Body': MagicMock()
        }
        s3_response['Body'].read.return_value = json.dumps({
            "version": "1.0.0",
            "last_updated": "2025-03-01",
            "description": "Test model",
            "features": ["feature1", "feature2"],
            "performance_metrics": {
                "accuracy": 0.85,
                "precision": 0.82
            }
        }).encode('utf-8')
        
        mock_boto3_client['s3'].list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'model-info/risk_relapse.json'}
            ]
        }
        mock_boto3_client['s3'].get_object.return_value = s3_response
        
        # Create service
        service = AWSXGBoostService()
        service.initialize(aws_config)
        
        # Replace the PHI detector with a mock
        service.phi_detector = MagicMock()
        service.phi_detector.scan_for_phi.return_value = {"has_phi": False, "matches": []}
        service.phi_detector.sanitize_prediction.side_effect = lambda x: x
        
        return service
    
    @pytest.fixture
    def test_observer(self):
        """Create a test observer for prediction notifications."""
        class TestObserver:
            def __init__(self):
                self.last_notification = None
                
            def notify_prediction(self, prediction):
                self.last_notification = prediction
        
        return TestObserver()
    
    def test_initialize(self, xgboost_service, aws_config):
        """Test initializing the service with configuration."""
        assert xgboost_service.config["aws_region"] == aws_config["aws_region"]
        assert xgboost_service.config["endpoint_prefix"] == aws_config["endpoint_prefix"]
        assert "risk_relapse" in xgboost_service.endpoints
        
    def test_initialize_missing_region(self, mock_boto3_client):
        """Test initializing without AWS region."""
        service = AWSXGBoostService()
        
        with pytest.raises(ConfigurationError):
            service.initialize({})
            
    def test_initialize_missing_endpoint_prefix(self, mock_boto3_client):
        """Test initializing without endpoint prefix."""
        service = AWSXGBoostService()
        
        with pytest.raises(ConfigurationError):
            service.initialize({"aws_region": "us-east-1"})
    
    def test_predict_risk_missing_patient_id(self, xgboost_service):
        """Test predict_risk with missing patient ID."""
        with pytest.raises(ValidationError):
            xgboost_service.predict_risk(
                patient_id="",
                risk_type="relapse",
                clinical_data={"severity": "moderate"}
            )
            
    def test_predict_risk_unsupported_risk_type(self, xgboost_service):
        """Test predict_risk with unsupported risk type."""
        xgboost_service.endpoints = {}  # Clear endpoints
        
        with pytest.raises(ValidationError):
            xgboost_service.predict_risk(
                patient_id="patient123",
                risk_type="unsupported_type",
                clinical_data={"severity": "moderate"}
            )
    
    def test_predict_risk_phi_detection(self, xgboost_service):
        """Test PHI detection during risk prediction."""
        # Configure PHI detector to detect PHI
        xgboost_service.phi_detector.scan_for_phi.return_value = {
            "has_phi": True, 
            "matches": [{"type": "NAME"}]
        }
        
        with pytest.raises(DataPrivacyError):
            xgboost_service.predict_risk(
                patient_id="patient123",
                risk_type="relapse",
                clinical_data={"notes": "Contains PHI"}
            )
            
    def test_predict_risk_successful(self, xgboost_service, mock_boto3_client):
        """Test successful risk prediction."""
        # Configure SageMaker mock response
        sagemaker_response = {
            'Body': MagicMock()
        }
        sagemaker_response['Body'].read.return_value = json.dumps({
            "risk_level": "moderate",
            "risk_score": 0.65,
            "confidence": 0.8,
            "factors": [
                {"name": "sleep_quality", "weight": 0.7, "direction": "negative"},
                {"name": "medication_adherence", "weight": 0.6, "direction": "negative"}
            ]
        }).encode('utf-8')
        
        mock_boto3_client['sagemaker'].invoke_endpoint.return_value = sagemaker_response
        
        # Make prediction
        result = xgboost_service.predict_risk(
            patient_id="patient123",
            risk_type="relapse",
            clinical_data={
                "severity": "moderate",
                "assessment_scores": {
                    "phq9": 15,
                    "gad7": 12
                }
            }
        )
        
        # Check result
        assert result["patient_id"] == "patient123"
        assert result["risk_type"] == "relapse"
        assert result["risk_level"] == "moderate"
        assert result["risk_score"] == 0.65
        assert result["confidence"] == 0.8
        assert len(result["factors"]) == 2
        
        # Verify SageMaker was called
        mock_boto3_client['sagemaker'].invoke_endpoint.assert_called_once()
        
    def test_predict_risk_sagemaker_error(self, xgboost_service, mock_boto3_client):
        """Test handling SageMaker errors during prediction."""
        # Configure SageMaker to raise an error
        mock_boto3_client['sagemaker'].invoke_endpoint.side_effect = ClientError(
            {'Error': {'Code': 'ModelError', 'Message': 'Model error'}},
            'invoke_endpoint'
        )
        
        with pytest.raises(PredictionError):
            xgboost_service.predict_risk(
                patient_id="patient123",
                risk_type="relapse",
                clinical_data={"severity": "moderate"}
            )
            
    def test_predict_risk_service_unavailable(self, xgboost_service, mock_boto3_client):
        """Test handling service unavailable errors."""
        # Configure SageMaker to raise a service unavailable error
        mock_boto3_client['sagemaker'].invoke_endpoint.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
            'invoke_endpoint'
        )
        
        with pytest.raises(ServiceUnavailableError):
            xgboost_service.predict_risk(
                patient_id="patient123",
                risk_type="relapse",
                clinical_data={"severity": "moderate"}
            )
            
    def test_predict_risk_throttling(self, xgboost_service, mock_boto3_client):
        """Test handling throttling errors."""
        # Configure SageMaker to raise a throttling error
        mock_boto3_client['sagemaker'].invoke_endpoint.side_effect = ClientError(
            {'Error': {'Code': 'ThrottlingException', 'Message': 'Throttled'}},
            'invoke_endpoint'
        )
        
        with pytest.raises(ThrottlingError):
            xgboost_service.predict_risk(
                patient_id="patient123",
                risk_type="relapse",
                clinical_data={"severity": "moderate"}
            )
    
    def test_predict_treatment_response_successful(self, xgboost_service, mock_boto3_client):
        """Test successful treatment response prediction."""
        # Configure SageMaker mock response
        sagemaker_response = {
            'Body': MagicMock()
        }
        sagemaker_response['Body'].read.return_value = json.dumps({
            "response_probability": 0.75,
            "estimated_efficacy": 0.7,
            "time_to_response": {
                "unit": "weeks",
                "value": 4,
                "range": [3, 6]
            },
            "alternative_treatments": [
                {"name": "Alternative treatment", "estimated_efficacy": 0.65}
            ]
        }).encode('utf-8')
        
        mock_boto3_client['sagemaker'].invoke_endpoint.return_value = sagemaker_response
        
        # Make prediction
        result = xgboost_service.predict_treatment_response(
            patient_id="patient123",
            treatment_type="ssri",
            treatment_details={"medication": "fluoxetine"},
            clinical_data={"severity": "moderate"}
        )
        
        # Check result
        assert result["patient_id"] == "patient123"
        assert result["treatment_type"] == "ssri"
        assert result["response_probability"] == 0.75
        assert result["estimated_efficacy"] == 0.7
        assert "time_to_response" in result
        assert "alternative_treatments" in result
        
        # Verify SageMaker was called
        mock_boto3_client['sagemaker'].invoke_endpoint.assert_called_once()
        
    def test_get_model_info(self, xgboost_service):
        """Test getting model information."""
        # Add a model to model_info
        xgboost_service.model_info["test_model"] = {
            "version": "1.0.0",
            "description": "Test model"
        }
        
        result = xgboost_service.get_model_info("test_model")
        
        assert result["version"] == "1.0.0"
        assert result["description"] == "Test model"
        
    def test_get_model_info_not_found(self, xgboost_service):
        """Test getting info for a non-existent model."""
        with pytest.raises(ModelNotFoundError):
            xgboost_service.get_model_info("non_existent_model")
            
    def test_get_feature_importance(self, xgboost_service, mock_boto3_client):
        """Test getting feature importance."""
        # Add a prediction
        prediction_id = "pred-12345678"
        xgboost_service.predictions[prediction_id] = {
            "prediction_id": prediction_id,
            "patient_id": "patient123",
            "risk_type": "relapse"
        }
        
        # Configure SageMaker mock response
        sagemaker_response = {
            'Body': MagicMock()
        }
        sagemaker_response['Body'].read.return_value = json.dumps({
            "features": [
                {"name": "feature1", "value": 0.8, "percentile": 90},
                {"name": "feature2", "value": 0.6, "percentile": 70}
            ],
            "global_importance": {"feature1": 0.6, "feature2": 0.4},
            "local_importance": {"feature1": 0.7, "feature2": 0.3},
            "interactions": [
                {"feature1": "feature1", "feature2": "feature2", "strength": 0.5}
            ]
        }).encode('utf-8')
        
        # Add explanation endpoint
        xgboost_service.endpoints["risk_explanation"] = "xgboost-psychiatric-explanation"
        mock_boto3_client['sagemaker'].invoke_endpoint.return_value = sagemaker_response
        
        # Get feature importance
        result = xgboost_service.get_feature_importance(
            patient_id="patient123",
            model_type="risk",
            prediction_id=prediction_id
        )
        
        # Check result
        assert "features" in result
        assert "global_importance" in result
        assert "local_importance" in result
        assert "interactions" in result
        
        # Verify SageMaker was called
        mock_boto3_client['sagemaker'].invoke_endpoint.assert_called_once()
        
    def test_get_feature_importance_prediction_not_found(self, xgboost_service):
        """Test getting feature importance for non-existent prediction."""
        with pytest.raises(ResourceNotFoundError):
            xgboost_service.get_feature_importance(
                patient_id="patient123",
                model_type="risk",
                prediction_id="non_existent"
            )
            
    def test_get_feature_importance_no_endpoint(self, xgboost_service):
        """Test getting feature importance with no explanation endpoint."""
        # Add a prediction
        prediction_id = "pred-12345678"
        xgboost_service.predictions[prediction_id] = {
            "prediction_id": prediction_id,
            "patient_id": "patient123",
            "risk_type": "relapse"
        }
        
        # Clear endpoints
        xgboost_service.endpoints = {}
        
        with pytest.raises(ServiceUnavailableError):
            xgboost_service.get_feature_importance(
                patient_id="patient123",
                model_type="risk",
                prediction_id=prediction_id
            )
            
    def test_integrate_with_digital_twin(self, xgboost_service, mock_boto3_client):
        """Test integrating prediction with digital twin."""
        # Add a prediction
        prediction_id = "pred-12345678"
        xgboost_service.predictions[prediction_id] = {
            "prediction_id": prediction_id,
            "patient_id": "patient123",
            "risk_type": "relapse"
        }
        
        # Configure SageMaker mock response
        sagemaker_response = {
            'Body': MagicMock()
        }
        sagemaker_response['Body'].read.return_value = json.dumps({
            "status": "success",
            "details": {
                "integration_type": "prediction",
                "digital_twin_updates": ["update1", "update2"]
            }
        }).encode('utf-8')
        
        # Add digital twin endpoint
        xgboost_service.endpoints["digital_twin"] = "xgboost-psychiatric-twin"
        mock_boto3_client['sagemaker'].invoke_endpoint.return_value = sagemaker_response
        
        # Integrate with digital twin
        result = xgboost_service.integrate_with_digital_twin(
            patient_id="patient123",
            profile_id="profile123",
            prediction_id=prediction_id
        )
        
        # Check result
        assert result["patient_id"] == "patient123"
        assert result["profile_id"] == "profile123"
        assert result["prediction_id"] == prediction_id
        assert result["status"] == "success"
        assert "details" in result
        
        # Verify SageMaker was called
        mock_boto3_client['sagemaker'].invoke_endpoint.assert_called_once()
        
    def test_integrate_with_digital_twin_no_endpoint(self, xgboost_service):
        """Test digital twin integration with no endpoint."""
        # Add a prediction
        prediction_id = "pred-12345678"
        xgboost_service.predictions[prediction_id] = {
            "prediction_id": prediction_id,
            "patient_id": "patient123",
            "risk_type": "relapse"
        }
        
        # Clear endpoints
        xgboost_service.endpoints = {}
        
        with pytest.raises(ServiceUnavailableError):
            xgboost_service.integrate_with_digital_twin(
                patient_id="patient123",
                profile_id="profile123",
                prediction_id=prediction_id
            )
            
    def test_observer_notification(self, xgboost_service, mock_boto3_client, test_observer):
        """Test observer notification on prediction."""
        # Register observer
        observer_id = xgboost_service.register_prediction_observer(test_observer)
        
        # Configure SageMaker mock response
        sagemaker_response = {
            'Body': MagicMock()
        }
        sagemaker_response['Body'].read.return_value = json.dumps({
            "risk_level": "moderate",
            "risk_score": 0.65,
            "confidence": 0.8,
            "factors": []
        }).encode('utf-8')
        
        mock_boto3_client['sagemaker'].invoke_endpoint.return_value = sagemaker_response
        
        # Make prediction
        result = xgboost_service.predict_risk(
            patient_id="patient123",
            risk_type="relapse",
            clinical_data={"severity": "moderate"}
        )
        
        # Check that observer was notified
        assert test_observer.last_notification is not None
        assert test_observer.last_notification["prediction_id"] == result["prediction_id"]
        
        # Unregister observer
        assert xgboost_service.unregister_prediction_observer(observer_id) is True
        assert xgboost_service.unregister_prediction_observer("non-existent") is False