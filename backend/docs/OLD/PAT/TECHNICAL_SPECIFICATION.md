# Physical Activity Tracking (PAT) Service Technical Specification

## Overview

The Physical Activity Tracking (PAT) service is a HIPAA-compliant machine learning service that processes actigraphy data to provide insights into patients' physical activity patterns, sleep quality, movement characteristics, and other behavioral metrics relevant to mental health assessment and treatment.

## Architecture

### Clean Architecture

The PAT service follows Clean Architecture principles with strict separation of concerns:

1. **Domain Layer**
   - `interface.py`: Defines the `PATInterface` with core business methods
   - `exceptions.py`: Domain-specific exceptions

2. **Infrastructure Layer**
   - `mock.py`: Mock implementation for development and testing
   - `aws.py`: Production implementation using AWS services

3. **Factory**
   - `factory.py`: Factory for creating the appropriate implementation

4. **API Layer**
   - `app/api/schemas/actigraphy.py`: Request/response Pydantic models
   - `app/api/routes/actigraphy.py`: FastAPI endpoints

### Component Diagram

```
┌───────────────────────┐     ┌───────────────────────┐
│                       │     │                       │
│     API Routes        │────▶│    Pydantic Schemas   │
│                       │     │                       │
└───────────┬───────────┘     └───────────────────────┘
            │
            ▼
┌───────────────────────┐     ┌───────────────────────┐
│                       │     │                       │
│   PAT Service Factory │────▶│    PAT Interface      │
│                       │     │                       │
└───────────┬───────────┘     └───────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────┐
│                                                     │
│                  Implementations                    │
│                                                     │
├───────────────────────┐     ┌───────────────────────┐
│                       │     │                       │
│   Mock PAT Service    │     │   AWS PAT Service     │
│                       │     │                       │
└───────────────────────┘     └───────────────────────┘
```

## Data Flow

1. **Client** sends actigraphy data to the API endpoint
2. **API Layer** validates the request using Pydantic schemas
3. **Factory** creates the appropriate PAT service implementation
4. **Service Implementation** processes the data and returns results
5. **API Layer** formats and returns the response

## Interfaces

### PATInterface

The `PATInterface` defines the core methods for the PAT service:

```python
class PATInterface(ABC):
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the PAT service with configuration."""
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
        analysis_types: List[str],
    ) -> Dict[str, Any]:
        """Analyze actigraphy data."""
        pass
    
    @abstractmethod
    def get_actigraphy_embeddings(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float,
    ) -> Dict[str, Any]:
        """Generate embeddings from actigraphy data."""
        pass
    
    @abstractmethod
    def get_analysis_by_id(self, analysis_id: str) -> Dict[str, Any]:
        """Get analysis results by ID."""
        pass
    
    @abstractmethod
    def get_patient_analyses(
        self,
        patient_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get analyses for a patient."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the PAT model."""
        pass
    
    @abstractmethod
    def integrate_with_digital_twin(
        self,
        patient_id: str,
        profile_id: str,
        analysis_id: str
    ) -> Dict[str, Any]:
        """Integrate actigraphy analysis with digital twin."""
        pass
```

## API Endpoints

