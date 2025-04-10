#!/usr/bin/env python3
"""
Test classification script for the Novamind Digital Twin Backend.

This script analyzes test files to determine their dependency level:
- Standalone: No dependencies beyond Python standard library
- VENV-dependent: Requires Python packages but no external services
- DB-dependent: Requires database connections or other external services

It can also update the test files with the appropriate pytest markers.
"""
import os
import sys
import argparse
import re
import ast
from typing import List, Dict, Set, Tuple, Optional
import logging
from pathlib import Path
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("test_classifier")

# Constants
BACKEND_DIR = Path(__file__).parent.parent
TEST_DIR = BACKEND_DIR / "app" / "tests"
STANDALONE_DIR = TEST_DIR / "standalone"

# Database-related import patterns
DB_IMPORT_PATTERNS = [
    r"import.*sqlalchemy",
    r"from sqlalchemy",
    r"import.*databases",
    r"from databases",
    r"import.*asyncpg",
    r"from asyncpg",
    r"import.*redis",
    r"from redis",
    r"import.*mongodb",
    r"from mongodb",
    r"import.*motor",
    r"from motor",
]

# Environment variable patterns that suggest DB usage
DB_ENV_PATTERNS = [
    r"DATABASE_URL",
    r"DB_HOST",
    r"DB_PORT",
    r"DB_USER",
    r"DB_PASSWORD",
    r"REDIS_URL",
    r"MONGO_URL",
]

# Function/class/variable names that suggest DB usage
DB_NAME_PATTERNS = [
    r"database",
    r"db",
    r"session",
    r"connection",
    r"query",
    r"execute",
    r"transaction",
    r"repository",
    r"store",
    r"redis",
    r"mongo",
]

# Marker patterns
STANDALONE_MARKER = "@pytest.mark.standalone"
VENV_MARKER = "@pytest.mark.venv_only"
DB_MARKER = "@pytest.mark.db_required"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Classify test files by dependency level")
    
    parser.add_argument("--update", action="store_true", help="Update test files with markers")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--dir", type=str, default=str(TEST_DIR), help="Directory to scan for test files")
    
    return parser.parse_args()


def contains_pattern(content: str, patterns: List[str]) -> bool:
    """Check if content contains any of the patterns."""
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def analyze_test_file(file_path: Path) -> Tuple[str, float]:
    """
    Analyze a test file to determine its dependency level.
    
    Returns:
        Tuple[str, float]: The dependency level and confidence score
    """
    # Read file content
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for existing markers
    if STANDALONE_MARKER in content:
        return "standalone", 1.0
    elif VENV_MARKER in content:
        return "venv", 1.0
    elif DB_MARKER in content:
        return "db", 1.0
    
    # Check for DB patterns
    if contains_pattern(content, DB_IMPORT_PATTERNS):
        return "db", 0.9
    
    if contains_pattern(content, DB_ENV_PATTERNS):
        return "db", 0.8
    
    if contains_pattern(content, DB_NAME_PATTERNS):
        return "db", 0.7
    
    # Check if it's in the standalone directory
    if str(STANDALONE_DIR) in str(file_path):
        return "standalone", 0.9
    
    # Try to parse the code and check for imports
    try:
        tree = ast.parse(content)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)
        
        # If only importing from stdlib or pytest, likely standalone
        non_stdlib_imports = []
        for imp in imports:
            if isinstance(imp, ast.Import):
                for name in imp.names:
                    if name.name not in sys.modules and not name.name.startswith("pytest"):
                        non_stdlib_imports.append(name.name)
            elif isinstance(imp, ast.ImportFrom):
                if imp.module not in sys.modules and not imp.module.startswith("pytest"):
                    non_stdlib_imports.append(imp.module)
        
        if not non_stdlib_imports:
            return "standalone", 0.8
        
        # Check for mocking - suggests venv dependency
        if "mock" in content.lower() or "patch" in content.lower():
            return "venv", 0.7
    except SyntaxError:
        # If we can't parse the file, default to venv-dependent
        pass
    
    # Default: assume venv-dependent
    return "venv", 0.6


def update_test_file(file_path: Path, dependency: str) -> bool:
    """
    Update a test file with the appropriate marker.
    
    Args:
        file_path: Path to the test file
        dependency: Dependency level ('standalone', 'venv', 'db')
        
    Returns:
        bool: True if file was updated, False otherwise
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if file already has the marker
    marker = ""
    if dependency == "standalone":
        marker = STANDALONE_MARKER
    elif dependency == "venv":
        marker = VENV_MARKER
    elif dependency == "db":
        marker = DB_MARKER
    
    if marker in content:
        return False
    
    # Remove other markers if present
    content = re.sub(r"@pytest\.mark\.(standalone|venv_only|db_required)", "", content)
    
    # Find test functions and classes
    test_function_pattern = r"(def\s+test_\w+\s*\()"
    test_class_pattern = r"(class\s+Test\w+\s*\(?)"
    
    # Add marker to test functions
    content = re.sub(
        test_function_pattern,
        f"{marker}\n\\1",
        content
    )
    
    # Add marker to test classes
    content = re.sub(
        test_class_pattern,
        f"{marker}\n\\1",
        content
    )
    
    # Write updated content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return True


def find_test_files(directory: Path) -> List[Path]:
    """Find all Python test files in the directory."""
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(Path(root) / file)
    return test_files


def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Find test files
    directory = Path(args.dir)
    test_files = find_test_files(directory)
    logger.info(f"Found {len(test_files)} test files in {directory}")
    
    # Analyze test files
    results = {
        "standalone": [],
        "venv": [],
        "db": []
    }
    
    for file_path in test_files:
        dependency, confidence = analyze_test_file(file_path)
        results[dependency].append((file_path, confidence))
        
        if args.verbose:
            logger.debug(f"{file_path}: {dependency} (confidence: {confidence:.2f})")
        
        # Update the file if requested
        if args.update:
            if update_test_file(file_path, dependency):
                logger.info(f"Updated {file_path} with {dependency} marker")
    
    # Print summary
    logger.info("\nClassification Summary:")
    logger.info(f"Standalone tests: {len(results['standalone'])}")
    logger.info(f"VENV-dependent tests: {len(results['venv'])}")
    logger.info(f"DB-dependent tests: {len(results['db'])}")
    
    # Suggest moving standalone tests
    if args.update and results['standalone']:
        logger.info("\nConsider moving standalone tests to the standalone directory:")
        for file_path, _ in results['standalone']:
            if str(STANDALONE_DIR) not in str(file_path):
                new_path = STANDALONE_DIR / file_path.name
                logger.info(f"  {file_path} -> {new_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())