"""
Unit tests for the AWS SageMaker implementation of the XGBoost service.

These tests verify that the AWS XGBoost service implementation correctly interacts
with AWS services and handles errors appropriately. All AWS services are mocked:
    to avoid external dependencies.
    """

    import json
    import uuid
    import pytest
    from unittest.mock import patch, MagicMock, ANY
    from datetime import datetime
    from botocore.exceptions import ClientError

    from app.core.services.ml.xgboost.aws import AWSXGBoostService

    # Import Enums from the correct schema location
    from app.api.schemas.xgboost import (
    RiskLevel,
    TreatmentType,
)  # Renamed TreatmentCategory to TreatmentType, removed ValidationStatus

    # Import Exceptions from the service exception module
    from app.core.services.ml.xgboost.exceptions import (
    ModelNotFoundError,
    # PredictionNotFoundError,   # Does not exist in exceptions module
    # InvalidFeatureError,   # Does not exist in exceptions module
    PredictionError,
    ServiceConfigurationError,
    ServiceConnectionError,
)

# ModelType might be defined elsewhere or needs clarification
from app.core.services.ml.xgboost import (
    ModelType,
)  # Assuming ModelType is correctly here for now


@pytest.fixture
def mock_aws_clients():

            """Fixture to mock all AWS clients used by the service."""
    with patch("boto3.client") as mock_client, patch("boto3.resource") as mock_resource:
        # Mock SageMaker clients
        mock_sagemaker = MagicMock(,
        mock_sagemaker_runtime= MagicMock(,
        mock_s3= MagicMock()

        # Mock DynamoDB
        mock_dynamodb = MagicMock(,
        mock_predictions_table= MagicMock()
        mock_dynamodb.Table.return_value = mock_predictions_table
        mock_resource.return_value = mock_dynamodb

        # Set up client return values
        def get_boto_client(service, **kwargs):

                        if service == "sagemaker":
                            return mock_sagemaker
                            elif service == "sagemaker-runtime":
                                return mock_sagemaker_runtime
                                elif service == "s3":
                        return mock_s3
                        return MagicMock()

                        mock_client.side_effect = get_boto_client

                        # Return all mocks
                        yield {
                        "sagemaker": mock_sagemaker,
                        "sagemaker_runtime": mock_sagemaker_runtime,
                        "s3": mock_s3,
                        "dynamodb": mock_dynamodb,
                        "predictions_table": mock_predictions_table,
                }


@pytest.fixture
def aws_xgboost_service(mock_aws_clients):

            """Fixture to create an AWSXGBoostService with mocked AWS clients."""
    # Set up successful validation responses
    mock_aws_clients["predictions_table"].scan.return_value = {"Items": []}
    mock_aws_clients["s3"].head_bucket.return_value = {}
    mock_aws_clients["sagemaker"].list_endpoints.return_value = {
        "Endpoints": []}

    service = AWSXGBoostService(
        region_name="us-east-1",
        endpoint_prefix="xgboost-",
        dynamodb_table="predictions",
        s3_bucket="xgboost-models",
        log_level="INFO",
    )

    return service


@pytest.mark.db_required()
class TestAWSXGBoostServiceInitialization:
    """Tests for AWSXGBoostService initialization."""

    def test_initialization_success(self, mock_aws_clients):


                    """Test successful initialization."""
        # Set up successful validation responses
        mock_aws_clients["predictions_table"].scan.return_value = {"Items": []}
        mock_aws_clients["s3"].head_bucket.return_value = {}
        mock_aws_clients["sagemaker"].list_endpoints.return_value = {
            "Endpoints": []}

        service = AWSXGBoostService(
            region_name="us-east-1",
            endpoint_prefix="xgboost-",
            dynamodb_table="predictions",
            s3_bucket="xgboost-models",
            log_level="INFO",
        )

        assert service.region_name == "us-east-1"
        assert service.endpoint_prefix == "xgboost-"
        assert service.dynamodb_table == "predictions"
        assert service.s3_bucket == "xgboost-models"

        # Verify AWS clients initialization
        mock_aws_clients["dynamodb"].Table.assert_called_once_with(
            "predictions")
        mock_aws_clients["predictions_table"].scan.assert_called_once()
        mock_aws_clients["s3"].head_bucket.assert_called_once_with(
            Bucket="xgboost-models"
        )
        mock_aws_clients["sagemaker"].list_endpoints.assert_called_once()

    def test_initialization_failure_dynamodb(self, mock_aws_clients):


                    """Test initialization failure due to DynamoDB error."""
        mock_aws_clients["predictions_table"].scan.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Table not found",
                }
            },
            "Scan",
        )

        with pytest.raises(ServiceConfigurationError) as exc_info:
            AWSXGBoostService(
                region_name="us-east-1",
                endpoint_prefix="xgboost-",
                dynamodb_table="nonexistent-table",
                s3_bucket="xgboost-models",
                log_level="INFO",
            )

        assert "Resource not found" in str(exc_info.value)

    def test_initialization_failure_s3(self, mock_aws_clients):


                    """Test initialization failure due to S3 error."""
        mock_aws_clients["predictions_table"].scan.return_value = {"Items": []}
        mock_aws_clients["s3"].head_bucket.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}},
            "HeadBucket",
        )

        with pytest.raises(ServiceConfigurationError) as exc_info:
            AWSXGBoostService(
                region_name="us-east-1",
                endpoint_prefix="xgboost-",
                dynamodb_table="predictions",
                s3_bucket="nonexistent-bucket",
                log_level="INFO",
            )

        assert "validation failed" in str(exc_info.value)
