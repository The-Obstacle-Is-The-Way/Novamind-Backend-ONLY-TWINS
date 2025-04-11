# Test Suite Implementation Roadmap

## Overview

This document provides a detailed, actionable implementation roadmap for transforming the current Novamind Digital Twin test suite into a production-ready test infrastructure. It builds on the analysis in `04_TEST_SUITE_CURRENT_STATE_ANALYSIS.md` and outlines specific steps, code examples, and a timeline for implementation.

## Implementation Timeline

| Phase | Focus Area | Timeframe | Key Deliverables |
|-------|------------|-----------|------------------|
| 1 | Scripts Cleanup & Foundation | Weeks 1-2 | Reorganized scripts directory, Canonical test runners |
| 2 | Test Migration & Quality | Weeks 3-4 | Migrated tests, Improved test isolation |
| 3 | Coverage & CI/CD | Weeks 5-6 | Coverage improvements, CI/CD integration |

## Phase 1: Scripts Cleanup & Foundation (Weeks 1-2)

### Task 1.1: Script Directory Restructuring (2 days)

```bash
# Create the new directory structure
mkdir -p backend/scripts/test/runners/legacy
mkdir -p backend/scripts/test/tools/legacy
mkdir -p backend/scripts/test/fixtures
mkdir -p backend/scripts/test/ci
mkdir -p backend/scripts/db
mkdir -p backend/scripts/deployment
mkdir -p backend/scripts/utils

# Analyze existing scripts and categorize them
python -c "
import os
import shutil
from pathlib import Path

script_dir = Path('backend/scripts')
scripts = list(script_dir.glob('*.py')) + list(script_dir.glob('*.sh'))

# Analyze and categorize
for script in scripts:
    content = script.read_text()
    
    # Determine category based on name and content
    if 'test' in script.name.lower() and 'run' in script.name.lower():
        target_dir = script_dir / 'test' / 'runners' / 'legacy'
    elif 'test' in script.name.lower() and any(x in script.name.lower() for x in ['analyze', 'classify', 'categorize']):
        target_dir = script_dir / 'test' / 'tools' / 'legacy'
    elif 'ci' in script.name.lower() or 'pipeline' in script.name.lower():
        target_dir = script_dir / 'test' / 'ci'
    elif 'db' in script.name.lower() or 'database' in script.name.lower():
        target_dir = script_dir / 'db'
    elif 'deploy' in script.name.lower():
        target_dir = script_dir / 'deployment'
    else:
        target_dir = script_dir / 'utils'
    
    # Ensure target directory exists
    target_dir.mkdir(exist_ok=True, parents=True)
    
    # Report categorization (but don't move yet)
    print(f'Would categorize {script} → {target_dir / script.name}')
"
```

### Task 1.2: Implement Canonical Test Runner (3 days)

Create the canonical test runner based on the implementation in `06_TEST_SCRIPTS_IMPLEMENTATION.md`:

```python
#!/usr/bin/env python3
"""
Novamind Digital Twin Canonical Test Runner

This script is the canonical test runner for the Novamind Digital Twin platform.
It implements the directory-based SSOT approach where tests are organized by
dependency level:
  - standalone/ - No external dependencies (fastest)
  - venv/ - Python package dependencies (medium)
  - integration/ - External services required (slowest)

Usage:
    python scripts/test/runners/run_tests.py --standalone  # Run standalone tests
    python scripts/test/runners/run_tests.py --venv        # Run venv tests
    python scripts/test/runners/run_tests.py --integration # Run integration tests
    python scripts/test/runners/run_tests.py --all         # Run all tests
    python scripts/test/runners/run_tests.py --coverage    # Generate coverage
"""

import os
import sys
import time
import argparse
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set

# ANSI color codes for terminal output
class Color:
    """ANSI color codes for terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def disable_if_windows():
        """Disable colors on Windows if not supported."""
        if platform.system() == "Windows":
            Color.BLUE = ''
            Color.GREEN = ''
            Color.YELLOW = ''
            Color.RED = ''
            Color.ENDC = ''
            Color.BOLD = ''


def print_header(message: str) -> None:
    """
    Print a formatted header message.
    
    Args:
        message: The message to print as a header
    """
    print(f"\n{Color.BOLD}{Color.BLUE}{'=' * 80}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.BLUE}{message.center(80)}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.BLUE}{'=' * 80}{Color.ENDC}\n")


def print_section(message: str) -> None:
    """
    Print a formatted section header.
    
    Args:
        message: The message to print as a section header
    """
    print(f"\n{Color.BOLD}{Color.YELLOW}{message}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.YELLOW}{'-' * len(message)}{Color.ENDC}\n")


def run_command(cmd: List[str], env: Optional[Dict[str, str]] = None) -> Tuple[bool, str, float]:
    """
    Run a command and return success status, output, and execution time.
    
    Args:
        cmd: The command to run as a list of strings
        env: Optional environment variables to set
        
    Returns:
        Tuple of (success, output, execution_time)
    """
    print(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        # Use provided environment or current environment
        env_vars = env or os.environ.copy()
        
        # Run the command
        result = subprocess.run(
            cmd,
            env=env_vars,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Check if the command succeeded
        success = result.returncode == 0
        output = result.stdout
    except Exception as e:
        success = False
        output = str(e)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    return success, output, execution_time

# ... continue with implementation from 06_TEST_SCRIPTS_IMPLEMENTATION.md ...
```

