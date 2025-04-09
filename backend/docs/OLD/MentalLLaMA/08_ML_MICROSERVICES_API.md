# NOVAMIND ML MICROSERVICES API

## Overview

The NOVAMIND ML Microservices API provides a secure, HIPAA-compliant interface for integrating advanced mental health AI capabilities into the platform. This document outlines the API design, endpoints, security considerations, and integration patterns for the MentaLLaMA-powered microservices that support the Digital Twin and other AI-enhanced features.

## Key Principles

1. **Clean Interfaces**: Each microservice exposes a well-defined API that follows REST principles
2. **PHI Protection**: All services implement comprehensive PHI detection and protection
3. **Domain Segregation**: Clear boundaries between clinical logic and ML implementation details
4. **Asynchronous Processing**: Support for both synchronous and asynchronous analysis operations
5. **Traceability**: Complete audit trail for all ML operations without exposing PHI

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │     │                 │
│  Core Platform  │────►│  API Gateway    │────►│  ML Service     │────►│  MentaLLaMA     │
│  FastAPI        │     │  Authentication │     │  Orchestration  │     │  Analysis Engine│
│                 │     │  & Routing      │     │  Layer          │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │                 │
                                               │  PHI Detection  │
                                               │  & Protection   │
                                               │  Service        │
                                               │                 │
                                               └─────────────────┘
