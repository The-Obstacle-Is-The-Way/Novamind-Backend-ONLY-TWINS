# Pretrained Actigraphy Transformer (PAT)

## Executive Summary

The Pretrained Actigraphy Transformer (PAT) is a HIPAA-compliant system for analyzing wearable device accelerometer data to extract clinically relevant insights about patient behavior, sleep patterns, and activity levels. It serves as a critical component in our concierge psychiatry platform, providing objective biometric data to enhance clinical decision-making.

PAT analyzes raw actigraphy data from wearable devices such as Fitbit, Apple Watch, Oura Ring, and Garmin to extract insights about:

- **Sleep quality** (efficiency, duration, stages, disturbances)
- **Activity levels** (sedentary time, exercise intensity)
- **Circadian rhythms** (regularity, phase shifts, social jet lag)
- **Behavioral patterns** (daily routines, disruptions)
- **Mood indicators** (activity signatures correlated with mood states)

These insights are seamlessly integrated with our Digital Twin system to create a comprehensive patient model that combines subjective reports with objective biometric data.

## Architecture

PAT follows Clean Architecture principles with strict separation of concerns:

### Domain Layer

The `PATInterface` Protocol defines the core operations without any external dependencies, allowing for multiple implementations while maintaining a consistent API.

Key domain entities include:
- Sleep metrics
- Activity levels
- Circadian metrics
- Behavioral patterns
- Mood indicators

Domain-specific exceptions ensure proper error handling throughout the system.

### Data/Infrastructure Layer

Two implementations are provided:
- `MockPAT`: For development, testing, and demonstration purposes
- `BedrockPAT`: Production implementation using AWS Bedrock and other AWS services

The `PATFactory` follows the Factory pattern to create and manage PAT service instances based on configuration settings.

### Presentation Layer

FastAPI routes provide a RESTful API for the PAT service, with Pydantic v2 schemas for request/response validation.

## Design Patterns

PAT implements several Gang of Four (GoF) design patterns:

1. **Strategy Pattern**: Multiple implementations of the `PATInterface` Protocol
2. **Factory Pattern**: The `PATFactory` creates PAT service instances based on configuration
3. **Dependency Injection**: PAT services are injected via FastAPI's `Depends()`
4. **Repository Pattern**: Data access is abstracted behind repository interfaces

## HIPAA Compliance

PAT is designed with HIPAA compliance as a core requirement:

- **Data Encryption**: All data is encrypted at rest and in transit
- **Access Control**: All endpoints enforce authentication and authorization
- **Audit Logging**: Operations are logged with PHI sanitization
- **Limited Data Collection**: Only necessary data is processed and stored
- **Secure Infrastructure**: AWS services with BAA support are used
- **Data Retention**: Configurable data retention policies

## API Usage

### Analyzing Actigraphy Data

```python
import requests
import json

# Authentication token
headers = {
    "Authorization": f"Bearer {token}"
}

# Request payload
payload = {
    "patient_id": "p123e4567-e89b-12d3-a456-426614174000",
    "readings": [
        {
            "timestamp": "2025-03-28T00:00:00Z",
            "x": 0.1,
            "y": 0.2,
            "z": 0.3
        },
        # Additional readings...
    ],
    "start_time": "2025-03-28T00:00:00Z",
    "end_time": "2025-03-28T08:00:00Z",
    "sampling_rate_hz": 10.0,
    "device_info": {
        "device_type": "fitbit",
        "model": "versa-3",
        "firmware_version": "1.2.3",
        "sampling_capabilities": {
            "accelerometer": True,
            "heart_rate": True,
            "temperature": False
        }
    },
    "analysis_types": [
        "sleep_quality",
        "activity_levels",
        "circadian_rhythm"
    ]
}

# Send request
response = requests.post(
    "https://api.example.com/actigraphy/analyze",
    headers=headers,
    json=payload
)

# Process response
result = response.json()
print(json.dumps(result, indent=2))
```

### Integrating with Digital Twin

