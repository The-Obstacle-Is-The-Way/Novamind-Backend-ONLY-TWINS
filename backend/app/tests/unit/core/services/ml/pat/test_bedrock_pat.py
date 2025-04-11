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
from app.core.services.ml.pat.exceptions import (
    AnalysisError,
    AuthorizationError,
    EmbeddingError,
    InitializationError,
    ResourceNotFoundError,
    ValidationError,
)


@pytest.fixture
def mock_aws_clients():
    """Create mock AWS clients for testing."""
    with patch("boto3.session.Session") as mock_session:
        # Create mock clients
        mock_bedrock = MagicMock()
        mock_s3 = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb_resource = MagicMock()
        
        # Configure session to return mock clients
        mock_session_instance = mock_session.return_value
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'bedrock-runtime': mock_bedrock,
            's3': mock_s3,
            'dynamodb': mock_dynamodb
        }[service]
        mock_session_instance.resource.return_value = mock_dynamodb_resource
        
        yield {
            'bedrock': mock_bedrock,
            's3': mock_s3,
            'dynamodb': mock_dynamodb,
            'dynamodb_resource': mock_dynamodb_resource,
            'session': mock_session_instance
        }


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
        session.client.side_effect = lambda service, **kwargs: {
            'bedrock-runtime': mock_bedrock,
            's3': mock_s3,
            'dynamodb': mock_dynamodb
        }[service]
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
    mock_response['body'].read.return_value = json.dumps({
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
    })
    return mock_response


