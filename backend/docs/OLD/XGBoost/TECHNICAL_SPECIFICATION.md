# XGBoost Service Technical Specification

## 1. Introduction

This document provides a comprehensive technical specification for the XGBoost machine learning service within the Concierge Psychiatry Platform. The XGBoost service employs gradient-boosted decision trees to deliver predictive analytics for psychiatric risk assessment, treatment response forecasting, and clinical outcome prediction while maintaining strict HIPAA compliance.

## 2. Architecture Overview

### 2.1 Clean Architecture Implementation

The XGBoost service follows Clean Architecture (Onion/Hexagonal) principles with the following layers:

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    API Layer                          │  │
│  │  FastAPI Routes (xgboost.py)                         │  │
│  │  Pydantic Schemas (xgboost.py)                       │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Service Layer                      │  │
│  │  Factory (factory.py)                                │  │
│  │                    ┌───────────────────────────────┐ │  │
│  │                    │     XGBoostInterface          │ │  │
│  │                    │     (interface.py)            │ │  │
│  │                    └───────────────┬───────────────┘ │  │
│  │                                    │                 │  │
│  │  ┌──────────────────┐  ┌───────────▼──────────────┐ │  │
│  │  │ MockXGBoostService│  │   AWSXGBoostService     │ │  │
│  │  │   (mock.py)      │  │      (aws.py)           │ │  │
│  │  └──────────────────┘  └──────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Domain Exceptions                      │  │
│  │  (exceptions.py)                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 2.2 Design Patterns Utilized

1. **Factory Method Pattern**: 
   - Implementation: `factory.py`
   - Purpose: Creates appropriate XGBoostInterface implementation based on configuration

2. **Strategy Pattern**:
   - Implementation: `XGBoostInterface` and concrete implementations
   - Purpose: Enables swapping prediction algorithms and implementations

3. **Observer Pattern**:
   - Implementation: `PredictionObserver` interface
   - Purpose: Enables notification of prediction events to interested components

4. **Dependency Injection**:
   - Implementation: FastAPI dependency system with `get_xgboost_service()`
   - Purpose: Facilitates testing and loose coupling

### 2.3 Component Interaction

```
┌────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│                │     │                  │     │                   │
│   API Client   │────▶│   FastAPI Routes │────▶│  XGBoostInterface │
│                │     │                  │     │                   │
└────────────────┘     └──────────────────┘     └─────────┬─────────┘
                                                          │
                                                          │
                    ┌────────────────────────────────────┐│
                    │                                    ││
                    ▼                                    ▼▼
         ┌─────────────────────┐             ┌─────────────────────┐
         │                     │             │                     │
         │  MockXGBoostService │             │  AWSXGBoostService  │
         │                     │             │                     │
         └─────────────────────┘             └─────────────────────┘
                                                        │
                                                        │
                                              ┌─────────▼──────────┐
                                              │                    │
                                              │   AWS Services     │
                                              │   (SageMaker,      │
                                              │    DynamoDB, KMS)  │
                                              │                    │
                                              └────────────────────┘
```

## 3. Interface Specification

### 3.1 XGBoostInterface

```python
class XGBoostInterface(ABC):
    """Abstract interface for XGBoost prediction service."""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> 'XGBoostInterface':
        """Initialize the service with configuration."""
        pass

    @abstractmethod
    def predict_risk(
        self, 
        patient_id: str, 
        risk_type: str, 
        clinical_data: Dict[str, Any],
        demographic_data: Optional[Dict[str, Any]] = None,
        temporal_data: Optional[Dict[str, Any]] = None,
        confidence_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Predict psychiatric risk."""
        pass

    @abstractmethod
    def predict_treatment_response(
        self,
        patient_id: str,
        treatment_type: str,
        treatment_details: Dict[str, Any],
        clinical_data: Dict[str, Any],
        genetic_data: Optional[List[str]] = None,
        treatment_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Predict treatment response."""
        pass

    @abstractmethod
    def predict_outcome(
        self,
        patient_id: str,
        outcome_timeframe: Dict[str, Any],
        clinical_data: Dict[str, Any],
        treatment_plan: Dict[str, Any],
        social_determinants: Optional[Dict[str, Any]] = None,
        comorbidities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Predict psychiatric outcomes."""
        pass

    @abstractmethod
    def get_feature_importance(
        self,
        patient_id: str,
        model_type: str,
        prediction_id: str
    ) -> Dict[str, Any]:
        """Get feature importance for a prediction."""
        pass
        
    @abstractmethod
    def integrate_with_digital_twin(
        self,
        patient_id: str,
        profile_id: str,
        prediction_id: str
    ) -> Dict[str, Any]:
        """Integrate prediction with digital twin profile."""
        pass
        
    @abstractmethod
    def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get model information."""
        pass
        
    @abstractmethod
    def register_prediction_observer(self, observer: PredictionObserver) -> str:
        """Register observer for prediction notifications."""
        pass
        
    @abstractmethod
    def unregister_prediction_observer(self, observer_id: str) -> bool:
        """Unregister prediction observer."""
        pass
```

