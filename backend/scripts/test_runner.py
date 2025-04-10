#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Runner for Novamind Backend

This script runs unit, integration, and security tests, and generates coverage reports.
It supports selective test execution and custom reporting.
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Test groups definitions
TEST_GROUPS = {
    "ml": ["app/tests/unit/core/services/ml/"],
    "phi": ["app/tests/security/phi/"],
    "core": ["app/tests/unit/core/"],
    "domain": ["app/tests/unit/domain/"],
    "api": ["app/tests/unit/api/", "app/tests/integration/api/"],
    "security": ["app/tests/security/"],
    "infrastructure": ["app/tests/unit/infrastructure/", "app/tests/integration/infrastructure/"],
    "application": ["app/tests/unit/application/", "app/tests/integration/application/"],
    "integration": ["app/tests/integration/"],
    "e2e": ["app/tests/e2e/"]
}

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run tests and generate coverage reports")
    
    # Test selection options
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--security", action="store_true", help="Run security tests only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument("--ml", action="store_true", help="Run ML service tests only")
    parser.add_argument("--phi", action="store_true", help="Run PHI detection tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    
    # Test path options
    parser.add_argument("--path", type=str, help="Specific test path to run")
    parser.add_argument("--module", type=str, help="Specific test module to run")
    
    # Coverage options
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--xml", action="store_true", help="Generate XML coverage report")
    
    # Report options
    parser.add_argument("--report", action="store_true", help="Generate test report")
    parser.add_argument("--report-dir", type=str, default="test-reports", 
                        help="Directory for test reports")
    
    # Execution options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--docker", action="store_true", 
                        help="Run in Docker test environment")
    parser.add_argument("--target", type=int, default=80, 
                        help="Target coverage percentage (default: 80)")
    
    return parser.parse_args()

def print_header(title: str) -> None:
    """Print a formatted header."""
    width = 80
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * width}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title.center(width)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * width}{Colors.END}\n")

def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.BLUE}{'-' * len(title)}{Colors.END}\n")

