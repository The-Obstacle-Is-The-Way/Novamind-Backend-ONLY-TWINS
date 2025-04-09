# DEPENDENCY INJECTION PYRAMID

## Overview

This document outlines the foundational dependency injection pyramid for the NOVAMIND platform, providing a comprehensive source of truth for all modules and their dependencies. This pyramid serves as a guide for AI agents and developers to understand how components are wired together, ensuring consistent and maintainable code.

## 1. Dependency Injection Pyramid Structure

The NOVAMIND platform follows a clean architecture approach with strict layering, where dependencies flow inward from the outer layers to the inner layers. The dependency injection pyramid reflects this architecture, with the domain layer at the core and the presentation layer at the outermost level.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                               │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     APPLICATION LAYER                           │    │
│  │                                                                 │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │                     DOMAIN LAYER                        │    │    │
│  │  │                                                         │    │    │
│  │  │   ┌─────────────────────────────────────────────────┐   │    │    │
│  │  │   │             CORE ENTITIES & VALUE OBJECTS       │   │    │    │
│  │  │   └─────────────────────────────────────────────────┘   │    │    │
│  │  │                                                         │    │    │
│  │  │   ┌─────────────────────────────────────────────────┐   │    │    │
│  │  │   │           DOMAIN REPOSITORY INTERFACES          │   │    │    │
│  │  │   └─────────────────────────────────────────────────┘   │    │    │
│  │  │                                                         │    │    │
│  │  │   ┌─────────────────────────────────────────────────┐   │    │    │
│  │  │   │               DOMAIN SERVICES                   │   │    │    │
│  │  │   └─────────────────────────────────────────────────┘   │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  │                                                                 │    │
│  │   ┌─────────────────────────────────────────────────────────┐   │    │
│  │   │                     USE CASES                           │   │    │
│  │   └─────────────────────────────────────────────────────────┘   │    │
│  │                                                                 │    │
│  │   ┌─────────────────────────────────────────────────────────┐   │    │
│  │   │               APPLICATION SERVICES                      │   │    │
│  │   └─────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     API ENDPOINTS                               │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     SCHEMAS & VALIDATORS                        │   │
│   └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                       INFRASTRUCTURE LAYER                              │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │               REPOSITORY IMPLEMENTATIONS                        │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │               EXTERNAL SERVICE ADAPTERS                         │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │               DEPENDENCY INJECTION CONTAINER                    │   │
│   └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

1. **Core Entities & Value Objects**: The foundational domain models that represent the business concepts.
2. **Domain Repository Interfaces**: Abstract interfaces defining data access operations.
3. **Domain Services**: Services that encapsulate complex domain logic.
4. **Use Cases**: Application-specific business logic that orchestrates domain entities and services.
5. **Application Services**: Services that coordinate use cases and provide additional application-level functionality.
6. **API Endpoints**: FastAPI route handlers that expose the application's functionality.
7. **Schemas & Validators**: Pydantic models for request/response validation.
8. **Repository Implementations**: Concrete implementations of the domain repository interfaces.
9. **External Service Adapters**: Adapters for external services like AWS, OpenAI, etc.
10. **Dependency Injection Container**: The container that manages all dependencies and their lifecycles.

## 2. Dependency Flow

The dependency flow in the NOVAMIND platform follows the Dependency Inversion Principle, where high-level modules depend on abstractions, not concrete implementations. This is achieved through constructor injection at all levels of the application.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DEPENDENCY FLOW                                  │
│                                                                         │
│   API Endpoints                                                         │
│        │                                                                │
│        ▼                                                                │
│   Use Cases / Application Services                                      │
│        │                                                                │
│        ▼                                                                │
│   Domain Services                                                       │
│        │                                                                │
│        ▼                                                                │
│   Repository Interfaces                                                 │
│        │                                                                │
│        ▼                                                                │
│   Repository Implementations                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

## 3. Dependency Injection Container

