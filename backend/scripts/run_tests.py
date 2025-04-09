#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Runner

A unified test runner script that handles all test suites, coverage reporting,
and provides detailed feedback on test results.

Usage:
    python -m backend.scripts.run_tests [options]

Options:
    --unit              Run only unit tests
    --integration       Run only integration tests
    --security          Run only security tests
    --ml-mock           Run only ML mock tests
    --coverage          Run with coverage reporting (default: False)
    --verbose           Run with verbose output (default: False)
    --quick             Run a smaller subset of tests for quick feedback
    --fail-under=N      Fail if coverage is under N percent (default: 80)
    --output=PATH       Path to write reports to (default: reports/)
    --html              Generate HTML coverage report (default: False)
    --xml               Generate XML coverage report (default: False)
    --json              Generate JSON coverage report (default: False)
"""

import argparse
import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set


class TestRunner:
    """Test runner for all test suites."""
    
    def __init__(self, base_dir: Path) -> None:
        """Initialize the test runner.
        
        Args:
            base_dir: Base directory of the project
        """
        self.base_dir = base_dir
        self.app_dir = base_dir / "app"
        self.test_dir = self.app_dir / "tests"
        self.report_dir = base_dir / "reports"
        self.test_structure = self._detect_test_structure()
        self.results: Dict[str, Any] = {}
        
    def _detect_test_structure(self) -> str:
        """Detect the test structure.
        
        Returns:
            A string indicating the test structure: 'app_tests' or 'standalone_tests'
        """
        if (self.app_dir / "tests").exists():
            return "app_tests"
        elif (self.base_dir / "tests").exists():
            self.test_dir = self.base_dir / "tests"
            return "standalone_tests"
        else:
            print("WARNING: No test directory found.")
            return "app_tests"  # Default to app_tests
    
    def _run_command(self, cmd: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
        """Run a command and return the result.
        
        Args:
            cmd: Command to run
            timeout: Timeout in seconds (default: 300)
            
        Returns:
            CompletedProcess object with return code, stdout, and stderr
        """
        print(f"Running command: {' '.join(cmd)}")
        
        # Always use the virtual environment python if available
        venv_python = Path(self.base_dir) / "venv" / "bin" / "python"
        venv_pytest = Path(self.base_dir) / "venv" / "bin" / "pytest"
        
        # If we're trying to run pytest and the venv has pytest, use that directly
        if venv_pytest.exists() and "-m" in cmd and "pytest" in cmd:
            # Find the index of pytest in the command
            pytest_index = cmd.index("pytest") if "pytest" in cmd else cmd.index("-m") + 1
            # Replace python -m pytest with direct venv pytest
            cmd = [str(venv_pytest)] + cmd[pytest_index+1:]
            print(f"Using virtual environment pytest directly: {cmd[0]}")
        # Otherwise use venv python if available
        elif venv_python.exists() and cmd[0].endswith("python"):
            cmd[0] = str(venv_python)
            print(f"Using virtual environment Python: {cmd[0]}")
        
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,  # 5 minute timeout by default
                check=False  # Don't raise exception on non-zero exit
            )
        except subprocess.TimeoutExpired:
            print(f"ERROR: Command timed out after {timeout} seconds")
            # Create a dummy result object with timeout information
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds"
            )
    
    def _run_pytest(self, test_paths: List[str], coverage: bool = False, 
                   verbose: bool = False, fail_under: int = 80,
                   html: bool = False, xml: bool = False, json: bool = False,
                   markers: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Run pytest on the specified test paths.
        
        Args:
            test_paths: List of test paths to run
            coverage: Whether to run with coverage (default: False)
            verbose: Whether to run with verbose output (default: False)
            fail_under: Fail if coverage is under this percentage (default: 80)
            html: Whether to generate HTML coverage report (default: False)
            xml: Whether to generate XML coverage report (default: False)
            json: Whether to generate JSON coverage report (default: False)
            markers: Optional pytest markers to filter tests (default: None)
            
        Returns:
            Tuple of (success: bool, results: Dict[str, Any])
        """
        cmd = [
            sys.executable, "-m", "pytest",
        ]
        
        if verbose:
            cmd.append("-v")
            # Only add --no-header if it's supported by the pytest version
            try:
                # Check if --help contains no-header
                help_cmd = [sys.executable, "-m", "pytest", "--help"]
                help_result = subprocess.run(help_cmd, capture_output=True, text=True)
                if "--no-header" in help_result.stdout:
                    cmd.append("--no-header")  # Remove pytest header for cleaner output
            except:
                pass  # Ignore if we can't check
        
        if markers:
            cmd.extend(["-m", markers])
        
        if coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=term-missing",
            ])
            
            if fail_under > 0:
                cmd.append(f"--cov-fail-under={fail_under}")
            
            if html:
                cmd.append("--cov-report=html")
            
            if xml:
                cmd.append("--cov-report=xml")
            
            if json:
                cmd.append("--cov-report=json")
        
        # Add test paths
        cmd.extend(test_paths)
        
        # Run pytest
        start_time = time.time()
        result = self._run_command(cmd)
        elapsed_time = time.time() - start_time
        
        success = result.returncode == 0
        
        if success:
            print("\n✅ Tests passed!")
        else:
            print("\n❌ Tests failed!")
            # Print the error output for better visibility
            if result.stderr:
                print(f"\nError output:")
                print(result.stderr)
        
        output = result.stdout
        error = result.stderr
        
        # Extract coverage from output
        coverage_pct = 0
        if coverage:
            for line in output.split("\n"):
                if "TOTAL" in line and "%" in line:
                    parts = line.split()
                    for part in parts:
                        if "%" in part:
                            try:
                                coverage_pct = float(part.strip('%'))
                            except:
                                pass
        
        return success, {
            "success": success,
            "return_code": result.returncode,
            "output": output,
            "error": error,
            "elapsed_time": elapsed_time,
            "coverage_pct": coverage_pct,
        }
    
    def run_unit_tests(self, coverage: bool = False, verbose: bool = False, 
                       fail_under: int = 80, html: bool = False, 
                       xml: bool = False, json: bool = False) -> bool:
        """Run unit tests.
        
        Args:
            coverage: Whether to run with coverage (default: False)
            verbose: Whether to run with verbose output (default: False)
            fail_under: Fail if coverage is under this percentage (default: 80)
            html: Whether to generate HTML coverage report (default: False)
            xml: Whether to generate XML coverage report (default: False)
            json: Whether to generate JSON coverage report (default: False)
            
        Returns:
            True if tests passed, False otherwise
        """
        print("\n" + "="*80)
        print("Running Unit Tests")
        print("="*80 + "\n")
        
        # Different paths based on test structure
        if self.test_structure == "app_tests":
            test_paths = [str(self.test_dir / "unit")]
            if not Path(test_paths[0]).exists():
                # Fall back to domain & core tests
                test_paths = [
                    str(self.test_dir / "domain"),
                    str(self.test_dir / "core"),
                ]
        else:
            test_paths = [str(self.test_dir / "unit")]
            
        success, results = self._run_pytest(
            test_paths=test_paths,
            coverage=coverage,
            verbose=verbose,
            fail_under=fail_under,
            html=html,
            xml=xml,
            json=json,
            markers="not integration and not security",
        )
        
        self.results["unit"] = results
        return success
    
    def run_integration_tests(self, coverage: bool = False, verbose: bool = False,
                             fail_under: int = 80, html: bool = False,
                             xml: bool = False, json: bool = False) -> bool:
        """Run integration tests.
        
        Args:
            coverage: Whether to run with coverage (default: False)
            verbose: Whether to run with verbose output (default: False)
            fail_under: Fail if coverage is under this percentage (default: 80)
            html: Whether to generate HTML coverage report (default: False)
            xml: Whether to generate XML coverage report (default: False)
            json: Whether to generate JSON coverage report (default: False)
            
        Returns:
            True if tests passed, False otherwise
        """
        print("\n" + "="*80)
        print("Running Integration Tests")
        print("="*80 + "\n")
        
        # Different paths based on test structure
        if self.test_structure == "app_tests":
            test_paths = [str(self.test_dir / "integration")]
        else:
            test_paths = [str(self.test_dir / "integration")]
            
        success, results = self._run_pytest(
            test_paths=test_paths,
            coverage=coverage,
            verbose=verbose,
            fail_under=fail_under,
            html=html,
            xml=xml,
            json=json,
            markers="integration",
        )
        
        self.results["integration"] = results
        return success
    
    def run_security_tests(self, coverage: bool = False, verbose: bool = False,
                          fail_under: int = 80, html: bool = False,
                          xml: bool = False, json: bool = False) -> bool:
        """Run security tests.
        
        Args:
            coverage: Whether to run with coverage (default: False)
            verbose: Whether to run with verbose output (default: False)
            fail_under: Fail if coverage is under this percentage (default: 80)
            html: Whether to generate HTML coverage report (default: False)
            xml: Whether to generate XML coverage report (default: False)
            json: Whether to generate JSON coverage report (default: False)
            
        Returns:
            True if tests passed, False otherwise
        """
        print("\n" + "="*80)
        print("Running Security Tests")
        print("="*80 + "\n")
        
        # Different paths based on test structure
        if self.test_structure == "app_tests":
            test_paths = [str(self.test_dir / "security")]
        else:
            test_paths = [str(self.test_dir / "security")]
            
        success, results = self._run_pytest(
            test_paths=test_paths,
            coverage=coverage,
            verbose=verbose,
            fail_under=fail_under,
            html=html,
            xml=xml,
            json=json,
            markers="security",
        )
        
        self.results["security"] = results
        return success
    
    def run_ml_mock_tests(self, coverage: bool = False, verbose: bool = False) -> bool:
        """Run ML mock tests.
        
        Args:
            coverage: Whether to run with coverage (default: False)
            verbose: Whether to run with verbose output (default: False)
            
        Returns:
            True if tests passed, False otherwise
        """
        print("\n" + "="*80)
        print("Running ML Mock Tests")
        print("="*80 + "\n")
        
        # Different paths based on test structure
        if self.test_structure == "app_tests":
            test_paths = [str(self.test_dir / "core/services/ml")]
            # Make sure the path exists
            if not Path(test_paths[0]).exists():
                print(f"WARNING: ML mock test path {test_paths[0]} does not exist")
                # Try alternative paths
                alternative_path = str(self.app_dir / "tests/core/services/ml")
                if Path(alternative_path).exists():
                    test_paths = [alternative_path]
                    print(f"Using alternative ML mock test path: {alternative_path}")
        else:
            test_paths = [str(self.test_dir / "core/services/ml")]
            
        success, results = self._run_pytest(
            test_paths=test_paths,
            coverage=coverage,
            verbose=verbose,
            # Lower coverage threshold for ML mock tests
            fail_under=0,  # Don't fail on coverage for ML mocks
            html=False,
            xml=False,
            json=False,
        )
        
        # Extract coverage percentage for ML mock tests
        if coverage:
            coverage_pct = 0
            for line in results["output"].split("\n"):
                if "TOTAL" in line and "%" in line:
                    parts = line.split()
                    for part in parts:
                        if "%" in part:
                            try:
                                coverage_pct = float(part.strip('%'))
                            except:
                                pass
            
            print(f"\nML Mock Tests Coverage: {coverage_pct:.2f}%")
            results["coverage_pct"] = coverage_pct
        
        self.results["ml_mock"] = results
        return success
    
    def run_quick_tests(self, verbose: bool = False) -> bool:
        """Run a subset of tests for quick feedback.
        
        Args:
            verbose: Whether to run with verbose output (default: False)
            
        Returns:
            True if tests passed, False otherwise
        """
        print("\n" + "="*80)
        print("Running Quick Tests")
        print("="*80 + "\n")
        
        # Different paths based on test structure
        if self.test_structure == "app_tests":
            ml_path = str(self.test_dir / "core/services/ml")
            domain_path = str(self.test_dir / "domain")
        else:
            ml_path = str(self.test_dir / "unit/core/services/ml")
            domain_path = str(self.test_dir / "unit/domain")
            
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "not slow",
            ml_path,  # ML service tests
            domain_path,  # Core domain tests
        ]
        
        if verbose:
            cmd.append("-v")
        
        # Run pytest
        result = self._run_command(cmd)
        success = result.returncode == 0
        
        if success:
            print("\n✅ Quick tests passed!")
        else:
            print("\n❌ Quick tests failed!")
        
        self.results["quick"] = {
            "success": success,
            "return_code": result.returncode,
            "output": result.stdout,
            "error": result.stderr,
        }
        
        return success
    
    def run_all_tests(self, coverage: bool = False, verbose: bool = False,
                     fail_under: int = 80, html: bool = False,
                     xml: bool = False, json: bool = False) -> bool:
        """Run all tests.
        
        Args:
            coverage: Whether to run with coverage (default: False)
            verbose: Whether to run with verbose output (default: False)
            fail_under: Fail if coverage is under this percentage (default: 80)
            html: Whether to generate HTML coverage report (default: False)
            xml: Whether to generate XML coverage report (default: False)
            json: Whether to generate JSON coverage report (default: False)
            
        Returns:
            True if all tests passed, False otherwise
        """
        # Track which test suites failed
        failed_suites = set()
        
        # Run unit tests
        unit_success = self.run_unit_tests(
            coverage=coverage,
            verbose=verbose,
            fail_under=0,  # Don't fail on coverage for individual suites
            html=False,
            xml=False,
            json=False,
        )
        if not unit_success:
            failed_suites.add("Unit Tests")
        
        # Run integration tests
        integration_success = self.run_integration_tests(
            coverage=coverage,
            verbose=verbose,
            fail_under=0,  # Don't fail on coverage for individual suites
            html=False,
            xml=False,
            json=False,
        )
        if not integration_success:
            failed_suites.add("Integration Tests")
        
        # Run security tests
        security_success = self.run_security_tests(
            coverage=coverage,
            verbose=verbose,
            fail_under=0,  # Don't fail on coverage for individual suites
            html=False,
            xml=False,
            json=False,
        )
        if not security_success:
            failed_suites.add("Security Tests")
        
        # Run ML mock tests
        ml_mock_success = self.run_ml_mock_tests(
            coverage=coverage,
            verbose=verbose,
        )
        if not ml_mock_success:
            failed_suites.add("ML Mock Tests")
        
        # Generate coverage report
        if coverage:
            print("\n" + "="*80)
            print("Running Coverage Report")
            print("="*80 + "\n")
            
            # Different paths based on test structure
            if self.test_structure == "app_tests":
                test_paths = [str(self.test_dir)]
            else:
                test_paths = [str(self.test_dir)]
                
            cmd = [
                sys.executable, "-m", "pytest",
                "--cov=app",
                "--cov-report=term-missing",
            ]
            
            if fail_under > 0:
                cmd.append(f"--cov-fail-under={fail_under}")
            
            if html:
                cmd.append("--cov-report=html")
            
            if xml:
                cmd.append("--cov-report=xml")
            
            if json:
                cmd.append("--cov-report=json")
            
            if verbose:
                cmd.append("-v")
            
            # Add test paths
            cmd.extend(test_paths)
            
            # Run pytest with combined coverage
            result = self._run_command(cmd)
            coverage_success = result.returncode == 0
            
            if not coverage_success:
                failed_suites.add("Coverage")
            
            # Extract coverage percentage from output
            coverage_pct = 0
            for line in result.stdout.split("\n"):
                if "TOTAL" in line and "%" in line:
                    parts = line.split()
                    for part in parts:
                        if "%" in part:
                            try:
                                coverage_pct = float(part.strip('%'))
                            except:
                                pass
            
            print(f"\nCoverage: {coverage_pct:.2f}%")
            
            self.results["coverage"] = {
                "success": coverage_success,
                "return_code": result.returncode,
                "output": result.stdout,
                "error": result.stderr,
                "coverage_pct": coverage_pct,
            }
        
        # Return True if all tests passed and coverage meets threshold
        return len(failed_suites) == 0
    
    def print_summary(self) -> None:
        """Print a summary of test results."""
        print("\n" + "="*80)
        print("Test Summary")
        print("="*80)
        
        overall_status = "✅ PASSED" if all(r.get("success", False) for r in self.results.values()) else "❌ FAILED"
        
        for suite, results in self.results.items():
            if suite == "unit":
                print(f"Unit Tests: {'✅ PASSED' if results['success'] else '❌ FAILED'}")
            elif suite == "integration":
                print(f"Integration Tests: {'✅ PASSED' if results['success'] else '❌ FAILED'}")
            elif suite == "security":
                print(f"Security Tests: {'✅ PASSED' if results['success'] else '❌ FAILED'}")
            elif suite == "ml_mock":
                print(f"Ml_mock Tests: {'✅ PASSED' if results['success'] else '❌ FAILED'}")
            elif suite == "coverage":
                coverage_pct = results.get("coverage_pct", 0)
                status = "✅ PASSED" if results["success"] else "❌ FAILED"
                print(f"Coverage: {status} (coverage: {coverage_pct:.1f}%)")
        
        print(f"\nOverall Status: {overall_status}")
        print("="*80 + "\n")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run tests with various options.")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--ml-mock", action="store_true", help="Run ML mock tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--verbose", action="store_true", help="Run with verbose output")
    parser.add_argument("--quick", action="store_true", help="Run a smaller subset of tests for quick feedback")
    parser.add_argument("--fail-under", type=int, default=80, help="Fail if coverage is under N percent")
    parser.add_argument("--output", type=str, default="reports/", help="Path to write reports to")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--xml", action="store_true", help="Generate XML coverage report")
    parser.add_argument("--json", action="store_true", help="Generate JSON coverage report")
    
    return parser.parse_args()


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 on success, 1 on failure)
    """
    args = parse_args()
    
    # Get the base directory (parent of the script directory)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Initialize the test runner
    test_runner = TestRunner(base_dir)
    
    # If no test suites are specified, run all tests
    run_all = not (args.unit or args.integration or args.security or args.ml_mock or args.quick)
    
    success = True
    
    if run_all:
        success = test_runner.run_all_tests(
            coverage=args.coverage,
            verbose=args.verbose,
            fail_under=args.fail_under,
            html=args.html,
            xml=args.xml,
            json=args.json,
        )
    else:
        # Run specified test suites
        if args.unit:
            success = test_runner.run_unit_tests(
                coverage=args.coverage,
                verbose=args.verbose,
                fail_under=args.fail_under,
                html=args.html,
                xml=args.xml,
                json=args.json,
            ) and success
        
        if args.integration:
            success = test_runner.run_integration_tests(
                coverage=args.coverage,
                verbose=args.verbose,
                fail_under=args.fail_under,
                html=args.html,
                xml=args.xml,
                json=args.json,
            ) and success
        
        if args.security:
            success = test_runner.run_security_tests(
                coverage=args.coverage,
                verbose=args.verbose,
                fail_under=args.fail_under,
                html=args.html,
                xml=args.xml,
                json=args.json,
            ) and success
        
        if args.ml_mock:
            success = test_runner.run_ml_mock_tests(
                coverage=args.coverage,
                verbose=args.verbose,
            ) and success
        
        if args.quick:
            success = test_runner.run_quick_tests(
                verbose=args.verbose,
            ) and success
    
    # Print summary
    test_runner.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())