# Testing Guide: Novamind Digital Twin Platform

This comprehensive testing guide outlines standards, procedures, and best practices for testing the Novamind Digital Twin Platform. As a HIPAA-compliant platform handling sensitive psychiatric data, our testing strategy must be exceptionally rigorous and thorough.

## Testing Philosophy

The Novamind testing philosophy follows these core principles:

1. **Proactive Quality Assurance**: Test-driven development (TDD) for core components, ensuring requirements are captured as tests before implementation.
2. **Comprehensive Coverage**: Aim for 80%+ code coverage across all modules.
3. **Security-First Testing**: Every test should consider security and privacy implications.
4. **Behavioral Verification**: Tests should verify behavior, not implementation details.
5. **Isolation**: Tests should be independent and hermetic.

## Test Categories

Our testing strategy includes multiple layers of testing:

### 1. Unit Tests

Unit tests verify individual components in isolation, ensuring each function, method, or class performs as expected.

**Location**: `app/tests/unit/` (or domain-specific directories like `app/tests/domain/`, `app/tests/core/`, etc.)

**Coverage Goal**: 90%+ coverage for all core business logic and critical modules.

**Best Practices**:
- Tests should be fast and independent
- Use mocks for external dependencies
- Each test should have a clear purpose and verify a single behavior
- Naming convention: `test_<function_name>_<scenario>_<expected_outcome>`

**Example**:
```python
def test_detect_depression_with_valid_input_returns_expected_structure():
    # Arrange
    service = MockMentaLLaMA()
    text = "I've been feeling sad for weeks."
    
    # Act
    result = service.detect_depression(text)
    
    # Assert
    assert isinstance(result, dict)
    assert "score" in result
    assert isinstance(result["score"], float)
    assert 0.0 <= result["score"] <= 1.0
```

### 2. Integration Tests

Integration tests verify that components work together correctly, focusing on the interactions between modules.

**Location**: `app/tests/integration/`

**Coverage Goal**: 80%+ coverage for all API endpoints and service integrations.

**Best Practices**:
- Use real dependencies where possible, mocking only external services
- Test realistic workflows that span multiple components
- Include error handling and edge case scenarios
- Naming convention: `test_<workflow/feature>_<scenario>_<expected_outcome>`

**Example**:
```python
@pytest.mark.asyncio
async def test_digital_twin_session_workflow_creates_and_persists_insights():
    # Arrange
    service = DigitalTwinService(repository=MockRepository())
    patient_id = "patient-123"
    
    # Act
    session = await service.create_session(patient_id)
    await service.send_message(session.id, "I didn't sleep well last night")
    await service.send_message(session.id, "My medication is making me drowsy")
    insights = await service.get_insights(session.id)
    
    # Assert
    assert len(insights["sleep"]) > 0
    assert len(insights["medication"]) > 0
```

### 3. Security Tests

Security tests verify that the system protects patient data and prevents unauthorized access.

**Location**: `app/tests/security/`

**Coverage Goal**: 100% coverage for authentication, authorization, and PHI handling.

**Best Practices**:
- Test for common security vulnerabilities (OWASP Top 10)
- Verify proper sanitization of PHI data
- Test authorization at all access points
- Test audit logging for compliance

**Example**:
```python
def test_phi_detection_identifies_and_redacts_sensitive_information():
    # Arrange
    detector = PHIDetector()
    text = "Patient John Smith (DOB: 01/01/1980) reports headaches."
    
    # Act
    result = detector.redact_phi(text)
    
    # Assert
    assert "John Smith" not in result
    assert "01/01/1980" not in result
    assert "reports headaches" in result  # Non-PHI content preserved
```

### 4. Performance Tests

Performance tests ensure the system can handle the expected load and respond within acceptable timeframes.

**Location**: `app/tests/performance/`

**Best Practices**:
- Establish baseline performance metrics
- Test under various load conditions
- Verify response times for critical operations
- Test database query performance

