# Novamind Digital Twin Test Infrastructure: Single Source of Truth

## Overview

This document serves as the definitive Single Source of Truth (SSOT) for the Novamind Digital Twin test infrastructure. It provides comprehensive technical details on test organization, execution, and best practices to ensure consistent implementation across the team.

## Core Principles

The Novamind Digital Twin test infrastructure is built on these foundational principles:

1. **Dependency-Based Organization**: Tests are categorized by their external dependency requirements, not by architecture layer
2. **Progressive Test Execution**: Tests run from most isolated to most integrated
3. **SSOT Directory Structure**: Clear, consistent directory structure for all tests
4. **Unified Test Runners**: Canonical tools for test execution
5. **HIPAA-Compliant Testing**: Special considerations for protected health information (PHI)

## Directory Structure

The test suite follows this standardized directory structure:

```
/backend/app/tests/
├── standalone/          # No external dependencies
│   ├── domain/          # Domain-specific standalone tests
│   ├── application/     # Application-specific standalone tests
│   └── ...
├── venv/                # Requires Python environment but no external services
│   ├── domain/          # Domain-specific venv tests
│   ├── application/     # Application-specific venv tests
│   └── ...
└── integration/         # Requires external services (DB, API, etc.)
    ├── domain/          # Domain-specific integration tests
    ├── application/     # Application-specific integration tests
    └── ...
```

Within each dependency level, tests can be further organized by domain/module to maintain logical grouping. However, the primary organization is always by dependency level.

## Test Categorization Criteria

### Standalone Tests

Tests are categorized as **standalone** if they:
- Have no external dependencies (file system, network, etc.)
- Use only Python standard library and internal application code
- Use mocks or stubs for all external interactions
- Do not require environment variables or configuration

Example: Unit tests for pure business logic, value objects, or utility functions.

### VENV Tests

Tests are categorized as **venv** if they:
- Require installed Python packages beyond the standard library
- May use the file system for temporary files
- May use in-memory implementations of databases or services
- Require environment variables or configuration
- Do not require external network services or persistent databases

Example: Tests for modules using ORM models with SQLite in-memory database, or tests using file system for configuration.

### Integration Tests

Tests are categorized as **integration** if they:
- Require external network services (even if mocked)
- Require persistent databases
- Test multiple components together
- Require specific environment configuration
- May have side effects on external systems

Example: Tests for repository implementations with real databases, API endpoints, or third-party services.

## Test Runners

The canonical way to run tests is through the `/backend/scripts/test/runners/run_tests.py` script, which provides a unified interface for test execution at different dependency levels.

### Command-Line Interface

```bash
# Run only standalone tests
python /backend/scripts/test/runners/run_tests.py --standalone

# Run standalone and venv tests
python /backend/scripts/test/runners/run_tests.py --venv

# Run all tests
python /backend/scripts/test/runners/run_tests.py --all

# Run tests with security markers
python /backend/scripts/test/runners/run_tests.py --security

# Generate coverage report
python /backend/scripts/test/runners/run_tests.py --all --coverage

# Run tests with verbose output
python /backend/scripts/test/runners/run_tests.py --all --verbose
```

### Progressive Execution

The test runner supports progressive execution, where tests at higher dependency levels are only run if tests at lower levels pass:

```bash
python /backend/scripts/test/runners/run_tests.py --all --progressive
```

### Configuration

The test runner uses configuration from:
1. Command-line arguments
2. Environment variables
3. Configuration files (`pytest.ini`, `.coveragerc`)

## Test Markers

Test markers are used to categorize tests orthogonally to their dependency level. Common markers include:

- `@pytest.mark.security` - Security-focused tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.hipaa` - Tests specifically for HIPAA compliance
- `@pytest.mark.slow` - Tests that take a long time to run

Example usage:

```python
import pytest

@pytest.mark.security
def test_password_hashing():
    # Test implementation
    pass
