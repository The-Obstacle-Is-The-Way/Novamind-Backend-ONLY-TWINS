#!/usr/bin/env python3
"""
Comprehensive Test Runner for Novamind Backend

This script runs tests in three phases based on directory structure:
1. Standalone tests - No external dependencies
2. VENV tests - Requires virtualenv but not a full database
3. Integration tests - Requires a full database and possibly Docker

Usage:
    python scripts/run_tests.py [--standalone] [--venv] [--integration] [--all] [--coverage]
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime


class Color:
    """ANSI color codes for terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(message):
    """Print a formatted header."""
    print(f"\n{Color.BOLD}{Color.BLUE}{'=' * 60}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.BLUE}{message.center(60)}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.BLUE}{'=' * 60}{Color.ENDC}\n")


def print_section(message):
    """Print a formatted section header."""
    print(f"\n{Color.BOLD}{Color.YELLOW}{message}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.YELLOW}{'-' * len(message)}{Color.ENDC}\n")


def print_result(phase, success, time_taken=None):
    """Print a test phase result."""
    status = f"{Color.GREEN}PASSED{Color.ENDC}" if success else f"{Color.RED}FAILED{Color.ENDC}"
    time_info = f" in {time_taken:.2f}s" if time_taken else ""
    print(f"\n{Color.BOLD}{phase}: {status}{time_info}{Color.ENDC}\n")


def run_command(command, env=None):
    """Run a shell command and return the success status and output."""
    print(f"Running: {' '.join(command)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command, 
            env=env or os.environ.copy(),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        success = result.returncode == 0
        output = result.stdout
    except Exception as e:
        success = False
        output = str(e)
    
    time_taken = time.time() - start_time
    return success, output, time_taken


def run_standalone_tests(coverage=False):
    """Run standalone tests that don't require database or external services."""
    print_section("Running Standalone Tests")
    
    cmd = ['python', '-m', 'pytest', 'app/tests/standalone/']
    if coverage:
        cmd += ['--cov=app', '--cov-report=html:coverage_html/standalone_tests']
    
    success, output, time_taken = run_command(cmd)
    print(output)
    print_result("Standalone Tests", success, time_taken)
    
    return success


def run_venv_tests(coverage=False):
    """Run tests that require virtualenv but not a full database."""
    print_section("Running VENV Tests")
    
    cmd = ['python', '-m', 'pytest', 'app/tests/venv/']
    if coverage:
        cmd += ['--cov=app', '--cov-report=html:coverage_html/venv_tests']
    
    success, output, time_taken = run_command(cmd)
    print(output)
    print_result("VENV Tests", success, time_taken)
    
    return success


def run_integration_tests(coverage=False):
    """Run integration tests that require a full database and possibly Docker."""
    print_section("Running Integration Tests")
    
    # Set up any necessary environment for integration tests
    env = os.environ.copy()
    env["TESTING"] = "True"
    env["POSTGRES_USER"] = "test_user"
    env["POSTGRES_PASSWORD"] = "test_password"
    env["POSTGRES_DB"] = "test_db"
    
    # Check if Docker is available
    docker_available, docker_output, _ = run_command(['docker', '--version'])
    
    if docker_available:
        # Start test containers if needed
        print("Setting up Docker containers for testing...")
        docker_setup_success, docker_setup_output, _ = run_command(
            ['docker-compose', '-f', 'docker-compose.test.yml', 'up', '-d']
        )
        
        if not docker_setup_success:
            print(f"{Color.RED}Failed to set up Docker containers:{Color.ENDC}")
            print(docker_setup_output)
            return False
        
        print("Docker containers started successfully")
    else:
        print(f"{Color.YELLOW}Docker not available, skipping container setup{Color.ENDC}")
    
    cmd = ['python', '-m', 'pytest', 'app/tests/integration/']
    if coverage:
        cmd += ['--cov=app', '--cov-report=html:coverage_html/integration_tests']
    
    try:
        success, output, time_taken = run_command(cmd, env)
        print(output)
        print_result("Integration Tests", success, time_taken)
    finally:
        # Clean up Docker containers if we started them
        if docker_available:
            print("Cleaning up Docker containers...")
            run_command(['docker-compose', '-f', 'docker-compose.test.yml', 'down'])
    
    return success


def generate_coverage_report():
    """Generate a combined coverage report."""
    print_section("Generating Combined Coverage Report")
    
    cmd = ['python', '-m', 'coverage', 'combine']
    success, output, _ = run_command(cmd)
    
    if success:
        cmd = ['python', '-m', 'coverage', 'html', '-d', 'coverage_html/combined']
        success, output, _ = run_command(cmd)
        
        if success:
            cmd = ['python', '-m', 'coverage', 'report']
            success, output, _ = run_command(cmd)
            print(output)
    
    return success


def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Run Novamind Backend tests by test type")
    parser.add_argument('--standalone', action='store_true', help='Run standalone tests only')
    parser.add_argument('--venv', action='store_true', help='Run venv tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage reports')
    
    args = parser.parse_args()
    
    # If no specific test type is specified, run all tests
    if not (args.standalone or args.venv or args.integration or args.all):
        args.all = True
    
    print_header("Novamind Backend Test Runner")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run tests based on arguments
    if args.standalone or args.all:
        results['standalone'] = run_standalone_tests(args.coverage)
    
    if args.venv or args.all:
        # Standalone tests are a prerequisite for VENV tests
        if args.all and not results.get('standalone', False):
            print(f"{Color.YELLOW}Skipping VENV Tests due to failed Standalone Tests{Color.ENDC}")
            results['venv'] = False
        else:
            results['venv'] = run_venv_tests(args.coverage)
    
    if args.integration or args.all:
        # Both standalone and VENV tests are prerequisites for integration tests
        if args.all and not (results.get('standalone', False) and results.get('venv', False)):
            print(f"{Color.YELLOW}Skipping Integration Tests due to failed prerequisite tests{Color.ENDC}")
            results['integration'] = False
        else:
            results['integration'] = run_integration_tests(args.coverage)
    
    # Generate combined coverage report if needed
    if args.coverage and any(results.values()):
        generate_coverage_report()
    
    # Print summary
    print_header("Test Summary")
    
    for test_type, success in results.items():
        status = f"{Color.GREEN}PASSED{Color.ENDC}" if success else f"{Color.RED}FAILED{Color.ENDC}"
        print(f"{test_type.capitalize()} Tests: {status}")
    
    # Return non-zero exit code if any test failed
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())