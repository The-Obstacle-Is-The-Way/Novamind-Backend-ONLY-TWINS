# Novamind Backend Scripts

This directory contains utility scripts for the Novamind Digital Twin backend project.

## Testing

### Unified Test Runner
The preferred way to run tests is through the unified test runner:

```bash
# Run all tests
python -m backend.scripts.run_tests

# Run only unit tests
python -m backend.scripts.run_tests --unit

# Run only ML mock tests (high coverage area)
python -m backend.scripts.run_tests --ml-mock

# Generate coverage report
python -m backend.scripts.run_tests --coverage

# Quick smoke test
python -m backend.scripts.run_tests --quick

# Verbose output
python -m backend.scripts.run_tests --verbose
```

The test runner follows clean architecture principles and provides consistent reporting across all test types.

## Coverage Requirements

- Target coverage: 80% across all code
- ML Mock Services: Maintain >80% coverage for mock implementations
- Domain layer: Maintain >85% coverage
- Security components: Maintain >90% coverage

## Other Utilities

- `generate_compliance_summary.py`: Generates HIPAA compliance report
- `run_hipaa_phi_audit.py`: Audits code for PHI protection 
- `secure_logger.py`: Secure logging utility

## Test Structure

Tests are organized following clean architecture principles:

```
backend/
├── tests/
│   ├── unit/            # Unit tests for isolated components
│   ├── integration/     # Integration tests for component interactions
│   ├── security/        # Security and HIPAA compliance tests
│   └── e2e/             # End-to-end tests
```

All test file names should follow the pattern `test_*.py` to be automatically discovered.
