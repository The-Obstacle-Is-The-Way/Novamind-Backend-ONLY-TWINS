# Test Suite Implementation Plan

## Overview

This document provides a concrete, actionable implementation plan to migrate the current Novamind Digital Twin test suite to the SSOT-based directory structure outlined in the Test Infrastructure SSOT document. This plan addresses the issues identified in the Test Suite Analysis document and prescribes specific steps, scripts, and procedures for executing the migration.

## Implementation Goals

1. Reorganize tests using the directory-based SSOT approach
2. Eliminate redundancy and duplication in the test suite
3. Standardize test naming and conventions
4. Ensure all tests run successfully in the new structure
5. Update CI/CD pipelines to work with the new organization

## Migration Phases

The implementation will proceed in six phases:

1. **Test Analysis & Classification**
2. **Initial Directory Structure Creation**
3. **Test Migration & Adaptation**
4. **Fixture Consolidation**
5. **CI/CD Pipeline Updates**
6. **Validation & Documentation**

## Detailed Implementation Plan

### Phase 1: Test Analysis & Classification (Week 1)

#### 1.1 Test Classification Script Development

Create a script that analyzes test files to determine their dependency level:

```python
# backend/scripts/classify_tests.py

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

STANDARD_LIB_MODULES = set(sys.builtin_module_names)
STANDARD_LIB_PATHS = set(sys.path)
STANDALONE_EXCEPTIONS = {"pytest", "typing", "dataclasses"}
VENV_INDICATORS = {
    "fastapi", "sqlalchemy", "pydantic", "numpy", "pandas",
    "passlib", "jwt", "cryptography", "httpx", "starlette"
}
INTEGRATION_INDICATORS = {
    "psycopg2", "asyncpg", "requests", "aiohttp", 
    "test_client", "TestClient", "database", "repository"
}

def get_imports(file_path: Path) -> Set[str]:
    """Extract all import statements from a Python file."""
    with open(file_path, 'r') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return set()
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.add(name.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    
    return imports

def classify_test_file(file_path: Path) -> str:
    """Classify a test file by analyzing its imports and content."""
    imports = get_imports(file_path)
    
    # Remove standard library and standalone exceptions
    non_std_imports = {imp for imp in imports 
                       if imp not in STANDARD_LIB_MODULES 
                       and imp not in STANDALONE_EXCEPTIONS}
    
    # Check for integration indicators in imports or content
    with open(file_path, 'r') as f:
        content = f.read()
        
    for indicator in INTEGRATION_INDICATORS:
        if indicator in content:
            return "integration"
    
    # Check for VENV indicators in imports
    for indicator in VENV_INDICATORS:
        if indicator in non_std_imports:
            return "venv"
    
    # If it has non-standard imports not in our lists, default to venv
    if non_std_imports:
        return "venv"
        
    return "standalone"

def scan_test_directory(directory: Path) -> Dict[str, List[Path]]:
    """Recursively scan a directory for test files and classify them."""
    classification = {
        "standalone": [],
        "venv": [],
        "integration": []
    }
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                file_path = Path(root) / file
                category = classify_test_file(file_path)
                classification[category].append(file_path)
    
    return classification

def generate_report(classification: Dict[str, List[Path]], output_file: Path):
    """Generate a markdown report of test classification."""
    with open(output_file, 'w') as f:
        f.write("# Test Classification Report\n\n")
        
        total = sum(len(files) for files in classification.values())
        f.write(f"Total test files: {total}\n\n")
        
        for category, files in classification.items():
            percentage = (len(files) / total) * 100 if total else 0
            f.write(f"## {category.capitalize()} Tests: {len(files)} ({percentage:.1f}%)\n\n")
            
            for file_path in sorted(files):
                relative_path = file_path.relative_to(Path.cwd())
                f.write(f"- `{relative_path}`\n")
            
            f.write("\n")

def main():
    tests_dir = Path("backend/app/tests")
    output_file = Path("backend/test-classification-report.md")
    
    print(f"Scanning test directory: {tests_dir}")
    classification = scan_test_directory(tests_dir)
    
    print(f"Generating report to: {output_file}")
    generate_report(classification, output_file)
    
    print("\nSummary:")
    for category, files in classification.items():
        print(f"{category.capitalize()}: {len(files)} tests")

if __name__ == "__main__":
    main()
```

#### 1.2 Run Classification Analysis

Execute the classification script to analyze the current test suite:

```bash
python backend/scripts/classify_tests.py
```

#### 1.3 Manual Review of Classification

Review the generated report and make any necessary adjustments to the classification:

1. Identify tests incorrectly classified by the script
2. Document special cases or tests with unusual dependencies
3. Flag tests that will require significant adaptation

### Phase 2: Initial Directory Structure Creation (Week 1)

#### 2.1 Create New Directory Structure

Create the new directory structure while preserving the existing files:

```bash
mkdir -p backend/app/tests/standalone
mkdir -p backend/app/tests/venv
mkdir -p backend/app/tests/integration

# Create subdirectories for clean architecture layers
mkdir -p backend/app/tests/standalone/domain
mkdir -p backend/app/tests/standalone/application
mkdir -p backend/app/tests/standalone/core
mkdir -p backend/app/tests/standalone/common

mkdir -p backend/app/tests/venv/api
mkdir -p backend/app/tests/venv/infrastructure
mkdir -p backend/app/tests/venv/presentation
mkdir -p backend/app/tests/venv/security

mkdir -p backend/app/tests/integration/api
mkdir -p backend/app/tests/integration/repositories
mkdir -p backend/app/tests/integration/e2e
mkdir -p backend/app/tests/integration/security
```

#### 2.2 Add Test Package Files

Add `__init__.py` files to make the new directories proper Python packages:

```bash
for dir in $(find backend/app/tests -type d); do
    touch "$dir/__init__.py"
done
```

#### 2.3 Create Placeholder Conftest Files

Create placeholder conftest files for each level:

```python
# backend/app/tests/standalone/conftest.py
"""
Fixtures for standalone tests that have no external dependencies.
"""
import pytest

# Shared fixtures for standalone tests go here
```

```python
# backend/app/tests/venv/conftest.py
"""
Fixtures for VENV tests that require Python packages but no external services.
"""
import pytest

# Shared fixtures for VENV tests go here
```

```python
# backend/app/tests/integration/conftest.py
"""
Fixtures for integration tests that require external services.
"""
import pytest

# Shared fixtures for integration tests go here
```

### Phase 3: Test Migration & Adaptation (Weeks 2-3)

#### 3.1 Create Migration Script

Create a script to move tests to their new locations:

```python
# backend/scripts/migrate_tests.py

import os
import shutil
from pathlib import Path
import sys
import re

# Import the classification function from classify_tests.py
sys.path.append(str(Path(__file__).parent))
from classify_tests import classify_test_file

def determine_submodule(file_path: Path) -> str:
    """Determine which clean architecture layer submodule a test belongs to."""
    with open(file_path, "r") as f:
        content = f.read()
    
    # Determine submodule based on content patterns
    if re.search(r"(Repository|DB|Database|Model)", content):
        return "repositories" if "integration" in str(file_path) else "infrastructure"
    elif re.search(r"(Controller|Route|Endpoint|API)", content):
        return "api"
    elif re.search(r"(Service|UseCase)", content):
        return "application"
    elif re.search(r"(Entity|Domain|Value)", content):
        return "domain"
    elif re.search(r"(Security|Auth|JWT|Password|Encryption)", content):
        return "security"
    elif re.search(r"(UI|View|Template|Render)", content):
        return "presentation"
    elif re.search(r"(Util|Helper|Common)", content):
        return "core" if "standalone" in str(file_path) else "common"
    
    # Default based on directory
    if "api" in str(file_path):
        return "api"
    elif "domain" in str(file_path):
        return "domain"
    elif "core" in str(file_path):
        return "core"
    elif "infrastructure" in str(file_path):
        return "infrastructure"
    elif "application" in str(file_path):
        return "application"
    elif "security" in str(file_path):
        return "security"
    
    # Fall back to common
    return "common"

def migrate_test_file(file_path: Path, dry_run: bool = True) -> Path:
    """Migrate a test file to its proper location in the new structure."""
    # Classify the test
    category = classify_test_file(file_path)
    
    # Determine submodule
    submodule = determine_submodule(file_path)
    
    # Adjust submodule for category
    if category == "standalone":
        valid_submodules = {"domain", "application", "core", "common"}
        if submodule not in valid_submodules:
            submodule = "common"
    elif category == "integration":
        valid_submodules = {"api", "repositories", "e2e", "security"}
        if submodule not in valid_submodules:
            # Map infrastructure to repositories
            if submodule == "infrastructure":
                submodule = "repositories"
            else:
                submodule = "e2e"
    
    # Construct new path
    new_directory = Path(f"backend/app/tests/{category}/{submodule}")
    new_path = new_directory / file_path.name
    
    print(f"Moving {file_path} -> {new_path}")
    
    if not dry_run:
        # Create directory if it doesn't exist
        os.makedirs(new_directory, exist_ok=True)
        
        # Copy file to new location
        shutil.copy2(file_path, new_path)
        
        # Open the file and replace any imports that might break
        with open(new_path, "r") as f:
            content = f.read()
        
        # Update relative imports - this is a simplistic approach
        # A more robust solution would parse and update the import statements
        if "from .." in content or "from ." in content:
            with open(new_path, "w") as f:
                # Fix imports - more sophisticated handling would be needed
                # This is just a placeholder for the actual implementation
                fixed_content = content.replace("from ..", "from app")
                fixed_content = fixed_content.replace("from .", "from app.tests")
                f.write(fixed_content)
    
    return new_path

def migrate_all_tests(dry_run: bool = True):
    """Migrate all test files to their new locations."""
    tests_dir = Path("backend/app/tests")
    migrated_files = []
    
    for root, _, files in os.walk(tests_dir):
        for file in files:
            # Skip files in the new directory structure
            if any(segment in root for segment in ["standalone", "venv", "integration"]):
                continue
                
            if file.startswith("test_") and file.endswith(".py"):
                file_path = Path(root) / file
                new_path = migrate_test_file(file_path, dry_run)
                migrated_files.append((file_path, new_path))
    
    # Generate migration report
    with open("backend/test-migration-report.md", "w") as f:
        f.write("# Test Migration Report\n\n")
        f.write(f"Mode: {'Dry Run' if dry_run else 'Actual Migration'}\n\n")
        f.write("## Migrated Files\n\n")
        
        for old_path, new_path in migrated_files:
            f.write(f"- `{old_path}` -> `{new_path}`\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate tests to new directory structure")
    parser.add_argument("--execute", action="store_true", help="Actually perform the migration")
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    if dry_run:
        print("DRY RUN MODE - No files will be moved")
    else:
        print("EXECUTE MODE - Files will be migrated")
    
    migrate_all_tests(dry_run)
    
    if dry_run:
        print("\nDry run completed. Review backend/test-migration-report.md and run with --execute to perform migration.")
    else:
        print("\nMigration completed. Review backend/test-migration-report.md for details.")

if __name__ == "__main__":
    main()
```