```

## API Service Endpoints

### 1. Mental Health Analysis Service

**Base URL**: `/api/v1/ml/mental-health`

#### Endpoints:

##### Depression Detection

```
POST /depression-detection
```

**Description**: Analyzes text for signs of depression using MentaLLaMA model

**Request Schema**:
```json
{
  "text_content": "string",
  "analysis_parameters": {
    "include_rationale": true,
    "severity_assessment": true
  },
  "processing_mode": "sync"  // or "async"
}
```

**Response Schema**:
```json
{
  "request_id": "uuid-string",
  "status": "completed",  // or "processing" if async
  "result": {
    "depression_indicated": true,
    "confidence": "high",  // high, medium, low
    "severity": "moderate",  // none, mild, moderate, severe
    "rationale": "The text contains multiple references to persistent low mood, sleep disturbance, and loss of interest in previously enjoyed activities, which are key indicators of depression.",
    "key_indicators": [
      "persistent low mood",
      "sleep disturbance",
      "loss of interest"
    ]
  },
  "model_version": "MentaLLaMA-33B-lora-v1.0",
  "processing_time_ms": 1250
}
```

**Request Headers**:
- `Authorization`: JWT token (required)
- `X-Request-ID`: Client-generated request ID (optional)
- `X-Correlation-ID`: Correlation ID for tracing (optional)

##### Risk Assessment

```
POST /risk-assessment
```

**Description**: Evaluates text for potential self-harm or suicide risk using MentaLLaMA model

**Request Schema**:
```json
{
  "text_content": "string",
  "analysis_parameters": {
    "include_key_phrases": true,
    "include_suggested_actions": true
  },
  "processing_mode": "sync"  // or "async"
}
```

**Response Schema**:
```json
{
  "request_id": "uuid-string",
  "status": "completed",  // or "processing" if async
  "result": {
    "risk_level": "low",  // low, moderate, high, severe
    "confidence": "high",  // high, medium, low
    "key_indicators": [
      "expression of hopelessness",
      "references to feeling like a burden"
    ],
    "suggested_actions": [
      "Continue regular monitoring",
      "Address hopelessness in next session"
    ],
    "rationale": "While the text contains expressions of hopelessness, there are no explicit references to self-harm, suicidal ideation, or a specific plan. The individual also mentions future plans, which is a protective factor."
  },
  "model_version": "MentaLLaMA-33B-lora-v1.0",
  "processing_time_ms": 1320
}
```

##### Sentiment Analysis

```
POST /sentiment-analysis
```

**Description**: Analyzes the emotional sentiment expressed in text using MentaLLaMA model

**Request Schema**:
```json
{
  "text_content": "string",
  "analysis_parameters": {
    "include_emotion_distribution": true
  },
  "processing_mode": "sync"  // or "async"
}
```

**Response Schema**:
```json
{
  "request_id": "uuid-string",
  "status": "completed",  // or "processing" if async
  "result": {
    "overall_sentiment": "negative",  // positive, negative, neutral, mixed
    "sentiment_score": -0.65,  // -1.0 to 1.0
    "confidence": "high",  // high, medium, low
    "emotion_distribution": {
      "sadness": 0.65,
      "anxiety": 0.25,
      "anger": 0.05,
      "fear": 0.03,
      "joy": 0.02
    },
    "key_phrases": [
      "feeling overwhelmed",
      "difficult week"
    ]
  },
  "model_version": "MentaLLaMA-33B-lora-v1.0",
  "processing_time_ms": 980
}
```

##### Wellness Dimensions

```
POST /wellness-dimensions
```

**Description**: Analyzes text for indicators across multiple wellness dimensions using MentaLLaMA model

**Request Schema**:
```json
{
  "text_content": "string",
  "analysis_parameters": {
    "dimensions": ["emotional", "social", "physical", "spiritual", "intellectual"],
    "include_recommendations": true
  },
  "processing_mode": "sync"  // or "async"
}
```

**Response Schema**:
```json
{
  "request_id": "uuid-string",
  "status": "completed",  // or "processing" if async
  "result": {
    "dimension_scores": {
      "emotional": 0.4,  // 0.0 to 1.0
      "social": 0.65,
      "physical": 0.75,
      "spiritual": 0.3,
      "intellectual": 0.6
    },
    "areas_of_strength": [
      "physical wellness",
      "social engagement"
    ],
    "areas_for_improvement": [
      "emotional wellbeing",
      "spiritual connection"
    ],
    "recommendations": [
      "Consider mindfulness practices to improve emotional regulation",
      "Explore activities that provide sense of meaning and purpose"
    ]
  },
  "model_version": "MentaLLaMA-33B-lora-v1.0",
  "processing_time_ms": 1450
}
```

### 2. PHI Detection Service

**Base URL**: `/api/v1/ml/phi-detection`

#### Endpoints:

##### Detect and Mask PHI

```
POST /detect-and-mask
```

**Description**: Detects and masks Protected Health Information in text

**Request Schema**:
```json
{
  "text_content": "string",
  "detection_level": "strict",  // standard, strict
  "mask_format": "token",  // token, redaction
  "include_detection_metadata": true
}
```

**Response Schema**:
```json
{
  "request_id": "uuid-string",
  "status": "completed",
  "result": {
    "masked_text": "Hi, my name is [NAME] and I live in [LOCATION]. I was diagnosed with depression by Dr. [NAME] on [DATE].",
    "phi_detected": true,
    "detection_metadata": {
      "entity_counts": {
        "NAME": 2,
        "LOCATION": 1,
        "DATE": 1
      },
      "detection_score": 0.98,
      "confidence_by_entity": {
        "NAME_1": 0.99,
        "NAME_2": 0.97,
        "LOCATION": 0.98,
        "DATE": 0.99
      }
    }
  },
  "processing_time_ms": 320
}
```

### 3. Digital Twin Analysis Service

**Base URL**: `/api/v1/ml/digital-twin`

#### Endpoints:

##### Analyze for Digital Twin

```
POST /analyze
```

**Description**: Perform comprehensive analysis for the Digital Twin, combining multiple MentaLLaMA analyses

**Request Schema**:
```json
{
  "patient_id": "uuid-string",
  "source_type": "journal_entry",  // journal_entry, session_notes, assessment
  "text_content": "string",
  "analysis_types": [
    "depression_detection",
    "risk_assessment",
    "sentiment_analysis",
    "wellness_dimensions"
  ],
  "processing_mode": "async"  // async recommended for comprehensive analysis
}
```

**Response Schema**:
```json
{
  "request_id": "uuid-string",
  "status": "processing",  // or "completed"
  "task_id": "uuid-string",  // for checking status
  "estimated_completion_time": "2025-03-28T10:45:00Z"
}
```

##### Check Analysis Status

```
GET /analysis-status/{task_id}
```

**Description**: Check the status of an asynchronous Digital Twin analysis

**Response Schema**:
```json
{
  "task_id": "uuid-string",
  "status": "completed",  // processing, completed, failed
  "progress": 100,  // percentage
  "analyses_completed": [
    "depression_detection",
    "risk_assessment",
    "sentiment_analysis",
    "wellness_dimensions"
  ],
  "estimated_completion_time": null,  // or timestamp if still processing
  "result_url": "/api/v1/ml/digital-twin/results/uuid-string",  // only when completed
  "error": null  // or error message if failed
}
```

##### Get Analysis Results

```
GET /results/{result_id}
```

**Description**: Retrieve results of a completed Digital Twin analysis

**Response Schema**:
```json
{
  "result_id": "uuid-string",
  "patient_id": "uuid-string",
  "source_type": "journal_entry",
  "timestamp": "2025-03-28T10:45:00Z",
  "analyses": {
    "depression_detection": {
      // depression detection result (same format as standalone endpoint)
    },
    "risk_assessment": {
      // risk assessment result (same format as standalone endpoint)
    },
    "sentiment_analysis": {
      // sentiment analysis result (same format as standalone endpoint)
    },
    "wellness_dimensions": {
      // wellness dimensions result (same format as standalone endpoint)
    }
  },
  "comprehensive_insights": {
    "summary": "Patient shows moderate depressive symptoms with low suicide risk. Key concerns include sleep disturbance and social withdrawal. Emotional wellness is the primary area needing improvement.",
    "notable_patterns": [
      "Depressive symptoms consistently mentioned in morning journal entries",
      "Social engagement shows improvement compared to previous analyses"
    ],
    "suggested_focus_areas": [
      "Sleep hygiene",
      "Emotional regulation techniques"
    ]
  },
  "model_version": "MentaLLaMA-33B-lora-v1.0"
}
```

## Security and Authentication

### Authentication

All ML microservice endpoints require authentication using JSON Web Tokens (JWT):

1. **Token Issuance**: JWTs are issued by the main authentication service (AWS Cognito)
2. **Required Claims**:
   - `sub`: Subject (user ID)
   - `roles`: User roles (clinician, admin, patient)
   - `exp`: Expiration time
   - `scope`: API access scope

3. **Token Validation**:
   - Signature verification
   - Expiration check
   - Scope validation
   - Role authorization

### Authorization

Access to ML endpoints follows a strict role-based authorization model:

| Endpoint                  | Clinician | Admin | Patient | Notes                                  |
|---------------------------|-----------|-------|---------|----------------------------------------|
| Depression Detection      | ✓         | ✓     | ✗       | Clinicians only                        |
| Risk Assessment           | ✓         | ✓     | ✗       | Clinicians only                        |
| Sentiment Analysis        | ✓         | ✓     | ✗       | Clinicians only                        |
| Wellness Dimensions       | ✓         | ✓     | ✗       | Clinicians only                        |
| PHI Detection & Masking   | ✓         | ✓     | ✓       | Patient can use for own content only   |
| Digital Twin Analysis     | ✓         | ✓     | ✗       | Clinicians only, with patient access   |
| Analysis Status Check     | ✓         | ✓     | ✗       | Matches access of the original request |
| Get Analysis Results      | ✓         | ✓     | ✗       | Matches access of the original request |

### Data Protection

1. **In Transit**:
   - All API communication uses TLS 1.3
   - Certificate pinning for sensitive operations
   - Secure cipher suites only

2. **At Rest**:
   - All stored analysis results encrypted with AWS KMS
   - Key rotation policy
   - Access logs encrypted

3. **PHI Handling**:
   - All text content processed through PHI detection before analysis
   - PHI detection happens before any ML processing
   - Original text never stored with analysis results
   - Analysis logs contain only metadata, never content

## Error Handling

All API endpoints use consistent error response formats:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field_name": "Additional error context"
    },
    "request_id": "uuid-string"
  }
}
```