### Task 1.3: Implement Security Test Runner (2 days)

Create a specialized security test runner based on the implementation plan:

```python
#!/usr/bin/env python3
"""
Novamind Digital Twin Security Test Runner

This script focuses specifically on security-related tests across all dependency
levels. It provides specialized functionality for HIPAA compliance testing, PHI
handling verification, and security vulnerability scanning.

Usage:
    python scripts/test/runners/run_security.py  # Run all security tests
    python scripts/test/runners/run_security.py --hipaa  # HIPAA compliance only
    python scripts/test/runners/run_security.py --phi    # PHI handling only
    python scripts/test/runners/run_security.py --auth   # Authentication only
"""

import sys
import os
from pathlib import Path

# Import common functionality from the main test runner
sys.path.append(str(Path(__file__).parent))
from run_tests import (
    run_command, print_header, print_section, Color, 
    ensure_test_directories, parse_pytest_output, extract_pytest_summary
)


def run_security_tests(hipaa: bool = False, phi: bool = False, auth: bool = False, 
                     junit: bool = False, coverage: bool = False) -> int:
    """
    Run security tests across all dependency levels.
    
    Args:
        hipaa: Whether to run only HIPAA compliance tests
        phi: Whether to run only PHI handling tests
        auth: Whether to run only authentication/authorization tests
        junit: Whether to generate JUnit XML reports
        coverage: Whether to generate coverage reports
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    print_header("Novamind Digital Twin Security Test Runner")
    
    # Determine which markers to use
    markers = []
    if hipaa:
        markers.append("hipaa")
    if phi:
        markers.append("phi")
    if auth:
        markers.append("auth")
    
    # If no specific markers, run all security tests
    if not markers:
        markers = ["security"]
    
    # Combine markers with OR operator
    marker_expr = " or ".join(markers)
    
    # Run tests across all dependency levels
    stages = ["standalone", "venv", "integration"]
    all_passed = True
    
    for stage in stages:
        # Build the command
        cmd = [
            "python", "-m", "pytest", 
            f"backend/app/tests/{stage}/", 
            f"-m='{marker_expr}'",
            "-v"
        ]
        
        # Add coverage if requested
        if coverage:
            cmd.extend([
                "--cov=backend/app",
                f"--cov-report=html:backend/coverage_html/security_{stage}",
                "--cov-report=term"
            ])
        
        # Add JUnit if requested
        if junit:
            results_dir = Path("backend/test-results")
            results_dir.mkdir(exist_ok=True)
            cmd.append(f"--junitxml=backend/test-results/security_{stage}.xml")
        
        # Run the tests
        print_section(f"Running Security Tests in {stage.capitalize()} Tests")
        
        # Set environment variables for integration tests
        env = os.environ.copy()
        if stage == "integration":
            env.update({
                "TESTING": "True",
                "DATABASE_URL": os.environ.get("DATABASE_URL", 
                                "postgresql://postgres:postgres@localhost:5432/novamind_test")
            })
        
        success, output, execution_time = run_command(cmd, env)
        
        # Print results
        print(f"\n{stage.capitalize()} Security Tests: "
              f"{'PASSED' if success else 'FAILED'} in {execution_time:.2f}s")
        
        # Print summary
        summary_lines = extract_pytest_summary(output)
        for line in summary_lines:
            print(line)
        
        # Keep track of overall success
        all_passed = all_passed and success
    
    # Generate combined security coverage report if requested
    if coverage:
        print_section("Generating Combined Security Coverage Report")
        run_command([
            "python", "-m", "coverage", "combine"
        ])
        run_command([
            "python", "-m", "coverage", "html",
            "-d", "backend/coverage_html/security_combined"
        ])
        _, output, _ = run_command([
            "python", "-m", "coverage", "report", 
            "--include=*/app/security/*,*/app/auth/*"
        ])
        print(output)
    
    return 0 if all_passed else 1


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Novamind Digital Twin Security Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1]
    )
    
    parser.add_argument("--hipaa", action="store_true", help="Run HIPAA compliance tests only")
    parser.add_argument("--phi", action="store_true", help="Run PHI handling tests only")
    parser.add_argument("--auth", action="store_true", help="Run authentication tests only")
    parser.add_argument("--junit", action="store_true", help="Generate JUnit XML reports")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage reports")
    
    args = parser.parse_args()
    
    # Run the tests
    exit_code = run_security_tests(
        hipaa=args.hipaa,
        phi=args.phi,
        auth=args.auth,
        junit=args.junit,
        coverage=args.coverage
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

### Task 1.4: Implement Test Analysis Tool (3 days)

Create a test analysis tool to help categorize and migrate tests:

```python
#!/usr/bin/env python3
"""
Novamind Digital Twin Test Analyzer

This tool analyzes test files to determine their appropriate category based on
dependencies, markers, and imports. It helps in the migration to the directory-based
SSOT approach by providing accurate categorization.

Usage:
    python scripts/test/tools/analyze_tests.py  # Analyze all tests
    python scripts/test/tools/analyze_tests.py --file path/to/test.py  # Analyze specific file
    python scripts/test/tools/analyze_tests.py --report  # Generate HTML report
"""

