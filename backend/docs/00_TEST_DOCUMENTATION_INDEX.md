# Novamind Digital Twin Testing Framework

## Overview

This document serves as the comprehensive guide to the Novamind Digital Twin testing infrastructure. It provides an overview of our testing philosophy, architecture, and practical guidance for maintaining and extending the test suite.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Organization](#test-organization)
3. [Test Types](#test-types)
4. [Running Tests](#running-tests)
5. [Test Documentation](#test-documentation)
6. [Adding New Tests](#adding-new-tests)
7. [Continuous Integration](#continuous-integration)
8. [HIPAA Compliance in Testing](#hipaa-compliance-in-testing)
9. [Performance and Scalability Testing](#performance-and-scalability-testing)
10. [Further Reading](#further-reading)

## Testing Philosophy

The Novamind Digital Twin project follows these core testing principles:

- **Clean Tests**: Tests should be readable, maintainable, and follow SOLID principles
- **Fast Feedback**: Tests should run quickly to provide rapid developer feedback
- **Isolation**: Tests should be independent and not rely on other tests
- **Deterministic**: Tests should produce the same result every time they run
- **Comprehensive**: Tests should cover business logic, security, and integration points

Our testing strategy is built on a "shift-left" approach, where testing begins early in the development cycle and defects are caught before they reach production. We prioritize test organization by dependency level to enable rapid, incremental testing during development.

## Test Organization

### Directory-Based SSOT Approach

We organize tests using a directory-based Single Source of Truth (SSOT) approach, where tests are categorized by their external dependencies rather than by the traditional unit/integration classification:

```
backend/app/tests/
├── standalone/     # Tests with no external dependencies (fastest)
├── venv/           # Tests requiring Python packages but no external services
├── integration/    # Tests requiring external services like databases
└── security/       # Cross-cutting security and HIPAA compliance tests
```

This organization allows for efficient test execution, starting with the fastest, most isolated tests and progressively moving to more integrated tests.

## Test Types

### Standalone Tests

- **Dependencies**: None beyond the Python standard library and pytest
- **Examples**: Domain model tests, utility function tests, pure business logic
- **Run Time**: Fastest (milliseconds to seconds)
- **When to Run**: Continuously during development

### VENV Tests

- **Dependencies**: Python packages like FastAPI, SQLAlchemy, numpy, pandas
- **Examples**: Pydantic model validation, service layer tests with mocks
- **Run Time**: Medium (seconds to minutes)
- **When to Run**: After code changes, before commits

### Integration Tests

- **Dependencies**: External services like databases, Redis, third-party APIs
- **Examples**: Repository tests, API endpoint tests, workflow tests
- **Run Time**: Slowest (minutes)
- **When to Run**: Before PRs, in CI/CD pipelines

### Security Tests

- **Dependencies**: Varies (can be standalone, venv, or integration)
- **Examples**: Authentication tests, authorization tests, PHI handling
- **Run Time**: Varies
- **When to Run**: Before PRs, in CI/CD pipelines

## Running Tests

### Using the Canonical Test Runner

Our primary test runner is `backend/scripts/test/runners/run_tests.py`, which provides flexible options for running different test categories:

```bash
# Run standalone tests only
python backend/scripts/test/runners/run_tests.py --standalone

# Run all tests
python backend/scripts/test/runners/run_tests.py --all

# Run with coverage
python backend/scripts/test/runners/run_tests.py --all --coverage

# Run security tests across all levels
python backend/scripts/test/runners/run_tests.py --all --markers security
```

See [Test Scripts Implementation](06_TEST_SCRIPTS_IMPLEMENTATION.md) for detailed documentation of the test runner.

### Using pytest Directly

For more targeted testing during development, you can use pytest directly:

```bash
# Run a specific test file
pytest backend/app/tests/standalone/test_neurotransmitter_model.py

# Run tests matching a pattern
pytest backend/app/tests/standalone/ -k "neurotransmitter"

# Run tests with specific markers
pytest backend/app/tests/ -m "security"
```

## Test Documentation

Our test documentation consists of the following documents:

1. [Test Suite Analysis](01_TEST_SUITE_ANALYSIS.md) - Analysis of the current test suite structure
2. [Test Best Practices](02_TEST_BEST_PRACTICES.md) - Guidelines for writing effective tests
3. [Test Fixtures Guide](03_TEST_FIXTURES_GUIDE.md) - Documentation for shared test fixtures
4. [Test Mocking Strategy](04_TEST_MOCKING_STRATEGY.md) - Approach to mocking dependencies
5. [Test Scripts Analysis](05_TEST_SCRIPTS_ANALYSIS.md) - Analysis of test automation scripts
6. [Test Scripts Implementation](06_TEST_SCRIPTS_IMPLEMENTATION.md) - Implementation details for test scripts

## Adding New Tests

When adding new tests to the Novamind Digital Twin platform, follow these guidelines:

1. **Determine Dependency Level**: Identify whether your test is standalone, venv, or integration
2. **Place in Correct Directory**: Add the test file to the appropriate directory
3. **Follow Naming Conventions**: Name test files with `test_` prefix
4. **Add Appropriate Markers**: Use pytest markers like `@pytest.mark.security` for special categories
5. **Use Fixtures Correctly**: Leverage existing fixtures; create new ones if needed
6. **Ensure Independence**: Tests should not depend on other tests

Example of adding a new standalone test:

```python
# backend/app/tests/standalone/test_patient_model.py
import pytest
from app.domain.models.patient import Patient

def test_patient_name_formatting():
    """Test that patient names are formatted correctly."""
    patient = Patient(first_name="John", last_name="Doe")
    assert patient.full_name == "John Doe"
```

## Continuous Integration

Our CI/CD pipeline automatically runs tests on branches and pull requests, following this sequence:

1. **Early Stage**: Run standalone tests only
2. **Mid Stage**: Add venv tests if standalone tests pass
3. **Late Stage**: Run integration tests if earlier tests pass
4. **Final Stage**: Run security tests and generate reports

See the CI configuration in `.github/workflows/test.yml` for implementation details.

## HIPAA Compliance in Testing

The Novamind Digital Twin platform requires special consideration for HIPAA compliance in testing:

- **Synthetic Data**: All test data must be synthetic, never real PHI
- **Data Sanitization**: Test output must be sanitized to avoid accidental PHI exposure
- **Comprehensive Coverage**: Security tests must cover all HIPAA Security Rule requirements
- **PHI Handling**: Tests must verify proper encryption, access controls, and audit logging

See our [HIPAA Compliance Testing Guide](backend/docs/legacy/hipaa_compliance_testing.md) for detailed information.

## Performance and Scalability Testing

In addition to functional testing, we conduct performance and scalability testing:

- **Load Tests**: Verify system behavior under expected load
- **Stress Tests**: Identify breaking points under extreme conditions
- **Endurance Tests**: Verify system stability over extended periods
- **Scalability Tests**: Verify system can scale with increasing load

These tests are run on a scheduled basis in our CI/CD pipeline, not as part of the regular development cycle.

## Further Reading

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html)
- [Clean Architecture in Python](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)