The Dependency Injection Container is responsible for creating and managing all dependencies in the application. It is implemented in the `app/infrastructure/di/container.py` file and follows these principles:

1. **Constructor Injection**: All dependencies are injected through constructors.
2. **No Singletons**: No hidden global state or singletons are used.
3. **Explicit Dependencies**: All dependencies are explicitly declared.
4. **Lifecycle Management**: The container manages the lifecycle of all dependencies.

## 4. FastAPI Integration

FastAPI's dependency injection system is used to wire up the dependencies at the API level. This is done using the `Depends()` function, which creates a dependency that can be injected into route handlers.

```python
from fastapi import APIRouter, Depends

from app.application.use_cases.patient.create_patient import CreatePatientUseCase
from app.infrastructure.di.container import get_container

router = APIRouter()

@router.post("/patients")
async def create_patient(
    patient_data: PatientCreate,
    use_case: CreatePatientUseCase = Depends(get_container().get_create_patient_use_case)
):
    return await use_case.execute(patient_data.dict())
```

In this example, the `get_container().get_create_patient_use_case` function returns a factory that creates a new instance of the `CreatePatientUseCase` with all its dependencies injected.# DEPENDENCY INJECTION GLOSSARY

## Overview

This document provides a comprehensive glossary of all dependency injections in the NOVAMIND platform. It serves as a reference for AI agents and developers to understand the complete dependency tree, making it easier to maintain and extend the system.

## Domain Layer Dependencies

### Domain Entities

Domain entities are the core business objects that represent the fundamental concepts in the system. They typically don't have dependencies injected into them, as they are created using constructors or factory methods.

| Entity | Description | Dependencies |
|--------|-------------|--------------|
| `Patient` | Represents a patient in the concierge psychiatry practice | None |
| `Provider` | Represents a healthcare provider | None |
| `Appointment` | Represents a scheduled appointment | None |
| `ClinicalNote` | Represents a clinical note | None |
| `Medication` | Represents a medication | None |
| `DigitalTwin` | Represents a patient's digital twin | None |

### Domain Services

Domain services encapsulate complex business logic that doesn't naturally fit within a single entity.

| Service | Description | Dependencies |
|---------|-------------|--------------|
| `PatientService` | Manages patient-related business logic | `PatientRepository`, `ProviderRepository`, `AppointmentRepository`, `ClinicalNoteRepository` |
| `AppointmentService` | Manages appointment-related business logic | `AppointmentRepository`, `PatientRepository`, `ProviderRepository` |
| `ClinicalDocumentationService` | Manages clinical documentation | `ClinicalNoteRepository`, `PatientRepository` |
| `MedicationService` | Manages medication-related business logic | `MedicationRepository`, `PatientRepository` |
| `ProviderService` | Manages provider-related business logic | `ProviderRepository` |
| `DigitalTwinService` | Manages digital twin-related business logic | `DigitalTwinRepository`, `PatientRepository` |
| `AIAssistantService` | Manages AI-assisted features | `MLServiceInterface` |
| `AnalyticsService` | Manages analytics and reporting | Various repositories |

## Application Layer Dependencies

### Use Cases

Use cases represent the application-specific business logic that orchestrates domain entities and services.

| Use Case | Description | Dependencies |
|----------|-------------|--------------|
| `CreatePatientUseCase` | Creates a new patient | `PatientRepository` |
| `CreateAppointmentUseCase` | Creates a new appointment | `AppointmentRepository`, `PatientRepository`, `ProviderRepository` |
| `GenerateDigitalTwinUseCase` | Generates a digital twin for a patient | `DigitalTwinService`, `PatientRepository` |

### Application Services

Application services coordinate use cases and provide additional application-level functionality.

| Service | Description | Dependencies |
|---------|-------------|--------------|
| `PatientService` (Application) | Orchestrates patient-related operations | `PatientRepository` |
| `DigitalTwinService` (Application) | Orchestrates digital twin operations | `DigitalTwinRepository`, `PatientRepository` |

## Infrastructure Layer Dependencies

