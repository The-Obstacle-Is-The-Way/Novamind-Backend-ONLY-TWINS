#!/usr/bin/env python3
"""
Test Migration Utility

This script analyzes and migrates tests between different organizational structures,
particularly from the mixed approach to the dependency-based directory structure.

Usage:
    python migrate_tests.py --analyze        # Only analyze test dependencies, don't move
    python migrate_tests.py --migrate        # Analyze and migrate tests
    python migrate_tests.py --rollback       # Rollback migration (requires backup)
    python migrate_tests.py --report         # Generate migration report

The script categorizes tests into three levels:
1. standalone - Tests with no external dependencies
2. venv - Tests requiring Python environment but no external services
3. integration - Tests requiring external services, databases, etc.
"""

import os
import sys
import ast
import argparse
import shutil
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
import logging
import json
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("test_migration.log")
    ]
)
logger = logging.getLogger("test_migration")

# Project paths
PROJECT_ROOT = Path("/workspaces/Novamind-Backend-ONLY-TWINS")
BACKEND_DIR = PROJECT_ROOT / "backend"
APP_DIR = BACKEND_DIR / "app"
TESTS_DIR = APP_DIR / "tests"

# Target directories
STANDALONE_DIR = TESTS_DIR / "standalone"
VENV_DIR = TESTS_DIR / "venv"
INTEGRATION_DIR = TESTS_DIR / "integration"

# Backup directory
BACKUP_DIR = BACKEND_DIR / "app" / "tests_backup"

# Markers for dependency levels
STANDALONE_MARKERS = ["pytest.mark.standalone", "@pytest.mark.standalone"]
VENV_MARKERS = ["pytest.mark.venv", "@pytest.mark.venv"]
INTEGRATION_MARKERS = ["pytest.mark.integration", "@pytest.mark.integration"]

# Imports indicating dependency levels
STANDALONE_IMPORTS = {"unittest", "pytest"}
VENV_IMPORTS = {
    "pandas", "numpy", "sqlalchemy.ext.declarative", "sqlalchemy", 
    "pydantic", "fastapi", "tempfile", "shutil"
}
INTEGRATION_IMPORTS = {
    "requests", "httpx", "aiohttp", "redis", "pymongo", "psycopg2", 
    "databases", "sqlalchemy.ext.asyncio", "fastapi.testclient"
}