### Common Error Codes

| HTTP Status | Error Code                  | Description                                           |
|-------------|----------------------------|-------------------------------------------------------|
| 400         | INVALID_REQUEST            | Malformed request or invalid parameters               |
| 401         | UNAUTHORIZED               | Missing or invalid authentication                     |
| 403         | FORBIDDEN                  | Insufficient permissions                              |
| 404         | RESOURCE_NOT_FOUND         | Requested resource does not exist                     |
| 409         | CONFLICT                   | Request conflicts with current state                  |
| 422         | UNPROCESSABLE_ENTITY       | Request validation failed                             |
| 429         | RATE_LIMIT_EXCEEDED        | Too many requests                                     |
| 500         | INTERNAL_ERROR             | Server error processing request                       |
| 503         | SERVICE_UNAVAILABLE        | Service temporarily unavailable                       |
| 504         | GATEWAY_TIMEOUT            | Request timed out                                      |

### ML-Specific Error Codes

| HTTP Status | Error Code                  | Description                                           |
|-------------|----------------------------|-------------------------------------------------------|
| 400         | TEXT_TOO_LONG              | Input text exceeds maximum length                     |
| 400         | TEXT_TOO_SHORT             | Input text below minimum length for analysis          |
| 422         | PHI_DETECTION_FAILED       | PHI detection service encountered an error            |
| 422         | ANALYSIS_FAILED            | ML model analysis failed                              |
| 422         | INSUFFICIENT_TEXT_QUALITY  | Text does not contain sufficient content for analysis |
| 502         | MODEL_UNAVAILABLE          | ML model currently unavailable                        |
| 503         | ANALYSIS_QUEUE_FULL        | Analysis queue at capacity                            |

## Rate Limiting

Rate limits are enforced at the API Gateway level:

| Endpoint Category          | Limit Type      | Clinician    | Admin        | Patient      |
|----------------------------|-----------------|--------------|--------------|--------------|
| Analysis Endpoints         | Requests/Minute | 30           | 60           | 10           |
| Analysis Endpoints         | Requests/Hour   | 500          | 1000         | 100          |
| PHI Detection              | Requests/Minute | 60           | 100          | 20           |
| Digital Twin Analysis      | Requests/Minute | 15           | 30           | N/A          |
| Status Check Endpoints     | Requests/Minute | 120          | 240          | 30           |

Rate limit headers included in all responses:
- `X-RateLimit-Limit`: Rate limit ceiling
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

## Asynchronous Processing

For long-running analysis operations, asynchronous processing is recommended:

1. **Request Flow**:
   - Client makes request with `"processing_mode": "async"`
   - Server returns immediately with a task ID
   - Client polls status endpoint or receives webhook notification
   - Results retrieved when processing complete

2. **Webhook Notifications** (optional):
   - Client can provide `webhook_url` in request
   - Server POSTs status updates to webhook URL
   - Authentication via shared secret or JWT
   - Retry with exponential backoff for failed notifications

3. **Status Polling**:
   - Check status via `/analysis-status/{task_id}`
   - Recommended polling interval: 5-10 seconds
   - Status includes estimated completion time

## Integration Examples

### Example 1: Depression Screening Analysis with PHI Protection

**Step 1**: Detect and mask PHI in patient journal entry

```http
POST /api/v1/ml/phi-detection/detect-and-mask
Authorization: Bearer eyJhbGciOiJ...
Content-Type: application/json

{
  "text_content": "Yesterday I told Dr. Smith at Chicago Memorial that I've been feeling very sad for the past 3 weeks. I can't sleep well and don't enjoy activities anymore.",
  "detection_level": "strict",
  "mask_format": "token",
  "include_detection_metadata": false
}
```

**Response**:
```json
{
  "request_id": "f67a1c4b-8d5e-4abe-a861-32bcfe6f7893",
  "status": "completed",
  "result": {
    "masked_text": "Yesterday I told Dr. [NAME] at [LOCATION] that I've been feeling very sad for the past 3 weeks. I can't sleep well and don't enjoy activities anymore.",
    "phi_detected": true
  },
  "processing_time_ms": 287
}
```

**Step 2**: Perform depression detection analysis

```http
POST /api/v1/ml/mental-health/depression-detection
Authorization: Bearer eyJhbGciOiJ...
Content-Type: application/json

{
  "text_content": "Yesterday I told Dr. [NAME] at [LOCATION] that I've been feeling very sad for the past 3 weeks. I can't sleep well and don't enjoy activities anymore.",
  "analysis_parameters": {
    "include_rationale": true,
    "severity_assessment": true
  },
  "processing_mode": "sync"
}
```

