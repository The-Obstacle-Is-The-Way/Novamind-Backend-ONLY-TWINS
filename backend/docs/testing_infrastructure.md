# Novamind Digital Twin Testing Infrastructure

This document describes the testing infrastructure for the Novamind Digital Twin backend platform, including test classification, organization, and execution strategies.

## Testing Philosophy

The Novamind testing infrastructure follows a dependency-based organization strategy that optimizes for:

1. **Fast feedback** - Tests with fewer dependencies run first to provide quick feedback
2. **Isolation** - Tests are categorized based on their dependency requirements
3. **Reliability** - Tests that require complex setups run in controlled environments
4. **Maintainability** - Clear separation of test types makes maintenance easier

## Test Classification

Tests are categorized into three primary dependency levels:

### 1. Standalone Tests

Standalone tests have **no external dependencies** beyond Python itself. These tests:
- Evaluate pure business logic, utilities, and data structures
- Can run in complete isolation (no network, no database, minimal imports)
- Provide the fastest feedback in CI/CD pipelines
- Are located in `app/tests/standalone/`
- Are marked with `@pytest.mark.standalone`

Examples: 
- Validation functions
- Data transformations
- Model logic
- Utility functions

### 2. VENV-Only Tests

VENV-only tests require Python packages but **no external services** (like databases). These tests:
- Depend on external Python packages but not infrastructure
- May use mocking to avoid real external dependencies
- Are generally unit tests for framework-dependent code
- Are located throughout `app/tests/unit/`
- Are marked with `@pytest.mark.venv_only`

Examples:
- FastAPI endpoint unit tests with mocked dependencies
- Pydantic model validation
- Service layer tests with mocked repositories

### 3. DB-Required Tests

DB-required tests depend on **database connections or other external services**. These tests:
- Need a running database (PostgreSQL)
- May need other services (Redis, external APIs, etc.)
- Verify integration with external systems
- Are located in `app/tests/integration/` or `app/tests/repository/`
- Are marked with `@pytest.mark.db_required`

Examples:
- Repository tests with real database connections
- API integration tests
- End-to-end workflow tests

## Directory Structure

```
app/tests/
├── standalone/          # Tests with no dependencies
├── unit/                # Tests requiring VENV but no external services
├── integration/         # Tests requiring external services
├── repository/          # Tests specifically for database repositories
├── security/            # Security-specific tests
├── conftest.py          # Test fixtures and configuration
└── helpers/             # Test helpers and utilities
```

## Test Execution

Tests can be executed in several ways:

### 1. Running All Tests

```bash
# Run all tests
python -m pytest
```

### 2. Running Tests by Dependency Level

```bash
# Standalone tests only
python -m pytest -m standalone

# VENV-only tests
python -m pytest -m venv_only

# DB-required tests
python -m pytest -m db_required
```

### 3. Using the Multi-Stage Test Runner

```bash
# Run all tests in dependency order
python scripts/run_tests_by_dependency.py

# Run just standalone tests
python scripts/run_tests_by_dependency.py --stage standalone

# Generate JUnit reports
python scripts/run_tests_by_dependency.py --junit
```

## Test Utilities

The project includes several utilities for managing and organizing tests:

### 1. Test Classification

```bash
# Analyze and classify tests by dependency
python scripts/classify_tests.py

# Update tests with appropriate markers
python scripts/classify_tests.py --update

# Generate a classification report
python scripts/classify_tests.py --report
```

### 2. Standalone Test Identification

```bash
# Identify unit tests that could be standalone
python scripts/identify_standalone_candidates.py

# Show detailed analysis
python scripts/identify_standalone_candidates.py --verbose

# Migrate eligible tests to standalone
python scripts/identify_standalone_candidates.py --migrate
```

### 3. Test Database Setup

For DB-dependent tests, the project provides Docker Compose configuration:

```bash
# Start test database containers
docker-compose -f docker-compose.test.yml up -d

# Run tests against the containers
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/novamind_test python -m pytest -m db_required
```

## CI/CD Integration

The testing infrastructure integrates with GitHub Actions for continuous integration. The workflow:

1. Runs standalone tests first (fastest feedback)
2. Then runs VENV-only tests
3. Finally runs DB-required tests with Docker containers for dependencies
4. Generates test reports for all stages

This approach provides the fastest possible feedback in the CI pipeline, failing early on simple issues before spending resources on complex test setups.

## Guidelines for Writing Tests

When writing new tests, follow these guidelines:

1. **Determine the dependency level** - What's the minimum dependency your test needs?
2. **Place tests in the appropriate directory** - Based on dependency level
3. **Add the correct pytest marker** - `standalone`, `venv_only`, or `db_required`
4. **Minimize dependencies** - Less is better, especially for frequently run tests
5. **Isolation is key** - Tests should not depend on other tests or shared state

### Example: Converting a Unit Test to Standalone

Many unit tests can be converted to standalone by:
1. Mocking external dependencies
2. Focusing on pure business logic
3. Using the `identify_standalone_candidates.py` script to assist

## Test Coverage

Test coverage reports can be generated with:

```bash
# Generate coverage report
python -m pytest --cov=app --cov-report=html

# View the report
open coverage_html/index.html