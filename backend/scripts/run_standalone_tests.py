#!/usr/bin/env python3
"""
Standalone Test Runner for Novamind Digital Twin Platform

This script identifies and runs all standalone tests (tests that don't require external dependencies)
and generates comprehensive coverage reports. It's designed to be used both locally and in CI/CD
pipelines to verify that standalone tests pass before proceeding to integration tests.

Usage:
    python scripts/run_standalone_tests.py [--verbose] [--xml] [--html] [--ci]

Options:
    --verbose   : Show detailed test output
    --xml       : Generate XML coverage report
    --html      : Generate HTML coverage report
    --ci        : Run in CI mode (fails on any test failure)
"""

import os
import sys
import argparse
import subprocess
import datetime
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run standalone tests for Novamind")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--xml", action="store_true", help="Generate XML coverage report")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--ci", action="store_true", help="Run in CI mode")
    return parser.parse_args()


def ensure_directory_exists(directory_path):
    """Ensure directory exists, create if it doesn't."""
    Path(directory_path).mkdir(parents=True, exist_ok=True)


def generate_timestamp():
    """Generate a timestamp string for report naming."""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def run_standalone_tests(args):
    """Run the standalone tests and generate reports."""
    # Ensure we're in the backend root directory
    backend_dir = Path(__file__).resolve().parent.parent
    os.chdir(backend_dir)
    
    # Create necessary directories
    test_results_dir = backend_dir / "test-results"
    ensure_directory_exists(test_results_dir)
    
    # Verify standalone tests directory exists
    standalone_test_dir = backend_dir / "app" / "tests" / "standalone"
    if not standalone_test_dir.exists():
        print(f"Error: Standalone test directory not found at {standalone_test_dir}")
        return False
    
    # Count test files to give feedback
    test_files = list(standalone_test_dir.glob("test_*.py"))
    print(f"Found {len(test_files)} standalone test files")
    
    # Build pytest command
    timestamp = generate_timestamp()
    cmd = ["python", "-m", "pytest", "app/tests/standalone/"]
    
    # Set environment variables
    env = os.environ.copy()
    env["TESTING"] = "1"
    env["TEST_TYPE"] = "unit"
    env["PYTHONPATH"] = str(backend_dir)
    
    # Add flags based on arguments
    if args.verbose:
        cmd.append("-v")
    
    # Add coverage settings
    cmd.extend(["--cov=app"])
    
    # Add report outputs
    if args.xml:
        xml_path = f"coverage-{timestamp}.xml"
