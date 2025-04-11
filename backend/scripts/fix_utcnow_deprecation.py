#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix UTC Datetime Deprecation Warnings

This script updates all instances of the deprecated datetime.now(UTC) method
to use the recommended timezone-aware datetime.now(datetime.UTC) instead.

Usage:
    python -m backend.scripts.fix_utcnow_deprecation
"""

import os
import re
from pathlib import Path
import shutil
from datetime import datetime, UTC, UTC


def fix_utcnow_deprecation(fix_all=True, dry_run=False):
    """
    Fix deprecated datetime.now(UTC) calls in the codebase.
    
    Args:
        fix_all: If True, fix all occurrences in the codebase. If False, only fix ML services.
        dry_run: If True, don't actually write changes, just report what would be changed.
    """
    # Get the base directory
    base_dir = Path(__file__).resolve().parent.parent
    
    # Files to update
    target_files = []
    if fix_all:
        # Find all Python files in the project
        for root, _, files in os.walk(base_dir):
            path = Path(root)
            # Skip venv folders, __pycache__, etc.
            if any(part.startswith('.') or part == '__pycache__' 
                   or part == 'venv' or part == '.venv'
                   for part in path.parts):
                continue
            
            for file in files:
                if file.endswith('.py'):
                    target_files.append(path / file)
    else:
        # Only fix ML services directory
        ml_services_dir = base_dir / "app" / "core" / "services" / "ml"
        if not ml_services_dir.exists():
            print(f"ML services directory not found: {ml_services_dir}")
            return False
        
        target_files = list(ml_services_dir.glob("*.py"))
        if not target_files:
            print("No Python files found in ML services directory.")
            return False
    
    # Backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = base_dir / "backup" / f"utcnow_fix_{timestamp}"
    if not dry_run:
        backup_dir.mkdir(parents=True, exist_ok=True)
    
    updated_files = 0
    updated_calls = 0
    
    # Regex patterns
    import_patterns = [
        # From import with only datetime
        (r'from\s+datetime\s+import\s+datetime\b(?!,\s*UTC\b)', r'from datetime import datetime, UTC, UTC'),
        # From import with multiple items but not UTC
        (r'from\s+datetime\s+import\s+(.*?)\bdatetime\b(.*?)(?!\bUTC\b)', r'from datetime import \1datetime\2, UTC'),
        # Direct import
        (r'import\s+datetime\b', r'import datetime')
    ]
    
    # Function call pattern
    utcnow_patterns = [
        # Direct call on datetime module
        (r'datetime\.datetime\.utcnow\(\)', r'datetime.datetime.now(datetime.UTC)'),
        # Call after from import
        (r'datetime\.utcnow\(\)', r'datetime.now(UTC)')
    ]
    
    for file_path in target_files:
        rel_path = file_path.relative_to(base_dir)
        print(f"Processing {rel_path}...")
        
        # Read the content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Skip files without utcnow
        if 'utcnow' not in content:
            print(f"⏭️ No utcnow() calls found in {rel_path}")
            continue
        
        # Create a backup
        if not dry_run:
            backup_path = backup_dir / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
        
        old_content = content
        
        # First ensure proper imports
        for pattern, replacement in import_patterns:
            content = re.sub(pattern, replacement, content)
        
        # Then replace utcnow calls
        for pattern, replacement in utcnow_patterns:
            old_len = len(content)
            content = re.sub(pattern, replacement, content)
            new_len = len(content)
            if old_len != new_len:
                updated_calls += (old_len - new_len) // (len(pattern) - len(replacement))
        
        if content != old_content:
            if not dry_run:
                # Update the file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                updated_files += 1
                print(f"✅ Updated {rel_path}")
            else:
                updated_files += 1
                print(f"🔍 Would update {rel_path} (dry run)")
    
    print(f"\nProcess completed. {'Would update' if dry_run else 'Updated'} {updated_files} files with {updated_calls} utcnow() call replacements.")
    
    if not dry_run and updated_files > 0:
        print(f"Backups stored in: {backup_dir}")
    
    return updated_files > 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix deprecated datetime.now(UTC) calls")
    parser.add_argument("--ml-only", action="store_true", 
                       help="Only fix ML services directory")
    parser.add_argument("--dry-run", action="store_true",
                       help="Don't modify files, just show what would be changed")
    
    args = parser.parse_args()
    
    fix_utcnow_deprecation(fix_all=not args.ml_only, dry_run=args.dry_run)