# Novamind Test Suite Documentation

This document serves as the entry point for all test-related documentation in the Novamind Digital Twin platform.

## Documentation Index

| Document | Description |
|----------|-------------|
| [Test Suite Architecture](./test_suite_architecture.md) | Overview of the test suite architecture, organization, and structure |
| [Test Suite Best Practices](./test_suite_best_practices.md) | Guidelines and best practices for writing effective tests |
| [Test Dependency Level Guide](./test_dependency_level_guide.md) | How to work with the dependency-based test organization |
| [Test Syntax Repair Guide](./test_syntax_repair_guide.md) | Guide for fixing common syntax errors in test files |

## Test Suite Overview

The Novamind test suite has been restructured according to a dependency-level organization pattern that improves:

1. **Test Reliability**: By isolating tests with similar dependency requirements
2. **Test Speed**: By enabling faster execution of tests with fewer dependencies
3. **Developer Experience**: By providing clear guidelines for test placement and setup
4. **CI/CD Integration**: By enabling dependency-aware test execution in pipelines

## Key Concepts

### Dependency Levels

Tests are organized into three primary dependency levels:

- **Standalone**: Tests with no external dependencies (fastest, most reliable)
- **Venv**: Tests requiring file system access but no network/database (medium speed)
- **Integration**: Tests requiring external services, networks, or databases (slowest, most thorough)

### Domain Organization

Within each dependency level, tests are further organized by domain:

- **domain/**: Tests for core domain entities and business logic
- **application/**: Tests for application services and use cases
- **infrastructure/**: Tests for external services and persistence
- **api/**: Tests for API endpoints and routes
- **core/**: Tests for cross-cutting concerns
- **security/**: Tests specifically focused on security aspects

## Quick Start

### Running Tests

```bash
# Run standalone tests (fastest)
python -m pytest backend/app/tests/standalone/

# Run venv tests (medium)
python -m pytest backend/app/tests/venv/

# Run integration tests (slowest)
python -m pytest backend/app/tests/integration/

# Run all tests
python -m pytest backend/app/tests/
```

### Creating a New Test

1. Determine the appropriate dependency level for your test
2. Place it in the correct subdirectory based on domain
3. Add appropriate pytest markers
4. Use fixtures from the corresponding dependency level's conftest.py

Example:

```python
# backend/app/tests/standalone/domain/test_patient.py
import pytest
from app.domain.entities.patient import Patient

@pytest.mark.standalone
def test_patient_creation():
    """Test that a patient can be created with valid attributes."""
    patient = Patient(id="p-12345", name="Test Patient", age=30)
    
    assert patient.id == "p-12345"
    assert patient.name == "Test Patient"
    assert patient.age == 30
```

## Test Suite Maintenance

The test suite includes tools for maintenance and repair:

```bash
# Repair syntax errors in test files
python backend/scripts/test/tools/repair_test_syntax.py

# Migrate tests to the correct directory structure
python backend/scripts/test/migrations/migrate_tests.py

# Generate test coverage report
python -m pytest --cov=backend/app backend/app/tests/ --cov-report=html
```

## HIPAA Compliance Testing

Special attention is given to HIPAA compliance testing:

- **PHI Protection**: Tests verify that PHI is properly protected and sanitized
- **Authorization**: Tests verify that proper authorization controls are in place
- **Audit Logging**: Tests verify that all PHI access is properly logged
- **Encryption**: Tests verify that sensitive data is encrypted at rest and in transit

All tests with PHI access should be marked with the `hipaa` marker:

```python
@pytest.mark.hipaa
def test_phi_sanitization():
    # Test PHI sanitization
    ...
```

## Digital Twin Testing

The test suite includes specialized tests for the Digital Twin functionality:

- **Biometric Processing**: Tests for biometric data processing
- **Neurotransmitter Modeling**: Tests for neurotransmitter level modeling
- **ML Integration**: Tests for machine learning model integration
- **Temporal Analysis**: Tests for temporal sequence analysis

## Security Testing

The test suite includes comprehensive security tests:

- **Authentication**: Tests for proper authentication mechanisms
- **Authorization**: Tests for proper authorization controls
- **Encryption**: Tests for proper data encryption
- **Sanitization**: Tests for proper data sanitization
- **Input Validation**: Tests for proper input validation
- **Audit Logging**: Tests for proper audit logging

## Contributing

When contributing to the test suite:

1. Follow the best practices in [Test Suite Best Practices](./test_suite_best_practices.md)
2. Ensure tests are placed in the correct dependency level
3. Use the appropriate markers for your tests
4. Include proper documentation for complex test setups
5. Verify that tests do not intermittently fail due to race conditions or timing issues