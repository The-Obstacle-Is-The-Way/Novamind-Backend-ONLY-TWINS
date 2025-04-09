# TESTING FRAMEWORK AND REQUIREMENTS

## Overview

This document outlines the testing framework and requirements for the NOVAMIND platform. It provides a comprehensive guide to setting up and running tests, ensuring that the dependency injection system and all other components work flawlessly.

## 1. Testing Dependencies

The following dependencies are required for testing the NOVAMIND platform:

```python
# requirements-dev.txt

# Testing
pytest==7.4.2
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-xdist==3.3.1
hypothesis==6.88.1
coverage==7.3.2

# Linting and Formatting
black==23.9.1
flake8==6.1.0
mypy==1.6.1
isort==5.12.0
bandit==1.7.5
safety==2.3.5

# Type Checking
types-requests==2.31.0.2
types-PyYAML==6.0.12.12
sqlalchemy-stubs==0.4.0

# Documentation
sphinx==7.2.6
sphinx-rtd-theme==1.3.0
```

## 2. Test Directory Structure

The test directory structure should mirror the application structure:

```
tests/
├── conftest.py                  # Shared fixtures
├── unit/                        # Unit tests
│   ├── domain/                  # Domain layer tests
│   │   ├── entities/            # Entity tests
│   │   ├── services/            # Domain service tests
│   │   └── repositories/        # Repository interface tests
│   ├── application/             # Application layer tests
│   │   ├── services/            # Application service tests
│   │   └── use_cases/           # Use case tests
│   └── infrastructure/          # Infrastructure layer tests
│       ├── persistence/         # Persistence tests
│       ├── security/            # Security tests
│       └── di/                  # Dependency injection tests
├── integration/                 # Integration tests
│   ├── persistence/             # Database integration tests
│   ├── api/                     # API integration tests
│   └── external/                # External service integration tests
└── e2e/                         # End-to-end tests
    └── api/                     # API end-to-end tests
```

## 3. Test Configuration

### pytest.ini

Create a `pytest.ini` file in the root directory:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
    dependency_injection: Tests for the dependency injection system
```

### conftest.py

Create a `conftest.py` file in the tests directory:

```python
# tests/conftest.py

import os
import pytest
from typing import Dict, Any

from app.core.config import Config
from app.infrastructure.di.container import Container
from app.infrastructure.persistence.sqlalchemy.config.database import Database

@pytest.fixture
def test_config() -> Config:
    """
    Create a test configuration.
    
    Returns:
        Test configuration
    """
    return Config(
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_USERNAME="test",
        DB_PASSWORD="test",
        DB_NAME="test",
        DB_ECHO=True,
        JWT_SECRET_KEY="test_secret_key",
        JWT_ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        LOG_LEVEL="DEBUG",
        LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        LOG_FILE=None,
        AWS_ACCESS_KEY="test_access_key",
        AWS_SECRET_KEY="test_secret_key",
        AWS_REGION="us-east-1",
        AWS_S3_BUCKET="test-bucket",
        OPENAI_API_KEY="test_api_key",
        OPENAI_MODEL="gpt-4",
        SMTP_HOST="localhost",
        SMTP_PORT=25,
        SMTP_USERNAME="test",
        SMTP_PASSWORD="test",
        FROM_EMAIL="test@example.com",
        TWILIO_ACCOUNT_SID="test_account_sid",
        TWILIO_AUTH_TOKEN="test_auth_token",
        TWILIO_PHONE_NUMBER="+15555555555"
    )

@pytest.fixture
def test_database(test_config: Config) -> Database:
    """
    Create a test database.
    
    Args:
        test_config: Test configuration
        
    Returns:
        Test database
    """
    return Database(
        host=test_config.DB_HOST,
        port=test_config.DB_PORT,
        username=test_config.DB_USERNAME,
        password=test_config.DB_PASSWORD,
        database=test_config.DB_NAME,
        echo=test_config.DB_ECHO
    )

@pytest.fixture
def test_container(test_config: Config, test_database: Database) -> Container:
    """
    Create a test container with test dependencies.
    
    Args:
        test_config: Test configuration
        test_database: Test database
        
    Returns:
        Test container
    """
    container = Container(test_config)
    
    # Override the database
    container._instances["Database"] = test_database
    
    return container
```

## 4. Unit Testing

Unit tests should test individual components in isolation, with all dependencies mocked.

### Example: Testing a Use Case

```python
# tests/unit/application/use_cases/test_create_patient.py

import pytest
from unittest.mock import Mock, AsyncMock

from app.application.use_cases.patient.create_patient import CreatePatientUseCase
from app.domain.entities.patient import Patient
from app.domain.repositories.patient_repository import PatientRepository

@pytest.fixture
def mock_patient_repository():
    """
    Create a mock patient repository.
    
    Returns:
        Mock patient repository
    """
    repository = Mock(spec=PatientRepository)
    repository.create = AsyncMock()
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
    """
    Create a CreatePatientUseCase with a mock repository.
    
    Args:
        mock_patient_repository: Mock patient repository
        
    Returns:
        CreatePatientUseCase instance
    """
    return CreatePatientUseCase(patient_repository=mock_patient_repository)

@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_patient(create_patient_use_case, mock_patient_repository):
    """
    Test creating a patient.
    
    Args:
        create_patient_use_case: CreatePatientUseCase instance
        mock_patient_repository: Mock patient repository
    """
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
    mock_patient_repository.create.assert_called_once()
```

### Example: Testing the Dependency Injection Container

```python
# tests/unit/infrastructure/di/test_container.py

import pytest
from unittest.mock import Mock, patch

