# Test Dependency Classification

## Overview

This document describes the test dependency classification system implemented in the Novamind Digital Twin Backend project. The classification helps organize and run tests based on their external dependency requirements, improving CI/CD efficiency by running independent tests first.

## Dependency Levels

Tests are classified into the following dependency levels:

1. **Standalone Tests**: No dependencies beyond Python itself
   - Can run without any external services or database
   - Fastest to execute, ideal for quick feedback
   - Currently: 95 test files

2. **DB-Required Tests**: Require database connections or other external services
   - Need PostgreSQL, Redis, or other external services
   - Take longer to set up and run
   - Currently: 104 test files

## Classification Tool

The `classify_tests.py` script automatically analyzes test files to determine their dependency level by:

1. Examining import statements
2. Detecting database, Redis, or API-related code
3. Recognizing existing pytest markers

### Usage

```bash
# View dependency classification report
python -m scripts.classify_tests --report-only

# Update tests with appropriate markers
python -m scripts.classify_tests --update

# Dry run to preview marker changes
python -m scripts.classify_tests --dry-run

# Show detailed classification information
python -m scripts.classify_tests --verbose
```

## Integration with Existing Test Infrastructure

The test classification system integrates with the existing test infrastructure:

### In Existing Scripts

The `run_tests.sh` shell script already includes options for running tests by dependency level:

```bash
# Run standalone tests
./run_tests.sh --standalone

# Run venv-dependent tests
./run_tests.sh --venv

# Run DB-dependent tests
./run_tests.sh --db

# Run all tests in order (fastest first)
./run_tests.sh --all
```

### In CI/CD Pipelines

The CI/CD pipelines should be configured to run tests in dependency order:

1. Standalone tests first (for fast feedback)
2. DB-dependent tests afterward

## Test Classification Results

As of the current analysis:

- **Total Test Files**: 199
- **Standalone Tests**: 95 (48%)
- **DB-Required Tests**: 104 (52%)

## Next Steps

1. Run the classifier with `--update` to add appropriate markers to all test files
2. Consider moving pure standalone tests to the `/app/tests/standalone/` directory
3. Ensure CI/CD pipelines leverage this classification for optimal performance