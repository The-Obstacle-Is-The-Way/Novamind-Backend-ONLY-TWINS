# Test Scripts Implementation Plan

## Overview

This document provides a detailed implementation plan for the canonical test scripts infrastructure, building on the analysis in `05_TEST_SCRIPTS_ANALYSIS.md`. It includes specific code implementations, migration steps, and guidelines to establish a production-grade test execution environment for the Novamind Digital Twin platform.

## Canonical Test Runner Implementation

The core of our testing infrastructure will be a single, canonical test runner that implements the directory-based SSOT approach. Below is the complete implementation of this runner:

### `backend/scripts/test/runners/run_tests.py`

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

Features:
    - Progressive test execution (dependent on preceding test success)
    - Detailed reporting with colored output
    - Coverage reporting integration
    - JUnit XML output for CI/CD integration
    - Filtering by markers

Exit Codes:
    0 - All requested tests passed
    1 - At least one test failed
    2 - Invalid arguments or configuration
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


def ensure_test_directories() -> bool:
    """
    Ensure test directory structure exists.
    
    Returns:
        True if all directories exist or were created, False otherwise
    """
    try:
        tests_dir = Path('backend/app/tests')
        if not tests_dir.exists():
            print(f"{Color.RED}Test directory {tests_dir} does not exist{Color.ENDC}")
            return False
            
        for directory in ['standalone', 'venv', 'integration']:
            dir_path = tests_dir / directory
            dir_path.mkdir(exist_ok=True, parents=True)
            
            # Create __init__.py files for Python imports
            init_file = dir_path / '__init__.py'
            if not init_file.exists():
                init_file.touch()
        
        return True
    except Exception as e:
        print(f"{Color.RED}Error ensuring test directories: {e}{Color.ENDC}")
        return False


