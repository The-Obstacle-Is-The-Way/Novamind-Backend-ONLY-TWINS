#!/usr/bin/env python3
"""
Test Classification Script for Novamind Digital Twin Platform

This script analyzes test files to categorize them by dependency requirements
and adds the appropriate pytest markers.

Usage:
    python classify_tests.py [--path PATH] [--update] [--log-level {DEBUG,INFO,WARNING,ERROR}]

Options:
    --path PATH     Directory to analyze (default: app/tests)
    --update        Update test files with dependency markers
    --log-level     Set logging level (default: INFO)
"""

import os
import re
import ast
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Set, Tuple, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("test_classifier")

# Import patterns that indicate dependencies
DB_IMPORTS = {
    # Database-related imports
    "sqlalchemy", "asyncpg", "psycopg2", "aiomysql", "alembic", "sqlite3", 
    "databases", "redis", "pymongo", "motor", "beanie", "tortoise",
    # Repository imports that likely use DB
    "app.infrastructure.persistence", "app.infrastructure.database",
    "app.repositories", "app.infrastructure.repositories",
}

NETWORK_IMPORTS = {
    # Network/HTTP-related imports
    "requests", "httpx", "aiohttp", "boto3", "aioboto3", "pika", 
    "websockets", "socket", "urllib", "fastapi.testclient",
    # API or service modules that likely use network
    "app.api", "app.external_services", "app.infrastructure.external", 
}

FRAMEWORK_IMPORTS = {
    # Framework imports
    "fastapi", "starlette", "uvicorn", "flask", "django",
    "app.core", "app.application",
}

MOCK_IMPORTS = {
    # Mocking libraries
    "unittest.mock", "pytest_mock", "mock", 
}

# Output stats
stats = {
    "total": 0,
    "standalone": 0,
    "venv_only": 0,
    "db_required": 0,
    "network_required": 0,
    "updated": 0,
    "errors": 0,
}

