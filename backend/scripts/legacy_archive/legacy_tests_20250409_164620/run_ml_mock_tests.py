#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to run unit tests for all ML mock services.

This script runs the tests for all ML mock services (mock.py, mock_dt.py, and mock_phi.py)
and generates a coverage report to ensure we have at least 80% test coverage across
these critical mock implementations used for testing.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_tests(timeout=300, quick=False):
    """
    Run the ML mock tests with coverage.
    
    Args:
        timeout: Maximum time in seconds to allow the tests to run
        quick: When True, runs only basic initialization tests for faster feedback
    """
    print(f"Running ML mock tests with coverage (timeout: {timeout}s)...")
    
    try:
        # Ensure we're in the backend directory
        backend_dir = Path(__file__).resolve().parent.parent  # Go up one level from scripts/ to backend/
        os.chdir(backend_dir)
        print(f"Working directory: {os.getcwd()}")

        # Command to run pytest with coverage
        # Use the project's virtual environment
        cmd = [
            "./venv/bin/pytest",  # Use the pytest executable from the venv
            "-xvs",
        ]
        
        if quick:
            # In quick mode, just run a subset of tests
            print("Running in QUICK mode - testing only basic functionality")
            cmd.append("app/tests/core/services/ml/test_mock.py::TestMockMentaLLaMA::test_initialization")
            cmd.append("app/tests/core/services/ml/test_mock_dt.py::TestMockDigitalTwinService::test_initialization")
            cmd.append("app/tests/core/services/ml/test_mock_phi.py::TestMockPHIDetection::test_initialization")
            cmd.append("--cov=app.core.services.ml.mock")
            cmd.append("--cov=app.core.services.ml.mock_dt")
            cmd.append("--cov=app.core.services.ml.mock_phi")
        else:
            # In normal mode, run all tests
            cmd.extend([
                "app/tests/core/services/ml/test_mock.py",
                "app/tests/core/services/ml/test_mock_dt.py",
                "app/tests/core/services/ml/test_mock_phi.py",
                "--cov=app.core.services.ml.mock",
                "--cov=app.core.services.ml.mock_dt",
                "--cov=app.core.services.ml.mock_phi",
            ])
        
        # Add coverage report format
        cmd.append("--cov-report=term-missing")
        
        print(f"Running command: {' '.join(cmd)}")
    
        # Run the tests with a timeout at the subprocess level too
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 10  # Give a little extra time for subprocess management
        )
        
        # Print test output
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        # Check if tests passed
        if result.returncode != 0:
            print(f"Tests failed with exit code: {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print(f"ERROR: Tests timed out after {timeout} seconds!")
        return False
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {str(e)}")
        return False
    
    # Parse coverage from output
    coverage = extract_coverage(result.stdout)
    
    # Validate coverage
    target_coverage = 20 if quick else 80  # Lower threshold for quick mode
    
    if coverage >= target_coverage:
        print(f"\n🎉 Target coverage of {target_coverage}% achieved! Current coverage: {coverage:.2f}%")
        return True
    else:
        print(f"\n❌ Coverage is at {coverage:.2f}%. Target is {target_coverage}%.")
        return False


def extract_coverage(output):
    """Extract the coverage percentage from the pytest output."""
    try:
        # Find the coverage line in the output
        for line in output.split('\n'):
            if "TOTAL" in line and "%" in line:
                # Extract the percentage
                parts = line.split()
                for part in parts:
                    if "%" in part:
                        return float(part.strip('%'))
        return 0
    except Exception as e:
        print(f"Error extracting coverage: {e}")
        return 0


def create_venv_instructions():
    """Print instructions for setting up a virtual environment."""
    print("\n=== Setup Instructions ===")
    print("If you're having trouble running the tests, try setting up a virtual environment:")
    print("\n1. Create a virtual environment:")
    print("   python -m venv venv")
    print("\n2. Activate the virtual environment:")
    print("   On Windows: venv\\Scripts\\activate")
    print("   On macOS/Linux: source venv/bin/activate")
    print("\n3. Install development dependencies:")
    print("   pip install -r requirements-dev.txt")
    print("\n4. Run the tests again:")
    print("   python scripts/run_ml_mock_tests.py")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run ML mock tests with coverage')
    parser.add_argument('--timeout', type=int, default=300,
                        help='Maximum time in seconds to allow tests to run')
    parser.add_argument('--quick', action='store_true',
                        help='Run only basic tests for a quick check')
    args = parser.parse_args()
    
    # Run with specified parameters
    success = run_tests(timeout=args.timeout, quick=args.quick)
    
    if not success:
        create_venv_instructions()
    
    sys.exit(0 if success else 1)