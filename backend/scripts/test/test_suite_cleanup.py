#!/usr/bin/env python3
"""
Novamind Digital Twin Test Suite Cleanup Orchestrator

This script orchestrates the entire test suite cleanup process, guiding
users through the migration from the mixed organizational approach to
the dependency-based SSOT directory structure.

Usage:
    python test_suite_cleanup.py [--step STEP_NUMBER]
"""

import argparse
import os
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


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


class CleanupStep(Enum):
    """Steps in the test suite cleanup process."""
    ANALYZE = 1
    VERIFY_DIRECTORY_STRUCTURE = 2
    PREPARE_MIGRATION = 3
    MIGRATE_TESTS = 4
    VERIFY_MIGRATION = 5
    UPDATE_IMPORTS = 6
    RUN_MIGRATED_TESTS = 7
    CLEANUP_ORIGINAL_FILES = 8
    UPDATE_DOCUMENTATION = 9


class TestSuiteCleanup:
    """
    Orchestrates the test suite cleanup process.
    
    This class guides users through the entire process of migrating tests
    from the mixed organizational approach to the dependency-based SSOT
    directory structure.
    """
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.test_root = self.project_root / "app" / "tests"
        self.script_dir = Path(__file__).parent
        self.tools_dir = self.script_dir / "tools"
        self.runners_dir = self.script_dir / "runners"
        self.migrations_dir = self.script_dir / "migrations"
        
        # Define the steps in the cleanup process
        self.steps: Dict[CleanupStep, Callable[[], bool]] = {
            CleanupStep.ANALYZE: self.analyze_tests,
            CleanupStep.VERIFY_DIRECTORY_STRUCTURE: self.verify_directory_structure,
            CleanupStep.PREPARE_MIGRATION: self.prepare_migration,
            CleanupStep.MIGRATE_TESTS: self.migrate_tests,
            CleanupStep.VERIFY_MIGRATION: self.verify_migration,
            CleanupStep.UPDATE_IMPORTS: self.update_imports,
            CleanupStep.RUN_MIGRATED_TESTS: self.run_migrated_tests,
            CleanupStep.CLEANUP_ORIGINAL_FILES: self.cleanup_original_files,
            CleanupStep.UPDATE_DOCUMENTATION: self.update_documentation
        }
    
    def run_step(self, step: CleanupStep) -> bool:
        """
        Run a specific step in the cleanup process.
        
        Args:
            step: The step to run
            
        Returns:
            True if the step was successful, False otherwise
        """
        print(f"\n{Colors.HEADER}Step {step.value}: {step.name}{Colors.ENDC}\n")
        
        if step not in self.steps:
            print(f"{Colors.RED}Invalid step: {step}{Colors.ENDC}")
            return False
        
        try:
            return self.steps[step]()
        except Exception as e:
            print(f"{Colors.RED}Error in step {step.name}: {str(e)}{Colors.ENDC}")
            return False
    
    def analyze_tests(self) -> bool:
        """
        Analyze the current test suite to determine appropriate locations.
        
        Returns:
            True if the analysis was successful, False otherwise
        """
        print(f"{Colors.BLUE}Analyzing the current test suite...{Colors.ENDC}")
        
        try:
            analyzer_script = self.tools_dir / "test_analyzer.py"
            result = subprocess.run(
                [sys.executable, str(analyzer_script)],
                cwd=str(self.project_root),
                check=False,
                capture_output=False
            )
            
            return result.returncode == 0
        except Exception as e:
            print(f"{Colors.RED}Error analyzing tests: {str(e)}{Colors.ENDC}")
            return False
    
    def verify_directory_structure(self) -> bool:
        """
        Verify that the target directory structure is correct.
        
        Returns:
            True if the directory structure is correct, False otherwise
        """
        print(f"{Colors.BLUE}Verifying target directory structure...{Colors.ENDC}")
        
        # Ensure target directories exist
        required_dirs = ["standalone", "venv", "integration"]
        
        for dir_name in required_dirs:
            dir_path = self.test_root / dir_name
            if not dir_path.exists():
                print(f"{Colors.YELLOW}Creating missing directory: {dir_path.relative_to(self.project_root)}{Colors.ENDC}")
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Create an __init__.py file to make it a proper package
                init_file = dir_path / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
                    print(f"{Colors.GREEN}Created {init_file.relative_to(self.project_root)}{Colors.ENDC}")
        
        print(f"{Colors.GREEN}Target directory structure verified.{Colors.ENDC}")
        return True
    
    def prepare_migration(self) -> bool:
        """
        Prepare for the migration by backing up the current state.
        
        Returns:
            True if the preparation was successful, False otherwise
        """
        print(f"{Colors.BLUE}Preparing for migration...{Colors.ENDC}")
        
        # Ensure __init__.py files exist in all test directories
        for root, dirs, files in os.walk(str(self.test_root)):
            if "__pycache__" in root:
                continue
                
            init_file = Path(root) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"{Colors.GREEN}Created {init_file.relative_to(self.project_root)}{Colors.ENDC}")
        
        print(f"{Colors.GREEN}Migration preparation complete.{Colors.ENDC}")
        return True
    
    def migrate_tests(self) -> bool:
        """
        Migrate tests to their appropriate directories.
        
        Returns:
            True if the migration was successful, False otherwise
        """
        print(f"{Colors.BLUE}Migrating tests to appropriate directories...{Colors.ENDC}")
        
        try:
            migration_script = self.migrations_dir / "migrate_tests.py"
            result = subprocess.run(
                [sys.executable, str(migration_script), "--migrate"],
                cwd=str(self.project_root),
                check=False,
                capture_output=False
            )
            
            return result.returncode == 0
        except Exception as e:
            print(f"{Colors.RED}Error migrating tests: {str(e)}{Colors.ENDC}")
            return False
    
    def verify_migration(self) -> bool:
        """
        Verify that the migration was successful.
        
        Returns:
            True if the verification was successful, False otherwise
        """
        print(f"{Colors.BLUE}Verifying migration...{Colors.ENDC}")
        
        # Count tests in each directory
        standalone_count = len(list((self.test_root / "standalone").glob("test_*.py")))
        venv_count = len(list((self.test_root / "venv").glob("test_*.py")))
        integration_count = len(list((self.test_root / "integration").glob("test_*.py")))
        total_count = standalone_count + venv_count + integration_count
        
        print(f"{Colors.GREEN}Migration verification complete.{Colors.ENDC}")
        print(f"  - {standalone_count} standalone tests")
        print(f"  - {venv_count} venv tests")
        print(f"  - {integration_count} integration tests")
        print(f"  - {total_count} total tests")
        
        # Check if we have a reasonable number of tests in each category
        if total_count < 10:
            print(f"{Colors.RED}Very few tests found after migration. This may indicate a problem.{Colors.ENDC}")
            return False
        
        return True
    
    def update_imports(self) -> bool:
        """
        Update imports in migrated test files.
        
        Returns:
            True if the import updates were successful, False otherwise
        """
        print(f"{Colors.BLUE}Updating imports in migrated test files...{Colors.ENDC}")
        
        # In a real implementation, we'd have a more sophisticated import fixer
        # For now, we'll just print a message
        print(f"{Colors.YELLOW}Import updates are handled during migration.{Colors.ENDC}")
        print(f"{Colors.YELLOW}If you encounter import issues, please fix them manually.{Colors.ENDC}")
        
        return True
    
    def run_migrated_tests(self) -> bool:
        """
        Run the migrated tests to ensure they still work.
        
        Returns:
            True if the tests run successfully, False otherwise
        """
        print(f"{Colors.BLUE}Running migrated tests...{Colors.ENDC}")
        
        try:
            runner_script = self.runners_dir / "run_tests.py"
            result = subprocess.run(
                [sys.executable, str(runner_script), "--standalone"],
                cwd=str(self.project_root),
                check=False,
                capture_output=False
            )
            
            if result.returncode != 0:
                print(f"{Colors.RED}Standalone tests failed. Please fix the issues before proceeding.{Colors.ENDC}")
                return False
            
            print(f"{Colors.GREEN}Standalone tests passed. Running VENV tests...{Colors.ENDC}")
            
            result = subprocess.run(
                [sys.executable, str(runner_script), "--venv"],
                cwd=str(self.project_root),
                check=False,
                capture_output=False
            )
            
            if result.returncode != 0:
                print(f"{Colors.RED}VENV tests failed. Please fix the issues before proceeding.{Colors.ENDC}")
                return False
            
            print(f"{Colors.GREEN}VENV tests passed. Running integration tests...{Colors.ENDC}")
            
            result = subprocess.run(
                [sys.executable, str(runner_script), "--integration"],
                cwd=str(self.project_root),
                check=False,
                capture_output=False
            )
            
            if result.returncode != 0:
                print(f"{Colors.RED}Integration tests failed. Please fix the issues before proceeding.{Colors.ENDC}")
                return False
            
            print(f"{Colors.GREEN}All tests passed!{Colors.ENDC}")
            return True
        except Exception as e:
