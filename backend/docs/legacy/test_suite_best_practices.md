# Novamind Test Suite Best Practices

This document outlines the best practices for writing and maintaining tests for the Novamind backend. Following these guidelines will ensure a consistent, maintainable, and effective test suite.

## Dependency Level Guidelines

### Standalone Tests

Standalone tests should:

- Run without any external dependencies (no file system, network, or database access)
- Be completely deterministic and reproducible
- Use in-memory mocks instead of real implementations
- Focus on testing pure logic and algorithms
- Be fast (sub-millisecond execution time)

```python
# Good standalone test example
def test_patient_model_validation():
    # Uses only in-memory data structures
    patient = Patient(id="p-12345", name="Test Patient", age=30)
    assert patient.id == "p-12345"
    assert patient.name == "Test Patient"
    assert patient.age == 30
```

### Venv Tests

Venv tests should:

- Limit dependencies to the file system and installed packages
- Not require network access or external services
- Use temporary directories/files for isolation
- Clean up any created files/directories
- Be relatively fast (sub-second execution time)

```python
# Good venv test example
def test_config_file_loading(temp_dir):
    # Uses file system but no network or external services
    config_path = os.path.join(temp_dir, "config.json")
    with open(config_path, "w") as f:
        json.dump({"api_key": "test-key"}, f)
    
    config = ConfigLoader.load(config_path)
    assert config.api_key == "test-key"
```

### Integration Tests

Integration tests should:

- Test integration between multiple components or external services
- Use test doubles for third-party services when possible
- Be isolated from other tests to prevent interference
- Handle setup and teardown properly
- Document external dependencies clearly

```python
# Good integration test example
@pytest.mark.integration
async def test_patient_repository_saves_to_database(test_db_connection):
    # Tests actual database integration
    repo = PatientRepository(test_db_connection)
    patient = Patient(id="p-12345", name="Test Patient", age=30)
    
    await repo.save(patient)
    retrieved = await repo.get_by_id("p-12345")
    
    assert retrieved.id == patient.id
    assert retrieved.name == patient.name
    assert retrieved.age == patient.age
```

## Testing HIPAA Compliance

All tests involving PHI (Protected Health Information) should:

1. Use completely anonymized mock data
2. Never include real patient identifiers
3. Test PHI detection and sanitization
4. Validate proper audit logging
5. Test authorization boundaries

```python
# Example of proper PHI testing
def test_phi_sanitization():
    sanitizer = PHISanitizer()
    text_with_phi = "Patient John Doe (DOB: 01/01/1980) reported symptoms."
    
    sanitized = sanitizer.sanitize(text_with_phi)
    
    assert "John Doe" not in sanitized
    assert "01/01/1980" not in sanitized
    assert "[REDACTED_NAME]" in sanitized
    assert "[REDACTED_DATE]" in sanitized
```

## Test Structure Standards

Each test file should:

1. Follow a clear naming convention: `test_<component>_<aspect>.py`
2. Include test cases that each test a single behavior
3. Group related test cases together
4. Use descriptive test names that explain the behavior being tested
5. Include setup, action, and assertion phases clearly separated

```python
# Good test structure example
def test_digital_twin_creation_with_valid_inputs():
    # Setup
    patient_id = "p-12345"
    model_data = {"serotonin": 0.7, "dopamine": 0.6}
    
    # Action
    twin = DigitalTwin.create(patient_id, model_data)
    
    # Assertion
    assert twin.patient_id == patient_id
    assert twin.model_data["serotonin"] == 0.7
    assert twin.model_data["dopamine"] == 0.6
    assert twin.created_at is not None
```

## Fixture Guidelines

Fixtures should:

1. Be defined at the appropriate level (standalone, venv, integration)
2. Handle their own setup and teardown
3. Be focused on a single responsibility
4. Be documented clearly
5. Be reusable across multiple tests

```python
# Good fixture example
@pytest.fixture
def mock_patient_data():
    """
    Provides a set of mock patient data for testing.
    """
    return {
        "id": "p-12345",
        "name": "Test Patient",
        "age": 30,
        "gender": "F",
        "medical_history": ["Anxiety", "Depression"]
    }
```

## Mocking Best Practices

When using mocks:

1. Mock at the boundaries, not internally
2. Use explicit mocks rather than monkey patching
3. Only mock what you need to
4. Verify important interactions with mocks
5. Reset mocks between tests

```python
# Good mocking example
def test_patient_service_calls_repository(mocker):
    # Mock the repository at the boundary
    mock_repo = mocker.Mock()
    mock_repo.get_by_id.return_value = Patient(id="p-12345", name="Test Patient")
    
    # Inject the mock
    service = PatientService(repository=mock_repo)
    
    # Exercise the service
    patient = service.get_patient("p-12345")
    
    # Verify behavior
    mock_repo.get_by_id.assert_called_once_with("p-12345")
    assert patient.id == "p-12345"
```

## Security Testing Guidelines

Security tests should:

1. Validate access controls work as expected
2. Test for proper encryption of sensitive data
3. Verify audit logging captures required events
4. Test for proper input validation and sanitization
5. Verify security headers and configurations

```python
# Security test example
@pytest.mark.security
def test_unauthorized_access_is_blocked(client):
    # No authentication provided
    response = client.get("/api/v1/patients/p-12345")
    
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
```

## Performance Testing Guidelines

Performance tests should:

1. Measure specific metrics (response time, throughput, etc.)
2. Have clearly defined performance requirements
3. Run in an isolated environment
4. Use representative data volumes
5. Be run separately from regular tests

```python
# Performance test example
@pytest.mark.performance
def test_digital_twin_generation_performance():
    patient_data = generate_test_patient_data(100)  # Generate representative data
    
    start_time = time.time()
    twins = batch_generate_digital_twins(patient_data)
    end_time = time.time()
    
    execution_time = end_time - start_time
    assert len(twins) == 100
    assert execution_time < 2.0  # Should complete in under 2 seconds
```

## Test Documentation

Tests should be documented with:

1. Clear docstrings explaining the test's purpose
2. References to requirements being tested
3. Explanations of complex test setups
4. Notes about any external dependencies
5. Expected behavior in failure cases

```python
def test_biometric_alert_generation():
    """
    Tests that biometric alerts are generated when values exceed thresholds.
    
    Requirements: SEC-103, CLIN-45
    
    This test verifies that when biometric data exceeds clinical thresholds,
    the system generates appropriate alerts with the correct severity levels.
    """
    # Test implementation
```

## Continuous Integration Integration

Tests should be tagged appropriately for CI:

1. Use pytest markers to categorize tests
2. Structure tests for parallel execution
3. Isolate slow tests
4. Set appropriate timeouts

```python
# Markers for CI
@pytest.mark.standalone
def test_fast_standalone_feature(): ...

@pytest.mark.integration
@pytest.mark.slow
def test_slow_integration_feature(): ...
```

## Test Maintenance

Good practices for maintaining tests:

1. Review and update tests when requirements change
2. Remove obsolete tests
3. Refactor tests for clarity and maintainability
4. Investigate and fix flaky tests immediately
5. Monitor test coverage and add tests for uncovered code