import os
import re
import sys
import ast
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

# Define standard test categories
TEST_CATEGORIES = ["standalone", "venv", "integration"]

# Define dependency patterns to search for
STANDALONE_SAFE_IMPORTS = {
    'pytest', 'unittest', 're', 'json', 'datetime', 'typing', 
    'enum', 'mock', 'patch', 'MagicMock', 'copy', 'random', 'math',
    'functools', 'itertools', 'app.domain', 'app.core', 'dataclasses',
    'abc', 'collections', 'contextlib', 'hashlib', 'uuid', 'os', 'sys'
}

DB_DEPENDENCY_PATTERNS = [
    r'session', r'database', r'models\.', r'db\.',
    r'repository', r'sqlalchemy', r'transaction',
    r'commit', r'rollback', r'query', r'execute', r'SELECT',
    r'PostgreSQL', r'alembic'
]

EXTERNAL_SERVICE_PATTERNS = [
    r'requests\.', r'http', r'boto3', r'aws', r's3', 
    r'sqs', r'sns', r'redis', r'kafka', r'smtp', 
    r'email\.', r'sms', r'twilio', r'openai', r'api\.'
]

# Define markers that indicate test categories
MARKER_PATTERNS = {
    "standalone": [r'@pytest\.mark\.standalone'],
    "integration": [r'@pytest\.mark\.integration', r'@pytest\.mark\.db', r'@pytest\.mark\.database'],
    "security": [r'@pytest\.mark\.security', r'@pytest\.mark\.hipaa', r'@pytest\.mark\.phi']
}

# ... continue with implementation ...
```

### Task 1.5: Script Migration Execution (2 days)

Execute the script migration plan:

```bash
# 1. Move scripts to their new locations
find backend/scripts -name "*.py" -o -name "*.sh" -maxdepth 1 | while read script; do
  if [[ $script == *run_test* || $script == *test_runner* ]]; then
    mkdir -p backend/scripts/test/runners/legacy
    cp "$script" backend/scripts/test/runners/legacy/
    echo "Moved $script to test/runners/legacy/"
  elif [[ $script == *classify* || $script == *analyze* || $script == *categorize* || $script == *migrate* ]]; then
    mkdir -p backend/scripts/test/tools/legacy
    cp "$script" backend/scripts/test/tools/legacy/
    echo "Moved $script to test/tools/legacy/"
  # ... other categories ...
  fi
done

# 2. Create canonical scripts
mkdir -p backend/scripts/test/runners
mkdir -p backend/scripts/test/tools

# Create run_tests.py (from implementation in Task 1.2)
# Create run_security.py (from implementation in Task 1.3)
# Create analyze_tests.py (from implementation in Task 1.4)
```

## Phase 2: Test Migration & Quality (Weeks 3-4)

### Task 2.1: Test Categorization (2 days)

Use the analysis tool to categorize all existing tests:

```bash
# Run the test analyzer
python backend/scripts/test/tools/analyze_tests.py --report

# Review the report
cat backend/test-analysis-report.md
```

Example categorization criteria:

```python
def categorize_test(file_path: Path) -> str:
    """Determine the appropriate category for a test file."""
    
    # Extract imports and dependencies
    content = file_path.read_text()
    
    # Check for explicit markers
    for category, patterns in MARKER_PATTERNS.items():
        if any(re.search(pattern, content) for pattern in patterns):
            return category
    
    # Check for database dependencies
    if any(re.search(pattern, content, re.IGNORECASE) for pattern in DB_DEPENDENCY_PATTERNS):
        return "integration"
    
    # Check for external service dependencies
    if any(re.search(pattern, content, re.IGNORECASE) for pattern in EXTERNAL_SERVICE_PATTERNS):
        return "integration"
    
    # Extract imports
    try:
        tree = ast.parse(content)
        imports = extract_imports(tree)
        
        # Check if imports are within standalone safe list
        if imports.issubset(STANDALONE_SAFE_IMPORTS):
            return "standalone"
        else:
            return "venv"
    except SyntaxError:
        # If we can't parse the file, assume venv dependencies
        return "venv"