### Repository Implementations

Repository implementations provide concrete data access mechanisms for the domain repositories.

| Repository | Description | Dependencies |
|------------|-------------|--------------|
| `SQLAlchemyPatientRepository` | SQLAlchemy implementation of `PatientRepository` | `Database` |
| `SQLAlchemyAppointmentRepository` | SQLAlchemy implementation of `AppointmentRepository` | `Database` |
| `SQLAlchemyClinicalNoteRepository` | SQLAlchemy implementation of `ClinicalNoteRepository` | `Database` |
| `SQLAlchemyMedicationRepository` | SQLAlchemy implementation of `MedicationRepository` | `Database` |
| `SQLAlchemyProviderRepository` | SQLAlchemy implementation of `ProviderRepository` | `Database` |
| `SQLAlchemyDigitalTwinRepository` | SQLAlchemy implementation of `DigitalTwinRepository` | `Database` |
| `SQLAlchemyUserRepository` | SQLAlchemy implementation of `UserRepository` | `Database` |

### External Service Adapters

External service adapters provide interfaces to external services like AWS, OpenAI, etc.

| Adapter | Description | Dependencies |
|---------|-------------|--------------|
| `S3Client` | Adapter for AWS S3 | AWS credentials |
| `GPTClient` | Adapter for OpenAI GPT | OpenAI API key |
| `EmailService` | Adapter for email services | Email configuration |
| `SMSService` | Adapter for SMS services | SMS configuration |
| `TokenHandler` | Adapter for JWT token handling | JWT configuration |
| `PasswordHandler` | Adapter for password hashing | None |
| `RoleManager` | Adapter for role-based access control | None |

### ML Services

ML services provide machine learning capabilities to the application.

| Service | Description | Dependencies |
|---------|-------------|--------------|
| `BiometricCorrelationService` | Correlates biometric data | ML models |
| `DigitalTwinIntegrationService` | Integrates digital twin data | ML models |
| `PharmacogenomicsService` | Provides pharmacogenomics insights | ML models |
| `SymptomForecastingService` | Forecasts symptoms | ML models |

## Presentation Layer Dependencies

### API Endpoints

API endpoints expose the application's functionality through HTTP endpoints.

| Endpoint | Description | Dependencies |
|----------|-------------|--------------|
| `PatientsEndpoint` | Handles patient-related requests | `CreatePatientUseCase`, `PatientService` |
| `AppointmentsEndpoint` | Handles appointment-related requests | `CreateAppointmentUseCase`, `AppointmentService` |
| `DigitalTwinsEndpoint` | Handles digital twin-related requests | `GenerateDigitalTwinUseCase`, `DigitalTwinService` |
| `AuthEndpoint` | Handles authentication requests | `TokenHandler`, `UserRepository` |

## Dependency Injection Container

The dependency injection container is responsible for creating and managing all dependencies in the application.

| Component | Description | Dependencies |
|-----------|-------------|--------------|
| `Container` | Manages all dependencies | None |
| `get_container` | Factory function for the container | None |

## Dependency Resolution Tree

The dependency resolution tree shows how dependencies are resolved from the top level (API endpoints) down to the lowest level (repositories and external services).