**Response**:
```json
{
  "request_id": "a2c45f8d-3b7e-42c1-9d8e-2f6ab5c9e12f",
  "status": "completed",
  "result": {
    "depression_indicated": true,
    "confidence": "high",
    "severity": "moderate",
    "rationale": "The text describes persistent sadness for 3 weeks, accompanied by sleep disturbance and anhedonia (lack of enjoyment in activities). These are core symptoms of depression that have persisted for a clinically significant duration.",
    "key_indicators": [
      "persistent sadness (3 weeks)",
      "sleep disturbance",
      "anhedonia"
    ]
  },
  "model_version": "MentaLLaMA-33B-lora-v1.0",
  "processing_time_ms": 1326
}
```

### Example 2: Comprehensive Digital Twin Analysis (Asynchronous)

```http
POST /api/v1/ml/digital-twin/analyze
Authorization: Bearer eyJhbGciOiJ...
Content-Type: application/json

{
  "patient_id": "5f3a9c2d-6e8b-4a1c-bd74-8e9d5f2c62a1",
  "source_type": "journal_entry",
  "text_content": "I've been feeling much better this week. I went for a walk with my friend yesterday and actually enjoyed it. My sleep is still not great but improving. I'm starting to feel hopeful again.",
  "analysis_types": [
    "depression_detection",
    "risk_assessment",
    "sentiment_analysis",
    "wellness_dimensions"
  ],
  "processing_mode": "async",
  "webhook_url": "https://example.com/api/webhooks/analysis-completed"
}
```

**Response**:
```json
{
  "request_id": "b8c72d9e-5f1a-4e6b-9d83-7a4e5c2f18b6",
  "status": "processing",
  "task_id": "7e9d5f3a-2c8b-4d1e-9a7c-6b8e3f2d1a9c",
  "estimated_completion_time": "2025-03-28T10:45:00Z"
}
```

**Status Check**:
```http
GET /api/v1/ml/digital-twin/analysis-status/7e9d5f3a-2c8b-4d1e-9a7c-6b8e3f2d1a9c
Authorization: Bearer eyJhbGciOiJ...
```

**Status Response**:
```json
{
  "task_id": "7e9d5f3a-2c8b-4d1e-9a7c-6b8e3f2d1a9c",
  "status": "completed",
  "progress": 100,
  "analyses_completed": [
    "depression_detection",
    "risk_assessment",
    "sentiment_analysis",
    "wellness_dimensions"
  ],
  "estimated_completion_time": null,
  "result_url": "/api/v1/ml/digital-twin/results/d1e9a7c6-b8e3-4f2d-1a9c-7e9d5f3a2c8b",
  "error": null
}
```

**Results Retrieval**:
```http
GET /api/v1/ml/digital-twin/results/d1e9a7c6-b8e3-4f2d-1a9c-7e9d5f3a2c8b
Authorization: Bearer eyJhbGciOiJ...
```

(Full results response would follow the schema described in the API documentation)

## Client SDK Integration

The ML Microservices API is designed to be used with the NOVAMIND client SDK, which provides:

1. **Type-Safe Integration**:
   - TypeScript/Python SDK with full type definitions
   - Automatic request validation
   - Response parsing

2. **PHI Protection Helpers**:
   - Streamlined PHI detection workflow
   - Pre-submission validation

3. **Authentication Management**:
   - Token acquisition & refresh
   - Automatic retry on authentication failures
   - Permission checking

4. **Asynchronous Processing Utilities**:
   - Polling with configurable backoff
   - Webhook integration
   - Progress tracking

## Deployment & Scaling

The MentaLLaMA-powered ML microservices are deployed with the following infrastructure:

1. **Containerization**:
   - Docker containers for all services
   - Kubernetes orchestration
   - Auto-scaling based on demand

2. **Isolation**:
   - Separate VPC for ML services
   - Private networking between components
   - Restricted egress to necessary services only

3. **Resource Allocation**:
   - GPU instances for MentaLLaMA inference (g4dn.xlarge or higher)
   - CPU instances for API and orchestration services
   - Elastic scaling based on queue depth

## Conclusion

The NOVAMIND ML Microservices API provides a secure, scalable, and HIPAA-compliant interface to the MentaLLaMA mental health analysis capabilities. By following a clean architecture approach with clear separation of concerns, the API enables rich mental health insights while maintaining the highest standards of patient privacy and data security.

For implementation details, please refer to [ML Microservices Implementation](./09_ML_MICROSERVICES_IMPLEMENTATION.md).
