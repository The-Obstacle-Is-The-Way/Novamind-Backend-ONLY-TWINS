#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Script to run pytest with coverage and identify modules with less than 50% coverage.
"""

import os
import sys
import subprocess
import re
import json
from pathlib import Path


def run_coverage():
    """Run pytest with coverage reporting."""
    print("Running pytest with coverage...")
    
    result = subprocess.run(
        ["pytest", "--cov=app", "--cov-report=term-missing"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode == 0


def parse_coverage_data():
    """Parse the coverage data from .coverage file."""
    try:
        # Convert .coverage to JSON
        subprocess.run(["coverage", "json"], check=True)
        
        # Read the JSON data
        with open(".coverage.json", "r") as f:
            data = json.load(f)
            
        return data
    except Exception as e:
        print(f"Error parsing coverage data: {e}")
        return None


def identify_low_coverage_modules(data, threshold=50):
    """Identify modules with coverage below the threshold."""
    if not data or "files" not in data:
        print("No coverage data found.")
        return []
    
    low_coverage = []
    for file_path, file_data in data["files"].items():
        # Skip __init__.py files
        if file_path.endswith("__init__.py"):
            continue
            
        # Skip frontend code
        if "/web/" in file_path:
            continue
            
        # Calculate coverage percentage
        if file_data["summary"]["num_statements"] > 0:
            covered = file_data["summary"]["covered_lines"]
            total = file_data["summary"]["num_statements"]
            coverage_pct = (covered / total) * 100
            
            if coverage_pct < threshold:
                low_coverage.append({
                    "path": file_path,
                    "coverage": coverage_pct,
                    "covered_lines": covered,
                    "total_lines": total,
                    "missing_lines": total - covered
                })
    
    # Sort by coverage (ascending)
    low_coverage.sort(key=lambda x: x["coverage"])
    
    return low_coverage


def prioritize_modules(modules):
    """
    Prioritize modules based on their importance for security and PHI handling.
    
    Returns a sorted list of modules with priority indicators.
    """
    priorities = {
        "app/infrastructure/security/": "HIGH",
        "app/core/utils/": "HIGH",
        "app/domain/entities/": "MEDIUM", 
        "app/domain/services/": "MEDIUM",
        "app/application/services/": "MEDIUM"
    }
    
    prioritized = []
    
    for module in modules:
        path = module["path"]
        
        # Determine priority
        priority = "LOW"
        for key, value in priorities.items():
            if key in path:
                priority = value
                break
                
        module_with_priority = module.copy()
        module_with_priority["priority"] = priority
        prioritized.append(module_with_priority)
    
    # Sort by priority (HIGH, MEDIUM, LOW) and then by coverage
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    prioritized.sort(key=lambda x: (priority_order[x["priority"]], x["coverage"]))
    
    return prioritized


def suggest_test_file_path(module_path):
    """Suggest a test file path for a module."""
    # Convert from app/path/to/module.py to tests/unit/path/to/test_module.py
    parts = module_path.split("/")
    
    # Handle app/ prefix
    if parts[0] == "app":
        parts = parts[1:]  # Remove 'app'
        
    module_name = parts[-1]
    module_dir = "/".join(parts[:-1])
    
    # Create test file name
    test_name = f"test_{module_name}"
    
    # Create test path
    test_path = f"tests/unit/{module_dir}/{test_name}"
    
    return test_path


def print_report(prioritized_modules):
    """Print a report of modules needing test coverage."""
    print("\n===== Modules Needing Test Coverage =====")
    
    if not prioritized_modules:
        print("All modules have adequate test coverage!")
        return
    
    # Print by priority group
    for priority in ["HIGH", "MEDIUM", "LOW"]:
        modules = [m for m in prioritized_modules if m["priority"] == priority]
        
        if modules:
            print(f"\n{priority} PRIORITY:")
            print("-" * 80)
            
            for module in modules:
                print(f"  {module['path']}")
                print(f"    Coverage: {module['coverage']:.2f}% ({module['covered_lines']}/{module['total_lines']} lines)")
                print(f"    Suggested test file: {suggest_test_file_path(module['path'])}")
                print()


def main():
    """Run the coverage check and report on modules needing coverage."""
    print("Starting coverage check...")
    
    # Run pytest with coverage
    run_coverage()
    
    # Parse coverage data
    coverage_data = parse_coverage_data()
    
    if not coverage_data:
        print("Failed to get coverage data.")
        return 1
    
    # Calculate overall coverage
    summary = coverage_data["totals"]
    overall_coverage = (summary["covered_lines"] / summary["num_statements"]) * 100
    
    print(f"\nOverall coverage: {overall_coverage:.2f}%")
    
    # Identify low coverage modules
    low_coverage = identify_low_coverage_modules(coverage_data)
    
    # Prioritize modules
    prioritized = prioritize_modules(low_coverage)
    
    # Print report
    print_report(prioritized)
    
    # Determine success based on overall coverage
    if overall_coverage >= 80:
        print("\n🎉 Target coverage of 80% has been achieved!")
        return 0
    else:
        print(f"\n❌ Coverage is at {overall_coverage:.2f}%. Target is 80%.")
        return 1


if __name__ == "__main__":
    sys.exit(main())