**Example**:
```python
@pytest.mark.slow
def test_ml_model_response_time_under_load():
    # Arrange
    service = MentaLLaMAService()
    texts = ["..." for _ in range(100)]  # 100 typical user inputs
    
    # Act
    start_time = time.time()
    results = [service.process(text) for text in texts]
    end_time = time.time()
    
    # Assert
    avg_time = (end_time - start_time) / len(texts)
    assert avg_time < 0.5  # Average response time under 500ms
```

## Test Execution

### Running Tests

We provide several scripts to run tests with various options:

1. **Run all tests**:
   ```bash
   ./scripts/run_tests.py
   ```

2. **Run specific test categories**:
   ```bash
   ./scripts/run_tests.py --unit
   ./scripts/run_tests.py --integration
   ./scripts/run_tests.py --security
   ./scripts/run_tests.py --ml-mock
   ```

3. **Run with coverage reporting**:
   ```bash
   ./scripts/run_tests.py --coverage
   # or
   ./scripts/generate_test_coverage.py
   ```

4. **Quick tests for development feedback**:
   ```bash
   ./scripts/run_tests.py --quick
   ```

### Coverage Reports

Coverage reports are generated in multiple formats:

- **HTML**: `coverage_html/` - Detailed report with line-by-line coverage visualization
- **XML**: `coverage.xml` - For integration with CI/CD systems
- **JSON**: `coverage.json` - For automated processing

The minimum acceptable coverage threshold is 80% for the overall codebase, with higher thresholds for critical components:

- Core domain models: 90%+
- Security components: 95%+
- PHI handling: 100%

## CI/CD Integration

Tests are integrated into our CI/CD pipeline:

1. **Pre-commit checks**: Run linting and quick tests
2. **Pull request builds**: Run all tests with coverage reports
3. **Main branch builds**: Run extended tests including security and performance tests
4. **Release builds**: Full test suite with additional compliance verification

## Testing Tools

The Novamind testing infrastructure uses:

- **pytest**: Core testing framework
- **pytest-cov**: Code coverage reporting
- **pytest-asyncio**: For testing asynchronous code
- **pytest-mock**: For mocking dependencies
- **hypothesis**: For property-based testing
- **locust**: For load testing

## HIPAA Compliance in Testing

Special considerations for HIPAA compliance:

1. **Never use real PHI**: Always use synthetic data in tests
2. **Data isolation**: Test databases must be isolated and secured
3. **Sanitized logs**: Ensure test logs don't contain sensitive information
4. **Comprehensive audit testing**: Verify all PHI access is properly logged
5. **Authorization testing**: Verify role-based access controls

## Writing New Tests

When adding new features, follow this process:

1. Write tests that define the expected behavior
2. Implement the feature to make tests pass
3. Refactor while keeping tests green
4. Ensure test coverage meets or exceeds thresholds
5. Include edge cases and error scenarios

**Test file structure**:
```python
"""
Test module for [feature].

This module contains tests for [feature], verifying [primary behaviors].
"""
import pytest
from datetime import datetime, UTC
from app.core.services.feature import FeatureService

# Fixtures
@pytest.fixture
def service():
    """Return a configured instance of FeatureService for testing."""
    return FeatureService()

# Test cases
class TestFeatureService:
    """Tests for the FeatureService."""
    
    def test_feature_happy_path(self, service):
        """Test the primary/happy path for the feature."""
        # Arrange
        # Act
        # Assert
    
    def test_feature_edge_case(self, service):
        """Test edge case behavior."""
        # Arrange
        # Act
        # Assert
    
    def test_feature_error_handling(self, service):
        """Test error handling behavior."""
        # Arrange
        # Act
        # Assert
```

## Debugging Failed Tests

When tests fail:

1. Read the failure message carefully
2. Check the line where the assertion failed
3. Use the `--verbose` flag for more details
4. Consider adding debug logs or stepping through with a debugger
5. Check for environment-specific issues

## Contact

For questions about testing standards or help debugging test failures, contact the platform engineering team.

---

*This testing guide is part of the Novamind Digital Twin Platform documentation suite.*