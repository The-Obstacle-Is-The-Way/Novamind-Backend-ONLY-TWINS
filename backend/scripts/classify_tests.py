#!/usr/bin/env python3
"""Test Classification Script for Novamind Backend.

This script analyzes test files to classify them by dependency level:
- standalone: No dependencies beyond Python stdlib
- venv_only: Requires packages but no external services
- db_required: Requires database or other external services

It can also add appropriate pytest markers to tests.
"""

import ast
import importlib.util
import os
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Root directory
ROOT_DIR = Path(__file__).parent.parent
TESTS_DIR = ROOT_DIR / "app" / "tests"

# Add project root to path for imports
sys.path.insert(0, str(ROOT_DIR))


class DependencyLevel(str, Enum):
    """Test dependency levels."""
    STANDALONE = "standalone"
    VENV_ONLY = "venv_only"
    DB_REQUIRED = "db_required"


# External dependencies that require services
DB_DEPENDENCIES = {
    "sqlalchemy", "asyncpg", "psycopg2", "alembic", "redis", 
    "aioredis", "motor", "beanie", "odmantic", "tortoise",
    "databases", "mysql", "boto3", "aioboto3", "moto",
    "aiohttp", "requests", "httpx", "websockets",
    "kafka", "confluent_kafka", "aiokafka", "elasticsearch"
}

# Dependencies that can be mocked but still require the package
VENV_DEPENDENCIES = {
    "fastapi", "pydantic", "starlette", "passlib", "jose", "jwt",
    "python-jose", "bcrypt", "argon2", "cryptography", "hashlib",
    "pyotp", "python-multipart", "jinja2", "email-validator", 
    "pyyaml", "ujson", "orjson", "msgpack", "numpy", "pandas",
    "sklearn", "tensorflow", "torch", "transformers", "spacy"
}

# Skip directories when scanning
SKIP_DIRS = {"__pycache__", ".mypy_cache", ".pytest_cache", ".hypothesis"}

# Import standard library modules to know what's stdlib
STDLIB_MODULES = set(sys.modules.keys())


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract imports from Python files."""
    
    def __init__(self):
        self.imports = set()
        self.from_imports = {}
        
    def visit_Import(self, node):
        for name in node.names:
            self.imports.add(name.name.split('.')[0])
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        if node.module is not None:
            module = node.module.split('.')[0]
            if node.level == 0:  # Absolute import
                self.imports.add(module)
            for name in node.names:
                if module not in self.from_imports:
                    self.from_imports[module] = []
                self.from_imports[module].append(name.name)
        self.generic_visit(node)


def parse_imports(file_path: Path) -> Tuple[Set[str], Dict[str, List[str]]]:
    """Parse imports from a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
            visitor = ImportVisitor()
            visitor.visit(tree)
            return visitor.imports, visitor.from_imports
        except SyntaxError:
            print(f"Error parsing {file_path}")
            return set(), {}


def detect_db_usage(file_content: str) -> bool:
    """Detect if file contains DB-related operations."""
    db_patterns = [
        r'Session\(',
        r'engine\.',
        r'Base\.',
        r'create_engine',
        r'sessionmaker',
        r'MetaData',
        r'Column\(',
        r'Table\(',
        r'relationship\(',
        r'execute\(',
        r'query\(',
        r'cursor\(',
        r'connect\(',
        r'fetchall\(',
        r'fetchone\(',
        r'commit\(',
        r'rollback\(',
        r'redis\.',
        r'r\.get',
        r'r\.set',
        r'bucket\.',
        r's3\.',
        r'dynamo\.',
    ]
    
    return any(re.search(pattern, file_content) for pattern in db_patterns)


