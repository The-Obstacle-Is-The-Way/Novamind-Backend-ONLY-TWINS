#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency-Based Test Runner for Novamind Digital Twin Backend

This script runs tests in optimized order based on their dependency level:
1. Standalone tests (no dependencies beyond Python)
2. VENV-only tests (require packages but no external services)
3. DB-required tests (require database or other external services)

Usage:
    python -m scripts.run_dependency_tests [options] [test_path]

Options:
    --category CATEGORY   Run tests of a specific category: 'standalone', 'venv_only', 'db_required', or 'all'
    --verbose             Show detailed output
    --report              Generate a report of test distribution
    --coverage            Generate coverage report
    --junit               Generate JUnit XML report
    --help                Show this help message
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any


# ANSI colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    RESET = '\033[0m'


class TestCategory(str, Enum):
    STANDALONE = "standalone"
    VENV_ONLY = "venv_only"
    DB_REQUIRED = "db_required"
    ALL = "all"


@dataclass
class TestConfiguration:
    """Configuration for a test run"""
    category: TestCategory
    verbose: bool
    report: bool
    coverage: bool
    junit: bool
    test_path: Optional[str]


@dataclass
class TestResult:
    """Results from a test run"""
    category: TestCategory
    success: bool
    duration: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    coverage_percent: Optional[float] = None
    output: Optional[str] = None