class TestDependencyAnalyzer:
    """Analyzes test files to determine their dependencies."""
    
    def __init__(self, update: bool = False):
        """Initialize the analyzer.
        
        Args:
            update: Whether to update test files with markers
        """
        self.update = update
        
    def analyze_dependencies(self, file_path: Path) -> dict:
        """
        Analyze a test file for dependencies.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            Dict with dependency classification results
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Parse the file
            try:
                tree = ast.parse(content)
            except SyntaxError:
                logger.error(f"Error parsing {file_path}")
                stats["errors"] += 1
                return {
                    "is_standalone": False,
                    "needs_venv": True,
                    "needs_db": False,
                    "needs_network": False,
                    "error": True,
                }
                
            # Extract all imports
            imports = self._extract_imports(tree)
            
            # Check for existing markers
            has_standalone_marker = "@pytest.mark.standalone" in content
            has_db_marker = "@pytest.mark.db_required" in content
            has_venv_marker = "@pytest.mark.venv_only" in content
            has_network_marker = "@pytest.mark.network_required" in content
            
            # Check for specific patterns in the code
            has_db_access = any(db_import in imports for db_import in DB_IMPORTS)
            has_network_access = any(net_import in imports for net_import in NETWORK_IMPORTS)
            has_framework_deps = any(framework in imports for framework in FRAMEWORK_IMPORTS)
            
            # Look for direct database interactions using repository pattern
            uses_repository = "repository" in content.lower() and not "mock_repository" in content.lower()
            
            # Check for direct usage of services or clients that might use external resources
            uses_service = (
                "service" in content.lower() 
                and not "mock_service" in content.lower()
                and not "MockService" in content
            )
            
            # Check if test mocks database/network access
            has_mocks = any(mock_import in imports for mock_import in MOCK_IMPORTS)
            mocks_db = has_mocks and ("mock" in content.lower() and any(db_term in content.lower() for db_term in ["database", "repository", "session"]))
            mocks_network = has_mocks and ("mock" in content.lower() and any(net_term in content.lower() for net_term in ["http", "request", "client", "api"]))
            
            # Make dependency classification decision
            needs_db = (has_db_marker or has_db_access or uses_repository) and not mocks_db
            needs_network = (has_network_marker or has_network_access or uses_service) and not mocks_network
            needs_framework = has_framework_deps and not ("mock" in content.lower() and "app" in content.lower())
            
            # A test is standalone if it's explicitly marked or has no external dependencies
            is_standalone = has_standalone_marker or (
                not needs_db and 
                not needs_network and 
                not needs_framework and
                "unittest" in imports  # Likely a self-contained test
            )
            
            # Needs venv but no other external dependencies
            needs_venv = has_venv_marker or (
                not is_standalone and 
                not needs_db and 
                not needs_network
            )
            
            return {
                "is_standalone": is_standalone,
                "needs_venv": needs_venv,
                "needs_db": needs_db,
                "needs_network": needs_network,
                "imports": imports,
                "error": False,
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {str(e)}")
            stats["errors"] += 1
            return {
                "is_standalone": False,
                "needs_venv": True,
                "needs_db": False,
                "needs_network": False,
                "error": True,
            }
    
    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """
        Extract all imports from an AST.
        
        Args:
            tree: AST tree from ast.parse()
            
        Returns:
            Set of imported modules
        """
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name.split('.')[0])
                    imports.add(name.name)  # Add full import path too
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
                    imports.add(node.module)  # Add full import path too
                for name in node.names:
                    if node.module:
                        imports.add(f"{node.module}.{name.name}")
                        
        return imports

    def update_test_markers(self, file_path: Path, dependencies: Dict[str, bool]) -> bool:
        """
        Update the pytest markers in a test file.
        
        Args:
            file_path: Path to the test file
            dependencies: Dependency classification dict
            
        Returns:
            True if file was updated, False otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            # Extract existing content for comparison later
            original_content = "".join(lines)
                
            # Determine which markers to add
            marker_lines = []
            if dependencies["is_standalone"]:
                marker_lines.append("@pytest.mark.standalone\n")
            elif dependencies["needs_venv"]:
                marker_lines.append("@pytest.mark.venv_only\n")
                
            if dependencies["needs_db"]:
                marker_lines.append("@pytest.mark.db_required\n")
                
            if dependencies["needs_network"]:
                marker_lines.append("@pytest.mark.network_required\n")
                
            # Find where to insert markers (before class or function definitions)
            updated_lines = []
            inserted = False
            i = 0
            
            # Find imports section to ensure pytest is imported
            has_pytest_import = any("pytest" in line for line in lines)
            import_section_end = 0
            
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    import_section_end = i + 1
                elif line.strip() and import_section_end > 0:
                    # First non-empty line after imports
                    break
                    
            # Add pytest import if needed
            if not has_pytest_import and marker_lines:
                updated_lines = lines[:import_section_end] + ["import pytest\n"] + lines[import_section_end:]
                lines = updated_lines
                updated_lines = []
            
            # Find class/function definitions to add markers
            in_docstring = False
            class_or_func_line = -1
            
            for i, line in enumerate(lines):
                # Track if we're in a docstring
                if '"""' in line or "'''" in line:
                    in_docstring = not in_docstring
                    
                # Skip lines until we're out of the docstring
                if in_docstring:
                    updated_lines.append(line)
                    continue
                
                # Look for class or function definitions
                if re.match(r"^\s*(class|def)\s+\w+", line) and not inserted:
                    class_or_func_line = i
                    
                    # Go backwards to find the first non-decorator, non-blank line
                    j = i - 1
                    while j >= 0:
                        prev_line = lines[j].strip()
                        if not prev_line or prev_line.startswith("@"):
                            j -= 1
                        else:
                            break
                            
                    # Insert markers
                    updated_lines.extend(lines[:j+1])
                    updated_lines.extend(marker_lines)
                    updated_lines.extend(lines[j+1:])
                    inserted = True
                    break
                    
                if not inserted:
                    updated_lines.append(line)
            
            # If we didn't find a place to insert, just append to the file
            if not inserted:
                updated_lines = lines + marker_lines
                
            # Only write if we actually changed something
            new_content = "".join(updated_lines)
            if new_content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(updated_lines)
                stats["updated"] += 1
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error updating markers in {file_path}: {str(e)}")
            return False

