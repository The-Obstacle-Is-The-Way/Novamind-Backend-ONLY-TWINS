#!/usr/bin/env python3
"""
Test Organization Script

This script implements the reorganization of tests based on the classification report.
It moves test files to the correct directories based on their dependencies.
"""

import os
import shutil
import argparse
from pathlib import Path
import re

def ensure_directories_exist():
    """Ensure that the test directories exist."""
    directories = [
        "app/tests/standalone",
        "app/tests/venv",
        "app/tests/integration"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        # Create an __init__.py file if it doesn't exist
        init_file = Path(directory) / "__init__.py"
        if not init_file.exists():
            init_file.touch()


def extract_misclassified_tests(report_path="test-classification-report.md"):
    """Extract misclassified tests from the classification report."""
    if not os.path.exists(report_path):
        print(f"Report file {report_path} not found.")
        return {}
    
    with open(report_path, 'r') as f:
        content = f.read()
    
    # Parse the report to extract misclassified tests
    misclassified = {
        "standalone": [],
        "venv": [],
        "integration": []
    }
    
    # Extract sections for each test type
    sections = {}
    for test_type in misclassified.keys():
        pattern = f"### Should be {test_type.upper()} tests:(.*?)(?=###|$)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            sections[test_type] = match.group(1).strip()
    
    # Extract file paths from each section
    for test_type, section in sections.items():
        if not section:
            continue
        
        # Extract file paths using regex
        file_paths = re.findall(r'- (.*?) \(currently in', section)
        misclassified[test_type].extend(file_paths)
    
    return misclassified


def move_test_file(source_path, target_category, dry_run=True):
    """Move a test file to the correct directory."""
    if not os.path.exists(source_path):
        print(f"Source file {source_path} does not exist.")
        return False
    
    # Extract the filename
    filename = os.path.basename(source_path)
    
    # Construct the target path
    target_dir = f"app/tests/{target_category}"
    target_path = os.path.join(target_dir, filename)
    
    # Create the target directory if it doesn't exist
    if not os.path.exists(target_dir):
        if not dry_run:
            os.makedirs(target_dir, exist_ok=True)
        print(f"Created directory: {target_dir}")
    
    # Move the file
    if dry_run:
        print(f"Would move {source_path} to {target_path}")
    else:
        try:
            # Ensure the target directory exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            # Copy the file to the new location
            shutil.copy2(source_path, target_path)
            # Optionally remove the original file
            # os.remove(source_path)
