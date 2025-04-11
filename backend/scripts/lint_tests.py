#!/usr/bin/env python
"""
Lint and format test files using Ruff.

This script helps enforce consistent formatting and code quality in test files.
It can be used to automatically fix simple issues and identify more complex ones.

Usage:
    python -m scripts.lint_tests --fix  # Automatically fix issues
    python -m scripts.lint_tests --check # Just check for issues without fixing
    python -m scripts.lint_tests --standalone # Only check standalone tests
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
    parser = argparse.ArgumentParser(description="Lint and format test files")
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix issues when possible"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check for issues without fixing"
    )
    parser.add_argument(
        "--standalone", action="store_true", help="Only check standalone tests"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output"
    )

    return parser.parse_args()


def get_project_root():
    """Get the project root directory."""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


def run_ruff(test_path, fix=False, verbose=False):
    """Run Ruff on the specified path."""
    cmd = ["ruff", "check"]
    
    if fix:
        cmd.append("--fix")
    
    if verbose:
        cmd.append("--verbose")
    
    cmd.append(str(test_path))
    
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"Ruff found issues:\n{result.stdout}")
            if result.stderr:
                logger.error(f"Errors: {result.stderr}")
            return False
        else:
            if result.stdout:
                logger.info(result.stdout)
            logger.info("Linting passed successfully")
            return True
    except Exception as e:
        logger.error(f"Error running Ruff: {e}")
        return False


def main():
    """Main entry point."""
    args = parse_args()
    root_dir = get_project_root()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    if not (args.fix or args.check):
        logger.info("No action specified, defaulting to --check")
        args.check = True
    
    # Determine which paths to lint
    if args.standalone:
        test_path = root_dir / "app" / "tests" / "standalone"
        if not test_path.exists():
            logger.error(f"Standalone test directory not found: {test_path}")
            return 1
    else:
        test_path = root_dir / "app" / "tests"
    
    fix_mode = args.fix
    success = run_ruff(test_path, fix=fix_mode, verbose=args.verbose)
    
    if not success and not fix_mode:
        logger.info("To automatically fix these issues, run with the --fix flag")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())