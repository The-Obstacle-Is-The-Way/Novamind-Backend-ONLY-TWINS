# Novamind Backend Test Suite

This directory contains the comprehensive test suite for the Novamind Backend. The tests are organized into several categories based on their dependencies and requirements.

## Test Organization

The tests are organized into three main categories:

1. **Standalone Tests** (`app/tests/standalone/`)
   - Tests that have no external dependencies (no DB, no network, no files)
   - Can run in isolation without any setup
   - Ideal for unit testing and mock-based testing
   - Use fixtures to mock out dependencies when needed

2. **VENV Tests** (`app/tests/venv/`)
   - Tests that require the virtual environment but no external services
   - May access the filesystem but don't require Docker or databases
   - Used for integration tests between components that don't need external services

3. **Integration Tests** (`app/tests/integration/`)
   - Tests that require external services (DB, network, etc.)
   - Run in Docker environment with all services
   - Test complete end-to-end workflows
   - Closest to real-world usage

## Running Tests

### Using the Test Runner Script

We've created a comprehensive test runner script that handles running tests in the correct order with proper isolation. 

```bash
# Run all tests in order (standalone → venv → integration)
./scripts/run_tests.py

# Run only standalone tests
./scripts/run_tests.py --skip-venv --skip-integration

# Run specific test files
./scripts/run_tests.py app/tests/standalone/test_enhanced_log_sanitizer.py

# Continue running tests even if previous stages fail
./scripts/run_tests.py --continue-on-failure

# Show commands without executing them
./scripts/run_tests.py --dry-run
```

### Using pytest Directly

You can also run the tests directly with pytest:

```bash
# Run all standalone tests with coverage
python -m pytest app/tests/standalone/ --cov=app --cov-report=html:coverage_html/standalone_tests

# Run a specific test file
python -m pytest app/tests/standalone/test_enhanced_log_sanitizer.py

# Run a specific test class or method
python -m pytest app/tests/standalone/test_enhanced_log_sanitizer.py::TestPatternRepository
python -m pytest app/tests/standalone/test_enhanced_log_sanitizer.py::TestPatternRepository::test_default_patterns
```

### Running Integration Tests

Integration tests require Docker and external services:

```bash
# Start the test environment
docker-compose -f docker-compose.test.yml up -d

# Run the integration tests
docker-compose -f docker-compose.test.yml exec app python -m pytest app/tests/integration/

# Stop the test environment
docker-compose -f docker-compose.test.yml down
```

## Test Utilities and Helpers

### Test Classification

You can generate a comprehensive report of all tests in the project:

```bash
./scripts/create_test_classification.py
```

This will produce a Markdown report (`test-classification-report.md`) with details about:
- Total number of tests
- Tests by category
- Dependencies for each test file
- Fixtures and mocks used
- Special requirements

### Fixing Common Issues

We've created scripts to fix common issues with the tests:

```bash
# Fix PAT mock service issues
./scripts/fix_pat_mock.py
```

## Writing New Tests

When adding new tests, follow these guidelines:

1. **Choose the right category**:
   - If your test has no external dependencies, put it in `standalone/`
   - If it requires local environment features but no database, put it in `venv/`
   - If it requires external services or databases, put it in `integration/`

2. **Use proper naming conventions**:
   - Test files should be named `test_*.py`
   - Test classes should be named `Test*` and inherit from `unittest.TestCase` or pytest fixtures
   - Test methods should be named `test_*`

3. **Use fixtures and mocking**:
   - For standalone tests, mock all external dependencies
   - Use pytest fixtures for setup and teardown
   - Create reusable fixtures in `conftest.py` files

4. **Document special requirements**:
   - Add clear docstrings to tests with special requirements
   - Include information about what's being tested and any assumptions

## Test Coverage

We track code coverage for each category of tests:

- Standalone test coverage: `coverage_html/standalone_tests/`
- VENV test coverage: `coverage_html/venv_tests/`
- Integration test coverage: `coverage_html/integration_tests/`

The goal is to achieve:
- 90%+ coverage for critical path code
- 80%+ overall coverage
- 100% coverage for security-related code

## Troubleshooting

### Common Issues

1. **Tests fail in CI but pass locally**:
   - Check for race conditions or time-dependent tests
   - Ensure tests clean up resources properly
   - Look for environment differences

2. **Tests suddenly failing**:
   - Check recent changes to dependencies
   - Look for changes to the database schema
   - Verify test data hasn't been corrupted

3. **Slow tests**:
   - Use profiling to identify slow tests
   - Consider moving slow tests to a separate group
   - Look for opportunities to parallelize tests

### Getting Help

If you're struggling with tests, check:
- The test documentation in `docs/testing.md`
- Existing test patterns in the codebase
- Ask other team members for assistance