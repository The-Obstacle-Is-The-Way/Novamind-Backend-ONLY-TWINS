# PAT Implementation Guide

This guide provides detailed information on implementing, extending, and maintaining the Pretrained Actigraphy Transformer (PAT) service in the Novamind platform. It is intended for developers who need to work with or extend the PAT functionality.

## Architecture Overview

The PAT service follows a clean, layered architecture with clear separation of concerns:

```
┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
│                   │      │                   │      │                   │
│  API Layer        │─────▶│  Service Layer    │─────▶│  Implementation  │
│  (FastAPI)        │      │  (Interfaces)     │      │  Layer            │
│                   │◀────│                   │◀─────│                  │
└───────────────────┘      └───────────────────┘      └───────────────────┘
                                    │                          │
                                    ▼                          ▼
                           ┌───────────────────┐      ┌───────────────────┐
                           │                   │      │                   │
                           │  Factory Layer    │      │  Storage Layer    │
                           │                   │      │  (S3, DynamoDB)   │
                           │                   │      │                   │
                           └───────────────────┘      └───────────────────┘
```

## Directory Structure

```
app/
├── api/
│   ├── dependencies/
│   │   └── ml.py                    # Dependency injection for PAT service
│   ├── routes/
│   │   └── actigraphy.py            # API endpoints for actigraphy analysis
│   └── schemas/
│       └── actigraphy.py            # Pydantic models for actigraphy data
├── core/
│   ├── config/
│   │   └── settings.py              # Configuration settings
│   ├── services/
│   │   └── ml/
│   │       └── pat/
│   │           ├── __init__.py
│   │           ├── bedrock.py       # AWS Bedrock implementation
│   │           ├── exceptions.py    # PAT-specific exceptions
│   │           ├── factory.py       # Factory for instantiating implementations
│   │           ├── interface.py     # Interface defining PAT contract
│   │           └── mock.py          # Mock implementation for testing
│   └── utils/
│       └── phi_sanitizer.py         # PHI sanitization utilities
tests/
├── integration/
│   ├── api/
│   │   └── endpoints/
│   │       └── test_actigraphy_endpoints.py  # API integration tests
│   └── core/
│       └── services/
│           └── ml/
│               └── pat/
│                   └── test_pat_integration.py  # Service integration tests
└── unit/
    └── core/
        └── services/
            └── ml/
                └── pat/
                    ├── test_bedrock_pat.py  # Unit tests for Bedrock implementation
                    ├── test_factory.py      # Unit tests for factory
                    └── test_mock_pat.py     # Unit tests for mock implementation
```

## Interface Definition

The core of the PAT service is defined by the `PATInterface` in `interface.py`:

```python
class PATInterface(ABC):
    """Interface for Pretrained Actigraphy Transformer (PAT) services."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the PAT service with configuration parameters.
        
        Args:
            config: Dictionary containing configuration parameters
        """
        pass
    
    @abstractmethod
    def analyze_actigraphy(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float,
        device_info: Dict[str, Any],
        analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Analyze actigraphy data and return insights.
        
        Args:
            patient_id: Unique identifier for the patient
            readings: List of accelerometer readings (x, y, z values with timestamps)
            start_time: ISO-8601 formatted start time
            end_time: ISO-8601 formatted end time
            sampling_rate_hz: Sampling rate in Hz
            device_info: Information about the device that collected the data
            analysis_types: List of analysis types to perform
        
        Returns:
            Dictionary containing analysis results
        """
        pass
    
    @abstractmethod
    def get_actigraphy_embeddings(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float
    ) -> Dict[str, Any]:
        """Generate embeddings from actigraphy data.
        
        Args:
            patient_id: Unique identifier for the patient
            readings: List of accelerometer readings (x, y, z values with timestamps)
            start_time: ISO-8601 formatted start time
            end_time: ISO-8601 formatted end time
            sampling_rate_hz: Sampling rate in Hz
        
        Returns:
            Dictionary containing embedding information
        """
        pass
    
    @abstractmethod
    def get_analysis_by_id(self, analysis_id: str) -> Dict[str, Any]:
        """Retrieve an analysis by its ID.
        
        Args:
            analysis_id: Unique identifier for the analysis
        
        Returns:
            Dictionary containing the analysis
        """
        pass
    
    @abstractmethod
    def get_patient_analyses(
        self,
        patient_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Retrieve analyses for a patient.
        
        Args:
            patient_id: Unique identifier for the patient
            limit: Maximum number of analyses to return
            offset: Offset for pagination
        
        Returns:
            Dictionary containing the analyses and pagination information
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the PAT model.
        
        Returns:
            Dictionary containing model information
        """
        pass
    
    @abstractmethod
    def integrate_with_digital_twin(
        self,
        patient_id: str,
        profile_id: str,
        analysis_id: str
    ) -> Dict[str, Any]:
        """Integrate actigraphy analysis with a digital twin profile.
        
        Args:
            patient_id: Unique identifier for the patient
            profile_id: Unique identifier for the digital twin profile
            analysis_id: Unique identifier for the analysis to integrate
        
        Returns:
            Dictionary containing the integration status and updated profile information
        """
        pass
```