class TestAnalyzer:
    """Analyzes test files to determine their dependency level."""
    
    def __init__(self):
        self.standalone_tests = []
        self.venv_tests = []
        self.integration_tests = []
        self.unclassified_tests = []
    
    def analyze_file(self, file_path: Path) -> str:
        """
        Analyze a single test file and categorize it.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            str: Category of the test ('standalone', 'venv', 'integration', or 'unclassified')
        """
        logger.info(f"Analyzing {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for explicit markers
            for marker in STANDALONE_MARKERS:
                if marker in content:
                    self.standalone_tests.append(file_path)
                    return 'standalone'
            
            for marker in VENV_MARKERS:
                if marker in content:
                    self.venv_tests.append(file_path)
                    return 'venv'
            
            for marker in INTEGRATION_MARKERS:
                if marker in content:
                    self.integration_tests.append(file_path)
                    return 'integration'
            
            # If no markers, perform import analysis
            return self._analyze_imports(file_path, content)
        
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            self.unclassified_tests.append(file_path)
            return 'unclassified'
    
    def _analyze_imports(self, file_path: Path, content: str) -> str:
        """
        Analyze imports to determine test category.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            
        Returns:
            str: Category based on imports
        """
        try:
            tree = ast.parse(content)
            imports = self._extract_imports(tree)
            
            # Check for integration-level imports
            if any(imp in INTEGRATION_IMPORTS for imp in imports):
                self.integration_tests.append(file_path)
                return 'integration'
            
            # Check for venv-level imports
            if any(imp in VENV_IMPORTS for imp in imports):
                self.venv_tests.append(file_path)
                return 'venv'
            
            # Check for fixture usage that might indicate dependencies
            if "db_session" in content or "test_client" in content:
                self.integration_tests.append(file_path)
                return 'integration'
            
            # If no specific imports found, default to standalone
            self.standalone_tests.append(file_path)
            return 'standalone'
        
        except SyntaxError:
            logger.error(f"Syntax error in {file_path}")
            self.unclassified_tests.append(file_path)
            return 'unclassified'
    
    def _extract_imports(self, tree: ast.Module) -> Set[str]:
        """
        Extract imported module names from AST.
        
        Args:
            tree: AST tree of the file
            
        Returns:
            Set of imported module names
        """
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        return imports
    
    def analyze_directory(self, directory: Path) -> Dict[str, List[Path]]:
        """
        Analyze all test files in a directory.
        
        Args:
            directory: Directory containing test files
            
        Returns:
            Dict of categorized test files
        """
        test_files = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    test_files.append(Path(root) / file)
        
        for file_path in test_files:
            self.analyze_file(file_path)
        
        return {
            'standalone': self.standalone_tests,
            'venv': self.venv_tests,
            'integration': self.integration_tests,
            'unclassified': self.unclassified_tests
        }


class TestMigrator:
    """Migrates tests to their appropriate dependency-based directories."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.backup_created = False
        self.migration_map = {}  # Maps original paths to new paths
    
    def create_backup(self) -> bool:
        """
        Create a backup of the tests directory.
        
        Returns:
            bool: True if backup was created, False otherwise
        """
        if self.backup_created:
            return True
        
        try:
            if BACKUP_DIR.exists():
                logger.warning(f"Backup directory {BACKUP_DIR} already exists")
                return False
            
            if not self.dry_run:
                shutil.copytree(TESTS_DIR, BACKUP_DIR)
                self.backup_created = True
                logger.info(f"Backup created at {BACKUP_DIR}")
            else:
                logger.info(f"[DRY RUN] Would create backup at {BACKUP_DIR}")
                self.backup_created = True
            
            return True
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def migrate_test(self, source_path: Path, category: str) -> Optional[Path]:
        """
        Migrate a single test file to its appropriate directory.
        
        Args:
            source_path: Source path of the test file
            category: Dependency category ('standalone', 'venv', 'integration')
            
        Returns:
            Path: New path of the migrated test, or None if migration failed
        """
        if category not in ('standalone', 'venv', 'integration'):
            logger.error(f"Invalid category '{category}' for {source_path}")
            return None
        
        # Determine the relative path within the tests directory
        rel_path = source_path.relative_to(TESTS_DIR)
        
        # Determine target category directory
        if category == 'standalone':
            target_dir = STANDALONE_DIR
        elif category == 'venv':
            target_dir = VENV_DIR
        else:  # integration
            target_dir = INTEGRATION_DIR
        
        # Extract components from the relative path
        parts = list(rel_path.parts)
        
        # If the first part is already a category directory, remove it
        if parts[0] in ('standalone', 'venv', 'integration', 'unit', 'e2e'):
            parts = parts[1:]
        
        # Construct the new path
        new_path = target_dir.joinpath(*parts)
        
        # Ensure target directory exists
        if not self.dry_run:
            os.makedirs(new_path.parent, exist_ok=True)
        
        # Log the migration
        logger.info(f"Migrating {source_path} to {new_path}")
        
        # Perform the migration
        if not self.dry_run:
            if new_path.exists():
                logger.warning(f"Target file {new_path} already exists, skipping")
                return None
            
            # Create parent directories if they don't exist
            os.makedirs(new_path.parent, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_path, new_path)
            
            # Check if we need to create __init__.py files
            current_dir = new_path.parent
            while current_dir != target_dir.parent:
                init_file = current_dir / "__init__.py"
                if not init_file.exists():
                    with open(init_file, 'w') as f:
                        f.write(f'"""\n{current_dir.name.capitalize()} test package\n"""\n')
                current_dir = current_dir.parent
        
        # Record the migration
        self.migration_map[str(source_path)] = str(new_path)
        
        return new_path
    
    def migrate_tests(self, categorized_tests: Dict[str, List[Path]]) -> Dict[str, List[Path]]:
        """
        Migrate all tests to their appropriate directories.
        
        Args:
            categorized_tests: Dict of tests categorized by dependency level
            
        Returns:
            Dict: Result of the migration with new paths
        """
        if not self.create_backup():
            logger.error("Failed to create backup, aborting migration")
            return {}
        
        results = {
            'standalone': [],
            'venv': [],
            'integration': [],
            'failed': []
        }
        
        # Create the target directories if they don't exist
        if not self.dry_run:
            os.makedirs(STANDALONE_DIR, exist_ok=True)
            os.makedirs(VENV_DIR, exist_ok=True)
            os.makedirs(INTEGRATION_DIR, exist_ok=True)
        
        # Migrate each test based on its category
        for category, test_files in categorized_tests.items():
            if category == 'unclassified':
                logger.warning(f"Skipping {len(test_files)} unclassified tests")
                continue
            
            for file_path in test_files:
                new_path = self.migrate_test(file_path, category)
                if new_path:
                    results[category].append(new_path)
                else:
                    results['failed'].append(file_path)
        
        # Save the migration map
        self._save_migration_map()
        
        return results
    
    def _save_migration_map(self):
        """Save the migration map to a JSON file."""
        if not self.dry_run:
            map_file = BACKEND_DIR / "app" / "test_migration_map.json"
            with open(map_file, 'w') as f:
                json.dump(self.migration_map, f, indent=2)
            logger.info(f"Migration map saved to {map_file}")
    
    def rollback(self) -> bool:
        """
        Rollback the migration using the backup.
        
        Returns:
            bool: True if rollback succeeded, False otherwise
        """
        if not BACKUP_DIR.exists():
            logger.error(f"Backup directory {BACKUP_DIR} does not exist")
            return False
        
        try:
            # Remove the migrated tests
            shutil.rmtree(STANDALONE_DIR, ignore_errors=True)
            shutil.rmtree(VENV_DIR, ignore_errors=True)
            shutil.rmtree(INTEGRATION_DIR, ignore_errors=True)
            
            # Restore from backup
            for item in BACKUP_DIR.iterdir():
                dest = TESTS_DIR / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
            
            logger.info("Migration rolled back successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error rolling back migration: {e}")
            return False


class TestImportFixer:
    """Fixes imports in migrated test files."""
    
    def __init__(self, migration_map: Dict[str, str]):
        self.migration_map = migration_map
    
    def fix_imports(self) -> int:
        """
        Fix imports in all migrated files.
        
        Returns:
            int: Number of files with fixed imports
        """
        fixed_count = 0
        
        for _, new_path in self.migration_map.items():
            if self._fix_imports_in_file(Path(new_path)):
                fixed_count += 1
        
        return fixed_count
    
    def _fix_imports_in_file(self, file_path: Path) -> bool:
        """
        Fix imports in a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if imports were fixed, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for relative imports that might need fixing
            pattern = r'from \.\.+\w+'
            if not re.search(pattern, content):
                return False
            
            # Parse the file
            tree = ast.parse(content)
            
            # Track modified status
            modified = False
            
            # Build the map of replacements
            replacements = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level > 0:
                    # This is a relative import
                    old_import = content[node.lineno-1]
                    
                    # Calculate the correct absolute import
                    if node.module:
                        module_path = f"app.{node.module}"
                    else:
                        # Empty module means importing from parent
                        module_path = "app"
                    
                    # Create the new import statement
                    new_import = f"from {module_path} import {', '.join(n.name for n in node.names)}"
                    
                    replacements.append((old_import, new_import))
                    modified = True
            
            if modified:
                # Apply all replacements
                for old, new in replacements:
                    content = content.replace(old, new)
                
                # Write the modified content back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"Fixed imports in {file_path}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error fixing imports in {file_path}: {e}")
            return False


def analyze_tests() -> Dict[str, List[Path]]:
    """
    Analyze all tests in the project.
    
    Returns:
        Dict of categorized tests
    """
    analyzer = TestAnalyzer()
    return analyzer.analyze_directory(TESTS_DIR)


def migrate_tests(categorized_tests: Dict[str, List[Path]], dry_run: bool = False) -> Dict[str, List[Path]]:
    """
    Migrate tests to their appropriate directories.
    
    Args:
        categorized_tests: Dict of categorized tests
        dry_run: If True, only simulate the migration
        
    Returns:
        Dict of migration results
    """
    migrator = TestMigrator(dry_run=dry_run)
    return migrator.migrate_tests(categorized_tests)


def fix_imports(migration_map_path: Path) -> int:
    """
    Fix imports in migrated test files.
    
    Args:
        migration_map_path: Path to the migration map JSON file
        
    Returns:
        int: Number of files with fixed imports
    """
    try:
        with open(migration_map_path, 'r') as f:
            migration_map = json.load(f)
        
        fixer = TestImportFixer(migration_map)
        return fixer.fix_imports()
    
    except Exception as e:
        logger.error(f"Error fixing imports: {e}")
        return 0


def rollback_migration() -> bool:
    """
    Rollback the migration.
    
    Returns:
        bool: True if rollback succeeded, False otherwise
    """
    migrator = TestMigrator()
    return migrator.rollback()


def generate_report(categorized_tests: Dict[str, List[Path]]) -> Dict[str, Any]:
    """
    Generate a report of test categorization.
    
    Args:
        categorized_tests: Dict of categorized tests
        
    Returns:
        Dict: Report data
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": sum(len(tests) for tests in categorized_tests.values()),
        "categories": {
            "standalone": len(categorized_tests.get('standalone', [])),
            "venv": len(categorized_tests.get('venv', [])),
            "integration": len(categorized_tests.get('integration', [])),
            "unclassified": len(categorized_tests.get('unclassified', []))
        },
        "file_details": {}
    }
    
    # Add details for each file
    for category, files in categorized_tests.items():
        report["file_details"][category] = [str(f) for f in files]
    
    return report


def save_report(report: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the analysis report to a file.
    
    Args:
        report: Report data
        output_path: Path to save the report (optional)
        
    Returns:
        Path: Path where the report was saved
    """
    if output_path is None:
        output_path = BACKEND_DIR / f"test_classification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to {output_path}")
    return output_path


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Test Migration Utility")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--analyze', action='store_true', help='Analyze tests without migration')
    group.add_argument('--migrate', action='store_true', help='Analyze and migrate tests')
    group.add_argument('--dry-run', action='store_true', help='Simulate migration without moving files')
    group.add_argument('--rollback', action='store_true', help='Rollback migration')
    group.add_argument('--fix-imports', action='store_true', help='Fix imports in migrated tests')
    group.add_argument('--report', action='store_true', help='Generate migration report')
    
    args = parser.parse_args()
    
    if args.analyze or args.migrate or args.dry_run or args.report:
        # Analyze tests
        categorized_tests = analyze_tests()
        
        # Generate report
        report = generate_report(categorized_tests)
        report_path = save_report(report)
        
        # Print summary
        print("\nTest Categorization Summary:")
        print(f"Total tests: {report['total_tests']}")
        print(f"Standalone tests: {report['categories']['standalone']}")
        print(f"VENV tests: {report['categories']['venv']}")
        print(f"Integration tests: {report['categories']['integration']}")
        print(f"Unclassified tests: {report['categories']['unclassified']}")
        print(f"\nDetailed report saved to: {report_path}")
        
        # Perform migration if requested
        if args.migrate:
            print("\nMigrating tests...")
            results = migrate_tests(categorized_tests, dry_run=False)
            print("\nMigration completed:")
            print(f"Standalone tests migrated: {len(results.get('standalone', []))}")
            print(f"VENV tests migrated: {len(results.get('venv', []))}")
            print(f"Integration tests migrated: {len(results.get('integration', []))}")
            print(f"Failed migrations: {len(results.get('failed', []))}")
            
            # Fix imports
            print("\nFixing imports...")
            fixed_count = fix_imports(BACKEND_DIR / "app" / "test_migration_map.json")
            print(f"Fixed imports in {fixed_count} files")
        
        # Simulate migration if requested
        if args.dry_run:
            print("\nSimulating migration (dry run)...")
            results = migrate_tests(categorized_tests, dry_run=True)
            print("\nSimulated migration completed:")
            print(f"Standalone tests to migrate: {len(results.get('standalone', []))}")
            print(f"VENV tests to migrate: {len(results.get('venv', []))}")
            print(f"Integration tests to migrate: {len(results.get('integration', []))}")
    
    # Rollback migration if requested
    if args.rollback:
        print("\nRolling back migration...")
        if rollback_migration():
            print("Migration rolled back successfully")
        else:
            print("Failed to roll back migration")
    
    # Fix imports if requested
    if args.fix_imports:
        print("\nFixing imports...")
        migration_map_path = BACKEND_DIR / "app" / "test_migration_map.json"
        if migration_map_path.exists():
            fixed_count = fix_imports(migration_map_path)
            print(f"Fixed imports in {fixed_count} files")
        else:
            print(f"Migration map not found at {migration_map_path}")


if __name__ == "__main__":
    main()