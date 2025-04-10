#!/usr/bin/env python3
"""
Script to migrate standalone tests to the proper directory.

This script copies standalone tests from various directories to the dedicated
standalone test directory, avoiding duplicates and ensuring proper imports.
"""
import os
import sys
import shutil
import re
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("test_migrator")

# Constants
BACKEND_DIR = Path(__file__).parent.parent.parent
TEST_DIR = BACKEND_DIR / "app" / "tests"
STANDALONE_DIR = TEST_DIR / "standalone"
STANDALONE_MARKER = "@pytest.mark.standalone"

# List of tests to migrate, based on classification
STANDALONE_TESTS = [
    TEST_DIR / "e2e" / "test_patient_flow.py",
    TEST_DIR / "integration" / "api" / "test_patient_api.py",
    TEST_DIR / "integration" / "persistence" / "test_sqlalchemy_repositories.py",
    TEST_DIR / "unit" / "application" / "use_cases" / "test_create_patient.py",
    TEST_DIR / "unit" / "application" / "use_cases" / "test_generate_digital_twin.py",
    TEST_DIR / "unit" / "domain" / "test_digital_twin.py",
    TEST_DIR / "unit" / "presentation" / "api" / "test_patient_endpoints.py"
]

def ensure_standalone_marker(content):
    """Ensure the test file has the standalone marker."""
    # Check if the marker already exists
    if STANDALONE_MARKER in content:
        return content
    
    # Add the marker to test functions and classes
    test_function_pattern = r"(def\s+test_\w+\s*\()"
    test_class_pattern = r"(class\s+Test\w+\s*\(?)"
    
    # Add marker to test functions
    content = re.sub(
        test_function_pattern,
        f"{STANDALONE_MARKER}\n\\1",
        content
    )
    
    # Add marker to test classes
    content = re.sub(
        test_class_pattern,
        f"{STANDALONE_MARKER}\n\\1",
        content
    )
    
    return content

def migrate_test(src_path, dest_dir):
    """
    Migrate a test file from source to destination.
    
    Args:
        src_path: Path to the source test file
        dest_dir: Directory where the test file should be moved to
    
    Returns:
        bool: True if migration was successful, False otherwise
    """
    if not src_path.exists():
        logger.error(f"Source file does not exist: {src_path}")
        return False
    
    # Create destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    
    # Determine destination file name
    # If there's a naming conflict, use a prefix to avoid overwriting
    dest_filename = src_path.name
    if (dest_dir / dest_filename).exists():
        # Check if it's the same file (to avoid duplicate copies)
        with open(src_path, "r") as src_file, open(dest_dir / dest_filename, "r") as dest_file:
            if src_file.read() == dest_file.read():
                logger.info(f"File already exists and is identical: {dest_dir / dest_filename}")
                return True
        
        # It's a different file with the same name, so we need to rename
        # Use a prefix based on the source directory
        prefix = src_path.parent.name.replace("/", "_")
        dest_filename = f"{prefix}_{dest_filename}"
        
        # If it still exists, add a numeric suffix
        suffix = 1
        while (dest_dir / dest_filename).exists():
            dest_filename = f"{prefix}_{suffix}_{src_path.name}"
            suffix += 1
    
    # Copy the file
    dest_path = dest_dir / dest_filename
    
    try:
        # Read the source file
        with open(src_path, "r") as src_file:
            content = src_file.read()
        
        # Ensure the standalone marker is present
        content = ensure_standalone_marker(content)
        
        # Write the updated content to the destination
        with open(dest_path, "w") as dest_file:
            dest_file.write(content)
        
        logger.info(f"Successfully migrated test: {src_path} -> {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Error migrating test {src_path}: {str(e)}")
        return False

def main():
    """Main entry point."""
    success_count = 0
    error_count = 0
    
    logger.info(f"Starting migration of {len(STANDALONE_TESTS)} standalone tests")
    
    for test_path in STANDALONE_TESTS:
        if migrate_test(test_path, STANDALONE_DIR):
            success_count += 1
        else:
            error_count += 1
    
    logger.info(f"Migration complete: {success_count} tests migrated successfully, {error_count} errors")
    
    # Return non-zero exit code if there were errors
    return 1 if error_count > 0 else 0

if __name__ == "__main__":
    sys.exit(main())