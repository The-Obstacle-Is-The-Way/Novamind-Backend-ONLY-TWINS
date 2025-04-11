#!/usr/bin/env python3
"""
Canonical Test Runner for Novamind Digital Twin

This script is the Single Source of Truth (SSOT) for running tests in the Novamind 
Digital Twin platform. It provides a standardized interface for test execution with
a dependency-based approach, running tests from most isolated to most integrated.

Usage:
    python run_tests.py --standalone      # Run only standalone tests
    python run_tests.py --venv            # Run standalone and venv tests
    python run_tests.py --integration     # Run all tests
    python run_tests.py --all             # Run all tests (same as --integration)
    python run_tests.py --security        # Run only security-marked tests
    python run_tests.py --coverage        # Generate coverage report
"""

import argparse
import os
import subprocess
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Define test levels with increasing dependency requirements
class TestLevel(Enum):
    STANDALONE = "standalone"
    VENV = "venv"
    INTEGRATION = "integration"
    SECURITY = "security"  # Orthogonal concern

# Define colors for output formatting
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestRunner:
    """
    Canonical test runner for the Novamind Digital Twin platform.
    
    This class implements the directory-based SSOT approach for running tests,
    organizing them by dependency level rather than by architecture layer.
    """
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[3]
        self.test_root = self.project_root / "app" / "tests"
        self.results: Dict[TestLevel, Dict[str, int]] = {}
        
    def run(self, args: argparse.Namespace) -> int:
        """
        Run the tests according to the specified arguments.
        
        Args:
            args: Command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        start_time = time.time()
        
        # Determine which test levels to run
        test_levels = self._get_test_levels(args)
        
        # Run the specified test levels
        exit_code = 0
        for level in test_levels:
            level_success = self._run_test_level(level, args)
            if not level_success:
                exit_code = 1
                # If progressive execution is enabled and a level fails, stop
                if args.progressive and not args.force_all:
                    print(f"{Colors.RED}Stopping progressive execution due to failures in {level.value} tests{Colors.ENDC}")
                    break
        
        # Generate coverage report if requested
        if args.coverage:
            self._generate_coverage_report()
        
        # Print summary
        self._print_summary(time.time() - start_time)
        
        return exit_code
    
    def _get_test_levels(self, args: argparse.Namespace) -> List[TestLevel]:
        """
        Determine which test levels to run based on the provided arguments.
        
        Args:
            args: Command-line arguments
            
        Returns:
            List of TestLevel enums to run
        """
        if args.security:
            # Security is an orthogonal concern, not a dependency level
            # We return all levels but will filter by marker
            return [TestLevel.STANDALONE, TestLevel.VENV, TestLevel.INTEGRATION]
        
        if args.all or args.integration:
            return [TestLevel.STANDALONE, TestLevel.VENV, TestLevel.INTEGRATION]
        
        if args.venv:
            return [TestLevel.STANDALONE, TestLevel.VENV]
        
        if args.standalone:
            return [TestLevel.STANDALONE]
        
        # Default to running all tests
        return [TestLevel.STANDALONE, TestLevel.VENV, TestLevel.INTEGRATION]
    
    def _run_test_level(self, level: TestLevel, args: argparse.Namespace) -> bool:
        """
        Run tests for a specific dependency level.
        
        Args:
            level: Test level to run
            args: Command-line arguments
            
        Returns:
            True if all tests passed, False otherwise
        """
        print(f"\n{Colors.HEADER}Running {level.value} tests...{Colors.ENDC}\n")
        
        # Build pytest command
        pytest_args = [
            "pytest",
            str(self.test_root / level.value),
            "-v",
        ]
        
        # Add markers if specified
        if args.security:
            pytest_args.extend(["-m", "security"])
        
        # Add coverage options if requested
        if args.coverage:
            pytest_args.extend([
                "--cov=app",
                f"--cov-report=term-missing",
                f"--cov-config={self.project_root / '.coveragerc'}"
            ])
        
        # Add output file option if specified
        if args.output:
            output_file = Path(args.output)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            pytest_args.extend([f"--junitxml={output_file}"])
        
        # Print the command being run
        command_str = " ".join(pytest_args)
        print(f"{Colors.BLUE}Running: {command_str}{Colors.ENDC}")
        
        # Run the tests
        try:
            result = subprocess.run(
                pytest_args,
                cwd=str(self.project_root),
                capture_output=not args.verbose,
                text=True,
                check=False  # Don't raise exception on test failure
            )
            
            # Store the results
            self.results[level] = {
                "exit_code": result.returncode,
                "command": command_str
            }
            
            # Print detailed output if requested or if tests failed
            if args.verbose or result.returncode != 0:
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(f"{Colors.RED}{result.stderr}{Colors.ENDC}")
            
            # Print status based on result
            if result.returncode == 0:
                print(f"{Colors.GREEN}✓ {level.value} tests passed{Colors.ENDC}")
                return True
            else:
                print(f"{Colors.RED}✗ {level.value} tests failed{Colors.ENDC}")
                return False
                
        except Exception as e:
            print(f"{Colors.RED}Error running {level.value} tests: {str(e)}{Colors.ENDC}")
            self.results[level] = {
                "exit_code": 1,
                "command": command_str,
                "error": str(e)
            }
            return False
    
    def _generate_coverage_report(self):
        """Generate HTML coverage report."""
        print(f"\n{Colors.HEADER}Generating coverage report...{Colors.ENDC}\n")
        
        coverage_cmd = [
            "coverage", "html",
            "-d", str(self.project_root / "coverage_html"),
            "--rcfile", str(self.project_root / ".coveragerc")
        ]
        
        try:
            subprocess.run(
                coverage_cmd,
                cwd=str(self.project_root),
                check=True,
                capture_output=True,
                text=True
            )
            print(f"{Colors.GREEN}Coverage report generated at {self.project_root / 'coverage_html'}{Colors.ENDC}")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Error generating coverage report: {e.stderr}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}Error generating coverage report: {str(e)}{Colors.ENDC}")
    
    def _print_summary(self, elapsed_time: float):
        """
        Print a summary of the test execution.
        
        Args:
            elapsed_time: Total elapsed time for test execution
        """
        print(f"\n{Colors.HEADER}Test Execution Summary{Colors.ENDC}")
        print(f"{Colors.BOLD}Total time: {elapsed_time:.2f} seconds{Colors.ENDC}")
        
        # Print results for each level
        all_passed = True
        for level, result in self.results.items():
            status = "✓ Passed" if result["exit_code"] == 0 else "✗ Failed"
            color = Colors.GREEN if result["exit_code"] == 0 else Colors.RED
            print(f"{color}{level.value}: {status}{Colors.ENDC}")
            all_passed = all_passed and result["exit_code"] == 0
        
        # Print overall status
        if all_passed:
            print(f"\n{Colors.GREEN}All tests passed!{Colors.ENDC}")
        else:
            print(f"\n{Colors.RED}Some tests failed.{Colors.ENDC}")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Novamind Digital Twin Test Runner")
    
    # Test selection options
    test_group = parser.add_argument_group("Test Selection")
    test_group.add_argument("--standalone", action="store_true", help="Run standalone tests only")
    test_group.add_argument("--venv", action="store_true", help="Run standalone and venv tests")
    test_group.add_argument("--integration", action="store_true", help="Run all tests including integration")
    test_group.add_argument("--all", action="store_true", help="Run all tests (same as --integration)")
    test_group.add_argument("--security", action="store_true", help="Run security tests")
    
    # Execution options
    exec_group = parser.add_argument_group("Execution Options")
    exec_group.add_argument("--progressive", action="store_true", help="Stop if a test level fails")
    exec_group.add_argument("--force-all", action="store_true", help="Run all specified tests even if earlier levels fail")
    exec_group.add_argument("--verbose", "-v", action="store_true", help="Show verbose test output")
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument("--coverage", action="store_true", help="Generate coverage report")
    output_group.add_argument("--output", "-o", help="Output file for test results (JUnit XML format)")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    runner = TestRunner()
    exit_code = runner.run(args)
    sys.exit(exit_code)