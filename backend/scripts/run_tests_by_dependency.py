#!/usr/bin/env python
"""
Run tests by dependency level.

This script runs tests based on their dependency requirements:
1. Standalone tests: No dependencies beyond Python itself
2. VENV-dependent tests: Require Python packages but no external services
3. DB-dependent tests: Require database connections or other external services

Usage:
    python -m scripts.run_tests_by_dependency --standalone  # Run standalone tests
    python -m scripts.run_tests_by_dependency --venv        # Run venv-dependent tests
    python -m scripts.run_tests_by_dependency --db          # Run DB-dependent tests
    python -m scripts.run_tests_by_dependency --all         # Run all tests in order
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run tests by dependency level")
    parser.add_argument(
        "--standalone", action="store_true", help="Run standalone tests"
    )
    parser.add_argument(
        "--venv", action="store_true", help="Run VENV-dependent tests"
    )
    parser.add_argument(
        "--db", action="store_true", help="Run DB-dependent tests"
    )
    parser.add_argument(
        "--all", action="store_true", help="Run all tests in order"
    )
    parser.add_argument(
        "--xml", action="store_true", help="Generate XML reports"
    )
    parser.add_argument(
        "--html", action="store_true", help="Generate HTML coverage reports"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output"
    )

    return parser.parse_args()


def get_project_root():
    """Get the project root directory."""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


def run_pytest(marker, xml_output=None, html=False, verbose=False):
    """Run pytest with the specified marker."""
    cmd = ["pytest"]
    
    if marker:
        cmd.extend(["-m", marker])
    
    cmd.extend(["--cov=app"])
    
    if xml_output:
        cmd.extend(["--junitxml", xml_output])
    
    if html:
        cmd.extend(["--cov-report", "html:coverage_html"])
    
    cmd.extend(["--cov-report", "term"])
    
    if verbose:
        cmd.append("-v")
    
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.error(result.stderr)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running pytest: {e}")
        return False


def main():
    """Main entry point."""
    args = parse_args()
    os.chdir(get_project_root())  # Change to project root
    
    if not any([args.standalone, args.venv, args.db, args.all]):
        logger.info("No test type specified, defaulting to --all")
        args.all = True
    
    success = True
    
    # Run standalone tests
    if args.standalone or args.all:
        logger.info("Running standalone tests...")
        xml_output = "test-results/standalone-results.xml" if args.xml else None
        standalone_success = run_pytest("standalone", xml_output, args.html, args.verbose)
        if not standalone_success:
            logger.error("Standalone tests failed")
            success = False
            if not args.all:
                return 1
    
    # Run VENV-dependent tests
    if args.venv or args.all:
        logger.info("Running VENV-dependent tests...")
        xml_output = "test-results/venv-results.xml" if args.xml else None
        venv_success = run_pytest("venv_only", xml_output, args.html, args.verbose)
        if not venv_success:
            logger.error("VENV-dependent tests failed")
            success = False
            if not args.all:
                return 1
    
    # Run DB-dependent tests
    if args.db or args.all:
        logger.info("Running DB-dependent tests...")
        xml_output = "test-results/db-results.xml" if args.xml else None
        db_success = run_pytest("db_required", xml_output, args.html, args.verbose)
        if not db_success:
            logger.error("DB-dependent tests failed")
            success = False
            if not args.all:
                return 1
    
    if not success:
        logger.error("One or more test types failed")
        return 1
    
    logger.info("All tests passed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())