### 3.2 PredictionObserver Interface

```python
class PredictionObserver(ABC):
    """Observer interface for prediction notifications."""

    @abstractmethod
    def notify_prediction(self, prediction: Dict[str, Any]) -> None:
        """Notify observer of a new prediction."""
        pass
```

### 3.3 Factory Methods

```python
def create_xgboost_service(config: Dict[str, Any]) -> XGBoostInterface:
    """Create XGBoost service from configuration dict."""
    pass

def create_xgboost_service_from_env() -> XGBoostInterface:
    """Create XGBoost service from environment variables."""
    pass
```

## 4. Data Models

### 4.1 Input Data Structures

#### 4.1.1 Risk Prediction Input

```
{
  "patient_id": "unique-id-123",
  "risk_type": "relapse|suicide|self_harm|hospitalization|medication_nonresponse",
  "clinical_data": {
    "phq9_score": 15,
    "gad7_score": 12,
    "symptom_duration_weeks": 8,
    "previous_episodes": 2,
    "medication_adherence": 0.7,
    "substance_use": { ... },
    "sleep_patterns": { ... },
    "activity_levels": { ... }
  },
  "demographic_data": {
    "age": 35,
    "gender": "female",
    "education_level": "college"
  },
  "temporal_data": {
    "assessment_history": [ ... ],
    "symptom_trajectory": [ ... ]
  },
  "confidence_threshold": 0.7
}
```

#### 4.1.2 Treatment Response Input

```
{
  "patient_id": "unique-id-123",
  "treatment_type": "medication|psychotherapy|combined|...",
  "treatment_details": {
    "medication_class": "SSRI",
    "dosage": "20mg",
    "frequency": "daily",
    "duration_weeks": 12
  },
  "clinical_data": {
    "phq9_score": 15,
    "gad7_score": 11,
    "symptom_duration_weeks": 12,
    "previous_episodes": 1
  },
  "genetic_data": ["CYP2D6*1/*2", "CYP2C19*1/*1"],
  "treatment_history": [
    {
      "medication": "Sertraline",
      "dosage": "50mg",
      "duration_weeks": 8,
      "response": "partial",
      "side_effects": ["nausea", "insomnia"]
    }
  ]
}
```

#### 4.1.3 Outcome Prediction Input

```
{
  "patient_id": "unique-id-123",
  "outcome_timeframe": {
    "weeks": 12,
    "target_date": "2025-06-15T00:00:00Z"
  },
  "clinical_data": {
    "phq9_score": 14,
    "gad7_score": 10,
    "symptom_duration_weeks": 10,
    "previous_episodes": 2
  },
  "treatment_plan": {
    "type": "combined",
    "intensity": "moderate",
    "medications": ["fluoxetine"],
    "therapy_type": "CBT",
    "session_frequency": "weekly"
  },
  "social_determinants": {
    "social_support": "moderate",
    "employment_status": "employed",
    "financial_stability": "stable"
  },
  "comorbidities": ["hypertension", "insomnia"]
}
```

### 4.2 Output Data Structures

#### 4.2.1 Risk Prediction Output

```
{
  "prediction_id": "risk-123456",
  "patient_id": "unique-id-123",
  "risk_type": "relapse",
  "risk_level": "moderate",
  "risk_score": 0.45,
  "confidence": 0.82,
  "factors": [
    {"name": "phq9_score", "importance": 0.7, "value": 15},
    {"name": "previous_episodes", "importance": 0.6, "value": 2},
    {"name": "medication_adherence", "importance": 0.5, "value": 0.7}
  ],
  "timestamp": "2025-03-28T12:34:56Z"
}
```