```
PatientsEndpoint
├── CreatePatientUseCase
│   └── PatientRepository
│       └── SQLAlchemyPatientRepository
│           └── Database
└── PatientService (Application)
    └── PatientRepository
        └── SQLAlchemyPatientRepository
            └── Database

AppointmentsEndpoint
├── CreateAppointmentUseCase
│   ├── AppointmentRepository
│   │   └── SQLAlchemyAppointmentRepository
│   │       └── Database
│   ├── PatientRepository
│   │   └── SQLAlchemyPatientRepository
│   │       └── Database
│   └── ProviderRepository
│       └── SQLAlchemyProviderRepository
│           └── Database
└── AppointmentService
    ├── AppointmentRepository
    │   └── SQLAlchemyAppointmentRepository
    │       └── Database
    ├── PatientRepository
    │   └── SQLAlchemyPatientRepository
    │       └── Database
    └── ProviderRepository
        └── SQLAlchemyProviderRepository
            └── Database

DigitalTwinsEndpoint
├── GenerateDigitalTwinUseCase
│   ├── DigitalTwinService
│   │   └── DigitalTwinRepository
│   │       └── SQLAlchemyDigitalTwinRepository
│   │           └── Database
│   └── PatientRepository
│       └── SQLAlchemyPatientRepository
│           └── Database
└── DigitalTwinService (Application)
    ├── DigitalTwinRepository
    │   └── SQLAlchemyDigitalTwinRepository
    │       └── Database
    └── PatientRepository
        └── SQLAlchemyPatientRepository
            └── Database

AuthEndpoint
├── TokenHandler
│   └── JWT configuration
└── UserRepository
    └── SQLAlchemyUserRepository
        └── Database
```

This tree illustrates how dependencies are resolved from the top level (API endpoints) down to the lowest level (repositories and external services). Each level depends on the level below it, with the container managing the creation and lifecycle of all components.# DEPENDENCY TREE CONSTRUCTION

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

This approach aligns with the platform's commitment to clean architecture, SOLID principles, and maintainable code.# DEPENDENCY INJECTION IMPLEMENTATION GUIDE

## Overview

This document provides a comprehensive implementation guide for the dependency injection system in the NOVAMIND platform. It serves as a practical guide for developers and AI agents to implement and extend the dependency injection container.

## 1. Container Implementation

The first step is to implement the dependency injection container in the `app/infrastructure/di/container.py` file. This container will be responsible for creating and managing all dependencies in the application.

```python
# app/infrastructure/di/container.py

from typing import Dict, Any, Optional

from app.core.config import Config
from app.domain.repositories.patient_repository import PatientRepository
from app.infrastructure.persistence.sqlalchemy.repositories.patient_repository import SQLAlchemyPatientRepository
from app.application.use_cases.patient.create_patient import CreatePatientUseCase

class Container:
    """Dependency Injection Container for the NOVAMIND platform"""
    
    def __init__(self, config: Config):
        """Initialize the container with configuration"""
        self.config = config
        self._instances = {}
    
    def _get_or_create(self, key: str, factory: callable) -> Any:
        """Get an instance from the cache or create it if it doesn't exist"""
        if key not in self._instances:
            self._instances[key] = factory()
        return self._instances[key]
    
    # Database
    
    def get_database(self):
        """Get the database instance"""
        return self._get_or_create(
            "Database",
            lambda: Database(
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                username=self.config.DB_USERNAME,
                password=self.config.DB_PASSWORD,
                database=self.config.DB_NAME
            )
        )
    
    # Repositories
    
    def get_patient_repository(self) -> PatientRepository:
        """Get the patient repository"""
        return self._get_or_create(
            "PatientRepository",
            lambda: SQLAlchemyPatientRepository(
                database=self.get_database()
            )
        )
    
    # Use Cases
    
    def get_create_patient_use_case(self) -> CreatePatientUseCase:
        """Get the create patient use case"""
        return CreatePatientUseCase(
            patient_repository=self.get_patient_repository()
        )

# Global container instance
_container: Optional[Container] = None

def get_container() -> Container:
    """Get the global container instance"""
    global _container
    if _container is None:
        from app.core.config import get_config
        _container = Container(get_config())
    return _container
```

## 2. FastAPI Integration

The next step is to integrate the dependency injection container with FastAPI. This is done using the `Depends()` function.

