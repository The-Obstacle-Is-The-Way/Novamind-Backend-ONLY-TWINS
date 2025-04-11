#!/usr/bin/env python3
"""
Novamind Digital Twin Test Analyzer and Fix Helper

This script analyzes test results and helps fix them by:
1. Identifying failing tests and their patterns
2. Running code quality tools (ruff, black, isort) to fix common issues
3. Providing a summary of test failures by category

Usage:
    python -m backend.scripts.fix_test_and_code_quality.py [--fix] [--level LEVEL]
"""

import os
import re
import sys
import subprocess
import argparse
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import xml.etree.ElementTree as ET

# Root directory setup
ROOT_DIR = Path(__file__).parents[1]  # backend directory
TEST_DIR = ROOT_DIR / "app" / "tests"
RESULTS_DIR = ROOT_DIR / "test-results"

# Define test directories by dependency level
TEST_LEVELS = {
    "standalone": [str(TEST_DIR / "standalone")],
    "venv_only": [str(TEST_DIR / "unit"), str(TEST_DIR / "venv_only")],
    "db_required": [str(TEST_DIR / "integration"), str(TEST_DIR / "api"), str(TEST_DIR / "e2e")]
}

# Error patterns to match and categorize
ERROR_PATTERNS = {
    "validation_error": [r"ValidationError", r"Field required", r"Input should be", r"Invalid value"],
    "import_error": [r"ImportError", r"ModuleNotFoundError", r"No module named"],
    "assertion_error": [r"AssertionError"],
    "attribute_error": [r"AttributeError"],
    "type_error": [r"TypeError"],
    "not_implemented": [r"NotImplementedError"],
    "connection_error": [r"ConnectionError", r"ConnectionRefused", r"Connection refused"],
    "database_error": [r"Database", r"SQL", r"Postgres", r"AsyncPG"],
    "file_not_found": [r"FileNotFoundError", r"No such file"],
    "syntax_error": [r"SyntaxError", r"IndentationError"],
    "recursion_error": [r"RecursionError"],
    "memory_error": [r"MemoryError"],
    "value_error": [r"ValueError"],
    "key_error": [r"KeyError"],
    "index_error": [r"IndexError"],
    "permission_error": [r"PermissionError"],
    "timeout_error": [r"TimeoutError"],
    "runtime_error": [r"RuntimeError", r"RuntimeWarning"],
    "zero_division_error": [r"ZeroDivisionError"],
}

def ensure_dirs():
    """Make sure necessary directories exist."""
    RESULTS_DIR.mkdir(exist_ok=True, parents=True)

