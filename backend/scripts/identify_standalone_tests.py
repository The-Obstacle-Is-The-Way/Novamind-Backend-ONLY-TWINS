#!/usr/bin/env python3
"""
Standalone Test Identifier

This script analyzes existing test files to identify potential candidates
for standalone tests based on their imports and dependencies.

Usage:
    python identify_standalone_tests.py [--dir <test_directory>] [--verbose]

Options:
    --dir     Directory to scan for tests (default: backend/app/tests)
    --verbose Show detailed analysis for each file
"""

import os
import re
import sys
import ast
import argparse
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class TestFileAnalysis:
    """Analysis result for a test file."""
    path: str
    module_name: str
    external_imports: List[str] = field(default_factory=list)
    internal_imports: List[str] = field(default_factory=list)
    test_count: int = 0
    lines_of_code: int = 0
    has_db_dependency: bool = False
    has_network_dependency: bool = False
    has_file_dependency: bool = False
    standalone_potential: str = "Unknown"
    reason: str = ""


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to collect import information."""
    
    DB_MODULES = {
        'sqlalchemy', 'asyncpg', 'databases', 'alembic', 'psycopg2',
        'app.core.db', 'app.persistence', 'app.infrastructure.persistence'
    }
    
    NETWORK_MODULES = {
        'aiohttp', 'requests', 'httpx', 'urllib', 'socket',
        'app.infrastructure.external'
    }
    
    FILE_MODULES = {
        'tempfile', 'csv', 'openpyxl', 'xlrd', 'xlwt'
    }
    
    def __init__(self):
        self.imports = set()
        self.from_imports = {}
        self.has_db_dependency = False
        self.has_network_dependency = False
        self.has_file_dependency = False
        
    def visit_Import(self, node):
        for name in node.names:
            self.imports.add(name.name)
            self._check_dependency(name.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        module = node.module if node.module else ''
        for name in node.names:
            if module not in self.from_imports:
                self.from_imports[module] = []
            self.from_imports[module].append(name.name)
            self._check_dependency(f"{module}.{name.name}" if module else name.name)
        self.generic_visit(node)
    
    def _check_dependency(self, import_path):
        # Check for database dependencies
        if any(db_module in import_path for db_module in self.DB_MODULES):
            self.has_db_dependency = True
        
        # Check for network dependencies
        if any(net_module in import_path for net_module in self.NETWORK_MODULES):
            self.has_network_dependency = True
            
        # Check for file dependencies
        if any(file_module in import_path for file_module in self.FILE_MODULES):
            self.has_file_dependency = True


class TestCountVisitor(ast.NodeVisitor):
    """AST visitor to count test functions/methods."""
    
    def __init__(self):
        self.test_count = 0
        
    def visit_FunctionDef(self, node):
        # Count functions that start with 'test_'
        if node.name.startswith('test_'):
            self.test_count += 1
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        # Check for unittest.TestCase subclasses
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'TestCase':
                # Count methods that start with 'test_'
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                        self.test_count += 1
        self.generic_visit(node)


def get_module_name(file_path: str) -> str:
    """Extract module name from file path."""
    # Convert path to module notation
    module_parts = []
    path_parts = file_path.split(os.sep)
    
    # Find where the Python package starts
    start_idx = 0
    for i, part in enumerate(path_parts):
        if part == 'backend' or part == 'app':
            start_idx = i
            break
    
    # Build module name from path components
    for part in path_parts[start_idx:]:
        # Skip __pycache__ directories
        if part == '__pycache__':
            continue
        
        # Remove .py extension if present
        if part.endswith('.py'):
            part = part[:-3]
            
        # Skip __init__.py files for module name
        if part != '__init__':
            module_parts.append(part)
    
    return '.'.join(module_parts)


def analyze_test_file(file_path: str) -> Optional[TestFileAnalysis]:
    """Analyze a test file for dependencies and potential for standalone testing."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Calculate lines of code (excluding comments and blank lines)
        lines = [line for line in content.split('\n') 
                if line.strip() and not line.strip().startswith('#')]
        
        # Parse the file
        tree = ast.parse(content)
        
        # Collect imports
        import_visitor = ImportVisitor()
        import_visitor.visit(tree)
        
        # Count tests
        test_counter = TestCountVisitor()
        test_counter.visit(tree)
        
        # Create analysis result
        analysis = TestFileAnalysis(
            path=file_path,
            module_name=get_module_name(file_path),
            external_imports=list(import_visitor.imports),
            internal_imports=[
                f"{module}.{name}" for module, names in import_visitor.from_imports.items()
                for name in names
            ],
            test_count=test_counter.test_count,
            lines_of_code=len(lines),
            has_db_dependency=import_visitor.has_db_dependency,
            has_network_dependency=import_visitor.has_network_dependency,
            has_file_dependency=import_visitor.has_file_dependency
        )
        
        # Evaluate standalone potential
        if analysis.has_db_dependency:
            analysis.standalone_potential = "Low"
            analysis.reason = "Has database dependencies"
        elif analysis.has_network_dependency:
            analysis.standalone_potential = "Low"
            analysis.reason = "Has network dependencies"
        elif "pytest" in " ".join(analysis.external_imports) and analysis.test_count > 0:
            # Check for common pytest fixture usage that might indicate integration tests
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "db_session" in content or "client" in content and "test_client" in content:
                    analysis.standalone_potential = "Medium"
                    analysis.reason = "Uses pytest fixtures that might be mockable"
                else:
                    analysis.standalone_potential = "High"
                    analysis.reason = "Uses pytest without obvious integration dependencies"
        elif "unittest" in " ".join(analysis.external_imports) and analysis.test_count > 0:
            analysis.standalone_potential = "High"
            analysis.reason = "Uses unittest with no external dependencies"
        else:
            analysis.standalone_potential = "Medium"
            analysis.reason = "No obvious integration dependencies but requires further analysis"
            
        return analysis
    except Exception as e:
        print(f"Error analyzing {file_path}: {str(e)}")
        return None


