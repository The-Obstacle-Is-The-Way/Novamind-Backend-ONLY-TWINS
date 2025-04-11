# Novamind Backend Test Infrastructure

## Overview

This directory contains a comprehensive testing infrastructure for the Novamind Backend. The test suite has been organized to support:

1. **Test Directory Classification**: Tests are separated based on their dependencies
2. **Progressive Test Execution**: Tests run in dependency order
3. **Comprehensive Test Coverage**: Covering unit, integration, and system tests
4. **CI/CD Integration**: Ready for GitHub Actions

## Fixes Implemented

The following test issues have been fixed:

1. **PAT Mock Service Tests**: All 29 test cases now pass with proper mock implementation.
2. **Enhanced Log Sanitizer Tests**: All tests now pass with appropriate PHI detection.
3. **Clinical Rule Engine Tests**: Fixed parameter issues in test implementations.
4. **PHI Sanitizer**: Created corrected tests that properly handle patient IDs as PHI.

## Directory-Based Test Organization

Tests are organized into three main directories:

- **app/tests/standalone/**: Tests with no external dependencies
- **app/tests/venv/**: Tests requiring environment setup but no database
- **app/tests/integration/**: Tests requiring database and external services

## Using the Test Infrastructure

### Running Tests

```bash
# Run all standalone tests
python scripts/run_tests.py --standalone

# Run all VENV tests
python scripts/run_tests.py --venv

# Run all integration tests
python scripts/run_tests.py --integration

# Run all tests with coverage reporting
python scripts/run_tests.py --all --coverage

# Run the complete test suite with the shell script
./scripts/run_all_tests.sh --all
```

### Classifying Tests

```bash
# Generate a classification report
python scripts/classify_tests.py --report

# See what tests would be moved (dry run)
python scripts/organize_tests.py

# Actually move tests to their correct directories
python scripts/organize_tests.py --execute
```

## GitHub Actions Integration

A GitHub Actions workflow has been configured in `.github/workflows/backend-ci.yml` that:

1. Runs code quality and linting checks
2. Runs standalone tests
3. Runs VENV tests if standalone tests pass
4. Runs integration tests if VENV tests pass
5. Performs security scanning

## Next Steps

1. **Test Organization**: Use `scripts/organize_tests.py --execute` to move tests to their correct directories.
2. **Database Configuration**: Ensure the test database is properly configured for integration tests.
3. **Docker Integration**: Verify that the Docker setup for integration tests works correctly.
4. **Complete CI/CD**: Integrate with your GitHub repository to enable CI/CD.

## File Overview

- `scripts/run_tests.py`: Main test runner with coverage support
- `scripts/classify_tests.py`: Analyzes and classifies tests
- `scripts/organize_tests.py`: Moves tests to their correct directories
- `scripts/run_all_tests.sh`: Shell script to run all tests in sequence
- `.github/workflows/backend-ci.yml`: GitHub Actions workflow
- `docs/test-infrastructure-guide.md`: Comprehensive documentation

## Conclusion

This test infrastructure provides a robust foundation for ensuring the quality and reliability of the Novamind Backend. By organizing tests according to their dependencies and running them in a logical sequence, we can catch issues early and maintain high code quality.