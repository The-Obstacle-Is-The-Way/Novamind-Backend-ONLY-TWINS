# PHI Log Sanitization Framework for HIPAA Compliance

## Overview

Log sanitization is a critical component of HIPAA compliance in healthcare applications. This document outlines the principles, implementation strategies, and configuration for the PHI Log Sanitization system used in the Novamind concierge psychiatry platform.

## HIPAA Requirements for Log Sanitization

The HIPAA Security Rule (45 CFR §164.312) requires appropriate technical safeguards to prevent unauthorized access to PHI. For logging systems, this means:

1. **No PHI in logs** - Logs must not contain identifiable patient information
2. **Audit trails** - Must maintain records of system activities without exposing PHI
3. **Access controls** - Log files must be protected from unauthorized access
4. **Integrity controls** - Log data must be protected from tampering

## Architecture

The PHI log sanitization system uses a multi-layered approach:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Logger Input   │────▶│ PHI Detection   │────▶│ PHI Redaction   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               ▲                        │
                               │                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  PHI Patterns   │     │  Sanitized Log  │
                        └─────────────────┘     └─────────────────┘
```

## PHI Detection Methods

The system uses four complementary methods to detect PHI:

1. **Pattern-based detection** - Uses regex patterns to identify PHI such as:
   - Patient IDs
   - Phone numbers
   - Email addresses
   - Social Security Numbers
   - Credit card numbers
   - Medical record numbers

2. **Key-based detection** - Identifies PHI based on dictionary keys like:
   - `ssn`
   - `dob`
   - `patient_id`
   - `first_name` + `last_name` (when combined)

3. **Context-based detection** - Uses surrounding terms to infer PHI
   - Words like "patient", "doctor", "medical record" near identifiers

4. **ML-enhanced detection** (optional extension) - Uses NLP techniques to identify PHI in natural language

## Configuration System

### Pattern Configuration File (phi_patterns.yaml)

```yaml
# Example phi_patterns.yaml
patterns:
  - name: "Patient ID"
    pattern: "PT\\d{6,8}"
    type: "regex"
    priority: 10
    partial_redaction_length: 4
    examples: ["PT12345678", "PT987654"]
    
  - name: "Social Security Number"
    pattern: "\\d{3}-\\d{2}-\\d{4}"
    type: "regex" 
    priority: 10
    partial_redaction_length: 4
    examples: ["123-45-6789"]
    
  - name: "Email Address"
    pattern: "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    type: "regex"
    priority: 8
    # For emails, preserve the domain only in partial mode
    partial_format: "xxxx@{domain}"
    examples: ["patient@example.com", "doctor.name@hospital.org"]
    
  - name: "Phone Number"
    pattern: "\\(\\d{3}\\)\\s*\\d{3}-\\d{4}|\\d{3}-\\d{3}-\\d{4}"
    type: "regex"
    priority: 7
    partial_redaction_length: 4
    examples: ["(555) 123-4567", "555-123-4567"]

sensitive_keys:
  - name: "SSN"
    keys: ["ssn", "social_security", "social_security_number"]
    priority: 10
    
  - name: "DOB"
    keys: ["dob", "date_of_birth", "birth_date"]
    priority: 9
    
  - name: "Credit Card"
    keys: ["credit_card", "cc_number", "card_number"]
    priority: 10
```

### Redaction Modes

The system supports three redaction modes:

1. **Full redaction** - Replaces the entire value with `[REDACTED]`
2. **Partial redaction** - Shows only a portion of the value (e.g., last 4 digits)
3. **Hash redaction** - Replaces the value with a consistent hash

### Configuration Settings

```python
class LogSanitizerConfig:
    # Default configuration
    redaction_mode: RedactionMode = RedactionMode.FULL
    partial_redaction_length: int = 4
    redaction_marker: str = "[REDACTED]"
    hash_algorithm: str = "sha256"
    hash_length: int = 8
    pattern_file_path: str = "phi_patterns.yaml"
    enable_key_detection: bool = True
    enable_pattern_detection: bool = True
    enable_context_detection: bool = True
    allow_logging_non_phi: bool = True  # Critical for test logs to work
    
    # Performance settings
    max_pattern_cache_size: int = 1000
    max_string_scan_length: int = 10000  # For performance