```

### Task 2.2: Test Migration (3 days)

Implement and execute the test migration:

```bash
# Run the test migration tool
python backend/scripts/test/tools/migrate_tests.py --execute

# Verify the tests after migration
python backend/scripts/test/runners/run_tests.py --all
```

Migration script logic:

```python
def migrate_test(source_path: Path, category: str) -> bool:
    """
    Migrate a test file to its appropriate category directory.
    
    Args:
        source_path: Path to the source test file
        category: Target category (standalone, venv, integration)
    
    Returns:
        bool: True if migration succeeded, False otherwise
    """
    if not source_path.exists():
        print(f"Error: Source file {source_path} does not exist")
        return False
    
    # Determine target directory based on category and original path
    tests_dir = Path("backend/app/tests")
    
    # Preserve the subdirectory structure within the category
    try:
        rel_path = source_path.relative_to(tests_dir)
        # Skip if already in the correct category
        if rel_path.parts and rel_path.parts[0] == category:
            print(f"Skipping {source_path} - already in {category}")
            return True
        
        # Determine new relative path
        if len(rel_path.parts) > 1:
            # Keep subdirectory structure but replace top-level dir
            new_parts = [category] + list(rel_path.parts[1:])
            target_path = tests_dir.joinpath(*new_parts)
        else:
            # No subdirectory, just move to category root
            target_path = tests_dir / category / source_path.name
    except ValueError:
        # Fallback if we can't determine relative path
        target_path = tests_dir / category / source_path.name
    
    # Create target directory if it doesn't exist
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Update imports and markers if needed
    content = source_path.read_text()
    
    # Copy file to target location
    target_path.write_text(content)
    print(f"Migrated {source_path} to {target_path}")
    
    return True
```

### Task 2.3: Test Isolation Improvements (4 days)

Identify and fix tests with isolation issues:

```bash
# Run a test to identify isolation issues
python -m pytest backend/app/tests --random-order
```

Example test isolation fix:

```python
# Before: Test with isolation issues
@pytest.fixture
def test_user():
    user = create_user("test@example.com")
    return user

def test_user_profile(test_user):
    profile = get_user_profile(test_user.id)
    assert profile is not None

# After: Fixed test with proper isolation
@pytest.fixture
def test_user():
    user = create_user(f"test-{uuid.uuid4()}@example.com")
    yield user
    # Clean up
    delete_user(user.id)

def test_user_profile(test_user):
    profile = get_user_profile(test_user.id)
    assert profile is not None
```

### Task 2.4: Test Quality Improvements (5 days)

Implement standardized test patterns and fix quality issues:

Example fixture improvement:

```python
# Before: Complex, confusing fixtures
@pytest.fixture
def app_client():
    app = create_app()
    client = app.test_client()
    return client

@pytest.fixture
def auth_client(app_client):
    response = app_client.post("/login", json={"username": "admin", "password": "password"})
    token = response.json["token"]
    app_client.token = token
    return app_client

# After: Clear, well-documented fixtures
@pytest.fixture
def app_client():
    """Create a FastAPI TestClient instance with a configured test application."""
    app = create_app({"TESTING": True, "DATABASE_URL": "sqlite:///:memory:"})
    client = TestClient(app)
    yield client

@pytest.fixture
def auth_client(app_client):
    """
    Create an authenticated TestClient with admin privileges.
    
    This fixture:
    1. Creates a test user with admin role
    2. Authenticates the client
    3. Returns the authenticated client with the token attached
    """
    # Create test admin user
    test_user = create_test_user(role="admin")
    
    # Authenticate
    response = app_client.post(
        "/auth/login", 
        json={"username": test_user.username, "password": "password123"}
    )
    assert response.status_code == 200, f"Authentication failed: {response.json()}"
    
    # Extract token
    token = response.json()["access_token"]
    
    # Configure client with token
    app_client.headers = {"Authorization": f"Bearer {token}"}
    
    # Attach user to client for convenience
    app_client.test_user = test_user
    
    return app_client
```

## Phase 3: Coverage & CI/CD (Weeks 5-6)

### Task 3.1: Coverage Gap Analysis (2 days)

Run a comprehensive coverage analysis to identify gaps:

```bash
# Run coverage on all tests
python backend/scripts/test/runners/run_tests.py --all --coverage

