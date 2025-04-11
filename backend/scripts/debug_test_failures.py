#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Failure Debugger for Novamind Digital Twin Backend

This script analyzes failing tests, categorizes them by failure type,
and provides suggestions for fixing common issues.

Usage:
    python debug_test_failures.py --category standalone
    python debug_test_failures.py --category venv
    python debug_test_failures.py --category db
    python debug_test_failures.py --module patient
    python debug_test_failures.py --search sanitize_text
"""

import os
import re
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

# Path to the backend directory
BACKEND_DIR = Path(__file__).parent.parent
TESTS_DIR = BACKEND_DIR / "app" / "tests"

# Regular expressions for parsing pytest output
ERROR_PATTERN = re.compile(r'(ERROR|FAILED) ([\w\./]+)(::[\w\.:]+)+ - ([\w\.]+): (.+)$')
ASSERTION_PATTERN = re.compile(r'(ERROR|FAILED) ([\w\./]+)(::[\w\.:]+)+ - AssertionError: (.+)$')
TYPEERROR_PATTERN = re.compile(r'(ERROR|FAILED) ([\w\./]+)(::[\w\.:]+)+ - TypeError: (.+)$')
ATTRIBUTE_PATTERN = re.compile(r'(ERROR|FAILED) ([\w\./]+)(::[\w\.:]+)+ - AttributeError: (.+)$')

# Failure categories
FAILURE_CATEGORIES = {
    "interface_mismatch": {
        "title": "Interface Mismatches",
        "description": "Test failures due to changes in class interfaces, method signatures, or parameters",
        "patterns": [
            r"TypeError: .*__init__\(\) got an unexpected keyword argument",
            r"TypeError: .*\(\) missing \d+ required positional argument",
            r"AttributeError: '.*' object has no attribute '.*'"
        ]
    },
    "behavior_mismatch": {
        "title": "Behavior Mismatches",
        "description": "Test failures due to changes in expected behavior or logic",
        "patterns": [
            r"AssertionError: assert .* == .*",
            r"AssertionError: assert .* in .*",
            r"AssertionError: assert not .*"
        ]
    },
    "validation_error": {
        "title": "Validation Errors",
        "description": "Test failures due to validation issues or constraints",
        "patterns": [
            r"ValidationError: .*",
            r"ValueError: .*"
        ]
    },
    "dependency_missing": {
        "title": "Missing Dependencies",
        "description": "Test failures due to missing dependencies or imports",
        "patterns": [
            r"ImportError: .*",
            r"ModuleNotFoundError: .*"
        ]
    }
}

def parse_test_failures(output: str) -> List[Dict]:
    """Parse pytest output to extract test failures."""
    failures = []
    lines = output.split('\n')
    
    # Extract the summary line to get the count of failures
    summary_line = next((line for line in lines if "failed," in line and "error" in line), None)
    
    # Find the line before the first test result
    start_idx = next((i for i, line in enumerate(lines) if "FAILED" in line or "ERROR" in line), 0)
    
    # Extract failure details
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        
        # Check for different failure patterns
        match = ERROR_PATTERN.search(line)
        if match:
            failure_type = match.group(1)  # ERROR or FAILED
            file_path = match.group(2)
            test_name = match.group(3)[2:]  # Remove leading ::
            exception_type = match.group(4)
            message = match.group(5)
            
            failures.append({
                "type": failure_type,
                "file": file_path,
                "test": test_name,
                "exception": exception_type,
                "message": message,
                "category": categorize_failure(exception_type, message)
            })
            continue
        
        # Check for assertion errors
        match = ASSERTION_PATTERN.search(line)
        if match:
            failure_type = match.group(1)  # ERROR or FAILED
            file_path = match.group(2)
            test_name = match.group(3)[2:]  # Remove leading ::
            message = match.group(4)
            
            failures.append({
                "type": failure_type,
                "file": file_path,
                "test": test_name,
                "exception": "AssertionError",
                "message": message,
                "category": "behavior_mismatch"
            })
    
    return failures

def categorize_failure(exception_type: str, message: str) -> str:
    """Categorize a test failure based on the exception type and message."""
    # Check for each category
    for category, config in FAILURE_CATEGORIES.items():
        for pattern in config["patterns"]:
            if re.search(pattern, f"{exception_type}: {message}"):
                return category
    
    # Default category
    return "other"

def run_tests(category: str, module: Optional[str] = None, verbose: bool = False) -> str:
    """Run tests for a specific category and return the output."""
    cmd = ["python", "-m", "pytest"]
    
    # Add the category marker
    if category == "standalone":
        cmd.extend(["-m", "standalone"])
    elif category == "venv":
        cmd.extend(["-m", "venv_only"])
    elif category == "db":
        cmd.extend(["-m", "db_required"])
    
    # Add module pattern if specified
    if module:
        cmd.append(f"app/tests/*/{module}*")
    
    # Add verbose flag
    if verbose:
        cmd.append("-v")
    
    # Run pytest
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BACKEND_DIR))
    return result.stdout + result.stderr

def generate_failure_report(failures: List[Dict]) -> str:
    """Generate a report of test failures."""
    report = "\n" + "=" * 80 + "\n"
    report += "TEST FAILURE ANALYSIS REPORT\n"
    report += "=" * 80 + "\n\n"
    
    # Categorize failures
    categories = defaultdict(list)
    for failure in failures:
        categories[failure["category"]].append(failure)
    
    # Summary
    report += f"Total failures: {len(failures)}\n\n"
    report += "FAILURE BREAKDOWN:\n"
    report += "-" * 40 + "\n"
    for category, items in categories.items():
        config = FAILURE_CATEGORIES.get(category, {
            "title": category.replace("_", " ").title(),
            "description": "Uncategorized test failures"
        })
        report += f"{config['title']} ({len(items)})\n"
        report += f"  {config['description']}\n\n"
    
    # Detailed report for each category
    for category, items in categories.items():
        config = FAILURE_CATEGORIES.get(category, {
            "title": category.replace("_", " ").title(),
            "description": "Uncategorized test failures"
        })
        report += "\n" + "=" * 40 + "\n"
        report += f"{config['title'].upper()}\n"
        report += "=" * 40 + "\n\n"
        report += f"{config['description']}\n\n"
        
        # Group by exception type
        exceptions = defaultdict(list)
        for item in items:
            exceptions[item["exception"]].append(item)
        
        # Report for each exception type
        for exception, items in exceptions.items():
            report += f"\n{exception}:\n"
            report += "-" * len(exception) + "\n"
            
            # Group by failure message
            message_groups = defaultdict(list)
            for item in items:
                message_groups[item["message"]].append(item)
            
            # Report for each failure message
            for message, items in message_groups.items():
                report += f"\n  Message: {message}\n"
                report += "  Affected tests:\n"
                for item in items:
                    report += f"    - {item['file']}::{item['test']}\n"
                
                # Add suggestions for fixing
                report += "\n  Suggestions:\n"
                if exception == "TypeError" and "got an unexpected keyword argument" in message:
                    arg_name = re.search(r"got an unexpected keyword argument '([^']+)'", message)
                    if arg_name:
                        report += f"    1. Update the test to remove the '{arg_name.group(1)}' parameter\n"
                        report += f"    2. Check if the class interface has changed and update tests accordingly\n"
                
                elif exception == "TypeError" and "missing" in message and "required positional argument" in message:
                    report += "    1. Update the test to provide all required arguments\n"
                    report += "    2. Check the function/method signature for changes\n"
                
                elif exception == "AttributeError" and "has no attribute" in message:
                    attr_name = re.search(r"no attribute '([^']+)'", message)
                    if attr_name:
                        replacement = re.search(r"Did you mean: '([^']+)'", message)
                        if replacement:
                            report += f"    1. Replace '{attr_name.group(1)}' with '{replacement.group(1)}'\n"
                        else:
                            report += f"    1. Update the test to use the correct method name instead of '{attr_name.group(1)}'\n"
                        report += "    2. Check if the class interface has been refactored\n"
                
                elif exception == "AssertionError":
                    report += "    1. Update the test to match the current behavior\n"
                    report += "    2. Fix the implementation to match the expected behavior\n"
    
    # Add overall recommendations
    report += "\n" + "=" * 40 + "\n"
    report += "OVERALL RECOMMENDATIONS\n"
    report += "=" * 40 + "\n\n"
    
    # Recommendations based on failure categories
    if "interface_mismatch" in categories:
        report += "1. Update test fixtures and mocks to match current interfaces\n"
        report += "   - Check for class constructor parameter changes\n"
        report += "   - Update method names and signatures in tests\n\n"
    
    if "behavior_mismatch" in categories:
        report += "2. Address behavior mismatches\n"
        report += "   - Determine if tests or implementation should be updated\n"
        report += "   - For sanitizer tests: check sanitization rules and expected output\n\n"
    
    if "validation_error" in categories:
        report += "3. Fix validation errors\n"
        report += "   - Check data model changes that might affect validation\n"
        report += "   - Update tests to provide valid data according to current models\n\n"
    
    return report

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Debug test failures in Novamind tests")
    parser.add_argument("--category", choices=["standalone", "venv", "db"],
                      help="Test category to analyze")
    parser.add_argument("--module", help="Specific module to test (e.g., 'patient' or 'phi_sanitizer')")
    parser.add_argument("--search", help="Search for specific error messages")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", help="Output report to file")
    args = parser.parse_args()
    
    # Default to standalone if no category specified
    category = args.category or "standalone"
    
    # Run tests and collect failures
    print(f"Running {category} tests...")
    output = run_tests(category, args.module, args.verbose)
    
    # Parse failures
    failures = parse_test_failures(output)
    
    # Filter failures if search specified
    if args.search:
        failures = [f for f in failures if args.search.lower() in 
                   f"{f['file']} {f['test']} {f['exception']} {f['message']}".lower()]
    
    # Generate report
    report = generate_failure_report(failures)
    
    # Output report
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)

if __name__ == "__main__":
    main()