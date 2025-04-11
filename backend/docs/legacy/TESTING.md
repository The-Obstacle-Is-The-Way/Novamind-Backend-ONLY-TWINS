# Novamind Digital Twin Backend Testing

This document serves as the entry point for understanding the testing infrastructure of the Novamind Digital Twin Backend.

## Key Documentation

- [Test Infrastructure](TEST_INFRASTRUCTURE.md) - Organization, structure, and execution of tests
- [Security Testing](TEST_SECURITY.md) - Security-specific test coverage and compliance

## Test Categories

The Novamind testing infrastructure organizes tests into distinct dependency levels:

1. **Standalone Tests** 
   - No dependencies beyond Python itself
   - Fast to run, ideal for CI/CD early feedback

2. **VENV-Only Tests**
   - Require Python packages but no external services
   - Medium execution speed

3. **DB-Required Tests**
   - Require database connections or other external services
   - Most comprehensive but slowest to run

## Test Tools

### Running Tests

```bash
# Run all tests in dependency order
./scripts/run_tests.sh all

# Run standalone tests only
./scripts/run_tests.sh standalone

# Run venv-only tests
./scripts/run_tests.sh venv

# Run database tests
./scripts/run_tests.sh db

# Generate test dependency report
./scripts/run_tests.sh report
```

### Test Maintenance

```bash
# Classify tests by dependency type
python scripts/classify_tests.py --update

# Find standalone test candidates from unit tests
python scripts/identify_standalone_candidates.py

# Debug test failures
python scripts/debug_test_failures.py
```

## CI/CD Integration

For CI/CD pipelines, tests should be run in dependency order:

1. Linting & Standalone Tests (fastest)
2. VENV Tests (medium speed)
3. DB Tests (slowest, need full environment)

This approach provides faster feedback by catching simple issues early.
