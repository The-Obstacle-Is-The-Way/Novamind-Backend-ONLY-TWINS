# Novamind Backend Test Infrastructure Guide

## Overview

The Novamind Backend test suite has been reorganized to follow a directory-based structure that clearly separates tests based on their dependencies. This approach provides several advantages over using pytest markers:

1. **Clear organization**: Tests are physically separated by their dependency requirements
2. **Faster execution**: Standalone tests can run quickly without setup/teardown overhead
3. **Progressive CI/CD**: Tests can be run in dependency order, stopping early on failures
4. **Easier maintenance**: New developers can easily understand where tests belong

## Test Directories

Tests are organized into three main directories:

### 1. Standalone Tests (`app/tests/standalone/`)

- No external dependencies
- No database or network access
- Fast, focused, and reliable
- Should run in any environment without setup
- Primarily test business logic and domain models
- These tests must pass before proceeding to other test levels

### 2. VENV Tests (`app/tests/venv/`)

- Require Python virtual environment configuration
- May need environment variables or local configuration
- Can access the filesystem but not external services
- No database dependencies
- Example: Tests that read/write local files, use environment variables

### 3. Integration Tests (`app/tests/integration/`)

- Require external dependencies like databases
- May need Docker containers or services
- Test the system as a whole
- Slower and more resource-intensive
- Example: API endpoint tests, database repository tests

## Running Tests

### Using the Test Runner

The `scripts/run_tests.py` script provides a convenient way to run tests:

```bash
# Run standalone tests only
python scripts/run_tests.py --standalone

# Run VENV tests only
python scripts/run_tests.py --venv

# Run integration tests only
python scripts/run_tests.py --integration

# Run all tests in sequence (standalone → venv → integration)
python scripts/run_tests.py --all

# Generate coverage reports
python scripts/run_tests.py --all --coverage
```

### Manual Test Execution

Tests can also be run directly with pytest:

```bash
# Run standalone tests
pytest app/tests/standalone/

# Run VENV tests
pytest app/tests/venv/

# Run integration tests
pytest app/tests/integration/
```

## Test Classification

The `scripts/classify_tests.py` script helps maintain the directory-based organization by analyzing test files and suggesting the correct classification:

```bash
# Generate a classification report
python scripts/classify_tests.py --report

# Move misclassified tests (dry run)
python scripts/classify_tests.py --move --dry-run

# Move misclassified tests to the correct directories
python scripts/classify_tests.py --move
```

## Recent Fixes

The following issues have been resolved:

1. **PAT Mock Service Tests**: Fixed mock implementation to match test expectations, resolving 29 test cases.

2. **Enhanced Log Sanitizer**: Updated to match expected behavior for PHI detection and redaction.

3. **Clinical Rule Engine**: Fixed parameter issues in the implementation.

4. **PHI Sanitizer**: Created updated test fixtures that correctly reflect HIPAA requirements for patient IDs.

## Remaining Work

To complete the test infrastructure:

1. **Test Organization**: Use the classification script to move tests to the appropriate directories.

2. **Test Database Setup**: Create fixtures for database setup/teardown in integration tests.

3. **Docker Compose**: Update the docker-compose.test.yml file to support running all levels of tests.

4. **CI/CD Pipeline**: Implement the GitHub Actions workflow to run tests on PRs and merges.

## Best Practices

1. **Write Standalone Tests First**: Start with standalone tests for all business logic.

2. **Keep Standalone Tests Fast**: Avoid any external dependencies in standalone tests.

3. **Use Mocks Appropriately**: Mock external dependencies in standalone and VENV tests.

4. **Test in Isolation**: Each test should be independent and not rely on the state from other tests.

5. **Follow Naming Conventions**: Use consistent naming for test files and functions to improve discoverability.

6. **Include Both Positive and Negative Tests**: Test both valid and invalid scenarios.

7. **Test Edge Cases**: Ensure boundary conditions are properly handled.

## Contribution Guidelines

When adding new tests:

1. Identify the appropriate test level (standalone, VENV, or integration).
2. Add the test to the correct directory.
3. Run the test to ensure it passes.
4. Add any necessary fixtures or setup code.
5. Include documentation on what the test covers.

By following these guidelines, we can maintain a robust and efficient test suite that ensures the quality and reliability of the Novamind Backend system.