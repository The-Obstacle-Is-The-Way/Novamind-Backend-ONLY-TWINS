#!/usr/bin/env python3
"""
Test Analyzer for Novamind Digital Twin

This script analyzes test files to determine their dependencies and
suggests the appropriate directory in the dependency-based SSOT structure.

Usage:
    python test_analyzer.py [file_or_directory]
    python test_analyzer.py --all
"""

import ast
import os
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


class TestLevel(Enum):
    """Test levels based on external dependencies."""
    STANDALONE = "standalone"
    VENV = "venv"
    INTEGRATION = "integration"
    UNKNOWN = "unknown"


class TestAnalyzer:
    """
    Analyzes test files to determine their appropriate test level based on dependencies.
    """
    
    # Python standard library modules (indicating standalone tests)
    STDLIB_MODULES = {
        "abc", "argparse", "array", "asyncio", "base64", "collections", "contextlib",
        "copy", "csv", "datetime", "decimal", "enum", "functools", "hashlib", "io",
        "itertools", "json", "logging", "math", "os", "pathlib", "pickle", "random",
        "re", "string", "sys", "tempfile", "time", "typing", "uuid", "xml"
    }
    
    # Modules that require venv but not external services
    VENV_MODULES = {
        "fastapi", "pydantic", "sqlalchemy", "sqlalchemy.orm", "pandas", "numpy", 
        "sklearn", "pytest", "aiohttp", "requests", "uvicorn", "starlette",
        "jose", "passlib", "bcrypt", "cryptography"
    }
    
    # Modules that indicate integration test needs
    INTEGRATION_MODULES = {
        "databases", "motor", "aiomysql", "psycopg2", "httpx", "redis", "aioredis",
        "elasticsearch", "boto3", "minio", "kafka", "azure", "google.cloud"
    }
    
    # Patterns indicating database usage in code
    DB_PATTERNS = [
        r"\.execute\(", r"session\.", r"connection\.", r"cursor\.",
        r"query\.", r"\.commit\(", r"\.rollback\(", r"\.fetchall\(",
        r"repository", r"Repository", r"database", r"Database"
    ]
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[3]
        self.test_root = self.project_root / "app" / "tests"
        
    def analyze_all_tests(self) -> Dict[Path, TestLevel]:
        """
        Analyze all test files in the project.
        
        Returns:
            Dictionary mapping test files to their determined test level
        """
        results: Dict[Path, TestLevel] = {}
        
        for test_file in self._find_test_files():
            level = self.analyze_file(test_file)
            results[test_file] = level
            
        return results
    
    def analyze_file(self, file_path: Path) -> TestLevel:
        """
        Analyze a single test file to determine its dependency level.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            TestLevel enum indicating the appropriate test level
        """
        print(f"Analyzing {file_path.relative_to(self.project_root)}...")
        
        try:
            # Check if file exists
            if not file_path.exists():
                print(f"  File not found: {file_path}")
                return TestLevel.UNKNOWN
            
            # Open and parse the file
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
                
            # Check for pytest markers that might indicate type
            if self._has_integration_marker(file_content):
                print(f"  Integration test (marker): {file_path.name}")
                return TestLevel.INTEGRATION
                
            # Try to parse with AST to get imports
            try:
                imports = self._extract_imports(file_content)
                
                # Check for integration dependencies
                for module in imports:
                    if any(module.startswith(m) for m in self.INTEGRATION_MODULES):
                        print(f"  Integration test (imports): {file_path.name}")
                        return TestLevel.INTEGRATION
                
                # Check for venv dependencies
                if any(any(module.startswith(m) for m in self.VENV_MODULES) for module in imports):
                    # Check file content for DB usage patterns
                    if any(re.search(pattern, file_content) for pattern in self.DB_PATTERNS):
                        print(f"  Integration test (db patterns): {file_path.name}")
                        return TestLevel.INTEGRATION
                    
                    print(f"  VENV test: {file_path.name}")
                    return TestLevel.VENV
                
                # If no external imports, it's likely standalone
                print(f"  Standalone test: {file_path.name}")
                return TestLevel.STANDALONE
                
            except SyntaxError:
                # If AST parsing fails, fall back to simpler heuristics
                return self._analyze_without_ast(file_content, file_path)
                
        except Exception as e:
            print(f"  Error analyzing {file_path}: {str(e)}")
            return TestLevel.UNKNOWN
    
    def _find_test_files(self) -> List[Path]:
        """
        Find all test files in the project.
        
        Returns:
            List of paths to test files
        """
        test_files: List[Path] = []
        
        for root, _, files in os.walk(str(self.test_root)):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    test_files.append(Path(root) / file)
        
        return test_files
    
    def _extract_imports(self, content: str) -> Set[str]:
        """
        Extract all import module names from a Python file.
        
        Args:
            content: Python file content
            
        Returns:
            Set of imported module names
        """
        tree = ast.parse(content)
        imports: Set[str] = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
        
        return imports
    
    def _has_integration_marker(self, content: str) -> bool:
        """
        Check if a file has pytest markers indicating it's an integration test.
        
        Args:
            content: Python file content
            
        Returns:
            True if file has integration markers
        """
        markers = [
            "@pytest.mark.integration",
            "@pytest.mark.database",
            "@pytest.mark.external",
            "@pytest.mark.usefixtures(\"db\"",
            "@pytest.mark.usefixtures(\"database\""
        ]
        
        return any(marker in content for marker in markers)
    
    def _analyze_without_ast(self, content: str, file_path: Path) -> TestLevel:
        """
        Analyze a file without using AST (fallback method).
        
        Args:
            content: Python file content
            file_path: Path to the file
            
        Returns:
            TestLevel enum indicating the appropriate test level
        """
        # Check for import statements using regex
        import_lines = re.findall(r"^\s*(?:from|import)\s+([a-zA-Z0-9_.]+)", content, re.MULTILINE)
        
        # Integration modules
        for module in import_lines:
            if any(module.startswith(m) for m in self.INTEGRATION_MODULES):
                print(f"  Integration test (regex imports): {file_path.name}")
                return TestLevel.INTEGRATION
        
        # VENV modules
        if any(any(module.startswith(m) for m in self.VENV_MODULES) for module in import_lines):
            if any(re.search(pattern, content) for pattern in self.DB_PATTERNS):
                print(f"  Integration test (regex db patterns): {file_path.name}")
                return TestLevel.INTEGRATION
            
            print(f"  VENV test (regex): {file_path.name}")
            return TestLevel.VENV
        
        # Default to standalone
        print(f"  Standalone test (regex): {file_path.name}")
        return TestLevel.STANDALONE
    
    def generate_migration_plan(self) -> Dict[TestLevel, List[Path]]:
        """
        Generate a migration plan for all test files.
        
        Returns:
            Dictionary mapping test levels to lists of files that should be in that level
        """
        results = self.analyze_all_tests()
        migration_plan: Dict[TestLevel, List[Path]] = {
            TestLevel.STANDALONE: [],
            TestLevel.VENV: [],
            TestLevel.INTEGRATION: [],
            TestLevel.UNKNOWN: []
        }
        
        for file_path, level in results.items():
            migration_plan[level].append(file_path)
        
        return migration_plan
    
    def print_migration_plan(self):
        """Print a human-readable migration plan."""
        plan = self.generate_migration_plan()
        
        print("\n============== Test Migration Plan ==============\n")
        
        for level, files in plan.items():
            if level != TestLevel.UNKNOWN:
                print(f"{level.value.upper()} Tests ({len(files)}):")
                for file in sorted(files):
                    current_dir = file.parent.relative_to(self.test_root)
                    target_dir = f"tests/{level.value}"
                    print(f"  {current_dir}/{file.name} -> {target_dir}/{file.name}")
                print()
        
        if plan[TestLevel.UNKNOWN]:
            print(f"UNKNOWN Tests ({len(plan[TestLevel.UNKNOWN])}):")
            for file in sorted(plan[TestLevel.UNKNOWN]):
                print(f"  {file.relative_to(self.project_root)}")
            print()
        
        print("=============================================\n")
        print(f"Total: {sum(len(files) for files in plan.values())} test files")
        print(f"  - {len(plan[TestLevel.STANDALONE])} standalone tests")
        print(f"  - {len(plan[TestLevel.VENV])} venv tests")
        print(f"  - {len(plan[TestLevel.INTEGRATION])} integration tests")
        print(f"  - {len(plan[TestLevel.UNKNOWN])} unknown tests")
        

def main():
    """Entry point for the script."""
    analyzer = TestAnalyzer()
    analyzer.print_migration_plan()


if __name__ == "__main__":
    main()