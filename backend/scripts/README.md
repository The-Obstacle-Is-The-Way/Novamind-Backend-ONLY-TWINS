# Novamind Digital Twin Backend Scripts

This directory contains utility scripts for the Novamind Digital Twin Backend project. The scripts have been organized into clear categories to facilitate development, testing, and maintenance.

## Core Test Infrastructure

| Script | Description |
|--------|-------------|
| `run_tests.sh` | **Main entry point** for running tests. Supports different dependency levels (standalone, venv, db) |
| `run_dependency_tests.py` | Python implementation of dependency-based test runner |
| `classify_tests.py` | Tool to classify tests by dependency level and update markers |
| `debug_test_failures.py` | Tool for diagnosing and debugging test failures |
| `identify_standalone_candidates.py` | Identifies tests that could be converted to standalone tests |
| `run_simple_test.py` | Creates and runs a minimal test to verify test infrastructure |

## Test Environment Setup

| Script | Description |
|--------|-------------|
| `run_test_environment.sh` | Sets up Docker-based test environment with databases |
| `install-test-dependencies.sh` | Installs all test dependencies |

## Reporting Tools

| Script | Description |
|--------|-------------|
| `generate_coverage_report.py` | Generates test coverage reports |
| `generate_compliance_summary.py` | Creates compliance documentation for HIPAA |
| `run_hipaa_phi_audit.py` | Scans codebase for potential PHI exposure risks |

## Maintenance Utilities

| Script | Description |
|--------|-------------|
| `fix_datetime_tests.py` | Fixes datetime-related test issues |
| `fix_db_driver.py` | Configures database drivers correctly |
| `fix_utcnow_deprecation.py` | Updates deprecated utcnow calls |
| `lint_tests.py` | Lints test files for code quality |
| `secure_logger.py` | Security-enhanced logging functionality |

## Usage Examples

### Running Tests

```bash
# Run all tests in dependency order
./run_tests.sh all

# Run only standalone tests
./run_tests.sh standalone

# Run venv-dependent tests with coverage
./run_tests.sh venv --coverage

# Run database tests with verbose output
./run_tests.sh db --verbose
```

### Test Classification

```bash
# Classify tests by dependency
python classify_tests.py --update

# Identify standalone test candidates
python identify_standalone_candidates.py
```

### Generating Reports

```bash
# Generate test coverage report
python generate_coverage_report.py

# Run HIPAA PHI audit
python run_hipaa_phi_audit.py
```

## Note on Legacy Scripts

Older scripts have been archived in the `legacy_backup` directory. These are maintained for reference but should not be used for new development.

For detailed documentation on the test infrastructure, see `/backend/docs/TEST_INFRASTRUCTURE.md`.
