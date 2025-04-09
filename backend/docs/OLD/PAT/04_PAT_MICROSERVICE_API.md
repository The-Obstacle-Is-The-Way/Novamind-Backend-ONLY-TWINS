# PAT Microservice API Specification

## Overview

This document defines the API specifications for the Pretrained Actigraphy Transformer (PAT) microservice within the Novamind digital twin psychiatry platform. The API follows RESTful principles and is implemented using FastAPI with HIPAA-compliant security measures.

## Base URL

```
/api/v1/actigraphy
```

## Authentication

All endpoints require authentication using JWT tokens. The tokens must be included in the `Authorization` header with the `Bearer` prefix.

```
Authorization: Bearer <token>
```

## Endpoints

### 1. Upload Actigraphy Data

Upload raw actigraphy data from wearable devices for analysis.

**Endpoint:** `POST /upload`

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file`: Actigraphy data file (CSV, JSON, or binary format)
  - `patient_id`: Patient identifier (string)
  - `device_type`: Type of wearable device (string)
  - `start_time`: Start time of recording (ISO 8601 format)
  - `end_time`: End time of recording (ISO 8601 format)
  - `metadata`: Additional metadata (JSON string)

**Response:**
```json
{
  "upload_id": "string",
  "patient_id": "string",
  "file_name": "string",
  "status": "success",
  "message": "Actigraphy data uploaded successfully",
  "timestamp": "2025-03-28T12:00:00Z"
}
```

**Status Codes:**
- `201 Created`: Upload successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: Insufficient permissions
- `503 Service Unavailable`: Service not available

### 2. Analyze Actigraphy Data

Analyze actigraphy data to extract biometric insights and mental health correlations.

**Endpoint:** `POST /analyze`

**Request:**
- Content-Type: `application/json`
- Body:
```json
{
  "patient_id": "string",
  "readings": [
    {
      "timestamp": "2025-03-28T12:00:00Z",
      "x": 0.0,
      "y": 0.0,
      "z": 0.0,
      "source_device": "string"
    }
  ],
  "start_time": "2025-03-28T12:00:00Z",
  "end_time": "2025-03-28T12:00:00Z",
  "sampling_rate_hz": 30.0,
  "device_info": {
    "device_type": "string",
    "firmware_version": "string",
    "model": "string"
  },
  "analysis_types": [
    "activity_levels",
    "sleep_quality",
    "circadian_rhythm",
    "mental_health_correlations"
  ]
}
```

**Response:**
```json
{
  "analysis_id": "string",
  "patient_id": "string",
  "timestamp": "2025-03-28T12:00:00Z",
  "activity_levels": {
    "sedentary": 0.6,
    "light": 0.3,
    "moderate": 0.1,
    "vigorous": 0.0
  },
  "sleep_metrics": {
    "sleep_efficiency": 0.85,
    "sleep_duration_hours": 7.2,
    "wake_after_sleep_onset_minutes": 25.0,
    "sleep_latency_minutes": 15.0
  },
  "circadian_rhythm_metrics": {
    "rhythm_stability": 0.78,
    "interdaily_stability": 0.65,
    "intradaily_variability": 0.22
  },
  "mental_health_correlations": {
    "depression_risk_score": 0.35,
    "anxiety_indicator": 0.42,
    "stress_level": 0.51
  }
}
```

**Status Codes:**
- `200 OK`: Analysis successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: Insufficient permissions
- `503 Service Unavailable`: Service not available

### 3. Get Embeddings

Generate embeddings from actigraphy data for use in downstream models.

**Endpoint:** `POST /embeddings`

**Request:**
- Content-Type: `application/json`
- Body: Same as the `/analyze` endpoint

**Response:**
```json
{
  "embedding_id": "string",
  "patient_id": "string",
  "timestamp": "2025-03-28T12:00:00Z",
  "embeddings": [0.1, 0.2, 0.3, ...],
  "embedding_size": 256,
  "model_version": "PAT-M"
}
```

**Status Codes:**
- `200 OK`: Embeddings generated successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: Insufficient permissions
- `503 Service Unavailable`: Service not available

### 4. Get Analysis by ID

Retrieve a previously generated analysis by its ID.

**Endpoint:** `GET /analysis/{analysis_id}`

**Parameters:**
- `analysis_id`: ID of the analysis to retrieve (path parameter)

**Response:**
- Same as the `/analyze` endpoint response

**Status Codes:**
- `200 OK`: Analysis found
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Analysis not found
- `503 Service Unavailable`: Service not available

### 5. Get Patient Analyses

Retrieve all analyses for a specific patient.

**Endpoint:** `GET /patient/{patient_id}/analyses`

**Parameters:**
- `patient_id`: Patient identifier (path parameter)
- `start_date`: Start date for filtering (query parameter, ISO 8601 format)
- `end_date`: End date for filtering (query parameter, ISO 8601 format)
- `limit`: Maximum number of analyses to return (query parameter, default: 10)
- `offset`: Offset for pagination (query parameter, default: 0)

**Response:**
```json
{
  "patient_id": "string",
  "analyses": [
    {
      "analysis_id": "string",
      "timestamp": "2025-03-28T12:00:00Z",
      "analysis_types": ["activity_levels", "sleep_quality"],
      "summary": {
        "sleep_efficiency": 0.85,
        "activity_level": "moderate"
      }
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0
}
```

**Status Codes:**
- `200 OK`: Analyses found
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Patient not found
- `503 Service Unavailable`: Service not available

### 6. Get Model Information

Retrieve information about the PAT model being used.

**Endpoint:** `GET /model-info`

**Response:**
```json
{
  "model_name": "PAT",
  "model_size": "medium",
  "model_version": "1.0.0",
  "input_dimensions": [null, 3],
  "output_dimensions": 256,
  "supported_analysis_types": [
    "activity_levels",
    "sleep_quality",
    "circadian_rhythm",
    "mental_health_correlations"
  ],
  "last_updated": "2025-01-15T00:00:00Z"
}
```

**Status Codes:**
- `200 OK`: Information retrieved successfully
- `401 Unauthorized`: Authentication failed
- `503 Service Unavailable`: Service not available

## Integration with Digital Twin

The PAT microservice integrates with the Digital Twin platform through the following mechanisms:

### 1. Direct API Calls

The Digital Twin Integration Service can make direct API calls to the PAT microservice to analyze actigraphy data and incorporate the results into the digital twin model.

Example integration code:
```python
async def analyze_patient_actigraphy(patient_id: str, actigraphy_data: ActigraphyData):
    """
    Analyze patient actigraphy data and update digital twin.
    
    Args:
        patient_id: Patient identifier
        actigraphy_data: Actigraphy data to analyze
    """
    # Call PAT microservice
    pat_result = await pat_client.analyze(
        patient_id=patient_id,
        readings=actigraphy_data.readings,
        start_time=actigraphy_data.start_time,
        end_time=actigraphy_data.end_time,
        sampling_rate_hz=actigraphy_data.sampling_rate_hz,
        device_info=actigraphy_data.device_info,
        analysis_types=["activity_levels", "sleep_quality", "mental_health_correlations"]
    )
    
    # Update digital twin with PAT results
    await update_digital_twin_biometrics(
        patient_id=patient_id,
        biometric_data={
            "activity_levels": pat_result.activity_levels,
            "sleep_metrics": pat_result.sleep_metrics,
            "mental_health_correlations": pat_result.mental_health_correlations
        }
    )
```

### 2. Event-Based Integration

The PAT microservice can publish events to a message queue (e.g., AWS SNS/SQS, RabbitMQ) when new analyses are completed. The Digital Twin service subscribes to these events and updates the twin state accordingly.

Example event schema:
```json
{
  "event_type": "actigraphy_analysis_completed",
  "timestamp": "2025-03-28T12:00:00Z",
  "patient_id": "string",
  "analysis_id": "string",
  "summary": {
    "sleep_efficiency": 0.85,
    "activity_level": "moderate",
    "depression_risk_score": 0.35
  }
}
```

### 3. Shared Database

Both services can access a shared database for storing and retrieving analysis results, ensuring consistency and reducing duplication of data.

## Error Handling

All endpoints return standardized error responses in the following format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

Common error codes:
- `INVALID_REQUEST`: Invalid request parameters
- `AUTHENTICATION_ERROR`: Authentication failed
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `SERVICE_UNAVAILABLE`: Service not available
- `INTERNAL_ERROR`: Internal server error

## Data Schemas

### ActigraphyReading

```json
{
  "timestamp": "2025-03-28T12:00:00Z",
  "x": 0.0,
  "y": 0.0,
  "z": 0.0,
  "source_device": "string"
}
```

### ActigraphyData

```json
{
  "patient_id": "string",
  "readings": [ActigraphyReading],
  "start_time": "2025-03-28T12:00:00Z",
  "end_time": "2025-03-28T12:00:00Z",
  "sampling_rate_hz": 30.0,
  "device_info": {
    "device_type": "string",
    "firmware_version": "string",
    "model": "string"
  }
}
```

### ActigraphyAnalysisResult

```json
{
  "analysis_id": "string",
  "patient_id": "string",
  "timestamp": "2025-03-28T12:00:00Z",
  "activity_levels": {
    "sedentary": 0.0,
    "light": 0.0,
    "moderate": 0.0,
    "vigorous": 0.0
  },
  "sleep_metrics": {
    "sleep_efficiency": 0.0,
    "sleep_duration_hours": 0.0,
    "wake_after_sleep_onset_minutes": 0.0,
    "sleep_latency_minutes": 0.0
  },
  "circadian_rhythm_metrics": {
    "rhythm_stability": 0.0,
    "interdaily_stability": 0.0,
    "intradaily_variability": 0.0
  },
  "mental_health_correlations": {
    "depression_risk_score": 0.0,
    "anxiety_indicator": 0.0,
    "stress_level": 0.0
  }
}
```

## HIPAA Compliance Considerations

1. **Authentication and Authorization**
   - All endpoints require authentication using JWT tokens
   - Role-based access control (RBAC) for different user types
   - Audit logging of all API access

2. **Data Security**
   - All API communications use TLS 1.2+
   - Request and response payloads are encrypted in transit
   - Patient identifiers are never exposed in URLs

3. **Audit Trail**
   - All API calls are logged with timestamp, user ID, and action
   - Logs are stored in a HIPAA-compliant manner
   - Audit logs can be retrieved for compliance reporting

4. **PHI Protection**
   - No PHI is included in error messages or logs
   - All PHI is encrypted at rest
   - Data retention policies are enforced

## Implementation Example

Here's an example of how to implement the `/analyze` endpoint using FastAPI:

```python
@router.post(
    "/analyze",
    response_model=ActigraphyAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze actigraphy data",
    description="Analyze actigraphy data to extract insights.",
    response_description="Analysis results"
)
async def analyze_actigraphy(
    request: ActigraphyAnalysisRequest,
    current_user = Depends(get_current_active_provider),
    pat_service: PATService = Depends(get_pat_service)
) -> ActigraphyAnalysisResponse:
    """
    Analyze actigraphy data to extract insights.
    
    Args:
        request: Analysis request parameters
        current_user: The authenticated user making the request
        pat_service: The PAT service
        
    Returns:
        Analysis results
        
    Raises:
        HTTPException: If the analysis fails
    """
    if not pat_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Actigraphy service is not available"
        )
    
    try:
        # Convert request to domain model
        actigraphy_data = ActigraphyData(
            patient_id=request.patient_id,
            readings=request.readings,
            start_time=request.start_time,
            end_time=request.end_time,
            sampling_rate_hz=request.sampling_rate_hz,
            device_info=request.device_info
        )
        
        # Perform analysis
        result = await pat_service.analyze_actigraphy(
            actigraphy_data=actigraphy_data,
            analysis_types=request.analysis_types
        )
        
        # Convert domain model to response schema
        return ActigraphyAnalysisResponse(
            analysis_id=result.analysis_id,
            patient_id=result.patient_id,
            timestamp=result.timestamp,
            activity_levels=result.activity_levels,
            sleep_metrics=result.sleep_metrics,
            circadian_rhythm_metrics=result.circadian_rhythm_metrics,
            mental_health_correlations=result.mental_health_correlations
        )
    
    except Exception as e:
        logger.exception(f"Error analyzing actigraphy data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing actigraphy data: {str(e)}"
        )
```

## Client Integration Example

Here's an example of how a client might integrate with the PAT microservice:

```python
import aiohttp
import json
from typing import Dict, List, Any

class PATClient:
    """Client for interacting with the PAT microservice."""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the PAT client.
        
        Args:
            base_url: Base URL of the PAT microservice
            api_key: API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def analyze(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float,
        device_info: Dict[str, str],
        analysis_types: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze actigraphy data.
        
        Args:
            patient_id: Patient identifier
            readings: Accelerometer readings
            start_time: Start time of recording
            end_time: End time of recording
            sampling_rate_hz: Sampling rate in Hz
            device_info: Device information
            analysis_types: Types of analysis to perform
            
        Returns:
            Analysis results
        """
        url = f"{self.base_url}/analyze"
        payload = {
            "patient_id": patient_id,
            "readings": readings,
            "start_time": start_time,
            "end_time": end_time,
            "sampling_rate_hz": sampling_rate_hz,
            "device_info": device_info,
            "analysis_types": analysis_types
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    raise Exception(f"Error analyzing actigraphy data: {error_data}")
```

## Conclusion

This API specification provides a comprehensive guide for implementing and integrating with the PAT microservice. By following these guidelines, developers can ensure that the microservice is HIPAA-compliant, secure, and interoperable with the broader digital twin platform.

For implementation details, refer to the following documents:
- [01_PAT_ARCHITECTURE_AND_INTEGRATION.md](01_PAT_ARCHITECTURE_AND_INTEGRATION.md)
- [02_PAT_AWS_DEPLOYMENT_HIPAA.md](02_PAT_AWS_DEPLOYMENT_HIPAA.md)
- [03_PAT_IMPLEMENTATION_GUIDE.md](03_PAT_IMPLEMENTATION_GUIDE.md)