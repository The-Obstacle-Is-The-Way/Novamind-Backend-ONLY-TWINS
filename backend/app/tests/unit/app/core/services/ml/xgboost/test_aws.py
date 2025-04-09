"""
Unit tests for the AWS XGBoost service implementation.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
from botocore.exceptions import ClientError

from app.core.services.ml.xgboost.aws import AWSXGBoostService
from app.core.services.ml.xgboost.interface import EventType, PrivacyLevel, Observer
from app.core.services.ml.xgboost.exceptions import (
    ValidationError,
    DataPrivacyError,
    ResourceNotFoundError,
    ModelNotFoundError,
    PredictionError,
    ServiceConnectionError,
    ConfigurationError
)


class TestObserver(Observer):
    """Test implementation of the Observer interface."""
    
    def __init__(self):
        """Initialize the test observer."""
        self.events = []
    
    def update(self, event_type, data):
        """Record events for testing."""
        self.events.append((event_type, data))


@pytest.fixture
def aws_config():
    """Fixture for AWS configuration."""
    return {
        "region_name": "us-east-1",
        "endpoint_prefix": "xgboost",
        "bucket_name": "novamind-ml-models",
        "log_level": "INFO",
        "privacy_level": PrivacyLevel.STANDARD,
        "model_mappings": {
            "risk-relapse": "relapse-risk-model",
            "risk-suicide": "suicide-risk-model",
            "treatment-medication_ssri": "ssri-response-model",
            "feature-importance": "feature-importance-model",
            "digital-twin-integration": "digital-twin-integration-model"
        }
    }


@pytest.fixture
def test_observer():
    """Fixture for test observer."""
    return TestObserver()


@pytest.fixture
def boto_clients():
    """Fixture for mocked boto3 clients."""
    with patch("boto3.client") as mock_boto3_client:
        sagemaker_runtime = MagicMock()
        sagemaker = MagicMock()
        s3 = MagicMock()
        
        # Configure mock boto3.client to return different clients
        def get_client(service_name, **kwargs):
            if service_name == "sagemaker-runtime":
                return sagemaker_runtime
            elif service_name == "sagemaker":
                return sagemaker
            elif service_name == "s3":
                return s3
            else:
                return MagicMock()
        
        mock_boto3_client.side_effect = get_client
        
        yield {
            "sagemaker_runtime": sagemaker_runtime,
            "sagemaker": sagemaker,
            "s3": s3,
            "mock_boto3_client": mock_boto3_client
        }


@pytest.fixture
def aws_service(boto_clients, aws_config):
    """Fixture for AWS XGBoost service."""
    service = AWSXGBoostService()
    service.initialize(aws_config)
    return service


@pytest.fixture
def clinical_data():
    """Fixture for clinical data."""
    return {
        "symptom_severity": 7,
        "medication_adherence": 0.8,
        "previous_episodes": 2,
        "social_support": 5,
        "stress_level": 6
    }


@pytest.fixture
def treatment_details():
    """Fixture for treatment details."""
    return {
        "medication": "Fluoxetine",
        "dosage": "20mg",
        "frequency": "daily",
        "duration_weeks": 8
    }


@pytest.fixture
def treatment_plan():
    """Fixture for treatment plan."""
    return {
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
    }


class TestAWSXGBoostService:
    """Test suite for the AWS XGBoost service implementation."""
    
    def test_initialization(self, aws_config, boto_clients):
        """Test initialization with configuration."""
        service = AWSXGBoostService()
        service.initialize(aws_config)
        
        assert service._initialized is True
        assert service._region_name == aws_config["region_name"]
        assert service._endpoint_prefix == aws_config["endpoint_prefix"]
        assert service._bucket_name == aws_config["bucket_name"]
        assert service._model_mappings == aws_config["model_mappings"]
        assert service._privacy_level == PrivacyLevel.STANDARD
        
        # Check that boto3 clients were created
        calls = [
            call("sagemaker-runtime", region_name=aws_config["region_name"]),
            call("sagemaker", region_name=aws_config["region_name"]),
            call("s3", region_name=aws_config["region_name"])
        ]
        boto_clients["mock_boto3_client"].assert_has_calls(calls, any_order=True)
    
    def test_initialization_missing_parameters(self):
        """Test initialization with missing parameters."""
        service = AWSXGBoostService()
        
        with pytest.raises(ConfigurationError) as exc_info:
            service.initialize({})
        
        assert "Missing required AWS parameter" in str(exc_info.value)
    
    def test_initialization_client_error(self, boto_clients):
        """Test initialization with AWS client error."""
        # Make boto3.client raise ClientError
        error_response = {"Error": {"Code": "AuthFailure", "Message": "Auth failure"}}
        
        boto_clients["mock_boto3_client"].side_effect = ClientError(
            error_response, "CreateClient"
        )
        
        service = AWSXGBoostService()
        
        with pytest.raises(ServiceConnectionError) as exc_info:
            service.initialize({
                "region_name": "us-east-1",
                "endpoint_prefix": "xgboost",
                "bucket_name": "novamind-ml-models"
            })
        
        assert "Failed to connect to AWS services" in str(exc_info.value)
        assert exc_info.value.service == "AWS"
        assert exc_info.value.error_type == "AuthFailure"
    
    def test_observer_registration(self, aws_service, test_observer):
        """Test observer registration and notification."""
        # Register observer
        aws_service.register_observer(EventType.PREDICTION, test_observer)
        
        # Trigger event - we'll need to patch _invoke_endpoint for this
        with patch.object(aws_service, "_invoke_endpoint") as mock_invoke:
            mock_invoke.return_value = {
                "prediction_score": 0.8,
                "confidence": 0.9,
                "prediction_id": "test-id"
            }
            
            aws_service.predict_risk(
                patient_id="P12345",
                risk_type="relapse",
                clinical_data={"symptom_severity": 7}
            )
        
        # Verify observer was notified
        assert len(test_observer.events) == 1
        event_type, data = test_observer.events[0]
        assert event_type == EventType.PREDICTION
        assert data["prediction_type"] == "risk"
        assert data["risk_type"] == "relapse"
        assert data["patient_id"] == "P12345"
        assert "timestamp" in data
    
    def test_observer_unregistration(self, aws_service, test_observer):
        """Test observer unregistration."""
        # Register then unregister observer
        aws_service.register_observer(EventType.PREDICTION, test_observer)
        aws_service.unregister_observer(EventType.PREDICTION, test_observer)
        
        # Trigger event
        with patch.object(aws_service, "_invoke_endpoint") as mock_invoke:
            mock_invoke.return_value = {
                "prediction_score": 0.8,
                "confidence": 0.9,
                "prediction_id": "test-id"
            }
            
            aws_service.predict_risk(
                patient_id="P12345",
                risk_type="relapse",
                clinical_data={"symptom_severity": 7}
            )
        
        # Verify observer was not notified
        assert len(test_observer.events) == 0
    
    def test_predict_risk(self, aws_service, boto_clients, clinical_data):
        """Test risk prediction."""
        # Mock SageMaker endpoint response
        response_body = {
            "prediction_score": 0.7,
            "confidence": 0.85,
            "risk_level": "moderate",
            "factors": ["symptom_severity", "previous_episodes"],
            "prediction_id": "risk-123456-P12345"
        }
        
        mock_response = {
            "Body": MagicMock()
        }
        mock_response["Body"].read.return_value = json.dumps(response_body).encode("utf-8")
        
        boto_clients["sagemaker_runtime"].invoke_endpoint.return_value = mock_response
        
        # Call predict_risk
        result = aws_service.predict_risk(
            patient_id="P12345",
            risk_type="relapse",
            clinical_data=clinical_data,
            time_frame_days=60
        )
        
        # Check result
        assert result == response_body
        
        # Verify SageMaker endpoint was called
        boto_clients["sagemaker_runtime"].invoke_endpoint.assert_called_once()
        
        # Get the call args
        call_args = boto_clients["sagemaker_runtime"].invoke_endpoint.call_args[1]
        assert call_args["EndpointName"] == "xgboost-relapse-risk-model"
        assert call_args["ContentType"] == "application/json"
        
        # Parse the request body
        request_body = json.loads(call_args["Body"])
        assert request_body["patient_id"] == "P12345"
        assert request_body["clinical_data"] == clinical_data
        assert request_body["time_frame_days"] == 60
    
    def test_predict_risk_validation_error(self, aws_service):
        """Test risk prediction with validation error."""
        with pytest.raises(ValidationError):
            aws_service.predict_risk(
                patient_id="",  # Empty patient ID
                risk_type="relapse",
                clinical_data={"symptom_severity": 7}
            )
        
        with pytest.raises(ValidationError):
            aws_service.predict_risk(
                patient_id="P12345",
                risk_type="",  # Empty risk type
                clinical_data={"symptom_severity": 7}
            )
        
        with pytest.raises(ValidationError):
            aws_service.predict_risk(
                patient_id="P12345",
                risk_type="relapse",
                clinical_data={}  # Empty clinical data
            )
    
    def test_predict_risk_phi_detection(self, aws_service):
        """Test risk prediction with PHI detection."""
        with pytest.raises(DataPrivacyError):
            aws_service.predict_risk(
                patient_id="P12345",
                risk_type="relapse",
                clinical_data={
                    "symptom_severity": 7,
                    "ssn": "123-45-6789"  # Contains PHI
                }
            )
    
    def test_predict_risk_model_not_found(self, aws_service):
        """Test risk prediction with model not found."""
        with pytest.raises(ModelNotFoundError):
            aws_service.predict_risk(
                patient_id="P12345",
                risk_type="unknown_model",  # Not in model mappings
                clinical_data={"symptom_severity": 7}
            )
    
    def test_predict_risk_aws_error(self, aws_service, boto_clients):
        """Test risk prediction with AWS error."""
        # Make SageMaker endpoint raise ClientError
        error_response = {"Error": {"Code": "ModelError", "Message": "Model error"}}
        
        boto_clients["sagemaker_runtime"].invoke_endpoint.side_effect = ClientError(
            error_response, "InvokeEndpoint"
        )
        
        with pytest.raises(PredictionError) as exc_info:
            aws_service.predict_risk(
                patient_id="P12345",
                risk_type="relapse",
                clinical_data={"symptom_severity": 7}
            )
        
        assert "Model prediction failed" in str(exc_info.value)
        assert exc_info.value.model_type == "risk-relapse"
    
    def test_predict_treatment_response(self, aws_service, boto_clients, clinical_data, treatment_details):
        """Test treatment response prediction."""
        # Mock SageMaker endpoint response
        response_body = {
            "response_probability": 0.65,
            "confidence": 0.8,
            "response_level": "moderate",
            "time_to_response_weeks": 4,
            "prediction_id": "treatment-123456-P12345"
        }
        
        mock_response = {
            "Body": MagicMock()
        }
        mock_response["Body"].read.return_value = json.dumps(response_body).encode("utf-8")
        
        boto_clients["sagemaker_runtime"].invoke_endpoint.return_value = mock_response
        
        # Call predict_treatment_response
        result = aws_service.predict_treatment_response(
            patient_id="P12345",
            treatment_type="medication_ssri",
            treatment_details=treatment_details,
            clinical_data=clinical_data,
            prediction_horizon="12_weeks"
        )
        
        # Check result
        assert result == response_body
        
        # Verify SageMaker endpoint was called
        boto_clients["sagemaker_runtime"].invoke_endpoint.assert_called_once()
        
        # Get the call args
        call_args = boto_clients["sagemaker_runtime"].invoke_endpoint.call_args[1]
        assert call_args["EndpointName"] == "xgboost-ssri-response-model"
        assert call_args["ContentType"] == "application/json"
        
        # Parse the request body
        request_body = json.loads(call_args["Body"])
        assert request_body["patient_id"] == "P12345"
        assert request_body["clinical_data"] == clinical_data
        assert request_body["treatment_details"] == treatment_details
        assert request_body["prediction_horizon"] == "12_weeks"
    
    def test_predict_outcome(self, aws_service, boto_clients, clinical_data, treatment_plan):
        """Test outcome prediction."""
        # Mock SageMaker endpoint response
        response_body = {
            "outcome_score": 0.75,
            "confidence": 0.85,
            "outcome_category": "Remission",
            "projected_changes": {
                "symptom_reduction": 0.6,
                "functioning_improvement": 0.5
            },
            "prediction_id": "outcome-123456-P12345"
        }
        
        mock_response = {
            "Body": MagicMock()
        }
        mock_response["Body"].read.return_value = json.dumps(response_body).encode("utf-8")
        
        boto_clients["sagemaker_runtime"].invoke_endpoint.return_value = mock_response
        
        # Call predict_outcome
        result = aws_service.predict_outcome(
            patient_id="P12345",
            outcome_timeframe={"weeks": 8, "days": 3},
            clinical_data=clinical_data,
            treatment_plan=treatment_plan,
            outcome_type="symptom"
        )
        
        # Check result
        assert result == response_body
        
        # Verify SageMaker endpoint was called
        boto_clients["sagemaker_runtime"].invoke_endpoint.assert_called_once()
        
        # Get the call args
        call_args = boto_clients["sagemaker_runtime"].invoke_endpoint.call_args[1]
        assert call_args["EndpointName"].startswith("xgboost-outcome-")
        assert call_args["ContentType"] == "application/json"
        
        # Parse the request body
        request_body = json.loads(call_args["Body"])
        assert request_body["patient_id"] == "P12345"
        assert request_body["clinical_data"] == clinical_data
        assert request_body["treatment_plan"] == treatment_plan
        assert request_body["time_frame_days"] == 8 * 7 + 3
        assert request_body["outcome_type"] == "symptom"
    
    def test_get_feature_importance(self, aws_service, boto_clients):
        """Test feature importance retrieval."""
        # Mock SageMaker endpoint response
        response_body = {
            "features": [
                {"name": "symptom_severity", "importance": 0.35},
                {"name": "previous_episodes", "importance": 0.25},
                {"name": "medication_adherence", "importance": 0.2},
                {"name": "social_support", "importance": 0.15},
                {"name": "stress_level", "importance": 0.05}
            ],
            "model_type": "relapse-risk",
            "prediction_id": "risk-123456-P12345",
            "timestamp": datetime.now().isoformat()
        }
        
        mock_response = {
            "Body": MagicMock()
        }
        mock_response["Body"].read.return_value = json.dumps(response_body).encode("utf-8")
        
        boto_clients["sagemaker_runtime"].invoke_endpoint.return_value = mock_response
        
        # Call get_feature_importance
        result = aws_service.get_feature_importance(
            patient_id="P12345",
            model_type="relapse-risk",
            prediction_id="risk-123456-P12345"
        )
        
        # Check result
        assert result == response_body
        
        # Verify SageMaker endpoint was called
        boto_clients["sagemaker_runtime"].invoke_endpoint.assert_called_once()
        
        # Get the call args
        call_args = boto_clients["sagemaker_runtime"].invoke_endpoint.call_args[1]
        assert call_args["EndpointName"] == "xgboost-feature-importance-model"
        assert call_args["ContentType"] == "application/json"
        
        # Parse the request body
        request_body = json.loads(call_args["Body"])
        assert request_body["patient_id"] == "P12345"
        assert request_body["model_type"] == "relapse-risk"
        assert request_body["prediction_id"] == "risk-123456-P12345"
    
    def test_integrate_with_digital_twin(self, aws_service, boto_clients):
        """Test digital twin integration."""
        # Mock SageMaker endpoint response
        response_body = {
            "integration_id": "integration-123456",
            "status": "success",
            "patient_id": "P12345",
            "profile_id": "DP67890",
            "prediction_id": "risk-123456-P12345",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "updated_regions": ["amygdala", "prefrontal_cortex"],
                "confidence": 0.85
            }
        }
        
        mock_response = {
            "Body": MagicMock()
        }
        mock_response["Body"].read.return_value = json.dumps(response_body).encode("utf-8")
        
        boto_clients["sagemaker_runtime"].invoke_endpoint.return_value = mock_response
        
        # Call integrate_with_digital_twin
        result = aws_service.integrate_with_digital_twin(
            patient_id="P12345",
            profile_id="DP67890",
            prediction_id="risk-123456-P12345"
        )
        
        # Check result
        assert result == response_body
        
        # Verify SageMaker endpoint was called
        boto_clients["sagemaker_runtime"].invoke_endpoint.assert_called_once()
        
        # Get the call args
        call_args = boto_clients["sagemaker_runtime"].invoke_endpoint.call_args[1]
        assert call_args["EndpointName"] == "xgboost-digital-twin-integration-model"
        assert call_args["ContentType"] == "application/json"
        
        # Parse the request body
        request_body = json.loads(call_args["Body"])
        assert request_body["patient_id"] == "P12345"
        assert request_body["profile_id"] == "DP67890"
        assert request_body["prediction_id"] == "risk-123456-P12345"
    
    def test_get_model_info(self, aws_service, boto_clients):
        """Test model info retrieval."""
        # Mock SageMaker response
        model_response = {
            "ModelName": "relapse-risk-model",
            "ModelVersion": "1.2.0",
            "CreationTime": datetime.now(),
            "ModelStatus": "InService",
            "ModelDescription": "XGBoost model for relapse risk prediction"
        }
        
        boto_clients["sagemaker"].describe_model.return_value = model_response
        
        # Call get_model_info
        result = aws_service.get_model_info("risk-relapse")
        
        # Check result
        assert result["model_type"] == "risk-relapse"
        assert result["version"] == "1.2.0"
        assert "last_updated" in result
        assert result["description"] == "XGBoost model for relapse risk prediction"
        assert result["status"] == "active"
        assert "features" in result
        assert "performance_metrics" in result
        assert "hyperparameters" in result
        
        # Verify SageMaker was called
        boto_clients["sagemaker"].describe_model.assert_called_once_with(
            ModelName="relapse-risk-model"
        )
    
    def test_get_model_info_not_found(self, aws_service):
        """Test model info retrieval for non-existent model."""
        with pytest.raises(ModelNotFoundError):
            aws_service.get_model_info("non-existent-model")
    
    def test_calculate_timeframe_days(self, aws_service):
        """Test calculation of timeframe days."""
        # Test with all units
        timeframe = {"days": 5, "weeks": 2, "months": 1}
        result = aws_service._calculate_timeframe_days(timeframe)
        assert result == 5 + 2 * 7 + 1 * 30
        
        # Test with only days
        timeframe = {"days": 10}
        result = aws_service._calculate_timeframe_days(timeframe)
        assert result == 10
        
        # Test with only weeks
        timeframe = {"weeks": 4}
        result = aws_service._calculate_timeframe_days(timeframe)
        assert result == 4 * 7
        
        # Test with only months
        timeframe = {"months": 2}
        result = aws_service._calculate_timeframe_days(timeframe)
        assert result == 2 * 30
    
    def test_validate_outcome_params(self, aws_service, clinical_data, treatment_plan):
        """Test validation of outcome parameters."""
        # Valid parameters
        aws_service._validate_outcome_params(
            patient_id="P12345",
            outcome_timeframe={"weeks": 8},
            clinical_data=clinical_data,
            treatment_plan=treatment_plan
        )
        
        # Invalid patient ID
        with pytest.raises(ValidationError):
            aws_service._validate_outcome_params(
                patient_id="",
                outcome_timeframe={"weeks": 8},
                clinical_data=clinical_data,
                treatment_plan=treatment_plan
            )
        
        # Invalid outcome timeframe (empty)
        with pytest.raises(ValidationError):
            aws_service._validate_outcome_params(
                patient_id="P12345",
                outcome_timeframe={},
                clinical_data=clinical_data,
                treatment_plan=treatment_plan
            )
        
        # Invalid outcome timeframe (invalid unit)
        with pytest.raises(ValidationError):
            aws_service._validate_outcome_params(
                patient_id="P12345",
                outcome_timeframe={"years": 1},
                clinical_data=clinical_data,
                treatment_plan=treatment_plan
            )
        
        # Invalid outcome timeframe (invalid value)
        with pytest.raises(ValidationError):
            aws_service._validate_outcome_params(
                patient_id="P12345",
                outcome_timeframe={"weeks": -1},
                clinical_data=clinical_data,
                treatment_plan=treatment_plan
            )
        
        # Invalid clinical data
        with pytest.raises(ValidationError):
            aws_service._validate_outcome_params(
                patient_id="P12345",
                outcome_timeframe={"weeks": 8},
                clinical_data={},
                treatment_plan=treatment_plan
            )
        
        # Invalid treatment plan
        with pytest.raises(ValidationError):
            aws_service._validate_outcome_params(
                patient_id="P12345",
                outcome_timeframe={"weeks": 8},
                clinical_data=clinical_data,
                treatment_plan={}
            )