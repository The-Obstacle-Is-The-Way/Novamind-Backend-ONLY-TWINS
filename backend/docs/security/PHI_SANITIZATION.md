# PHI Sanitization and HIPAA Compliance

This document describes the PHI (Protected Health Information) sanitization framework implemented in the Novamind platform to ensure HIPAA compliance and protection of sensitive patient data.

## Overview

The PHI sanitization framework is designed to prevent accidental exposure of PHI in logs, error messages, and other non-secure channels. It provides comprehensive detection and sanitization of PHI across the platform.

## Key Components

### 1. PHI Sanitizer

The `PHISanitizer` class (`app/core/utils/phi_sanitizer.py`) is the core component responsible for detecting and sanitizing PHI. It provides:

- Pattern-based detection of common PHI types (SSNs, emails, phone numbers, etc.)
- Context-aware sanitization that preserves data format while removing sensitive content
- Support for both simple text and complex structured data
- Configurable sanitization strategies for different PHI types

### 2. HIPAA-Compliant Logger

The `HIPAACompliantLogger` class (`app/core/utils/logging.py`) extends the standard Python logger with automatic PHI sanitization capabilities:

- Sanitizes all log messages before they are written to logs
- Handles structured data in log context
- Preserves non-PHI information for debugging purposes
- Maintains audit logs for compliance reporting

### 3. Data Encryption

The platform implements robust data encryption for PHI:

- Field-level encryption in the database for PHI fields
- Transparent encryption/decryption via the ORM layer
- Secure key management using AWS KMS (or equivalent)
- Separation of encryption concerns from business logic

## Usage Guidelines

### Logging with PHI Sanitization

Always use the `HIPAACompliantLogger` instead of standard Python loggers:

```python
from app.core.utils.logging import get_hipaa_compliant_logger

logger = get_hipaa_compliant_logger(__name__)

# Safe logging - PHI will be automatically sanitized
logger.info(f"Processing request for patient {patient_email}")
```

### Manual PHI Sanitization

For cases requiring explicit sanitization:

```python
from app.core.utils.phi_sanitizer import PHISanitizer

# Sanitize a single string
safe_text = PHISanitizer.sanitize_text(text_with_phi)

# Sanitize structured data (dict, list, etc.)
safe_data = PHISanitizer.sanitize_structured_data(data_with_phi)
```

### Error Handling

When handling exceptions that might contain PHI:

```python
try:
    # Operation that might contain PHI
    process_patient_data(patient)
except Exception as e:
    # Sanitize exception message before logging
    from app.core.utils.phi_sanitizer import sanitize_log_message
    sanitized_error = sanitize_log_message(str(e))
    logger.error(f"Error processing data: {sanitized_error}")
    raise  # Re-raise the original exception
```

## Testing and Verification

The PHI sanitization framework includes comprehensive test coverage:

- Unit tests for PHI detection and sanitization
- Integration tests for cross-module PHI protection
- HIPAA compliance audit scripts

Run the PHI audit to verify compliance:

```bash
./scripts/run_phi_audit.sh
```

## PHI Types Handled

The sanitization framework handles the following PHI types:

| PHI Type | Example | Sanitized Form |
|----------|---------|----------------|
| Email addresses | patient@example.com | [REDACTED_EMAIL]@example.com |
| Phone numbers | 555-123-4567 | 555-000-0000 |
| SSNs | 123-45-6789 | 000-00-0000 |
| Dates of birth | 1980-01-01 | YYYY-MM-DD |
| Names | John Smith | [REDACTED_NAME] |
| Addresses | 123 Main St | [REDACTED_ADDRESS] |
| Credit card numbers | 4111-1111-1111-1111 | [REDACTED_CREDIT_CARD] |
| Medical record numbers | MRN-12345 | [REDACTED_MRN] |

## Configuration

PHI sanitization settings can be configured in the `.env` file:

```
# PHI Sanitization Configuration
PHI_SANITIZATION_ENABLED=true
PHI_LOG_SANITIZATION_LEVEL=HIGH  # Options: BASIC, MEDIUM, HIGH
PHI_KNOWN_TEST_VALUES_ENABLED=true
```

## Best Practices

1. **Never disable PHI sanitization** in production environments
2. **Don't bypass the sanitization** by using direct string concatenation
3. **Use structured logging** with the `extra` parameter to maintain context
4. **Regularly audit logs** for potential PHI leakage
5. **Update PHI patterns** as new formats are identified

## Compliance Verification

The `run_hipaa_phi_audit.py` script performs comprehensive verification of PHI handling:

- Tests PHI detection and sanitization
- Checks for PHI in system logs
- Verifies database encryption for PHI fields
- Generates compliance reports

Run this audit regularly to ensure ongoing compliance.