# Generate report
coverage report
coverage html -d backend/coverage_html/full
```

Example coverage gap analysis:

```python
def analyze_coverage_gaps(coverage_data):
    """Analyze coverage data to identify key gaps."""
    
    # Extract data by module category
    coverage_by_category = {
        "domain": {},
        "application": {},
        "infrastructure": {},
        "api": {},
        "core": {},
    }
    
    # Categorize modules
    for module_path, stats in coverage_data.items():
        if "domain" in module_path:
            category = "domain"
        elif "application" in module_path:
            category = "application"
        elif "infrastructure" in module_path:
            category = "infrastructure"
        elif "api" in module_path:
            category = "api"
        elif "core" in module_path:
            category = "core"
        else:
            continue
        
        coverage_by_category[category][module_path] = stats
    
    # Calculate coverage by category
    results = {}
    for category, modules in coverage_by_category.items():
        if not modules:
            continue
            
        total_lines = sum(stats["lines"] for stats in modules.values())
        covered_lines = sum(stats["covered_lines"] for stats in modules.values())
        missed_lines = sum(stats["missed_lines"] for stats in modules.values())
        
        coverage_pct = covered_lines / total_lines * 100 if total_lines > 0 else 0
        
        # Find modules with lowest coverage
        sorted_modules = sorted(
            modules.items(), 
            key=lambda x: x[1]["covered_lines"] / x[1]["lines"] if x[1]["lines"] > 0 else 0
        )
        worst_modules = sorted_modules[:5]
        
        results[category] = {
            "coverage_pct": coverage_pct,
            "total_lines": total_lines,
            "covered_lines": covered_lines,
            "missed_lines": missed_lines,
            "worst_modules": worst_modules
        }
    
    return results
```

### Task 3.2: Coverage Improvements (5 days)

Add tests for identified coverage gaps:

Example infrastructure test improvement:

```python
# Before: No error handling test
def test_database_connection():
    db = Database()
    assert db.is_connected()

# After: Added error handling test
def test_database_connection_error_handling():
    # Test with invalid connection parameters
    with pytest.raises(DatabaseConnectionError) as exc_info:
        db = Database(host="invalid-host")
        db.connect()
    
    assert "Could not connect to database" in str(exc_info.value)
    
    # Test with network timeout
    with patch("app.infrastructure.db.socket.connect") as mock_connect:
        mock_connect.side_effect = TimeoutError("Connection timed out")
        
        with pytest.raises(DatabaseConnectionError) as exc_info:
            db = Database()
            db.connect()
        
        assert "Connection timed out" in str(exc_info.value)
```

### Task 3.3: CI/CD Integration (3 days)

Update CI/CD pipeline to use the new test structure:

Example GitHub Actions workflow:

```yaml
name: Novamind Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  standalone-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements-test.txt
      - name: Run standalone tests
        run: |
          cd backend
          python scripts/test/runners/run_tests.py --standalone --junit
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: standalone-test-results
          path: backend/test-results/standalone-results.xml
  
  venv-tests:
    runs-on: ubuntu-latest
    needs: standalone-tests
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt
          pip install -r backend/requirements-test.txt
      - name: Run venv tests
        run: |
          cd backend
          python scripts/test/runners/run_tests.py --venv --junit
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: venv-test-results
          path: backend/test-results/venv-results.xml
  
  integration-tests:
    runs-on: ubuntu-latest
    needs: venv-tests
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: novamind_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt
          pip install -r backend/requirements-test.txt
      - name: Run integration tests
        run: |
          cd backend
          python scripts/test/runners/run_tests.py --integration --junit
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/novamind_test
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: integration-test-results
          path: backend/test-results/integration-results.xml
  
  security-tests:
    runs-on: ubuntu-latest
    needs: standalone-tests
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: novamind_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt
          pip install -r backend/requirements-security.txt
          pip install -r backend/requirements-test.txt
      - name: Run security tests
        run: |
          cd backend
          python scripts/test/runners/run_security.py --junit
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/novamind_test
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: security-test-results
          path: backend/test-results/security-*.xml
```

### Task 3.4: Documentation Update (2 days)

Create comprehensive documentation for the new test infrastructure:

```markdown
# Novamind Test Suite Documentation

## Overview

The Novamind Digital Twin test suite follows a directory-based Single Source of Truth (SSOT) approach, where tests are organized by their dependency requirements rather than by test type or architectural layer.

## Test Categories

Tests are organized into three primary categories:

1. **Standalone Tests** (`backend/app/tests/standalone/`)
   - No external dependencies beyond Python standard library
   - Fast execution (milliseconds)
   - Perfect for core domain logic and utilities

2. **VENV Tests** (`backend/app/tests/venv/`)
   - Require Python package dependencies but no external services
   - Medium execution speed (tens to hundreds of milliseconds)
   - Suitable for framework-dependent components with mocked backends

3. **Integration Tests** (`backend/app/tests/integration/`)
   - Require external services such as databases
   - Slower execution (hundreds of milliseconds to seconds)
   - Test full system behavior with real dependencies

## Running Tests

### Using the Canonical Test Runner

```bash
# Run all tests in dependency order
python backend/scripts/test/runners/run_tests.py --all

# Run only standalone tests
python backend/scripts/test/runners/run_tests.py --standalone

# Run with coverage reporting
python backend/scripts/test/runners/run_tests.py --all --coverage

# Run with JUnit XML reports for CI integration
python backend/scripts/test/runners/run_tests.py --all --junit

# Run with parallel execution
python backend/scripts/test/runners/run_tests.py --all --parallel 4
```