class TestPredictRisk:
            """Tests for the predict_risk method."""

            def test_predict_risk_success(self, aws_xgboost_service, mock_aws_clients):


                    """Test successful risk prediction."""
                # Mock endpoint lookup
                aws_xgboost_service.model_cache = {}  # Reset cache
                mock_aws_clients["sagemaker"].describe_endpoint.return_value = {
                "EndpointName": "xgboost-risk_relapse",
                "EndpointStatus": "InService",
        }

        # Mock SageMaker runtime response
        mock_response = {"Body": MagicMock()}
        mock_response["Body"].read.return_value = json.dumps(
            {
                "risk_score": 0.75,
                "confidence": 0.85,
                "features_used": ["age", "phq9_score"],
                "explanation": "High risk based on PHQ-9 score",
                "contributing_factors": [
                    {
                        "name": "phq9_score",
                        "impact": 0.8,
                        "description": "Elevated depression score",
                    }
                ],
                "model_id": "model-123",
            }
        ).encode("utf-8")
        mock_aws_clients[
            "sagemaker_runtime"
        ].invoke_endpoint.return_value = mock_response

        # Mock DynamoDB put_item
        mock_aws_clients["predictions_table"].put_item.return_value = {}

        # Test data
        patient_id = "patient-123"
        risk_type = ModelType.RISK_RELAPSE  # Use ModelType
        features = {"age": 35, "phq9_score": 18, "gender": "female"}
        time_frame_days = 90

        # Call method
        with patch(
            "uuid.uuid4", return_value=uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
        ):
            result = aws_xgboost_service.predict_risk(
                patient_id=patient_id,
                risk_type=risk_type,
                features=features,
                time_frame_days=time_frame_days,
            )

        # Verify result
        assert result.prediction_id == "123e4567-e89b-12d3-a456-426614174000"
        assert result.patient_id == patient_id
        assert result.prediction_type == risk_type
        assert result.risk_level == RiskLevel.HIGH  # Based on risk_score 0.75
        assert result.risk_score == 0.75
        assert result.confidence == 0.85
        assert result.time_frame_days == time_frame_days
        assert len(result.contributing_factors) == 1
        assert result.contributing_factors[0]["name"] == "phq9_score"

        # Verify API calls
        mock_aws_clients["sagemaker"].describe_endpoint.assert_called_with(
            EndpointName="xgboost-risk_relapse"
        )
        mock_aws_clients["sagemaker_runtime"].invoke_endpoint.assert_called_with(
            EndpointName="xgboost-risk_relapse",
            ContentType="application/json",
            Body=ANY,  # Can't easily check the exact serialized body
        )
        mock_aws_clients["predictions_table"].put_item.assert_called_once()

    def test_predict_risk_model_not_found(
            self, aws_xgboost_service, mock_aws_clients):
                """Test risk prediction with non-existent model."""
                # Mock endpoint lookup failure
                aws_xgboost_service.model_cache = {}  # Reset cache
                mock_aws_clients["sagemaker"].describe_endpoint.side_effect = ClientError(
                {"Error": {"Code": "ValidationException", "Message": "Endpoint not found"}},
                "DescribeEndpoint",
        )

        # Test data
        patient_id = "patient-123"
        risk_type = ModelType.RISK_RELAPSE  # Use ModelType
        features = {"age": 35, "phq9_score": 18}

        # Call method and verify exception
        with pytest.raises(ModelNotFoundError) as exc_info:
            aws_xgboost_service.predict_risk(
                patient_id=patient_id, risk_type=risk_type, features=features
            )

        assert "No model available for risk_relapse" in str(exc_info.value)

    def test_predict_risk_invalid_risk_type(self, aws_xgboost_service):


                    """Test risk prediction with invalid risk type."""
        # Test data
        patient_id = "patient-123"
        risk_type = (
            ModelType.TREATMENT_RESPONSE_MEDICATION
        )  # Not a risk type, use ModelType
        features = {"age": 35, "phq9_score": 18}

        # Call method and verify exception
        with pytest.raises(ValidationError) as exc_info:  # Use ValidationError
            aws_xgboost_service.predict_risk(
                patient_id=patient_id, risk_type=risk_type, features=features
            )

        assert "Invalid risk type" in str(exc_info.value)

    def test_predict_risk_invocation_error(
            self, aws_xgboost_service, mock_aws_clients):
                """Test risk prediction with SageMaker invocation error."""
                # Mock endpoint lookup success
                aws_xgboost_service.model_cache = {}  # Reset cache
                mock_aws_clients["sagemaker"].describe_endpoint.return_value = {
                "EndpointName": "xgboost-risk_relapse",
                "EndpointStatus": "InService",
        }

        # Mock SageMaker runtime error
        mock_aws_clients["sagemaker_runtime"].invoke_endpoint.side_effect = ClientError(
            {"Error": {"Code": "ModelError", "Message": "Model error"}},
            "InvokeEndpoint",
        )

        # Test data
        patient_id = "patient-123"
        risk_type = ModelType.RISK_RELAPSE  # Use ModelType
        features = {"age": 35, "phq9_score": 18}

        # Call method and verify exception
        with pytest.raises(ServiceConnectionError) as exc_info:
            aws_xgboost_service.predict_risk(
                patient_id=patient_id, risk_type=risk_type, features=features
            )

        assert "Failed to invoke endpoint" in str(exc_info.value)
