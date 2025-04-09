# DEPENDENCY TREE CONSTRUCTION

## Overview

This document explains how the dependency tree is constructed in the NOVAMIND platform. It provides a detailed guide on how dependencies are wired together, from the container configuration to the runtime resolution of dependencies.

## 1. Dependency Injection Container Implementation

The dependency injection container is implemented in the `app/infrastructure/di/container.py` file. This container is responsible for creating and managing all dependencies in the application.

### Container Structure

The container follows a modular structure, with separate methods for creating different types of dependencies:

```python
# app/infrastructure/di/container.py

from typing import Dict, Any, Callable
from sqlalchemy.orm import Session

from app.domain.repositories.patient_repository import PatientRepository
from app.infrastructure.persistence.sqlalchemy.repositories.patient_repository import SQLAlchemyPatientRepository
from app.application.use_cases.patient.create_patient import CreatePatientUseCase
# ... other imports

class Container:
    """Dependency Injection Container for the NOVAMIND platform"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the container with configuration"""
        self.config = config
        self._instances = {}
    
    # Database
    
    def get_db_session(self) -> Session:
        """Get a SQLAlchemy database session"""
        if "db_session" not in self._instances:
            # Create a new session
            from app.infrastructure.persistence.sqlalchemy.config.database import get_session
            self._instances["db_session"] = get_session()
        return self._instances["db_session"]
    
    # Repositories
    
    def get_patient_repository(self) -> PatientRepository:
        """Get the patient repository implementation"""
        if "patient_repository" not in self._instances:
            self._instances["patient_repository"] = SQLAlchemyPatientRepository(
                session=self.get_db_session()
            )
        return self._instances["patient_repository"]
    
    # ... other repository getters
    
    # Use Cases
    
    def get_create_patient_use_case(self) -> CreatePatientUseCase:
        """Get the create patient use case"""
        return CreatePatientUseCase(
            patient_repository=self.get_patient_repository()
        )
    
    # ... other use case getters
    
    # Services
    
    def get_patient_service(self) -> PatientService:
        """Get the patient service"""
        if "patient_service" not in self._instances:
            self._instances["patient_service"] = PatientService(
                patient_repository=self.get_patient_repository(),
                provider_repository=self.get_provider_repository(),
                appointment_repository=self.get_appointment_repository(),
                clinical_note_repository=self.get_clinical_note_repository()
            )
        return self._instances["patient_service"]
    
    # ... other service getters
    
    # External Services
    
    def get_s3_client(self) -> S3Client:
        """Get the S3 client"""
        if "s3_client" not in self._instances:
            self._instances["s3_client"] = S3Client(
                aws_access_key=self.config["AWS_ACCESS_KEY"],
                aws_secret_key=self.config["AWS_SECRET_KEY"],
                region=self.config["AWS_REGION"]
            )
        return self._instances["s3_client"]
    
    # ... other external service getters


# Global container instance
_container = None

def get_container() -> Container:
    """Get the global container instance"""
    global _container
    if _container is None:
        from app.core.config import get_config
        _container = Container(get_config())
    return _container
```

### Dependency Lifecycle Management

The container manages the lifecycle of dependencies using the following strategies:

1. **Singleton Dependencies**: Dependencies that should be shared across the application are stored in the `_instances` dictionary and reused.
2. **Transient Dependencies**: Dependencies that should be created anew for each request are created on-demand and not stored.

## 2. FastAPI Integration

FastAPI's dependency injection system is used to wire up the dependencies at the API level. This is done using the `Depends()` function, which creates a dependency that can be injected into route handlers.

### Endpoint Dependencies

```python
# app/presentation/api/v1/endpoints/patients.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.application.use_cases.patient.create_patient import CreatePatientUseCase
from app.infrastructure.di.container import get_container
from app.presentation.api.v1.schemas.patient import PatientCreate, PatientResponse

router = APIRouter()

@router.post("/patients", response_model=PatientResponse)
async def create_patient(
    patient_data: PatientCreate,
    use_case: CreatePatientUseCase = Depends(get_container().get_create_patient_use_case)
):
    """Create a new patient"""
    try:
        patient = await use_case.execute(patient_data.dict())
        return PatientResponse.from_entity(patient)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Middleware Dependencies

Dependencies can also be injected into middleware functions:

```python
# app/presentation/api/v1/middleware/logging_middleware.py

from fastapi import Request, Depends
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.utils.logging import Logger
from app.infrastructure.di.container import get_container

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""
    
    async def dispatch(
        self,
        request: Request,
        call_next,
        logger: Logger = Depends(get_container().get_logger)
    ):
        """Log request and response"""
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        logger.info(f"Response: {response.status_code}")
        
        return response