def classify_test_file(file_path: Path) -> DependencyLevel:
    """Classify a test file by its dependency level."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract imports
    imports, from_imports = parse_imports(file_path)
    
    # Check for DB dependencies
    if any(dep in imports for dep in DB_DEPENDENCIES) or detect_db_usage(content):
        return DependencyLevel.DB_REQUIRED
    
    # Check for VENV dependencies
    if any(dep in imports for dep in VENV_DEPENDENCIES):
        return DependencyLevel.VENV_ONLY
    
    # If file imports only from app but not DB or VENV deps, need to check what those imports use
    app_imports = [imp for imp in imports if imp.startswith("app")]
    if app_imports:
        # This is a more complex case, we'd need to resolve transitive dependencies
        # For simplicity, we'll classify it as VENV_ONLY until proven otherwise
        return DependencyLevel.VENV_ONLY
    
    # If we get here, it's likely standalone
    # But check for pytest.mark.db_required or venv_only
    if "pytest.mark.db_required" in content or "@pytest.mark.db_required" in content:
        return DependencyLevel.DB_REQUIRED
    if "pytest.mark.venv_only" in content or "@pytest.mark.venv_only" in content:
        return DependencyLevel.VENV_ONLY
    if "pytest.mark.standalone" in content or "@pytest.mark.standalone" in content:
        return DependencyLevel.STANDALONE
    
    # Default: if in standalone directory, treat as standalone
    if "standalone" in str(file_path):
        return DependencyLevel.STANDALONE
    
    return DependencyLevel.VENV_ONLY


def find_tests(directory: Path) -> List[Path]:
    """Find all test files in a directory."""
    test_files = []
    
    for item in directory.glob("**/*.py"):
        if item.is_file() and (item.name.startswith("test_") or item.name.endswith("_test.py")):
            # Skip files in excluded directories
            if not any(skip_dir in str(item) for skip_dir in SKIP_DIRS):
                test_files.append(item)
    
    return test_files


def add_marker_to_file(file_path: Path, level: DependencyLevel) -> bool:
    """Add appropriate pytest marker to test file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if marker already exists
    marker_pattern = f"@pytest.mark.{level}"
    if marker_pattern in content:
        print(f"Marker {level} already exists in {file_path}")
        return False
    
    # Look for test classes and functions
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    
    # Find all test classes and functions
    test_classes = []
    test_functions = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            test_classes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            test_functions.append(node)
    
    if not test_classes and not test_functions:
        print(f"No test classes or functions found in {file_path}")
        return False
    
    # Add marker to first line of file before imports
    import_match = re.search(r"(import|from)\s+", content, re.MULTILINE)
    if import_match:
        insert_pos = import_match.start()
        new_content = (
            content[:insert_pos] + 
            f"import pytest\npytestmark = [pytest.mark.{level}]\n\n" + 
            content[insert_pos:]
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Added marker {level} to {file_path}")
        return True
    
    return False


def analyze_tests():
    """Analyze test files and print statistics."""
    test_files = find_tests(TESTS_DIR)
    classifications = {}
    
    for file in test_files:
        relative_path = file.relative_to(ROOT_DIR)
        level = classify_test_file(file)
        classifications[relative_path] = level
    
    # Print statistics
    stats = {level: 0 for level in DependencyLevel}
    for level in classifications.values():
        stats[level] += 1
    
    print("\n=== Test Classification Statistics ===")
    total = sum(stats.values())
    print(f"Total test files: {total}")
    for level, count in stats.items():
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"{level}: {count} ({percentage:.1f}%)")
    
    # Print files by level
    for level in DependencyLevel:
        print(f"\n=== {level.upper()} Tests ===")
        level_files = [path for path, l in classifications.items() if l == level]
        for path in sorted(level_files):
            print(f"- {path}")
    
    return classifications


def mark_tests(classifications):
    """Add pytest markers to test files based on classification."""
    print("\n=== Adding Markers to Tests ===")
    marked_count = 0
    
    for file_path, level in classifications.items():
        full_path = ROOT_DIR / file_path
        if add_marker_to_file(full_path, level):
            marked_count += 1
    
    print(f"\nAdded markers to {marked_count} files")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Classify tests by dependency level")
    parser.add_argument("--mode", choices=["analyze", "mark"], default="analyze",
                       help="Mode: analyze (just report) or mark (add pytest markers)")
    
    args = parser.parse_args()
    
    print("Analyzing test files...")
    classifications = analyze_tests()
    
    if args.mode == "mark":
        mark_tests(classifications)


if __name__ == "__main__":
    main()