"""
Unit tests for the BedrockPAT service.

These tests verify the functionality of the BedrockPAT implementation
while mocking all external dependencies (AWS services).
"""

import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import boto3
import pytest
from botocore.exceptions import ClientError

from app.core.services.ml.pat.bedrock import BedrockPAT
from app.core.services.ml.pat.exceptions import ()
    AnalysisError,
    AuthorizationError,
    EmbeddingError,
    InitializationError,
    ResourceNotFoundError,
    ValidationError
()

@pytest.fixture
def mock_aws_session():
    """Mock the get_aws_session utility function."""
    with patch("app.core.services.ml.pat.bedrock.get_aws_session") as mock_get_session:
        session = MagicMock()
        mock_get_session.return_value = session

        # Create mock clients
        mock_bedrock = MagicMock()
        mock_s3 = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb_resource = MagicMock()

        # Configure session to return mock clients
        def client_side_effect(service, **kwargs):
            if service == 'bedrock-runtime':
                return mock_bedrock
            elif service == 's3':
                return mock_s3
            elif service == 'dynamodb':
                return mock_dynamodb
            else:
                raise ValueError(f"Unexpected service requested: {service}")
        session.client.side_effect = client_side_effect
        session.resource.return_value = mock_dynamodb_resource

        yield {
            'bedrock': mock_bedrock,
            's3': mock_s3,
            'dynamodb': mock_dynamodb,
            'dynamodb_resource': mock_dynamodb_resource,
            'session': session
        }

@pytest.fixture
def bedrock_pat_service(mock_aws_session):
    """Create a BedrockPAT service instance for testing."""
    service = BedrockPAT()

    # Configure the mock S3 and DynamoDB clients to pass validation
    mock_aws_session['s3'].head_bucket.return_value = {}
    mock_aws_session['dynamodb'].describe_table.return_value = {}

    # Initialize the service
    config = {
        'pat_s3_bucket': 'test-bucket',
        'pat_dynamodb_table': 'test-table',
        'pat_bedrock_model_id': 'test-model-id',
        'pat_kms_key_id': 'test-kms-key-id'
    }
    service.initialize(config)
    return service

@pytest.fixture
def mock_bedrock_response():
    """Create a mock response from Bedrock."""
    mock_response = {
        'body': Mock()
    }
    mock_response['body'].read.return_value = json.dumps({)
        'results': {
            'sleep': {
                'total_sleep_minutes': 420,
                'sleep_stages': {
                    'deep_sleep_minutes': 90,
                    'rem_sleep_minutes': 120,
                    'light_sleep_minutes': 210
                }
            }
        },
        'confidence_scores': {
            'sleep': 0.85
        },
        'embedding': [0.1, 0.2, 0.3, 0.4],
        'model_version': 'test-model-1.0.0',
        'insights_added': [
            {'type': 'sleep', 'description': 'Test insight'}
        ],
        'profile_update_summary': {
            'updated_segments': ['sleep_habits']
        }
(    }).encode('utf-8') # Encode to bytes as Bedrock client expects
    return mock_response


