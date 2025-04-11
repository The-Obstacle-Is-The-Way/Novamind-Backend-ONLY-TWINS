# Test Infrastructure SSOT

## Overview

This document defines the canonical Single Source of Truth (SSOT) for the Novamind Digital Twin test infrastructure. It serves as the definitive reference for test organization, execution, and management.

## Directory-Based Test Organization

The Novamind test suite is organized primarily by dependency level, not by test type or architectural layer. This approach optimizes for:

1. **Test Execution Speed:** Fast tests run first, providing immediate feedback
2. **Resource Efficiency:** Tests with similar requirements run together
3. **Developer Experience:** Clear, consistent organization simplifies test development
4. **CI/CD Integration:** Progressive test execution in CI pipelines

### Three-Tier Directory Structure

All tests must be organized into one of three top-level directories based on their dependency requirements:

```
backend/app/tests/
├── standalone/  # No external dependencies
├── venv/        # Python package dependencies only
├── integration/ # External service dependencies
├── conftest.py  # Shared fixtures
└── helpers/     # Test utilities
```

#### 1. Standalone Tests (`backend/app/tests/standalone/`)

Tests that require **no external dependencies** beyond Python standard library:

- **Eligible Components:**
  - Pure business logic
  - Domain models and entities
  - Utility functions
  - Value objects
  - Core algorithms

- **Requirements:**
  - No imports beyond standard library and pytest
  - No database access
  - No file system operations
  - No network requests
  - No dependency on installed packages beyond pytest

- **Execution Environment:**
  - Can run in any Python environment with pytest
  - No container or service requirements
  - Execute first in CI pipeline
  - Should complete in seconds

#### 2. VENV Tests (`backend/app/tests/venv/`)

Tests that require **Python package dependencies but no external services**:

- **Eligible Components:**
  - Framework-dependent code (FastAPI, SQLAlchemy) with mocked backends
  - Data analysis components (numpy, pandas)
  - Tests requiring specialized libraries
  - Components with complex package dependencies

- **Requirements:**
  - Depends on installed Python packages
  - No database access (use in-memory SQLite or mocks)
  - No external service dependencies
  - May access filesystem for test data

- **Execution Environment:**
  - Requires specific virtualenv with dependencies installed
  - No container or database requirements
  - Execute after standalone tests in CI
  - Should complete in under a minute

#### 3. Integration Tests (`backend/app/tests/integration/`)

Tests that require **external services** or infrastructure:

- **Eligible Components:**
  - Database repositories
  - API endpoints
  - External service clients
  - Component-to-component integrations
  - Security and authentication flows

- **Requirements:**
  - Requires running database
  - May need API servers or external services
  - May require Docker or other containers
  - Tests full system behaviors

- **Execution Environment:**
  - Typically runs in Docker environment
  - Requires service initialization and teardown
  - Execute last in CI pipeline
  - May take several minutes to complete

### Sub-Organization Within Dependency Levels

Within each dependency level, tests should be organized to reflect the clean architecture layers:

```
backend/app/tests/standalone/
├── domain/          # Domain model tests
├── application/     # Application service tests
├── core/            # Core utility tests
└── common/          # Shared component tests

backend/app/tests/venv/
├── api/             # API tests with mocked backends
├── infrastructure/  # Infrastructure with mocked external services
├── presentation/    # Presentation layer tests
└── security/        # Security feature tests

backend/app/tests/integration/
├── api/             # API tests with real backends
├── repositories/    # Repository tests with real databases
├── e2e/             # End-to-end test flows
└── security/        # Security integration tests
```

## Test File Naming Conventions

### File Names

All test files must follow these naming conventions:

- Prefix with `test_`
- Use snake_case
- Name should indicate what is being tested
- Suffix can indicate test type for clarity

Examples:
```
test_patient_repository.py
test_auth_service.py
test_digital_twin_integration.py
```

### Class Names

Test classes should:

- Prefix with `Test`
- Use PascalCase
- Describe the component being tested
- Inherit from appropriate base classes

Examples:
```python
class TestPatientRepository(BaseRepositoryTest):
    ...

class TestAuthenticationService:
    ...
```

### Method Names

Test methods should:

- Prefix with `test_`
- Use snake_case
- Describe the scenario and expected outcome
- Be specific about what's being tested

Examples:
```python
def test_create_patient_with_valid_data_succeeds():
    ...

def test_login_with_invalid_credentials_raises_auth_error():
    ...
```

## Markers and Test Classification