```python
# Request payload
payload = {
    "patient_id": "p123e4567-e89b-12d3-a456-426614174000",
    "profile_id": "pr123e4567-e89b-12d3-a456-426614174000",
    "actigraphy_analysis": {
        # Analysis result from previous call
    }
}

# Send request
response = requests.post(
    "https://api.example.com/actigraphy/integrate",
    headers=headers,
    json=payload
)

# Process response
result = response.json()
print(json.dumps(result, indent=2))
```

## Configuration

PAT configuration is stored in the application's `.env` file:

```env
# PAT Configuration
PAT_PROVIDER=bedrock                   # Provider: 'mock' or 'bedrock'
PAT_STORAGE_PATH=/path/to/storage      # Storage path for mock provider
PAT_BUCKET_NAME=pat-data-bucket        # S3 bucket for Bedrock provider
PAT_TABLE_NAME=pat-analyses            # DynamoDB table for Bedrock provider
PAT_KMS_KEY_ID=arn:aws:kms:...         # KMS key ARN for encryption
PAT_MODEL_ID=amazon.titan-embed-text-v1 # Bedrock model ID
```

## Using the Mock Implementation

The `MockPAT` implementation is useful for development, testing, and demonstration purposes. It generates realistic synthetic data that mimics the behavior of the real PAT service.

To use the mock implementation, set `PAT_PROVIDER=mock` in your `.env` file.

## Using the Bedrock Implementation

The `BedrockPAT` implementation uses AWS Bedrock for inference and other AWS services for secure, HIPAA-compliant data storage and processing:

- **AWS Bedrock**: For model inference
- **Amazon S3**: For storing raw data with server-side encryption
- **Amazon DynamoDB**: For storing analysis results
- **AWS KMS**: For encryption key management

To use the Bedrock implementation, set `PAT_PROVIDER=bedrock` in your `.env` file and ensure that the following AWS services are configured:

1. AWS Bedrock with the appropriate model
2. S3 bucket with server-side encryption
3. DynamoDB table with appropriate schema
4. KMS key for encryption

## Integration with Digital Twin

PAT seamlessly integrates with the Digital Twin system to enhance the patient model with objective biometric data. The integration workflow is as follows:

1. Actigraphy data is analyzed using the PAT service
2. The analysis results are transformed into a format suitable for the Digital Twin
3. The transformed data is integrated into the patient's Digital Twin profile
4. The enhanced Digital Twin model provides a more comprehensive view of the patient's health state

## High-Level Workflow

The typical workflow for using PAT is as follows:

1. **Data Collection**: Collect accelerometer data from wearable devices
2. **Data Analysis**: Analyze the data using the PAT service
3. **Insight Generation**: Extract clinically relevant insights
4. **Digital Twin Integration**: Integrate the insights with the patient's Digital Twin
5. **Clinical Decision Support**: Use the enhanced Digital Twin for clinical decision support

## Security Considerations

PAT implements several security measures to protect patient data:

- **Authentication**: All API endpoints require authentication
- **Authorization**: Access to patient data is restricted based on user roles
- **Encryption**: All data is encrypted at rest and in transit
- **Audit Logging**: All operations are logged with PHI sanitization
- **Access Control**: Fine-grained access control based on JWT tokens
- **Secure Configuration**: Sensitive configuration is stored securely

## Performance Considerations

PAT is designed to handle large volumes of data with high performance:

- **Batch Processing**: Data can be processed in batches for efficiency
- **Caching**: Results are cached to improve performance
- **Pagination**: API responses are paginated to handle large result sets
- **Asynchronous Processing**: Long-running operations can be processed asynchronously

## Testing

PAT includes comprehensive tests at multiple levels:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test the complete workflow
- **Security Tests**: Test security measures
- **Performance Tests**: Test performance under load

## Future Enhancements

Planned enhancements for PAT include:

- Additional analysis types (heart rate variability, stress levels)
- Support for additional wearable devices
- Enhanced Digital Twin integration for more comprehensive patient modeling
- Real-time data streaming for continuous monitoring
- Machine learning for personalized insights

## Conclusion

The Pretrained Actigraphy Transformer (PAT) is a critical component of our concierge psychiatry platform, providing objective biometric data to enhance clinical decision-making. Its clean architecture, HIPAA compliance, and seamless integration with the Digital Twin system make it a powerful tool for mental health care providers.