def run_command(command: List[str], env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
    """Run a command and capture its output."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        universal_newlines=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

def run_test_command(pytest_args: List[str], env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
    """Run pytest with specified arguments."""
    command = [sys.executable, "-m", "pytest"] + pytest_args
    return run_command(command, env)

def get_test_paths(args: argparse.Namespace) -> List[str]:
    """Determine test paths based on command line arguments."""
    if args.path:
        return [args.path]
    
    if args.module:
        module_path = args.module.replace('.', '/')
        return [f"app/tests/{module_path}.py"]
    
    paths = []
    
    # Handle specific test groups
    if args.ml:
        paths.extend(TEST_GROUPS["ml"])
    if args.phi:
        paths.extend(TEST_GROUPS["phi"])
    if args.unit:
        paths.append("app/tests/unit/")
    if args.integration:
        paths.append("app/tests/integration/")
    if args.security:
        paths.append("app/tests/security/")
    if args.e2e:
        paths.append("app/tests/e2e/")
    
    # If no specific test group is selected, run all tests
    if not paths and (args.all or not any([
        args.unit, args.integration, args.security, args.e2e, 
        args.ml, args.phi, args.path, args.module
    ])):
        paths.append("app/tests/")
    
    return paths

def setup_test_environment(args: argparse.Namespace) -> Dict[str, str]:
    """Set up the test environment and return environment variables."""
    env = os.environ.copy()
    
    # Set environment variables for testing
    env["ENVIRONMENT"] = "test"
    
    # Database connection for testing
    if args.docker:
        env["TEST_DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@db-test:5432/novamind_test"
        env["TEST_REDIS_URL"] = "redis://redis-test:6379/0"
    else:
        env["TEST_DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:15432/novamind_test"
        env["TEST_REDIS_URL"] = "redis://localhost:16379/0"
    
    # Security and encryption keys for testing
    env["SECRET_KEY"] = "test-secret-key-for-pytest-runner-do-not-use-in-production"
    env["ENCRYPTION_KEY"] = "test-encryption-key-for-pytest-runner-not-for-prod"
    
    return env

def build_pytest_args(args: argparse.Namespace, test_paths: List[str]) -> List[str]:
    """Build pytest arguments based on command-line options."""
    pytest_args = []
    
    # Add test paths
    pytest_args.extend(test_paths)
    
    # Configure verbosity
    if args.verbose:
        pytest_args.append("-v")
    
    # Configure coverage
    if args.coverage:
        pytest_args.append("--cov=app")
        pytest_args.append("--cov-report=term")
        if args.html:
            pytest_args.append("--cov-report=html:coverage_html")
        if args.xml:
            pytest_args.append("--cov-report=xml:coverage.xml")
    
    # Configure test reports
    if args.report:
        os.makedirs(args.report_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{args.report_dir}/test_report_{timestamp}.xml"
        pytest_args.extend(["--junitxml", report_file])
    
    return pytest_args

def parse_coverage_report(stdout: str) -> Dict[str, float]:
    """Parse coverage percentages from pytest output."""
    coverage = {}
    
    if "TOTAL" not in stdout:
        return coverage
    
    # Capture lines after the TOTAL line
    lines = stdout.split("\n")
    total_line_index = None
    
    for i, line in enumerate(lines):
        if "TOTAL" in line:
            total_line_index = i
            break
    
    if total_line_index is None:
        return coverage
    
    # Parse the TOTAL line
    try:
        total_line = lines[total_line_index].strip()
        parts = [p for p in total_line.split() if p]
        if len(parts) >= 4:
            coverage["total"] = float(parts[-1].rstrip("%"))
    except (IndexError, ValueError):
        coverage["total"] = 0.0
    
    return coverage

def generate_summary(test_paths: List[str], exit_code: int, 
                    coverage: Dict[str, float], target: int, 
                    start_time: float, end_time: float) -> None:
    """Generate and print a test summary."""
    print_header("Test Summary")
    
    # Print test results
    test_result = "✅ PASSED" if exit_code == 0 else "❌ FAILED"
    print(f"Test Result: {Colors.GREEN if exit_code == 0 else Colors.RED}{test_result}{Colors.END}")
    
    # Print coverage information
    if "total" in coverage:
        coverage_color = (Colors.GREEN if coverage["total"] >= target else 
                         Colors.WARNING if coverage["total"] >= target * 0.8 else 
                         Colors.RED)
        print(f"Coverage: {coverage_color}{coverage['total']:.2f}%{Colors.END} (Target: {target}%)")
    
    # Print execution time
    execution_time = end_time - start_time
    print(f"Execution Time: {execution_time:.2f} seconds")
    
    # Print tested paths
    print("\nTested Paths:")
    for path in test_paths:
        print(f"  - {path}")
    
    # Print summary banner
    overall_status = "PASSED" if exit_code == 0 else "FAILED"
    print(f"\n{Colors.BOLD}Overall Status: {Colors.GREEN if exit_code == 0 else Colors.RED}{overall_status}{Colors.END}")

def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    # Time tracking
    start_time = time.time()
    
    # Determine test paths
    test_paths = get_test_paths(args)
    
    # Set up test environment
    env = setup_test_environment(args)
    
    # Build pytest arguments
    pytest_args = build_pytest_args(args, test_paths)
    
    # Print execution plan
    print_header("Novamind Test Runner")
    print(f"Executing Tests: {', '.join(test_paths)}")
    print(f"Command: {' '.join(['pytest'] + pytest_args)}")
    print(f"Environment: {'Docker' if args.docker else 'Local'}")
    
    # Run the tests
    print_section("Running Tests")
    exit_code, stdout, stderr = run_test_command(pytest_args, env)
    
    # Print output
    print(stdout)
    if stderr:
        print(f"{Colors.RED}Errors:{Colors.END}")
        print(stderr)
    
    # Parse coverage information
    coverage = {}
    if args.coverage:
        coverage = parse_coverage_report(stdout)
    
    # Print summary
    end_time = time.time()
    generate_summary(test_paths, exit_code, coverage, args.target, start_time, end_time)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())