With directory structure as the primary organization method, pytest markers are reserved for orthogonal concerns only:

| Marker    | Purpose                                      | Example Usage                        |
|-----------|----------------------------------------------|--------------------------------------|
| `slow`    | Tests taking >1 second even in their category| Long-running algorithmic tests       |
| `security`| Tests specifically checking security features| HIPAA compliance, encryption tests    |
| `flaky`   | Tests with occasional failures being fixed   | Tests with timing or race conditions |
| `smoke`   | Critical functionality for verification      | Core patient and auth flows          |

Example marker usage:
```python
@pytest.mark.slow
def test_complex_algorithm_with_large_dataset():
    ...

@pytest.mark.security
def test_phi_data_properly_encrypted():
    ...
```

## Test Fixtures and Utilities

### Fixture Organization

Fixtures should be organized by scope and purpose:

1. **Local fixtures** - Defined in the test file that uses them
2. **Module fixtures** - Defined in `conftest.py` in the same directory as the tests
3. **Package fixtures** - Defined in the top-level `conftest.py` for the test category
4. **Global fixtures** - Defined in the main `backend/app/tests/conftest.py`

### Standard Fixture Naming

| Fixture Type     | Naming Convention | Example            |
|------------------|-------------------|---------------------|
| Factory fixtures | `{entity}_factory`| `patient_factory`  |
| Instance fixtures| `{entity}`        | `test_patient`     |
| Repository fixtures| `{entity}_repository`| `patient_repository` |
| Service fixtures | `{name}_service`  | `auth_service`     |
| Mocks           | `mock_{dependency}`| `mock_database`    |

## Test Data Management

### Test Data Principles

1. **Isolation** - Tests should create their own data and not depend on other tests
2. **Cleanup** - Tests should clean up any created resources after execution
3. **Deterministic** - Test data should be consistent across test runs
4. **Minimal** - Use only the data needed for the specific test case
5. **No PHI** - Never use real PHI, even in secured test environments

### Test Database Management

Integration tests should use:

1. **Isolated databases** - Each test run gets its own database
2. **Migration verification** - Tests run against latest schema migrations
3. **Cleanup** - Database is dropped or cleaned after tests complete

## Test Execution Infrastructure

### Running Standalone Tests

```bash
# Run all standalone tests
python -m pytest backend/app/tests/standalone/

# Run with coverage
python -m pytest backend/app/tests/standalone/ --cov=app
```

### Running VENV Tests

```bash
# Ensure you're in the right virtualenv
python -m pytest backend/app/tests/venv/

# Run with coverage
python -m pytest backend/app/tests/venv/ --cov=app
```

### Running Integration Tests

```bash
# Start test infrastructure
docker-compose -f backend/docker-compose.test.yml up -d

# Run integration tests
docker-compose -f backend/docker-compose.test.yml exec app python -m pytest backend/app/tests/integration/

# Tear down test infrastructure
docker-compose -f backend/docker-compose.test.yml down
```

### Comprehensive Test Runner

The `run_tests.py` script provides a unified interface for test execution:

```bash
# Run all tests in dependency order
python backend/scripts/run_tests.py --all

# Run only standalone tests
python backend/scripts/run_tests.py --standalone

# Run with coverage report
python backend/scripts/run_tests.py --all --coverage

# Continue even if earlier test categories fail
python backend/scripts/run_tests.py --all --continue-on-failure
```

## CI/CD Integration

The test infrastructure is designed to integrate with CI/CD pipelines, with tests executed in dependency order:

1. **Code quality checks** (linting, type checking)
2. **Standalone tests** (fast, no dependencies)
3. **VENV tests** (if standalone pass)
4. **Integration tests** (if VENV tests pass)
5. **Security scanning and analysis**

## Test Coverage Requirements

Minimum coverage requirements:

| Component           | Coverage Target |
|---------------------|----------------|
| Domain layer        | 90%            |
| Application layer   | 85%            |
| Infrastructure layer| 75%            |
| Overall coverage    | 80%            |

Security-related code must maintain 100% test coverage.

## Implementation and Migration

The transition to this SSOT-based test organization will follow these steps:

1. **Classification** - Categorize existing tests by dependency level
2. **Migration** - Move tests to their appropriate directories
3. **Standardization** - Update naming and fixtures to follow conventions
4. **CI Integration** - Update CI pipelines to use the new structure

## Conclusion

This directory-based SSOT approach represents the official, forward-looking foundation for the Novamind test infrastructure. All new tests should follow this organization, and existing tests should be migrated to align with these principles.