@pytest.mark.db_required() # Assuming db_required is a valid marker
class TestBedrockPAT(unittest.TestCase): # Inherit from unittest.TestCase for assertions
    """Test suite for the BedrockPAT service."""

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, mock_aws_session, bedrock_pat_service, mock_bedrock_response):
        """Inject pytest fixtures into the unittest class."""
        self.mock_aws_session = mock_aws_session
        self.bedrock_pat_service = bedrock_pat_service
        self.mock_bedrock_response = mock_bedrock_response

    def test_initialization(self):
        """Test that the service initializes correctly."""
        # Arrange
        service = BedrockPAT()

        # Configure the mock S3 and DynamoDB clients to pass validation
    self.mock_aws_session['s3'].head_bucket.return_value = {}
    self.mock_aws_session['dynamodb'].describe_table.return_value = {}

        # Act
    config = {
    'pat_s3_bucket': 'test-bucket',
    'pat_dynamodb_table': 'test-table',
    'pat_bedrock_model_id': 'test-model-id',
    'pat_kms_key_id': 'test-kms-key-id'
    }
    service.initialize(config)

        # Assert
    self.assertTrue(service._initialized)
    self.assertEqual(service._s3_bucket, 'test-bucket')
    self.assertEqual(service._dynamodb_table, 'test-table')
    self.assertEqual(service._model_id, 'test-model-id')
    self.assertEqual(service._kms_key_id, 'test-kms-key-id')

    def test_initialization_missing_bucket(self):
        """Test initialization fails when S3 bucket is missing."""
        # Arrange
        service = BedrockPAT()

        # Act & Assert
    with self.assertRaises(InitializationError) as cm:
    service.initialize({)
    'pat_dynamodb_table': 'test-table',
    'pat_bedrock_model_id': 'test-model-id'
(    })
    self.assertIn("S3 bucket name is required", str(cm.exception))

    def test_initialization_missing_table(self):
        """Test initialization fails when DynamoDB table is missing."""
        # Arrange
        service = BedrockPAT()

        # Act & Assert
    with self.assertRaises(InitializationError) as cm:
    service.initialize({)
    'pat_s3_bucket': 'test-bucket',
    'pat_bedrock_model_id': 'test-model-id'
(    })
    self.assertIn("DynamoDB table name is required", str(cm.exception))

    def test_initialization_missing_model_id(self):
        """Test initialization fails when Bedrock model ID is missing."""
        # Arrange
        service = BedrockPAT()

        # Act & Assert
    with self.assertRaises(InitializationError) as cm:
    service.initialize({)
    'pat_s3_bucket': 'test-bucket',
    'pat_dynamodb_table': 'test-table'
(    })
    self.assertIn("Bedrock model ID is required", str(cm.exception))

    def test_initialization_s3_bucket_not_found(self):
        """Test initialization fails when S3 bucket does not exist."""
        # Arrange
        service = BedrockPAT()

        # Configure the mock S3 client to fail validation
    error_response = {'Error': {'Code': '404', 'Message': 'Not Found'}}
    self.mock_aws_session['s3'].head_bucket.side_effect = ClientError(error_response, 'HeadBucket')

        # Act & Assert
    with self.assertRaises(InitializationError) as cm:
    service.initialize({)
    'pat_s3_bucket': 'test-bucket',
    'pat_dynamodb_table': 'test-table',
    'pat_bedrock_model_id': 'test-model-id'
(    })
    self.assertIn("S3 bucket test-bucket not found", str(cm.exception))

    def test_initialization_dynamodb_table_not_found(self):
        """Test initialization fails when DynamoDB table does not exist."""
        # Arrange
        service = BedrockPAT()

        # Configure the mock S3 client to pass validation
    self.mock_aws_session['s3'].head_bucket.return_value = {}

        # Configure the mock DynamoDB client to fail validation
    error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}}
    self.mock_aws_session['dynamodb'].describe_table.side_effect = ClientError(error_response, 'DescribeTable')

        # Act & Assert
    with self.assertRaises(InitializationError) as cm:
    service.initialize({)
    'pat_s3_bucket': 'test-bucket',
    'pat_dynamodb_table': 'test-table',
    'pat_bedrock_model_id': 'test-model-id'
(    })
    self.assertIn("DynamoDB table test-table not found", str(cm.exception))

    def test_analyze_actigraphy_success(self):
        """Test successful actigraphy analysis."""
        # Arrange
        self.mock_aws_session['bedrock'].invoke_model.return_value = self.mock_bedrock_response

        # Configure table mock for DynamoDB
    table_mock = MagicMock()
    self.mock_aws_session['dynamodb_resource'].Table.return_value = table_mock

        # Test data
    patient_id = "test-patient"
    readings = [
    {"timestamp": "2025-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3}
    for _ in range(20)
    ]
    start_time = "2025-01-01T00:00:00Z"
    end_time = "2025-01-01T08:00:00Z"
    sampling_rate_hz = 50.0
    device_info = {
    "device_type": "smartwatch",
    "manufacturer": "Test Manufacturer",
    "model": "Test Model"
    }
    analysis_types = ["sleep"]

        # Act
    result = self.bedrock_pat_service.analyze_actigraphy()
    patient_id=patient_id,
    readings=readings,
    start_time=start_time,
    end_time=end_time,
    sampling_rate_hz=sampling_rate_hz,
    device_info=device_info,
    analysis_types=analysis_types
(    )

        # Assert
    self.assertEqual(result["patient_id"], patient_id)
    self.assertEqual(result["analysis_types"], analysis_types)
    self.assertIn("analysis_id", result)
    self.assertIn("created_at", result)
    self.assertEqual(result["device_info"], device_info)
    self.assertEqual(result["start_time"], start_time)
    self.assertEqual(result["end_time"], end_time)

        # Verify S3 storage was called
    self.mock_aws_session['s3'].put_object.assert_called_once()

        # Verify DynamoDB storage was called
    self.assertEqual(table_mock.put_item.call_count, 2) # One for full analysis, one for summary

        # Verify Bedrock was called with expected parameters
    invoke_model_call = self.mock_aws_session['bedrock'].invoke_model.call_args[1]
    self.assertEqual(invoke_model_call["modelId"], "test-model-id")

        # Parse the body to verify its content
    body = json.loads(invoke_model_call["body"])
    self.assertEqual(body["task"], "Analyze actigraphy data to extract insights, patterns, and health indicators.")

    input_data = json.loads(body["inputText"])
    self.assertEqual(input_data["patient_id"], patient_id)
    self.assertEqual(input_data["analysis_types"], analysis_types)

    def test_analyze_actigraphy_invalid_input(self):
        """Test actigraphy analysis with invalid input."""
        # Act & Assert - Missing patient_id
        with self.assertRaises(ValidationError) as cm:
        self.bedrock_pat_service.analyze_actigraphy()
                patient_id="",
                readings=[{"timestamp": "2025-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3}],
                start_time="2025-01-01T00:00:00Z",
                end_time="2025-01-01T08:00:00Z",
                sampling_rate_hz=50.0,
                device_info={"device_type": "smartwatch"},
                analysis_types=["sleep"]
(            )
        self.assertIn("patient_id is required", str(cm.exception))

        # Act & Assert - Too few readings
    with self.assertRaises(ValidationError) as cm:
    self.bedrock_pat_service.analyze_actigraphy()
    patient_id="test-patient",
    readings=[{"timestamp": "2025-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3}],
    start_time="2025-01-01T00:00:00Z",
    end_time="2025-01-01T08:00:00Z",
    sampling_rate_hz=50.0,
    device_info={"device_type": "smartwatch"},
    analysis_types=["sleep"]
(    )
    self.assertIn("At least 10 readings are required", str(cm.exception))

        # Act & Assert - Missing analysis_types
    with self.assertRaises(ValidationError) as cm:
    self.bedrock_pat_service.analyze_actigraphy()
    patient_id="test-patient",
    readings=[{"timestamp": "2025-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3} for _ in range(20)],
    start_time="2025-01-01T00:00:00Z",
    end_time="2025-01-01T08:00:00Z",
    sampling_rate_hz=50.0,
    device_info={"device_type": "smartwatch"},
    analysis_types=[]
(    )
    self.assertIn("At least one analysis_type is required", str(cm.exception))

    def test_analyze_actigraphy_bedrock_error(self):
        """Test actigraphy analysis when Bedrock returns an error."""
        # Arrange
        self.mock_aws_session['s3'].put_object.return_value = {}
        self.mock_aws_session['bedrock'].invoke_model.side_effect = ClientError()
            {'Error': {'Code': 'ModelError', 'Message': 'Model inference failed'}},
            'InvokeModel'
(        )

        # Test data
    patient_id = "test-patient"
    readings = [
    {"timestamp": "2025-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3}
    for _ in range(20)
    ]

        # Act & Assert
    with self.assertRaises(AnalysisError) as cm:
    self.bedrock_pat_service.analyze_actigraphy()
    patient_id=patient_id,
    readings=readings,
    start_time="2025-01-01T00:00:00Z",
    end_time="2025-01-01T08:00:00Z",
    sampling_rate_hz=50.0,
    device_info={"device_type": "smartwatch"},
    analysis_types=["sleep"]
(    )
    self.assertIn("Model inference error", str(cm.exception))

    def test_get_actigraphy_embeddings_success(self):
        """Test successful actigraphy embeddings generation."""
        # Arrange
        self.mock_aws_session['bedrock'].invoke_model.return_value = self.mock_bedrock_response

        # Configure table mock for DynamoDB
    table_mock = MagicMock()
    self.mock_aws_session['dynamodb_resource'].Table.return_value = table_mock

        # Test data
    patient_id = "test-patient"
    readings = [
    {"timestamp": "2025-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3}
    for _ in range(20)
    ]
    start_time = "2025-01-01T00:00:00Z"
    end_time = "2025-01-01T08:00:00Z"
    sampling_rate_hz = 50.0

        # Act
    result = self.bedrock_pat_service.get_actigraphy_embeddings()
    patient_id=patient_id,
    readings=readings,
    start_time=start_time,
    end_time=end_time,
    sampling_rate_hz=sampling_rate_hz
(    )

        # Assert
    self.assertEqual(result["patient_id"], patient_id)
    self.assertIn("embedding_id", result)
    self.assertIn("created_at", result)
    self.assertEqual(result["start_time"], start_time)
    self.assertEqual(result["end_time"], end_time)
    self.assertEqual(result["embedding"], [0.1, 0.2, 0.3, 0.4])
    self.assertEqual(result["dimensions"], 4)
    self.assertEqual(result["model_version"], "test-model-1.0.0")

        # Verify S3 storage was called
    self.mock_aws_session['s3'].put_object.assert_called_once()

        # Verify DynamoDB storage was called
    table_mock.put_item.assert_called_once()

        # Verify Bedrock was called with expected parameters
    invoke_model_call = self.mock_aws_session['bedrock'].invoke_model.call_args[1]
    self.assertEqual(invoke_model_call["modelId"], "test-model-id")

        # Parse the body to verify its content
    body = json.loads(invoke_model_call["body"])
    self.assertEqual(body["task"], "Generate vector embeddings from the actigraphy data for similarity comparison and pattern recognition.")

    def test_get_analysis_by_id_success(self):
        """Test successful retrieval of analysis by ID."""
        # Arrange
        analysis_id = "test-analysis-id"
        mock_analysis = {
            "analysis_id": analysis_id,
            "patient_id": "test-patient",
            "created_at": "2025-01-01T00:00:00Z",
            "results": {"sleep": {}}
        }

        # Configure table mock for DynamoDB
    table_mock = MagicMock()
    table_mock.get_item.return_value = {"Item": mock_analysis}
    self.mock_aws_session['dynamodb_resource'].Table.return_value = table_mock

        # Act
    result = self.bedrock_pat_service.get_analysis_by_id(analysis_id)

        # Assert
    self.assertEqual(result, mock_analysis)
    table_mock.get_item.assert_called_once_with(Key={"analysis_id": analysis_id})

    def test_get_analysis_by_id_not_found(self):
        """Test retrieval of non-existent analysis."""
        # Arrange
        analysis_id = "non-existent-id"

        # Configure table mock for DynamoDB
    table_mock = MagicMock()
    table_mock.get_item.return_value = {} # Simulate item not found
    self.mock_aws_session['dynamodb_resource'].Table.return_value = table_mock

        # Act & Assert
    with self.assertRaises(ResourceNotFoundError) as cm:
    self.bedrock_pat_service.get_analysis_by_id(analysis_id)
    self.assertIn(f"Analysis with ID {analysis_id} not found", str(cm.exception))

    def test_get_patient_analyses_success(self):
        """Test successful retrieval of patient analyses."""
        # Arrange
        patient_id = "test-patient"
        mock_analyses = [
            {
                "analysis_id": f"test-analysis-{i}",
                "created_at": "2025-01-01T00:00:00Z",
                "analysis_types": ["sleep"]
            }
            for i in range(3)
        ]

        # Configure table mock for DynamoDB
    table_mock = MagicMock()
    table_mock.query.return_value = {"Items": mock_analyses, "Count": 3}
    self.mock_aws_session['dynamodb_resource'].Table.return_value = table_mock

        # Act
    result = self.bedrock_pat_service.get_patient_analyses(patient_id, limit=10, offset=0)

        # Assert
    self.assertEqual(len(result["items"]), 3)
    self.assertEqual(result["total"], 3)
    self.assertEqual(result["limit"], 10)
    self.assertEqual(result["offset"], 0)
    self.assertFalse(result["has_more"])

        # Verify DynamoDB query was called with expected parameters
    query_call = table_mock.query.call_args[1]
    self.assertIn("PK = :pk", query_call["KeyConditionExpression"])
    self.assertEqual(query_call["ExpressionAttributeValues"][":pk"], f"PATIENT#{patient_id}")

    def test_get_model_info(self):
        """Test retrieval of model information."""
        # Act
        result = self.bedrock_pat_service.get_model_info()

        # Assert
    self.assertEqual(result["name"], "BedrockPAT")
    self.assertEqual(result["model_id"], "test-model-id")
    self.assertEqual(result["s3_bucket"], "test-bucket")
    self.assertEqual(result["dynamodb_table"], "test-table")
    self.assertIn("capabilities", result)
    self.assertIn("input_format", result)

    def test_integrate_with_digital_twin_success(self):
        """Test successful integration with digital twin."""
        # Arrange
        patient_id = "test-patient"
        profile_id = "test-profile"
        analysis_id = "test-analysis-id"
        mock_analysis = {
            "analysis_id": analysis_id,
            "patient_id": patient_id,
            "results": {"sleep": {"efficiency": 0.8}, "activity": {"steps": 5000}}
        }

        # Mock get_analysis_by_id
    with patch.object(self.bedrock_pat_service, 'get_analysis_by_id', return_value=mock_analysis):
            # Configure table mock for DynamoDB put_item
    table_mock = MagicMock()
    self.mock_aws_session['dynamodb_resource'].Table.return_value = table_mock

            # Act
    result = self.bedrock_pat_service.integrate_with_digital_twin()
    patient_id=patient_id,
    profile_id=profile_id,
    analysis_id=analysis_id
(    )

            # Assert
    self.assertEqual(result["patient_id"], patient_id)
    self.assertEqual(result["profile_id"], profile_id)
    self.assertEqual(result["integration_status"], "success")
    self.assertIn("timestamp", result)
    self.assertIn("integrated_profile", result)

            # Verify DynamoDB storage was called
    table_mock.put_item.assert_called_once()
            # Optionally, check the item structure put to DynamoDB
            # put_item_call = table_mock.put_item.call_args[1]
            # self.assertEqual(put_item_call['Item']['PK'], f"PROFILE#{profile_id}")

    def test_integrate_with_digital_twin_authorization_error(self):
        """Test integration authorization error when patient IDs don't match."""
        # Arrange
        patient_id = "test-patient"
        profile_id = "test-profile"
        analysis_id = "test-analysis-id"
        mock_analysis = {
            "analysis_id": analysis_id,
            "patient_id": "different-patient", # Analysis belongs to another patient
            "results": {"sleep": {"efficiency": 0.8}}
        }

        # Mock get_analysis_by_id
    with patch.object(self.bedrock_pat_service, 'get_analysis_by_id', return_value=mock_analysis):
            # Act & Assert
    with self.assertRaises(AuthorizationError) as cm:
    self.bedrock_pat_service.integrate_with_digital_twin()
    patient_id=patient_id,
    profile_id=profile_id,
    analysis_id=analysis_id
(    )
    self.assertIn("Analysis does not belong to patient", str(cm.exception))

# Example of how to run these tests with pytest
# if __name__ == "__main__":
    #     pytest.main(["-v", __file__]) # Corrected pytest invocation