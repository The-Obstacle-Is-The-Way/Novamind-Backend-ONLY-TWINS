#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Datetime Test Issues

This script fixes common issues with datetime usage in tests, particularly:
1. Replace deprecated datetime.utcnow() with datetime.now(UTC)
2. Fix timezone-aware vs naive datetime comparisons

Usage:
    python -m backend.scripts.fix_datetime_tests
"""

import os
import re
from pathlib import Path
import shutil

def fix_datetime_tests():
    """Fix datetime issues in test files."""
    # Get the base directory
    base_dir = Path(__file__).resolve().parent.parent
    print(f"Base directory: {base_dir}")
    
    # Test directories to scan
    test_dirs = [
        base_dir / "app" / "tests",
    ]
    
    # Create backup directory
    backup_dir = base_dir / "backup" / "tests"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Patterns to fix
    patterns = [
        # Replace direct utcnow() calls
        (r'datetime\.utcnow\(\)', 'datetime.now(UTC)'),
        
        # Fix naive vs aware datetime comparison pattern 1
        (r'(\s*)timestamp = datetime\.fromisoformat\((.*?)\.rstrip\("Z"\)\)(.*?)assert \(datetime\.utcnow\(\) - timestamp\)\.total_seconds\(\) < (\d+)',
         r'\1timestamp = datetime.fromisoformat(\2.rstrip("Z"))\1# Use timezone-aware comparison to prevent TypeError\1from datetime import UTC\1assert (datetime.now(UTC) - timestamp).total_seconds() < \4'),
        
        # Import UTC along with datetime if it's not already imported
        (r'from datetime import datetime(?!\s*,\s*UTC)', r'from datetime import datetime, UTC'),
    ]
    
    total_files = 0
    updated_files = 0
    
    for test_dir in test_dirs:
        if not test_dir.exists():
            print(f"Test directory not found: {test_dir}")
            continue
        
        # Find all Python test files
        for root, _, files in os.walk(test_dir):
            for file in files:
                if file.endswith('.py') and 'test_' in file:
                    file_path = Path(root) / file
                    
                    # Read the content
                    with open(file_path, "r") as f:
                        content = f.read()
                    
                    total_files += 1
                    original_content = content
                    
                    # Apply each pattern
                    for pattern, replacement in patterns:
                        content = re.sub(pattern, replacement, content)
                    
                    # If content was changed, backup and update the file
                    if content != original_content:
                        # Create a backup
                        rel_path = file_path.relative_to(base_dir)
                        backup_path = backup_dir / rel_path
                        backup_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, backup_path)
                        
                        # Update the file
                        with open(file_path, "w") as f:
                            f.write(content)
                        
                        updated_files += 1
                        print(f"✅ Updated {file_path.relative_to(base_dir)}")
    
    print(f"\nProcess completed. Scanned {total_files} files, updated {updated_files} files.")
    print(f"Backups stored in: {backup_dir}")
    
    return True


if __name__ == "__main__":
    fix_datetime_tests()