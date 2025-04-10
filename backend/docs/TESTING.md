# Novamind Backend Testing Guide

This document provides comprehensive instructions for testing the Novamind backend, including setup, execution, and best practices.

## Test Architecture

The Novamind testing framework is built with the following principles:

- **Isolation**: Tests are isolated from the production environment and from each other
- **Reproducibility**: Tests produce consistent results regardless of when or where they run
- **Comprehensiveness**: Tests cover unit, integration, security, and end-to-end scenarios
- **Performance**: Tests run efficiently and can be executed in parallel
- **Observability**: Test results and coverage metrics are easily accessible

## Test Categories

### Unit Tests
- Located in `app/tests/unit/`
- Test individual components in isolation (classes, functions)
- Use mocks and stubs to isolate dependencies
- Fast execution, focused on business logic

### Integration Tests
- Located in `app/tests/integration/`
- Test interactions between components
- Use real database connections (to test database)
- Verify API contracts and data flows

### Security Tests
- Located in `app/tests/security/`
- Focus on HIPAA compliance and PHI protection
- Verify authentication, authorization, and data protection
- Audit logging and security controls

### End-to-End Tests
- Located in `app/tests/e2e/`
- Simulate real user workflows
- Test the entire system as a black box
- Verify business requirements

## Test Environment Setup

### Option 1: Docker Test Environment

The easiest way to set up the test environment is using Docker:

```bash
# Start the test environment
./scripts/run_test_environment.sh start

# Run tests in the environment
./scripts/run_test_environment.sh run

# Stop the environment when done
./scripts/run_test_environment.sh stop
```

This will:
1. Start a PostgreSQL database on port 15432
2. Start a Redis instance on port 16379
3. Set up PgAdmin on port 15050 for database inspection
4. Configure necessary environment variables

### Option 2: Manual Setup

If you prefer to set up the environment manually:

1. Set up a PostgreSQL database for testing:
   ```bash
   createdb novamind_test
   ```

2. Set the required environment variables:
   ```bash
   export TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:15432/novamind_test"
   export TEST_REDIS_URL="redis://localhost:16379/0"
   export ENVIRONMENT="test"
   export SECRET_KEY="test-secret-key"
   export ENCRYPTION_KEY="test-encryption-key"
   ```

## Running Tests

### Using the Test Runner

The `test_runner.py` script provides a flexible way to run tests:

```bash
# Run all tests with coverage reporting
python scripts/test_runner.py --coverage --html

# Run specific test groups
python scripts/test_runner.py --ml --phi --coverage

# Run specific test path
python scripts/test_runner.py --path app/tests/unit/core/services/ml/

# Run with specific module
python scripts/test_runner.py --module domain.entities.digital_twin.test_twin
```

### Command Line Options

The `test_runner.py` script supports the following options:

| Option | Description |
| ------ | ----------- |
| `--unit` | Run unit tests only |
| `--integration` | Run integration tests only |
| `--security` | Run security tests only |
| `--e2e` | Run end-to-end tests only |
| `--ml` | Run ML service tests only |
| `--phi` | Run PHI detection tests only |
| `--all` | Run all tests (default) |
| `--path PATH` | Specific test path to run |
| `--module MODULE` | Specific test module to run |
| `--coverage` | Generate coverage report |
| `--html` | Generate HTML coverage report |
| `--xml` | Generate XML coverage report |
| `--report` | Generate test report |
| `--report-dir DIR` | Directory for test reports |
| `--verbose` | Verbose output |
| `--docker` | Run in Docker test environment |
| `--target PERCENT` | Target coverage percentage (default: 80) |

### Using pytest Directly

You can also run pytest directly with more granular control:

```bash
# Run specific test file
pytest app/tests/unit/core/services/ml/test_mock.py -v

# Run with a specific marker
pytest -m "slow" app/tests/integration/

# Run with coverage
pytest --cov=app --cov-report=html app/tests/unit/
```

## Test Fixtures

### Database Fixtures

The `db_test_fixture.py` module provides fixtures for database testing:

- `setup_database` - Creates test tables once per session
- `db_session` - Provides a fresh database session for each test
- `db_transaction` - Provides a nested transaction for isolation
- `override_get_session` - Overrides the dependency injection
- `clear_tables` - Clears all tables between tests

Example usage:

```python
import pytest
from app.tests.fixtures import db_session, override_get_session

@pytest.mark.asyncio
async def test_repository(db_session):
    # Use db_session for database operations
    result = await repository.find_all(db_session)
    assert len(result) == 0
```

### Auth Fixtures

Authentication fixtures in `auth_fixtures.py`:

- `test_user` - Creates a standard test user
- `admin_user` - Creates an admin test user

### Environment Fixtures

Environment fixtures in `env_fixture.py`:

- `test_env` - Sets up a test environment with configurable variables
- `mock_env_vars` - Mocks environment variables for a test

## Writing Tests

### Unit Test Best Practices

1. **Test one thing at a time**: Each test should verify a specific behavior
2. **Use clear test names**: Name tests by the behavior they verify
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Isolate dependencies**: Use mocks or stubs for external dependencies
5. **Test edge cases**: Include tests for error conditions and edge cases