```python
# app/presentation/api/dependencies.py

from fastapi import Depends

from app.application.use_cases.patient.create_patient import CreatePatientUseCase
from app.infrastructure.di.container import get_container

def get_create_patient_use_case() -> CreatePatientUseCase:
    """Get the create patient use case"""
    return get_container().get_create_patient_use_case()

# Authentication

def get_current_user(token_handler = Depends(get_token_handler)):
    """Get the current user from the JWT token"""
    async def _get_current_user(token: str) -> dict:
        return await token_handler.decode_token(token)
    return _get_current_user

# Authorization

def require_role(role: str):
    """Require a specific role for the current user"""
    async def _require_role(
        user: dict = Depends(get_current_user_with_roles())
    ) -> dict:
        if role not in user["roles"]:
            raise HTTPException(
                status_code=403,
                detail=f"User does not have the required role: {role}"
            )
        return user
    return _require_role
```

## 3. Using Dependencies in Endpoints

Now that we have the dependency injection container and FastAPI integration, we can use dependencies in our endpoints.

```python
# app/presentation/api/v1/endpoints/patients.py

from fastapi import APIRouter, Depends, HTTPException

from app.application.use_cases.patient.create_patient import CreatePatientUseCase
from app.presentation.api.dependencies import (
    get_create_patient_use_case,
    require_role
)
from app.presentation.api.v1.schemas.patient import (
    PatientCreate,
    PatientResponse
)

router = APIRouter()

@router.post("/patients", response_model=PatientResponse)
async def create_patient(
    patient_data: PatientCreate,
    use_case: CreatePatientUseCase = Depends(get_create_patient_use_case),
    user: dict = Depends(require_role("admin"))
):
    """Create a new patient"""
    try:
        patient = await use_case.execute(patient_data.dict())
        return PatientResponse.from_entity(patient)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## 4. Testing with Dependency Injection

The dependency injection pattern makes testing easier by allowing dependencies to be mocked or replaced with test doubles.

### Unit Testing

```python
# tests/unit/application/use_cases/test_create_patient.py

import pytest
from unittest.mock import Mock, AsyncMock

from app.application.use_cases.patient.create_patient import CreatePatientUseCase
from app.domain.entities.patient import Patient
from app.domain.repositories.patient_repository import PatientRepository

@pytest.fixture
def mock_patient_repository():
    """Create a mock patient repository"""
    repository = Mock(spec=PatientRepository)
    repository.create = AsyncMock()
    repository.create.return_value = Patient(
        id="123",
        first_name="John",
        last_name="Doe",
        date_of_birth="1980-01-01"
    )
    return repository

@pytest.fixture
def create_patient_use_case(mock_patient_repository):
    """Create a CreatePatientUseCase with a mock repository"""
    return CreatePatientUseCase(patient_repository=mock_patient_repository)

@pytest.mark.asyncio
async def test_create_patient(create_patient_use_case, mock_patient_repository):
    """Test creating a patient"""
    # Arrange
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-01-01"
    }
    
    # Act
    patient = await create_patient_use_case.execute(patient_data)
    
    # Assert
    assert patient.first_name == "John"
    assert patient.last_name == "Doe"
    mock_patient_repository.create.assert_called_once()
```

### Integration Testing

```python
# tests/integration/conftest.py

import pytest

from app.infrastructure.di.container import Container
from app.core.config import get_config

@pytest.fixture
def test_database():
    """Create a test database"""
    return Database(
        host="localhost",
        port=5432,
        username="test",
        password="test",
        database="test"
    )

@pytest.fixture
def test_container(test_database):
    """Create a test container with test dependencies"""
    config = get_config()
    container = Container(config)
    
    # Override the database
    container._instances["Database"] = test_database
    
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

## 6. Extending the Container

To extend the container with new dependencies, follow these steps:

1. Add the new dependency to the container class
2. Add a dependency provider function to the dependencies module
3. Use the dependency in your endpoints

## Conclusion

This implementation guide provides a comprehensive approach to implementing dependency injection in the NOVAMIND platform. By following these guidelines, you can create a maintainable, testable, and extensible application that adheres to clean architecture principles.
# DEPENDENCY INJECTION CONCLUSION

## Overview

This document provides a conclusion to the dependency injection documentation series for the NOVAMIND platform. It summarizes the key concepts, benefits, and implementation strategies for the dependency injection system, and provides guidance for future development.

