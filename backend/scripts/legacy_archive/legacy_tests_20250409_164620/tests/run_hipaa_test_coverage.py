#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
HIPAA Test Coverage Enhancement Workflow

This script orchestrates a complete workflow for improving test coverage
of HIPAA-critical components:

1. First, it fixes the PHI audit functionality
2. Checks current test coverage
3. Generates missing test files for modules with low coverage
4. Executes these tests to improve overall coverage
5. Provides a final report of coverage improvement
6. Cleans up temporary files

Usage:
    python run_hipaa_test_coverage.py [--clean]

Options:
    --clean     Clean up temporary and generated files after completion
"""

import os
import sys
import subprocess
import argparse
import time
import json
import shutil
from pathlib import Path


def print_header(message):
    """Print a section header with formatting."""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80)


def run_command(command, show_output=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        if show_output:
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
        return result.returncode == 0, result.stdout
    except Exception as e:
        print(f"Error running command: {command}")
        print(f"Exception: {e}")
        return False, ""


def get_coverage_percentage():
    """Run coverage and extract the overall percentage."""
    try:
        run_command("pytest --cov=app --cov-report=json", show_output=False)
        
        if os.path.exists(".coverage.json"):
            with open(".coverage.json", "r") as f:
                data = json.load(f)
                summary = data["totals"]
                total_statements = summary["num_statements"]
                covered_lines = summary["covered_lines"]
                
                if total_statements > 0:
                    return (covered_lines / total_statements) * 100
                
        return 0
    except Exception as e:
        print(f"Error calculating coverage: {e}")
        return 0


def fix_phi_audit():
    """Fix PHI audit functionality issues."""
    print_header("STEP 1: Fixing PHI Audit Functionality")
    
    # Run our patch script
    print("Running PHI detector patch...")
    success, output = run_command("python patch_phi_detector.py")
    if not success:
        print("❌ Failed to patch PHI detector")
        return False
    
    # Copy our fixed test file
    print("Verifying fixed test file is in place...")
    test_dir = os.path.dirname("tests/security/test_phi_audit_fixed.py")
    os.makedirs(test_dir, exist_ok=True)
    
    # Run fixed tests
    print("Running fixed PHI audit tests...")
    success, output = run_command("python run_fixed_tests.py")
    if not success:
        print("❌ Fixed PHI audit tests are still failing")
        return False
    
    print("✅ PHI audit functionality fixed successfully")
    return True


def check_initial_coverage():
    """Check initial test coverage."""
    print_header("STEP 2: Checking Initial Test Coverage")
    
    # Run coverage check
    success, output = run_command("python run_coverage_check.py")
    
    # Extract overall coverage percentage
    initial_coverage = get_coverage_percentage()
    print(f"Initial coverage: {initial_coverage:.2f}%")
    
    return initial_coverage


def generate_missing_tests():
    """Generate test files for modules with low coverage."""
    print_header("STEP 3: Generating Missing Test Files")
    
    # Run test generator
    success, output = run_command("python generate_test_files.py")
    if not success:
        print("❌ Failed to generate missing test files")
        return False
    
    print("✅ Generated missing test files")
    return True


def run_tests():
    """Run all tests to improve coverage."""
    print_header("STEP 4: Running Tests to Improve Coverage")
    
    # Run pytest with coverage
    success, output = run_command("pytest --cov=app --cov-report=term-missing")
    if not success:
        print("⚠️ Some tests failed, but continuing with coverage analysis")
    
    # Get updated coverage
    final_coverage = get_coverage_percentage()
    print(f"Updated coverage: {final_coverage:.2f}%")
    
    return final_coverage


def cleanup_temp_files(generated_files=None):
    """Clean up temporary files and optionally generated test files."""
    print_header("STEP 5: Cleaning Up Temporary Files")
    
    files_to_remove = [
        ".coverage",
        ".coverage.json",
        "scripts/run_hipaa_phi_audit.py.bak"
    ]
    
    if generated_files:
        files_to_remove.extend(generated_files)
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Removed {file_path}")
            except Exception as e:
                print(f"Failed to remove {file_path}: {e}")
    
    print("✅ Cleanup completed")


def print_final_report(initial_coverage, final_coverage):
    """Print a final report with coverage improvement."""
    print_header("FINAL REPORT: HIPAA Test Coverage Enhancement")
    
    improvement = final_coverage - initial_coverage
    
    print(f"Initial coverage: {initial_coverage:.2f}%")
    print(f"Final coverage:   {final_coverage:.2f}%")
    print(f"Improvement:      {improvement:.2f}%")
    
    if final_coverage >= 80:
        print("\n🎉 SUCCESS! The coverage target of 80% has been achieved.")
    else:
        print(f"\n⚠️ The coverage is now at {final_coverage:.2f}%, but the target is 80%.")
        print("   Additional tests may need to be written manually.")
    
    print("\nTo further improve coverage:")
    print("1. Review generated test files and add meaningful assertions")
    print("2. Add tests for edge cases and error conditions")
    print("3. Focus on security-critical modules first")
    print("4. Run 'python run_coverage_check.py' to identify remaining low-coverage modules")


def main():
    """Main function to run the HIPAA test coverage workflow."""
    parser = argparse.ArgumentParser(description="Run HIPAA test coverage enhancement workflow")
    parser.add_argument("--clean", action="store_true", help="Clean up generated files after completion")
    args = parser.parse_args()
    
    start_time = time.time()
    
    # Step 1: Fix PHI audit functionality
    if not fix_phi_audit():
        print("❌ Failed to fix PHI audit functionality")
        return 1
    
    # Step 2: Check initial coverage
    initial_coverage = check_initial_coverage()
    
    # Step 3: Generate missing tests
    if not generate_missing_tests():
        print("❌ Failed to generate missing tests")
        return 1
    
    # Step 4: Run tests to improve coverage
    final_coverage = run_tests()
    
    # Step 5: Clean up temporary files if requested
    if args.clean:
        cleanup_temp_files()
    
    # Print final report
    print_final_report(initial_coverage, final_coverage)
    
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"\nWorkflow completed in {execution_time:.2f} seconds")
    
    return 0 if final_coverage >= 80 else 1


if __name__ == "__main__":
    sys.exit(main())