### Running Security Tests

```bash
# Run all security-related tests
python backend/scripts/test/runners/run_security.py

# Run only HIPAA compliance tests
python backend/scripts/test/runners/run_security.py --hipaa

# Run with coverage reporting
python backend/scripts/test/runners/run_security.py --coverage
```

## Writing Tests

### Test File Organization

Within each category directory, tests should be organized by module:

```
backend/app/tests/standalone/
├── domain/              # Domain model tests
├── application/         # Application service tests
├── core/                # Core utility tests
└── common/              # Shared component tests
```

### Test File Naming

All test files should:
- Start with `test_`
- Use snake_case
- Clearly indicate what's being tested

Examples:
```
test_patient_model.py
test_auth_service.py
test_digital_twin_creation.py
```

### Test Function Naming

Test functions should:
- Start with `test_`
- Use descriptive names that indicate scenario and expected outcome

Examples:
```python
def test_create_patient_with_valid_data_succeeds():
    ...

def test_login_with_invalid_credentials_raises_auth_error():
    ...
```

### Test Class Naming

Test classes should:
- Start with `Test`
- Use PascalCase
- Describe the component being tested

Examples:
```python
class TestPatientRepository:
    ...

class TestAuthenticationService:
    ...
```

## Additional Documentation

For more detailed information, see:
- [Test Infrastructure SSOT](02_TEST_INFRASTRUCTURE_SSOT.md)
- [Test Suite Implementation Roadmap](05_TEST_SUITE_IMPLEMENTATION_ROADMAP.md)
- [Test Scripts Implementation](06_TEST_SCRIPTS_IMPLEMENTATION.md)
```

## Canonical Test Patterns

To ensure consistency across the test suite, here are canonical patterns for different types of tests:

### Standalone Test Pattern

```python
"""
Test module for the Patient domain model.

This module contains standalone tests for the Patient domain entity, focusing on
validation, business rules, and behavior without external dependencies.
"""

import pytest
from datetime import date
from uuid import uuid4
from app.domain.models.patient import Patient, PatientValidationError


class TestPatientModel:
    """Tests for the Patient domain model."""
    
    def test_create_patient_with_valid_data_succeeds(self):
        """Test that creating a patient with valid data succeeds."""
        # Arrange
        patient_id = str(uuid4())
        patient_data = {
            "id": patient_id,
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": date(1980, 1, 1),
            "gender": "male",
            "email": "john.doe@example.com"
        }
        
        # Act
        patient = Patient(**patient_data)
        
        # Assert
        assert patient.id == patient_id
        assert patient.first_name == "John"
        assert patient.last_name == "Doe"
        assert patient.date_of_birth == date(1980, 1, 1)
        assert patient.gender == "male"
        assert patient.email == "john.doe@example.com"
    
    def test_create_patient_with_invalid_email_raises_error(self):
        """Test that creating a patient with an invalid email raises a validation error."""
        # Arrange
        patient_data = {
            "id": str(uuid4()),
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": date(1980, 1, 1),
            "gender": "male",
            "email": "invalid-email"  # Invalid email format
        }
        
        # Act & Assert
        with pytest.raises(PatientValidationError) as exc_info:
            Patient(**patient_data)
        
        # Verify error message
        assert "email" in str(exc_info.value).lower()
        assert "invalid" in str(exc_info.value).lower()
    
    def test_patient_full_name_property(self):
        """Test that the full_name property returns the correct value."""
        # Arrange
        patient = Patient(
            id=str(uuid4()),
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 1),
            gender="male",
            email="john.doe@example.com"
        )
        
        # Act
        full_name = patient.full_name
        
        # Assert
        assert full_name == "John Doe"
    
    def test_patient_age_calculation(self):
        """Test that the age property calculates the correct age."""
        # Arrange
        birth_date = date(1980, 1, 1)
        patient = Patient(
            id=str(uuid4()),
            first_name="John",
            last_name="Doe",
            date_of_birth=birth_date,
            gender="male",
            email="john.doe@example.com"
        )
        
        # Act
        # Calculate expected age based on today's date
        today = date.today()
        expected_age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
        
        # Assert
        assert patient.age == expected_age
