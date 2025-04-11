#!/usr/bin/env python3
"""
Fix Integration Test Syntax Errors

This script fixes common syntax errors in integration tests:
1. Invalid 'async @pytest.mark.db_required' decorator ordering
2. Other malformed test syntax

Usage:
    python scripts/fix_integration_syntax.py
"""

import re
import sys
from pathlib import Path

def fix_decorator_ordering(file_path):
    """Fix incorrect async decorator ordering in test files."""
    file_content = file_path.read_text()
    
    # Fix invalid 'async @pytest.mark.db_required' ordering
    modified_content = re.sub(
        r'async\s+@pytest\.mark\.(\w+)',
        r'@pytest.mark.\1\nasync',
        file_content
    )
    
    # Also fix other common syntax errors
    modified_content = re.sub(
        r'class\s*$',
        r'class TestBase:',
        modified_content
    )
    
    # Write back if changes were made
    if modified_content != file_content:
        file_path.write_text(modified_content)
        return True
    return False

def scan_and_fix_tests():
    """Scan all integration test files and fix syntax issues."""
    tests_dir = Path('app/tests')
    integration_dir = tests_dir / 'integration'
    
    # Create integration directory if it doesn't exist
    integration_dir.mkdir(exist_ok=True, parents=True)
    
    # Find all integration test files
    test_files = list(tests_dir.glob('**/test_*integration*.py'))
    test_files.extend(integration_dir.glob('**/*.py'))
    
    fixed_count = 0
    
    for file_path in test_files:
        try:
            if fix_decorator_ordering(file_path):
                fixed_count += 1
                print(f"Fixed syntax in {file_path}")
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
    
    return fixed_count

if __name__ == "__main__":
    print("\n=== Fixing Integration Test Syntax ===\n")
    fixed_count = scan_and_fix_tests()
    print(f"\nFixed {fixed_count} files with syntax issues")
    sys.exit(0)