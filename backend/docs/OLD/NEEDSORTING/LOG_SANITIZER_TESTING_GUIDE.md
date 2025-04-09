# Log Sanitizer Testing Guide

## Overview

This guide provides instructions for testing the HIPAA-compliant log sanitization system. The log sanitizer is a critical security component that ensures Protected Health Information (PHI) is properly redacted from all system logs, a fundamental requirement for HIPAA compliance.

## Test Coverage

The log sanitizer has two comprehensive test suites:

1. **Basic Test Suite** (`tests/unit/infrastructure/security/test_log_sanitizer.py`): Tests core functionality including pattern detection, redaction modes, and handling of different data structures.

2. **Enhanced Test Suite** (`tests/unit/infrastructure/security/test_enhanced_log_sanitizer.py`): Provides more granular testing of individual components, including PHI patterns, redaction strategies, and logging integration.

Together, these test suites provide thorough coverage of the log sanitization system, ensuring that PHI is properly detected and redacted in all scenarios.

## Running the Tests

### Using the Test Runner

The simplest way to run the log sanitizer tests is to use the provided test runner script:

```bash
python test_log_sanitizer_runner.py
```

This script will run both test suites and provide a summary of the results, including any failing tests.

### Running Tests Manually

You can also run the tests manually using pytest:

```bash
# Run both test suites
python -m pytest tests/unit/infrastructure/security/test_log_sanitizer.py tests/unit/infrastructure/security/test_enhanced_log_sanitizer.py -v

# Run with coverage reporting
python -m pytest tests/unit/infrastructure/security/test_log_sanitizer.py tests/unit/infrastructure/security/test_enhanced_log_sanitizer.py -v --cov=app.infrastructure.security.log_sanitizer --cov-report=term
```

## Test Configuration

The tests use a custom pytest configuration file (`pytest_log_sanitizer.ini`) to avoid conflicts with the project's main pytest configuration. This configuration file is used automatically by the test runner script.

If you're running the tests manually, you can specify the configuration file using the `-c` option:

```bash
python -m pytest tests/unit/infrastructure/security/test_log_sanitizer.py -v -c pytest_log_sanitizer.ini
```

## Test Categories

The test suites cover the following categories:

### PHI Pattern Detection

- Regex pattern matching
- Exact pattern matching
- Fuzzy pattern matching
- Context-based pattern matching
- Pattern repository management

### Redaction Strategies

- Full redaction (replacing entire values)
- Partial redaction (preserving portions of values)
- Hash-based redaction (consistent anonymization)
- Strategy factory pattern

### Data Structure Handling

- Simple string sanitization
- JSON string sanitization
- Dictionary sanitization
- List sanitization
- Nested object sanitization
- Structured log sanitization

### Configuration and Customization

- Default configuration
- Custom configuration
- Sanitization hooks
- Disabled sanitization
- Maximum log size handling

### Logging Integration

- PHI formatter
- PHI redaction handler
- Sanitized logger
- Log record sanitization
- Sanitize logs decorator

## HIPAA Compliance Requirements

For HIPAA compliance, the log sanitizer must meet the following requirements:

1. **Complete PHI Detection**: All PHI must be detected, including direct identifiers (names, SSNs, etc.) and quasi-identifiers that could be used for re-identification.

2. **Proper Redaction**: Detected PHI must be properly redacted according to the configured redaction mode.

3. **Structure Preservation**: The structure of log messages must be preserved to maintain readability and usefulness.

4. **Performance**: The sanitization process must be efficient to avoid impacting system performance.

5. **Robustness**: The sanitizer must handle edge cases gracefully, including malformed input and unexpected data structures.

The test suites verify that the log sanitizer meets all these requirements.

## Extending the Tests

When adding new features to the log sanitizer, you should also add corresponding tests. Follow these guidelines:

1. **Test Each Component**: Add tests for each new component or feature.

2. **Test Edge Cases**: Include tests for edge cases and error conditions.

3. **Mock External Dependencies**: Use mocks for external dependencies to ensure tests are isolated and deterministic.

4. **Verify PHI Redaction**: Always verify that PHI is properly redacted in all test cases.

5. **Maintain Coverage**: Aim for 100% code coverage of the log sanitizer module.

## Troubleshooting

If tests are failing, check the following:

1. **PHI Pattern Configuration**: Ensure the PHI patterns are correctly configured in `phi_patterns.yaml`.

2. **Redaction Strategy**: Verify that the redaction strategy is working as expected.

3. **Data Structure Handling**: Check that the sanitizer correctly handles the data structure being tested.

4. **Mocking**: Ensure that external dependencies are properly mocked.

5. **Test Environment**: Verify that the test environment is correctly set up, including the pytest configuration.

## Conclusion

Thorough testing of the log sanitizer is essential for ensuring HIPAA compliance. By maintaining comprehensive test coverage, we can be confident that our system properly protects patient privacy by preventing PHI from appearing in logs.