# Physical Activity Tracker (PAT) Service

## Overview

The Physical Activity Tracker (PAT) service is a HIPAA-compliant AI-powered service for analyzing actigraphy data from wearable devices. It offers clinical insights about patients' physical activity, sleep patterns, stress levels, circadian rhythms, and anomalous behaviors.

This service is designed for luxury concierge psychiatry practices, providing high-quality, actionable insights that clinicians can use to better understand patient behaviors and adjust treatment plans accordingly.

## Key Features

- **Sleep Analysis**: Detailed breakdown of sleep cycles, quality, and patterns
- **Activity Analysis**: Quantification of physical activity levels, duration, and intensity
- **Stress Analysis**: Detection of high-stress periods and potential triggers
- **Circadian Rhythm Analysis**: Assessment of daily patterns and rhythm disruptions
- **Anomaly Detection**: Identification of unusual patterns that may indicate clinical concerns
- **Digital Twin Integration**: Seamless integration with patient Digital Twin profiles
- **Embedding Generation**: Creation of vector embeddings for machine learning applications

## Architecture

The PAT service follows Clean Architecture principles, with:

- **Domain Layer**: Pure business logic with no external dependencies
- **Data/Infrastructure Layer**: External integrations (AWS Bedrock, storage, etc.)
- **Presentation Layer**: API endpoints and request/response schemas

### Design Patterns

- **Strategy Pattern**: Different PAT implementations can be used interchangeably
- **Factory Pattern**: Service instances are created through a factory
- **Dependency Injection**: Services are injected into routes through FastAPI dependencies

## Components

### Core Service

- `PATInterface`: Abstract interface defining the service contract
- `MockPAT`: In-memory implementation for development and testing
- `BedrockPAT` (planned): Production implementation using AWS Bedrock
- `PATServiceFactory`: Factory for creating appropriate service instances

### API Layer

- Pydantic schemas for request/response validation
- FastAPI routes for each service capability
- Dependency injection for service instances

### Exception Handling

- Domain-specific exceptions for clear error messages
- HIPAA-compliant error handling (no PHI in logs)
- HTTP status code mapping

## Usage

### Service Configuration

Configure the PAT service using environment variables:

```
PAT_SERVICE_TYPE=mock  # or "bedrock" for production
PAT_MOCK_DELAY_MS=200  # optional delay for mock service
AWS_REGION=us-east-1   # required for "bedrock" service type
AWS_ACCESS_KEY_ID=***  # required for "bedrock" service type
AWS_SECRET_ACCESS_KEY=***  # required for "bedrock" service type
PAT_BEDROCK_MODEL_ID=model-id  # required for "bedrock" service type
```

### API Endpoints

- `POST /actigraphy/analyze`: Analyze actigraphy data
- `POST /actigraphy/embeddings`: Generate embeddings from actigraphy data
- `GET /actigraphy/analyses/{analysis_id}`: Get analysis by ID
- `GET /actigraphy/patients/{patient_id}/analyses`: Get analyses for a patient
- `GET /actigraphy/model-info`: Get information about the PAT model
- `POST /actigraphy/integrate-with-digital-twin`: Integrate analysis with Digital Twin

### Example Request

```python
import requests

url = "https://api.novamind.com/actigraphy/analyze"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "patient_id": "patient-123",
    "readings": [
        {"x": 0.1, "y": 0.2, "z": 0.9},
        # ... more readings
    ],
    "start_time": "2025-03-27T12:00:00Z",
    "end_time": "2025-03-28T12:00:00Z",
    "sampling_rate_hz": 30.0,
    "device_info": {
        "device_type": "Actigraph wGT3X-BT",
        "manufacturer": "Actigraph",
        "placement": "wrist"
    },
    "analysis_types": ["sleep", "activity", "stress"]
}

response = requests.post(url, json=payload, headers=headers)
analysis = response.json()
```

## Development

### Adding a New Analysis Type

1. Update the `AnalysisType` enum in `app/api/schemas/actigraphy.py`
2. Add corresponding Pydantic models for the analysis results
3. Implement the analysis logic in the service implementation
4. Update validation in the mock implementation

### Creating a Production Implementation

To create a production implementation using AWS Bedrock:

1. Create a new file `app/core/services/ml/pat/bedrock.py`
2. Implement `BedrockPAT` class implementing `PATInterface`
3. Register the implementation in `PATServiceFactory._registry`
4. Update environment variables for configuration

## HIPAA Compliance

The PAT service is designed with HIPAA compliance as a priority:

- No PHI is stored in logs
- PHI is strictly limited to what's necessary for the service
- Authentication and authorization are required for all endpoints
- All data is transmitted securely (HTTPS required)
- Clear error boundaries prevent PHI leakage

## Testing

The PAT service includes unit tests for both the service implementation and API endpoints:

- `tests/unit/services/test_pat_mock.py`: Tests for the mock implementation
- `tests/unit/api/test_actigraphy_routes.py`: Tests for API endpoints (planned)