# Novamind Digital Twin Test Suite Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Test Suite Organization](#test-suite-organization)
3. [Dependency-Based Testing Approach](#dependency-based-testing-approach)
4. [Test Directory Structure](#test-directory-structure)
5. [Test Classification Guidelines](#test-classification-guidelines)
6. [Writing Tests](#writing-tests)
7. [Test Tools and Runners](#test-tools-and-runners)
8. [Migration Process](#migration-process)
9. [CI/CD Integration](#cicd-integration)
10. [Test Coverage Requirements](#test-coverage-requirements)

## Introduction

This document serves as the canonical Single Source of Truth (SSOT) for the Novamind Digital Twin test suite. It outlines the dependency-based testing approach, directory structure, and best practices for writing and maintaining tests.

## Test Suite Organization

The Novamind Digital Twin test suite is organized primarily by **dependency level**, with secondary organization by **architectural layer**. This approach ensures that:

1. Tests can be run in order of increasing dependency requirements
2. Faster tests (with fewer dependencies) can be run first
3. CI/CD pipelines can be optimized for quick feedback
4. Tests are isolated from unrelated components

## Dependency-Based Testing Approach

Tests are categorized into three primary dependency levels:

### Standalone Tests
- **No external dependencies**
- Pure logic tests that don't require file system, network, or databases
- Can run completely in isolation
- Examples: Domain models, value objects, pure business logic

### VENV Tests
- **Require Python environment only**
- May use the file system, environment variables, etc.
- No external service or network dependencies
- Examples: Repository implementations with mocked DB connections, service classes

### Integration Tests
- **Require external services or connections**
- Database connections, network calls, API endpoints
- May create and destroy resources in test environments
- Examples: Database integration, API endpoint tests, external service interactions

## Test Directory Structure

The test directory follows this structure:

```
/backend/app/tests/
├── standalone/               # Standalone tests (no dependencies)
│   ├── conftest.py           # Standalone test fixtures
│   ├── domain/               # Domain layer tests
│   ├── application/          # Application layer tests
│   ├── infrastructure/       # Infrastructure layer tests
│   ├── api/                  # API layer tests
│   └── core/                 # Core module tests
├── venv/                     # VENV tests (Python env only)
│   ├── conftest.py           # VENV test fixtures
│   ├── domain/               # Domain layer tests
│   ├── application/          # Application layer tests
│   ├── infrastructure/       # Infrastructure layer tests
│   ├── api/                  # API layer tests
│   └── core/                 # Core module tests
└── integration/              # Integration tests (external dependencies)
    ├── conftest.py           # Integration test fixtures
    ├── domain/               # Domain layer tests
    ├── application/          # Application layer tests
    ├── infrastructure/       # Infrastructure layer tests
    ├── api/                  # API layer tests
    └── core/                 # Core module tests
```

## Test Classification Guidelines

### Determining Test Level

Tests should be placed in the correct dependency level based on:

1. **Dependencies required** - If a test needs a database, it's an integration test
2. **External interactions** - Tests that make HTTP requests are integration tests
3. **Isolation level** - Tests that can run in complete isolation are standalone tests
4. **Speed** - Tests that can run quickly without setup are standalone tests

When in doubt, use the following decision tree:

- Does the test need external services? → **Integration test**
- Does the test use the file system or environment vars? → **VENV test**
- Does the test only use in-memory data structures? → **Standalone test**

### Test Markers

Tests should be properly marked with pytest markers to indicate their dependency level:

```python
@pytest.mark.standalone
def test_domain_model_validation():
    # Test code here
```

```python
@pytest.mark.venv
def test_config_file_loading():
    # Test code here
```

```python
@pytest.mark.integration
def test_database_connection():
    # Test code here
```

## Writing Tests

### Naming Conventions

- Test files should be named `test_<component>.py`
- Test functions should be named `test_<function>_<scenario>`
- Test classes should be named `Test<Component>` 

### Test Structure

Follow the Arrange-Act-Assert pattern:

```python
def test_component_function_scenario():
    # Arrange - set up test data and preconditions
    test_data = {"key": "value"}
    component = Component()
    
    # Act - exercise the code being tested
    result = component.function(test_data)
    
    # Assert - verify the results
    assert result.status == "success"
    assert result.value == "expected_value"
```

### Test Independence

Each test should:
- Be independent of other tests
- Clean up after itself
- Not rely on state from previous tests
- Not modify shared state unless absolutely necessary

### Fixtures

Use pytest fixtures for shared setup:

- **Standalone fixtures**: In `/backend/app/tests/standalone/conftest.py`
- **VENV fixtures**: In `/backend/app/tests/venv/conftest.py`
- **Integration fixtures**: In `/backend/app/tests/integration/conftest.py`

Module-specific fixtures should be in that module's own conftest.py file.

## Test Tools and Runners

### Canonical Test Runner

The canonical way to run tests is using the test runner:

```bash
# Run standalone tests only
python backend/scripts/test/runners/run_tests.py --standalone

# Run standalone and venv tests
python backend/scripts/test/runners/run_tests.py --venv

# Run all tests including integration
python backend/scripts/test/runners/run_tests.py --all

# Run with coverage
python backend/scripts/test/runners/run_tests.py --all --coverage

# Run security-focused tests only
python backend/scripts/test/runners/run_tests.py --all --security
```

### Test Analysis Tools

```bash
# Analyze test classification
python backend/scripts/test/tools/test_analyzer.py
```

### Test Migration Tools

```bash
# Run all test suite cleanup steps
python backend/scripts/test/test_suite_cleanup.py --all

# Run specific steps
python backend/scripts/test/test_suite_cleanup.py --step 1
```

## Migration Process

The migration process follows these steps:

1. **Analysis**: Categorize tests by dependency level
2. **Directory Setup**: Create the new directory structure
3. **Test Migration**: Move tests to appropriate locations
4. **Import Fixing**: Update import paths after relocation
5. **Fixture Migration**: Consolidate fixtures in conftest.py files
6. **Verification**: Run tests to ensure they still work
7. **Cleanup**: Remove old test files or directories

Use the test suite cleanup script to perform these steps:

```bash
python backend/scripts/test/test_suite_cleanup.py --all
```

## CI/CD Integration

The CI/CD pipeline should run tests in this order:

1. **Linting and static analysis**
2. **Standalone tests**
3. **VENV tests**
4. **Integration tests**

This ensures fast feedback on issues that are quick to detect.

### Example CI Configuration

```yaml
stages:
  - lint
  - test-standalone
  - test-venv
  - test-integration
  - deploy

lint:
  script:
    - python -m flake8 backend/

test-standalone:
  script:
    - python backend/scripts/test/runners/run_tests.py --standalone

test-venv:
  script:
    - python backend/scripts/test/runners/run_tests.py --venv
  needs:
    - test-standalone

test-integration:
  script:
    - python backend/scripts/test/runners/run_tests.py --integration
  needs:
    - test-venv
```

## Test Coverage Requirements

The Novamind Digital Twin project has specific coverage requirements:

- **Domain Logic**: 95% minimum coverage
- **Application Services**: 90% minimum coverage
- **Infrastructure**: 85% minimum coverage
- **API Endpoints**: 85% minimum coverage
- **Security Components**: 100% coverage

Critical components related to PHI handling, security, and data integrity must have 100% test coverage.

Generate coverage reports using:

```bash
python backend/scripts/test/runners/run_tests.py --all --coverage --html
```

---

This documentation represents the canonical source of truth for the Novamind Digital Twin test suite. Any changes to the testing approach should be reflected in this document.