Example:

```python
@pytest.mark.asyncio
async def test_digital_twin_service_creates_session():
    # Arrange
    service = MockDigitalTwinService()
    await service.initialize({})
    
    # Act
    session_id = await service.create_session("test-patient-id")
    
    # Assert
    assert session_id is not None
    assert len(session_id) > 0
```

### Integration Test Best Practices

1. **Use real dependencies**: Test with actual database and services when possible
2. **Focus on interactions**: Verify how components work together
3. **Clean up after tests**: Ensure tests don't affect each other
4. **Test failure modes**: Verify how the system handles failures
5. **Use transactions**: Wrap tests in transactions for isolation

Example:

```python
@pytest.mark.asyncio
async def test_patient_repository_integration(db_session):
    # Arrange
    repository = PatientRepository()
    patient = Patient(id="test-id", name="Test Patient")
    
    # Act
    await repository.create(db_session, patient)
    result = await repository.get_by_id(db_session, "test-id")
    
    # Assert
    assert result is not None
    assert result.id == "test-id"
    assert result.name == "Test Patient"
```

## Testing for HIPAA Compliance

HIPAA compliance tests focus on:

1. **PHI Protection**: Verify PHI is properly identified and protected
2. **Access Controls**: Test authentication and authorization
3. **Audit Logging**: Verify access to PHI is properly logged
4. **Data Encryption**: Test encryption of PHI at rest and in transit
5. **Error Handling**: Ensure errors don't expose PHI

Example:

```python
def test_phi_redaction():
    # Arrange
    redactor = PHIRedactor()
    text = "Patient John Smith (SSN: 123-45-6789) reported symptoms."
    
    # Act
    redacted = redactor.redact(text)
    
    # Assert
    assert "John Smith" not in redacted
    assert "123-45-6789" not in redacted
    assert "[REDACTED]" in redacted
```

## Continuous Integration

The test suite is designed to run in CI/CD pipelines:

1. Tests run on every pull request
2. Coverage reports are generated and stored
3. Test failures block pull request merges
4. Security tests are required to pass

## Troubleshooting

### Common Issues

1. **Database connection errors**:
   - Ensure PostgreSQL is running on port 15432
   - Check the database name is `novamind_test`
   - Verify credentials are correct

2. **Missing dependencies**:
   - Run `pip install -r requirements-dev.txt`
   - Check for conflicting package versions

3. **Inconsistent test results**:
   - Ensure tests are properly isolated
   - Check for shared state between tests
   - Verify cleanup after tests

### Getting Help

If you encounter issues with the test suite:

1. Check this documentation for solutions
2. Examine the test logs for specific error messages
3. Reach out to the development team if problems persist
1. **Use real dependencies**: Test with actual database and services when possible
2. **Focus on interactions**: Verify how components work together
3. **Clean up after tests**: Ensure tests don't affect each other
4. **Test failure modes**: Verify how the system handles failures
5. **Use transactions**: Wrap tests in transactions for isolation

Example:

```python
@pytest.mark.asyncio
async def test_patient_repository_integration(db_session):
    # Arrange
    repository = PatientRepository()
    patient = Patient(id="test-id", name="Test Patient")
    
    # Act
    await repository.create(db_session, patient)
    result = await repository.get_by_id(db_session, "test-id")
    
    # Assert
    assert result is not None
    assert result.id == "test-id"
    assert result.name == "Test Patient"
```

## Testing for HIPAA Compliance

HIPAA compliance tests focus on:

1. **PHI Protection**: Verify PHI is properly identified and protected
2. **Access Controls**: Test authentication and authorization
3. **Audit Logging**: Verify access to PHI is properly logged
4. **Data Encryption**: Test encryption of PHI at rest and in transit
5. **Error Handling**: Ensure errors don't expose PHI

Example:

```python
def test_phi_redaction():
    # Arrange
    redactor = PHIRedactor()
    text = "Patient John Smith (SSN: 123-45-6789) reported symptoms."
    
    # Act
    redacted = redactor.redact(text)
    
    # Assert
    assert "John Smith" not in redacted
    assert "123-45-6789" not in redacted
    assert "[REDACTED]" in redacted
```

## Continuous Integration

The test suite is designed to run in CI/CD pipelines:

1. Tests run on every pull request
2. Coverage reports are generated and stored
3. Test failures block pull request merges
4. Security tests are required to pass

## Troubleshooting

### Common Issues

1. **Database connection errors**:
   - Ensure PostgreSQL is running on port 15432
   - Check the database name is `novamind_test`
   - Verify credentials are correct

2. **Missing dependencies**:
   - Run `pip install -r requirements-dev.txt`
   - Check for conflicting package versions

3. **Inconsistent test results**:
   - Ensure tests are properly isolated
   - Check for shared state between tests
   - Verify cleanup after tests

### Getting Help

If you encounter issues with the test suite:

1. Check this documentation for solutions
2. Examine the test logs for specific error messages
3. Reach out to the development team if problems persist