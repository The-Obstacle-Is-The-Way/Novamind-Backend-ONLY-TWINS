# Novamind Backend - Canonical Scripts

This directory contains only the essential, canonical scripts for the Novamind Backend project. All redundant, platform-specific, and legacy scripts have been removed to maintain a clean, minimal codebase.

## Core Scripts

| Script | Purpose |
|--------|---------|
| `unified_hipaa_security_suite.py` | Comprehensive security testing framework for static analysis, PHI detection, API security validation, configuration checking, and HIPAA compliance |
| `unified_test_runner.py` | Cross-platform, layer-aware test runner with coverage reporting for all Clean Architecture layers |
| `secure_logger.py` | HIPAA-compliant logging that automatically sanitizes PHI from log messages |
| `novamind_cleanup.py` | Canonical codebase cleanup script that maintains this ultra-clean state |

## Usage Guidelines

### Unified HIPAA Security Suite

```bash
python scripts/unified_hipaa_security_suite.py
```

Comprehensive security testing in one command. Generates reports in `security-reports/`.

### Unified Test Runner

```bash
# Run all tests
python scripts/unified_test_runner.py

# Run specific layer tests
python scripts/unified_test_runner.py --layer domain

# Run specific module tests
python scripts/unified_test_runner.py --module temporal_neurotransmitter

# Generate coverage report
python scripts/unified_test_runner.py --coverage --html
```

### Secure Logger

```python
from scripts.secure_logger import get_logger

logger = get_logger(__name__)
logger.info("Processing patient data")  # PHI automatically sanitized
```

### Codebase Cleanup

```bash
# See what would be deleted without making changes
python scripts/novamind_cleanup.py --dry-run

# Create backups before deletion
python scripts/novamind_cleanup.py --backup

# Perform cleanup
python scripts/novamind_cleanup.py
```

## Development Principles

1. **Canonical Minimalism**: Only essential scripts should exist
2. **Zero Redundancy**: No duplicate functionality
3. **Cross-Platform by Default**: No platform-specific implementations
4. **Clean Architecture**: Scripts respect architectural boundaries
5. **HIPAA Compliance**: Security and privacy by design

## Canonical Tests

Only these essential tests are maintained:

1. **Domain Layer**:
   - `app/tests/domain/entities/test_neurotransmitter_mapping.py`
   - `app/tests/domain/entities/test_temporal_neurotransmitter.py`
   - `app/tests/domain/services/test_enhanced_xgboost_service.py`

2. **Application Layer**:
   - `app/tests/application/services/test_temporal_neurotransmitter_service.py`

3. **Infrastructure Layer**:
   - `app/tests/infrastructure/repositories/test_temporal_event_repository.py`
   - `app/tests/infrastructure/repositories/test_temporal_sequence_repository.py`
   - `app/tests/infrastructure/services/test_mock_enhanced_digital_twin_neurotransmitter_service.py`

4. **Integration**:
   - `app/tests/integration/test_digital_twin_integration.py`
   - `app/tests/integration/test_temporal_neurotransmitter_integration.py`
