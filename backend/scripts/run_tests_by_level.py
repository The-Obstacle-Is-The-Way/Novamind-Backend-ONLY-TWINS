#!/usr/bin/env python3
"""
Novamind Digital Twin Test Runner by Dependency Level

This script runs tests based on their dependency level using the existing directory
structure rather than requiring manual markers. It follows a fail-fast approach
for CI/CD pipelines by running tests in order of increasing dependency complexity.

Key features:
- Directory-based test categorization (no markers needed)
- Automatic test discovery and counting
- Docker compatibility for integration tests
- XML reports for CI/CD integration
- Detailed test summary and statistics

Usage:
    python -m backend.scripts.run_tests_by_level standalone       # Run standalone tests only
    python -m backend.scripts.run_tests_by_level venv_only        # Run tests requiring only Python packages
    python -m backend.scripts.run_tests_by_level db_required      # Run tests requiring database/external services
    python -m backend.scripts.run_tests_by_level all              # Run all tests in dependency order
    python -m backend.scripts.run_tests_by_level count            # Count tests by level
    
    Optional flags:
    --fail-fast                 # Stop on first test failure
    --xml                       # Generate XML reports
    --cleanup                   # Remove temporary files after tests
    --docker                    # Indicate tests are running in Docker environment
"""

import sys
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import argparse
import xml.etree.ElementTree as ET
import time
import json

# Root directory setup
ROOT_DIR = Path(__file__).parents[1]  # backend directory
TEST_DIR = ROOT_DIR / "app" / "tests"

# Define test directories by dependency level
TEST_LEVELS = {
    "standalone": [str(TEST_DIR / "standalone")],
    "venv_only": [str(TEST_DIR / "unit"), str(TEST_DIR / "venv_only")],
    "db_required": [str(TEST_DIR / "integration"), str(TEST_DIR / "api"), str(TEST_DIR / "e2e")]
}

# Define expected test counts based on our analysis
TEST_COUNTS = {
    "standalone": 335,   # 335 tests in standalone directory
    "venv_only": 1124,   # 1124 tests in unit directory
    "db_required": 66,   # 66 tests in integration directory
}

RESULTS_DIR = ROOT_DIR / "test-results"

# Docker environment detection
IS_DOCKER = os.environ.get("TESTING", "0") == "1"


def ensure_results_dir():
    """Make sure the test results directory exists."""
    RESULTS_DIR.mkdir(exist_ok=True, parents=True)
    

def count_tests_by_level() -> Dict[str, int]:
    """Count how many tests exist at each dependency level based on directory location."""
    counts = {}
    
    for level, dirs in TEST_LEVELS.items():
        total_tests = 0
        
        for test_dir in dirs:
            if not os.path.exists(test_dir):
                continue
                
            # Run pytest --collect-only to get test count
            cmd = ["python", "-m", "pytest", test_dir, "--collect-only", "-q"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Extract test count from output (looking for lines like "collected X items")
            import re
            match = re.search(r"collected (\d+) items", result.stdout)
            if match:
                count = int(match.group(1))
                total_tests += count
        
        counts[level] = total_tests
    
    return counts


def run_tests(level: str, options: List[str] = None, is_docker: bool = False) -> Tuple[int, float, int]:
    """
    Run tests for a specified dependency level.
    
    Args:
        level: The dependency level (standalone, venv_only, db_required)
        options: Additional pytest options
        is_docker: Whether tests are running in Docker environment
        
    Returns:
        Tuple of (exit_code, duration_in_seconds, test_count)
    """
    if level not in TEST_LEVELS:
        print(f"Error: Unknown test level '{level}'")
        return 1, 0, 0
    
    test_dirs = TEST_LEVELS[level]
    existing_dirs = [d for d in test_dirs if os.path.exists(d)]
    
    if not existing_dirs:
        print(f"No test directories found for level: {level}")
        return 0, 0, 0
    
    # Default options
    if options is None:
        options = ["-v"]
    
    # Add JUnit XML output for CI integration
    xml_report = str(RESULTS_DIR / f"{level}-results.xml")
    options.extend(["--junitxml", xml_report])
    
    # Add coverage options if running in Docker
    if is_docker and level == "db_required":
        # Add Docker-specific environment variables for DB tests
        os.environ["TEST_DATABASE_URL"] = os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@novamind-db-test:5432/novamind_test"
        )
        os.environ["TEST_REDIS_URL"] = os.environ.get(
            "TEST_REDIS_URL",
            "redis://novamind-redis-test:6379/0"
        )
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"] + existing_dirs + options
    
    print(f"\n=== Running {level.upper()} tests ===\n")
    print(f"Command: {' '.join(cmd)}")
    
    # Time the test run
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start_time
    
    # Print the output
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # Extract test count from output
    test_count = 0
    collected_match = re.search(r"collected (\d+) items", result.stdout or "")
    if collected_match:
        test_count = int(collected_match.group(1))
    
    print(f"\n=== {level.upper()} tests completed in {duration:.2f} seconds ===\n")
    
    return result.returncode, duration, test_count