class DependencyTestRunner:
    """
    Test runner that executes tests based on their dependency level.
    """

    def __init__(self, project_root: Path):
        """
        Initialize the test runner.
        
        Args:
            project_root: Path to the project root
        """
        self.project_root = project_root
        self.test_dir = project_root / "app" / "tests"
        self.results_dir = project_root / "test-results"
        self.coverage_dir = project_root / "coverage_html"
        
        # Ensure directories exist
        self.results_dir.mkdir(exist_ok=True)
        
        # Environment setup
        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = str(project_root)
        self.env["TESTING"] = "1"

    def find_tests_by_marker(self, marker: str) -> List[Path]:
        """
        Find all test files with a specific marker.
        
        Args:
            marker: Pytest marker to search for
            
        Returns:
            List of paths to test files with the marker
        """
        # Use pytest to collect tests with the marker
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-m", marker, str(self.test_dir)],
                capture_output=True,
                text=True,
                env=self.env,
            )
            
            # Extract test file paths from the output
            test_files = set()
            for line in result.stdout.splitlines():
                if "<Module " in line:
                    # Extract the file path from the module collection output
                    match = re.search(r"<Module\s+'([^']+)'>", line)
                    if match:
                        test_files.add(Path(match.group(1)))
            
            return list(test_files)
            
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}Error collecting tests with marker: {marker}{Colors.RESET}")
            return []

    def find_tests_by_directory(self, directory: str) -> List[Path]:
        """
        Find all test files in a specific directory.
        
        Args:
            directory: Directory to search in
            
        Returns:
            List of paths to test files
        """
        directory_path = self.test_dir / directory
        if not directory_path.exists():
            return []
            
        test_files = []
        for file in directory_path.glob("**/*.py"):
            if file.name.startswith("test_") and file.is_file():
                test_files.append(file)
                
        return test_files

    def run_tests(self, configuration: TestConfiguration) -> TestResult:
        """
        Run tests based on the provided configuration.
        
        Args:
            configuration: Test configuration
            
        Returns:
            Test results
        """
        category = configuration.category
        
        # Determine test files to run
        test_files = []
        if configuration.test_path:
            test_path = Path(configuration.test_path)
            if test_path.exists():
                test_files = [test_path]
            else:
                print(f"{Colors.RED}Test path not found: {test_path}{Colors.RESET}")
                return TestResult(
                    category=category,
                    success=False,
                    duration=0,
                    total_tests=0,
                    passed_tests=0,
                    failed_tests=0,
                    error_tests=0,
                    skipped_tests=0,
                    output="Test path not found"
                )
        elif category == TestCategory.STANDALONE:
            test_files = self.find_tests_by_directory("standalone")
            if not test_files:
                # Fallback to marker-based selection
                test_files = self.find_tests_by_marker("standalone")
        elif category == TestCategory.VENV_ONLY:
            test_files = self.find_tests_by_directory("venv_only")
            if not test_files:
                # Fallback to marker-based selection
                test_files = self.find_tests_by_marker("venv_only")
        elif category == TestCategory.DB_REQUIRED:
            # DB-required tests are typically not in a specific directory
            test_files = self.find_tests_by_marker("db_required")
        elif category == TestCategory.ALL:
            # For ALL category, we need to run pytest on the entire test directory
            test_files = [self.test_dir]
            
        if not test_files:
            print(f"{Colors.YELLOW}No tests found for category: {category}{Colors.RESET}")
            return TestResult(
                category=category,
                success=True,
                duration=0,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                error_tests=0,
                skipped_tests=0,
                output="No tests found"
            )
            
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add test paths
        for test_file in test_files:
            cmd.append(str(test_file))
            
        # Add options
        if configuration.verbose:
            cmd.append("-v")
            
        if configuration.junit:
            junit_path = self.results_dir / f"{category}-results.xml"
            cmd.extend(["--junitxml", str(junit_path)])
            
        if configuration.coverage:
            cmd.extend([
                "--cov=app",
                f"--cov-report=html:{self.coverage_dir}",
                f"--cov-report=xml:{self.results_dir}/{category}-coverage.xml",
                "--cov-report=term"
            ])
            
        if category != TestCategory.ALL:
            # For specific categories, add the marker filter
            cmd.extend(["-m", category])
            
        # Run the tests
        print(f"\n{Colors.BLUE}Running {category} tests...{Colors.RESET}")
        print(f"{Colors.CYAN}Command: {' '.join(cmd)}{Colors.RESET}\n")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=self.env,
            )
            output = result.stdout + result.stderr
            success = result.returncode == 0
        except Exception as e:
            output = str(e)
            success = False
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Parse test summary
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        skipped_tests = 0
        
        summary_match = re.search(r"=+ (\d+) passed, (\d+) skipped, (\d+) failed, (\d+) error", output)
        if summary_match:
            passed_tests = int(summary_match.group(1))
            skipped_tests = int(summary_match.group(2))
            failed_tests = int(summary_match.group(3))
            error_tests = int(summary_match.group(4))
            total_tests = passed_tests + skipped_tests + failed_tests + error_tests
            
        # Parse coverage
        coverage_percent = None
        coverage_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        if coverage_match:
            coverage_percent = float(coverage_match.group(1))
            
        # Print summary
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if success else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"\n{Colors.BLUE}Test Summary for {category}:{Colors.RESET}")
        print(f"Status: {status}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors: {error_tests}")
        print(f"Skipped: {skipped_tests}")
        
        if coverage_percent is not None:
            print(f"Coverage: {coverage_percent:.1f}%")
            
        # Print detailed output if verbose
        if configuration.verbose:
            print(f"\n{Colors.CYAN}Test Output:{Colors.RESET}")
            print(output)
            
        # Return results
        return TestResult(
            category=category,
            success=success,
            duration=duration,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            error_tests=error_tests,
            skipped_tests=skipped_tests,
            coverage_percent=coverage_percent,
            output=output if configuration.verbose else None
        )

    def run_all_tests(self, configuration: TestConfiguration) -> Dict[TestCategory, TestResult]:
        """
        Run all tests in dependency order.
        
        Args:
            configuration: Base test configuration
            
        Returns:
            Dictionary of test results by category
        """
        results = {}
        
        # Always run in dependency order
        categories = [
            TestCategory.STANDALONE,
            TestCategory.VENV_ONLY,
            TestCategory.DB_REQUIRED
        ]
        
        # If a specific category is requested, only run that one
        if configuration.category != TestCategory.ALL:
            categories = [configuration.category]
            
        # Run tests for each category
        for category in categories:
            # Update configuration for this category
            category_config = TestConfiguration(
                category=category,
                verbose=configuration.verbose,
                report=configuration.report,
                coverage=configuration.coverage,
                junit=configuration.junit,
                test_path=configuration.test_path
            )
            
            # Run tests
            result = self.run_tests(category_config)
            results[category] = result
            
            # Stop if tests fail and this isn't the last category
            if not result.success and category != categories[-1]:
                print(f"\n{Colors.RED}Tests failed for {category}. Stopping test run.{Colors.RESET}")
                break
                
        return results

    def generate_report(self, results: Dict[TestCategory, TestResult]) -> Dict[str, Any]:
        """
        Generate a report based on test results.
        
        Args:
            results: Test results by category
            
        Returns:
            Report dictionary
        """
        total_duration = sum(result.duration for result in results.values())
        total_tests = sum(result.total_tests for result in results.values())
        total_passed = sum(result.passed_tests for result in results.values())
        total_failed = sum(result.failed_tests for result in results.values())
        total_errors = sum(result.error_tests for result in results.values())
        total_skipped = sum(result.skipped_tests for result in results.values())
        
        # Calculate overall success
        overall_success = all(result.success for result in results.values())
        
        # Calculate overall coverage if any
        coverage_values = [result.coverage_percent for result in results.values() 
                        if result.coverage_percent is not None]
        overall_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else None
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_success": overall_success,
            "total_duration": total_duration,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_errors": total_errors,
            "total_skipped": total_skipped,
            "overall_coverage": overall_coverage,
            "categories": {}
        }
        
        for category, result in results.items():
            report["categories"][category] = {
                "success": result.success,
                "duration": result.duration,
                "total_tests": result.total_tests,
                "passed_tests": result.passed_tests,
                "failed_tests": result.failed_tests,
                "error_tests": result.error_tests,
                "skipped_tests": result.skipped_tests,
                "coverage_percent": result.coverage_percent
            }
            
        return report

    def save_report(self, report: Dict[str, Any]) -> None:
        """
        Save a report to a file.
        
        Args:
            report: Report dictionary
        """
        report_path = self.results_dir / "test-report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"\n{Colors.GREEN}Test report saved to: {report_path}{Colors.RESET}")

    def print_report(self, report: Dict[str, Any]) -> None:
        """
        Print a report to the console.
        
        Args:
            report: Report dictionary
        """
        print(f"\n{Colors.BLUE}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BLUE}TEST EXECUTION SUMMARY{Colors.RESET}")
        print(f"{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")
        
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if report["overall_success"] else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"Overall Status: {status}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Total Duration: {report['total_duration']:.2f} seconds")
        print(f"Total Tests: {report['total_tests']}")
        print(f"Passed: {report['total_passed']}")
        print(f"Failed: {report['total_failed']}")
        print(f"Errors: {report['total_errors']}")
        print(f"Skipped: {report['total_skipped']}")
        
        if report["overall_coverage"] is not None:
            print(f"Overall Coverage: {report['overall_coverage']:.1f}%")
            
        print(f"\n{Colors.BLUE}Results by Category:{Colors.RESET}")
        for category, result in report["categories"].items():
            status = f"{Colors.GREEN}PASSED{Colors.RESET}" if result["success"] else f"{Colors.RED}FAILED{Colors.RESET}"
            print(f"  {category}: {status}")
            print(f"    Duration: {result['duration']:.2f} seconds")
            print(f"    Tests: {result['total_tests']}")
            print(f"    Passed: {result['passed_tests']}")
            print(f"    Failed: {result['failed_tests']}")
            print(f"    Errors: {result['error_tests']}")
            print(f"    Skipped: {result['skipped_tests']}")
            
            if result["coverage_percent"] is not None:
                print(f"    Coverage: {result['coverage_percent']:.1f}%")
                
            print()