## 1. Summary of Dependency Injection Documentation

We have created a comprehensive set of documentation for the dependency injection system in the NOVAMIND platform:

1. **Dependency Injection Pyramid** ([20_DEPENDENCY_INJECTION_PYRAMID.md](20_DEPENDENCY_INJECTION_PYRAMID.md)): Provides a visual representation of the dependency injection pyramid, showing the layered architecture and how dependencies flow through the system.

2. **Dependency Injection Glossary** ([21_DEPENDENCY_INJECTION_GLOSSARY.md](21_DEPENDENCY_INJECTION_GLOSSARY.md)): Contains a detailed glossary of all dependencies in the system, organized by layer and type, with descriptions and dependency relationships.

3. **Dependency Tree Construction** ([22_DEPENDENCY_TREE_CONSTRUCTION.md](22_DEPENDENCY_TREE_CONSTRUCTION.md)): Explains how the dependency tree is constructed at runtime, including the resolution process and best practices.

4. **Dependency Injection Implementation Guide** ([23_DEPENDENCY_INJECTION_IMPLEMENTATION_GUIDE.md](23_DEPENDENCY_INJECTION_IMPLEMENTATION_GUIDE.md)): Offers a practical implementation guide with code examples for implementing the container, integrating with FastAPI, and testing.

5. **Testing Framework and Requirements** ([24_TESTING_FRAMEWORK_AND_REQUIREMENTS.md](24_TESTING_FRAMEWORK_AND_REQUIREMENTS.md)): Provides a comprehensive guide to setting up and running tests, ensuring that the dependency injection system and all other components work flawlessly.

6. **Development Environment Setup** ([25_DEVELOPMENT_ENVIRONMENT_SETUP.md](25_DEVELOPMENT_ENVIRONMENT_SETUP.md)): Offers a detailed guide to setting up the development environment, including prerequisites, repository setup, environment configuration, and IDE configuration.

7. **Deployment and CI/CD Pipeline** ([26_DEPLOYMENT_AND_CICD_PIPELINE.md](26_DEPLOYMENT_AND_CICD_PIPELINE.md)): Provides a comprehensive guide to deploying the application to production and setting up a continuous integration and continuous deployment pipeline.

8. **Implementation Checklist and Best Practices** ([27_IMPLEMENTATION_CHECKLIST_AND_BEST_PRACTICES.md](27_IMPLEMENTATION_CHECKLIST_AND_BEST_PRACTICES.md)): Contains a checklist and best practices for implementing features in the NOVAMIND platform, ensuring code quality, maintainability, and adherence to established patterns.

9. **Documentation Index** ([28_DOCUMENTATION_INDEX.md](28_DOCUMENTATION_INDEX.md)): Provides a comprehensive index of all documentation for the NOVAMIND platform, serving as a central reference point for developers and AI agents.

## 2. Key Benefits of the Dependency Injection System

The dependency injection system in the NOVAMIND platform provides several key benefits:

### 2.1. Loose Coupling

By depending on abstractions rather than concrete implementations, the system achieves loose coupling between components. This makes the code more maintainable, testable, and extensible.

```python
# Good: Depending on abstractions
class PatientService:
    def __init__(self, patient_repository: PatientRepository):
        self.patient_repository = patient_repository

# Bad: Depending on concrete implementations
class PatientService:
    def __init__(self, patient_repository: SQLAlchemyPatientRepository):
        self.patient_repository = patient_repository
```

### 2.2. Testability

The dependency injection system makes it easy to test components in isolation by allowing dependencies to be mocked or replaced with test doubles.

```python
# Testing with mocked dependencies
def test_create_patient():
    # Arrange
    mock_repository = Mock(spec=PatientRepository)
    mock_repository.create.return_value = Patient(id="123", first_name="John", last_name="Doe")
    use_case = CreatePatientUseCase(patient_repository=mock_repository)
    
    # Act
    patient = use_case.execute({"first_name": "John", "last_name": "Doe"})
    
    # Assert
    assert patient.first_name == "John"
    assert patient.last_name == "Doe"
    mock_repository.create.assert_called_once()
```

