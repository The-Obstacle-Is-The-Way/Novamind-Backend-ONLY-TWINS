#!/usr/bin/env python3
"""
Script to run tests by dependency category.

Usage:
    python -m backend.scripts.run_tests_by_dependency.py standalone
    python -m backend.scripts.run_tests_by_dependency.py venv_only
    python -m backend.scripts.run_tests_by_dependency.py db_required
"""
import os
import sys
import subprocess
from pathlib import Path

# Root directory setup
ROOT_DIR = Path(__file__).parents[1]  # backend directory
TEST_DIR = ROOT_DIR / "app" / "tests"

def run_standalone_tests():
    """Run standalone tests."""
    print("\n=== Running STANDALONE tests ===\n")
    standalone_cmd = ["python", "-m", "pytest", 
                     f"{TEST_DIR}/standalone", 
                     "-m", "standalone",
                     "-v"]
    return subprocess.call(standalone_cmd)

def run_venv_only_tests():
    """Run tests that require the Python environment but no database."""
    print("\n=== Running VENV_ONLY tests ===\n")
    venv_cmd = ["python", "-m", "pytest", 
               f"{TEST_DIR}/unit", 
               "-m", "venv_only", 
               "-v"]
    return subprocess.call(venv_cmd)

def run_db_required_tests():
    """Run tests that require a database connection."""
    print("\n=== Running DB_REQUIRED tests ===\n")
    db_cmd = ["python", "-m", "pytest", 
             f"{TEST_DIR}/integration", 
             "-m", "db_required", 
             "-v"]
    return subprocess.call(db_cmd)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify test type: standalone, venv_only, or db_required")
        sys.exit(1)
        
    test_type = sys.argv[1].lower()
    
    if test_type == "standalone":
        exit_code = run_standalone_tests()
    elif test_type == "venv_only":
        exit_code = run_venv_only_tests()
    elif test_type == "db_required":
        exit_code = run_db_required_tests()
    else:
        print(f"Unknown test type: {test_type}")
        print("Please specify: standalone, venv_only, or db_required")
        exit_code = 1
        
    sys.exit(exit_code)