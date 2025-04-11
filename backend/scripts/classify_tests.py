#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Classification Script for Novamind Backend.

This script analyzes test files to categorize them by dependency level:
- standalone: Tests that have no external dependencies
- venv_only: Tests that require Python packages but no external services
- db_required: Tests that require database connections

Usage:
    python classify_tests.py [--update] [--report]
    
Options:
    --update: Add appropriate markers to test files
    --report: Generate a report of test classification
"""

import argparse
import ast
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


# Constants for dependency classification
class DependencyLevel:
    STANDALONE = "standalone"
    VENV_ONLY = "venv_only"
    DB_REQUIRED = "db_required"
    UNKNOWN = "unknown"


# Import patterns that indicate dependency levels
IMPORT_PATTERNS = {
    # Database imports suggest DB dependency
    DependencyLevel.DB_REQUIRED: [
        r"import\s+asyncpg",
        r"from\s+asyncpg",
        r"import\s+sqlalchemy",
        r"from\s+sqlalchemy",
        r"import\s+redis",
        r"from\s+redis",
        r"import\s+motor",
        r"from\s+motor",
        r"from\s+app\.infrastructure\.database",
        r"from\s+app\.infrastructure\.repositories",
    ],
    # Core package imports may be venv-only
    DependencyLevel.VENV_ONLY: [
        r"import\s+fastapi",
        r"from\s+fastapi",
        r"import\s+pydantic",
        r"from\s+pydantic",
        r"import\s+starlette",
        r"from\s+starlette",
        r"import\s+passlib",
        r"from\s+passlib",
        r"import\s+jwt",
        r"from\s+jwt",
    ],
}

# Marker patterns to detect existing pytest markers
MARKER_PATTERNS = {
    DependencyLevel.STANDALONE: r"@pytest\.mark\.standalone",
    DependencyLevel.VENV_ONLY: r"@pytest\.mark\.venv_only",
    DependencyLevel.DB_REQUIRED: r"@pytest\.mark\.db_required",
}


def find_test_files(start_dir: str = "app/tests") -> List[str]:
    """Find all test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(start_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    return test_files


def analyze_imports(file_path: str) -> Tuple[Set[str], Set[str]]:
    """
    Analyze a file for import statements to determine dependencies.
    
    Returns:
        Tuple of (imported_modules, from_imports)
    """
    imported_modules = set()
    from_imports = set()
    
    try:
        with open(file_path, "r") as f:
            file_content = f.read()
            
        tree = ast.parse(file_content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imported_modules.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:  # Handles 'from x import y' (not 'from . import y')
                    module_path = node.module
                    for name in node.names:
                        from_imports.add(f"{module_path}.{name.name}")
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
    
    return imported_modules, from_imports


def get_current_markers(file_path: str) -> Set[str]:
    """Get the current pytest markers in a file."""
    markers = set()
    
    try:
        with open(file_path, "r") as f:
            content = f.read()
            
        for level, pattern in MARKER_PATTERNS.items():
            if re.search(pattern, content):
                markers.add(level)
    except Exception as e:
        print(f"Error getting markers for {file_path}: {e}")
    
    return markers


def classify_test_file(file_path: str) -> str:
    """
    Classify a test file based on its imports and content.
    
    Returns:
        A string representing the dependency level: 'standalone', 'venv_only', 'db_required', or 'unknown'
    """
    # Read file content
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return DependencyLevel.UNKNOWN
    
    # Check if it already has markers
    current_markers = get_current_markers(file_path)
    if DependencyLevel.DB_REQUIRED in current_markers:
        return DependencyLevel.DB_REQUIRED
    if DependencyLevel.VENV_ONLY in current_markers:
        return DependencyLevel.VENV_ONLY
    if DependencyLevel.STANDALONE in current_markers:
        return DependencyLevel.STANDALONE
    
    # Try to determine dependency level from imports
    for level, patterns in IMPORT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content):
                return level
    
    # Check directory structure
    if "/standalone/" in file_path:
        return DependencyLevel.STANDALONE
    if "/unit/" in file_path:
        return DependencyLevel.VENV_ONLY
    if "/integration/" in file_path or "/repository/" in file_path or "/db/" in file_path:
        return DependencyLevel.DB_REQUIRED
    
    # If nothing matches, default to venv_only
    return DependencyLevel.VENV_ONLY


def update_test_file(file_path: str, dependency_level: str) -> bool:
    """
    Update a test file with the appropriate pytest marker.
    
    Args:
        file_path: Path to the test file
        dependency_level: The dependency level to add as a marker
        
    Returns:
        bool: True if file was updated, False otherwise
    """
    if dependency_level == DependencyLevel.UNKNOWN:
        return False
    
    # Read the file
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path} for update: {e}")
        return False
    
    # Check if marker already exists
    marker_pattern = MARKER_PATTERNS.get(dependency_level, "")
    if any(re.search(marker_pattern, line) for line in lines):
        return False  # Marker already exists
    
    # Find locations to insert marker
    new_lines = []
    test_fn_pattern = re.compile(r"^\s*def\s+test_\w+")
    
    for i, line in enumerate(lines):
        if test_fn_pattern.match(line) and i > 0:
            # Add marker before test function
            indent = re.match(r"^(\s*)", line).group(1)
            new_lines.append(f"{indent}@pytest.mark.{dependency_level}\n")
        new_lines.append(line)
    
    # Check if we need to add pytest import
    if not any("import pytest" in line for line in lines):
        # Add import at top, after docstring if present
        docstring_end = 0
        for i, line in enumerate(new_lines):
            if i == 0 and line.strip().startswith('"""'):
                # Skip to end of docstring
                for j in range(i + 1, len(new_lines)):
                    if '"""' in new_lines[j]:
                        docstring_end = j + 1
                        break
        
        new_lines.insert(docstring_end, "import pytest\n")
        if docstring_end > 0 and new_lines[docstring_end - 1].strip() != "":
            new_lines.insert(docstring_end, "\n")
    
    # Write updated content
    try:
        with open(file_path, "w") as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")
        return False