def run_test_directory(
    directory: str, 
    coverage: bool, 
    junit: bool, 
    markers: Optional[str],
    parallel: Optional[int] = None,
    verbose: bool = False,
    test_filter: Optional[str] = None,
    failfast: bool = False
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Run tests in the specified directory.
    
    Args:
        directory: The test directory to run (standalone, venv, integration)
        coverage: Whether to generate coverage reports
        junit: Whether to generate JUnit XML reports
        markers: Optional markers to filter tests
        parallel: Optional number of parallel processes to use
        verbose: Whether to use verbose output
        test_filter: Optional filter for test path/names
        failfast: Whether to stop on first failure
        
    Returns:
        Tuple of (success, execution_time, stats)
    """
    print_section(f"Running {directory.capitalize()} Tests")
    
    # Base pytest command
    cmd = ["python", "-m", "pytest", f"backend/app/tests/{directory}/"]
    
    if verbose:
        cmd.append("-v")
    
    # Add coverage options if requested
    if coverage:
        cmd.extend([
            "--cov=backend/app", 
            f"--cov-report=html:backend/coverage_html/{directory}_tests",
            "--cov-report=term"
        ])
    
    # Add JUnit XML output if requested
    if junit:
        results_dir = Path("backend/test-results")
        results_dir.mkdir(exist_ok=True)
        cmd.append(f"--junitxml=backend/test-results/{directory}-results.xml")
    
    # Add markers if specified
    if markers:
        cmd.extend(["-m", markers])
    
    # Add test filter if specified
    if test_filter:
        cmd.append(test_filter)
    
    # Add parallel execution if specified
    if parallel and parallel > 1:
        cmd.extend(["-n", str(parallel)])
    
    # Add failfast if specified
    if failfast:
        cmd.append("--exitfirst")
    
    # Set up environment variables
    env = os.environ.copy()
    if directory == 'integration':
        # Configuration for integration tests
        env.update({
            "TESTING": "True",
            "DATABASE_URL": os.environ.get("DATABASE_URL", 
                            "postgresql://postgres:postgres@localhost:5432/novamind_test")
        })
    
    # Run the tests
    success, output, execution_time = run_command(cmd, env)
    
    # Parse output for test statistics
    stats = parse_pytest_output(output)
    
    # Print output and result
    if verbose:
        print(output)
    else:
        # Print just the summary in non-verbose mode
        summary_lines = extract_pytest_summary(output)
        for line in summary_lines:
            print(line)
    
    status = f"{Color.GREEN}PASSED{Color.ENDC}" if success else f"{Color.RED}FAILED{Color.ENDC}"
    print(f"\n{directory.capitalize()} Tests: {status} in {execution_time:.2f}s\n")
    
    return success, execution_time, stats


def parse_pytest_output(output: str) -> Dict[str, Any]:
    """
    Parse pytest output to extract test statistics.
    
    Args:
        output: The pytest output to parse
        
    Returns:
        Dictionary with test statistics
    """
    stats = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "xfailed": 0,
        "xpassed": 0
    }
    
    # Look for the summary line
    for line in output.splitlines():
        if "failed" in line and "passed" in line and "skipped" in line:
            # Parse the summary line
            parts = line.split()
            for part in parts:
                if "passed" in part:
                    try:
                        stats["passed"] = int(part.split("passed")[0])
                    except (ValueError, IndexError):
                        pass
                elif "failed" in part:
                    try:
                        stats["failed"] = int(part.split("failed")[0])
                    except (ValueError, IndexError):
                        pass
                elif "skipped" in part:
                    try:
                        stats["skipped"] = int(part.split("skipped")[0])
                    except (ValueError, IndexError):
                        pass
                elif "error" in part:
                    try:
                        stats["errors"] = int(part.split("error")[0])
                    except (ValueError, IndexError):
                        pass
                elif "xfailed" in part:
                    try:
                        stats["xfailed"] = int(part.split("xfailed")[0])
                    except (ValueError, IndexError):
                        pass
                elif "xpassed" in part:
                    try:
                        stats["xpassed"] = int(part.split("xpassed")[0])
                    except (ValueError, IndexError):
                        pass
    
    # Calculate total
    stats["total"] = (stats["passed"] + stats["failed"] + stats["skipped"] + 
                     stats["errors"] + stats["xfailed"] + stats["xpassed"])
    
    return stats


def extract_pytest_summary(output: str) -> List[str]:
    """
    Extract just the summary lines from pytest output.
    
    Args:
        output: The pytest output to parse
        
    Returns:
        List of summary lines
    """
    summary_lines = []
    in_summary = False
    
    for line in output.splitlines():
        if "= FAILURES =" in line:
            in_summary = True
            summary_lines.append(line)
        elif in_summary:
            summary_lines.append(line)
        elif "= short test summary info =" in line:
            in_summary = True
            summary_lines.append(line)
        elif "= " in line and " =" in line and "test session starts" not in line:
            # Catch section headers
            summary_lines.append(line)
    
    # Always include the final summary line
    for line in output.splitlines():
        if "failed" in line and "passed" in line and " in " in line:
            summary_lines.append(line)
            break
    
    return summary_lines


def generate_coverage_report() -> None:
    """Generate combined coverage report from all test runs."""
    print_section("Generating Combined Coverage Report")
    
    # Create coverage directory if it doesn't exist
    coverage_dir = Path("backend/coverage_html/combined")
    coverage_dir.mkdir(exist_ok=True, parents=True)
    
    # Combine coverage data
    run_command(["python", "-m", "coverage", "combine"])
    
    # Generate reports
    run_command([
        "python", "-m", "coverage", "html", 
        "-d", "backend/coverage_html/combined"
    ])
    
    # Show report
    success, output, _ = run_command(["python", "-m", "coverage", "report"])
    print(output)


def main() -> int:
    """
    Main function to parse arguments and run tests.
    
    Returns:
        Exit code (0 for success, 1 for test failures, 2 for configuration errors)
    """
    # Disable colors on Windows if not supported
    Color.disable_if_windows()
    
    parser = argparse.ArgumentParser(
        description="Novamind Digital Twin Canonical Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1]
    )
    
    # Test selection arguments
    test_group = parser.add_argument_group("Test Selection")
    test_group.add_argument('--all', action='store_true', help='Run all tests')
    test_group.add_argument('--standalone', action='store_true', help='Run standalone tests')
    test_group.add_argument('--venv', action='store_true', help='Run VENV tests')
    test_group.add_argument('--integration', action='store_true', help='Run integration tests')
    test_group.add_argument('--security', action='store_true', help='Run security tests (across all levels)')
    
    # Output arguments
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument('--coverage', action='store_true', help='Generate coverage reports')
    output_group.add_argument('--junit', action='store_true', help='Generate JUnit XML reports')
    output_group.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Filtering arguments
    filter_group = parser.add_argument_group("Test Filtering")
    filter_group.add_argument('--markers', type=str, help='Only run tests with specific markers')
    filter_group.add_argument('--filter', type=str, help='Filter tests by name/path')
    
    # Execution arguments
    exec_group = parser.add_argument_group("Execution Options")
    exec_group.add_argument('--parallel', '-p', type=int, help='Number of processes to use for test execution')
    exec_group.add_argument('--failfast', action='store_true', help='Stop on first failure')
    
    args = parser.parse_args()
    
    # Default to running all tests if no specific test type specified
    if not (args.standalone or args.venv or args.integration or args.all or args.security):
        args.all = True
    
    # Print banner
    print_header("Novamind Digital Twin Test Runner")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ensure directory structure exists
    if not ensure_test_directories():
        print(f"{Color.RED}Failed to ensure test directories exist. Aborting.{Color.ENDC}")
        return 2
    
    # Special handling for security tests
    if args.security:
        args.markers = "security"
        if not args.standalone and not args.venv and not args.integration:
            args.all = True
    
    results = {}
    execution_times = {}
    stats = {}
    
    # Run standalone tests
    if args.standalone or args.all:
        results['standalone'], execution_times['standalone'], stats['standalone'] = run_test_directory(
            'standalone', args.coverage, args.junit, args.markers, args.parallel, args.verbose, args.filter, args.failfast
        )
    
    # Run VENV tests only if standalone tests pass (when running all)
    if args.venv or args.all:
        if args.all and not results.get('standalone', True):
            print(f"{Color.YELLOW}Skipping VENV tests due to standalone test failures{Color.ENDC}")
            results['venv'] = False
        else:
            results['venv'], execution_times['venv'], stats['venv'] = run_test_directory(
                'venv', args.coverage, args.junit, args.markers, args.parallel, args.verbose, args.filter, args.failfast
            )
    
    # Run integration tests only if VENV tests pass (when running all)
    if args.integration or args.all:
        if args.all and not results.get('venv', True):
            print(f"{Color.YELLOW}Skipping integration tests due to VENV test failures{Color.ENDC}")
            results['integration'] = False
        else:
            results['integration'], execution_times['integration'], stats['integration'] = run_test_directory(
                'integration', args.coverage, args.junit, args.markers, args.parallel, args.verbose, args.filter, args.failfast
            )
    
    # Generate combined coverage report
    if args.coverage and any(results.values()):
        generate_coverage_report()
    
    # Print summary
    print_header("Test Summary")
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_time = 0.0
    
    for test_type, success in results.items():
        status = f"{Color.GREEN}PASSED{Color.ENDC}" if success else f"{Color.RED}FAILED{Color.ENDC}"
        time_info = f" ({execution_times.get(test_type, 0):.2f}s)" if test_type in execution_times else ""
        
        # Add test counts if available
        test_info = ""
        if test_type in stats:
            test_stats = stats[test_type]
            test_info = f" - {test_stats.get('passed', 0)} passed, {test_stats.get('failed', 0)} failed, {test_stats.get('skipped', 0)} skipped"
            total_tests += test_stats.get('total', 0)
            total_passed += test_stats.get('passed', 0)
            total_failed += test_stats.get('failed', 0)
        
        print(f"{test_type.capitalize()} Tests: {status}{time_info}{test_info}")
        
        total_time += execution_times.get(test_type, 0)
    
    # Print totals
    if total_tests > 0:
        print(f"\nTotal: {total_tests} tests, {total_passed} passed, {total_failed} failed in {total_time:.2f}s")
    
    # Return appropriate exit code
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
```

## Security Test Runner Implementation

A specialized runner for security tests is also essential:

### `backend/scripts/test/runners/run_security.py`

```python
#!/usr/bin/env python3
"""
Novamind Digital Twin Security Test Runner

This script focuses on running security tests for HIPAA compliance across all test levels.
It complements the main test runner but focuses specifically on security-related tests.

Usage:
    python scripts/test/runners/run_security.py  # Run all security tests
    python scripts/test/runners/run_security.py --report  # Generate security report
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import functions from main test runner
try:
    from backend.scripts.test.runners.run_tests import (
        print_header, print_section, run_command, Color
    )
except ImportError:
    # If we can't import, define simple versions
    class Color:
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
    
    def print_header(message):
        print(f"\n{Color.BOLD}{Color.BLUE}{'=' * 80}{Color.ENDC}")
        print(f"{Color.BOLD}{Color.BLUE}{message.center(80)}{Color.ENDC}")
        print(f"{Color.BOLD}{Color.BLUE}{'=' * 80}{Color.ENDC}\n")
    
    def print_section(message):
        print(f"\n{Color.BOLD}{Color.YELLOW}{message}{Color.ENDC}")
        print(f"{Color.BOLD}{Color.YELLOW}{'-' * len(message)}{Color.ENDC}\n")
    
    def run_command(cmd, env=None):
        try:
            env_vars = env or os.environ.copy()
            result = subprocess.run(
                cmd,
                env=env_vars,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            success = result.returncode == 0
            output = result.stdout
        except Exception as e:
            success = False
            output = str(e)
        return success, output, 0


def run_security_tests(report: bool = False) -> bool:
    """
    Run all security-related tests.
    
    Args:
        report: Whether to generate a security report
        
    Returns:
        True if all tests passed, False otherwise
    """
    print_header("Novamind Digital Twin Security Test Runner")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests with security marker
    print_section("Running Security Tests")
    
    # Use the main test runner with the security marker
    cmd = [
        "python", "backend/scripts/test/runners/run_tests.py",
        "--all", "--markers", "security", 
        "--junit", "--coverage"
    ]
    
    success, output, _ = run_command(cmd)
    
    print(output)
    
    if report:
        generate_security_report()
    
    status = f"{Color.GREEN}PASSED{Color.ENDC}" if success else f"{Color.RED}FAILED{Color.ENDC}"
    print(f"\nSecurity Tests: {status}\n")
    
    return success


def generate_security_report() -> None:
    """Generate a comprehensive security report."""
    print_section("Generating Security Report")
    
    # Ensure report directory exists
    reports_dir = Path("backend/security-reports")
    reports_dir.mkdir(exist_ok=True, parents=True)
    
    # Current timestamp for report filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Generate coverage report for security-related code
    coverage_cmd = [
        "python", "-m", "pytest", 
        "backend/app/tests/", 
        "--cov=backend/app/infrastructure/security", 
        "--cov=backend/app/domain/security",
        "--cov-report=term",
        f"--cov-report=json:backend/security-reports/security_coverage_{timestamp}.json"
    ]
    
    success, output, _ = run_command(coverage_cmd)
    
    if success:
        print("Security coverage report generated successfully")
    else:
        print(f"{Color.RED}Failed to generate security coverage report{Color.ENDC}")
    
    # 2. Run HIPAA compliance check
    hipaa_cmd = [
        "python", "backend/scripts/security/run_hipaa_phi_audit.py",
        f"--output=backend/security-reports/hipaa_security_report_{timestamp}.json"
    ]
    
    success, output, _ = run_command(hipaa_cmd)
    
    if success:
        print("HIPAA compliance report generated successfully")
    else:
        print(f"{Color.RED}Failed to generate HIPAA compliance report{Color.ENDC}")
    
    # 3. Dependency security scan
    dependency_cmd = [
        "python", "backend/scripts/security/scan_dependencies.py",
        f"--output=backend/security-reports/dependency_report_{timestamp}.json"
    ]
    
    success, output, _ = run_command(dependency_cmd)
    
    if success:
        print("Dependency security report generated successfully")
    else:
        print(f"{Color.RED}Failed to generate dependency security report{Color.ENDC}")
    
    # 4. Generate combined security report
    combined_cmd = [
        "python", "backend/scripts/security/generate_security_report.py",
        f"--coverage=backend/security-reports/security_coverage_{timestamp}.json",
        f"--hipaa=backend/security-reports/hipaa_security_report_{timestamp}.json",
        f"--dependencies=backend/security-reports/dependency_report_{timestamp}.json",
        f"--output=backend/security-reports/security-report-{timestamp}"
    ]
    
    success, output, _ = run_command(combined_cmd)
    
    if success:
        print(f"Combined security report generated: backend/security-reports/security-report-{timestamp}.html")
    else:
        print(f"{Color.RED}Failed to generate combined security report{Color.ENDC}")


def main() -> int:
    """
    Main function to parse arguments and run security tests.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Run security tests for Novamind Digital Twin")
    parser.add_argument('--report', action='store_true', help='Generate security report')
    
    args = parser.parse_args()
    
    success = run_security_tests(args.report)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
```

## Test Analysis Tool Implementation

A key tool for analyzing test dependencies:

### `backend/scripts/test/tools/analyze_tests.py`

```python
#!/usr/bin/env python3
"""
Novamind Digital Twin Test Analyzer

This script analyzes test files to determine their dependency level, helping with
test classification and migration to the directory SSOT approach.

Usage:
    python scripts/test/tools/analyze_tests.py  # Analyze all tests
    python scripts/test/tools/analyze_tests.py --path backend/app/tests/some_dir  # Analyze specific directory
    python scripts/test/tools/analyze_tests.py --report  # Generate detailed report
"""

import ast
import os
import sys
import json
import argparse
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

# ANSI color codes for terminal output
class Color:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


# Define dependency indicators for each level
STANDALONE_STDLIB_MODULES = {
    'abc', 'argparse', 'asyncio', 'base64', 'collections', 'contextlib', 
    'copy', 'dataclasses', 'datetime', 'decimal', 'enum', 'functools', 
    'hashlib', 'io', 'itertools', 'json', 'math', 'os', 'pathlib', 're', 
    'secrets', 'string', 'sys', 'tempfile', 'time', 'typing', 'uuid', 'warnings'
}

STANDALONE_EXCEPTIONS = {
    'pytest', 'unittest', 'typing_extensions'
}

VENV_INDICATORS = {
    # Main package dependencies
    'fastapi', 'sqlalchemy', 'pydantic', 'numpy', 'pandas',
    'passlib', 'cryptography', 'httpx', 'starlette', 'jose',
    'jwt', 'bcrypt', 'redis', 'celery', 'alembic', 'boto3',
    'requests',
    
    # Internal app modules that don't need external services
    'app.domain', 'app.core', 'app.application'
}

INTEGRATION_INDICATORS = {
    # External service dependencies
    'psycopg2', 'asyncpg', 'aiobotocore', 'aiohttp', 'motor',
    'docker', 'kubernetes', 'redis.asyncio',
    
    # Test client and database
    'test_client', 'TestClient', 'database', 'db_session',
    
    # Internal app modules that need external services
    'app.infrastructure.persistence', 'app.infrastructure.external'
}

SECURITY_MARKERS = {
    'security', 'hipaa', 'phi', 'authentication', 'authorization', 'encryption',
    'app.infrastructure.security'
}


class TestAnalyzer:
    """Analyzer for test files to determine dependency level."""
    
    def __init__(self):
        self.categorized_tests = {
            "standalone": [],
            "venv": [],
            "integration": [],
            "security": [],  # Tests can be both security and one of the above
            "unknown": []
        }
        self.test_details = {}
        self.errors = []
    
    def get_imports(self, file_path: Path) -> Set[str]:
        """
        Extract all import statements from a Python file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Set of imported module names
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            imports = set()
            import_froms = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.add(name.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module
                        import_froms.add(module_name)
                        # Also add the root package
                        imports.add(module_name.split('.')[0])
            
            return imports | import_froms
        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {str(e)}")
            return set()
    
    def has_marker(self, file_path: Path, marker: str) -> bool:
        """
        Check if a file has a specific pytest marker.
        
        Args:
            file_path: Path to the Python file
            marker: The marker to look for
            
        Returns:
            True if the marker is found, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return f"@pytest.mark.{marker}" in content
        except Exception:
            return False
    
    def get_test_fixtures(self, file_path: Path) -> Set[str]:
        """
        Extract fixture usage from a test file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Set of fixture names used
        """
        fixtures = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            # Find all function definitions with arguments
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for arg in node.args.args:
                        # Assume function arguments in test files are fixtures
                        # This is a heuristic and might need refinement
                        fixtures.add(arg.arg)
        except Exception:
            pass
        
        return fixtures
    
    def classify_test_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Classify a test file by analyzing its imports and content.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            Dictionary with classification details
        """
        result = {
            "path": str(file_path),
            "file_name": file_path.name,
            "category": "unknown",
            "imports": [],
            "fixtures": [],
            "markers": [],
            "is_security": False
        }
        
        # Get imports
        imports = self.get_imports(file_path)
        result["imports"] = list(imports)
        
        # Get fixtures
        fixtures = self.get_test_fixtures(file_path)
        result["fixtures"] = list(fixtures)
        
        # Check for markers
        markers = []
        for marker in ["standalone", "venv", "integration", "security"]:
            if self.has_marker(file_path, marker):
                markers.append(marker)
        result["markers"] = markers
        
        # Check if any security indicators are present
        is_security = False
        for indicator in SECURITY_MARKERS:
            if indicator in str(imports) or self.has_marker(file_path, "security"):
                is_security = True
                break
        result["is_security"] = is_security
        
        # Determine category
        if "integration" in markers or any(ind in imports for ind in INTEGRATION_INDICATORS) or "db_session" in fixtures:
            category = "integration"
        elif "venv" in markers or any(ind in imports for ind in VENV_INDICATORS):
            category = "venv"
        elif "standalone" in markers or (
                all(imp in STANDALONE_STDLIB_MODULES or imp in STANDALONE_EXCEPTIONS for imp in imports)):
            category = "standalone"
        else:
            category = "unknown"
        
        result["category"] = category
        
        return result
    
    def analyze_directory(self, directory: Path) -> None:
        """
        Analyze all test files in a directory recursively.
        
        Args:
            directory: Directory to analyze
        """
        for root, _, files in os.walk(directory):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    file_path = Path(root) / file
                    result = self.classify_test_file(file_path)
                    
                    category = result["category"]
                    self.categorized_tests[category].append(str(file_path))
                    
                    if result["is_security"]:
                        self.categorized_tests["security"].append(str(file_path))
                    
                    self.test_details[str(file_path)] = result
    
    def generate_report(self, output_file: Optional[Path] = None) -> None:
        """
        Generate a detailed report of the analysis.
        
        Args:
            output_file: Optional path to write the report to
        """
        total_tests = sum(len(tests) for tests in self.categorized_tests.values()) - len(self.categorized_tests["security"])
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "standalone_count": len(self.categorized_tests["standalone"]),
                "venv_count": len(self.categorized_tests["venv"]),
                "integration_count": len(self.categorized_tests["integration"]),
                "security_count": len(self.categorized_tests["security"]),
                "unknown_count": len(self.categorized_tests["unknown"]),
                "standalone_percentage": (len(self.categorized_tests["standalone"]) / total_tests) * 100 if total_tests else 0,
                "venv_percentage": (len(self.categorized_tests["venv"]) / total_tests) * 100 if total_tests else 0,
                "integration_percentage": (len(self.categorized_tests["integration"]) / total_tests) * 100 if total_tests else 0,
                "security_percentage": (len(self.categorized_tests["security"]) / total_tests) * 100 if total_tests else 0,
                "unknown_percentage": (len(self.categorized_tests["unknown"]) / total_tests) * 100 if total_tests else 0
            },
            "categorized_tests": self.categorized_tests,
            "test_details": self.test_details,
            "errors": self.errors
        }
        
        # Print summary to console
        print(f"\n{Color.BOLD}Test Analysis Summary{Color.ENDC}")
        print(f"Total tests: {total_tests}")
        print(f"Standalone tests: {len(self.categorized_tests['standalone'])} ({report['summary']['standalone_percentage']:.1f}%)")
        print(f"VENV tests: {len(self.categorized_tests['venv'])} ({report['summary']['venv_percentage']:.1f}%)")
        print(f"Integration tests: {len(self.categorized_tests['integration'])} ({report['summary']['integration_percentage']:.1f}%)")
        print(f"Security tests: {len(self.categorized_tests['security'])} ({report['summary']['security_percentage']:.1f}%)")
        print(f"Unknown tests: {len(self.categorized_tests['unknown'])} ({report['summary']['unknown_percentage']:.1f}%)")
        
        if self.errors:
            print(f"\n{Color.RED}Errors:{Color.ENDC}")
            for error in self.errors:
                print(f"- {error}")
        
        # Write report to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=4)
            
            print(f"\nDetailed report written to {output_file}")


def main() -> int:
    """
    Main function to parse arguments and run analysis.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Analyze test files for dependency level")
    parser.add_argument('--path', type=str, default='backend/app/tests', help='Path to analyze')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--output', type=str, help='Output file for detailed report')
    
    args = parser.parse_args()
    
    analyzer = TestAnalyzer()
    analyzer.analyze_directory(Path(args.path))
    
    if args.report or args.output:
        output_file = args.output or "backend/test-classification-report.json"
        analyzer.generate_report(Path(output_file))
    else:
        analyzer.generate_report()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Tests Migration Tool Implementation

To facilitate migration from the current test organization to the SSOT approach:

### `backend/scripts/test/tools/migrate_tests.py`

```python
#!/usr/bin/env python3
"""
Novamind Digital Twin Test Migration Tool

This script migrates tests to the directory-based SSOT approach, moving them
to the appropriate directories based on their dependency level.

Usage:
    python scripts/test/tools/migrate_tests.py --analyze  # Analyze tests without moving
    python scripts/test/tools/migrate_tests.py --execute  # Move tests to new locations
"""

import os
import re
import sys
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

# Import test analyzer
try:
    from backend.scripts.test.tools.analyze_tests import TestAnalyzer
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from test.tools.analyze_tests import TestAnalyzer


class Color:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class TestMigrator:
    """Migrates tests to the directory-based SSOT approach."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.analyzer = TestAnalyzer()
        self.migrated_files = []
        self.errors = []
    
    def ensure_directory_structure(self) -> bool:
        """
        Ensure the SSOT directory structure exists.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            tests_dir = Path('backend/app/tests')
            if not tests_dir.exists():
                print(f"{Color.RED}Test directory {tests_dir} does not exist{Color.ENDC}")
                return False
            
            for directory in ['standalone', 'venv', 'integration']:
                dir_path = tests_dir / directory
                if not self.dry_run:
                    dir_path.mkdir(exist_ok=True, parents=True)
                    
                    # Create __init__.py files
                    init_file = dir_path / '__init__.py'
                    if not init_file.exists():
                        if not self.dry_run:
                            init_file.touch()
                
                print(f"{'Would create' if self.dry_run else 'Created'} directory: {dir_path}")
            
            return True
        except Exception as e:
            self.errors.append(f"Error ensuring directory structure: {str(e)}")
            return False
    
    def update_imports(self, file_path: Path, new_path: Path) -> str:
        """
        Update imports in a test file to work in its new location.
        
        Args:
            file_path: Original file path
            new_path: New file path
            
        Returns:
            Updated file content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Calculate the relative path difference
            old_parts = file_path.parent.parts
            new_parts = new_path.parent.parts
            
            # Find common prefix
            common_prefix_len = 0
            for i, (old, new) in enumerate(zip(old_parts, new_parts)):
                if old != new:
                    break
                common_prefix_len = i + 1
            
            # If there's no need to update imports
            if common_prefix_len == len(old_parts) and common_prefix_len == len(new_parts):
                return content
            
            # Update relative imports
            updated_content = content
            
            # Handle relative imports
            updated_content = re.sub(
                r'from \.{1,2}(\w+)',
                r'from app.tests.\1',
                updated_content
            )
            
            # Handle import statements that should be updated
            for old_dir in ['unit', 'integration', 'api']:
                updated_content = re.sub(
                    f'from app.tests.{old_dir}',
                    'from app.tests',
                    updated_content
                )
            
            return updated_content
        except Exception as e:
            self.errors.append(f"Error updating imports in {file_path}: {str(e)}")
            return ""
    
    def migrate_test_file(self, file_path: Path, category: str) -> Optional[Path]:
        """
        Migrate a test file to its appropriate directory.
        
        Args:
            file_path: Path to the test file
            category: The test category (standalone, venv, integration)
            
        Returns:
            Path to the new location, or None if migration failed
        """
        try:
            # Determine new path
            relative_path = file_path.relative_to(Path('backend/app/tests'))
            new_dir = Path('backend/app/tests') / category
            
            # Just use the filename, not preserving subdirectories
            new_path = new_dir / file_path.name
            
            # Check if we need to move the file
            if file_path == new_path:
                print(f"{Color.YELLOW}File is already in the correct location: {file_path}{Color.ENDC}")
                return file_path
            
            # Update imports
            updated_content = self.update_imports(file_path, new_path)
            if not updated_content:
                return None
            
            print(f"{'Would move' if self.dry_run else 'Moving'} {file_path} -> {new_path}")
            
            if not self.dry_run:
                # Write the updated content to the new location
                new_path.parent.mkdir(exist_ok=True, parents=True)
                with open(new_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
            
            return new_path
        except Exception as e:
            self.errors.append(f"Error migrating {file_path}: {str(e)}")
            return None
    
    def migrate_all_tests(self) -> None:
        """Migrate all tests to the directory-based SSOT approach."""
        # Ensure directory structure
        if not self.ensure_directory_structure():
            return
        
        # Analyze tests
        self.analyzer.analyze_directory(Path('backend/app/tests'))
        
        # Migrate tests by category
        for category in ["standalone", "venv", "integration"]:
            for file_path_str in self.analyzer.categorized_tests[category]:
                file_path = Path(file_path_str)
                new_path = self.migrate_test_file(file_path, category)
                
                if new_path:
                    self.migrated_files.append((file_path, new_path))
        
        # Handle unknown tests
        for file_path_str in self.analyzer.categorized_tests["unknown"]:
            file_path = Path(file_path_str)
            
            # Default unknown tests to venv if no clear determination can be made
            print(f"{Color.YELLOW}Unknown test type: {file_path}, defaulting to 'venv'{Color.ENDC}")
            new_path = self.migrate_test_file(file_path, "venv")
            
            if new_path:
                self.migrated_files.append((file_path, new_path))
    
    def generate_report(self) -> None:
        """Generate a report of the migration."""
        print(f"\n{Color.BOLD}Test Migration Summary{Color.ENDC}")
        print(f"Total files: {len(self.migrated_files)}")
        print(f"Dry run: {'Yes' if self.dry_run else 'No'}")
        
        if self.errors:
            print(f"\n{Color.RED}Errors:{Color.ENDC}")
            for error in self.errors:
                print(f"- {error}")
        
        print(f"\n{Color.BOLD}Files to migrate:{Color.ENDC}")
        for old_path, new_path in self.migrated_files:
            if old_path != new_path:
                print(f"- {old_path} -> {new_path}")


def main() -> int:
    """
    Main function to parse arguments and run migration.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Migrate tests to directory-based SSOT approach")
    parser.add_argument('--analyze', action='store_true', help='Analyze tests without moving')
    parser.add_argument('--execute', action='store_true', help='Execute migration')
    
    args = parser.parse_args()
    
    if not args.analyze and not args.execute:
        parser.print_help()
        return 1
    
    migrator = TestMigrator(dry_run=not args.execute)
    migrator.migrate_all_tests()
    migrator.generate_report()
    
    return 0 if not migrator.errors else 1


if __name__ == "__main__":
    sys.exit(main())
```

## Implementation Roadmap

The implementation will proceed in five phases:

### Phase 1: Setting Up the Script Infrastructure (Week 1)

1. Create the directory structure:
   ```bash
   mkdir -p backend/scripts/test/runners
   mkdir -p backend/scripts/test/tools
   mkdir -p backend/scripts/test/ci
   mkdir -p backend/scripts/test/fixes
   mkdir -p backend/scripts/security
   mkdir -p backend/scripts/setup
   mkdir -p backend/scripts/utils
   ```

2. Implement the core scripts:
   - `backend/scripts/test/runners/run_tests.py`
   - `backend/scripts/test/tools/analyze_tests.py`

3. Create documentation and README files for each directory

### Phase 2: Test Analysis and Classification (Week 2)

1. Run the analysis tool to understand current test dependencies:
   ```bash
   python backend/scripts/test/tools/analyze_tests.py --report
   ```

2. Review and refine the classification logic based on results
3. Document the test categorization results
4. Identify problematic tests that need attention

### Phase 3: Test Migration (Weeks 3-4)

1. Implement the test migration tool
2. Run the migration in dry-run mode:
   ```bash
   python backend/scripts/test/tools/migrate_tests.py --analyze
   ```

3. Fix any issues identified in dry-run
4. Execute the migration:
   ```bash
   python backend/scripts/test/tools/migrate_tests.py --execute
   ```

5. Verify migrated tests run correctly

### Phase 4: CI/CD Integration (Week 5)

1. Update CI/CD pipelines to use the new test runners
2. Implement test parallelization for faster test execution
3. Set up staging checks for security tests
4. Configure coverage reporting and thresholds

### Phase 5: Cleanup and Documentation (Week 6)

1. Create deprecation notices for old scripts
2. Clean up redundant scripts
3. Update documentation for test processes
4. Train team on new test infrastructure

## HIPAA Compliance Considerations

For HIPAA compliance, the following additional considerations must be addressed:

1. **PHI Data Protection in Tests**:
   - All test data containing PHI must be synthetic
   - Test databases must have encryption at rest
   - Test output must be sanitized to avoid PHI leakage

2. **Security Testing Requirements**:
   - Security tests must be comprehensive
   - Coverage for all HIPAA Security Rule controls
   - Audit logging must be verified

3. **Test Access Controls**:
   - Test results and reports must be properly secured
   - Limited access to test environments

4. **Compliance Reporting**:
   - Security test results must generate compliance reports
   - Issues must be tracked and remediated

## Conclusion

This implementation plan provides a comprehensive approach to modernizing the Novamind Digital Twin test infrastructure using a directory-based SSOT approach. Following this plan will create a clean, maintainable, and scalable test infrastructure that meets HIPAA compliance requirements and supports the platform's progression to a production-ready state.

The included script implementations provide a solid foundation that can be deployed immediately to begin the modernization process. Additional customization and refinement will be required as the implementation progresses, but this plan provides all the necessary tools and direction to successfully complete the migration.