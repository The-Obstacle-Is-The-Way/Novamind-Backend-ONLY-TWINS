# Novamind Digital Twin: Test Infrastructure Guide

This guide provides a comprehensive overview of the Novamind Digital Twin Backend testing infrastructure, designed to optimize test execution, organization, and CI/CD integration.

## Table of Contents

1. [Test Dependency Hierarchy](#test-dependency-hierarchy)
2. [Running Tests](#running-tests)
3. [Writing New Tests](#writing-new-tests)
4. [CI/CD Integration](#cicd-integration)
5. [Docker Testing Environment](#docker-testing-environment)
6. [Test Classification](#test-classification)
7. [Development Workflow](#development-workflow)
8. [Troubleshooting](#troubleshooting)

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

# Migrate standalone tests
python scripts/test_migration/migrate_standalone_tests.py
```

### Using Docker

To run tests in a containerized environment:

```bash
# Build and run the test containers
docker-compose -f docker-compose.test.yml up --build

# Run only specific test stages
docker-compose -f docker-compose.test.yml run novamind-test-runner python -m scripts.run_tests_by_dependency --standalone
```

## Writing New Tests

When writing new tests, follow these guidelines to ensure proper organization:

### 1. Determine Dependency Level

Before writing a test, determine its dependency level:

- **Standalone**: If it has no dependencies beyond Python standard library
- **VENV-dependent**: If it requires Python packages but no external services
- **DB-dependent**: If it requires database connections or other external services

### 2. Choose the Correct Location

- **Standalone tests** should be placed in the `backend/app/tests/standalone/` directory
- **VENV-dependent** and **DB-dependent** tests can be placed in appropriate subdirectories based on what they're testing (e.g., `unit/`, `integration/`, etc.)

### 3. Add the Correct Marker

Always add the appropriate pytest marker to your test functions or classes:

```python
import pytest

@pytest.mark.standalone
def test_standalone_function():
    # Test code with no dependencies

@pytest.mark.venv_only
def test_venv_dependent_function():
    # Test code with package dependencies but no external services

@pytest.mark.db_required
def test_db_dependent_function():
    # Test code requiring database access
```

### 4. Use Dependency Injection

Make your tests more maintainable by using dependency injection:

```python
# Good - dependencies are injected and can be mocked
def test_user_service(mock_repository, mock_logger):
    service = UserService(repository=mock_repository, logger=mock_logger)
    # Test the service
```

### 5. Follow Best Practices

- Use descriptive test names that indicate what's being tested
- Keep tests focused on a single behavior or scenario
- Use appropriate fixtures for setup and teardown
- Add clear assertions with descriptive messages
- Use parameterized tests for testing multiple input/output combinations

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

The Novamind Digital Twin platform includes test classification tools that analyze and categorize tests based on their dependencies.

### Tools for Test Management

- `classify_tests.py`: Analyzes test files and determines their dependency level
- `migrate_standalone_tests.py`: Moves standalone tests to the dedicated directory
- `run_tests_by_dependency.py`: Runs tests based on their dependency level

### Classification Logic

Tests are classified based on:

1. Import statements (e.g., sqlalchemy imports suggest DB dependency)
2. Code patterns (e.g., repository usage suggests DB dependency)
3. Existing markers (if already present)
4. File location (e.g., tests in the standalone directory are classified as standalone)

## Development Workflow

The recommended workflow for development with this test infrastructure is:

1. **Write standalone tests first** for core business logic
2. **Run standalone tests frequently** during development (fast feedback)
3. **Add VENV-dependent tests** for functionality requiring packages
4. **Run VENV-dependent tests** when changing service logic
5. **Add DB-dependent tests** for integration scenarios
6. **Run DB-dependent tests** before committing changes
7. **Classify new tests** to ensure they're properly marked

This approach follows the "test pyramid" concept, with many fast, reliable unit tests at the base, fewer integration tests in the middle, and even fewer end-to-end tests at the top.

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
```

#### Missing Dependencies

If tests fail due to missing dependencies:

```bash
# Install all dependencies
pip install -r requirements.txt -r requirements-dev.txt -r requirements-test.txt
```

### Getting Help

For more assistance:

1. Check the logs to identify the specific issue
2. Review the test code for any unexpected dependencies
3. Consult the detailed documentation in the `/docs` directory
4. Reach out to the development team for complex issues