#### 4.2.2 Treatment Response Output

```
{
  "prediction_id": "treatment-123456",
  "patient_id": "unique-id-123",
  "treatment_type": "medication",
  "response_probability": 0.72,
  "estimated_efficacy": 0.68,
  "time_to_response": {
    "estimated_weeks": 4,
    "range": {"min": 2, "max": 6},
    "confidence": 0.75
  },
  "alternative_treatments": [
    {
      "treatment": "Alternative medication",
      "type": "medication",
      "probability": 0.65,
      "description": "Alternative medication option"
    }
  ],
  "confidence": 0.78,
  "factors": [
    {"name": "previous_response", "importance": 0.8, "value": "positive"},
    {"name": "symptom_duration", "importance": 0.6, "value": 12}
  ],
  "timestamp": "2025-03-28T12:34:56Z"
}
```

#### 4.2.3 Outcome Prediction Output

```
{
  "prediction_id": "outcome-123456",
  "patient_id": "unique-id-123",
  "timeframe": {"weeks": 12},
  "success_probability": 0.65,
  "predicted_outcomes": {
    "timeframe_weeks": 12,
    "symptom_reduction": {
      "percent_improvement": 60,
      "confidence": 0.75
    },
    "functional_improvement": {
      "percent_improvement": 55,
      "confidence": 0.72
    },
    "relapse_risk": {
      "probability": 0.25,
      "confidence": 0.8
    }
  },
  "key_factors": [
    {"name": "treatment_adherence", "importance": 0.85, "value": "high"},
    {"name": "social_support", "importance": 0.75, "value": "moderate"}
  ],
  "recommendations": [
    {
      "category": "medication",
      "recommendation": "Continue current medication regimen"
    },
    {
      "category": "therapy",
      "recommendation": "Increase therapy frequency"
    }
  ],
  "confidence": 0.7,
  "timestamp": "2025-03-28T12:34:56Z"
}
```

## 5. Implementation Details

### 5.1 MockXGBoostService

The mock implementation uses in-memory data structures to simulate prediction functionality:

- Stores prediction data in-memory for retrieval
- Generates deterministic but plausible prediction results
- Implements full interface for testing without external dependencies
- Simulates feature importance calculation
- Implements Observer pattern for prediction notifications
- Contains PHI detection for compliance testing

### 5.2 AWSXGBoostService

The AWS implementation leverages AWS services for production deployment:

- Uses SageMaker endpoints for model inference
- Stores prediction data in DynamoDB tables
- Encrypts PHI using KMS
- Implements PHI detection and sanitization
- Handles AWS-specific error cases
- Provides robust error handling and logging
- Includes performance optimizations like connection pooling
- Implements TTL for prediction data

### 5.3 Configuration Parameters

The service supports the following configuration parameters:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| service_type | string | Yes | "mock" | Implementation type ("aws" or "mock") |
| prediction_ttl_days | integer | No | 90 | Days to retain predictions |
| aws_region | string | Yes (for AWS) | N/A | AWS region for services |
| kms_key_id | string | Yes (for AWS) | N/A | KMS key ID for encryption |
| table_names | object | Yes (for AWS) | N/A | DynamoDB table names |
| endpoint_names | object | Yes (for AWS) | N/A | SageMaker endpoint names |

## 6. Error Handling

### 6.1 Domain Exceptions

| Exception | Description | HTTP Status |
|-----------|-------------|-------------|
| ValidationError | Invalid input data | 400 |
| DataPrivacyError | Potential PHI detected | 400 |
| ResourceNotFoundError | Requested resource not found | 404 |
| ModelNotFoundError | Requested model not found | 404 |
| ConfigurationError | Service configuration error | 500 |
| PredictionError | Error during prediction calculation | 500 |
| ServiceUnavailableError | External service unavailable | 503 |
| ThrottlingError | Rate limit exceeded | 429 |

### 6.2 Exception Flow

```
Client Request
    │
    ▼
FastAPI Route
    │
    ▼
Domain Exception (if any)
    │
    ▼
HTTP Exception with appropriate status code
    │
    ▼
Client Response
```

