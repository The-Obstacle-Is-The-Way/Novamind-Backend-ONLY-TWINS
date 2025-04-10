#!/usr/bin/env python3
"""
Test runner script for the Novamind Digital Twin Backend.

This script runs tests based on their dependency level, allowing for more
efficient testing by running independent tests first and dependent tests later.
"""
import os
import sys
import argparse
import asyncio
import subprocess
from typing import List, Optional, Dict, Any
import logging
import time
import json
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("test_runner")

# Constants
BACKEND_DIR = Path(__file__).parent.parent
TEST_DIR = BACKEND_DIR / "app" / "tests"
STANDALONE_DIR = TEST_DIR / "standalone"
TEST_RESULTS_DIR = BACKEND_DIR / "test-results"
COVERAGE_DIR = BACKEND_DIR / "coverage_html"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run tests by dependency level")
    
    # Test selection options
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Run all tests")
    group.add_argument("--standalone", action="store_true", help="Run standalone tests only")
    group.add_argument("--venv", action="store_true", help="Run venv-dependent tests only")
    group.add_argument("--db", action="store_true", help="Run database-dependent tests only")
    
    # Output options
    parser.add_argument("--xml", action="store_true", help="Generate XML test report")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--ci", action="store_true", help="Run in CI mode (changes output paths)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Environment options
    parser.add_argument("--cleanup", action="store_true", help="Clean up test environment after tests")
    parser.add_argument("--setup-env", action="store_true", help="Set up test environment without running tests")
    parser.add_argument("--cleanup-env", action="store_true", help="Clean up test environment without running tests")
    
    return parser.parse_args()


def setup_environment() -> bool:
    """Set up the test environment."""
    logger.info("Setting up test environment...")
    
    # Create directories
    os.makedirs(TEST_RESULTS_DIR, exist_ok=True)
    os.makedirs(COVERAGE_DIR, exist_ok=True)
    
    # Start services if needed for DB tests
    # This would typically start Docker containers with test databases
    if os.path.exists(BACKEND_DIR / "scripts" / "run_test_environment.sh"):
        try:
            subprocess.run(
                ["bash", BACKEND_DIR / "scripts" / "run_test_environment.sh", "start"],
                check=True
            )
            logger.info("Test environment started successfully")
        except subprocess.CalledProcessError:
            logger.error("Failed to start test environment")
            return False
    
    return True


def cleanup_environment() -> bool:
    """Clean up the test environment."""
    logger.info("Cleaning up test environment...")
    
    # Stop services if needed
    if os.path.exists(BACKEND_DIR / "scripts" / "run_test_environment.sh"):
        try:
            subprocess.run(
                ["bash", BACKEND_DIR / "scripts" / "run_test_environment.sh", "stop"],
                check=True
            )
            logger.info("Test environment stopped successfully")
        except subprocess.CalledProcessError:
            logger.error("Failed to stop test environment")
            return False
    
    return True


def run_tests(
    test_type: str, 
    xml_output: bool = False, 
    html_output: bool = False, 
    verbose: bool = False, 
    ci_mode: bool = False
) -> bool:
    """
    Run tests of a specific dependency level.
    
    Args:
        test_type: Type of tests to run ('standalone', 'venv', 'db')
        xml_output: Whether to generate XML report
        html_output: Whether to generate HTML coverage report
        verbose: Whether to use verbose output
        ci_mode: Whether running in CI environment
        
    Returns:
        bool: True if tests passed, False otherwise
    """
    logger.info(f"Running {test_type} tests...")
    
    # Prepare pytest arguments
    pytest_args = ["-xvs"] if verbose else ["-x"]
    
    if test_type == "standalone":
        # Standalone tests are in a dedicated directory
        pytest_args.extend([str(STANDALONE_DIR)])
        marker = "standalone"
    elif test_type == "venv":
        # VENV-dependent tests are anywhere with the venv_only marker
        pytest_args.extend(["-m", "venv_only", str(TEST_DIR)])
        marker = "venv_only"
    elif test_type == "db":
        # DB-dependent tests are anywhere with the db_required marker
        pytest_args.extend(["-m", "db_required", str(TEST_DIR)])
        marker = "db_required"
    else:
        logger.error(f"Unknown test type: {test_type}")
        return False
    
    # Add coverage options
    pytest_args.extend(["--cov=app", "--cov-report=term"])
    
    # Add XML output if requested
    if xml_output:
        xml_file = TEST_RESULTS_DIR / f"{test_type}-results.xml"
        pytest_args.extend(["--junitxml", str(xml_file)])
    
    # Add HTML output if requested
    if html_output:
        pytest_args.extend(["--cov-report", f"html:{COVERAGE_DIR}"])
    
    # Run pytest
    logger.info(f"Running pytest with args: {' '.join(pytest_args)}")
    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + pytest_args,
        cwd=BACKEND_DIR
    )
    
    return result.returncode == 0


def main() -> int:
    """Main entry point."""
    args = parse_args()
    start_time = time.time()
    
    # Early returns for environment-only operations
    if args.setup_env:
        return 0 if setup_environment() else 1
    
    if args.cleanup_env:
        return 0 if cleanup_environment() else 1
    
    # Determine which tests to run
    run_standalone = args.all or args.standalone
    run_venv = args.all or args.venv
    run_db = args.all or args.db
    
    # If no test type specified, run all
    if not (run_standalone or run_venv or run_db):
        run_standalone = run_venv = run_db = True
    
    # Set up environment if needed
    if run_db and not setup_environment():
        return 1
    
    # Track pass/fail status
    tests_passed = True
    
    try:
        # Run tests in dependency order
        if run_standalone:
            standalone_passed = run_tests(
                "standalone", 
                xml_output=args.xml, 
                html_output=args.html, 
                verbose=args.verbose,
                ci_mode=args.ci
            )
            tests_passed = tests_passed and standalone_passed
            
            if not standalone_passed and not args.all:
                logger.error("Standalone tests failed, stopping test run")
                return 1
        
        if run_venv:
            venv_passed = run_tests(
                "venv", 
                xml_output=args.xml, 
                html_output=args.html, 
                verbose=args.verbose,
                ci_mode=args.ci
            )
            tests_passed = tests_passed and venv_passed
            
            if not venv_passed and not args.all:
                logger.error("VENV-dependent tests failed, stopping test run")
                return 1
        
        if run_db:
            db_passed = run_tests(
                "db", 
                xml_output=args.xml, 
                html_output=args.html, 
                verbose=args.verbose,
                ci_mode=args.ci
            )
            tests_passed = tests_passed and db_passed
    
    finally:
        # Clean up if requested or if we're running DB tests
        if (args.cleanup or run_db) and not args.setup_env:
            cleanup_environment()
    
    # Report test results
    elapsed_time = time.time() - start_time
    if tests_passed:
        logger.info(f"All tests passed in {elapsed_time:.2f} seconds")
        return 0
    else:
        logger.error(f"Tests failed after {elapsed_time:.2f} seconds")
        return 1


if __name__ == "__main__":
    sys.exit(main())