def generate_report(classifications: Dict[str, List[str]]) -> str:
    """Generate a report of test classifications."""
    report = "# Novamind Backend Test Classification Report\n\n"
    
    total_tests = sum(len(files) for files in classifications.values())
    report += f"Total Test Files: {total_tests}\n\n"
    
    for level, files in classifications.items():
        report += f"## {level.upper()} Tests: {len(files)}\n\n"
        if files:
            for file in sorted(files):
                report += f"- {file}\n"
        else:
            report += "No tests in this category.\n"
        report += "\n"
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Classify test files by dependency level")
    parser.add_argument("--update", action="store_true", help="Update test files with dependency markers")
    parser.add_argument("--report", action="store_true", help="Generate a classification report")
    parser.add_argument("--dir", default="app/tests", help="Directory to scan for test files")
    args = parser.parse_args()
    
    # Ensure we're in the backend directory
    current_dir = os.path.basename(os.getcwd())
    if current_dir != "backend":
        if os.path.exists("backend"):
            os.chdir("backend")
        else:
            print("Error: Script must be run from the backend directory or its parent")
            sys.exit(1)
    
    # Find and classify test files
    test_files = find_test_files(args.dir)
    classifications = defaultdict(list)
    
    for file in test_files:
        level = classify_test_file(file)
        classifications[level].append(file)
        
        if args.update and level != DependencyLevel.UNKNOWN:
            if update_test_file(file, level):
                print(f"Updated {file} with {level} marker")
    
    # Print summary
    print("\nTest Classification Summary:")
    for level, files in classifications.items():
        print(f"{level}: {len(files)} files")
    
    if args.report:
        report = generate_report(classifications)
        report_path = "test-classification-report.md"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\nDetailed report written to {report_path}")


if __name__ == "__main__":
    main()