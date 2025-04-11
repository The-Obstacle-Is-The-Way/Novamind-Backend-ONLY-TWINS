#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency-Based Test Runner for Novamind Digital Twin Backend

This script runs tests based on their dependency level (standalone, venv, db)
and can generate reports on test dependencies.

Usage:
    python run_dependency_tests.py --level standalone
    python run_dependency_tests.py --level venv
    python run_dependency_tests.py --level db
    python run_dependency_tests.py --report
"""

import os
import re
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
import xml.etree.ElementTree as ET

# Path to the app directory
BACKEND_DIR = Path(__file__).parent.parent
TESTS_DIR = BACKEND_DIR / "app" / "tests"
RESULTS_DIR = BACKEND_DIR / "test-results"

# Dependency levels
DEPENDENCY_LEVELS = {
    "standalone": {
        "marker": "standalone",
        "description": "No dependencies beyond Python itself"
    },
    "venv": {
        "marker": "venv_only",
        "description": "Requires Python packages but no external services"
    },
    "db": {
        "marker": "db_required",
        "description": "Requires database connections"
    },
    "network": {
        "marker": "network",
        "description": "Requires network connections"
    }
}

def run_tests(level: str, args: List[str]) -> Tuple[int, str]:
    """Run tests for a specific dependency level."""
    marker = DEPENDENCY_LEVELS.get(level, {}).get("marker", level)
    
    # Create results directory if it doesn't exist
    RESULTS_DIR.mkdir(exist_ok=True)
    
    # Build the pytest command
    cmd = [
        "python", "-m", "pytest",
        "-m", marker,
        f"--junitxml={RESULTS_DIR}/{level}-results.xml"
    ]
    
    # Add any additional arguments
    cmd.extend(args)
    
    # Run pytest
    print(f"Running {level} tests...")
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BACKEND_DIR))
    duration = time.time() - start_time
    
    return result.returncode, result.stdout + result.stderr, duration

def count_tests_by_marker() -> Dict[str, int]:
    """Count tests by marker using pytest."""
    result = {}
    total_tests = 0
    
    # Run pytest with --collect-only to get all tests
    cmd = ["python", "-m", "pytest", "--collect-only", "-v"]
    process = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BACKEND_DIR))
    
    if process.returncode != 0:
        print("Error collecting tests:", process.stderr)
        return result
    
    # Count total tests
    all_tests = re.findall(r"<([\w\.]+) .*>", process.stdout)
    total_tests = len(all_tests)
    
    # Count for each marker
    for level, info in DEPENDENCY_LEVELS.items():
        marker = info["marker"]
        cmd = ["python", "-m", "pytest", "--collect-only", "-m", marker, "-v"]
        process = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BACKEND_DIR))
        
        if process.returncode != 0:
            print(f"Error collecting {level} tests:", process.stderr)
            continue
        
        # Count tests with this marker
        marker_tests = re.findall(r"<([\w\.]+) .*>", process.stdout)
        result[level] = len(marker_tests)
    
    # Calculate unmarked tests
    marked_tests = sum(result.values())
    result["unmarked"] = total_tests - marked_tests
    result["total"] = total_tests
    
    return result

def generate_report() -> str:
    """Generate a report on test dependencies."""
    print("\nCollecting test counts by category...")
    counts = count_tests_by_marker()
    
    # Create the report
    report = "\n" + "=" * 80 + "\n"
    report += "NOVAMIND TEST DEPENDENCY REPORT\n"
    report += "=" * 80 + "\n\n"
    
    # Summary
    total_tests = counts.get("total", 0)
    report += f"Total tests: {total_tests}\n\n"
    
    # Breakdown by dependency
    report += "DEPENDENCY BREAKDOWN:\n"
    report += "-" * 40 + "\n"
    
    for level, info in DEPENDENCY_LEVELS.items():
        count = counts.get(level, 0)
        percentage = (count / total_tests * 100) if total_tests > 0 else 0
        
        report += f"{level.upper()}:\n"
        report += f"  Description: {info['description']}\n"
        report += f"  Tests: {count} ({percentage:.1f}%)\n\n"
    
    # Unmarked tests
    unmarked = counts.get("unmarked", 0)
    unmarked_percentage = (unmarked / total_tests * 100) if total_tests > 0 else 0
    
    report += "UNMARKED TESTS:\n"
    report += f"  Tests: {unmarked} ({unmarked_percentage:.1f}%)\n"
    report += "  These tests don't have explicit dependency markers and might need to be categorized\n\n"
    
    # Recommendations
    report += "RECOMMENDATIONS:\n"
    if unmarked_percentage > 20:
        report += f"  ⚠️ Over 20% of tests are unmarked. Consider adding dependency markers for better organization.\n"
    
    standalone_percentage = (counts.get("standalone", 0) / total_tests * 100) if total_tests > 0 else 0
    if standalone_percentage < 30:
        report += f"  ⚠️ Only {standalone_percentage:.1f}% of tests are standalone. Consider converting more tests to standalone.\n"
    
    # Save the report to a file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = RESULTS_DIR / f"test-dependency-report-{timestamp}.txt"
    
    # Ensure the directory exists
    RESULTS_DIR.mkdir(exist_ok=True)
    
    # Write to file
    with open(report_file, "w") as f:
        f.write(report)
    
    report += f"\nReport saved to {report_file}\n"
    
    return report

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run tests based on dependency level"
    )
    parser.add_argument("--level", choices=["standalone", "venv", "db", "all"],
                       help="Dependency level to run tests for")
    parser.add_argument("--report", action="store_true",
                       help="Generate a report on test dependencies")
    parser.add_argument("--xml", action="store_true",
                       help="Output test results in XML format")
    parser.add_argument("--junit", action="store_true",
                       help="Output test results in JUnit XML format")
    
    # Capture all other args to pass to pytest
    args, unknown = parser.parse_known_args()
    
    # If no level is specified and no report is requested, show help
    if not args.level and not args.report:
        parser.print_help()
        return 1
    
    # Generate report if requested
    if args.report:
        report = generate_report()
        print(report)
        return 0
    
    # Run tests for the specified level
    if args.level != "all":
        exit_code, output, duration = run_tests(args.level, unknown)
        print(output)
        print(f"\nTests completed in {duration:.2f} seconds with exit code {exit_code}")
        return exit_code
    
    # Run all tests in order if level is "all"
    levels = ["standalone", "venv", "db"]
    exit_codes = []
    
    for level in levels:
        exit_code, output, duration = run_tests(level, unknown)
        print(output)
        print(f"\n{level.capitalize()} tests completed in {duration:.2f} seconds with exit code {exit_code}")
        exit_codes.append(exit_code)
    
    # Return non-zero if any test level failed
    return max(exit_codes) if exit_codes else 0

if __name__ == "__main__":
    sys.exit(main())