def parse_args() -> TestConfiguration:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run tests based on dependency level")
    parser.add_argument(
        "--category",
        type=str,
        choices=[cat.value for cat in TestCategory],
        default=TestCategory.ALL.value,
        help="Test category to run (default: all)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a report of test distribution"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--junit",
        action="store_true",
        help="Generate JUnit XML report"
    )
    parser.add_argument(
        "test_path",
        nargs="?",
        default=None,
        help="Path to specific test file or directory"
    )
    
    args = parser.parse_args()
    
    return TestConfiguration(
        category=TestCategory(args.category),
        verbose=args.verbose,
        report=args.report,
        coverage=args.coverage,
        junit=args.junit,
        test_path=args.test_path
    )


def main() -> int:
    """Main entry point."""
    # Parse arguments
    configuration = parse_args()
    
    # Find the project root
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent  # Assuming this script is in the scripts directory
    
    # Print banner
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BLUE}NOVAMIND DIGITAL TWIN BACKEND - DEPENDENCY-BASED TEST RUNNER{Colors.RESET}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")
    
    # Create runner
    runner = DependencyTestRunner(project_root)
    
    # Run tests
    results = runner.run_all_tests(configuration)
    
    # Generate report if requested
    if configuration.report:
        report = runner.generate_report(results)
        runner.print_report(report)
        runner.save_report(report)
        
    # Determine overall success
    overall_success = all(result.success for result in results.values())
    
    # Print final message
    if overall_success:
        print(f"\n{Colors.GREEN}All tests completed successfully!{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}Some tests failed. See above for details.{Colors.RESET}")
        
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())