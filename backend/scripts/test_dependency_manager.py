#!/usr/bin/env python3
"""
Test Dependency Manager for Novamind Backend.

This script helps manage test dependencies, analyze existing tests, and run tests based on 
their dependency requirements.

Usage:
    python -m backend.scripts.test_dependency_manager analyze
    python -m backend.scripts.test_dependency_manager count-markers
    python -m backend.scripts.test_dependency_manager run standalone|venv_only|db_required
"""
import os
import sys
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

# Root directory setup
ROOT_DIR = Path(__file__).parents[1]  # backend directory
TEST_DIR = ROOT_DIR / "app" / "tests"

# Define test dependency levels
DEPENDENCY_MARKERS = ['standalone', 'venv_only', 'db_required']
OTHER_MARKERS = ['unit', 'integration', 'security', 'slow', 'network_required', 'e2e']
ALL_MARKERS = DEPENDENCY_MARKERS + OTHER_MARKERS

def count_marker_usage() -> Dict[str, int]:
    """Count how many tests are marked with each marker."""
    marker_counts = {marker: 0 for marker in ALL_MARKERS}
    
    # Run pytest --collect-only with markers
    for marker in ALL_MARKERS:
        cmd = ["python", "-m", "pytest", str(TEST_DIR), f"-m", marker, "--collect-only", "-q"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Extract test count from output (looking for lines like "collected X items")
        match = re.search(r"collected (\d+) items", result.stdout)
        if match:
            count = int(match.group(1))
            marker_counts[marker] = count
    
    return marker_counts

def run_tests_by_dependency(dependency_level: str) -> int:
    """Run tests based on their dependency level."""
    if dependency_level not in DEPENDENCY_MARKERS:
        print(f"Error: {dependency_level} is not a valid dependency level.")
        print(f"Valid levels: {', '.join(DEPENDENCY_MARKERS)}")
        return 1
    
    print(f"\n=== Running {dependency_level.upper()} tests ===\n")
    
    # Set up target directories based on dependency level
    if dependency_level == 'standalone':
        target_dirs = [str(TEST_DIR / "standalone")]
    elif dependency_level == 'venv_only':
        target_dirs = [str(TEST_DIR / "unit")]
    elif dependency_level == 'db_required':
        target_dirs = [str(TEST_DIR / "integration")]
    else:
        target_dirs = [str(TEST_DIR)]
    
    # Build the pytest command
    cmd = ["python", "-m", "pytest"] + target_dirs + ["-m", dependency_level, "-v"]
    
    # Execute the command and return its exit code
    return subprocess.call(cmd)

def analyze_tests() -> Dict[str, List[str]]:
    """
    Analyze tests to suggest appropriate dependency markers.
    
    Returns a dictionary mapping dependency levels to lists of test files.
    """
    results = {marker: [] for marker in DEPENDENCY_MARKERS}
    
    # Find all test files
    test_files = []
    for root, _, files in os.walk(TEST_DIR):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    
    # Get the current marker usage per test file
    for test_file in test_files:
        rel_path = os.path.relpath(test_file, ROOT_DIR)
        
        # Simple heuristics based on file path and content
        if "standalone" in test_file:
            results['standalone'].append(rel_path)
        elif "unit" in test_file:
            results['venv_only'].append(rel_path)
        elif "integration" in test_file or "api" in test_file:
            results['db_required'].append(rel_path)
        else:
            # Look inside file for imports that might indicate dependencies
            with open(test_file, 'r') as f:
                content = f.read()
                
                # Look for database imports
                if re.search(r'import\s+.*\b(database|asyncpg|sqlalchemy)\b', content):
                    results['db_required'].append(rel_path)
                # Look for external API imports
                elif re.search(r'import\s+.*\b(requests|aiohttp|httpx)\b', content):
                    results['db_required'].append(rel_path)
                # Otherwise assume it could be venv_only
                else:
                    results['venv_only'].append(rel_path)
    
    return results

def print_analysis_report(analysis: Dict[str, List[str]]) -> None:
    """Print a report of the test analysis."""
    print("\n=== Test Analysis Report ===\n")
    
    for marker, files in analysis.items():
        print(f"{marker.upper()} tests: {len(files)}")
        for file in sorted(files[:5]):  # Show first 5 examples
            print(f"  - {file}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")
        print()
    
    # Print instructions for marking tests
    print("To mark tests with a dependency level, add the appropriate marker:")
    print("@pytest.mark.standalone  # No dependencies")
    print("@pytest.mark.venv_only   # Requires packages but no external services")
    print("@pytest.mark.db_required # Requires database connection")
    print()
    
    # Warning about unmarked tests
    print("Warning: Many tests aren't explicitly marked with dependency markers.")
    print("Consider adding dependency markers to improve test organization and CI/CD efficiency.")
    print()

def print_marker_usage_report(marker_counts: Dict[str, int]) -> None:
    """Print a report of marker usage."""
    print("\n=== Marker Usage Report ===\n")
    
    # Print dependency markers first
    print("Dependency Markers:")
    for marker in DEPENDENCY_MARKERS:
        print(f"  {marker:12}: {marker_counts[marker]} tests")
    
    # Print other markers
    print("\nOther Markers:")
    for marker in OTHER_MARKERS:
        print(f"  {marker:12}: {marker_counts[marker]} tests")
    
    # Total tests collected
    cmd = ["python", "-m", "pytest", str(TEST_DIR), "--collect-only", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    match = re.search(r"collected (\d+) items", result.stdout)
    total_tests = int(match.group(1)) if match else 0
    
    print(f"\nTotal tests: {total_tests}")
    print(f"Tests with dependency markers: {sum(marker_counts[m] for m in DEPENDENCY_MARKERS)}")
    print(f"Percentage of tests with dependency markers: {sum(marker_counts[m] for m in DEPENDENCY_MARKERS) / total_tests * 100:.1f}%")
    
    # Print warning if tests aren't marked
    if sum(marker_counts[m] for m in DEPENDENCY_MARKERS) < total_tests * 0.5:
        print("\nWarning: Less than 50% of tests have dependency markers.")
        print("Consider adding markers to improve test organization and CI/CD efficiency.")

def main():
    """Main function for the test dependency manager."""
    if len(sys.argv) < 2:
        print("Please specify a command: analyze, count-markers, or run")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "analyze":
        analysis = analyze_tests()
        print_analysis_report(analysis)
    
    elif command == "count-markers":
        marker_counts = count_marker_usage()
        print_marker_usage_report(marker_counts)
    
    elif command == "run":
        if len(sys.argv) < 3:
            print("Please specify a dependency level: standalone, venv_only, or db_required")
            sys.exit(1)
        
        dependency_level = sys.argv[2].lower()
        exit_code = run_tests_by_dependency(dependency_level)
        sys.exit(exit_code)
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: analyze, count-markers, run")
        sys.exit(1)

if __name__ == "__main__":
    main()