#### 3.2 Run Migration in Dry-Run Mode

Test the migration script in dry-run mode:

```bash
python backend/scripts/migrate_tests.py
```

#### 3.3 Review Migration Plan

Review the migration report to identify any issues or adjustments needed.

#### 3.4 Execute Migration

Run the migration script to actually move the files:

```bash
python backend/scripts/migrate_tests.py --execute
```

#### 3.5 Test Compatibility Verification

Run tests in their new locations to ensure they still work:

```bash
python -m pytest backend/app/tests/standalone/
python -m pytest backend/app/tests/venv/
python -m pytest backend/app/tests/integration/
```

Fix any broken tests due to import changes or dependency issues.

### Phase 4: Fixture Consolidation (Week 4)

#### 4.1 Fixture Analysis Script

Create a script to analyze fixtures and their usage:

```python
# backend/scripts/analyze_fixtures.py

import ast
import os
from pathlib import Path
from typing import Dict, List, Set

def extract_fixtures(file_path: Path) -> Set[str]:
    """Extract fixture names defined in a file."""
    with open(file_path, 'r') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return set()
    
    fixtures = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.FunctionDef) and 
            any(d.id == 'pytest' and d.attr == 'fixture' 
                for d in node.decorator_list 
                if isinstance(d, ast.Attribute))):
            fixtures.add(node.name)
    
    return fixtures

def extract_fixture_usage(file_path: Path) -> Set[str]:
    """Extract fixture names used in a file."""
    with open(file_path, 'r') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return set()
    
    fixture_usages = set()
    for node in ast.walk(tree):
        # Look for function parameters that might be fixtures
        if isinstance(node, ast.FunctionDef) and node.args.args:
            for arg in node.args.args:
                fixture_usages.add(arg.arg)
    
    return fixture_usages

def analyze_fixtures(directory: Path) -> Dict[str, Dict]:
    """Analyze fixtures defined and used in a directory."""
    fixture_info = {}
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                
                # Extract fixtures defined in this file
                defined_fixtures = extract_fixtures(file_path)
                
                # Extract fixture usage in this file
                used_fixtures = extract_fixture_usage(file_path)
                
                # Record information
                for fixture in defined_fixtures:
                    if fixture not in fixture_info:
                        fixture_info[fixture] = {"defined_in": [], "used_in": []}
                    fixture_info[fixture]["defined_in"].append(str(file_path))
                
                for fixture in used_fixtures:
                    if fixture not in fixture_info:
                        fixture_info[fixture] = {"defined_in": [], "used_in": []}
                    fixture_info[fixture]["used_in"].append(str(file_path))
    
    return fixture_info

def generate_fixture_report(fixture_info: Dict[str, Dict], output_file: Path):
    """Generate a report on fixture usage."""
    with open(output_file, 'w') as f:
        f.write("# Fixture Analysis Report\n\n")
        
        # Orphaned fixtures (defined but not used)
        orphaned = [name for name, info in fixture_info.items() 
                   if info["defined_in"] and not info["used_in"]]
        
        # Missing fixtures (used but not defined)
        missing = [name for name, info in fixture_info.items() 
                  if not info["defined_in"] and info["used_in"]]
        
        # Duplicate fixtures (defined in multiple places)
        duplicated = [name for name, info in fixture_info.items() 
                     if len(info["defined_in"]) > 1]
        
        f.write(f"## Summary\n\n")
        f.write(f"Total fixtures: {len(fixture_info)}\n")
        f.write(f"Orphaned fixtures: {len(orphaned)}\n")
        f.write(f"Missing fixtures: {len(missing)}\n")
        f.write(f"Duplicate fixtures: {len(duplicated)}\n\n")
        
        # Details for each category
        f.write(f"## Orphaned Fixtures\n\n")
        for name in sorted(orphaned):
            f.write(f"### `{name}`\n")
            f.write(f"Defined in:\n")
            for path in fixture_info[name]["defined_in"]:
                f.write(f"- {path}\n")
            f.write("\n")
        
        f.write(f"## Missing Fixtures\n\n")
        for name in sorted(missing):
            f.write(f"### `{name}`\n")
            f.write(f"Used in:\n")
            for path in fixture_info[name]["used_in"]:
                f.write(f"- {path}\n")
            f.write("\n")
        
        f.write(f"## Duplicate Fixtures\n\n")
        for name in sorted(duplicated):
            f.write(f"### `{name}`\n")
            f.write(f"Defined in:\n")
            for path in fixture_info[name]["defined_in"]:
                f.write(f"- {path}\n")
            f.write(f"Used in: {len(fixture_info[name]['used_in'])} files\n\n")

def main():
    tests_dir = Path("backend/app/tests")
    output_file = Path("backend/fixture-analysis-report.md")
    
    print(f"Analyzing fixtures in: {tests_dir}")
    fixture_info = analyze_fixtures(tests_dir)
    
    print(f"Generating report to: {output_file}")
    generate_fixture_report(fixture_info, output_file)

if __name__ == "__main__":
    main()
```

