# Novamind Digital Twin Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the Novamind Digital Twin platform, including test classification, organization, execution, and CI/CD integration.

## Testing Hierarchy

The Novamind testing approach follows a hierarchical, dependency-based organization that optimizes for early feedback and reliability:

```
Standalone Tests → VENV Tests → Integration Tests
(fastest, least     (framework-   (database, external
 dependencies)      dependent)     services)
```

### Test Classification

Tests are categorized into three primary dependency levels:

1. **Standalone Tests**
   - No external dependencies beyond Python standard library
   - Test pure business logic, utilities, domain models
   - Run in complete isolation (no DB, no network)
   - Located in `app/tests/standalone/`

2. **VENV Tests**
   - Require Python packages but no external services
   - May use mocking to avoid real infrastructure
   - Test framework-dependent code with isolation
   - Located in `app/tests/venv/`

3. **Integration Tests**
   - Require database and/or external services
   - Test real interactions with infrastructure
   - Verify system integration and workflows
   - Located in `app/tests/integration/`

## Directory Structure

The test directories are organized by dependency level, not by the units they test. This approach enables faster test execution and clearer separation of concerns:

```
app/tests/
├── standalone/          # No external dependencies
├── venv/                # Framework dependencies only
├── integration/         # External service dependencies
├── conftest.py          # Shared fixtures
└── helpers/             # Test utilities
```

## Testing Tools

### Test Runner

The `scripts/run_tests.py` script enables progressive test execution:

```bash
# Run standalone tests
python scripts/run_tests.py --standalone

# Run VENV tests
python scripts/run_tests.py --venv

# Run integration tests
python scripts/run_tests.py --integration

# Run all tests with coverage
python scripts/run_tests.py --all --coverage
```

### Test Classification

The `scripts/classify_tests.py` script helps maintain proper test organization:

```bash
# Generate a classification report
python scripts/classify_tests.py --report
```

### Test Organization

The `scripts/organize_tests.py` script can automatically move tests to their correct directories:

```bash
# Preview test organization (dry run)
python scripts/organize_tests.py

# Move tests to appropriate directories
python scripts/organize_tests.py --execute
```

## CI/CD Integration

Our GitHub Actions workflow executes tests progressively:

1. Code quality checks (linting, type checking)
2. Standalone tests
3. VENV tests (if standalone pass)
4. Integration tests (if VENV tests pass)
5. Security scanning

This approach provides quick feedback on failures and optimizes CI resources.

## Test Coverage Targets

- **Domain layer**: 90% coverage
- **Application layer**: 85% coverage
- **Infrastructure layer**: 75% coverage
- **Overall coverage target**: 80%

Test coverage reports are generated as part of the CI process and can be viewed in the job artifacts.

## Mock Services

For tests requiring external services, we provide mock implementations:

- **MockPATService** - For Physical Activity Tracking services
- **MockMentalLamaService** - For AI-assisted analysis
- **MockDigitalTwinService** - For digital twin simulations

These mocks ensure tests can run without external dependencies while still providing realistic behavior.

## HIPAA-Compliant Testing

All tests must respect HIPAA guidelines:

- No real PHI in test data
- All test data must be sanitized
- Test database connections must be secure
- Test coverage must include PHI sanitization

## Test Environment Setup

Integration tests require a configured environment:

```bash
# Start test database
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
python scripts/run_tests.py --integration
```

## Writing Effective Tests

When writing new tests:

1. **Determine the minimum dependency level** needed for your test
2. **Place the test in the correct directory**
3. **Use appropriate mocks** to minimize dependencies
4. **Create isolated tests** that don't depend on other tests
5. **Test both positive and negative cases**

## Conclusion

This testing strategy ensures our code is robust, reliable, and maintainable. By organizing tests by dependency level, we optimize for both speed and thoroughness in our CI/CD pipeline.