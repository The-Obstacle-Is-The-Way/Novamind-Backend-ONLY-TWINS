# Test Scripts Implementation Plan

## Overview

This document provides a detailed implementation plan for the canonical test scripts infrastructure, building on the analysis in `05_TEST_SCRIPTS_ANALYSIS.md`. It includes specific code implementations, migration steps, and guidelines to establish a production-grade test execution environment for the Novamind Digital Twin platform.

## Canonical Test Runner Implementation

The core of our testing infrastructure will be a single, canonical test runner that implements the directory-based SSOT approach. Below is the complete implementation of this runner:

### `backend/scripts/test/runners/run_tests.py`

```python
#!/usr/bin/env python3
"""
Novamind Digital Twin Canonical Test Runner

This script is the canonical test runner for the Novamind Digital Twin platform.
It implements the directory-based SSOT approach where tests are organized by
dependency level:
  - standalone/ - No external dependencies (fastest)
  - venv/ - Python package dependencies (medium)
  - integration/ - External services required (slowest)

Usage:
    python scripts/test/runners/run_tests.py --standalone  # Run standalone tests
    python scripts/test/runners/run_tests.py --venv        # Run venv tests
    python scripts/test/runners/run_tests.py --integration # Run integration tests
    python scripts/test/runners/run_tests.py --all         # Run all tests
    python scripts/test/runners/run_tests.py --coverage    # Generate coverage

Features:
    - Progressive test execution (dependent on preceding test success)
    - Detailed reporting with colored output
    - Coverage reporting integration
    - JUnit XML output for CI/CD integration
    - Filtering by markers

Exit Codes:
    0 - All requested tests passed
    1 - At least one test failed
    2 - Invalid arguments or configuration
"""

import os
import sys
import time
import argparse
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set

# ANSI color codes for terminal output
class Color:
    """ANSI color codes for terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def disable_if_windows():
        """Disable colors on Windows if not supported."""
        if platform.system() == "Windows":
            Color.BLUE = ''
            Color.GREEN = ''
            Color.YELLOW = ''
            Color.RED = ''
            Color.ENDC = ''
            Color.BOLD = ''


def print_header(message: str) -> None:
    """
    Print a formatted header message.
    
    Args:
        message: The message to print as a header
    """
    print(f"\n{Color.BOLD}{Color.BLUE}{'=' * 80}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.BLUE}{message.center(80)}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.BLUE}{'=' * 80}{Color.ENDC}\n")


def print_section(message: str) -> None:
    """
    Print a formatted section header.
    
    Args:
        message: The message to print as a section header
    """
    print(f"\n{Color.BOLD}{Color.YELLOW}{message}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.YELLOW}{'-' * len(message)}{Color.ENDC}\n")


def run_command(cmd: List[str], env: Optional[Dict[str, str]] = None) -> Tuple[bool, str, float]:
    """
    Run a command and return success status, output, and execution time.
    
    Args:
        cmd: The command to run as a list of strings
        env: Optional environment variables to set
        
    Returns:
        Tuple of (success, output, execution_time)
    """
    print(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        # Use provided environment or current environment
        env_vars = env or os.environ.copy()
        
        # Run the command
        result = subprocess.run(
            cmd,
            env=env_vars,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Check if the command succeeded
        success = result.returncode == 0
        output = result.stdout
    except Exception as e:
        success = False
        output = str(e)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    return success, output, execution_time


def ensure_test_directories() -> bool:
    """
    Ensure test directory structure exists.
    
    Returns:
        True if all directories exist or were created, False otherwise
    """
    try:
        tests_dir = Path('backend/app/tests')
        if not tests_dir.exists():
            print(f"{Color.RED}Test directory {tests_dir} does not exist{Color.ENDC}")
            return False
            
        for directory in ['standalone', 'venv', 'integration']:
            dir_path = tests_dir / directory
            dir_path.mkdir(exist_ok=True, parents=True)
            
            # Create __init__.py files for Python imports
            init_file = dir_path / '__init__.py'
            if not init_file.exists():
                init_file.touch()
        
        return True
    except Exception as e:
        print(f"{Color.RED}Error ensuring test directories: {e}{Color.ENDC}")
        return False


def run_test_directory(
    directory: str, 
    coverage: bool, 
    junit: bool, 
    markers: Optional[str],
    parallel: Optional[int] = None,
    verbose: bool = False,
    test_filter: Optional[str] = None,
    failfast: bool = False
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Run tests in the specified directory.
    
    Args:
        directory: The test directory to run (standalone, venv, integration)
        coverage: Whether to generate coverage reports
        junit: Whether to generate JUnit XML reports
        markers: Optional markers to filter tests
        parallel: Optional number of parallel processes to use
        verbose: Whether to use verbose output
        test_filter: Optional filter for test path/names
