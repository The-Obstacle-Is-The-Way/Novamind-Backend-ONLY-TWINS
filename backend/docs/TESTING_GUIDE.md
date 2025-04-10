# Novamind Digital Twin Backend Testing Guide

This guide provides comprehensive instructions for setting up and running tests for the Novamind Digital Twin Backend. It covers test infrastructure, dependencies, configuration, and execution strategies.

## Test Infrastructure Overview

The Novamind testing infrastructure follows a layered approach:

1. **Standalone Tests**: Tests that can run without database connections or external dependencies
2. **Unit Tests**: Tests for individual components with mocked dependencies
3. **Integration Tests**: Tests for component interactions with test databases
4. **API Tests**: Tests for HTTP endpoints and request handling
5. **Security Tests**: Specialized tests for HIPAA compliance and security features

## Prerequisites

Before running tests, ensure you have the following installed:

- Python 3.10+
- PostgreSQL (for local integration testing)
- Git

## Installing Test Dependencies

### Automatic Installation

We provide a script to automatically install all test dependencies:

```bash
# From the backend directory
chmod +x install-test-dependencies.sh
./install-test-dependencies.sh
```

### Manual Installation

If you prefer manual installation:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Ensure async database drivers are installed
pip install asyncpg>=0.28.0 aiosqlite>=0.19.0
```

## Test Configuration

Tests use a separate configuration sourced from:

1. Environment variables (prefixed with `TESTING=1`)
2. A `.env.test` file in the backend directory

For local testing, create a `.env.test` file with:

```
TESTING=1
ENVIRONMENT=testing
POSTGRES_SERVER=localhost
POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_password
POSTGRES_DB=novamind_test
SECRET_KEY=test_secret_key_do_not_use_in_production
```

## Running Tests

### Running Standalone Tests

These tests don't require database setup and are the fastest to run:

```bash
# From the backend directory
python -m backend.app.tests.standalone.test_ml_exceptions_self_contained

# Or using pytest
TESTING=1 python -m pytest app/tests/standalone/ -v
```

### Running Unit Tests

```bash
# From the backend directory
TESTING=1 python -m pytest app/tests/domain/ app/tests/core/ -v
```

### Running Database Tests

These tests require a configured test database:

```bash
# From the backend directory
TESTING=1 python -m pytest app/tests/infrastructure/ -v
```

### Running API Tests

```bash
# From the backend directory
TESTING=1 python -m pytest app/tests/api/ -v
```

### Running All Tests

```bash
# From the backend directory
TESTING=1 python -m pytest
```

### Running Tests with Coverage

```bash
# From the backend directory
TESTING=1 python -m pytest --cov=app --cov-report=html
# Then open htmlcov/index.html in your browser
```

## Test Structure

The tests are organized according to the Clean Architecture principles:

```
app/tests/
├── __init__.py                # Sets up testing environment variables
├── conftest.py                # Global test fixtures
├── standalone/                # Standalone tests without external dependencies
├── core/                      # Tests for core modules
│   ├── security/              # Security-related tests
│   └── config/                # Configuration tests
├── domain/                    # Tests for domain entities and business logic
│   ├── ml/                    # ML-related tests
│   └── entities/              # Entity tests
├── infrastructure/            # Tests for database and external services
│   └── repositories/          # Repository tests
├── api/                       # API endpoint tests
└── fixtures/                  # Shared test fixtures
    ├── mock_db_fixture.py     # Database mocking utilities
    └── user_fixtures.py       # Authentication fixtures
```

## Mock Database Infrastructure

For tests that require database operations without connecting to an actual database:

```python
# Example using the mock database
from app.tests.fixtures.mock_db_fixture import MockAsyncSession

async def test_repository_function():
    # Create a mock session
    mock_db = MockAsyncSession()
    
    # Set up expected query results
    mock_db._query_results = [expected_entity]
    
    # Test your repository with the mock session
    repository = YourRepository(mock_db)
    result = await repository.get_by_id(1)
    
    # Verify correct query was executed
    assert mock_db._last_executed_query is not None
    assert result == expected_entity
```

## PHI Sanitization Testing

For testing HIPAA compliance and PHI sanitization:

```python
# Example using PHI sanitizer
from app.core.security.phi_sanitizer import PHISanitizer

def test_phi_sanitization():
    sanitizer = PHISanitizer()
    
    # Data with PHI
    data_with_phi = {
        "patient_name": "John Smith",
        "medical_record": "12345678",
        "notes": "Patient reports improved symptoms"
    }
    
    # Sanitize the data
    sanitized_data = sanitizer.sanitize(data_with_phi)
    
    # Verify PHI is redacted
    assert sanitized_data["patient_name"] != "John Smith"
    assert "[REDACTED]" in sanitized_data["patient_name"]
    assert sanitized_data["notes"] == "Patient reports improved symptoms"  # Non-PHI preserved
```

## Test Authentication

For tests requiring authentication:

```python
# Example using BaseSecurityTest
from app.tests.core.security.test_base_security import BaseSecurityTest

class TestSecuredEndpoint(BaseSecurityTest):
    def setup_method(self):
        # Set up with admin role for testing
        self.test_roles = [Role.ADMIN]
        super().setup_method()
    
    async def test_admin_endpoint(self, client):
        # Test with authenticated admin user
        response = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {get_test_token(self.user)}"}
        )
        assert response.status_code == 200
```

## Continuous Integration

The repository includes GitHub Actions workflows in `.github/workflows/test.yml` for automated testing on every push and pull request. The CI pipeline:

1. Runs standalone tests first
2. Runs database tests with a PostgreSQL service container
3. Runs API tests
4. Performs security scanning
5. Generates and uploads test coverage reports

## Best Practices

1. **Isolation**: Each test should be independent and not rely on the state from other tests
2. **Mocking**: Use mocks for external dependencies to keep tests fast and reliable
3. **Test Organization**: Keep test files mirroring the structure of the actual code
4. **Coverage**: Aim for high test coverage, especially for critical components
5. **Security**: Always include tests for security features and PHI handling
6. **Clean Setup/Teardown**: Ensure proper cleanup after tests to avoid interference

## Troubleshooting

Common issues and solutions:

### Database Connection Issues

- Ensure the test PostgreSQL instance is running
- Verify credentials in the `.env.test` file match your test database
- Check that async database drivers are installed

### Import Errors

- Make sure PYTHONPATH includes the backend directory
- Check for circular imports in test fixtures

### Async Test Failures

- Ensure pytest-asyncio is installed
- Mark async tests with `@pytest.mark.asyncio`
- Use the correct event loop policy for your OS

### Mock Database Issues

- Check that the mock session is tracking operations correctly
- Verify query results are properly set before execution