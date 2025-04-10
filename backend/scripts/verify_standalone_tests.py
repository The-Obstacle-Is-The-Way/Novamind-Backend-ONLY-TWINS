#!/usr/bin/env python3
"""
Standalone Test Verification Tool

This script verifies that standalone tests can run properly in an isolated environment.
It identifies existing standalone tests, runs them without external dependencies,
and reports any issues that would prevent them from running in a CI environment.

Usage:
    python verify_standalone_tests.py [--test-file <specific_test_file>] [--verbose]

Options:
    --test-file  Path to a specific test file to verify (optional)
    --verbose    Show detailed output
"""

import os
import sys
import argparse
import subprocess
import tempfile
import shutil
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Verify standalone tests")
    parser.add_argument("--test-file", help="Path to a specific test file to verify")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    return parser.parse_args()


def find_standalone_tests(tests_dir):
    """Find all standalone test files."""
    standalone_tests_dir = tests_dir / "standalone"
    if not standalone_tests_dir.exists():
        print(f"Error: Standalone test directory not found at {standalone_tests_dir}")
        return []
    
    test_files = list(standalone_tests_dir.glob("test_*.py"))
    return test_files


def verify_test_isolation(test_file, verbose=False):
    """Verify that a test can run in isolation without external dependencies."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy the test file to the temp directory
        test_name = test_file.name
        temp_test_file = temp_path / test_name
        shutil.copy(test_file, temp_test_file)
        
        # Run pytest on the copied file
        cmd = ["python", "-m", "pytest", str(temp_test_file), "-v"]
        
        if verbose:
            print(f"Running: {' '.join(cmd)}")
            print(f"In directory: {temp_path}")
        
        # Execute in an environment with minimal dependencies
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path.cwd())  # Only include the current dir in PYTHONPATH
        
        result = subprocess.run(
            cmd, 
            env=env,
            cwd=temp_path,
            capture_output=True,
            text=True
        )
        
        success = result.returncode == 0
        
        if verbose or not success:
            print(f"\n--- Output for {test_name} ---")
            print(result.stdout)
            
            if result.stderr:
                print("--- Error output ---")
                print(result.stderr)
        
        return {
            "file": str(test_file),
            "success": success,
            "output": result.stdout,
            "error": result.stderr
        }


def main():
    """Main entry point."""
    args = parse_args()
    
    # Get backend directory
    backend_dir = Path.cwd()
    if backend_dir.name != "backend":
        # Try to find the backend directory
        if (backend_dir / "backend").exists():
            backend_dir = backend_dir / "backend"
        else:
            print("Error: Could not locate the backend directory.")
            return 1
    
    # Get test directory
    tests_dir = backend_dir / "app" / "tests"
    if not tests_dir.exists():
        print(f"Error: Tests directory not found at {tests_dir}")
        return 1
    
    if args.test_file:
        # Verify a specific test file
        test_file = Path(args.test_file)
        if not test_file.exists():
            print(f"Error: Test file not found: {test_file}")
            return 1
        
        print(f"Verifying isolation for: {test_file}")
        result = verify_test_isolation(test_file, args.verbose)
        
        if result["success"]:
            print(f"✅ {test_file.name} can run in isolation")
            return 0
        else:
            print(f"❌ {test_file.name} fails when run in isolation")
            return 1
    
    # Find all standalone tests
    test_files = find_standalone_tests(tests_dir)
    if not test_files:
        print("No standalone test files found.")
        return 1
    
    print(f"Found {len(test_files)} standalone test files")
    
    # Verify each test
    results = []
    for test_file in test_files:
        print(f"Verifying: {test_file.name}...")
        result = verify_test_isolation(test_file, args.verbose)
        results.append(result)
    
    # Print summary
    success_count = sum(1 for r in results if r["success"])
    
    print("\n===== SUMMARY =====")
    print(f"Total tests: {len(results)}")
    print(f"Passed isolation check: {success_count}")
    print(f"Failed isolation check: {len(results) - success_count}")
    
    if len(results) - success_count > 0:
        print("\nFailing tests:")
        for result in results:
            if not result["success"]:
                print(f"❌ {result['file']}")
    
    # Return non-zero if any test failed
    return 0 if success_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())