```

## Test Creation Guidelines

### Placing New Tests

When creating a new test, determine its appropriate location based on its dependencies:

1. Identify the minimal dependency requirements for the test
2. Place it in the corresponding directory (standalone, venv, integration)
3. Within that directory, organize by domain/module

### Test File Naming

Test files should follow these naming conventions:

- All test files should start with `test_`
- Name should reflect the module/functionality being tested
- Example: `test_patient_repository.py`

### Test Function Naming

Test functions should follow these naming conventions:

- All test functions should start with `test_`
- Name should clearly describe the scenario being tested
- Include success/failure condition in the name
- Example: `test_create_patient_with_valid_data_succeeds()`

### Test Fixtures

Test fixtures should be placed based on their scope and dependency requirements:

- Module-specific fixtures in the test module
- Shared fixtures within a dependency level in a `conftest.py` file in that level
- Cross-dependency fixtures are discouraged but can be placed in the root `conftest.py` if necessary

### Example Test Structure

```python
import pytest
from app.domain.entities import Patient
from app.domain.value_objects import PatientId
from unittest.mock import Mock

# Standalone test - no external dependencies
def test_patient_initialization_with_valid_id_succeeds():
    # Arrange
    patient_id = PatientId("12345")
    
    # Act
    patient = Patient(id=patient_id, name="Test Patient")
    
    # Assert
    assert patient.id == patient_id
    assert patient.name == "Test Patient"
```

## Migration Tools

To help with the transition to the dependency-based structure, several tools are provided:

### Test Analyzer

The test analyzer examines existing tests to determine their appropriate dependency level:

```bash
python /backend/scripts/test/tools/test_analyzer.py
```

### Test Migrator

The test migrator helps move tests to their appropriate locations:

```bash
# Analyze without migrating
python /backend/scripts/test/migrations/migrate_tests.py --analyze

# Migrate tests
python /backend/scripts/test/migrations/migrate_tests.py --migrate

# Delete original files after migration
python /backend/scripts/test/migrations/migrate_tests.py --delete-originals

# Rollback migration
python /backend/scripts/test/migrations/migrate_tests.py --rollback
```

### Test Suite Cleanup

For a guided process through the entire migration, use the cleanup orchestrator:

```bash
python /backend/scripts/test/test_suite_cleanup.py
```

## CI/CD Integration

The dependency-based test organization is designed to optimize CI/CD pipelines by:

1. Running standalone tests first (fastest, most reliable)
2. Running venv tests next
3. Running integration tests last (slowest, most dependencies)

A typical CI/CD configuration would look like:

```yaml
stages:
  - lint
  - standalone-tests
  - venv-tests
  - integration-tests
  - deploy

standalone-tests:
  script:
    - python /backend/scripts/test/runners/run_tests.py --standalone

venv-tests:
  script:
    - python /backend/scripts/test/runners/run_tests.py --venv
  needs:
    - standalone-tests

integration-tests:
  script:
    - python /backend/scripts/test/runners/run_tests.py --integration
  needs:
    - venv-tests
```

## HIPAA Compliance Considerations

Special care must be taken with tests involving PHI:

1. Never use real PHI in tests, even in integration tests
2. Use the provided `PHIGenerator` to create realistic but fake PHI
3. Ensure test data is purged after test execution
4. Use the `@pytest.mark.hipaa` marker to identify tests that deal with PHI-handling code
5. Run separate HIPAA compliance checks on the test suite itself

## Best Practices

### Test Isolation

- Each test should be independent of others
- Tests should clean up after themselves
- Don't rely on test execution order

### Mocking

- Prefer dependency injection to make mocking easier
- Use `unittest.mock` or `pytest-mock` for mocking
- Document mock behavior clearly

### Fixtures

- Keep fixtures simple and focused
- Document fixture dependencies
- Don't create fixtures with side effects

### Test Coverage

- Aim for high coverage in standalone tests
- Focus integration tests on critical paths
- Use `--coverage` flag to generate coverage reports

## Troubleshooting

### Common Issues

1. **Import Errors**: Often caused by moving tests without updating imports. Use the `--update-imports` flag with migration tools.

2. **Missing Dependencies**: Integration tests failing due to missing external services. Make sure the test is categorized correctly.

3. **Test Interference**: Tests affecting each other. Ensure tests clean up after themselves.

4. **Slow Tests**: Review if tests are in the correct category. Standalone tests should run quickly.

### Getting Help

For issues with the test infrastructure, consult:

1. This documentation
2. The test tool help menus (`--help` flag)
3. The test infrastructure team

## Conclusion

The dependency-based SSOT approach to testing provides a clear, consistent, and maintainable structure for the Novamind Digital Twin test suite. By following these guidelines, we ensure that our tests are reliable, efficient, and effectively support the development of high-quality, HIPAA-compliant software.