#### 4.2 Run Fixture Analysis

Execute the fixture analysis script:

```bash
python backend/scripts/analyze_fixtures.py
```

#### 4.3 Consolidate Fixtures

Based on the fixture analysis, consolidate fixtures into the appropriate conftest.py files:

1. Move global fixtures to the main conftest.py
2. Move dependency-level fixtures to the respective conftest.py files
3. Eliminate duplicate fixtures
4. Resolve any missing fixtures

#### 4.4 Update Conftest Files

Update the conftest.py files with the consolidated fixtures, ensuring proper imports and dependencies.

### Phase 5: CI/CD Pipeline Updates (Week 5)

#### 5.1 Create Updated Test Runner Script

Create an updated test runner script that works with the new directory structure:

```python
# backend/scripts/run_tests.py

import argparse
import os
import subprocess
import sys
from pathlib import Path
import time

def run_command(command, continue_on_error=False):
    """Run a shell command and return its exit code."""
    print(f"\n>>> Running: {' '.join(command)}\n")
    
    start_time = time.time()
    result = subprocess.run(command)
    duration = time.time() - start_time
    
    print(f"\n>>> Completed in {duration:.2f} seconds with exit code {result.returncode}\n")
    
    if result.returncode != 0 and not continue_on_error:
        sys.exit(result.returncode)
    
    return result.returncode

def run_tests(args):
    """Run tests based on the provided arguments."""
    coverage_args = ["--cov=app", f"--cov-report={args.cov_report}"] if args.coverage else []
    verbose_args = ["-v"] if args.verbose else []
    
    # Remember exit codes for summary
    exit_codes = {}
    
    # Run standalone tests
    if args.standalone or args.all:
        cmd = [
            "python", "-m", "pytest", 
            "backend/app/tests/standalone/",
            *coverage_args,
            *verbose_args
        ]
        exit_codes["standalone"] = run_command(cmd, args.continue_on_failure)
    
    # Run venv tests
    if args.venv or args.all:
        cmd = [
            "python", "-m", "pytest", 
            "backend/app/tests/venv/",
            *coverage_args,
            *verbose_args
        ]
        exit_codes["venv"] = run_command(cmd, args.continue_on_failure)
    
    # Run integration tests
    if args.integration or args.all:
        cmd = [
            "python", "-m", "pytest", 
            "backend/app/tests/integration/",
            *coverage_args,
            *verbose_args
        ]
        exit_codes["integration"] = run_command(cmd, args.continue_on_failure)
    
    # Print summary
    print("\n=== Test Summary ===")
    for category, code in exit_codes.items():
        print(f"{category}: {'PASSED' if code == 0 else 'FAILED'}")

def main():
    parser = argparse.ArgumentParser(description="Run Novamind test suite")
    
    # Test category options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Run all tests")
    group.add_argument("--standalone", action="store_true", help="Run standalone tests only")
    group.add_argument("--venv", action="store_true", help="Run venv tests only")
    group.add_argument("--integration", action="store_true", help="Run integration tests only")
    
    # Additional options
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--cov-report", default="html:coverage_html", help="Coverage report format")
    parser.add_argument("--continue-on-failure", action="store_true", help="Continue running tests even if a category fails")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    run_tests(args)

if __name__ == "__main__":
    main()
```

