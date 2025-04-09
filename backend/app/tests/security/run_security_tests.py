#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIPAA Security Test Runner

This script coordinates the execution of all HIPAA security tests
and generates comprehensive reports on compliance status.

Usage:
    python run_security_tests.py [options]
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configure terminal colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print formatted header text"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")

def print_section(text):
    """Print section header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'-' * 50}{Colors.ENDC}")

def get_test_files():
    """Get all security test files"""
    current_dir = Path(__file__).parent
    return sorted([
        f for f in current_dir.glob("test_*.py") 
        if f.is_file() and f.name.startswith("test_")
    ])

def run_security_test(test_file, verbose=False):
    """Run a single security test file with pytest"""
    test_name = test_file.stem
    print_section(f"Running {test_name}")
    
    # Prepare command
    cmd = [
        sys.executable, 
        "-m", 
        "pytest", 
        str(test_file),
        "-v",
        "--no-header",
        "--tb=short"
    ]
    
    if not verbose:
        cmd.append("-q")
    
    # Run the test
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    # Process results
    stdout = result.stdout
    stderr = result.stderr
    passed = result.returncode == 0
    
    # Count tests
    total_tests = stdout.count('::')
    passed_tests = stdout.count('PASSED')
    failed_tests = stdout.count('FAILED')
    skipped_tests = stdout.count('SKIPPED')
    
    # Print summary
    status = f"{Colors.GREEN}PASSED{Colors.ENDC}" if passed else f"{Colors.RED}FAILED{Colors.ENDC}"
    print(f"Status: {status}")
    
    if total_tests > 0:
        print(f"Tests: {total_tests} total, {passed_tests} passed, {failed_tests} failed, {skipped_tests} skipped")
    else:
        print(f"No tests found in {test_name}")
    
    print(f"Time: {end_time - start_time:.2f}s")
    
    if verbose:
        if stdout:
            print("\nOutput:")
            print(stdout)
        
        if stderr and not passed:
            print("\nErrors:")
            print(stderr)
    
    return {
        "test_file": test_file.name,
        "passed": passed,
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "skipped_tests": skipped_tests,
        "duration": end_time - start_time,
        "stdout": stdout,
        "stderr": stderr
    }

def generate_report(results, output_dir):
    """Generate a JSON report from test results"""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_dir, f"hipaa_security_report_{timestamp}.json")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "summary": {
            "total_files": len(results),
            "passed_files": sum(1 for r in results if r["passed"]),
            "total_tests": sum(r["total_tests"] for r in results),
            "passed_tests": sum(r["passed_tests"] for r in results),
            "failed_tests": sum(r["failed_tests"] for r in results),
            "skipped_tests": sum(r["skipped_tests"] for r in results),
            "total_duration": sum(r["duration"] for r in results)
        }
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    return report_file

def print_summary(results):
    """Print a summary of all test results"""
    print_header("HIPAA SECURITY TEST SUMMARY")
    
    # Calculate summary stats
    total_files = len(results)
    passed_files = sum(1 for r in results if r["passed"])
    total_tests = sum(r["total_tests"] for r in results)
    passed_tests = sum(r["passed_tests"] for r in results)
    failed_tests = sum(r["failed_tests"] for r in results)
    skipped_tests = sum(r["skipped_tests"] for r in results)
    
    # Print stats
    print(f"Files: {passed_files}/{total_files} passed")
    print(f"Tests: {passed_tests}/{total_tests} passed, {failed_tests} failed, {skipped_tests} skipped")
    
    # Print file details
    print("\nTest Files:")
    for result in results:
        status = f"{Colors.GREEN}PASSED{Colors.ENDC}" if result["passed"] else f"{Colors.RED}FAILED{Colors.ENDC}"
        file_name = result["test_file"]
        test_counts = f"{result['passed_tests']}/{result['total_tests']} tests passed"
        print(f"  {status} {file_name:<25} {test_counts}")
    
    # Print overall result
    overall_passed = all(r["passed"] for r in results)
    overall_status = f"{Colors.GREEN}PASSED{Colors.ENDC}" if overall_passed else f"{Colors.RED}FAILED{Colors.ENDC}"
    print(f"\nOverall Status: {overall_status}")
    
    # Print HIPAA compliance status
    hipaa_threshold = 0.80  # 80% pass rate required for HIPAA compliance
    if total_tests == 0:
        hipaa_status = f"{Colors.YELLOW}UNKNOWN{Colors.ENDC}"
    else:
        pass_rate = passed_tests / total_tests
        hipaa_status = f"{Colors.GREEN}COMPLIANT{Colors.ENDC}" if pass_rate >= hipaa_threshold else f"{Colors.RED}NON-COMPLIANT{Colors.ENDC}"
    
    print(f"HIPAA Security Status: {hipaa_status}")
    
    if not overall_passed:
        print(f"\n{Colors.YELLOW}Recommendation: Fix failing tests to ensure HIPAA compliance{Colors.ENDC}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="HIPAA Security Test Runner")
    
    parser.add_argument(
        "--output-dir",
        default="security-reports",
        help="Directory to save reports"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed test output"
    )
    
    parser.add_argument(
        "--tests",
        help="Comma-separated list of specific tests to run (e.g., encryption,jwt_auth)"
    )
    
    args = parser.parse_args()
    
    # Print welcome message
    print_header("HIPAA SECURITY TEST RUNNER")
    print("Running comprehensive security tests for Novamind concierge psychiatry platform\n")
    
    # Get test files
    all_test_files = get_test_files()
    
    if args.tests:
        # Filter test files by specified tests
        test_names = [f"test_{name.strip()}.py" for name in args.tests.split(",")]
        test_files = [f for f in all_test_files if f.name in test_names]
        if not test_files:
            print(f"{Colors.RED}Error: No matching test files found for: {args.tests}{Colors.ENDC}")
            return 1
    else:
        test_files = all_test_files
    
    print(f"Found {len(test_files)} security test files")
    
    # Run tests
    results = []
    for test_file in test_files:
        results.append(run_security_test(test_file, args.verbose))
    
    # Generate report
    generate_report(results, args.output_dir)
    
    # Print summary
    print_summary(results)
    
    # Return status code
    return 0 if all(r["passed"] for r in results) else 1

if __name__ == "__main__":
    sys.exit(main())