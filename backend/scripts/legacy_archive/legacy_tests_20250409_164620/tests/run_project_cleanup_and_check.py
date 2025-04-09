#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIPAA Compliance Project Cleanup and Coverage Check

This script runs the project cleanup and test coverage check in sequence,
ensuring the codebase is both organized according to Clean Architecture principles
and meets the 80% coverage requirements for HIPAA compliance.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Define color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    """Print a formatted header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD} {message} {Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(message):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠️ {message}{Colors.ENDC}")

def print_error(message):
    """Print an error message."""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def run_script(script_path, description):
    """Run a Python script and report success/failure."""
    print_header(f"RUNNING: {description}")
    
    # Make sure the script exists
    if not Path(script_path).exists():
        print_error(f"Script not found: {script_path}")
        return False
        
    # Run the script
    start_time = time.time()
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    end_time = time.time()
    
    # Print output
    print(result.stdout)
    
    if result.stderr:
        print_error("Errors encountered:")
        print(result.stderr)
    
    # Report result
    if result.returncode == 0:
        print_success(f"{description} completed successfully in {end_time - start_time:.2f} seconds")
        return True
    else:
        print_error(f"{description} failed with exit code {result.returncode}")
        return False

def backup_project():
    """Create a backup of the project files."""
    print_header("CREATING PROJECT BACKUP")
    
    backup_dir = Path("./project_backup")
    backup_dir.mkdir(exist_ok=True)
    
    # Use the system's copy command (cp on Unix, xcopy on Windows)
    if os.name == 'nt':  # Windows
        cmd = f'xcopy /E /I /Y . {backup_dir} /EXCLUDE:venv\\.git'
    else:  # Unix
        cmd = f'cp -r --exclude=venv --exclude=.git . {backup_dir}'
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print_success(f"Project backup created at {backup_dir}")
        return True
    else:
        print_error("Failed to create project backup")
        print(result.stderr)
        return False

def verify_cleanup():
    """Verify that the cleanup was successful."""
    print_header("VERIFYING PROJECT STRUCTURE")
    
    # Check for py files in root (excluding main.py and this script)
    root_dir = Path('.')
    py_files_in_root = [f for f in root_dir.glob('*.py') 
                        if f.name not in ['main.py', 'run_project_cleanup_and_check.py', 'cleanup_project_structure.py']]
    
    # Check for .ini files in root (excluding pytest.ini)
    ini_files_in_root = [f for f in root_dir.glob('*.ini') 
                         if f.name not in ['pytest.ini', 'alembic.ini']]
    
    # Check for expected directories
    expected_dirs = ['scripts', 'scripts/security_utils', 'config', 'tests']
    missing_dirs = [d for d in expected_dirs if not Path(d).exists()]
    
    # Report findings
    if py_files_in_root:
        print_warning(f"Found {len(py_files_in_root)} Python files in root directory:")
        for f in py_files_in_root:
            print(f"  - {f.name}")
    else:
        print_success("No unexpected Python files in root directory")
        
    if ini_files_in_root:
        print_warning(f"Found {len(ini_files_in_root)} INI files in root directory:")
        for f in ini_files_in_root:
            print(f"  - {f.name}")
    else:
        print_success("No unexpected INI files in root directory")
        
    if missing_dirs:
        print_warning(f"Missing expected directories:")
        for d in missing_dirs:
            print(f"  - {d}")
    else:
        print_success("All expected directories exist")
    
    # Overall verdict
    if not (py_files_in_root or ini_files_in_root or missing_dirs):
        print_success("Project structure verification passed!")
        return True
    else:
        print_warning("Project structure has some issues that need attention")
        return False

def main():
    """Main function to run cleanup and check processes."""
    print_header("🧹 STARTING HIPAA COMPLIANCE PROJECT CLEANUP AND CHECK 🧹")
    
    # Create backup
    backup_success = backup_project()
    if not backup_success:
        if input("Backup failed. Continue anyway? (y/n): ").lower() != 'y':
            sys.exit(1)
    
    # Run cleanup script
    cleanup_success = run_script('cleanup_project_structure.py', "Project Structure Cleanup")
    
    # Verify cleanup
    if cleanup_success:
        verify_cleanup()
    
    # Run coverage check
    coverage_success = run_script('scripts/check_test_coverage.py', "HIPAA Test Coverage Check")
    
    # Print final summary
    print_header("🏁 CLEANUP AND CHECK PROCESS COMPLETE 🏁")
    
    if cleanup_success:
        print_success("Project structure has been organized according to Clean Architecture principles")
    else:
        print_error("Project structure cleanup failed")
        
    if coverage_success:
        print_success("Test coverage meets HIPAA compliance requirements")
    else:
        print_warning("Test coverage check failed or did not meet requirements")
    
    print("\nRefer to HIPAA_TEST_COVERAGE_README.md for documentation on maintaining\n"
          "proper project structure and HIPAA compliance test coverage.")

if __name__ == "__main__":
    main()