## 7. HIPAA Compliance Features

### 7.1 PHI Protection

1. **PHI Detection**:
   - Pattern matching for common PHI elements
   - Field name analysis for PHI indicators
   - Value analysis for potential PHI content

2. **Data Encryption**:
   - Patient IDs encrypted with KMS in DynamoDB
   - All PHI stored encrypted at rest
   - All data in transit protected with TLS

3. **Log Sanitization**:
   - PHI redaction in all logs
   - Anonymized identifier usage
   - Minimal logging of sensitive operations

4. **Observer Notification Sanitization**:
   - PHI removal before notification delivery
   - Redacted patient IDs in notifications

### 7.2 Access Controls

1. **Authentication**:
   - JWT token validation for all endpoints
   - Token validation through AWS Cognito

2. **Authorization**:
   - Role-based access control
   - Fine-grained permission checks for operations

3. **Audit Logging**:
   - All access and operations logged
   - User identity captured for all operations
   - Timestamp and operation details recorded

## 8. Performance Considerations

### 8.1 Caching Strategy

The service implements caching at multiple levels:

1. **Prediction Caching**:
   - Recent predictions cached for quick retrieval
   - Cache invalidation when PHI data changes

2. **Model Metadata Caching**:
   - Model information cached with TTL
   - Refreshed on model update or expiration

### 8.2 Scaling Approach

1. **Horizontal Scaling**:
   - Stateless service design for easy replication
   - Uses AWS auto-scaling for load management

2. **SageMaker Endpoint Scaling**:
   - Automatic scaling based on invocation metrics
   - Instance size optimization based on model complexity

### 8.3 Performance Benchmarks

Performance targets for the service:

| Operation | Target Latency | Max Load |
|-----------|----------------|----------|
| Risk Prediction | < 500ms | 100 req/sec |
| Treatment Response Prediction | < 800ms | 50 req/sec |
| Outcome Prediction | < 1000ms | 25 req/sec |
| Feature Importance Retrieval | < 200ms | 200 req/sec |
| Model Info Retrieval | < 100ms | 500 req/sec |

## 9. Testing Strategy

### 9.1 Unit Testing

Unit tests cover:

1. **Domain Logic**:
   - Input validation
   - PHI detection
   - Mock implementation correctness

2. **AWS Implementation**:
   - AWS client mocking
   - Error handling
   - Configuration validation

### 9.2 Integration Testing

Integration tests cover:

1. **API Layer**:
   - Request validation
   - Response formatting
   - Authentication and authorization
   - Error mapping

2. **Service Layer**:
   - End-to-end flow with mock service
   - Observer pattern functionality

### 9.3 Performance Testing

Performance tests evaluate:

1. **Latency**:
   - P50, P95, P99 latency metrics
   - Cold start performance

2. **Throughput**:
   - Maximum sustained requests/second
   - Error rates under load

3. **Resource Utilization**:
   - CPU and memory profiles
   - Network saturation points

## 10. Future Enhancements

Planned enhancements for future releases:

1. **Model Versioning**:
   - Support for multiple model versions
   - A/B testing of models
   - Gradual rollout of new models

2. **Federated Learning Support**:
   - Privacy-preserving model updates
   - Multi-clinic learning without data sharing

3. **Explainability Enhancements**:
   - SHAP value integration
   - Natural language explanations
   - Visual explanation artifacts

4. **Real-time Prediction Updates**:
   - Streaming data integration
   - Dynamic risk re-assessment
   - Push notifications for significant changes

## 11. References

1. XGBoost Documentation: [https://xgboost.readthedocs.io/](https://xgboost.readthedocs.io/)
2. AWS SageMaker Documentation: [https://docs.aws.amazon.com/sagemaker/](https://docs.aws.amazon.com/sagemaker/)
3. HIPAA Security Rule: [https://www.hhs.gov/hipaa/for-professionals/security/](https://www.hhs.gov/hipaa/for-professionals/security/)
4. Clean Architecture: Martin, R. C. (2017). Clean Architecture: A Craftsman's Guide to Software Structure and Design.
5. Design Patterns: Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). Design Patterns: Elements of Reusable Object-Oriented Software.