def find_all_test_files(base_path: Path) -> List[Path]:
    """
    Find all test files in the given directory.
    
    Args:
        base_path: Base directory to search in
        
    Returns:
        List of test file paths
    """
    test_files = []
    
    for item in base_path.glob("**/*.py"):
        if item.is_file() and (item.name.startswith("test_") or item.name.endswith("_test.py")):
            test_files.append(item)
            
    return test_files

def format_path(path: Path, base_dir: Path) -> str:
    """Format a path for display, making it relative to base_dir."""
    try:
        return str(path.relative_to(base_dir))
    except ValueError:
        return str(path)

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze and classify test files by dependencies")
    parser.add_argument("--path", default="app/tests", help="Path to test directory")
    parser.add_argument("--update", action="store_true", help="Update test files with markers")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        help="Set logging level")
    args = parser.parse_args()
    
    # Set log level
    logger.setLevel(getattr(logging, args.log_level))
    
    # Determine base paths
    script_dir = Path(__file__).resolve().parent
    backend_dir = script_dir.parent
    os.chdir(backend_dir)  # Change to backend directory
    
    base_path = Path(args.path)
    if not base_path.is_absolute():
        base_path = backend_dir / base_path
        
    # Analyze test files
    analyzer = TestDependencyAnalyzer(update=args.update)
    test_files = find_all_test_files(base_path)
    stats["total"] = len(test_files)
    
    logger.info(f"Found {len(test_files)} test files to analyze in {args.path}")
    
    standalone_tests = []
    venv_only_tests = []
    db_required_tests = []
    network_required_tests = []
    
    for file_path in test_files:
        rel_path = format_path(file_path, backend_dir)
        dependencies = analyzer.analyze_dependencies(file_path)
        
        if dependencies["error"]:
            continue
            
        # Categorize the test
        if dependencies["is_standalone"]:
            standalone_tests.append(rel_path)
            stats["standalone"] += 1
            logger.debug(f"STANDALONE: {rel_path}")
        elif dependencies["needs_venv"]:
            venv_only_tests.append(rel_path)
            stats["venv_only"] += 1
            logger.debug(f"VENV_ONLY: {rel_path}")
        elif dependencies["needs_db"]:
            db_required_tests.append(rel_path)
            stats["db_required"] += 1
            logger.debug(f"DB_REQUIRED: {rel_path}")
            
        if dependencies["needs_network"]:
            network_required_tests.append(rel_path)
            stats["network_required"] += 1
            logger.debug(f"NETWORK_REQUIRED: {rel_path}")
            
        # Update test markers if requested
        if args.update:
            updated = analyzer.update_test_markers(file_path, dependencies)
            if updated:
                logger.info(f"Updated markers for {rel_path}")
    
    # Output summary
    logger.info("\nTest Classification Summary:")
    logger.info(f"Total test files: {stats['total']}")
    logger.info(f"Standalone tests: {stats['standalone']} ({stats['standalone']/stats['total']*100:.1f}%)")
    logger.info(f"Venv-only tests: {stats['venv_only']} ({stats['venv_only']/stats['total']*100:.1f}%)")
    logger.info(f"DB-required tests: {stats['db_required']} ({stats['db_required']/stats['total']*100:.1f}%)")
    logger.info(f"Network-required tests: {stats['network_required']} ({stats['network_required']/stats['total']*100:.1f}%)")
    
    if args.update:
        logger.info(f"Updated {stats['updated']} test files with markers")
        
    if stats["errors"] > 0:
        logger.warning(f"Encountered {stats['errors']} errors during analysis")
        
    # Output test paths by category for further processing
    if stats["standalone"] > 0:
        logger.info("\nStandalone Tests:")
        for test in sorted(standalone_tests):
            logger.info(f"  {test}")
            
    if args.update:
        logger.info("\nRecommendation: Run standalone tests to verify classification:")
        logger.info("python -m pytest app/tests -m standalone -v")

if __name__ == "__main__":
    main()