#### 5.2 Update GitHub Actions Workflow

Update the GitHub Actions workflow to use the new directory structure:

```yaml
# .github/workflows/test.yml

name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  quality:
    name: Code Quality
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 mypy pytest
        pip install -r backend/requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 backend/app
    
    - name: Type check with mypy
      run: |
        mypy backend/app
  
  standalone:
    name: Standalone Tests
    needs: quality
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov
    
    - name: Run standalone tests
      run: |
        python -m pytest backend/app/tests/standalone/ --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: actions/upload-artifact@v3
      with:
        name: standalone-coverage
        path: coverage.xml
  
  venv:
    name: VENV Tests
    needs: standalone
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
        pip install -r backend/requirements-dev.txt
    
    - name: Run VENV tests
      run: |
        python -m pytest backend/app/tests/venv/ --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: actions/upload-artifact@v3
      with:
        name: venv-coverage
        path: coverage.xml
  
  integration:
    name: Integration Tests
    needs: venv
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
        pip install -r backend/requirements-dev.txt
    
    - name: Run Integration tests
      run: |
        python -m pytest backend/app/tests/integration/ --cov=app --cov-report=xml
      env:
        DATABASE_URL: postgresql://test:test@localhost:5432/test
    
    - name: Upload coverage
      uses: actions/upload-artifact@v3
      with:
        name: integration-coverage
        path: coverage.xml
```

### Phase 6: Validation & Documentation (Week 6)

#### 6.1 Comprehensive Test Run

Run the full test suite to ensure everything is working:

```bash
python backend/scripts/run_tests.py --all --coverage
```

#### 6.2 Coverage Analysis

Analyze test coverage and identify areas needing improvement:

```bash
python -m pytest backend/app/tests/ --cov=app --cov-report=html:coverage_html
```

#### 6.3 Update Documentation

Update any remaining documentation to reflect the new test organization:

1. Ensure README files are accurate
2. Update developer guides
3. Consolidate test-related documentation

#### 6.4 Final Cleanup

Remove any old test files or directories that are no longer needed:

```bash
# Remove old test directories after migration is complete and validated
rm -rf backend/app/tests/api
rm -rf backend/app/tests/unit
rm -rf backend/app/tests/e2e
# etc.
```

## Implementation Timeline

| Phase | Tasks | Duration | Dependencies |
|-------|-------|----------|--------------|
| 1. Analysis & Classification | Develop scripts, classify tests | 1 week | None |
| 2. Directory Structure | Create new directories | 1 week | Phase 1 |
| 3. Test Migration | Move and adapt tests | 2 weeks | Phase 2 |
| 4. Fixture Consolidation | Analyze and consolidate fixtures | 1 week | Phase 3 |
| 5. CI/CD Updates | Update test runner and CI | 1 week | Phase 4 |
| 6. Validation | Full testing and documentation | 1 week | Phase 5 |

## Success Criteria

The migration will be considered successful when:

1. All tests run successfully in the new directory structure
2. No redundant or duplicate tests remain
3. Test coverage remains at or above pre-migration levels
4. CI/CD pipelines successfully run all test categories
5. Documentation is updated to reflect the new organization

## Conclusion

This implementation plan provides a systematic approach to migrating the Novamind test suite to the SSOT directory-based organization. Following this phased approach will ensure a smooth transition with minimal disruption to ongoing development activities.