## Implementation Guidelines

### Creating a New Implementation

To create a new PAT implementation:

1. Create a new class that implements the `PATInterface`
2. Implement all required methods
3. Add the implementation to the factory

Example:

```python
from typing import Any, Dict, List

from app.core.services.ml.pat.interface import PATInterface


class CustomPAT(PATInterface):
    """Custom implementation of the PAT service."""
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the PAT service.
        
        Args:
            config: Dictionary containing configuration parameters
        """
        self.config = config
        self.model = load_custom_model(config.get("model_path"))
        self.storage = initialize_storage(config.get("storage_path"))
    
    # Implement all other methods from the interface
```

Then add it to the factory:

```python
@staticmethod
def get_pat_service(config: Dict[str, Any]) -> PATInterface:
    """Get a PAT service implementation.
    
    Args:
        config: Configuration dictionary with provider and other settings
        
    Returns:
        PAT service implementation
        
    Raises:
        ValueError: If an unknown provider is specified
    """
    provider = config.get("provider", "mock")
    
    if provider == "mock":
        return MockPAT(config)
    elif provider == "bedrock":
        return BedrockPAT(config)
    elif provider == "custom":  # Add new implementation
        return CustomPAT(config)
    else:
        raise ValueError(f"Unknown PAT provider: {provider}")
```

### Handling Errors

PAT implementations should use domain-specific exceptions defined in `exceptions.py`:

```python
class PATError(Exception):
    """Base exception for PAT-related errors."""
    pass


class InitializationError(PATError):
    """Error during PAT service initialization."""
    pass


class AnalysisError(PATError):
    """Error during actigraphy analysis."""
    pass


class EmbeddingError(PATError):
    """Error generating embeddings."""
    pass


class StorageError(PATError):
    """Error accessing PAT storage."""
    pass


class IntegrationError(PATError):
    """Error during integration with other services."""
    pass
```

Example of proper error handling:

```python
def analyze_actigraphy(
    self,
    patient_id: str,
    readings: List[Dict[str, Any]],
    start_time: str,
    end_time: str,
    sampling_rate_hz: float,
    device_info: Dict[str, Any],
    analysis_types: List[str]
) -> Dict[str, Any]:
    """Analyze actigraphy data and return insights.
    
    Args:
        patient_id: Unique identifier for the patient
        readings: List of accelerometer readings
        start_time: ISO-8601 formatted start time
        end_time: ISO-8601 formatted end time
        sampling_rate_hz: Sampling rate in Hz
        device_info: Information about the device
        analysis_types: List of analysis types to perform
    
    Returns:
        Dictionary containing analysis results
        
    Raises:
        AnalysisError: If analysis fails
    """
    try:
        # Validate input
        if not readings:
            raise ValueError("No readings provided")
        
        # Process data
        processed_data = self._preprocess_readings(readings)
        
        # Run analysis
        results = {}
        for analysis_type in analysis_types:
            try:
                results[analysis_type] = self._run_analysis(processed_data, analysis_type)
            except Exception as e:
                # Log the error but continue with other analyses
                logging.error(f"Error running {analysis_type} analysis: {str(e)}")
                results[analysis_type] = {"status": "error", "message": str(e)}
        
        # Store results
        analysis_id = str(uuid.uuid4())
        self._store_analysis(analysis_id, patient_id, results)
        
        return {
            "analysis_id": analysis_id,
            "patient_id": patient_id,
            "timestamp": datetime.utcnow().isoformat(),
            "device_info": device_info,
            "analysis_period": {
                "start_time": start_time,
                "end_time": end_time
            },
            "sampling_info": {
                "rate_hz": sampling_rate_hz,
                "sample_count": len(readings)
            },
            **results
        }
    except ValueError as e:
        # Re-raise validation errors as AnalysisError
        raise AnalysisError(f"Invalid input: {str(e)}")
    except Exception as e:
        # Catch all other exceptions and provide context
        raise AnalysisError(f"Analysis failed: {str(e)}")
```