def find_test_files(directory: str) -> List[str]:
    """Find all Python test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and (file.startswith('test_') or file.endswith('_test.py')):
                test_files.append(os.path.join(root, file))
    return test_files


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Identify potential standalone tests')
    parser.add_argument('--dir', default='backend/app/tests', help='Directory to scan for tests')
    parser.add_argument('--verbose', action='store_true', help='Show detailed analysis')
    args = parser.parse_args()
    
    print(f"Scanning directory: {args.dir}")
    test_files = find_test_files(args.dir)
    print(f"Found {len(test_files)} test files")
    
    # Analyze each test file
    analyses = []
    for file_path in test_files:
        analysis = analyze_test_file(file_path)
        if analysis:
            analyses.append(analysis)
    
    # Group by standalone potential
    high_potential = [a for a in analyses if a.standalone_potential == "High"]
    medium_potential = [a for a in analyses if a.standalone_potential == "Medium"]
    low_potential = [a for a in analyses if a.standalone_potential == "Low"]
    
    # Print summary
    print("\n===== STANDALONE TEST CANDIDATES SUMMARY =====")
    print(f"Total test files analyzed: {len(analyses)}")
    print(f"High potential: {len(high_potential)} files ({sum(a.test_count for a in high_potential)} tests)")
    print(f"Medium potential: {len(medium_potential)} files ({sum(a.test_count for a in medium_potential)} tests)")
    print(f"Low potential: {len(low_potential)} files ({sum(a.test_count for a in low_potential)} tests)")
    
    # Print high potential candidates
    print("\n===== HIGH POTENTIAL CANDIDATES =====")
    for analysis in sorted(high_potential, key=lambda a: a.test_count, reverse=True):
        print(f"{analysis.path} - {analysis.test_count} tests")
        if args.verbose:
            print(f"  Reason: {analysis.reason}")
            print(f"  Module: {analysis.module_name}")
            print(f"  Lines of code: {analysis.lines_of_code}")
            print(f"  External imports: {', '.join(analysis.external_imports)}")
            print("")
    
    # Print medium potential candidates if verbose
    if args.verbose:
        print("\n===== MEDIUM POTENTIAL CANDIDATES =====")
        for analysis in sorted(medium_potential, key=lambda a: a.test_count, reverse=True):
            print(f"{analysis.path} - {analysis.test_count} tests")
            print(f"  Reason: {analysis.reason}")
            print("")
    
    # Generate recommendations
    print("\n===== RECOMMENDED NEXT STEPS =====")
    if high_potential:
        print("1. Start by converting these high-potential test files to standalone tests:")
        for i, analysis in enumerate(sorted(high_potential, key=lambda a: a.test_count, reverse=True)[:5]):
            print(f"   {i+1}. {analysis.path} ({analysis.test_count} tests)")
    else:
        print("No high-potential candidates found. Consider analyzing more test files.")
    
    print("\n2. Create a migration plan for each test file:")
    print("   - Copy test to standalone directory")
    print("   - Add @pytest.mark.standalone marker")
    print("   - Update imports to resolve dependencies")
    print("   - Verify test runs in isolation")
    
    # Output machine-readable results if needed
    # Could add JSON output here for use in other scripts


if __name__ == "__main__":
    main()