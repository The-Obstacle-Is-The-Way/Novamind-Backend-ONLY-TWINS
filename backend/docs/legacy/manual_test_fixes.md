# Manual Test Syntax Repair Guide

Based on our automated analysis, we've identified 33 test files with syntax errors that require manual intervention. This guide provides specific fixes for the common error patterns.

## Common Error Patterns and Fixes

### 1. List Comprehensions with Line Breaks

**Error Pattern:**
```python
items = [
    Item(id=i, name=f"Item {i}")
    for i in range(5):  # SyntaxError: invalid syntax
]
```

**Fix:**
Keep the closing bracket on the same line as the last part of the comprehension:
```python
items = [
    Item(id=i, name=f"Item {i}")
    for i in range(5)
]
```

### 2. Missing Colons After Function/Method Declarations

**Error Pattern:**
```python
@pytest.fixture
def password_handler()  # SyntaxError: invalid syntax
    """Create a password handler instance for testing."""
    return PasswordHandler()
```

**Fix:**
```python
@pytest.fixture
def password_handler():
    """Create a password handler instance for testing."""
    return PasswordHandler()
```

### 3. Multi-line With Statement Continuations

**Error Pattern:**
```python
with patch.object(  # SyntaxError: invalid syntax
    repo, 'get_events_by_correlation_id', 
    return_value=[mock_event_model]
):
```

**Fix:**
```python
with patch.object(
    repo, 'get_events_by_correlation_id', 
    return_value=[mock_event_model]
):
```

### 4. Tuple/List Item Continuation Issues

**Error Pattern:**
```python
for phi_type, sample in [
    ("NAME", sample_phi_data["name"]),
    ("SSN", sample_phi_data["ssn"]),
    ("ADDRESS", sample_phi_data["address"]),  # SyntaxError: invalid syntax
]:
    # test code
```

**Fix:**
```python
for phi_type, sample in [
    ("NAME", sample_phi_data["name"]),
    ("SSN", sample_phi_data["ssn"]),
    ("ADDRESS", sample_phi_data["address"])
]:
    # test code
```

### 5. Parenthesis Matching Issues in Decorator Lines

**Error Pattern:**
```python
@pytest.mark.db_required:  # SyntaxError: invalid syntax
    class NeurotransmitterType(str, Enum):
```

**Fix:**
```python
@pytest.mark.db_required
class NeurotransmitterType(str, Enum):
```

## Specific Files with Examples

### 1. `app/tests/standalone/test_standalone_phi_sanitizer.py`

**Error (Line 29):**
```python
def __init__(:  # Missing self parameter
    self,
    name: str,
    regex: str = None,
```

**Fix:**
```python
def __init__(
    self,
    name: str,
    regex: str = None,
```

### 2. `app/tests/unit/infrastructure/security/test_password_handler.py`

**Error (Line 16):**
```python
@pytest.fixture:  # Colon after decorator
    def password_handler():
```

**Fix:**
```python
@pytest.fixture
def password_handler():
```

### 3. `app/tests/unit/core/services/ml/test_factory.py`

**Error (Line 67-69):**
```python
with patch()
    "app.core.services.ml.phi_detection.AWSComprehendMedicalPHIDetection.initialize":
) as mock_initialize:
```

**Fix:**
```python
with patch(
    "app.core.services.ml.phi_detection.AWSComprehendMedicalPHIDetection.initialize"
) as mock_initialize:
```

### 4. `app/tests/unit/core/services/ml/test_mock.py`

**Error (Line 107-108):**
```python
for model_type in ["depression_detection", "risk_assessment", "sentiment_analysis", :
                  "wellness_dimensions", "digital_twin"]:
```

**Fix:**
```python
for model_type in ["depression_detection", "risk_assessment", "sentiment_analysis", 
                  "wellness_dimensions", "digital_twin"]:
```

## Step-by-Step Fix Process

1. Start with standalone tests (highest priority)
2. For each file with an error:
   - Review the error location and context in the log
   - Identify which error pattern it matches
   - Apply the appropriate fix from this guide
   - Run `python -m py_compile <file_path>` to verify syntax
   - Use pytest to run just that file once fixed: `pytest <file_path> -v`

3. Track your progress using:
```bash
find backend/app/tests -name "*.py" -exec python -m py_compile {} \; 2>&1 | grep "SyntaxError" | wc -l
```

## Notes

- For more complex syntax errors, you may need to carefully reconstruct the full statement
- Watch for indentation issues when fixing code
- Consider adding comments when the original intent is unclear
- If a test is particularly problematic, mark it with `@pytest.mark.skip` temporarily