## HIPAA Compliance Implementation

### PHI Sanitization

When implementing PAT services, ensure all PHI is properly sanitized:

1. Use the `PHISanitizer` to sanitize any data that might contain PHI
2. Avoid logging PHI or including it in error messages
3. Use pseudonymized identifiers when possible

Example:

```python
from app.core.utils.phi_sanitizer import PHISanitizer

def _sanitize_device_info(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize device info to remove potential PHI.
    
    Args:
        device_info: Device information that might contain PHI
        
    Returns:
        Sanitized device information
    """
    sanitized_info = device_info.copy()
    
    # Remove known PHI fields
    phi_fields = ["patient_name", "patient_ssn", "patient_dob", "patient_address"]
    for field in phi_fields:
        if field in sanitized_info:
            del sanitized_info[field]
    
    # Sanitize free text fields that might contain PHI
    if "notes" in sanitized_info:
        sanitized_info["notes"] = PHISanitizer.sanitize_text(sanitized_info["notes"])
    
    return sanitized_info
```

### Audit Logging

Implement audit logging for all data access:

```python
def get_analysis_by_id(self, analysis_id: str) -> Dict[str, Any]:
    """Retrieve an analysis by its ID.
    
    Args:
        analysis_id: Unique identifier for the analysis
        
    Returns:
        Dictionary containing the analysis
    """
    try:
        # Log access attempt (without PHI)
        audit_logger.info(
            "Analysis access attempt",
            extra={
                "action": "access_analysis",
                "resource_type": "analysis",
                "resource_id": hashlib.sha256(analysis_id.encode()).hexdigest(),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "pending"
            }
        )
        
        # Retrieve analysis
        analysis = self._retrieve_analysis(analysis_id)
        
        # Log successful access
        audit_logger.info(
            "Analysis access successful",
            extra={
                "action": "access_analysis",
                "resource_type": "analysis",
                "resource_id": hashlib.sha256(analysis_id.encode()).hexdigest(),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
        )
        
        return analysis
    except Exception as e:
        # Log failed access
        audit_logger.warning(
            "Analysis access failed",
            extra={
                "action": "access_analysis",
                "resource_type": "analysis",
                "resource_id": hashlib.sha256(analysis_id.encode()).hexdigest(),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failure",
                "error": str(e)
            }
        )
        raise
```

## AWS Bedrock Implementation

The AWS Bedrock implementation uses Amazon's managed ML services for inference:

```python
class BedrockPAT(PATInterface):
    """AWS Bedrock implementation of the PAT service."""
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the AWS Bedrock PAT service.
        
        Args:
            config: Dictionary containing configuration parameters
        """
        self.config = config
        
        # Initialize AWS clients
        self.bedrock_client = boto3.client('bedrock-runtime')
        self.s3_client = boto3.client('s3')
        self.dynamodb_client = boto3.client('dynamodb')
        
        # Extract configuration
        self.bucket_name = config.get("bucket_name")
        self.table_name = config.get("table_name")
        self.model_id = config.get("model_id", "amazon.titan-embed-text-v1")
        
        # Validate required configuration
        if not self.bucket_name or not self.table_name:
            raise InitializationError("Missing required configuration: bucket_name or table_name")
```

### AWS Integration

When implementing AWS services, use the following patterns:

1. Use environment variables for AWS configuration
2. Implement proper error handling and retries
3. Use the AWS SDK's built-in pagination

Example:

```python
def get_patient_analyses(
    self,
    patient_id: str,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """Retrieve analyses for a patient.
    
    Args:
        patient_id: Unique identifier for the patient
        limit: Maximum number of analyses to return
        offset: Offset for pagination
        
    Returns:
        Dictionary containing the analyses and pagination information
    """
    try:
        # Query DynamoDB for analyses by patient_id
        response = self.dynamodb_client.query(
            TableName=self.table_name,
            IndexName="PatientIdIndex",
            KeyConditionExpression="patient_id = :pid",
            ExpressionAttributeValues={
                ":pid": {"S": patient_id}
            },
            Limit=limit,
            ScanIndexForward=False  # Sort by timestamp (descending)
        )
        
        # Process the results
        analyses = []
        for item in response.get("Items", []):
            analyses.append(self._dynamodb_item_to_dict(item))
        
        # Get total count
        count_response = self.dynamodb_client.query(
            TableName=self.table_name,
            IndexName="PatientIdIndex",
            KeyConditionExpression="patient_id = :pid",
            ExpressionAttributeValues={
                ":pid": {"S": patient_id}
            },
            Select="COUNT"
        )
        
        total = count_response.get("Count", 0)
        
        return {
            "analyses": analyses,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise StorageError(f"Failed to retrieve patient analyses: {str(e)}")
```

## Mock Implementation

The mock implementation is used for testing and development. It should:

1. Mimic the behavior of the real implementation
2. Return realistic but synthetic data
3. Store data in-memory or in temporary files

Example:

```python
class MockPAT(PATInterface):
    """Mock implementation of the PAT service for testing."""
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the mock PAT service.
        
        Args:
            config: Dictionary containing configuration parameters
        """
        self.storage_path = config.get("storage_path", tempfile.mkdtemp())
        self.analyses = {}
        self.embeddings = {}
        
        # Ensure storage directory exists
        os.makedirs(self.storage_path, exist_ok=True)
```

## Factory Pattern

The factory pattern is used to instantiate the appropriate PAT implementation:

```python
class PATFactory:
    """Factory for creating PAT service instances."""
    
    _instance_cache = {}
    
    @classmethod
    def get_pat_service(cls, config: Dict[str, Any]) -> PATInterface:
        """Get a PAT service implementation.
        
        Args:
            config: Configuration dictionary with provider and other settings
            
        Returns:
            PAT service implementation
            
        Raises:
            ValueError: If an unknown provider is specified
        """
        provider = config.get("provider", "mock")
        
        # Check cache for existing instance
        cache_key = f"{provider}-{hash(frozenset(config.items()))}"
        if cache_key in cls._instance_cache:
            return cls._instance_cache[cache_key]
        
        # Create new instance
        if provider == "mock":
            service = MockPAT()
        elif provider == "bedrock":
            service = BedrockPAT()
        else:
            raise ValueError(f"Unknown PAT provider: {provider}")
        
        # Initialize the service
        service.initialize(config)
        
        # Cache the instance
        cls._instance_cache[cache_key] = service
        
        return service
```

## Testing

### Unit Testing

Unit tests should test each implementation in isolation:

```python
def test_mock_pat_analyze_actigraphy():
    """Test the analyze_actigraphy method of MockPAT."""
    # Arrange
    pat = MockPAT()
    pat.initialize({"storage_path": tempfile.mkdtemp()})
    
    readings = [
        {"timestamp": "2025-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3},
        {"timestamp": "2025-01-01T00:00:01Z", "x": 0.2, "y": 0.3, "z": 0.4},
        {"timestamp": "2025-01-01T00:00:02Z", "x": 0.3, "y": 0.4, "z": 0.5}
    ]
    
    # Act
    result = pat.analyze_actigraphy(
        patient_id="test-patient-1",
        readings=readings,
        start_time="2025-01-01T00:00:00Z",
        end_time="2025-01-01T00:00:02Z",
        sampling_rate_hz=1.0,
        device_info={"device_type": "smartwatch"},
        analysis_types=["sleep_quality", "activity_levels"]
    )
    
    # Assert
    assert "analysis_id" in result
    assert result["patient_id"] == "test-patient-1"
    assert "timestamp" in result
    assert "sleep_quality" in result
    assert "activity_levels" in result
```

### Integration Testing

Integration tests should test the PAT service with other components:

```python
def test_api_analyze_actigraphy():
    """Test the API endpoint for analyzing actigraphy data."""
    # Arrange
    client = TestClient(app)
    
    request_data = {
        "patient_id": "test-patient-1",
        "readings": [
            {"timestamp": "2025-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3},
            {"timestamp": "2025-01-01T00:00:01Z", "x": 0.2, "y": 0.3, "z": 0.4},
            {"timestamp": "2025-01-01T00:00:02Z", "x": 0.3, "y": 0.4, "z": 0.5}
        ],
        "start_time": "2025-01-01T00:00:00Z",
        "end_time": "2025-01-01T00:00:02Z",
        "sampling_rate_hz": 1.0,
        "device_info": {"device_type": "smartwatch"},
        "analysis_types": ["sleep_quality", "activity_levels"]
    }
    
    # Act
    response = client.post(
        "/api/v1/actigraphy/analyze",
        json=request_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert data["patient_id"] == "test-patient-1"
```

## API Integration

### Dependency Injection

Use FastAPI's dependency injection to provide the PAT service:

```python
# In app/api/dependencies/ml.py
from app.core.config.settings import get_settings
from app.core.services.ml.pat.factory import PATFactory
from app.core.services.ml.pat.interface import PATInterface


def get_pat_service() -> PATInterface:
    """Dependency for getting a PAT service.
    
    Returns:
        PAT service implementation
    """
    settings = get_settings()
    
    config = {
        "provider": settings.pat_provider,
        "storage_path": settings.pat_storage_path,
        "bucket_name": settings.pat_bucket_name,
        "table_name": settings.pat_table_name,
        "model_id": settings.pat_model_id
    }
    
    return PATFactory.get_pat_service(config)
```

### API Endpoints

API endpoints should use dependency injection to get the PAT service:

```python
# In app/api/routes/actigraphy.py
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_actigraphy(
    request: AnalysisRequest,
    pat_service: PATInterface = Depends(get_pat_service),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Analyze actigraphy data and return insights.
    
    Args:
        request: Analysis request
        pat_service: PAT service implementation
        current_user: Authenticated user
        
    Returns:
        Analysis response
    """
    # Authorize the request
    if current_user.role not in ["provider", "admin"]:
        if request.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to analyze actigraphy for this patient"
            )
    
    try:
        # Call the PAT service
        result = pat_service.analyze_actigraphy(
            patient_id=request.patient_id,
            readings=request.readings,
            start_time=request.start_time,
            end_time=request.end_time,
            sampling_rate_hz=request.sampling_rate_hz,
            device_info=request.device_info.dict(),
            analysis_types=request.analysis_types
        )
        
        return result
    except PATError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in analyze_actigraphy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
```

## Production Considerations

### Performance Optimization

For production deployments:

1. Use caching to avoid redundant computations
2. Implement connection pooling for AWS services
3. Use asynchronous patterns where appropriate

### Deployment Configuration

Configure the PAT service through environment variables:

```
# PAT Service Configuration
PAT_PROVIDER=bedrock
PAT_STORAGE_PATH=/tmp/pat_storage
PAT_BUCKET_NAME=novamind-actigraphy-data
PAT_TABLE_NAME=novamind-actigraphy-analyses
PAT_MODEL_ID=amazon.titan-embed-text-v1
PAT_KMS_KEY_ID=arn:aws:kms:us-east-1:123456789012:key/abcd1234-5678-90ab-cdef-1234567890ab
```

### Monitoring and Logging

Implement comprehensive monitoring and logging:

1. Log all API calls and service operations
2. Use structured logging with proper PHI sanitization
3. Monitor performance metrics and error rates

### Security

Implement robust security measures:

1. Encrypt all data at rest and in transit
2. Implement least privilege access for AWS services
3. Regularly audit access logs
4. Use AWS KMS for key management

## Future Enhancements

Planned enhancements for the PAT service:

1. **Real-time Analysis**: Implement streaming capabilities for real-time monitoring
2. **Advanced Machine Learning**: Incorporate more advanced models for deeper insights
3. **Multi-device Support**: Support additional wearable device types
4. **Federated Learning**: Implement privacy-preserving federated learning
5. **Explainable AI**: Provide more transparent reasoning for insights

## Conclusion

This implementation guide provides a comprehensive overview of the PAT service architecture and implementation. By following these guidelines, developers can effectively work with and extend the PAT service while maintaining HIPAA compliance and ensuring a high-quality, reliable system.