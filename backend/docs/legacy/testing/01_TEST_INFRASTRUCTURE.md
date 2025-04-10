# Novamind Digital Twin: Test Infrastructure Guide

This guide provides a comprehensive overview of the Novamind Digital Twin Backend testing infrastructure, designed to optimize test execution, organization, and CI/CD integration.

## Table of Contents

1. [Test Dependency Hierarchy](#test-dependency-hierarchy)
2. [Running Tests](#running-tests)
3. [Writing Testable Code](#writing-testable-code)
4. [CI/CD Integration](#cicd-integration)
5. [Docker Testing Environment](#docker-testing-environment)
6. [Test Classification](#test-classification)
7. [Troubleshooting](#troubleshooting)

## Test Dependency Hierarchy

Tests in the Novamind Digital Twin platform are organized into a dependency hierarchy that optimizes test execution speed and reliability:

```
Dependency Hierarchy:
┌────────────────────┐
│ Standalone Tests   │ → No external dependencies, just pure Python
├────────────────────┤
│ VENV-dependent     │ → Require Python packages but no external services
├────────────────────┤
│ DB/Service-        │ → Require database connections or external services
│ dependent          │ 
└────────────────────┘
```

### Standalone Tests

- **Location**: `backend/app/tests/standalone/`
- **Characteristics**:
  - No external dependencies beyond Python standard library
  - No database connections
  - No network calls
  - No file system operations (except reading test fixtures)
  - Fast execution (milliseconds)
  - Deterministic results
- **Use Cases**:
  - Unit tests for pure business logic
  - Data transformations
  - Validation rules
  - Utility functions
  - Model behavior

### VENV-dependent Tests

- **Location**: Various, marked with `@pytest.mark.venv_only`
- **Characteristics**:
  - Require Python packages (e.g., pytest, sqlalchemy)
  - Mock external services
  - No actual database connections or network calls
  - Medium speed execution (milliseconds to seconds)
- **Use Cases**:
  - Tests using ORM models without DB connections
  - Service layer tests with mocked repositories
  - API endpoint tests with mocked dependencies

### DB/Service-dependent Tests

- **Location**: Various, marked with `@pytest.mark.db_required`
- **Characteristics**:
  - Require actual database connections 
  - May require other external services (Redis, etc.)
  - Slower execution (seconds)
  - Potentially non-deterministic results
- **Use Cases**:
  - Repository tests
  - Database migration tests
  - Integration tests
  - End-to-end tests

## Running Tests

The Novamind Digital Twin platform provides several ways to run tests based on your needs.

### Using the Test Runner Script

The most convenient way to run tests is using the `run_tests.sh` script in the backend directory:

```bash
# Run all tests
./run_tests.sh

# Run only standalone tests
./run_tests.sh --standalone

# Run only VENV-dependent tests
./run_tests.sh --venv

# Run only DB-dependent tests
./run_tests.sh --db

# Run tests with verbose output
./run_tests.sh --verbose

# Generate XML reports
./run_tests.sh --xml

# Generate HTML coverage reports
./run_tests.sh --html

# Clean up test environment after running
./run_tests.sh --cleanup

# Set up test environment without running tests
./run_tests.sh --setup-env

# Clean up test environment without running tests
./run_tests.sh --cleanup-env

# Classify tests by dependency level
./run_tests.sh --classify

# Classify tests and update markers
./run_tests.sh --classify-update
```

### Using Python Directly

You can also run tests using the Python scripts directly:

```bash
# Run tests by dependency level
python scripts/run_tests_by_dependency.py [options]

# Classify tests
python scripts/classify_tests.py [options]
```

### Using Docker

To run tests in a containerized environment:

```bash
# Build and run the test containers
docker-compose -f docker-compose.test.yml up --build

# Run only specific test stages
docker-compose -f docker-compose.test.yml run novamind-test-runner python -m scripts.run_tests_by_dependency --standalone
```

## Writing Testable Code

To effectively leverage this test infrastructure, follow these best practices for writing testable code:

### 1. Dependency Injection

- Always inject dependencies rather than creating them directly
- Use constructor injection to make dependencies explicit
- Provide sensible defaults for optional dependencies

```python
# Good - dependencies are injected and can be mocked in tests
class UserService:
    def __init__(self, repository, notifier=None):
        self.repository = repository
        self.notifier = notifier or DefaultNotifier()
        
    async def create_user(self, user_data):
        user = await self.repository.create(user_data)
        if self.notifier:
            await self.notifier.notify_creation(user)
        return user
```

### 2. Interface Segregation

- Define clear interfaces for services and repositories
- Keep interfaces focused on specific functionality
- Use protocols or abstract base classes for interfaces

```python
from typing import Protocol, List, Optional
from datetime import datetime

class PatientRepository(Protocol):
    async def get_by_id(self, id: str) -> Optional[Patient]: ...
    async def get_all(self) -> List[Patient]: ...
    async def create(self, patient_data: dict) -> Patient: ...
    async def update(self, id: str, patient_data: dict) -> Optional[Patient]: ...
    async def delete(self, id: str) -> bool: ...
```

### 3. Pure Functions and Immutability

- Use pure functions where possible (no side effects)
- Prefer immutable data structures
- Separate data transformation from I/O operations

```python
# Pure function - easy to test
def calculate_risk_score(
    age: int, 
    medical_history: List[str], 
    vital_signs: dict
) -> float:
    """Calculate patient risk score based on factors."""
    base_score = 0.0
    
    # Age factor
    if age > 65:
        base_score += (age - 65) * 0.1
    
    # Medical history factors
    for condition in medical_history:
        if condition in HIGH_RISK_CONDITIONS:
            base_score += 2.0
        elif condition in MEDIUM_RISK_CONDITIONS:
            base_score += 1.0
    
    # Vital signs
    if vital_signs.get("blood_pressure_systolic", 120) > 140:
        base_score += 1.5
    
    return min(10.0, base_score)  # Cap at 10
```

### 4. Test-Driven Development

- Write tests before implementing functionality
- Start with standalone tests for core logic
- Add integration tests as needed

## CI/CD Integration

The Novamind Digital Twin platform uses a multi-stage CI/CD pipeline that executes tests in dependency order:

1. **Standalone Tests**: Run first for rapid feedback on basic issues
2. **VENV-dependent Tests**: Run next to verify more complex functionality
3. **DB/Service-dependent Tests**: Run last for full integration verification

### GitHub Actions Workflow

The test pipeline is configured in `.github/workflows/test-pipeline.yml` and includes:

- Three separate jobs for different test types
- Proper dependency ordering (standalone → venv → db)
- Artifact collection for test reports and coverage
- Service containers for database testing

## Docker Testing Environment

The Docker testing environment is defined in `docker-compose.test.yml` and includes:

- PostgreSQL database for test data
- Redis for caching and session management
- PgAdmin for database inspection (optional)
- Test runner container with all dependencies

### Configuration

The Docker environment is pre-configured with:

- Database credentials
- Test-specific configuration
- Volume mounts for test results
- Health checks to ensure services are ready

## Test Classification

The Novamind Digital Twin platform includes a test classification tool that automatically categorizes tests based on their dependencies.

### Running the Classifier

```bash
# Analyze tests without updating
./run_tests.sh --classify

# Analyze tests and update markers
./run_tests.sh --classify-update
```

### Classification Logic

Tests are classified based on:

1. Import statements (e.g., sqlalchemy imports suggest DB dependency)
2. Code patterns (e.g., repository usage suggests DB dependency)
3. Existing markers (if already present)

### Adding Markers Manually

You can also manually mark tests:

```python
import pytest

@pytest.mark.standalone
def test_risk_score_calculation():
    """Test the risk score calculation logic."""
    result = calculate_risk_score(70, ["diabetes"], {"blood_pressure_systolic": 145})
    assert result == 3.5

@pytest.mark.db_required
async def test_patient_repository():
    """Test the patient repository with actual database."""
    # Test code that uses the database
```

## Troubleshooting

### Common Issues

#### Test Environment Not Starting

```bash
# Check if containers are running
docker ps | grep novamind

# View container logs
docker-compose -f docker-compose.test.yml logs
```

#### Tests Failing with Database Connection Errors

Ensure the database containers are running and healthy:

```bash
# Start the test environment
./run_tests.sh --setup-env

# Check container status
docker ps | grep novamind-db-test
```

#### Classifying Tests Incorrectly

Review the test code and add markers manually:

```python
@pytest.mark.db_required  # Add this marker if the classifier missed it
async def test_database_function():
    # Test code