```

### VENV Test Pattern

```python
"""
Test module for the PatientService application service.

This module contains VENV tests for the PatientService, which requires Python packages
but mocks external dependencies like databases.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import date
from uuid import uuid4

from app.application.services.patient_service import PatientService
from app.domain.models.patient import Patient
from app.domain.repositories.patient_repository import PatientRepository


class TestPatientService:
    """Tests for the PatientService application service."""
    
    @pytest.fixture
    def mock_patient_repository(self):
        """Create a mock patient repository."""
        repository = Mock(spec=PatientRepository)
        return repository
    
    @pytest.fixture
    def patient_service(self, mock_patient_repository):
        """Create a PatientService with mock dependencies."""
        return PatientService(repository=mock_patient_repository)
    
    @pytest.fixture
    def sample_patient(self):
        """Create a sample patient for testing."""
        return Patient(
            id=str(uuid4()),
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 1),
            gender="male",
            email="john.doe@example.com"
        )
    
    def test_create_patient_calls_repository(self, patient_service, mock_patient_repository):
        """Test that creating a patient calls the repository with correct data."""
        # Arrange
        patient_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": date(1980, 1, 1),
            "gender": "male",
            "email": "john.doe@example.com"
        }
        mock_patient_repository.create.return_value = Patient(id=str(uuid4()), **patient_data)
        
        # Act
        result = patient_service.create_patient(**patient_data)
        
        # Assert
        mock_patient_repository.create.assert_called_once()
        called_with_args = mock_patient_repository.create.call_args[0][0]
        assert called_with_args.first_name == patient_data["first_name"]
        assert called_with_args.last_name == patient_data["last_name"]
        assert called_with_args.date_of_birth == patient_data["date_of_birth"]
        assert isinstance(result, Patient)
    
    def test_get_patient_by_id_returns_patient(self, patient_service, mock_patient_repository, sample_patient):
        """Test that get_patient_by_id returns a patient when found."""
        # Arrange
        patient_id = sample_patient.id
        mock_patient_repository.get_by_id.return_value = sample_patient
        
        # Act
        result = patient_service.get_patient_by_id(patient_id)
        
        # Assert
        mock_patient_repository.get_by_id.assert_called_once_with(patient_id)
        assert result == sample_patient
    
    def test_get_patient_by_id_returns_none_when_not_found(self, patient_service, mock_patient_repository):
        """Test that get_patient_by_id returns None when patient is not found."""
        # Arrange
        patient_id = str(uuid4())
        mock_patient_repository.get_by_id.return_value = None
        
        # Act
        result = patient_service.get_patient_by_id(patient_id)
        
        # Assert
        mock_patient_repository.get_by_id.assert_called_once_with(patient_id)
        assert result is None
```

### Integration Test Pattern

```python
"""
Test module for the PatientRepository infrastructure component.