def run_all_tests(options: List[str] = None, is_docker: bool = False, fail_fast: bool = False) -> Dict[str, Dict]:
    """
    Run all tests in dependency order (standalone -> venv_only -> db_required).
    
    Args:
        options: Additional pytest options
        is_docker: Whether tests are running in Docker environment
        fail_fast: Whether to stop after first failed test level
        
    Returns:
        A dictionary with results for each level.
    """
    results = {}
    
    # Run tests in dependency order
    for level in ["standalone", "venv_only", "db_required"]:
        exit_code, duration, test_count = run_tests(level, options, is_docker)
        
        results[level] = {
            "exit_code": exit_code,
            "duration": duration,
            "tests": test_count
        }
        
        # Skip to next level on failure if fail_fast is enabled
        if exit_code != 0 and fail_fast:
            print(f"\n⚠️ Tests failed at {level} level. Stopping due to fail-fast option.")
            break
        
        # Parse XML results if available
        xml_report = RESULTS_DIR / f"{level}-results.xml"
        if xml_report.exists():
            try:
                tree = ET.parse(xml_report)
                root = tree.getroot()
                
                # Extract summary information
                tests = int(root.attrib.get("tests", 0))
                failures = int(root.attrib.get("failures", 0))
                errors = int(root.attrib.get("errors", 0))
                skipped = int(root.attrib.get("skipped", 0))
                
                results[level].update({
                    "tests": tests,
                    "failures": failures,
                    "errors": errors,
                    "skipped": skipped,
                    "passing": tests - failures - errors - skipped
                })
            except Exception as e:
                print(f"Error parsing test results: {e}")
    
    # Save summary to JSON file
    with open(RESULTS_DIR / "test-summary.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results


def print_summary(results: Dict[str, Dict]):
    """Print a summary of test results."""
    print("\n=== TEST SUMMARY ===\n")
    
    total_tests = 0
    total_passing = 0
    total_duration = 0
    
    for level, result in results.items():
        tests = result.get("tests", 0)
        passing = result.get("passing", 0)
        failures = result.get("failures", 0)
        errors = result.get("errors", 0)
        skipped = result.get("skipped", 0)
        duration = result.get("duration", 0)
        
        total_tests += tests
        total_passing += passing
        total_duration += duration
        
        print(f"{level.upper()} Tests:")
        print(f"  Tests: {tests}")
        print(f"  Passing: {passing}")
        print(f"  Failures: {failures}")
        print(f"  Errors: {errors}")
        print(f"  Skipped: {skipped}")
        print(f"  Duration: {duration:.2f} seconds")
        print()
    
    if total_tests > 0:
        pass_percentage = (total_passing / total_tests) * 100
        print(f"OVERALL:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Total Passing: {total_passing}")
        print(f"  Pass Rate: {pass_percentage:.2f}%")
        print(f"  Total Duration: {total_duration:.2f} seconds")
        print(f"\nTest results saved to: {RESULTS_DIR}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run tests by dependency level')
    parser.add_argument('level', choices=['standalone', 'venv_only', 'db_required', 'all', 'count'],
                        help='Test level to run, or "all" to run all levels, or "count" to count tests')
    parser.add_argument('--xvs', action='store_true', help='Add -xvs to pytest options')
    parser.add_argument('--keywords', '-k', help='Only run tests matching these keywords')
    parser.add_argument('--fail-fast', action='store_true', help='Stop on first failure')
    parser.add_argument('--xml', action='store_true', help='Generate XML reports')
    parser.add_argument('--cleanup', action='store_true', help='Remove temporary files after tests')
    parser.add_argument('--docker', action='store_true', help='Indicate tests are running in Docker environment')
    
    return parser.parse_args()

def cleanup_temp_files():
    """Clean up temporary files created during testing."""
    print("\nCleaning up temporary files...")
    # Add cleanup commands here if needed
    # For example, remove __pycache__ directories
    subprocess.run(["find", str(ROOT_DIR), "-name", "__pycache__", "-type", "d", "-exec", "rm", "-rf", "{}", "+"])
    print("Cleanup complete.")

def main():
    """Main entry point."""
    args = parse_args()
    ensure_results_dir()
    
    # Detect Docker environment
    is_docker = IS_DOCKER or args.docker
    if is_docker:
        print("Detected Docker environment")
    
    # Build pytest options
    options = ["-v"]
    if args.xvs:
        options = ["-xvs"]
    if args.keywords:
        options.extend(["-k", args.keywords])
    if args.xml:
        options.extend(["--junitxml", f"{RESULTS_DIR}/test-results.xml"])
    
    if args.level == 'count':
        counts = count_tests_by_level()
        print("\n=== Test Counts by Level ===\n")
        for level, count in counts.items():
            print(f"{level}: {count} tests")
        print(f"\nExpected counts:")
        for level, count in TEST_COUNTS.items():
            print(f"{level}: {count} tests (expected)")
        print(f"\nTotal: {sum(counts.values())} tests")
        return 0
    
    if args.level == 'all':
        results = run_all_tests(options, is_docker, args.fail_fast)
        print_summary(results)
        
        # Clean up if requested
        if args.cleanup:
            cleanup_temp_files()
            
        # Return highest exit code (to fail CI if any test level failed)
        return max(result.get("exit_code", 0) for result in results.values())
    else:
        exit_code, _, _ = run_tests(args.level, options, is_docker)
        
        # Clean up if requested
        if args.cleanup:
            cleanup_temp_files()
            
        return exit_code
        return exit_code


if __name__ == "__main__":
    sys.exit(main())