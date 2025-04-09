#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix UTC Datetime Deprecation Warnings

This script updates all instances of the deprecated datetime.utcnow() method
to use the recommended timezone-aware datetime.now(datetime.UTC) instead.

Usage:
    python -m backend.scripts.fix_utcnow_deprecation
"""

import os
import re
from pathlib import Path
import shutil


def fix_utcnow_deprecation():
    """Fix deprecated datetime.utcnow() calls in the codebase."""
    # Get the base directory
    base_dir = Path(__file__).resolve().parent.parent
    ml_services_dir = base_dir / "app" / "core" / "services" / "ml"
    
    if not ml_services_dir.exists():
        print(f"ML services directory not found: {ml_services_dir}")
        return False
    
    # Files to update
    target_files = list(ml_services_dir.glob("*.py"))
    if not target_files:
        print("No Python files found in ML services directory.")
        return False
    
    # Backup directory
    backup_dir = base_dir / "backup" / "ml_services"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    updated_files = 0
    
    for file_path in target_files:
        print(f"Processing {file_path.relative_to(base_dir)}...")
        
        # Create a backup
        backup_path = backup_dir / file_path.name
        shutil.copy2(file_path, backup_path)
        
        # Read the content
        with open(file_path, "r") as f:
            content = f.read()
        
        # Check for datetime import
        has_import = re.search(r'from\s+datetime\s+import\s+datetime', content)
        if has_import:
            # Replace imports to include UTC
            content = re.sub(
                r'from\s+datetime\s+import\s+datetime',
                'from datetime import datetime, UTC',
                content
            )
            
            # Replace utcnow() calls
            old_content = content
            content = re.sub(
                r'datetime\.utcnow\(\)',
                'datetime.now(UTC)',
                content
            )
            
            if content != old_content:
                # Update the file
                with open(file_path, "w") as f:
                    f.write(content)
                
                updated_files += 1
                print(f"✅ Updated {file_path.name}")
            else:
                print(f"⚠️ No utcnow() calls found in {file_path.name}")
        else:
            print(f"⚠️ No datetime import found in {file_path.name}")
    
    print(f"\nProcess completed. Updated {updated_files} files.")
    print(f"Backups stored in: {backup_dir}")
    
    return True


if __name__ == "__main__":
    fix_utcnow_deprecation()