### 2.3. Maintainability

By centralizing the creation and management of dependencies in the container, the system becomes more maintainable. Changes to dependencies can be made in a single place, rather than throughout the codebase.

```python
# Container manages dependencies centrally
class Container:
    def __init__(self, config: Config):
        self.config = config
        self._instances = {}
    
    def get_patient_repository(self) -> PatientRepository:
        if "patient_repository" not in self._instances:
            self._instances["patient_repository"] = SQLAlchemyPatientRepository(
                database=self.get_database()
            )
        return self._instances["patient_repository"]
```

### 2.4. Flexibility

The dependency injection system makes it easy to swap out implementations of dependencies, enabling flexibility in the system.

```python
# Swapping implementations is easy
def get_patient_repository() -> PatientRepository:
    if config.use_mongodb:
        return MongoDBPatientRepository(database=get_mongodb_database())
    else:
        return SQLAlchemyPatientRepository(database=get_sqlalchemy_database())
```

### 2.5. Separation of Concerns

The dependency injection system helps enforce the separation of concerns in the application, with each component focused on a single responsibility.

```python
# Each component has a single responsibility
class PatientRepository:
    """Repository for patient data access"""
    
    def create(self, patient: Patient) -> Patient:
        """Create a new patient"""
        pass

class PatientService:
    """Service for patient operations"""
    
    def __init__(self, patient_repository: PatientRepository):
        self.patient_repository = patient_repository
    
    def register_patient(self, patient_data: dict) -> Patient:
        """Register a new patient"""
        patient = Patient(**patient_data)
        return self.patient_repository.create(patient)
```

## 3. Implementation Strategies

The NOVAMIND platform uses several strategies for implementing dependency injection:

### 3.1. Constructor Injection

Dependencies are injected through constructors, making them explicit and immutable.

```python
class PatientService:
    def __init__(self, patient_repository: PatientRepository):
        self.patient_repository = patient_repository
```

### 3.2. Factory Functions

Factory functions are used to create instances of components with their dependencies.

```python
def create_patient_service(patient_repository: PatientRepository) -> PatientService:
    return PatientService(patient_repository=patient_repository)
```

### 3.3. Dependency Injection Container

A container is used to manage the creation and lifecycle of dependencies.

```python
class Container:
    def __init__(self, config: Config):
        self.config = config
        self._instances = {}
    
    def get_patient_repository(self) -> PatientRepository:
        return self._get_or_create(
            "patient_repository",
            lambda: SQLAlchemyPatientRepository(database=self.get_database())
        )
    
    def _get_or_create(self, key: str, factory: callable) -> Any:
        if key not in self._instances:
            self._instances[key] = factory()
        return self._instances[key]
```

### 3.4. FastAPI Integration

FastAPI's dependency injection system is used to wire up dependencies at the API level.

```python
@router.post("/patients")
async def create_patient(
    patient_data: PatientCreate,
    use_case: CreatePatientUseCase = Depends(get_create_patient_use_case)
):
    return await use_case.execute(patient_data.dict())
```

## 4. Best Practices

The following best practices should be followed when working with the dependency injection system:

### 4.1. Depend on Abstractions

Always depend on abstractions (interfaces or abstract classes) rather than concrete implementations.

```python
# Good
def __init__(self, patient_repository: PatientRepository):
    self.patient_repository = patient_repository

# Bad
def __init__(self, patient_repository: SQLAlchemyPatientRepository):
    self.patient_repository = patient_repository
```

### 4.2. Make Dependencies Explicit

Make all dependencies explicit in the constructor, rather than creating them internally.

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

### 4.3. Use Immutable Dependencies

Treat injected dependencies as immutable, and don't allow them to be changed after initialization.

```python
# Good
def __init__(self, patient_repository: PatientRepository):
    self._patient_repository = patient_repository  # Underscore indicates private

# Bad
def set_repository(self, patient_repository: PatientRepository):
    self.patient_repository = patient_repository  # Mutable dependency
```