```

## 3. Dependency Resolution Process

The dependency resolution process follows these steps:

1. **Container Initialization**: The container is initialized with the application configuration.
2. **Dependency Registration**: Dependencies are registered in the container through getter methods.
3. **Dependency Resolution**: When a dependency is requested, the container resolves it by:
   a. Checking if it's already instantiated (for singletons)
   b. Creating it and injecting its dependencies
   c. Returning the instance

### Resolution Example

Let's trace the resolution of dependencies for the `create_patient` endpoint:

1. The endpoint requires a `CreatePatientUseCase` instance.
2. The container's `get_create_patient_use_case` method is called.
3. This method creates a new `CreatePatientUseCase` instance, injecting a `PatientRepository`.
4. To get the `PatientRepository`, the container's `get_patient_repository` method is called.
5. This method checks if a `PatientRepository` instance already exists in the `_instances` dictionary.
6. If not, it creates a new `SQLAlchemyPatientRepository` instance, injecting a database session.
7. To get the database session, the container's `get_db_session` method is called.
8. This method checks if a session already exists in the `_instances` dictionary.
9. If not, it creates a new session using the `get_session` function.
10. The session is returned to the `SQLAlchemyPatientRepository` constructor.
11. The `SQLAlchemyPatientRepository` instance is stored in the `_instances` dictionary and returned.
12. The `PatientRepository` instance is injected into the `CreatePatientUseCase` constructor.
13. The `CreatePatientUseCase` instance is returned to the endpoint.

## 4. Testing with Dependency Injection

The dependency injection pattern makes testing easier by allowing dependencies to be mocked or replaced with test doubles.

### Unit Testing

In unit tests, dependencies can be mocked using pytest's `monkeypatch` or by directly injecting mock objects:

```python
# tests/unit/application/use_cases/test_create_patient.py

import pytest
from unittest.mock import Mock

from app.application.use_cases.patient.create_patient import CreatePatientUseCase
from app.domain.entities.patient import Patient

@pytest.fixture
def mock_patient_repository():
    """Create a mock patient repository"""
    repository = Mock()
    repository.create.return_value = Patient(
        id="123",
        first_name="John",
        last_name="Doe",
        date_of_birth="1980-01-01",
        contact_info={
            "email": "john.doe@example.com",
            "phone": "555-1234"
        }
    )
    return repository

@pytest.fixture
def create_patient_use_case(mock_patient_repository):
    """Create a CreatePatientUseCase with a mock repository"""
    return CreatePatientUseCase(patient_repository=mock_patient_repository)

async def test_create_patient(create_patient_use_case):
    """Test creating a patient"""
    # Arrange
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-01-01",
        "contact_info": {
            "email": "john.doe@example.com",
            "phone": "555-1234"
        }
    }
    
    # Act
    patient = await create_patient_use_case.execute(patient_data)
    
    # Assert
    assert patient.first_name == "John"
    assert patient.last_name == "Doe"
```

### Integration Testing

In integration tests, the container can be configured to use test doubles for external dependencies:

```python
# tests/integration/conftest.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.di.container import Container
from app.core.config import get_config

@pytest.fixture
def test_db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    return Session()

@pytest.fixture
def test_container(test_db_session):
    """Create a test container with test dependencies"""
    config = get_config()
    container = Container(config)
    
    # Override the database session
    container.get_db_session = lambda: test_db_session
    
    return container
```

## 5. Best Practices

### 1. Constructor Injection

Always use constructor injection for required dependencies:

```python
class PatientService:
    def __init__(self, patient_repository: PatientRepository):
        self.patient_repository = patient_repository
```

### 2. Interface-Based Dependencies

Depend on interfaces, not concrete implementations:

```python
# Good
def __init__(self, patient_repository: PatientRepository):
    self.patient_repository = patient_repository

# Bad
def __init__(self, patient_repository: SQLAlchemyPatientRepository):
    self.patient_repository = patient_repository
```

### 3. Explicit Dependencies

Make all dependencies explicit in the constructor:

```python
# Good
def __init__(self, patient_repository: PatientRepository, logger: Logger):
    self.patient_repository = patient_repository
    self.logger = logger

# Bad
def __init__(self, patient_repository: PatientRepository):
    self.patient_repository = patient_repository
    self.logger = get_logger()  # Hidden dependency
```

### 4. Immutable Dependencies

Treat injected dependencies as immutable:

```python
# Good
def __init__(self, patient_repository: PatientRepository):
    self._patient_repository = patient_repository  # Underscore indicates private

# Bad
def set_repository(self, patient_repository: PatientRepository):
    self.patient_repository = patient_repository  # Mutable dependency
```

### 5. Lazy Loading

Use lazy loading for expensive resources:

```python
def get_s3_client(self) -> S3Client:
    """Get the S3 client"""
    if "s3_client" not in self._instances:
        self._instances["s3_client"] = S3Client(
            aws_access_key=self.config["AWS_ACCESS_KEY"],
            aws_secret_key=self.config["AWS_SECRET_KEY"],
            region=self.config["AWS_REGION"]
        )
    return self._instances["s3_client"]
```

## Conclusion

The dependency injection system in the NOVAMIND platform provides a flexible and maintainable way to manage dependencies. By following the principles outlined in this document, the platform achieves:

1. **Loose coupling**: Components depend on abstractions, not concrete implementations.
2. **Testability**: Dependencies can be easily mocked or replaced with test doubles.
3. **Maintainability**: Dependencies are explicit and managed in a central location.
4. **Flexibility**: The system can be extended with new components without modifying existing code.

This approach aligns with the platform's commitment to clean architecture, SOLID principles, and maintainable code.