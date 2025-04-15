# Novamind Digital Twin Test Suite: Best Practices

This document provides detailed guidance on writing tests for the Novamind Digital Twin platform using the dependency-based testing approach. It serves as a practical guide for developers to ensure consistent, maintainable, and effective tests.

## Table of Contents

1. [Dependency-Based Testing Principles](#dependency-based-testing-principles)
2. [Writing Standalone Tests](#writing-standalone-tests)
3. [Writing VENV Tests](#writing-venv-tests)
4. [Writing Integration Tests](#writing-integration-tests)
5. [Fixture Best Practices](#fixture-best-practices)
6. [Test Naming Conventions](#test-naming-conventions)
7. [Test Organization](#test-organization)
8. [HIPAA and Security Test Considerations](#hipaa-and-security-test-considerations)
9. [Test Performance Optimization](#test-performance-optimization)
10. [Common Pitfalls to Avoid](#common-pitfalls-to-avoid)

## Dependency-Based Testing Principles

The Novamind Digital Twin platform uses a dependency-based approach to testing, categorizing tests based on their dependencies:

### Key Principles

1. **Separation of Concerns**: Tests should be organized by their dependency requirements, not just functionality.
2. **Fast Feedback**: Tests with fewer dependencies should run first to provide quick feedback.
3. **Isolation**: Tests should be isolated from dependencies not required for the test.
4. **Reliability**: Tests should be deterministic and not dependent on external state.
5. **Completeness**: All code paths should be covered by tests at the appropriate dependency level.

### Dependency Levels

| Level | Dependencies | Examples | Speed |
|-------|--------------|----------|-------|
| Standalone | None | Domain models, pure functions | Fastest |
| VENV | Python environment, file system | Config loading, file operations | Medium |
| Integration | External services, network, database | API endpoints, repository implementations | Slowest |

## Writing Standalone Tests

Standalone tests verify behavior without external dependencies. They should:

### Characteristics

- Test pure business logic
- Run completely in memory
- Have no file I/O, network, or database dependencies
- Be fast (milliseconds per test)
- Be deterministic (always produce the same result)

### Examples

**Domain Entity Test:**

```python
import pytest
from backend.app.domain.models.patient import Patient

@pytest.mark.standalone
def test_patient_name_validation():
    """Test that patient name validation works correctly."""
    # Arrange
    valid_name = "John Doe"
    invalid_name = ""
    
    # Act & Assert
    patient = Patient(id="P12345", name=valid_name)
    assert patient.name == valid_name
    
    with pytest.raises(ValueError) as exc_info:
        Patient(id="P12345", name=invalid_name)
    
    assert "name" in str(exc_info.value).lower()
```

**Value Object Test:**

```python
import pytest
from datetime import date
from backend.app.domain.value_objects import DateRange

@pytest.mark.standalone
def test_date_range_duration():
    """Test that date range correctly calculates duration in days."""
    # Arrange
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 10)
    
    # Act
    date_range = DateRange(start=start_date, end=end_date)
    
    # Assert
    assert date_range.duration_days == 9
```

### Key Tips for Standalone Tests

1. **Use pytest.mark.standalone**: Always mark standalone tests appropriately
2. **No External State**: Don't rely on anything outside the test function
3. **Pure Logic Only**: Focus on business rules and transformations
4. **Mock Dependencies**: If code has dependencies, mock them completely
5. **Deterministic Results**: Tests should always produce the same result

## Writing VENV Tests

VENV tests require the Python environment but no external services. They typically involve:

### Characteristics

- File system operations
- Environment variable usage
- Configuration loading
- Logging functionality
- Local file-based resource access

### Examples

**Config Loader Test:**

```python
import pytest
import os
import tempfile
import json

from backend.app.infrastructure.config.config_loader import ConfigLoader

@pytest.mark.venv
def test_config_loader():
    """Test that config loader can load and parse JSON files."""
    # Arrange
    config_data = {"app": {"name": "test_app", "port": 8000}}
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name
    
    try:
        # Act
        loader = ConfigLoader()
        loaded_config = loader.load_json_config(config_path)
        
        # Assert
        assert loaded_config == config_data
        assert loaded_config["app"]["name"] == "test_app"
        assert loaded_config["app"]["port"] == 8000
    finally:
        # Clean up
        os.unlink(config_path)
```

**File Utility Test:**

```python
import pytest
import tempfile
import os
from pathlib import Path

from backend.app.core.utils.file_utils import ensure_directory_exists

@pytest.mark.venv
def test_ensure_directory_exists():
    """Test that directory creation works correctly."""
    # Arrange
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_subdir" / "nested_dir"
        
        # Act
        ensure_directory_exists(test_dir)
        
        # Assert
        assert test_dir.exists()
        assert test_dir.is_dir()
```

### Key Tips for VENV Tests

1. **Clean Up Resources**: Always clean up temporary files and directories
2. **Use tempfile Module**: For creating temporary files and directories
3. **Don't Assume Directory Structure**: Tests should work regardless of environment
4. **Isolate From External Services**: No database or network connections
5. **Consider Parallel Execution**: Tests should not interfere with each other

## Writing Integration Tests

Integration tests verify that components work together with external dependencies:

### Characteristics

- Database connections
- Network communications
- External API calls
- Multiple component interactions
- Environment configuration

### Examples

**API Endpoint Test:**

```python
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.infrastructure.database.models import PatientModel

@pytest.mark.integration
def test_get_patient_endpoint(db_session):
    """Test that the get patient endpoint returns the correct patient."""
    # Arrange
    client = TestClient(app)
    
    # Create test patient in the database
    patient = PatientModel(
        id="P12345",
        name="Test Patient",
        date_of_birth="1980-01-01"
    )
    db_session.add(patient)
    db_session.commit()
    
    try:
        # Act
        response = client.get(f"/api/v1/patients/{patient.id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == patient.id
        assert data["name"] == patient.name
    finally:
        # Clean up
        db_session.delete(patient)
        db_session.commit()
```

**Repository Test:**

```python
import pytest
from datetime import date

from backend.app.infrastructure.repositories.patient_repository import PatientRepository
from backend.app.domain.models.patient import Patient

@pytest.mark.integration
def test_patient_repository_save_and_get(db_session):
    """Test that patient repository can save and retrieve patients."""
    # Arrange
    repository = PatientRepository(db_session)
    patient = Patient(
        id="P67890",
        name="Repository Test Patient",
        date_of_birth=date(1990, 5, 15)
    )
    
    # Act
    repository.save(patient)
    retrieved_patient = repository.get_by_id("P67890")
    
    # Assert
    assert retrieved_patient is not None
    assert retrieved_patient.id == patient.id
    assert retrieved_patient.name == patient.name
    assert retrieved_patient.date_of_birth == patient.date_of_birth
    
    # Clean up
    repository.delete(patient.id)
```

### Key Tips for Integration Tests

1. **Use Transactions**: Wrap tests in transactions for automatic rollback
2. **Clean Up Data**: Always clean up created test data
3. **Use Test Databases**: Never test against production databases
4. **Minimize External API Calls**: Mock external services when possible
5. **Be Aware of Side Effects**: Tests should not affect other tests

## Fixture Best Practices

Fixtures are a powerful way to set up test prerequisites. Here's how to use them effectively:

### Fixture Organization

Organize fixtures by dependency level:
- `backend/app/tests/standalone/conftest.py`: Standalone-only fixtures
- `backend/app/tests/venv/conftest.py`: VENV-level fixtures
- `backend/app/tests/integration/conftest.py`: Integration-level fixtures

### Fixture Scopes

Choose the appropriate scope for fixtures:

```python
@pytest.fixture(scope="function")  # Default: recreated for each test function
def my_function_fixture():
    return SomeObject()

@pytest.fixture(scope="class")  # Created once per test class
def my_class_fixture():
    return SomeObject()

@pytest.fixture(scope="module")  # Created once per test module
def my_module_fixture():
    return SomeObject()

@pytest.fixture(scope="session")  # Created once per test session
def my_session_fixture():
    return SomeObject()
```

### Fixture Dependencies

Fixtures can depend on other fixtures:

```python
@pytest.fixture
def db_connection():
    """Create a database connection."""
    connection = create_connection()
    yield connection
    connection.close()

@pytest.fixture
def db_session(db_connection):
    """Create a database session that depends on a connection."""
    session = create_session(db_connection)
    yield session
    session.close()
```

### Dynamic Fixtures

Parameterized fixtures for more flexible testing:

```python
@pytest.fixture(params=["sqlite", "postgres"])
def database_type(request):
    """Parameterized fixture that tests multiple database types."""
    return request.param

def test_database_connection(database_type):
    """This test will run twice, once for SQLite and once for Postgres."""
    assert connect_to_db(database_type)
```

## Test Naming Conventions

Consistent naming makes tests easier to find and understand:

### File Naming

- Test files should be named `test_<component>.py`
- Test modules should match the structure of the code being tested
- Example: `backend/app/domain/models/patient.py` → `backend/app/tests/standalone/domain/test_patient_model.py`

### Test Function Naming

- Test functions should be named `test_<function>_<scenario>`
- Names should clearly describe what is being tested
- Examples:
  - `test_patient_creation_with_valid_data`
  - `test_patient_creation_with_missing_name`
  - `test_get_patient_by_id_not_found`

### Test Class Naming

- Test classes should be named `Test<Component>`
- Use test classes to group related tests
- Example: `TestPatientModel`, `TestPatientRepository`

## Test Organization

Structure test files for maintainability and clarity:

### Arrange-Act-Assert Pattern

Organize test functions using the AAA pattern:

```python
def test_component_functionality():
    # Arrange - set up test prerequisites
    component = Component()
    input_data = {"key": "value"}
    
    # Act - execute the code being tested
    result = component.process(input_data)
    
    # Assert - verify the results
    assert result.status == "success"
    assert result.value == "expected_value"
```

### Test Grouping

Group related tests in classes:

```python
@pytest.mark.standalone
class TestPatientModel:
    """Tests for the Patient domain model."""
    
    def test_creation_with_valid_data(self):
        """Test patient creation with valid data."""
        # Test implementation
    
    def test_creation_with_invalid_data(self):
        """Test patient creation with invalid data."""
        # Test implementation
    
    def test_age_calculation(self):
        """Test patient age calculation."""
        # Test implementation
```

### Using Descriptive Docstrings

Always include descriptive docstrings:

```python
def test_patient_diagnosis_update():
    """
    Test that patient diagnosis can be updated with proper authorization.
    
    This test verifies:
    1. A provider with proper authorization can update a diagnosis
    2. The update is properly recorded in the audit log
    3. The patient record reflects the updated diagnosis
    """
    # Test implementation
```

## HIPAA and Security Test Considerations

Special considerations for testing HIPAA-compliant applications:

### PHI Test Data

- Never use real Protected Health Information (PHI) in tests
- Use consistently generated fake data or test fixtures
- Ensure test data is clearly marked as non-production

Example:

```python
@pytest.fixture
def test_patient_data():
    """Generate fake patient data for testing."""
    return {
        "id": "TEST-P12345",
        "name": "Test Patient",
        "date_of_birth": "1980-01-01",
        "ssn": "000-00-0000",  # Explicitly fake SSN
        "address": "123 Test Street, Test City, TS 12345"
    }
```

### Security Test Requirements

- Test all authorization boundaries
- Verify access controls work as expected
- Test that PHI is always encrypted at rest and in transit
- Verify audit logging functionality

Example:

```python
@pytest.mark.integration
@pytest.mark.security
def test_unauthorized_access_prevented(client, test_patient):
    """Test that unauthorized users cannot access patient data."""
    # Arrange
    unauthorized_token = create_token_for_role("non_clinical_staff")
    
    # Act
    response = client.get(
        f"/api/v1/patients/{test_patient.id}",
        headers={"Authorization": f"Bearer {unauthorized_token}"}
    )
    
    # Assert
    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()
```

## Test Performance Optimization

Strategies for maintaining fast test execution:

### Optimization Principles

1. **Use Appropriate Test Level**: Don't use integration tests when standalone tests will do
2. **Mock Expensive Operations**: Use mocks for slow operations in lower-level tests
3. **Use In-Memory Databases**: For faster integration tests
4. **Parameterize Tests**: Test multiple scenarios in one function
5. **Optimize Fixtures**: Use appropriate fixture scopes

### Fixture Optimization

```python
# Poor performance: creates a new connection for every test
@pytest.fixture
def slow_db_connection():
    connection = create_expensive_connection()
    yield connection
    connection.close()

# Better performance: reuses the connection across tests
@pytest.fixture(scope="module")
def optimized_db_connection():
    connection = create_expensive_connection()
    yield connection
    connection.close()
```

### Test Parametrization

```python
@pytest.mark.standalone
@pytest.mark.parametrize("input_value,expected_result", [
    ("valid_input", True),
    ("invalid_input", False),
    ("another_valid_input", True),
    # Add more test cases without duplicating test code
])
def test_input_validation(input_value, expected_result):
    """Test input validation with multiple scenarios."""
    validator = InputValidator()
    result = validator.is_valid(input_value)
    assert result == expected_result
```

## Common Pitfalls to Avoid

Avoid these common testing mistakes:

### 1. Test Interdependence

**Problem**: Tests depend on each other or on test execution order.

**Solution**: Ensure each test is completely independent and can run in isolation.

```python
# BAD: Tests depend on each other
def test_first_creates_data():
    # Creates data used by test_second
    
def test_second_uses_data():
    # Uses data from test_first

# GOOD: Tests are independent
def test_first():
    # Creates and uses its own data
    
def test_second():
    # Creates and uses its own data
```

### 2. Hardcoded Paths

**Problem**: Tests use hardcoded file paths that won't work across environments.

**Solution**: Use temporary files or relative paths based on test location.

```python
# BAD: Hardcoded path
def test_file_processing():
    processor = FileProcessor()
    result = processor.process("/home/user/test_data.json")
    
# GOOD: Use temporary files
def test_file_processing():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
        json.dump(test_data, f)
        f.flush()
        processor = FileProcessor()
        result = processor.process(f.name)
```

### 3. Missing Cleanup

**Problem**: Tests create resources but don't clean them up.

**Solution**: Use fixtures with cleanup logic or try/finally blocks.

```python
# BAD: No cleanup
def test_database_operation():
    repository = Repository()
    repository.save(test_entity)
    # No cleanup, test entity remains in database
    
# GOOD: With cleanup
def test_database_operation():
    repository = Repository()
    try:
        repository.save(test_entity)
        # Test assertions
    finally:
        repository.delete(test_entity.id)
```

### 4. Overlooking Edge Cases

**Problem**: Tests only cover the happy path, not edge cases or error conditions.

**Solution**: Explicitly test edge cases and error handling.

```python
# BAD: Only testing the happy path
def test_divide():
    result = calculator.divide(10, 2)
    assert result == 5
    
# GOOD: Testing edge cases too
def test_divide():
    # Happy path
    result = calculator.divide(10, 2)
    assert result == 5
    
    # Edge case - division by zero
    with pytest.raises(ZeroDivisionError):
        calculator.divide(10, 0)
    
    # Edge case - negative numbers
    result = calculator.divide(-10, 2)
    assert result == -5
```

### 5. Slow Integration Tests

**Problem**: Integration tests are too slow, discouraging developers from running them.

**Solution**: Use in-memory databases, mock external services, and optimize test setup.

```python
# BAD: Connecting to actual services
@pytest.mark.integration
def test_third_party_api():
    client = ThirdPartyApiClient()
    result = client.fetch_data()  # Actually calls the API
    
# GOOD: Mocking external services
@pytest.mark.integration
def test_third_party_api(mocker):
    mock_response = {"data": "test_data"}
    mocker.patch("requests.get", return_value=MockResponse(mock_response))
    
    client = ThirdPartyApiClient()
    result = client.fetch_data()  # Uses the mock
    assert result == mock_response
```

By following these best practices, you'll create a test suite that is maintainable, reliable, and effective at catching issues before they reach production.