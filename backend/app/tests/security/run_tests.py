#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NovaMind Digital Twin Security Test Runner

This script executes the comprehensive security test suite for the
NovaMind Digital Twin backend with HIPAA-compliant reporting.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add the root directory to Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
)


def run_quantum_security_tests():
    """
    Main function to run all security tests.
    This is designed to be run directly, not as a pytest test case.
    """
    test_runner = SecurityTestRunner()
    test_runner.run_all_tests()
    return test_runner.results

    class SecurityTestRunner:
    """Quantum-grade test collector and runner for NovaMind security tests."""

    def __init__(self, output_path: str = None):
        """Initialize test runner with output path.

        Args:
            output_path: Path to save test reports
            """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_path = output_path or os.path.join(
            self.base_dir, "test_results")

        # Ensure output directory exists
        os.makedirs(self.output_path, exist_ok=True)

        # Test categories in priority order
        self.test_categories = [
            {"name": "Core Encryption", "pattern": "test_ml_encryption.py"},
            {"name": "PHI Handling", "pattern": "test_address_helper.py"},
            {
                "name": "Enhanced Security",
                "pattern": "../unit/infrastructure/security/test_encryption_enhanced.py",
            },
            {"name": "JWT Authentication", "pattern": "test_jwt*.py"},
            {"name": "HIPAA Compliance", "pattern": "test_hipaa*.py"},
            {"name": "PHI Protection", "pattern": "test_phi*.py"},
            {"name": "Security Patterns", "pattern": "test_*security*.py"},
            {"name": "Audit Logging", "pattern": "test_audit*.py"},
            {"name": "API Security", "pattern": "test_api*.py"},
        ]

        # Test results collection
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
            },
            "categories": {},
        }

    def find_test_files(self, pattern: str) -> List[str]:
        """Find test files matching the pattern.

        Args:
            pattern: Glob pattern to match test files

            Returns:
            List of matching file paths
            """
        import glob

        # Handle both relative and absolute patterns
        if os.path.isabs(pattern):
            search_pattern = pattern
            else:
            search_pattern = os.path.join(self.base_dir, pattern)

            return glob.glob(search_pattern)

            def run_pytest(self, test_file: str) -> Dict[str, Any]:
        """Run pytest on a specific test file.

        Args:
            test_file: Path to test file

            Returns:
            Dictionary with test results
            """
        # Determine the pytest command for JSON output
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            test_file,
            "--json-report",
            "--no-header",
            "--no-summary",
        ]

        # Create a temporary directory for the JSON report
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Set the report path
            json_path = os.path.join(tmpdir, "report.json")
            cmd.extend(["--json-report-file", json_path])

            # Run pytest
            print(f"Running: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=False, capture_output=True)

                # Parse the JSON report
                with open(json_path, "r") as f:
                    results = json.load(f)

                    return results
                    except Exception as e:
                print(f"Error running test {test_file}: {str(e)}")
                return {
                    "summary": {
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "skipped": 0,
                        "errors": 1,
                    },
                    "tests": [],
                    "error": str(e),
                }

    def parse_test_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Parse pytest JSON report into a simplified format.

        Args:
            results: Pytest JSON report

            Returns:
            Simplified test results
            """
        # Extract summary statistics
        summary = {
            "total": results.get("summary", {}).get("total", 0),
            "passed": results.get("summary", {}).get("passed", 0),
            "failed": results.get("summary", {}).get("failed", 0),
            "skipped": results.get("summary", {}).get("skipped", 0),
            "errors": results.get("summary", {}).get("errors", 0),
        }

        # Extract individual test results
        tests = []
        for test_data in results.get("tests", []):
            test_result = {
                "name": test_data.get("name", ""),
                "outcome": test_data.get("outcome", ""),
                "duration": test_data.get("duration", 0),
                "message": test_data.get("call", {}).get("longrepr", ""),
            }
            tests.append(test_result)

        return {"summary": summary, "tests": tests}

    def run_category(self, category: Dict[str, str]) -> None:
        """Run tests for a specific category.

        Args:
            category: Dictionary with category name and file pattern
            """
        name = category["name"]
        pattern = category["pattern"]

        print("\n" + "=" * 60)
        print(f"RUNNING TESTS: {name}")
        print("=" * 60)

        # Find test files for this category
        test_files = self.find_test_files(pattern)

        # Initialize category results
        category_results = {
            "files_found": len(test_files),
            "files": [],
            "tests": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0},
        }

        # Run tests for each file
        for test_file in test_files:
            print(f"\nTesting {os.path.basename(test_file)}...")

            # Run the tests
            results = self.run_pytest(test_file)

            # Parse the results
            parsed_results = self.parse_test_results(results)

            # Store file results
            file_result = {
                "file": os.path.basename(test_file),
                "path": test_file,
                "summary": parsed_results["summary"],
                "tests": parsed_results["tests"],
            }
            category_results["files"].append(file_result)

            # Update category summary
            for key in category_results["tests"]:
                category_results["tests"][key] += parsed_results["summary"][key]

                # Print file summary
                print(
                    f"  Passed: {
                        parsed_results['summary']['passed']}/{
                        parsed_results['summary']['total']}")
            print(f"  Failed: {parsed_results['summary']['failed']}")
            print(f"  Errors: {parsed_results['summary']['errors']}")

        # Update overall summary
        for key in self.results["summary"]:
            self.results["summary"][key] += category_results["tests"][key]

            # Store category results
            self.results["categories"][name] = category_results

            # Print category summary
            print(f"\nSummary for {name}:")
            print(f"Files found: {category_results['files_found']}")
            print(
                f"Tests passed: {
                    category_results['tests']['passed']}/{
                    category_results['tests']['total']}")
        print(f"Tests failed: {category_results['tests']['failed']}")
        print(f"Tests with errors: {category_results['tests']['errors']}")

    def run_all_tests(self) -> None:
        """Run all test categories."""
        start_time = datetime.now()
        self.results["start_time"] = start_time.isoformat()

        # Run tests by category
        for category in self.test_categories:
            self.run_category(category)

            end_time = datetime.now()
            self.results["end_time"] = end_time.isoformat()
            self.results["duration_seconds"] = (
                end_time - start_time).total_seconds()

            # Output final summary
            print("\n" + "=" * 60)
            print("FINAL TEST SUMMARY")
            print("=" * 60)
            print(f"Total tests: {self.results['summary']['total']}")
            print(f"Tests passed: {self.results['summary']['passed']}")
            print(f"Tests failed: {self.results['summary']['failed']}")
            print(f"Tests skipped: {self.results['summary']['skipped']}")
            print(f"Tests with errors: {self.results['summary']['errors']}")
            print(f"Duration: {self.results['duration_seconds']:.2f} seconds")

            # Calculate success percentage
            if self.results["summary"]["total"] > 0:
            success_rate = (
                100
                * self.results["summary"]["passed"]
                / self.results["summary"]["total"]
            )
            self.results["success_rate"] = success_rate
            print(f"Success rate: {success_rate:.2f}%")

        # Save results to file
        report_filename = (
            f"security_test_report_{
                datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        report_path = os.path.join(self.output_path, report_filename)
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)

            print(f"\nDetailed report saved to: {report_path}")

            # Generate dashboard HTML if requested
            if os.environ.get("GENERATE_DASHBOARD", "true").lower() == "true":
            try:
                from app.tests.security.dashboard import generate_dashboard

                dashboard_path = os.path.join(
                    self.output_path, f"dashboard_{
                        datetime.now().strftime('%Y%m%d_%H%M%S')}.html", )
                generate_dashboard(self.results, dashboard_path)
                print(f"Dashboard generated at: {dashboard_path}")
            except ImportError:
                print("Dashboard generation module not available.")

                if __name__ == "__main__":
    run_quantum_security_tests()
