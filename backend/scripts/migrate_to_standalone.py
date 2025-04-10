#!/usr/bin/env python3
"""
Unit Test Migration Tool for Standalone Tests

This script helps migrate unit tests to the standalone test format.
It analyzes existing unit tests, identifies those suitable for migration,
and assists in converting them to the standalone format.

Usage:
    python migrate_to_standalone.py [--file <path_to_test_file>] [--dry-run]

Options:
    --file     Path to a specific test file to migrate
    --dry-run  Analyze and report changes without making them
"""

import os
import sys
import re
import ast
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Migrate unit tests to standalone tests")
    parser.add_argument("--file", help="Path to a specific test file to migrate")
    parser.add_argument("--dry-run", action="store_true", help="Analyze without making changes")
    return parser.parse_args()


class TestModuleTransformer(ast.NodeTransformer):
    """AST transformer to add standalone marker and modify imports."""
    
    def __init__(self):
        self.has_standalone_marker = False
        self.pytest_import_exists = False
        self.unittest_import_exists = False
        self.test_classes = []
        self.test_functions = []
        
    def visit_ImportFrom(self, node):
        # Check for pytest import
        if node.module == 'pytest':
            self.pytest_import_exists = True
        return node
    
    def visit_Import(self, node):
        # Check for unittest import
        for alias in node.names:
            if alias.name == 'unittest':
                self.unittest_import_exists = True
        return node
    
    def visit_ClassDef(self, node):
        # Track test classes
        if node.name.startswith('Test'):
            self.test_classes.append(node.name)
            # Check for standalone marker
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Attribute) and decorator.attr == 'standalone':
                    self.has_standalone_marker = True
        return self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        # Track test functions and check for standalone marker
        if node.name.startswith('test_'):
            self.test_functions.append(node.name)
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Attribute) and decorator.attr == 'standalone':
                    self.has_standalone_marker = True
                elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'mark' and isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == 'pytest':
                    if any(isinstance(kw, ast.keyword) and kw.arg == 'standalone' for kw in decorator.keywords):
                        self.has_standalone_marker = True
        return self.generic_visit(node)


def analyze_test_file(file_path: str) -> Dict[str, Any]:
    """Analyze a test file for migration suitability."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse the file
    tree = ast.parse(content)
    
    # Use the transformer to analyze
    transformer = TestModuleTransformer()
    transformer.visit(tree)
    
    # Check for database dependencies
    has_db_dependency = any(db_pattern in content for db_pattern in [
        'db_session', 'database', 'session', 'sqlalchemy',
        'repository', 'persist', 'alembic', 'migration'
    ])
    
    # Check for network dependencies
    has_network_dependency = any(net_pattern in content for net_pattern in [
        'requests', 'httpx', 'aiohttp', 'curl', 'socket',
        'api_client', 'client.get', 'client.post'
    ])
    
    # Determine suitability
    is_suitable = not has_db_dependency and not has_network_dependency
    
    return {
        'path': file_path,
        'is_suitable': is_suitable,
        'test_classes': transformer.test_classes,
        'test_functions': transformer.test_functions,
        'has_pytest': transformer.pytest_import_exists,
        'has_unittest': transformer.unittest_import_exists,
        'has_standalone_marker': transformer.has_standalone_marker,
        'has_db_dependency': has_db_dependency,
        'has_network_dependency': has_network_dependency
    }


def migrate_test_file(src_path: str, standalone_dir: str, dry_run: bool) -> bool:
    """Migrate a test file to the standalone format."""
    # Analyze the file first
    analysis = analyze_test_file(src_path)
    file_name = os.path.basename(src_path)
    dst_path = os.path.join(standalone_dir, file_name)
    
    if not analysis['is_suitable']:
        print(f"❌ {src_path} is not suitable for migration:")
        if analysis['has_db_dependency']:
            print("   - Has database dependencies")
        if analysis['has_network_dependency']:
            print("   - Has network dependencies")
        return False
    
    print(f"✅ {src_path} is suitable for migration")
    print(f"   - Test classes: {', '.join(analysis['test_classes'])}")
    print(f"   - Test functions: {', '.join(analysis['test_functions'])}")
    
    if dry_run:
        print(f"   - Would migrate to {dst_path}")
        return True
    
    # Read the content
    with open(src_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add pytest import if needed
    if not analysis['has_pytest'] and not "import pytest" in content:
        import_line = "import pytest\n"
        if "import " in content:
            # Add after the first import
            content = re.sub(
                r'(import .*?\n)',
                r'\1' + import_line,
                content,
                count=1
            )
        else:
            # Add at the beginning, after any possible docstrings
            docstring_match = re.match(r'(""".+?"""\s*\n)', content, re.DOTALL)
            if docstring_match:
                insert_pos = docstring_match.end()
                content = content[:insert_pos] + import_line + content[insert_pos:]
            else:
                content = import_line + content
    
    # Add standalone marker to each test class and function
    if not analysis['has_standalone_marker']:
        # For classes
        for class_name in analysis['test_classes']:
            content = re.sub(
                rf'(class {class_name}\(.*?\):)',
                r'@pytest.mark.standalone\n\1',
                content
            )
        
        # For functions
        for func_name in analysis['test_functions']:
            if not class_name:  # Only for standalone functions
                content = re.sub(
                    rf'(def {func_name}\(.*?\):)',
                    r'@pytest.mark.standalone\n\1',
                    content
                )
    
    # Write to the destination
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Migrated to {dst_path}")
    return True


def find_unit_test_files(unit_dir: str) -> List[str]:
    """Find all test files in the unit directory."""
    test_files = []
    for root, _, files in os.walk(unit_dir):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    return test_files


def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Get backend directory
    backend_dir = Path(__file__).resolve().parent.parent
    standalone_dir = backend_dir / "app" / "tests" / "standalone"
    
    # Ensure the standalone directory exists
    standalone_dir.mkdir(parents=True, exist_ok=True)
    
    if args.file:
        # Migrate a specific file
        if not os.path.exists(args.file):
            print(f"Error: File {args.file} does not exist")
            return 1
        
        success = migrate_test_file(args.file, str(standalone_dir), args.dry_run)
        return 0 if success else 1
    
    # Find and analyze all unit test files
    unit_dir = backend_dir / "app" / "tests" / "unit"
    if not unit_dir.exists():
        print(f"Error: Unit test directory not found at {unit_dir}")
        unit_dir = backend_dir / "app" / "tests"  # Fall back to general tests directory
        if not unit_dir.exists():
            print(f"Error: Tests directory not found at {unit_dir}")
            return 1
    
    print(f"Scanning for unit tests in {unit_dir}...")
    test_files = find_unit_test_files(str(unit_dir))
    print(f"Found {len(test_files)} test files")
    
    suitable_count = 0
    migrated_count = 0
    
    # Analyze each file
    for file_path in test_files:
        analysis = analyze_test_file(file_path)
        if analysis['is_suitable']:
            suitable_count += 1
            
            # Confirm before migration
            if not args.dry_run:
                response = input(f"Migrate {file_path} to standalone? (y/n): ")
                if response.lower() in ('y', 'yes'):
                    success = migrate_test_file(file_path, str(standalone_dir), False)
                    if success:
                        migrated_count += 1
            else:
                print(f"Would migrate {file_path} to standalone")
    
    print(f"\nSummary:")
    print(f"Total test files: {len(test_files)}")
    print(f"Suitable for migration: {suitable_count}")
    if not args.dry_run:
        print(f"Actually migrated: {migrated_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())