The following RESTful endpoints are available:

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/v1/actigraphy/analyze` | Analyze actigraphy data |
| POST | `/api/v1/actigraphy/embeddings` | Generate embeddings from actigraphy data |
| GET | `/api/v1/actigraphy/analyses/{analysis_id}` | Get analysis by ID |
| GET | `/api/v1/actigraphy/patient/{patient_id}/analyses` | List analyses for a patient |
| GET | `/api/v1/actigraphy/model-info` | Get model information |
| POST | `/api/v1/actigraphy/integrate-with-digital-twin` | Integrate analysis with digital twin |

## AWS Implementation

The AWS implementation uses the following AWS services:

1. **Amazon SageMaker**: For hosting the machine learning model
   - Custom model trained on actigraphy data
   - Supports real-time inference
   - GPU-accelerated for fast processing

2. **Amazon S3**: For storing raw data and analysis results
   - Encrypted at rest using AWS KMS
   - Versioning enabled for audit and recovery

3. **Amazon DynamoDB**: For metadata and results storage
   - Separate tables for analyses, embeddings, and integrations
   - On-demand capacity for optimal cost/performance

4. **AWS Comprehend Medical**: For PHI detection and removal
   - Identifies PHI in text fields
   - Redacts sensitive information before processing

## Data Models

### Actigraphy Reading Format

```json
{
  "x": 0.123,         // X-axis acceleration (g)
  "y": 0.456,         // Y-axis acceleration (g)
  "z": 0.789,         // Z-axis acceleration (g)
  "timestamp": "2025-03-28T12:00:00.000Z"  // ISO8601 timestamp
}
```

### Analysis Result Format

```json
{
  "analysis_id": "uuid-string",
  "patient_id": "patient-id",
  "timestamp": "2025-03-28T12:00:00.000Z",
  "data_summary": {
    "start_time": "2025-03-28T12:00:00.000Z",
    "end_time": "2025-03-28T13:00:00.000Z",
    "duration_seconds": 3600.0,
    "readings_count": 180000,
    "sampling_rate_hz": 50.0
  },
  "device_info": {
    "name": "ActiGraph GT9X",
    "firmware": "1.7.0",
    "device_id": "AG12345"
  },
  "analysis_types": ["activity_levels", "sleep_analysis"],
  "results": {
    "activity_levels": {
      "sedentary_minutes": 30.5,
      "light_minutes": 15.2,
      "moderate_minutes": 10.0,
      "vigorous_minutes": 4.3,
      "total_activity_score": 87.5
    },
    "sleep_analysis": {
      "total_sleep_time_minutes": 0.0,
      "sleep_efficiency_percent": 0.0,
      "wake_after_sleep_onset_minutes": 0.0,
      "sleep_latency_minutes": 0.0,
      "fragmentation_index": 0.0
    }
  }
}
```

### Embedding Format

```json
{
  "embedding_id": "uuid-string",
  "patient_id": "patient-id",
  "timestamp": "2025-03-28T12:00:00.000Z",
  "data_summary": {
    "start_time": "2025-03-28T12:00:00.000Z",
    "end_time": "2025-03-28T13:00:00.000Z",
    "duration_seconds": 3600.0,
    "readings_count": 180000,
    "sampling_rate_hz": 50.0
  },
  "embedding": {
    "vector": [0.1, 0.2, 0.3, ...],  // 256-dimensional vector
    "dimension": 256,
    "model_version": "pat-embeddings-v1.0"
  }
}
```

## Security & HIPAA Compliance

### Data Privacy

1. **No PHI in Logs**: All logging uses PHI detection and sanitization
2. **Encrypted Data**: All data is encrypted at rest and in transit
3. **Minimal Data Collection**: Only necessary data is collected and stored
4. **Data Lifecycle**: Automated data purging based on retention policies

### Authentication & Authorization

1. **JWT Tokens**: All API calls require valid JWT tokens
2. **Role-Based Access**: Different access levels for providers, patients, etc.
3. **Audit Logging**: All access and changes are logged for compliance

### AWS Security

1. **VPC Configuration**: SageMaker endpoints deployed in private subnets
2. **IAM Roles**: Least privilege principle for service accounts
3. **KMS Encryption**: Customer-managed keys for sensitive data
4. **CloudTrail**: Logging of all AWS API calls

## Testing Strategy

1. **Unit Tests**: For individual components
   - `tests/unit/services/ml/pat/test_mock_pat.py`
   - `tests/unit/services/ml/pat/test_aws_pat.py`
   - `tests/unit/api/routes/test_actigraphy_routes.py`

2. **Integration Tests**: For API and service interaction
   - `tests/integration/api/test_actigraphy_api_integration.py`

## Configuration

The PAT service is configured through environment variables:

```
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=novamind-prod

# PAT Service Configuration
PAT_SERVICE_TYPE=aws|mock
PAT_ENDPOINT_NAME=novamind-pat-endpoint
PAT_BUCKET_NAME=novamind-pat-data
PAT_ANALYSES_TABLE=novamind-pat-analyses
PAT_EMBEDDINGS_TABLE=novamind-pat-embeddings
PAT_INTEGRATIONS_TABLE=novamind-pat-integrations
```

## Performance Considerations

1. **Batch Processing**: Support for large dataset processing
2. **SageMaker Scaling**: Auto-scaling based on demand
3. **DynamoDB Throughput**: On-demand capacity for cost efficiency
4. **Result Caching**: Frequently accessed results are cached

## Digital Twin Integration

The PAT service can integrate with the Digital Twin service to update patient profiles:

1. **Movement Patterns**: Update movement characteristics
2. **Sleep Patterns**: Update sleep quality and patterns
3. **Activity Levels**: Update physical activity levels
4. **Behavioral Indicators**: Update behavioral metrics

## Future Enhancements

1. **Real-time Analysis**: Stream processing for continuous monitoring
2. **Multi-modal Integration**: Combine actigraphy with other sensor data
3. **Longitudinal Analysis**: Track changes over time
4. **Anomaly Detection**: Identify unusual patterns
5. **Federated Learning**: Privacy-preserving model updates

## References

1. **AWS Documentation**: [SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
2. **Actigraphy Standards**: [ActiGraph Device Specifications](https://actigraphcorp.com/)
3. **HIPAA Compliance**: [AWS HIPAA Compliance](https://aws.amazon.com/compliance/hipaa-compliance/)