This module contains integration tests for the PatientRepository, which requires
a real database connection.
"""

import pytest
from datetime import date
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from app.domain.models.patient import Patient
from app.infrastructure.repositories.patient_repository import SQLAlchemyPatientRepository
from app.infrastructure.database.models import PatientModel


@pytest.mark.integration
class TestPatientRepository:
    """Integration tests for the PatientRepository."""
    
    @pytest.fixture
    def db_session(self, test_db):
        """Create a database session for testing."""
        session = test_db.session_factory()
        yield session
        session.close()
    
    @pytest.fixture
    def patient_repository(self, db_session):
        """Create a real PatientRepository with a test database session."""
        return SQLAlchemyPatientRepository(session=db_session)
    
    @pytest.fixture
    def sample_patient_data(self):
        """Create sample patient data for testing."""
        return {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": date(1980, 1, 1),
            "gender": "male",
            "email": f"john.doe.{uuid4()}@example.com"  # Ensure unique email
        }
    
    def test_create_and_get_patient(self, patient_repository, sample_patient_data):
        """Test that a patient can be created and retrieved."""
        # Arrange
        patient = Patient(id=str(uuid4()), **sample_patient_data)
        
        # Act
        created_patient = patient_repository.create(patient)
        retrieved_patient = patient_repository.get_by_id(created_patient.id)
        
        # Assert
        assert retrieved_patient is not None
        assert retrieved_patient.id == created_patient.id
        assert retrieved_patient.first_name == sample_patient_data["first_name"]
        assert retrieved_patient.last_name == sample_patient_data["last_name"]
        assert retrieved_patient.date_of_birth == sample_patient_data["date_of_birth"]
        assert retrieved_patient.gender == sample_patient_data["gender"]
        assert retrieved_patient.email == sample_patient_data["email"]
    
    def test_update_patient(self, patient_repository, sample_patient_data):
        """Test that a patient can be updated."""
        # Arrange
        patient = Patient(id=str(uuid4()), **sample_patient_data)
        created_patient = patient_repository.create(patient)
        
        # Act
        created_patient.first_name = "Jane"
        updated_patient = patient_repository.update(created_patient)
        retrieved_patient = patient_repository.get_by_id(created_patient.id)
        
        # Assert
        assert updated_patient.first_name == "Jane"
        assert retrieved_patient.first_name == "Jane"
    
    def test_delete_patient(self, patient_repository, sample_patient_data):
        """Test that a patient can be deleted."""
        # Arrange
        patient = Patient(id=str(uuid4()), **sample_patient_data)
        created_patient = patient_repository.create(patient)
        
        # Act
        patient_repository.delete(created_patient.id)
        retrieved_patient = patient_repository.get_by_id(created_patient.id)
        
        # Assert
        assert retrieved_patient is None
    
    def test_get_patients_with_filters(self, patient_repository, sample_patient_data):
        """Test that patients can be retrieved with filters."""
        # Arrange
        # Create multiple patients
        patient1 = Patient(id=str(uuid4()), **sample_patient_data)
        patient2 = Patient(
            id=str(uuid4()),
            first_name="Jane",
            last_name="Doe",
            date_of_birth=date(1985, 5, 5),
            gender="female",
            email=f"jane.doe.{uuid4()}@example.com"
        )
        patient_repository.create(patient1)
        patient_repository.create(patient2)
        
        # Act
        results = patient_repository.get_patients(
            filters={"last_name": "Doe", "gender": "female"}
        )
        
        # Assert
        assert len(results) == 1
        assert results[0].first_name == "Jane"
        assert results[0].gender == "female"
```

## Conclusion

This implementation roadmap provides a detailed, step-by-step plan for transforming the current Novamind Digital Twin test suite into a production-ready test infrastructure. Following this roadmap will:

1. Reorganize the chaotic scripts directory into a clean, logical structure
2. Implement canonical test runners following the SSOT approach
3. Migrate tests to the proper directory structure
4. Improve test quality and coverage
5. Integrate with CI/CD pipelines

By the end of this implementation, the Novamind Digital Twin will have a robust, maintainable test infrastructure that ensures reliability, performance, and security while enabling rapid development.

The roadmap is designed to be incremental and pragmatic, allowing for continuous improvement while maintaining the ability to run tests throughout the migration process. This approach minimizes disruption while maximizing the benefits of the new test infrastructure.
    
    def test_create_and_get_patient(self, patient_repository, sample_patient_data):
        """Test that a patient can be created and retrieved."""
        # Arrange
        patient = Patient(id=str(uuid4()), **sample_patient_data)
        
        # Act
        created_patient = patient_repository.create(patient)
        retrieved_patient = patient_repository.get_by_id(created_patient.id)
        
        # Assert
        assert retrieved_patient is not None
        assert retrieved_patient.id == created_patient.id
        assert retrieved_patient.first_name == sample_patient_data["first_name"]
        assert retrieved_patient.last_name == sample_patient_data["last_name"]
        assert retrieved_patient.date_of_birth == sample_patient_data["date_of_birth"]
        assert retrieved_patient.gender == sample_patient_data["gender"]
        assert retrieved_patient.email == sample_patient_data["email"]
    
    def test_update_patient(self, patient_repository, sample_patient_data):
        """Test that a patient can be updated."""
        # Arrange
        patient = Patient(id=str(uuid4()), **sample_patient_data)
        created_patient = patient_repository.create(patient)
        
        # Act
        created_patient.first_name = "Jane"
        updated_patient = patient_repository.update(created_patient)
        retrieved_patient = patient_repository.get_by_id(created_patient.id)
        
        # Assert
        assert updated_patient.first_name == "Jane"
        assert retrieved_patient.first_name == "Jane"
    
    def test_delete_patient(self, patient_repository, sample_patient_data):
        """Test that a patient can be deleted."""
        # Arrange
        patient = Patient(id=str(uuid4()), **sample_patient_data)
        created_patient = patient_repository.create(patient)
        
        # Act
        patient_repository.delete(created_patient.id)
        retrieved_patient = patient_repository.get_by_id(created_patient.id)
        
        # Assert
        assert retrieved_patient is None
    
    def test_get_patients_with_filters(self, patient_repository, sample_patient_data):
        """Test that patients can be retrieved with filters."""
        # Arrange
        # Create multiple patients
        patient1 = Patient(id=str(uuid4()), **sample_patient_data)
        patient2 = Patient(
            id=str(uuid4()),
            first_name="Jane",
            last_name="Doe",
            date_of_birth=date(1985, 5, 5),
            gender="female",
            email=f"jane.doe.{uuid4()}@example.com"
        )
        patient_repository.create(patient1)
        patient_repository.create(patient2)
        
        # Act
        results = patient_repository.get_patients(
            filters={"last_name": "Doe", "gender": "female"}
        )
        
        # Assert
        assert len(results) == 1
        assert results[0].first_name == "Jane"
        assert results[0].gender == "female"
```

## Conclusion

This implementation roadmap provides a detailed, step-by-step plan for transforming the current Novamind Digital Twin test suite into a production-ready test infrastructure. Following this roadmap will:

1. Reorganize the chaotic scripts directory into a clean, logical structure
2. Implement canonical test runners following the SSOT approach
3. Migrate tests to the proper directory structure
4. Improve test quality and coverage
5. Integrate with CI/CD pipelines

By the end of this implementation, the Novamind Digital Twin will have a robust, maintainable test infrastructure that ensures reliability, performance, and security while enabling rapid development.

The roadmap is designed to be incremental and pragmatic, allowing for continuous improvement while maintaining the ability to run tests throughout the migration process. This approach minimizes disruption while maximizing the benefits of the new test infrastructure.