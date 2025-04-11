#!/usr/bin/env python3
"""
Cache cleaner script.

This script removes __pycache__ directories and .pyc files
to resolve pytest "import file mismatch" errors.
"""
import os
import shutil

def clean_cache(directory):
    """Remove __pycache__ directories and .pyc files recursively."""
    count = 0
    for root, dirs, files in os.walk(directory):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            print(f"Removing {cache_dir}")
            shutil.rmtree(cache_dir)
            count += 1
            
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc'):
                pyc_file = os.path.join(root, file)
                print(f"Removing {pyc_file}")
                os.remove(pyc_file)
                count += 1
    
    return count

if __name__ == "__main__":
    app_dir = os.path.join(os.getcwd(), 'app')
    count = clean_cache(app_dir)
    print(f"Removed {count} cache files/directories")