class TestGetPrediction:
            """Tests for the get_prediction method."""

            def test_get_prediction_success(
            self,
            aws_xgboost_service,
            mock_aws_clients):
                """Test successfully retrieving a prediction."""
                # Mock DynamoDB response
                mock_aws_clients["predictions_table"].get_item.return_value = {
                "Item": {
                "prediction_id": "pred-123",
                "patient_id": "patient-456",
                "model_id": "model-789",
                "prediction_type": "risk_relapse",
                "timestamp": "2025-03-29T12:00:00Z",
                "confidence": 0.85,
                "features_used": ["age", "phq9_score"],
                "features": {"age": 35, "phq9_score": 18},
                "explanation": "High risk based on PHQ-9 score",
                "validation_status": "pending",
                "risk_level": "high",
                "risk_score": 0.75,
                "time_frame_days": 90,
                "contributing_factors": [{"name": "phq9_score", "impact": 0.8}],
            }
        }

        # Call method
        result = aws_xgboost_service.get_prediction("pred-123")

        # Verify result
        assert result.prediction_id == "pred-123"
        assert result.patient_id == "patient-456"
        assert result.prediction_type == ModelType.RISK_RELAPSE  # Use ModelType
        assert result.risk_level == RiskLevel.HIGH
        assert result.risk_score == 0.75
        assert result.confidence == 0.85

        # Verify API calls
        mock_aws_clients["predictions_table"].get_item.assert_called_with(
            Key={"prediction_id": "pred-123"}
        )

    def test_get_prediction_not_found(
            self, aws_xgboost_service, mock_aws_clients):
                """Test retrieving a non-existent prediction."""
                # Mock DynamoDB response with no item
                mock_aws_clients["predictions_table"].get_item.return_value = {}

                # Call method and verify exception
                with pytest.raises(
                ResourceNotFoundError
        ) as exc_info:  # Use ResourceNotFoundError
                aws_xgboost_service.get_prediction("pred-123")

                assert "Prediction pred-123 not found" in str(exc_info.value)

                def test_get_prediction_dynamodb_error(
                self, aws_xgboost_service, mock_aws_clients):
                    """Test retrieving a prediction with DynamoDB error."""
                    # Mock DynamoDB error
                    mock_aws_clients["predictions_table"].get_item.side_effect = ClientError(
                    {
                    "Error": {
                    "Code": "InternalServerError",
                    "Message": "Internal server error",
                }
            },
            "GetItem",
        )

        # Call method and verify exception
        with pytest.raises(
            ServiceConnectionError
        ) as exc_info:  # Correct exception type
            aws_xgboost_service.get_prediction("pred-123")

        assert "Failed to retrieve prediction" in str(exc_info.value)
