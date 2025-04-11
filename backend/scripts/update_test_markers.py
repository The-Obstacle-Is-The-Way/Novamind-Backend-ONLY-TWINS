#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Marker Updater for Novamind Backend.

This script automatically adds the appropriate pytest markers to test files
based on their dependency level. It ensures all tests are properly categorized
for dependency-based test execution.

Usage:
    python update_test_markers.py [--dry-run] [--verbose] [--target-dir DIR]
    
Options:
    --dry-run: Show what would be done without making changes
    --verbose: Show detailed information about what's being updated
    --target-dir: Target directory to update (default: app/tests)
"""

import argparse
import ast
import os
import re
import sys
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MarkerInfo:
    """Information about a test marker."""
    name: str
    priority: int  # Lower is higher priority
    pattern: str


# Constants for dependency levels, in order of precedence
MARKERS = [
    MarkerInfo("db_required", 3, r"@pytest\.mark\.db_required"),
    MarkerInfo("venv_only", 2, r"@pytest\.mark\.venv_only"),
    MarkerInfo("standalone", 1, r"@pytest\.mark\.standalone")
]

# Import patterns that indicate dependency levels
DB_IMPORTS = [
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
]

VENV_IMPORTS = [
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
]


def find_test_files(start_dir: str = "app/tests") -> List[str]:
    """Find all test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(start_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    return test_files


def get_current_markers(file_path: str) -> Set[str]:
    """Get the current pytest markers in a file."""
    markers = set()
    
    try:
        with open(file_path, "r") as f:
            content = f.read()
            
        for marker in MARKERS:
            if re.search(marker.pattern, content):
                markers.add(marker.name)
    except Exception as e:
        print(f"Error getting markers for {file_path}: {e}")
    
    return markers


def determine_marker_from_directory(file_path: str) -> Optional[str]:
    """Determine marker based on directory structure."""
    if "/standalone/" in file_path:
        return "standalone"
    if "/unit/" in file_path:
        return "venv_only"
    if any(x in file_path for x in ["/integration/", "/repository/", "/db/"]):
        return "db_required"
    return None


def determine_marker_from_imports(file_path: str) -> Optional[str]:
    """Determine marker based on imports in the file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
            
        # Check for db imports first (highest precedence)
        for pattern in DB_IMPORTS:
            if re.search(pattern, content):
                return "db_required"
                
        # Check for venv imports
        for pattern in VENV_IMPORTS:
            if re.search(pattern, content):
                return "venv_only"
                
        # If no characteristic imports found, default to standalone
        return "standalone"
    except Exception as e:
        print(f"Error analyzing imports in {file_path}: {e}")
        return None


def determine_required_marker(file_path: str) -> Optional[str]:
    """
    Determine the marker that should be applied to a test file.
    
    Precedence:
    1. Directory-based inference
    2. Import-based inference
    """
    # Try directory-based inference
    marker = determine_marker_from_directory(file_path)
    if marker:
        return marker
    
    # Fall back to import-based inference
    return determine_marker_from_imports(file_path)


def update_test_file(file_path: str, required_marker: str, dry_run: bool = True, verbose: bool = False) -> bool:
    """
    Update a test file with the appropriate pytest marker.
    
    Args:
        file_path: Path to the test file
        required_marker: The marker to add
        dry_run: If True, only print what would be done
        verbose: If True, print detailed information
        
    Returns:
        bool: True if file was or would be updated, False otherwise
    """
    # Read the file
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False
    
    # Get current markers
    current_markers = get_current_markers(file_path)
    
    # Skip if already has the required marker
    if required_marker in current_markers:
        if verbose:
            print(f"{file_path}: Already has {required_marker} marker")
        return False
    
    # Find appropriate marker pattern
    marker_pattern = next((m.pattern for m in MARKERS if m.name == required_marker), None)
    if not marker_pattern:
        print(f"Error: Unknown marker {required_marker}")
        return False
    
    # Check for conflicting markers
    for marker in current_markers:
        if marker != required_marker:
            # Remove existing marker, as we're adding a new one with higher precedence
            conflicting_pattern = next((m.pattern for m in MARKERS if m.name == marker), "")
            if conflicting_pattern:
                old_content = content
                content = re.sub(
                    rf"{conflicting_pattern}\n", 
                    "", 
                    content
                )
                if content != old_content and verbose:
                    print(f"{file_path}: Removed conflicting marker {marker}")
    
    # Find test functions and add marker
    test_fn_pattern = re.compile(r"^\s*def\s+test_\w+", re.MULTILINE)
    class_pattern = re.compile(r"^\s*class\s+Test\w+", re.MULTILINE)
    
    # Find all test functions and classes
    test_positions = []
    for match in test_fn_pattern.finditer(content):
        test_positions.append(match.start())
    
    class_positions = []
    for match in class_pattern.finditer(content):
        class_positions.append(match.start())
    
    # No changes needed if no test functions or classes found
    if not test_positions and not class_positions:
        if verbose:
            print(f"{file_path}: No test functions or classes found")
        return False
    
    # Prepare for modifications
    marker_str = f"@pytest.mark.{required_marker}\n"
    lines = content.splitlines(True)  # Keep line breaks
    modified_lines = []
    
    # Track if we need pytest import
    needs_pytest_import = "import pytest" not in content and "from pytest import" not in content
    
    # Process lines
    i = 0
    while i < len(lines):
        line = lines[i]
        modified_lines.append(line)
        
        # Check if this line starts a test function
        if test_fn_pattern.match(line) and i > 0:
            # Get indentation
            indent = re.match(r"^(\s*)", line).group(1)
            
            # Check previous line for markers
            prev_line = lines[i-1]
            if not any(re.search(m.pattern, prev_line) for m in MARKERS):
                modified_lines.insert(len(modified_lines)-1, f"{indent}{marker_str}")
        
        # Check if this line starts a test class
        if class_pattern.match(line) and i < len(lines) - 1:
            i += 1
            modified_lines.append(lines[i])  # Add the class declaration line
            
            # Add marker before any test methods in the class
            while i < len(lines) - 1:
                i += 1
                next_line = lines[i]
                
                if test_fn_pattern.match(next_line):
                    # Get indentation
                    indent = re.match(r"^(\s*)", next_line).group(1)
                    
                    # Check line for existing markers
                    has_marker = any(re.search(m.pattern, next_line) for m in MARKERS)
                    if not has_marker:
                        modified_lines.append(f"{indent}{marker_str}")
                
                modified_lines.append(next_line)
        
        i += 1
    
    # Add pytest import if needed
    if needs_pytest_import:
        import_idx = 0
        # Find where to insert import
        for idx, line in enumerate(modified_lines):
            if line.startswith("import ") or line.startswith("from "):
                import_idx = idx
        
        # Insert after last import
        modified_lines.insert(import_idx + 1, "import pytest\n")
    
    # Combine all lines back into content
    new_content = "".join(modified_lines)
    
    if dry_run:
        if verbose or content != new_content:
            print(f"{file_path}: Would add {required_marker} marker")
        return content != new_content
    
    # Write changes back to file
    if content != new_content:
        try:
            with open(file_path, "w") as f:
                f.write(new_content)
            print(f"{file_path}: Added {required_marker} marker")
            return True
        except Exception as e:
            print(f"Error writing to {file_path}: {e}")
            return False
    
    return False


def main():
    parser = argparse.ArgumentParser(description="Update test files with appropriate markers")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--verbose", action="store_true", help="Show detailed information")
    parser.add_argument("--target-dir", default="app/tests", help="Target directory to update")
    args = parser.parse_args()
    
    # Ensure we're in the backend directory
    current_dir = os.path.basename(os.getcwd())
    if current_dir != "backend":
        if os.path.exists("backend"):
            os.chdir("backend")
        else:
            print("Error: Script must be run from the backend directory or its parent")
            sys.exit(1)
    
    # Find test files
    test_files = find_test_files(args.target_dir)
    print(f"Found {len(test_files)} test files")
    
    # Classify and update files
    results = {
        "standalone": {"files": 0, "updated": 0},
        "venv_only": {"files": 0, "updated": 0},
        "db_required": {"files": 0, "updated": 0},
    }
    
    for file_path in test_files:
        required_marker = determine_required_marker(file_path)
        if not required_marker:
            print(f"Unable to determine marker for {file_path}")
            continue
            
        results[required_marker]["files"] += 1
        
        # Update file with marker
        if update_test_file(file_path, required_marker, dry_run=args.dry_run, verbose=args.verbose):
            results[required_marker]["updated"] += 1
    
    # Print summary
    print("\nSummary:")
    for marker, stats in results.items():
        action = "Would update" if args.dry_run else "Updated"
        print(f"{marker}: {stats['updated']} {action} out of {stats['files']} files")
    
    total_files = sum(stats["files"] for stats in results.values())
    total_updated = sum(stats["updated"] for stats in results.values())
    
    print(f"\nTotal: {total_updated} {action} out of {total_files} files")
    
    if args.dry_run:
        print("\nThis was a dry run. Use without --dry-run to apply changes.")


if __name__ == "__main__":
    main()