### 4.4. Keep the Domain Layer Pure

Keep the domain layer pure, with no dependencies on infrastructure or external frameworks.

```python
# Good: Domain entity with no external dependencies
@dataclass
class Patient:
    first_name: str
    last_name: str
    date_of_birth: date
    contact_info: ContactInfo
    id: UUID = field(default_factory=uuid4)

# Bad: Domain entity with infrastructure dependencies
@dataclass
class Patient:
    first_name: str
    last_name: str
    date_of_birth: date
    contact_info: ContactInfo
    id: UUID = field(default_factory=uuid4)
    
    def save(self, session: Session):
        # Direct dependency on SQLAlchemy
        session.add(self)
        session.commit()
```

### 4.5. Use Lazy Loading for Expensive Resources

Use lazy loading for expensive resources to improve performance.

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

## 5. Future Directions

The dependency injection system in the NOVAMIND platform is designed to be flexible and extensible. Here are some potential future directions for the system:

### 5.1. Annotation-Based Injection

Consider implementing annotation-based injection to reduce boilerplate code.

```python
# Example of annotation-based injection
@inject
class PatientService:
    @inject
    def __init__(self, patient_repository: PatientRepository):
        self.patient_repository = patient_repository
```

### 5.2. Scoped Dependencies

Implement scoped dependencies to manage the lifecycle of dependencies more granularly.

```python
# Example of scoped dependencies
class Container:
    def __init__(self, config: Config):
        self.config = config
        self._singletons = {}
        self._request_scoped = {}
    
    def get_patient_repository(self, scope: str = "singleton") -> PatientRepository:
        if scope == "singleton":
            return self._get_or_create_singleton(
                "patient_repository",
                lambda: SQLAlchemyPatientRepository(database=self.get_database())
            )
        elif scope == "request":
            return self._get_or_create_request_scoped(
                "patient_repository",
                lambda: SQLAlchemyPatientRepository(database=self.get_database())
            )
```

### 5.3. Dependency Visualization

Develop tools to visualize the dependency graph to help developers understand the relationships between components.

```python
# Example of dependency visualization
def visualize_dependencies(container: Container) -> None:
    """Generate a visualization of the dependency graph"""
    graph = {}
    for name, instance in container._instances.items():
        dependencies = []
        for attr_name, attr_value in instance.__dict__.items():
            if isinstance(attr_value, object) and not isinstance(attr_value, (str, int, float, bool, list, dict)):
                dependencies.append(attr_name)
        graph[name] = dependencies
    
    # Generate visualization using graphviz or similar
    # ...
```

### 5.4. Dependency Metrics

Implement metrics to track the usage and performance of dependencies.

```python
# Example of dependency metrics
class MetricsContainer(Container):
    def __init__(self, config: Config):
        super().__init__(config)
        self._metrics = {}
    
    def _get_or_create(self, key: str, factory: callable) -> Any:
        start_time = time.time()
        if key not in self._instances:
            self._instances[key] = factory()
            creation_time = time.time() - start_time
            self._metrics[key] = {"creation_time": creation_time, "access_count": 1}
        else:
            self._metrics[key]["access_count"] += 1
        return self._instances[key]
    
    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        return self._metrics
```

## 6. Conclusion

The dependency injection system is a critical component of the NOVAMIND platform, enabling loose coupling, testability, maintainability, flexibility, and separation of concerns. By following the best practices and implementation strategies outlined in this documentation, developers can create clean, maintainable, and extensible code that adheres to the principles of clean architecture.

The comprehensive documentation we've created provides a solid foundation for understanding and working with the dependency injection system. It covers everything from the high-level architecture to the detailed implementation, testing, and deployment strategies.

By leveraging this documentation, developers and AI agents can efficiently work with the NOVAMIND platform, ensuring that the code remains clean, maintainable, and follows the established patterns and practices.