class TestValidatePrediction:
            """Tests for the validate_prediction method."""

            def test_validate_prediction_success(
            self, aws_xgboost_service, mock_aws_clients):
                """Test successfully validating a prediction."""
                # Mock get_prediction and update_prediction
                with patch.object(aws_xgboost_service, "_update_prediction") as mock_update:
                    mock_update.return_value = None

                    # Call method
                    result = aws_xgboost_service.validate_prediction(
                    prediction_id="pred-123",
                    status="validated",  # Using string literal temporarily
                    validator_notes="Clinically confirmed",
            )

            # Verify result
            assert result is True

            # Verify update called with correct params
            mock_update.assert_called_once_with(
                "pred-123",
                {
                    "validation_status": "validated",
                    "validator_notes": "Clinically confirmed",
                },
            )

    def test_validate_prediction_not_found(
            self, aws_xgboost_service, mock_aws_clients):
                """Test validating a non-existent prediction."""
                # Mock update_prediction with not found error
                with patch.object(aws_xgboost_service, "_update_prediction") as mock_update:
                    mock_update.side_effect = PredictionNotFoundError(
                    "Prediction pred-123 not found"
            )

            # Call method and verify exception
            with pytest.raises(PredictionNotFoundError) as exc_info:
                aws_xgboost_service.validate_prediction(
                    prediction_id="pred-123", status=ValidationStatus.VALIDATED
                )

            assert "Prediction pred-123 not found" in str(exc_info.value)
class TestHealthcheck:
                """Tests for the healthcheck method."""

                def test_healthcheck_all_healthy(
                self,
                aws_xgboost_service,
                mock_aws_clients):
                    """Test healthcheck with all components healthy."""
                    # Mock component checks
                    mock_aws_clients["predictions_table"].scan.return_value = {"Items": []}
                    mock_aws_clients["s3"].head_bucket.return_value = {}
                    mock_aws_clients["sagemaker"].list_endpoints.return_value = {
                    "Endpoints": [
                    {"EndpointName": "xgboost-risk_relapse", "EndpointStatus": "InService"},
                    {
                    "EndpointName": "xgboost-treatment_response_medication",
                    "EndpointStatus": "InService",
                },
                    ]
        }

        # Call method
        result = aws_xgboost_service.healthcheck()

        # Verify result
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert result["components"]["dynamodb"]["status"] == "healthy"
        assert result["components"]["s3"]["status"] == "healthy"
        assert result["components"]["sagemaker"]["status"] == "healthy"
        assert result["models"]["risk_relapse"] == "active"
        assert result["models"]["treatment_response_medication"] == "active"

    def test_healthcheck_degraded(self, aws_xgboost_service, mock_aws_clients):


                    """Test healthcheck with some components degraded."""
        # Mock component checks
        mock_aws_clients["predictions_table"].scan.return_value = {"Items": []}
        mock_aws_clients["s3"].head_bucket.side_effect = ClientError(
            {
                "Error": {
                    "Code": "SlowDown",
                    "Message": "Please reduce your request rate",
                }
            },
            "HeadBucket",
        )
        mock_aws_clients["sagemaker"].list_endpoints.return_value = {
            "Endpoints": [
                {"EndpointName": "xgboost-risk_relapse", "EndpointStatus": "InService"},
                {
                    "EndpointName": "xgboost-treatment_response_medication",
                    "EndpointStatus": "Updating",
                },
            ]
        }

        # Call method
        result = aws_xgboost_service.healthcheck()

        # Verify result
        assert result["status"] == "degraded"
        assert "timestamp" in result
        assert result["components"]["dynamodb"]["status"] == "healthy"
        assert result["components"]["s3"]["status"] == "unhealthy"
        assert "error" in result["components"]["s3"]
        assert result["components"]["sagemaker"]["status"] == "healthy"
        assert result["models"]["risk_relapse"] == "active"
        assert result["models"]["treatment_response_medication"] == "updating"
