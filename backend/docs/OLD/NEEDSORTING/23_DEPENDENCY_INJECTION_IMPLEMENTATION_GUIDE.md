# DEPENDENCY INJECTION IMPLEMENTATION GUIDE

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