@pytest.mark.db_required
class TestBedrockPAT:
    """Test suite for the BedrockPAT service."""
    
    def test_initialization(self, mock_aws_session):
        """Test that the service initializes correctly."""
        # Arrange
        service = BedrockPAT()
        
        # Configure the mock S3 and DynamoDB clients to pass validation
        mock_aws_session['s3'].head_bucket.return_value = {}
        mock_aws_session['dynamodb'].describe_table.return_value = {}
        
        # Act
        config = {
            'pat_s3_bucket': 'test-bucket',
            'pat_dynamodb_table': 'test-table',
            'pat_bedrock_model_id': 'test-model-id',
            'pat_kms_key_id': 'test-kms-key-id'
        }
        service.initialize(config)
        
        # Assert
        assert service._initialized is True
        assert service._s3_bucket == 'test-bucket'
        assert service._dynamodb_table == 'test-table'
        assert service._model_id == 'test-model-id'
        assert service._kms_key_id == 'test-kms-key-id'
    
    def test_initialization_missing_bucket(self, mock_aws_session):
        """Test initialization fails when S3 bucket is missing."""
        # Arrange
        service = BedrockPAT()
        
        # Act & Assert
        with pytest.raises(InitializationError) as excinfo:
            service.initialize({
                'pat_dynamodb_table': 'test-table',
                'pat_bedrock_model_id': 'test-model-id'
            })
        
        assert "S3 bucket name is required" in str(excinfo.value)
    
    def test_initialization_missing_table(self, mock_aws_session):
        """Test initialization fails when DynamoDB table is missing."""
        # Arrange
        service = BedrockPAT()
        
        # Act & Assert
        with pytest.raises(InitializationError) as excinfo:
            service.initialize({
                'pat_s3_bucket': 'test-bucket',
                'pat_bedrock_model_id': 'test-model-id'
            })
        
        assert "DynamoDB table name is required" in str(excinfo.value)
    
    def test_initialization_missing_model_id(self, mock_aws_session):
        """Test initialization fails when Bedrock model ID is missing."""
        # Arrange
        service = BedrockPAT()
        
        # Act & Assert
        with pytest.raises(InitializationError) as excinfo:
            service.initialize({
                'pat_s3_bucket': 'test-bucket',
                'pat_dynamodb_table': 'test-table'
            })
        
        assert "Bedrock model ID is required" in str(excinfo.value)
    
    def test_initialization_s3_bucket_not_found(self, mock_aws_session):
        """Test initialization fails when S3 bucket does not exist."""
        # Arrange
        service = BedrockPAT()
        
        # Configure the mock S3 client to fail validation
        error_response = {'Error': {'Code': '404'}}
        mock_aws_session['s3'].head_bucket.side_effect = ClientError(error_response, 'HeadBucket')
        
        # Act & Assert
        with pytest.raises(InitializationError) as excinfo:
            service.initialize({
                'pat_s3_bucket': 'test-bucket',
                'pat_dynamodb_table': 'test-table',
                'pat_bedrock_model_id': 'test-model-id'
            })
        
        assert "S3 bucket test-bucket not found" in str(excinfo.value)
    
    def test_initialization_dynamodb_table_not_found(self, mock_aws_session):
        """Test initialization fails when DynamoDB table does not exist."""
        # Arrange
        service = BedrockPAT()
        
        # Configure the mock S3 client to pass validation
        mock_aws_session['s3'].head_bucket.return_value = {}
        
        # Configure the mock DynamoDB client to fail validation
        error_response = {'Error': {'Code': 'ResourceNotFoundException'}}
        mock_aws_session['dynamodb'].describe_table.side_effect = ClientError(error_response, 'DescribeTable')
        
        # Act & Assert
        with pytest.raises(InitializationError) as excinfo:
            service.initialize({
                'pat_s3_bucket': 'test-bucket',
                'pat_dynamodb_table': 'test-table',
                'pat_bedrock_model_id': 'test-model-id'
            })
        
        assert "DynamoDB table test-table not found" in str(excinfo.value)
    
    def test_analyze_actigraphy_success(self, bedrock_pat_service, mock_aws_session, mock_bedrock_response):
        """Test successful actigraphy analysis."""
        # Arrange
        mock_aws_session['bedrock'].invoke_model.return_value = mock_bedrock_response
        
        # Configure table mock for DynamoDB
        table_mock = MagicMock()
        mock_aws_session['dynamodb_resource'].Table.return_value = table_mock
        
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
        result = bedrock_pat_service.analyze_actigraphy(
            patient_id=patient_id,
            readings=readings,
            start_time=start_time,
            end_time=end_time,
            sampling_rate_hz=sampling_rate_hz,
            device_info=device_info,
            analysis_types=analysis_types
        )
        
        # Assert
        assert result["patient_id"] == patient_id
        assert result["analysis_types"] == analysis_types
        assert "analysis_id" in result
        assert "created_at" in result
        assert result["device_info"] == device_info
        assert result["start_time"] == start_time
        assert result["end_time"] == end_time
        
        # Verify S3 storage was called
        mock_aws_session['s3'].put_object.assert_called_once()
        
        # Verify DynamoDB storage was called
        assert table_mock.put_item.call_count == 2  # One for full analysis, one for summary
        
        # Verify Bedrock was called with expected parameters
        invoke_model_call = mock_aws_session['bedrock'].invoke_model.call_args[1]
        assert invoke_model_call["modelId"] == "test-model-id"
        
        # Parse the body to verify its content
        body = json.loads(invoke_model_call["body"])
        assert body["task"] == "Analyze actigraphy data to extract insights, patterns, and health indicators."
        
        input_data = json.loads(body["inputText"])
        assert input_data["patient_id"] == patient_id
        assert input_data["analysis_types"] == analysis_types
    
    def test_analyze_actigraphy_invalid_input(self, bedrock_pat_service):
        """Test actigraphy analysis with invalid input."""
        # Act & Assert - Missing patient_id
        with pytest.raises(ValidationError) as excinfo:
            bedrock_pat_service.analyze_actigraphy(
                patient_id="",
                readings=[{"timestamp": "2025-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3}],
                start_time="2025-01-01T00:00:00Z",
                end_time="2025-01-01T08:00:00Z",
                sampling_rate_hz=50.0,
                device_info={"device_type": "smartwatch"},
                analysis_types=["sleep"]
            )
        assert "patient_id is required" in str(excinfo.value)
        
        # Act & Assert - Too few readings
        with pytest.raises(ValidationError) as excinfo:
            bedrock_pat_service.analyze_actigraphy(
                patient_id="test-patient",
                readings=[{"timestamp": "2025-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3}],
                start_time="2025-01-01T00:00:00Z",
                end_time="2025-01-01T08:00:00Z",
                sampling_rate_hz=50.0,
                device_info={"device_type": "smartwatch"},
                analysis_types=["sleep"]
            )
        assert "At least 10 readings are required" in str(excinfo.value)
        
        # Act & Assert - Missing analysis_types
        with pytest.raises(ValidationError) as excinfo:
            bedrock_pat_service.analyze_actigraphy(
                patient_id="test-patient",
                readings=[{"timestamp": "2025-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3} for _ in range(20)],
                start_time="2025-01-01T00:00:00Z",
                end_time="2025-01-01T08:00:00Z",
                sampling_rate_hz=50.0,
                device_info={"device_type": "smartwatch"},
                analysis_types=[]
            )
        assert "At least one analysis_type is required" in str(excinfo.value)
    
    def test_analyze_actigraphy_bedrock_error(self, bedrock_pat_service, mock_aws_session):
        """Test actigraphy analysis when Bedrock returns an error."""
        # Arrange
        mock_aws_session['s3'].put_object.return_value = {}
        mock_aws_session['bedrock'].invoke_model.side_effect = ClientError(
            {'Error': {'Code': 'ModelError', 'Message': 'Model inference failed'}},
            'InvokeModel'
        )
        
        # Test data
        patient_id = "test-patient"
        readings = [
            {"timestamp": "2025-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3}
            for _ in range(20)
        ]
        
        # Act & Assert
        with pytest.raises(AnalysisError) as excinfo:
            bedrock_pat_service.analyze_actigraphy(
                patient_id=patient_id,
                readings=readings,
                start_time="2025-01-01T00:00:00Z",
                end_time="2025-01-01T08:00:00Z",
                sampling_rate_hz=50.0,
                device_info={"device_type": "smartwatch"},
                analysis_types=["sleep"]
            )
        
        assert "Model inference error" in str(excinfo.value)
    
    def test_get_actigraphy_embeddings_success(self, bedrock_pat_service, mock_aws_session, mock_bedrock_response):
        """Test successful actigraphy embeddings generation."""
        # Arrange
        mock_aws_session['bedrock'].invoke_model.return_value = mock_bedrock_response
        
        # Configure table mock for DynamoDB
        table_mock = MagicMock()
        mock_aws_session['dynamodb_resource'].Table.return_value = table_mock
        
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
        result = bedrock_pat_service.get_actigraphy_embeddings(
            patient_id=patient_id,
            readings=readings,
            start_time=start_time,
            end_time=end_time,
            sampling_rate_hz=sampling_rate_hz
        )
        
        # Assert
        assert result["patient_id"] == patient_id
        assert "embedding_id" in result
        assert "created_at" in result
        assert result["start_time"] == start_time
        assert result["end_time"] == end_time
        assert result["embedding"] == [0.1, 0.2, 0.3, 0.4]
        assert result["dimensions"] == 4
        assert result["model_version"] == "test-model-1.0.0"
        
        # Verify S3 storage was called
        mock_aws_session['s3'].put_object.assert_called_once()
        
        # Verify DynamoDB storage was called
        table_mock.put_item.assert_called_once()
        
        # Verify Bedrock was called with expected parameters
        invoke_model_call = mock_aws_session['bedrock'].invoke_model.call_args[1]
        assert invoke_model_call["modelId"] == "test-model-id"
        
        # Parse the body to verify its content
        body = json.loads(invoke_model_call["body"])
        assert body["task"] == "Generate vector embeddings from the actigraphy data for similarity comparison and pattern recognition."
    
    def test_get_analysis_by_id_success(self, bedrock_pat_service, mock_aws_session):
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
        mock_aws_session['dynamodb_resource'].Table.return_value = table_mock
        
        # Act
        result = bedrock_pat_service.get_analysis_by_id(analysis_id)
        
        # Assert
        assert result == mock_analysis
        table_mock.get_item.assert_called_once_with(Key={"analysis_id": analysis_id})
    
    def test_get_analysis_by_id_not_found(self, bedrock_pat_service, mock_aws_session):
        """Test retrieval of non-existent analysis."""
        # Arrange
        analysis_id = "non-existent-id"
        
        # Configure table mock for DynamoDB
        table_mock = MagicMock()
        table_mock.get_item.return_value = {}
        table_mock.query.return_value = {"Items": []}
        mock_aws_session['dynamodb_resource'].Table.return_value = table_mock
        
        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as excinfo:
            bedrock_pat_service.get_analysis_by_id(analysis_id)
        
        assert f"Analysis with ID {analysis_id} not found" in str(excinfo.value)
    
    def test_get_patient_analyses_success(self, bedrock_pat_service, mock_aws_session):
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
        mock_aws_session['dynamodb_resource'].Table.return_value = table_mock
        
        # Act
        result = bedrock_pat_service.get_patient_analyses(patient_id, limit=10, offset=0)
        
        # Assert
        assert len(result["items"]) == 3
        assert result["total"] == 3
        assert result["limit"] == 10
        assert result["offset"] == 0
        assert result["has_more"] is False
        
        # Verify DynamoDB query was called with expected parameters
        query_call = table_mock.query.call_args[1]
        assert "PK = :pk" in query_call["KeyConditionExpression"]
        assert query_call["ExpressionAttributeValues"][":pk"] == f"PATIENT#{patient_id}"
    
    def test_get_model_info(self, bedrock_pat_service):
        """Test retrieval of model information."""
        # Act
        result = bedrock_pat_service.get_model_info()
        
        # Assert
        assert result["name"] == "BedrockPAT"
        assert result["model_id"] == "test-model-id"
        assert result["s3_bucket"] == "test-bucket"
        assert result["dynamodb_table"] == "test-table"
        assert "capabilities" in result
        assert "input_format" in result
    
    def test_integrate_with_digital_twin_success(self, bedrock_pat_service, mock_aws_session, mock_bedrock_response):
        """Test successful integration with digital twin."""
        # Arrange
        patient_id = "test-patient"
        profile_id = "test-profile"
        analysis_id = "test-analysis"
        
        # Mock get_analysis_by_id to return a valid analysis
        with patch.object(
            bedrock_pat_service, 'get_analysis_by_id', return_value={"patient_id": patient_id}
        ):
            # Configure Bedrock response
            mock_aws_session['bedrock'].invoke_model.return_value = mock_bedrock_response
            
            # Configure table mock for DynamoDB
            table_mock = MagicMock()
            mock_aws_session['dynamodb_resource'].Table.return_value = table_mock
            
            # Act
            result = bedrock_pat_service.integrate_with_digital_twin(
                patient_id=patient_id,
                profile_id=profile_id,
                analysis_id=analysis_id
            )
            
            # Assert
            assert result["patient_id"] == patient_id
            assert result["profile_id"] == profile_id
            assert result["analysis_id"] == analysis_id
            assert "integration_id" in result
            assert "created_at" in result
            assert result["status"] == "completed"
            assert "insights_added" in result
            assert "profile_update_summary" in result
            
            # Verify DynamoDB storage was called
            table_mock.put_item.assert_called_once()
            
            # Verify Bedrock was called with expected parameters
            invoke_model_call = mock_aws_session['bedrock'].invoke_model.call_args[1]
            assert invoke_model_call["modelId"] == "test-model-id"
            
            # Parse the body to verify its content
            body = json.loads(invoke_model_call["body"])
            assert body["task"] == "Integrate actigraphy analysis with a digital twin profile to enhance understanding of the patient's physical activity patterns."
    
    def test_integrate_with_digital_twin_authorization_error(self, bedrock_pat_service):
        """Test integration with digital twin when analysis doesn't belong to patient."""
        # Arrange
        patient_id = "test-patient"
        profile_id = "test-profile"
        analysis_id = "test-analysis"
        
        # Mock get_analysis_by_id to return an analysis belonging to a different patient
        with patch.object(
            bedrock_pat_service, 'get_analysis_by_id', return_value={"patient_id": "different-patient"}
        ):
            # Act & Assert
            with pytest.raises(AuthorizationError) as excinfo:
                bedrock_pat_service.integrate_with_digital_twin(
                    patient_id=patient_id,
                    profile_id=profile_id,
                    analysis_id=analysis_id
                )
            
            assert "Analysis does not belong to the patient" in str(excinfo.value)


if __name__ == "__main__":
    pytest.main(["-v", "test_bedrock_pat.py"])