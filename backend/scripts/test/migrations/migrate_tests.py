#!/usr/bin/env python3
"""
Test Migration Tool for Novamind Digital Twin

This script migrates tests to the appropriate directories in the
dependency-based SSOT structure. It analyzes test dependencies,
moves files, and updates imports as needed.

Usage:
    python migrate_tests.py --analyze   # Analyze without moving
    python migrate_tests.py --migrate   # Analyze and migrate
    python migrate_tests.py --rollback  # Rollback the last migration
"""

import argparse
import os
import re
import shutil
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import json

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Import the test analyzer
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from test_analyzer import TestAnalyzer, TestLevel


class Colors:
    """Terminal colors for output formatting."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestMigrator:
    """
    Migrates tests to the appropriate directories in the dependency-based SSOT structure.
    """
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[3]
        self.test_root = self.project_root / "app" / "tests"
        self.analyzer = TestAnalyzer()
        self.migration_log_path = self.project_root / "scripts" / "test" / "migrations" / "migration_log.json"
        self.migration_log: Dict = {}
        
    def analyze(self) -> Dict[TestLevel, List[Path]]:
        """
        Analyze all tests and report which ones need to be migrated.
        
        Returns:
            Dictionary mapping test levels to lists of files
        """
        print(f"{Colors.HEADER}Analyzing tests to determine appropriate locations...{Colors.ENDC}")
        return self.analyzer.generate_migration_plan()
        
    def migrate(self) -> bool:
        """
        Migrate tests to their appropriate directories.
        
        Returns:
            True if migration was successful, False otherwise
        """
        # Check if we already have a migration in progress
        if self._has_incomplete_migration():
            print(f"{Colors.RED}There appears to be an incomplete migration.{Colors.ENDC}")
            print(f"{Colors.RED}Please use --rollback to revert the previous migration before proceeding.{Colors.ENDC}")
            return False
        
        # Create a new migration log
        self.migration_log = {
            "timestamp": time.time(),
            "status": "in_progress",
            "moved_files": []
        }
        
        # Ensure target directories exist
        for level in TestLevel:
            if level != TestLevel.UNKNOWN:
                level_dir = self.test_root / level.value
                level_dir.mkdir(exist_ok=True)
        
        # Get migration plan
        migration_plan = self.analyzer.generate_migration_plan()
        
        # Count files to be migrated that aren't already in the right place
        files_to_migrate = 0
        for level, files in migration_plan.items():
            if level != TestLevel.UNKNOWN:
                for file_path in files:
                    if level.value not in str(file_path.relative_to(self.test_root)).split(os.sep)[0]:
                        files_to_migrate += 1
        
        print(f"{Colors.BLUE}Found {files_to_migrate} files to migrate.{Colors.ENDC}")
        
        # Move files
        for level, files in migration_plan.items():
            if level != TestLevel.UNKNOWN:
                level_dir = self.test_root / level.value
                
                for file_path in files:
                    # Skip files that are already in the right place
                    if level.value in str(file_path.relative_to(self.test_root)).split(os.sep)[0]:
                        continue
                    
                    try:
                        # Determine target path
                        target_path = level_dir / file_path.name
                        
                        # Handle filename collisions
                        if target_path.exists():
                            # Add a suffix based on the old directory
                            old_dir = file_path.parent.name
                            target_path = level_dir / f"{file_path.stem}_{old_dir}{file_path.suffix}"
                        
                        # Create parent directories if needed
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copy the file first, we'll only remove the original if everything succeeds
                        shutil.copy2(file_path, target_path)
                        
                        # Update imports in the file
                        self._update_imports(target_path)
                        
                        # Log the move
                        self.migration_log["moved_files"].append({
                            "source": str(file_path.relative_to(self.project_root)),
                            "target": str(target_path.relative_to(self.project_root)),
                            "level": level.value
                        })
                        
                        print(f"{Colors.GREEN}Migrated: {file_path.relative_to(self.test_root)} -> {target_path.relative_to(self.test_root)}{Colors.ENDC}")
                    
                    except Exception as e:
                        print(f"{Colors.RED}Error migrating {file_path}: {str(e)}{Colors.ENDC}")
        
        # Save the migration log
        self.migration_log["status"] = "completed"
        self._save_migration_log()
        
        print(f"{Colors.GREEN}Migration completed successfully. {len(self.migration_log['moved_files'])} files migrated.{Colors.ENDC}")
        print(f"{Colors.YELLOW}Note: Original files have not been deleted yet. After verifying the migration,{Colors.ENDC}")
        print(f"{Colors.YELLOW}you can delete them manually or use the --delete-originals flag.{Colors.ENDC}")
        
        return True
    
    def delete_originals(self) -> bool:
        """
        Delete the original files after a successful migration.
        
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self._has_completed_migration():
            print(f"{Colors.RED}No completed migration found. Please migrate first.{Colors.ENDC}")
            return False
        
        # Load the migration log
        self._load_migration_log()
        
        if self.migration_log.get("status") != "completed":
            print(f"{Colors.RED}Migration not completed. Please complete migration first.{Colors.ENDC}")
            return False
        
        # Delete original files
        for file_info in self.migration_log["moved_files"]:
            try:
                source_path = self.project_root / file_info["source"]
                if source_path.exists():
                    source_path.unlink()
                    print(f"{Colors.YELLOW}Deleted original: {file_info['source']}{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.RED}Error deleting {file_info['source']}: {str(e)}{Colors.ENDC}")
        
        # Update the migration log
        self.migration_log["originals_deleted"] = True
        self._save_migration_log()
        
        print(f"{Colors.GREEN}Original files deleted successfully.{Colors.ENDC}")
        return True
    
    def rollback(self) -> bool:
        """
        Rollback the last migration.
        
        Returns:
            True if rollback was successful, False otherwise
        """
        if not self._has_migration_log():
            print(f"{Colors.RED}No migration log found. Nothing to rollback.{Colors.ENDC}")
            return False
        
        # Load the migration log
        self._load_migration_log()
        
        # Check if originals have been deleted
        if self.migration_log.get("originals_deleted", False):
            print(f"{Colors.RED}Original files have been deleted. Cannot rollback.{Colors.ENDC}")
            return False
        
        # Rollback the migration
        for file_info in self.migration_log["moved_files"]:
            try:
                target_path = self.project_root / file_info["target"]
                if target_path.exists():
                    target_path.unlink()
                    print(f"{Colors.YELLOW}Removed migrated file: {file_info['target']}{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.RED}Error rolling back {file_info['target']}: {str(e)}{Colors.ENDC}")
        
        # Delete the migration log
        self.migration_log_path.unlink(missing_ok=True)
        
        print(f"{Colors.GREEN}Rollback completed successfully.{Colors.ENDC}")
        return True
    
    def _update_imports(self, file_path: Path) -> None:
        """
        Update imports in a migrated file.
        
        Args:
            file_path: Path to the migrated file
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Update relative imports that might be broken by the move
        # This is a simplified approach and might need more sophisticated handling
        # for complex import structures
        import_pattern = r"from\s+(\S+)\s+import"
        
        def replace_import(match):
            import_path = match.group(1)
            
            # Handle relative imports
            if import_path.startswith("."):
                # For now, just convert to absolute imports from the app.tests module
                # This is a simplified approach
                return f"from app.tests{import_path[1:]} import"
            
            return match.group(0)
        
        updated_content = re.sub(import_pattern, replace_import, content)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
    
    def _has_migration_log(self) -> bool:
        """
        Check if a migration log exists.
        
        Returns:
            True if a migration log exists, False otherwise
        """
        return self.migration_log_path.exists()
    
    def _has_incomplete_migration(self) -> bool:
        """
        Check if there is an incomplete migration.
        
        Returns:
            True if there is an incomplete migration, False otherwise
        """
        if not self._has_migration_log():
            return False
        
        self._load_migration_log()
        return self.migration_log.get("status") == "in_progress"
    
    def _has_completed_migration(self) -> bool:
        """
        Check if there is a completed migration.
        
        Returns:
            True if there is a completed migration, False otherwise
        """
        if not self._has_migration_log():
            return False
        
        self._load_migration_log()
        return self.migration_log.get("status") == "completed"
    
    def _load_migration_log(self) -> None:
        """Load the migration log from disk."""
        try:
            with open(self.migration_log_path, "r", encoding="utf-8") as f:
                self.migration_log = json.load(f)
        except Exception as e:
            print(f"{Colors.RED}Error loading migration log: {str(e)}{Colors.ENDC}")
            self.migration_log = {}
    
    def _save_migration_log(self) -> None:
        """Save the migration log to disk."""
        try:
            with open(self.migration_log_path, "w", encoding="utf-8") as f:
                json.dump(self.migration_log, f, indent=2)
        except Exception as e:
            print(f"{Colors.RED}Error saving migration log: {str(e)}{Colors.ENDC}")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Novamind Digital Twin Test Migration Tool")
    
    # Migration options
    migration_group = parser.add_mutually_exclusive_group(required=True)
    migration_group.add_argument("--analyze", action="store_true", help="Analyze tests without migrating")
    migration_group.add_argument("--migrate", action="store_true", help="Analyze and migrate tests")
    migration_group.add_argument("--delete-originals", action="store_true", help="Delete original files after migration")
    migration_group.add_argument("--rollback", action="store_true", help="Rollback the last migration")
    
    return parser.parse_args()


def main():
    """Entry point for the script."""
    args = parse_args()
    migrator = TestMigrator()
    
    if args.analyze:
        migration_plan = migrator.analyze()
        migrator.analyzer.print_migration_plan()
    elif args.migrate:
        migrator.migrate()
    elif args.delete_originals:
        migrator.delete_originals()
    elif args.rollback:
        migrator.rollback()


if __name__ == "__main__":
    main()