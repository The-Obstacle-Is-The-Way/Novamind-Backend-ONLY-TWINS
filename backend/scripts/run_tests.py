#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Runner for Novamind Digital Twin Platform

A unified test runner script that handles test suites, coverage reporting,
and provides detailed feedback. Supports running tests by suite or dependency level.

Usage:
    python -m backend.scripts.run_tests [options]

Options:
  Test Selection:
    --all               Run all tests (default: runs in dependency order: standalone -> venv -> db)
    --standalone        Run only standalone tests (marker: 'standalone')
    --venv              Run only venv-dependent tests (marker: 'venv_only')
    --db                Run only DB-dependent tests (marker: 'db_required')
    --unit              Run only tests under app/tests/unit/ (legacy)
    --integration       Run only tests under app/tests/integration/ (legacy)
    --security          Run only tests under app/tests/security/ (legacy)
    --ml-mock           Run only ML mock tests (under unit/core/services/ml) (legacy)
    --quick             Run a smaller subset of critical tests for quick feedback

  Reporting & Coverage:
    --coverage          Run with coverage reporting (default: False)
    --fail-under=N      Fail if coverage is under N percent (default: 80)
    --html              Generate HTML coverage report (default: False)
    --xml               Generate XML coverage report (default: False)
    --json              Generate JSON coverage report (default: False)
    --output=PATH       Path to write reports to (default: reports/) [Currently not used by coverage]

  Other:
    --verbose           Run with verbose output (default: False)
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
    """Test runner for all test suites following clean architecture."""
    
    def __init__(self, base_dir: Path) -> None:
        """Initialize the test runner.
        
        Args:
            base_dir: Base directory of the project
        """
        self.base_dir = base_dir
        self.app_dir = base_dir / "app"
        self.test_dir = self.app_dir / "tests"
        self.report_dir = base_dir / "reports"
        self.results: Dict[str, Any] = {}
        
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
        
        # Use the unified test structure under app/tests/unit
        test_paths = [str(self.test_dir / "unit")]
            
        success, results = self._run_pytest(
            test_paths=test_paths,
            coverage=coverage,
            verbose=verbose,
            fail_under=fail_under,
            html=html,
            xml=xml,
            json=json,
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
        
        # Use the unified test structure under app/tests/integration
        test_paths = [str(self.test_dir / "integration")]
            
        success, results = self._run_pytest(
            test_paths=test_paths,
            coverage=coverage,
            verbose=verbose,
            fail_under=fail_under,
            html=html,
            xml=xml,
            json=json,
        )
        
        self.results["integration"] = results
        return success
    
    def run_security_tests(self, coverage: bool = False, verbose: bool = False,
                          fail_under: int = 95, html: bool = False,
                          xml: bool = False, json: bool = False) -> bool:
        """Run security tests.
        
        Args:
            coverage: Whether to run with coverage (default: False)
            verbose: Whether to run with verbose output (default: False)
            fail_under: Fail if coverage is under this percentage (default: 95)
            html: Whether to generate HTML coverage report (default: False)
            xml: Whether to generate XML coverage report (default: False)
            json: Whether to generate JSON coverage report (default: False)
            
        Returns:
            True if tests passed, False otherwise
        """
        print("\n" + "="*80)
        print("Running Security Tests")
        print("="*80 + "\n")
        
        # Use the unified test structure under app/tests/security
        test_paths = [str(self.test_dir / "security")]
            
        success, results = self._run_pytest(
            test_paths=test_paths,
            coverage=coverage,
            verbose=verbose,
            fail_under=fail_under,
            html=html,
            xml=xml,
            json=json,
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
        
        # Use the unified test structure - ML mock tests are under unit/core/services/ml
        test_paths = [str(self.test_dir / "unit/core/services/ml")]
            
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

    def run_standalone_tests(self, coverage: bool = False, verbose: bool = False,
                             fail_under: int = 0, html: bool = False,
                             xml: bool = False, json: bool = False) -> bool:
        """Run standalone tests (marker: 'standalone')."""
        print("\n" + "="*80)
        print("Running Standalone Tests")
        print("="*80 + "\n")

        success, results = self._run_pytest(
            test_paths=[str(self.test_dir)],  # Run against all tests
            markers="standalone",
            coverage=coverage,
            verbose=verbose,
            fail_under=fail_under, # Typically don't fail coverage on subsets
            html=html,
            xml=xml,
            json=json,
        )

        self.results["standalone"] = results
        return success

    def run_venv_tests(self, coverage: bool = False, verbose: bool = False,
                       fail_under: int = 0, html: bool = False,
                       xml: bool = False, json: bool = False) -> bool:
        """Run venv-dependent tests (marker: 'venv_only')."""
        print("\n" + "="*80)
        print("Running VENV-Dependent Tests")
        print("="*80 + "\n")

        success, results = self._run_pytest(
            test_paths=[str(self.test_dir)], # Run against all tests
            markers="venv_only",
            coverage=coverage,
            verbose=verbose,
            fail_under=fail_under, # Typically don't fail coverage on subsets
            html=html,
            xml=xml,
            json=json,
        )

        self.results["venv"] = results
        return success

    def run_db_tests(self, coverage: bool = False, verbose: bool = False,
                     fail_under: int = 0, html: bool = False,
                     xml: bool = False, json: bool = False) -> bool:
        """Run DB-dependent tests (marker: 'db_required')."""
        print("\n" + "="*80)
        print("Running DB-Dependent Tests")
        print("="*80 + "\n")

        success, results = self._run_pytest(
            test_paths=[str(self.test_dir)], # Run against all tests
            markers="db_required",
            coverage=coverage,
            verbose=verbose,
            fail_under=fail_under, # Typically don't fail coverage on subsets
            html=html,
            xml=xml,
            json=json,
        )

        self.results["db"] = results
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
        
        # Use the most critical test paths for quick feedback
        ml_path = str(self.test_dir / "unit/core/services/ml")
        domain_path = str(self.test_dir / "unit/domain")
        phi_path = str(self.test_dir / "security/phi")
            
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "not slow",
            ml_path,      # ML service tests
            domain_path,  # Core domain tests
            phi_path,     # PHI protection tests
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
        
        # Generate combined coverage report if requested
        if coverage:
            print("\n" + "="*80)
            print("Generating Combined Coverage Report")
            print("="*80 + "\n")
            
            cmd = [
                sys.executable, "-m", "pytest",
                "--cov=app",
                str(self.test_dir),
            ]
            
            if html:
                cmd.append("--cov-report=html")
            if xml:
                cmd.append("--cov-report=xml")
            if json:
                cmd.append("--cov-report=json")
                
            if fail_under > 0:
                cmd.append(f"--cov-fail-under={fail_under}")
                
            # Always include terminal report
            cmd.append("--cov-report=term-missing")
            
            combined_result = self._run_command(cmd)
            if combined_result.returncode != 0 and fail_under > 0:
                failed_suites.add("Coverage")
                
            # Extract overall coverage
            coverage_pct = 0
            for line in combined_result.stdout.split("\n"):
                if "TOTAL" in line and "%" in line:
                    parts = line.split()
                    for part in parts:
                        if "%" in part:
                            try:
                                coverage_pct = float(part.strip('%'))
                            except:
                                pass
            
            print(f"\nOverall Coverage: {coverage_pct:.2f}%")
            if coverage_pct < fail_under:
                print(f"❌ Coverage is below the required {fail_under}%")
            else:
                print(f"✅ Coverage meets or exceeds the required {fail_under}%")
        
        # Print overall summary
        all_passed = len(failed_suites) == 0
        return all_passed
    
    def print_summary(self) -> None:
        """Print a summary of test results."""
        print("\n" + "="*80)
        print("Test Summary")
        print("="*80)
        
        # Print individual test suite results
        for suite, result in self.results.items():
            suite_name = suite.replace("_", " ").title()
            status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            print(f"{suite_name} Tests: {status}")
            
            # Print coverage if available
            if "coverage_pct" in result:
                print(f"  Coverage: {result['coverage_pct']:.2f}%")
        
        # Print overall status
        all_passed = all(result.get("success", False) for result in self.results.values())
        overall_status = "✅ PASSED" if all_passed else "❌ FAILED"
        print(f"\nOverall Status: {overall_status}")
        print("="*80)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run tests for the Novamind Backend", formatter_class=argparse.RawTextHelpFormatter)
    
    test_group = parser.add_argument_group('Test Selection')
    test_group.add_argument("--all", action="store_true", help="Run all tests (default: runs in dependency order)")
    test_group.add_argument("--standalone", action="store_true", help="Run only standalone tests (marker: 'standalone')")
    test_group.add_argument("--venv", action="store_true", help="Run only venv-dependent tests (marker: 'venv_only')")
    test_group.add_argument("--db", action="store_true", help="Run only DB-dependent tests (marker: 'db_required')")
    test_group.add_argument("--unit", action="store_true", help="Run only tests under app/tests/unit/ (legacy)")
    test_group.add_argument("--integration", action="store_true", help="Run only tests under app/tests/integration/ (legacy)")
    test_group.add_argument("--security", action="store_true", help="Run only tests under app/tests/security/ (legacy)")
    test_group.add_argument("--ml-mock", action="store_true", help="Run only ML mock tests (under unit/core/services/ml) (legacy)")
    test_group.add_argument("--quick", action="store_true", help="Run a smaller subset of critical tests")

    report_group = parser.add_argument_group('Reporting & Coverage')
    report_group.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    report_group.add_argument("--fail-under", type=int, default=80, help="Fail if coverage is under N percent (default: 80)")
    report_group.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    report_group.add_argument("--xml", action="store_true", help="Generate XML coverage report")
    report_group.add_argument("--json", action="store_true", help="Generate JSON coverage report")
    report_group.add_argument("--output", type=str, default="reports", help="Path to write reports to (default: reports/) [Currently not used by coverage]")

    other_group = parser.add_argument_group('Other')
    other_group.add_argument("--verbose", "-v", action="store_true", help="Run with verbose output")

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    # Get the project base directory
    base_dir = Path(__file__).parent.parent
    
    # Create the test runner
    test_runner = TestRunner(base_dir)
    
    # Determine which tests to run
    # Default to running all in dependency order if no specific type is selected
    run_all_ordered = args.all or not any([
        args.standalone, args.venv, args.db,
        args.unit, args.integration, args.security, args.ml_mock, args.quick
    ])

    overall_success = True

    if run_all_ordered:
        # Run all tests in dependency order
        print("\nRunning all tests in dependency order: standalone -> venv -> db")
        
        # Run Standalone
        standalone_success = test_runner.run_standalone_tests(
            coverage=args.coverage, verbose=args.verbose, fail_under=0, # Don't fail coverage on subsets
            html=args.html, xml=args.xml, json=args.json
        )
        if not standalone_success: overall_success = False

        # Run VENV (if standalone passed or we continue on failure)
        if overall_success: # Optional: Add a flag to continue on failure
            venv_success = test_runner.run_venv_tests(
                coverage=args.coverage, verbose=args.verbose, fail_under=0,
                html=args.html, xml=args.xml, json=args.json
            )
            if not venv_success: overall_success = False

        # Run DB (if previous passed or we continue on failure)
        if overall_success: # Optional: Add a flag to continue on failure
            db_success = test_runner.run_db_tests(
                coverage=args.coverage, verbose=args.verbose, fail_under=0,
                html=args.html, xml=args.xml, json=args.json
            )
            if not db_success: overall_success = False
            
        # Final combined coverage check if requested
        if args.coverage and overall_success:
             print("\n" + "="*80)
             print("Generating Combined Coverage Report")
             print("="*80 + "\n")
             # This re-runs pytest just for coverage reporting, which is inefficient.
             # A better approach would be to combine coverage data files.
             # For now, we'll just run it again on all tests.
             _, coverage_results = test_runner._run_pytest(
                 test_paths=[str(test_runner.test_dir)],
                 coverage=True, verbose=False, fail_under=args.fail_under,
                 html=args.html, xml=args.xml, json=args.json
             )
             if not coverage_results.get("success", False) and args.fail_under > 0:
                 print(f"❌ Coverage below threshold ({args.fail_under}%)")
                 overall_success = False
             else:
                 print(f"✅ Coverage meets threshold ({args.fail_under}%)")
                 
        success = overall_success # Final success status for --all ordered run

    elif args.standalone:
        success = test_runner.run_standalone_tests(
            coverage=args.coverage, verbose=args.verbose, fail_under=args.fail_under,
            html=args.html, xml=args.xml, json=args.json
        )
    elif args.venv:
        success = test_runner.run_venv_tests(
            coverage=args.coverage, verbose=args.verbose, fail_under=args.fail_under,
            html=args.html, xml=args.xml, json=args.json
        )
    elif args.db:
        success = test_runner.run_db_tests(
            coverage=args.coverage, verbose=args.verbose, fail_under=args.fail_under,
            html=args.html, xml=args.xml, json=args.json
        )
    # --- Legacy Test Suite Execution ---
    elif args.unit:
        success = test_runner.run_unit_tests(
            coverage=args.coverage, verbose=args.verbose, fail_under=args.fail_under,
            html=args.html, xml=args.xml, json=args.json
        )
    elif args.integration:
        success = test_runner.run_integration_tests(
            coverage=args.coverage, verbose=args.verbose, fail_under=args.fail_under,
            html=args.html, xml=args.xml, json=args.json
        )
    elif args.security:
        success = test_runner.run_security_tests(
            coverage=args.coverage, verbose=args.verbose, fail_under=args.fail_under,
            html=args.html, xml=args.xml, json=args.json
        )
    elif args.ml_mock:
        success = test_runner.run_ml_mock_tests(
            coverage=args.coverage, verbose=args.verbose
        )
    elif args.quick:
        success = test_runner.run_quick_tests(verbose=args.verbose)
    else:
        # Should not happen due to default logic, but handle defensively
        print("No specific test suite or dependency level selected.")
        success = True # Or False, depending on desired behavior

    # Print summary
    test_runner.print_summary()

    # Return exit code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())