def run_code_quality_tools(fix: bool = False) -> Dict:
    """Run code quality tools to analyze and optionally fix code issues."""
    results = {}
    
    # Change to the backend directory
    cwd = os.getcwd()
    os.chdir(str(ROOT_DIR))
    
    try:
        print("\n=== Running Code Quality Tools ===\n")
        
        # Run ruff for quick linting
        print("Running ruff...")
        cmd = ["ruff", "check", "app", "--statistics"]
        if fix:
            cmd.append("--fix")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            results["ruff"] = {
                "exit_code": result.returncode,
                "output": result.stdout,
                "errors": result.stderr
            }
            print(f"Ruff exit code: {result.returncode}")
            if result.stdout:
                print(result.stdout[:500] + ("..." if len(result.stdout) > 500 else ""))
        except FileNotFoundError:
            print("Ruff not found, installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "ruff"], check=True)
            result = subprocess.run(cmd, capture_output=True, text=True)
            results["ruff"] = {
                "exit_code": result.returncode,
                "output": result.stdout,
                "errors": result.stderr
            }
            
        # Run black for code formatting
        print("\nRunning black...")
        cmd = ["black", "app", "--check" if not fix else ""]
        if not fix:
            cmd = ["black", "app", "--check"]
        else:
            cmd = ["black", "app"]
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            results["black"] = {
                "exit_code": result.returncode,
                "output": result.stdout,
                "errors": result.stderr
            }
            print(f"Black exit code: {result.returncode}")
            if result.stdout:
                print(result.stdout[:500] + ("..." if len(result.stdout) > 500 else ""))
        except FileNotFoundError:
            print("Black not found, installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "black"], check=True)
            result = subprocess.run(cmd, capture_output=True, text=True)
            results["black"] = {
                "exit_code": result.returncode,
                "output": result.stdout,
                "errors": result.stderr
            }
            
        # Run isort for import sorting
        print("\nRunning isort...")
        cmd = ["isort", "app", "--check-only" if not fix else ""]
        if not fix:
            cmd = ["isort", "app", "--check-only"]
        else:
            cmd = ["isort", "app"]
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            results["isort"] = {
                "exit_code": result.returncode,
                "output": result.stdout,
                "errors": result.stderr
            }
            print(f"Isort exit code: {result.returncode}")
            if result.stdout:
                print(result.stdout[:500] + ("..." if len(result.stdout) > 500 else ""))
        except FileNotFoundError:
            print("Isort not found, installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "isort"], check=True)
            result = subprocess.run(cmd, capture_output=True, text=True)
            results["isort"] = {
                "exit_code": result.returncode,
                "output": result.stdout,
                "errors": result.stderr
            }
    
    finally:
        # Restore original directory
        os.chdir(cwd)
    
    return results

def analyze_xml_test_results() -> Dict:
    """Analyze XML test results from pytest."""
    results = {}
    
    for level in ["standalone", "venv_only", "db_required"]:
        xml_file = RESULTS_DIR / f"{level}-results.xml"
        if not xml_file.exists():
            results[level] = {
                "tests": 0,
                "failures": 0,
                "errors": 0,
                "skipped": 0,
                "passing": 0,
                "details": []
            }
            continue
            
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Extract summary information
            tests = int(root.attrib.get("tests", 0))
            failures = int(root.attrib.get("failures", 0))
            errors = int(root.attrib.get("errors", 0))
            skipped = int(root.attrib.get("skipped", 0))
            passing = tests - failures - errors - skipped
            
            # Collect details of failing tests
            details = []
            for testcase in root.findall(".//testcase"):
                # Check if this test failed or had an error
                failure = testcase.find("failure")
                error = testcase.find("error")
                
                if failure is not None or error is not None:
                    result = failure if failure is not None else error
                    test_name = f"{testcase.get('classname')}.{testcase.get('name')}"
                    message = result.get("message", "")
                    traceback = result.text or ""
                    
                    # Categorize error
                    error_type = "unknown"
                    for category, patterns in ERROR_PATTERNS.items():
                        if any(re.search(pattern, message + " " + traceback) for pattern in patterns):
                            error_type = category
                            break
                    
                    details.append({
                        "test": test_name,
                        "type": "failure" if failure is not None else "error",
                        "message": message,
                        "error_type": error_type,
                        "traceback": traceback[:500] + ("..." if len(traceback) > 500 else "")
                    })
            
            results[level] = {
                "tests": tests,
                "failures": failures,
                "errors": errors,
                "skipped": skipped,
                "passing": passing,
                "details": details
            }
            
        except Exception as e:
            print(f"Error parsing {xml_file}: {e}")
            results[level] = {
                "tests": 0,
                "failures": 0,
                "errors": 0,
                "skipped": 0,
                "passing": 0,
                "details": [],
                "parse_error": str(e)
            }
    
    return results

def run_tests(level: str, fix_mode: bool = False) -> Dict:
    """Run tests for a specific level and return results."""
    # Build the command
    cmd = ["python", "-m", "backend.scripts.run_tests_by_level", level]
    
    # Add timeout to prevent hanging
    timeouts = {
        "standalone": 120,
        "venv_only": 300,
        "db_required": 600
    }
    
    cmd.extend(["--timeout", str(timeouts.get(level, 300))])
    
    # Execute command
    print(f"\n=== Running {level.upper()} tests ===\n")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        xml_file = RESULTS_DIR / f"{level}-results.xml"
        if xml_file.exists():
            results = analyze_xml_test_results()
            return results.get(level, {})
        else:
            return {
                "tests": 0,
                "failures": 0,
                "errors": 0,
                "skipped": 0,
                "passing": 0,
                "details": [],
                "run_error": "XML results file not generated"
            }
            
    except Exception as e:
        print(f"Error running {level} tests: {e}")
        return {
            "tests": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "passing": 0,
            "details": [],
            "run_error": str(e)
        }

def summarize_by_error_type(test_results: Dict) -> Dict:
    """Summarize test failures by error type."""
    summary = {}
    
    for level, results in test_results.items():
        error_counts = {}
        file_counts = {}
        
        for detail in results.get("details", []):
            error_type = detail.get("error_type", "unknown")
            test_name = detail.get("test", "")
            
            # Count by error type
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            # Extract file path from test name
            file_path = test_name.split(".")[0].replace(".", "/")
            file_counts[file_path] = file_counts.get(file_path, 0) + 1
        
        summary[level] = {
            "by_error_type": error_counts,
            "by_file": file_counts
        }
    
    return summary

def suggest_fixes(summary: Dict, test_results: Dict) -> Dict:
    """Suggest fixes for common issues."""
    suggestions = {}
    
    for level, results in summary.items():
        level_suggestions = []
        
        # Handle validation errors - typically from schema mismatches
        if results["by_error_type"].get("validation_error", 0) > 0:
            level_suggestions.append({
                "type": "validation_error",
                "message": "Schema validation issues detected. Consider:",
                "actions": [
                    "Check required fields in Pydantic models",
                    "Verify field types match expected values",
                    "Look for UUID handling issues, string vs UUID objects",
                    "Ensure enum values are properly handled"
                ]
            })
        
        # Handle import errors
        if results["by_error_type"].get("import_error", 0) > 0:
            level_suggestions.append({
                "type": "import_error",
                "message": "Module import errors detected. Consider:",
                "actions": [
                    "Check package installations with 'pip list'",
                    "Verify import paths are correct",
                    "Look for circular imports",
                    "Check for installed vs imported package name mismatches"
                ]
            })
        
        # Handle assertion errors
        if results["by_error_type"].get("assertion_error", 0) > 0:
            level_suggestions.append({
                "type": "assertion_error",
                "message": "Test assertions are failing. Consider:",
                "actions": [
                    "Update test expectations to match current implementation",
                    "Fix implementation to meet test requirements",
                    "Check for test data consistency"
                ]
            })
        
        # Handle database errors
        if results["by_error_type"].get("database_error", 0) > 0:
            level_suggestions.append({
                "type": "database_error",
                "message": "Database connectivity issues detected. Consider:",
                "actions": [
                    "Verify database connection settings",
                    "Check PostgreSQL container is running",
                    "Ensure database migrations are applied",
                    "Check for proper transaction handling in tests"
                ]
            })
        
        # Handle recursion errors
        if results["by_error_type"].get("recursion_error", 0) > 0:
            level_suggestions.append({
                "type": "recursion_error",
                "message": "Infinite recursion detected. Consider:",
                "actions": [
                    "Look for circular references in object serialization",
                    "Check for mutual recursion between functions",
                    "Ensure proper base cases in recursive functions"
                ]
            })
        
        suggestions[level] = level_suggestions
    
    # Add specific suggestions based on failing tests
    for level, results in test_results.items():
        specific_suggestions = []
        
        for detail in results.get("details", []):
            test_name = detail.get("test", "")
            message = detail.get("message", "")
            traceback = detail.get("traceback", "")
            
            # Look for specific patterns in test failures
            if "ClinicalRuleEngine.register_rule_template() missing 1 required positional argument" in message:
                specific_suggestions.append({
                    "test": test_name,
                    "message": "Method signature mismatch in ClinicalRuleEngine class",
                    "fix": "Check the signature of the register_rule_template method - parameter is missing"
                })
            
            if "patient_id" in message and "UUID input should be a string, bytes or UUID object" in message:
                specific_suggestions.append({
                    "test": test_name,
                    "message": "UUID validation error for patient_id",
                    "fix": "Ensure patient_id is a valid UUID object or string representation"
                })
            
            if "maximum recursion depth exceeded" in traceback:
                specific_suggestions.append({
                    "test": test_name,
                    "message": "Infinite recursion detected in object serialization",
                    "fix": "Check for circular references in Pydantic models or dictionaries"
                })
        
        if level not in suggestions:
            suggestions[level] = []
        
        suggestions[level].extend(specific_suggestions)
    
    return suggestions

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Analyze and fix test issues')
    parser.add_argument('--fix', action='store_true', help='Apply fixes with code quality tools')
    parser.add_argument('--level', choices=['standalone', 'venv_only', 'db_required', 'all'], default='all',
                      help='Test level to analyze and fix')
    args = parser.parse_args()
    
    # Ensure necessary directories exist
    ensure_dirs()
    
    # If we're in fix mode, run code quality tools first
    if args.fix:
        code_quality_results = run_code_quality_tools(fix=True)
    else:
        code_quality_results = run_code_quality_tools(fix=False)
    
    # Run tests and analyze results
    test_results = {}
    
    if args.level == 'all':
        # Run all tests
        for level in ["standalone", "venv_only", "db_required"]:
            level_results = run_tests(level, fix_mode=args.fix)
            test_results[level] = level_results
    else:
        # Run specific level
        level_results = run_tests(args.level, fix_mode=args.fix)
        test_results[args.level] = level_results
    
    # Analyze and summarize results
    summary = summarize_by_error_type(test_results)
    suggestions = suggest_fixes(summary, test_results)
    
    # Print summary report
    print("\n\n=== TEST ANALYSIS SUMMARY ===\n")
    
    for level, results in test_results.items():
        print(f"\n{level.upper()} Tests:")
        print(f"  Total Tests: {results.get('tests', 0)}")
        print(f"  Passing: {results.get('passing', 0)}")
        print(f"  Failures: {results.get('failures', 0)}")
        print(f"  Errors: {results.get('errors', 0)}")
        print(f"  Skipped: {results.get('skipped', 0)}")
        
        if results.get('failures', 0) > 0 or results.get('errors', 0) > 0:
            print("\n  Error Type Summary:")
            for error_type, count in summary[level]["by_error_type"].items():
                print(f"    {error_type}: {count}")
            
            print("\n  Most Problematic Files:")
            sorted_files = sorted(summary[level]["by_file"].items(), key=lambda x: x[1], reverse=True)
            for file, count in sorted_files[:5]:
                print(f"    {file}: {count} issues")
        
        if level in suggestions and suggestions[level]:
            print("\n  Suggestions:")
            for suggestion in suggestions[level][:5]:  # Show top 5 suggestions
                if "type" in suggestion:
                    print(f"    - {suggestion['message']}")
                    for action in suggestion['actions'][:2]:  # Show top 2 actions
                        print(f"      * {action}")
                else:
                    print(f"    - Test: {suggestion['test']}")
                    print(f"      Issue: {suggestion['message']}")
                    print(f"      Fix: {suggestion['fix']}")
    
    # Save detailed results to file
    results_file = RESULTS_DIR / "test_analysis.json"
    with open(results_file, "w") as f:
        json.dump({
            "test_results": test_results,
            "summary": summary,
            "suggestions": suggestions,
            "code_quality": code_quality_results
        }, f, indent=2)
    
    print(f"\nDetailed analysis saved to {results_file}")
    
    if args.fix:
        print("\n\n=== FIXES APPLIED ===")
        print("Code formatting and linting issues have been fixed where possible.")
        print("Some test failures will need manual intervention. Review the suggestions above.")
    else:
        print("\n\n=== NEXT STEPS ===")
        print("To apply automatic fixes, run with the --fix flag:")
        print("  python -m backend.scripts.fix_test_and_code_quality.py --fix")
        print("\nManual fixes will be needed for some issues. Review the suggestions above.")

if __name__ == "__main__":
    main()