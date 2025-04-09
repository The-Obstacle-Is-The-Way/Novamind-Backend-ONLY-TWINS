# PAT Implementation Guide

## Overview

This implementation guide provides detailed instructions for integrating the Pretrained Actigraphy Transformer (PAT) into the Novamind digital twin psychiatry platform. It covers all aspects of implementation, from environment setup to code integration, testing, and deployment, ensuring HIPAA compliance and adherence to clean architecture principles.

## Prerequisites

Before implementing PAT, ensure the following prerequisites are met:

1. **Development Environment**:
   - Python 3.9+ with virtual environment
   - TensorFlow 2.18.0 with CUDA 12.2 and cuDNN 8.9
   - Boto3 1.34.0+ for AWS Bedrock support
   - FastAPI 0.109.0+ with Pydantic v2 compatibility
   - SQLAlchemy 2.0.25+ for async support
   - Docker with NVIDIA Container Toolkit
   - AWS CLI configured with appropriate permissions

2. **Knowledge Requirements**:
   - Understanding of transformer architecture
   - Experience with FastAPI and RESTful API design
   - Familiarity with AWS services (EC2, S3, DynamoDB, etc.)
   - Knowledge of HIPAA compliance requirements

3. **Access Requirements**:
   - Access to PAT model weights and configuration
   - AWS account with appropriate permissions
   - Access to the Novamind codebase repository

## Implementation Structure

### Clean Architecture Overview

The PAT integration follows clean architecture principles with distinct layers:

1. **Domain Layer**: Core business logic and entities
2. **Data Layer**: Repositories and data access
3. **Application Layer**: Use cases and services
4. **Presentation Layer**: API endpoints and controllers

### Key Components

#### 1. Interface Definition

The `PATInterface` protocol defines the contract that all PAT implementations must follow:

- Located in `app/core/services/ml/pat_interface.py`
- Defines methods for analyzing actigraphy data
- Ensures type safety and clear API boundaries
- Follows the Protocol pattern from Python's typing module

#### 2. Implementation Providers

Multiple implementations of the PAT interface are available:

- **BedrockPAT**: AWS Bedrock implementation for production
  - Located in `app/core/services/ml/providers/bedrock_pat.py`
  - Handles AWS-specific configuration and API calls
  - Implements error handling and retries for AWS service

- **MockPAT**: Mock implementation for testing
  - Located in `app/core/services/ml/providers/mock_pat.py`
  - Simulates PAT behavior without external dependencies
  - Useful for unit testing and development

#### 3. Factory Pattern

The `MLServiceFactory` creates instances of ML services:

- Located in `app/core/services/ml/factory.py`
- Provides a method for creating PAT service instances
- Handles configuration and dependency injection
- Follows the Factory pattern for object creation

#### 4. Data Models

Pydantic models for data validation:

- Input models for actigraphy data
- Output models for analysis results
- Configuration models for service settings

## Implementation Steps

### 1. Environment Setup

#### Local Development Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install required packages
pip install tensorflow==2.18.0
pip install fastapi uvicorn pydantic boto3 aiohttp
pip install pytest pytest-asyncio pytest-cov

# Install NVIDIA drivers and CUDA toolkit
# Follow NVIDIA's official documentation for your OS
```

#### Docker Development Environment

Create a `Dockerfile` for local development:

```dockerfile
FROM tensorflow/tensorflow:2.18.0-gpu

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for API
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create a `requirements.txt` file:

```
tensorflow==2.18.0
fastapi==0.109.0
uvicorn==0.24.0
pydantic==2.5.2
boto3==1.34.0
aiohttp==3.9.1
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

### 2. Code Implementation

#### Interface Definition

Create a PAT interface that extends the base MLService interface:

```python
# app/core/services/ml/pat_interface.py

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union

from app.core.services.ml.interface import MLService