from app.infrastructure.di.container import Container, get_container
from app.domain.repositories.patient_repository import PatientRepository
from app.infrastructure.persistence.sqlalchemy.repositories.patient_repository import SQLAlchemyPatientRepository
from app.application.use_cases.patient.create_patient import CreatePatientUseCase

@pytest.fixture
def container(test_config):
    """
    Create a container with a test configuration.
    
    Args:
        test_config: Test configuration
        
    Returns:
        Container instance
    """
    return Container(test_config)

@pytest.mark.unit
@pytest.mark.dependency_injection
def test_get_patient_repository(container):
    """
    Test getting a patient repository.
    
    Args:
        container: Container instance
    """
    # Arrange & Act
    repository = container.get_patient_repository()
    
    # Assert
    assert isinstance(repository, PatientRepository)
    assert isinstance(repository, SQLAlchemyPatientRepository)

@pytest.mark.unit
@pytest.mark.dependency_injection
def test_get_create_patient_use_case(container):
    """
    Test getting a create patient use case.
    
    Args:
        container: Container instance
    """
    # Arrange & Act
    use_case = container.get_create_patient_use_case()
    
    # Assert
    assert isinstance(use_case, CreatePatientUseCase)
    assert isinstance(use_case._patient_repository, PatientRepository)

@pytest.mark.unit
@pytest.mark.dependency_injection
def test_singleton_behavior(container):
    """
    Test that the container returns the same instance for singletons.
    
    Args:
        container: Container instance
    """
    # Arrange & Act
    repository1 = container.get_patient_repository()
    repository2 = container.get_patient_repository()
    
    # Assert
    assert repository1 is repository2

@pytest.mark.unit
@pytest.mark.dependency_injection
def test_transient_behavior(container):
    """
    Test that the container returns a new instance for transients.
    
    Args:
        container: Container instance
    """
    # Arrange & Act
    use_case1 = container.get_create_patient_use_case()
    use_case2 = container.get_create_patient_use_case()
    
    # Assert
    assert use_case1 is not use_case2
    assert use_case1._patient_repository is use_case2._patient_repository

@pytest.mark.unit
@pytest.mark.dependency_injection
def test_get_container():
    """
    Test getting the global container instance.
    """
    # Arrange & Act
    container = get_container()
    
    # Assert
    assert container is not None
    assert isinstance(container, Container)
```

## 5. Integration Testing

Integration tests should test the interaction between components, with minimal mocking.

### Example: Testing Repository Implementation

```python
# tests/integration/persistence/test_patient_repository.py

import pytest
from uuid import uuid4

from app.domain.entities.patient import Patient
from app.infrastructure.persistence.sqlalchemy.repositories.patient_repository import SQLAlchemyPatientRepository

@pytest.fixture
async def patient_repository(test_database):
    """
    Create a patient repository with a test database.
    
    Args:
        test_database: Test database
        
    Returns:
        SQLAlchemyPatientRepository instance
    """
    repository = SQLAlchemyPatientRepository(database=test_database)
    
    # Create tables
    await test_database.create_tables()
    
    yield repository
    
    # Drop tables
    await test_database.drop_tables()

@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_patient(patient_repository):
    """
    Test creating a patient.
    
    Args:
        patient_repository: SQLAlchemyPatientRepository instance
    """
    # Arrange
    patient = Patient(
        id=str(uuid4()),
        first_name="John",
        last_name="Doe",
        date_of_birth="1980-01-01",
        contact_info={
            "email": "john.doe@example.com",
            "phone": "555-1234"
        }
    )
    
    # Act
    created_patient = await patient_repository.create(patient)
    
    # Assert
    assert created_patient.id == patient.id
    assert created_patient.first_name == patient.first_name
    assert created_patient.last_name == patient.last_name
```

## 6. End-to-End Testing

End-to-end tests should test the entire system, from the API endpoints to the database.

### Example: Testing API Endpoints

```python
# tests/e2e/api/test_patients.py

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.di.container import get_container

@pytest.fixture
def client():
    """
    Create a test client.
    
    Returns:
        TestClient instance
    """
    return TestClient(app)

@pytest.fixture
async def setup_database():
    """
    Set up the database for testing.
    """
    # Get the database
    database = get_container().get_database()
    
    # Create tables
    await database.create_tables()
    
    yield
    
    # Drop tables
    await database.drop_tables()

@pytest.mark.e2e
def test_create_patient(client, setup_database):
    """
    Test creating a patient.
    
    Args:
        client: TestClient instance
        setup_database: Database setup fixture
    """
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
    response = client.post("/api/v1/patients", json=patient_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["first_name"] == patient_data["first_name"]
    assert response.json()["last_name"] == patient_data["last_name"]
```

## 7. Running Tests

### Running All Tests

```bash
pytest
```

### Running Unit Tests

```bash
pytest -m unit
```

### Running Integration Tests

```bash
pytest -m integration
```

### Running End-to-End Tests

```bash
pytest -m e2e
```

### Running Tests with Coverage

```bash
pytest --cov=app
```

### Running Tests in Parallel

```bash
pytest -xvs -n auto
```

## 8. Continuous Integration

Set up a CI pipeline to run tests automatically on every push:

```yaml
# .github/workflows/test.yml

name: Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
        pip install -e .
    
    - name: Lint with flake8
      run: |
        flake8 app tests
    
    - name: Type check with mypy
      run: |
        mypy app tests
    
    - name: Test with pytest
      run: |
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Conclusion

This testing framework provides a comprehensive approach to testing the NOVAMIND platform, ensuring that the dependency injection system and all other components work flawlessly. By following these guidelines, you can create a robust, maintainable, and reliable application.