```

## Implementation Best Practices

### 1. Selective Sanitization

Only sanitize actual PHI, not all data. Over-sanitization reduces the usefulness of logs.

```python
# Bad - Over-sanitization
log_message = "[REDACTED]: [REDACTED]: [REDACTED] [Patient ID ending in 4321]"

# Good - Selective sanitization
log_message = "User login: admin viewed [Patient ID ending in 4321]"
```

### 2. Nested Dictionary Handling

When sanitizing nested dictionaries, process each level while preserving structure.

```python
data = {
    "user_id": "admin123",  # Not PHI
    "patient": {
        "first_name": "John",  # PHI
        "last_name": "Doe",    # PHI
        "notes": "Normal checkup"  # Not PHI
    }
}

# Should become:
sanitized = {
    "user_id": "admin123",
    "patient": {
        "first_name": "[REDACTED]",
        "last_name": "[REDACTED]",
        "notes": "Normal checkup"
    }
}
```

### 3. Handling Special Cases

Some data requires special handling to maintain its utility while removing PHI:

- **Dates**: Consider keeping the year but redacting month/day
- **Addresses**: Keep city/state but redact street address
- **Names**: Consider initials instead of full redaction

### 4. Default Fallbacks

Always include default patterns when the pattern file is not found:

```python
DEFAULT_PHI_PATTERNS = [
    PHIPattern(
        name="Social Security Number",
        pattern=r"\b\d{3}-\d{2}-\d{4}\b",
        type=PatternType.REGEX,
        priority=10
    ),
    PHIPattern(
        name="Email Address",
        pattern=r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
        type=PatternType.REGEX,
        priority=8
    ),
    # Add more default patterns here
]
```

### 5. Regular Expression Optimization

Optimize regex patterns for performance:

- Use non-capturing groups `(?:...)` when possible
- Limit backtracking with possessive quantifiers `++` or atomic groups `(?>...)`
- Pre-compile patterns for reuse

## Integration Points

### 1. Logger Integration

```python
# Create sanitized logger
logger = get_sanitized_logger(__name__)

# Use normally
logger.info("Processed data for patient with ID PT12345")  # Will be sanitized
```

### 2. Middleware Integration

```python
# For FastAPI middleware
@app.middleware("http")
async def log_sanitization_middleware(request: Request, call_next):
    response = await call_next(request)
    # Sanitize request and response logs
    sanitized_request = log_sanitizer.sanitize_dict(request_data)
    logger.info(f"Request processed: {sanitized_request}")
    return response
```

### 3. Decorator Usage

```python
@sanitize_logs()
def process_patient_data(patient_id, data):
    # All logs in this function will be automatically sanitized
    logger.info(f"Processing data for {patient_id}")
    return processed_data
```

## Testing and Validation

### 1. Verification Tests

Create comprehensive tests to verify sanitization:

- Test all PHI pattern types (SSN, email, etc.)
- Test boundary cases (almost-PHI, PHI-like patterns)
- Test performance with large log volumes
- Verify that non-PHI is preserved (critical for logs to remain useful)

### 2. Validation Strategy

For each sanitization strategy, verify:

1. All PHI is properly redacted
2. Non-PHI is preserved when appropriate
3. The system fails safely (over-redaction is better than under-redaction)
4. Performance is acceptable for production use

## Troubleshooting Common Issues

### 1. Over-Sanitization

If too much data is being redacted:

- Review pattern definitions for over-broad patterns
- Ensure key detection isn't overly aggressive
- Set `allow_logging_non_phi = True` in configuration

### 2. Under-Sanitization

If PHI is leaking through:

- Add missing patterns to phi_patterns.yaml
- Increase context detection sensitivity
- Consider using more conservative redaction settings

### 3. Performance Issues

If sanitization is causing performance problems:

- Optimize regex patterns
- Consider increasing `max_pattern_cache_size`
- Profile the code to identify bottlenecks

## Compliance Documentation

Maintain documentation of:

1. All PHI patterns being detected
2. Sanitization strategies used
3. Regular testing and validation
4. Any changes to the sanitization approach

This documentation supports HIPAA compliance audits and demonstrates due diligence in protecting PHI.

## References

1. [HHS HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
2. [NIST Guide to Computer Security Log Management](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-92.pdf)
3. [OCR Guidance on HIPAA & Cloud Computing](https://www.hhs.gov/hipaa/for-professionals/special-topics/cloud-computing/index.html)
4. [HITRUST CSF](https://hitrustalliance.net/csf/) - Comprehensive security framework for healthcare