class PATInterface(MLService):
    """
    Interface for Pretrained Actigraphy Transformer (PAT) services.
    
    This interface defines the contract that PAT implementations must follow.
    """
    
    @abstractmethod
    def analyze_actigraphy(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float,
        device_info: Dict[str, str],
        analysis_types: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze actigraphy data using the PAT model.
        
        Args:
            patient_id: Patient identifier
            readings: Accelerometer readings with timestamp and x,y,z values
            start_time: Start time of recording (ISO 8601 format)
            end_time: End time of recording (ISO 8601 format)
            sampling_rate_hz: Sampling rate in Hz
            device_info: Information about the device used
            analysis_types: Types of analysis to perform (e.g., "sleep", "activity", "mood")
            **kwargs: Additional parameters
            
        Returns:
            Dict containing analysis results and metadata
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If request is invalid
        """
        ...
```

#### AWS Bedrock Implementation

Implement the PAT interface using AWS Bedrock:

```python
# app/core/services/ml/providers/bedrock_pat.py

import json
import time
from typing import Any, Dict, List, Optional, Union

import boto3
from botocore.exceptions import ClientError

from app.core.exceptions import InvalidConfigurationError, ServiceUnavailableError
from app.core.services.ml.pat_interface import PATInterface
from app.core.utils.logging import get_logger


# Create logger
logger = get_logger(__name__)


class BedrockPAT(PATInterface):
    """
    AWS Bedrock implementation of the PAT interface.
    
    This class implements the PAT interface using AWS Bedrock services.
    """
    
    def __init__(self):
        """Initialize the BedrockPAT service."""
        self.bedrock_runtime = None
        self.s3_client = None
        self.dynamodb_client = None
        self.config = {}
        self.initialized = False
        self.model_mapping = {}
        self.bucket_name = ""
        self.table_name = ""
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the service with configuration.
        
        Args:
            config: Service configuration parameters
            
        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        logger.info("Initializing BedrockPAT service")
        
        # Implementation details...
```

#### Mock Implementation for Testing

Create a mock implementation for testing:

```python
# app/core/services/ml/providers/mock_pat.py

import json
import time
from datetime import datetime, timedelta
import random
from typing import Any, Dict, List, Optional, Union

from app.core.services.ml.pat_interface import PATInterface
from app.core.utils.logging import get_logger


# Create logger
logger = get_logger(__name__)


class MockPAT(PATInterface):
    """
    Mock implementation of the PAT interface.
    
    This class provides a mock implementation of the PAT interface for testing purposes.
    """
    
    # Implementation details...
```

#### Factory Integration

Update the ML service factory to include the PAT service:

```python
# app/core/services/ml/factory.py

from app.core.services.ml.interface import (
    DigitalTwinService,
    MentaLLaMAInterface,
    MLService,
    PHIDetectionService,
)
from app.core.services.ml.pat_interface import PATInterface
from app.core.services.ml.providers import (
    BedrockDigitalTwin,
    BedrockMentaLLaMA,
    BedrockPAT,
    BedrockPHIDetection,
)


class MLServiceFactory:
    """Factory for creating ML service instances."""
    
    # Existing factory methods...
    
    @classmethod
    def create_pat_service(cls, config: Optional[Dict[str, Any]] = None) -> PATInterface:
        """
        Create a PAT service instance.
        
        Args:
            config: Service configuration parameters
            
        Returns:
            Initialized PAT service
            
        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        # Get default configuration from settings
        if config is None:
            config = settings.ml_config.pat
        
        # Get provider from configuration
        provider = config.get("provider")
        if not provider:
            raise InvalidConfigurationError("Provider not specified in PAT configuration")
        
        # Create service based on provider
        if provider == "bedrock":
            service = BedrockPAT()
        elif provider == "mock":
            from app.core.services.ml.providers.mock_pat import MockPAT
            service = MockPAT()
        else:
            raise InvalidConfigurationError(f"Unsupported PAT provider: {provider}")
        
        # Initialize service
        service.initialize(config)
        
        return service
```

### 3. API Implementation

Create FastAPI endpoints for the PAT service:

```python
# app/api/routes/actigraphy.py

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.ml import get_pat_service
from app.core.exceptions import InvalidRequestError, ServiceUnavailableError
from app.core.services.ml.pat_interface import PATInterface


router = APIRouter(prefix="/api/v1/actigraphy", tags=["actigraphy"])


class AccelerometerReading(BaseModel):
    timestamp: str
    x: float
    y: float
    z: float
    source_device: Optional[str] = None


class AnalyzeRequest(BaseModel):
    patient_id: str
    readings: List[AccelerometerReading]
    start_time: str
    end_time: str
    sampling_rate_hz: float
    device_info: Dict[str, str]
    analysis_types: List[str]


@router.post("/upload", status_code=201)
async def upload_actigraphy_data(
    file: UploadFile = File(...),
    patient_id: str = Form(...),
    device_type: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    metadata: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    pat_service: PATInterface = Depends(get_pat_service)
):
    """Upload actigraphy data from wearable devices."""
    # Implementation details...


@router.post("/analyze")
async def analyze_actigraphy_data(
    request: AnalyzeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    pat_service: PATInterface = Depends(get_pat_service)
):
    """Analyze actigraphy data to extract biometric insights."""
    try:
        # Convert Pydantic model to dict
        readings = [reading.dict() for reading in request.readings]
        
        # Call PAT service
        result = pat_service.analyze_actigraphy(
            patient_id=request.patient_id,
            readings=readings,
            start_time=request.start_time,
            end_time=request.end_time,
            sampling_rate_hz=request.sampling_rate_hz,
            device_info=request.device_info,
            analysis_types=request.analysis_types
        )
        
        return result
    except ServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except InvalidRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing actigraphy data: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 4. Dependencies Configuration

Create a dependency for the PAT service:

```python
# app/api/dependencies/ml.py

from fastapi import Depends

from app.core.services.ml.factory import MLServiceFactory
from app.core.services.ml.pat_interface import PATInterface


def get_pat_service() -> PATInterface:
    """
    Get a PAT service instance.
    
    Returns:
        Initialized PAT service
    """
    return MLServiceFactory.create_pat_service()
```

### 5. Configuration Settings

Update the application settings to include PAT configuration:

```python
# app/core/config.py

class MLConfig(BaseSettings):
    # Existing ML configuration...
    
    pat: Dict[str, Any] = {
        "provider": "bedrock",
        "region": "us-east-1",
        "model_mapping": {
            "sleep": "amazon.pat-sleep-analysis-v1",
            "activity": "amazon.pat-activity-analysis-v1",
            "mood": "amazon.pat-mood-prediction-v1",
            "anomaly_detection": "amazon.pat-anomaly-detection-v1",
            "digital_twin_integration": "amazon.pat-digital-twin-v1"
        },
        "bucket_name": "novamind-actigraphy-data",
        "table_name": "novamind-actigraphy-analysis",
        "kms_key_id": "alias/novamind-actigraphy-key"
    }
```

### 6. Digital Twin Integration

Implement the integration between PAT and the Digital Twin service:

```python
# app/core/services/ml/digital_twin_integration.py

from typing import Any, Dict

from app.core.services.ml.pat_interface import PATInterface
from app.core.services.ml.interface import DigitalTwinService


class DigitalTwinIntegrator:
    """
    Integrates PAT analysis results with the Digital Twin service.
    
    This class provides methods for integrating actigraphy analysis results
    with the Digital Twin service to create a comprehensive patient profile.
    """
    
    def __init__(
        self,
        pat_service: PATInterface,
        digital_twin_service: DigitalTwinService
    ):
        """
        Initialize the integrator.
        
        Args:
            pat_service: PAT service instance
            digital_twin_service: Digital Twin service instance
        """
        self.pat_service = pat_service
        self.digital_twin_service = digital_twin_service
    
    def integrate_analysis_with_profile(
        self,
        patient_id: str,
        profile_id: str,
        actigraphy_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Integrate actigraphy analysis with a digital twin profile.
        
        Args:
            patient_id: Patient identifier
            profile_id: Digital twin profile identifier
            actigraphy_analysis: Results from actigraphy analysis
            
        Returns:
            Updated digital twin profile
        """
        # Get existing profile
        profile = self.digital_twin_service.get_patient_profile(profile_id)
        
        # Integrate actigraphy analysis
        integrated_profile = self.pat_service.integrate_with_digital_twin(
            patient_id=patient_id,
            profile_id=profile_id,
            actigraphy_analysis=actigraphy_analysis
        )
        
        # Update profile in digital twin service
        updated_profile = self.digital_twin_service.update_patient_profile(
            profile_id=profile_id,
            patient_info=integrated_profile.get("integrated_profile", {})
        )
        
        return updated_profile
```

## HIPAA Compliance

### PHI Handling

The PAT implementation adheres to strict HIPAA compliance requirements for handling Protected Health Information (PHI):

1. **Data Minimization**: Only essential PHI is collected and processed, following the principle of minimum necessary use.

2. **Data Encryption**: All PHI is encrypted both at rest and in transit using industry-standard encryption algorithms.

3. **Access Controls**: Role-based access controls restrict PHI access to authorized personnel only.

4. **Audit Trails**: Comprehensive audit logging tracks all PHI access, modifications, and transmissions.

### PHI Detection and Sanitization

The PAT service includes robust PHI detection and sanitization capabilities:

1. **Automated Detection**: The system automatically detects potential PHI in unstructured data using pattern matching and machine learning techniques.

2. **Configurable Sensitivity**: PHI detection sensitivity can be configured (strict/moderate/relaxed) based on clinical requirements.

3. **Sanitization**: Detected PHI can be automatically redacted, tokenized, or encrypted based on policy settings.

4. **Logging Protection**: All system logs are automatically sanitized to prevent accidental PHI exposure.

### AWS HIPAA Compliance

When deploying to AWS, the following HIPAA-compliant configurations are implemented:

1. **BAA Agreement**: Ensure a Business Associate Agreement (BAA) is in place with AWS.

2. **Approved Services**: Only use AWS services covered under the BAA, including:
   - Amazon Bedrock
   - Amazon S3 (with encryption)
   - Amazon RDS (with encryption)
   - AWS Lambda
   - Amazon ECS/EKS

3. **Network Security**:
   - VPC configuration with private subnets
   - Security groups with least privilege access
   - VPC endpoints for AWS services
   - Network ACLs for additional security

4. **Encryption Requirements**:
   - Server-side encryption for S3 buckets (AES-256)
   - TLS 1.2+ for all data in transit
   - KMS for key management
   - Database encryption for all RDS instances

### Compliance Monitoring

Continuous monitoring ensures ongoing HIPAA compliance:

1. **Automated Scanning**: Regular automated scans detect potential PHI leaks or compliance issues.

2. **Compliance Dashboards**: Real-time dashboards track compliance metrics and potential issues.

3. **Remediation Workflows**: Predefined workflows address compliance violations when detected.

4. **Regular Audits**: Scheduled compliance audits verify adherence to HIPAA requirements.

### Documentation and Training

Comprehensive documentation and training support HIPAA compliance:

1. **Compliance Documentation**: Detailed documentation of all HIPAA compliance measures.

2. **Developer Training**: Required training for all developers on HIPAA requirements.

3. **Incident Response**: Clear procedures for handling potential PHI breaches.

4. **Regular Updates**: Documentation is regularly updated to reflect current best practices and regulations.

## Integration with Digital Twin

### Architecture Integration

The PAT service integrates with the Novamind digital twin platform through a well-defined API layer, following these principles:

1. **Loose Coupling**: The PAT service is loosely coupled with the digital twin platform, communicating through clearly defined interfaces.

2. **Dependency Injection**: Services are injected through the dependency injection system to maintain clean architecture.

3. **Event-Driven Communication**: An event-driven approach enables asynchronous processing of actigraphy data.

### Data Flow

The integration follows this data flow pattern:

1. **Data Collection**: Actigraphy data is collected from wearable devices through the digital twin platform.

2. **Data Preprocessing**: Raw data is preprocessed to normalize formats and remove artifacts.

3. **PAT Analysis**: The PAT service analyzes the preprocessed data to extract behavioral patterns.

4. **Results Integration**: Analysis results are integrated into the patient's digital twin profile.

5. **Clinical Insights**: The digital twin platform generates clinical insights based on the PAT analysis.

### API Integration

The PAT service exposes RESTful endpoints that the digital twin platform can consume:

- **Upload Endpoint**: For submitting actigraphy data
- **Analysis Endpoint**: For requesting analysis of previously uploaded data
- **Status Endpoint**: For checking the status of ongoing analyses
- **Results Endpoint**: For retrieving completed analysis results

### Security Integration

The integration maintains HIPAA compliance through:

1. **Authentication**: JWT-based authentication for all API calls

2. **Authorization**: Role-based access control for different API endpoints

3. **Encryption**: End-to-end encryption of all patient data

4. **Audit Logging**: Comprehensive logging of all data access and modifications

### Configuration Integration

The PAT service is configured through environment variables that can be adjusted based on deployment environment:

```env
PAT_MODEL_PROVIDER=bedrock
PAT_MODEL_ID=actigraphy-transformer-v1
PAT_AWS_REGION=us-west-2
PAT_BATCH_SIZE=32
PAT_MAX_SEQUENCE_LENGTH=1024
PAT_PHI_DETECTION_LEVEL=strict

# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-west-2

# HIPAA Compliance
HIPAA_LOG_SANITIZATION_ENABLED=true
HIPAA_PHI_DETECTION_LEVEL=strict

# Example Implementation

from typing import Dict, List, Any, Optional
from app.core.services.ml.pat_interface import PATInterface
from app.core.services.ml.factory import MLServiceFactory
from app.core.config import settings

# Create PAT service instance
pat_service: PATInterface = MLServiceFactory.create_pat_service(
    config={
        "provider": settings.PAT_MODEL_PROVIDER,
        "model_id": settings.PAT_MODEL_ID,
        "region": settings.PAT_AWS_REGION,
        "batch_size": settings.PAT_BATCH_SIZE,
        "max_sequence_length": settings.PAT_MAX_SEQUENCE_LENGTH,
        "phi_detection_level": settings.PAT_PHI_DETECTION_LEVEL
    }
)

# Analyze actigraphy data
results = pat_service.analyze_actigraphy(
    patient_id="patient-123",
    readings=[
        {"timestamp": "2023-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3},
        {"timestamp": "2023-01-01T00:00:01Z", "x": 0.2, "y": 0.3, "z": 0.4},
        # More readings...
    ],
    options={
        "include_raw_metrics": True,
        "generate_visualizations": True
    }
)

## References

- [01_PAT_ARCHITECTURE_AND_INTEGRATION.md](01_PAT_ARCHITECTURE_AND_INTEGRATION.md)
- [02_PAT_AWS_DEPLOYMENT_HIPAA.md](02_PAT_AWS_DEPLOYMENT_HIPAA.md)
- [04_PAT_MICROSERVICE_API.md](04_PAT_MICROSERVICE_API.md)

## Appendix A: Code Examples

### Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with the following configuration:

```env
# PAT Configuration
PAT_MODEL_PROVIDER=bedrock
PAT_MODEL_ID=actigraphy-transformer-v1
PAT_AWS_REGION=us-west-2
PAT_BATCH_SIZE=32
PAT_MAX_SEQUENCE_LENGTH=1024
PAT_PHI_DETECTION_LEVEL=strict

# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-west-2

# HIPAA Compliance
HIPAA_LOG_SANITIZATION_ENABLED=true
HIPAA_PHI_DETECTION_LEVEL=strict
```

### Example Implementation

```python
from typing import Dict, List, Any, Optional
from app.core.services.ml.pat_interface import PATInterface
from app.core.services.ml.factory import MLServiceFactory
from app.core.config import settings

# Create PAT service instance
pat_service: PATInterface = MLServiceFactory.create_pat_service(
    config={
        "provider": settings.PAT_MODEL_PROVIDER,
        "model_id": settings.PAT_MODEL_ID,
        "region": settings.PAT_AWS_REGION,
        "batch_size": settings.PAT_BATCH_SIZE,
        "max_sequence_length": settings.PAT_MAX_SEQUENCE_LENGTH,
        "phi_detection_level": settings.PAT_PHI_DETECTION_LEVEL
    }
)

# Analyze actigraphy data
results = pat_service.analyze_actigraphy(
    patient_id="patient-123",
    readings=[
        {"timestamp": "2023-01-01T00:00:00Z", "x": 0.1, "y": 0.2, "z": 0.3},
        {"timestamp": "2023-01-01T00:00:01Z", "x": 0.2, "y": 0.3, "z": 0.4},
        # More readings...
    ],
    options={
        "include_raw_metrics": True,
        "generate_visualizations": True
    }
)
```

## Testing Strategy

### Unit Testing

Create unit tests for the PAT service:

```python
# tests/unit/services/ml/test_pat_service.py

import pytest
from unittest.mock import MagicMock, patch

from app.core.services.ml.providers.mock_pat import MockPAT


@pytest.fixture
def mock_pat_service():
    """Create a mock PAT service for testing."""
    service = MockPAT()
    service.initialize({})
    return service


def test_analyze_actigraphy(mock_pat_service):
    """Test analyzing actigraphy data."""
    # Prepare test data
    patient_id = "test-patient"
    readings = [
        {
            "timestamp": "2025-03-28T12:00:00Z",
            "x": 0.1,
            "y": 0.2,
            "z": 0.9
        }
    ]
    
    # Call service
    result = mock_pat_service.analyze_actigraphy(
        patient_id=patient_id,
        readings=readings,
        start_time="2025-03-28T12:00:00Z",
        end_time="2025-03-28T13:00:00Z",
        sampling_rate_hz=30.0,
        device_info={"type": "fitbit", "model": "sense"},
        analysis_types=["sleep", "activity"]
    )
    
    # Verify result
    assert result["patient_id"] == patient_id
    assert "analysis_id" in result
    assert "results" in result
    assert "sleep" in result["results"]
    assert "activity" in result["results"]
```

### Integration Testing

Create integration tests for the PAT API:

```python
# tests/integration/api/test_actigraphy_api.py

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    # Mock authentication logic
    return {"Authorization": "Bearer test-token"}


def test_analyze_actigraphy_endpoint(auth_headers):
    """Test the analyze actigraphy endpoint."""
    # Prepare test data
    request_data = {
        "patient_id": "test-patient",
        "readings": [
            {
                "timestamp": "2025-03-28T12:00:00Z",
                "x": 0.1,
                "y": 0.2,
                "z": 0.9,
                "source_device": "fitbit"
            }
        ],
        "start_time": "2025-03-28T12:00:00Z",
        "end_time": "2025-03-28T13:00:00Z",
        "sampling_rate_hz": 30.0,
        "device_info": {"type": "fitbit", "model": "sense"},
        "analysis_types": ["sleep", "activity"]
    }
    
    # Call API
    response = client.post(
        "/api/v1/actigraphy/analyze",
        json=request_data,
        headers=auth_headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "test-patient"
    assert "analysis_id" in data
    assert "results" in data
```

## Deployment

### Docker Deployment

Create a production-ready Dockerfile:

```dockerfile
FROM tensorflow/tensorflow:2.18.0-gpu

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV MODULE_NAME="app.main"
ENV VARIABLE_NAME="app"
ENV PORT=8000

# Expose port for API
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### AWS Deployment

Follow these steps to deploy the PAT service on AWS:

1. Build and push the Docker image to ECR:

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build the Docker image
docker build -t novamind-pat .

# Tag the image
docker tag novamind-pat:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/novamind-pat:latest

# Push the image to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/novamind-pat:latest
```

2. Create an ECS task definition:

```json
{
  "family": "novamind-pat",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<account-id>:role/novamind-pat-task-role",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "novamind-pat",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/novamind-pat:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/novamind-pat",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {
          "name": "AWS_REGION",
          "value": "us-east-1"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:ssm:us-east-1:<account-id>:parameter/novamind/database_url"
        }
      ],
      "resourceRequirements": [
        {
          "type": "GPU",
          "value": "1"
        }
      ]
    }
  ],
  "requiresCompatibilities": [
    "FARGATE"
  ],
  "cpu": "4096",
  "memory": "16384"
}
```

3. Create an ECS service:

```json
{
  "cluster": "novamind-cluster",
  "serviceName": "novamind-pat-service",
  "taskDefinition": "novamind-pat",
  "desiredCount": 2,
  "launchType": "FARGATE",
  "platformVersion": "LATEST",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": [
        "subnet-12345678",
        "subnet-87654321"
      ],
      "securityGroups": [
        "sg-12345678"
      ],
      "assignPublicIp": "DISABLED"
    }
  },
  "loadBalancers": [
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/novamind-pat/12345678",
      "containerName": "novamind-pat",
      "containerPort": 8000
    }
  ],
  "healthCheckGracePeriodSeconds": 60,
  "schedulingStrategy": "REPLICA",
  "deploymentController": {
    "type": "ECS"
  },
  "enableECSManagedTags": true,
  "propagateTags": "SERVICE"
}
```

## Conclusion

This implementation guide provides a comprehensive approach to integrating the Pretrained Actigraphy Transformer (PAT) into the Novamind digital twin psychiatry platform. By following these guidelines, you can ensure that the PAT component is implemented in a way that is HIPAA-compliant, follows clean architecture principles, and integrates seamlessly with the existing digital twin architecture.

For additional information, refer to the following documents:
- [01_PAT_ARCHITECTURE_AND_INTEGRATION.md](01_PAT_ARCHITECTURE_AND_INTEGRATION.md)
- [02_PAT_AWS_DEPLOYMENT_HIPAA.md](02_PAT_AWS_DEPLOYMENT_HIPAA.md)
- [04_PAT_MICROSERVICE_API.md](04_PAT_MICROSERVICE_API.md)
