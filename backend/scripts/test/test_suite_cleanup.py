#!/usr/bin/env python
"""
Novamind Digital Twin Test Suite Cleanup

This is the master script for cleaning up and reorganizing the Novamind Digital Twin
test suite. It coordinates the entire process, from analysis to migration to verification.

Usage:
    python test_suite_cleanup.py --all
    python test_suite_cleanup.py --step 1  # Run specific step
    python test_suite_cleanup.py --steps 1,2,3  # Run specific steps
"""

import os
import sys
import argparse
import subprocess
import json
import datetime
from pathlib import Path
from typing import List, Optional


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


class TestSuiteCleanup:
    """
    Orchestrates the test suite cleanup process.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the test suite cleanup.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path(__file__).resolve().parents[3]
        self.scripts_dir = self.project_root / "scripts" / "test"
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backend_dir = self.project_root
        print(f"Project root: {self.project_root}")
        
    def analyze_tests(self) -> str:
        """
        Step 1: Analyze test files and categorize them.
        
        Returns:
            Path to the analysis results file
        """
        print(f"{Colors.HEADER}Step 1: Analyzing tests...{Colors.ENDC}")
        
        analyzer_path = self.scripts_dir / "tools" / "test_analyzer.py"
        output_file = f"test_classification_report_{self.timestamp}.json"
        output_path = self.project_root / output_file
        
        result = subprocess.run(
            [sys.executable, str(analyzer_path), "--output-file", str(output_path)],
            cwd=str(self.project_root),
            check=False,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"{Colors.RED}Error analyzing tests:{Colors.ENDC}")
            print(result.stderr)
            sys.exit(1)
        
        print(result.stdout)
        print(f"{Colors.GREEN}Test analysis completed. Report saved to {output_file}{Colors.ENDC}")
        return str(output_path)
    
    def setup_directory_structure(self) -> None:
        """
        Step 2: Set up the canonical directory structure.
        """
        print(f"{Colors.HEADER}Step 2: Setting up directory structure...{Colors.ENDC}")
        
        tests_dir = self.project_root / "backend" / "app" / "tests"
        print(f"Setting up test structure in: {tests_dir}")
        
        # Create main dependency level directories
        for level in ["standalone", "venv", "integration"]:
            level_dir = tests_dir / level
            level_dir.mkdir(exist_ok=True)
            print(f"Created directory: {level_dir}")
            
            # Create __init__.py in level directory
            (level_dir / "__init__.py").touch(exist_ok=True)
            
            # Create component directories within each level
            for component in ["domain", "application", "infrastructure", "api", "core"]:
                component_dir = level_dir / component
                component_dir.mkdir(exist_ok=True)
                
                # Create __init__.py in component directory
                (component_dir / "__init__.py").touch(exist_ok=True)
        
        print(f"{Colors.GREEN}Directory structure created successfully.{Colors.ENDC}")
    
    def prepare_migration(self, analysis_file: str) -> None:
        """
        Step 3: Prepare for test migration.
        
        Args:
            analysis_file: Path to the analysis results file
        """
        print(f"{Colors.HEADER}Step 3: Preparing for migration...{Colors.ENDC}")
        
        # Load analysis results
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        
        # Print summary statistics
        total_tests = analysis.get("total_tests", 0)
        dependency_counts = analysis.get("dependency_counts", {})
        syntax_errors = analysis.get("syntax_errors", 0)
        
        print(f"Total tests found: {total_tests}")
        print("Dependency levels:")
        for level, count in dependency_counts.items():
            print(f"  {level}: {count}")
        print(f"Files with syntax errors: {syntax_errors}")
        
        # Create conftest.py files if they don't exist
        for level in ["standalone", "venv", "integration"]:
            conftest_path = self.project_root / "backend" / "app" / "tests" / level / "conftest.py"
            if not conftest_path.exists():
                print(f"Creating {conftest_path}")
                conftest_content = f"""\"\"\"
{level.capitalize()} Test Configuration and Fixtures

This file contains test fixtures specific to {level} tests.
\"\"\"

import pytest


@pytest.fixture
def {level}_fixture():
    \"\"\"Basic fixture for {level} tests.\"\"\"
    return "{level}_fixture"
"""
                with open(conftest_path, 'w', encoding='utf-8') as f:
                    f.write(conftest_content)
        
        print(f"{Colors.GREEN}Migration preparation completed.{Colors.ENDC}")
    
    def migrate_tests(self, analysis_file: str, dry_run: bool = False) -> None:
        """
        Step 4: Migrate tests to the new structure.
        
        Args:
            analysis_file: Path to the analysis results file
            dry_run: If True, don't actually move files
        """
        print(f"{Colors.HEADER}Step 4: Migrating tests...{Colors.ENDC}")
        
        migrator_path = self.scripts_dir / "migrations" / "migrate_tests.py"
        
        args = [
            sys.executable,
            str(migrator_path),
            "--analysis-file", analysis_file
        ]
        
        if dry_run:
            args.append("--dry-run")
        
        result = subprocess.run(
            args,
            cwd=str(self.project_root),
            check=False,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"{Colors.RED}Error migrating tests:{Colors.ENDC}")
            print(result.stderr)
            sys.exit(1)
        
        print(result.stdout)
        print(f"{Colors.GREEN}Test migration completed.{Colors.ENDC}")
    
    def verify_migration(self) -> None:
        """
        Step 5: Verify the migration by running tests.
        """
        print(f"{Colors.HEADER}Step 5: Verifying migration...{Colors.ENDC}")
        
        runner_path = self.scripts_dir / "runners" / "run_tests.py"
        
        # Run standalone tests first
        print("Running standalone tests...")
        result = subprocess.run(
            [sys.executable, str(runner_path), "--standalone", "--verbose"],
            cwd=str(self.project_root),
            check=False,
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.returncode != 0:
            print(f"{Colors.YELLOW}Some standalone tests failed. This might need investigation.{Colors.ENDC}")
        else:
            print(f"{Colors.GREEN}All standalone tests passed.{Colors.ENDC}")
        
        # Run venv tests
        print("\nRunning venv tests...")
        result = subprocess.run(
            [sys.executable, str(runner_path), "--venv", "--verbose"],
            cwd=str(self.project_root),
            check=False,
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.returncode != 0:
            print(f"{Colors.YELLOW}Some venv tests failed. This might need investigation.{Colors.ENDC}")
        else:
            print(f"{Colors.GREEN}All venv tests passed.{Colors.ENDC}")
        
        # Run integration tests
        print("\nRunning integration tests...")
        result = subprocess.run(
            [sys.executable, str(runner_path), "--integration", "--verbose"],
            cwd=str(self.project_root),
            check=False,
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.returncode != 0:
            print(f"{Colors.YELLOW}Some integration tests failed. This might need investigation.{Colors.ENDC}")
        else:
            print(f"{Colors.GREEN}All integration tests passed.{Colors.ENDC}")
    
    def update_import_paths(self) -> None:
        """
        Step 6: Update import paths in test files.
        """
        print(f"{Colors.HEADER}Step 6: Updating import paths...{Colors.ENDC}")
        
        tests_dir = self.project_root / "app" / "tests"
        
        # Walk through all test files in the new structure
        for level in ["standalone", "venv", "integration"]:
            level_dir = tests_dir / level
            
            for root, dirs, files in os.walk(str(level_dir)):
                for file in files:
                    if file.startswith("test_") and file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        self._fix_imports(file_path)
        
        print(f"{Colors.GREEN}Import paths updated.{Colors.ENDC}")
    
    def _fix_imports(self, file_path: str) -> None:
        """
        Fix imports in a specific file.
        
        Args:
            file_path: Path to the file to fix
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix relative imports that might be broken
            # This is a simplified version - a real implementation would need more sophisticated parsing
            fixed_content = content.replace('from ..', 'from backend.app.')
            fixed_content = fixed_content.replace('from .', 'from backend.app.tests.')
            
            # Write back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"Fixed imports in {file_path}")
        except Exception as e:
            print(f"Error fixing imports in {file_path}: {str(e)}")
    
    def fix_broken_tests(self) -> None:
        """
        Step 7: Attempt to fix common issues in broken tests.
        """
        print(f"{Colors.HEADER}Step 7: Fixing broken tests...{Colors.ENDC}")
        
        # Run the test suite to identify broken tests
        tests_dir = self.project_root / "app" / "tests"
        
        # For now, we'll just print a message about this step
        print("This step would involve:")
        print("1. Running the test suite to identify broken tests")
        print("2. Automatically fixing common issues (import errors, missing fixtures)")
        print("3. Generating a report of tests that need manual attention")
        
        print(f"{Colors.YELLOW}This step requires implementation based on the specific errors found.{Colors.ENDC}")
    
    def cleanup_original_tests(self) -> None:
        """
        Step 8: Remove original test files that have been migrated.
        """
        print(f"{Colors.HEADER}Step 8: Cleaning up original test files...{Colors.ENDC}")
        
        # This is a dangerous operation so we'll just print a message
        print(f"{Colors.YELLOW}CAUTION: This step would remove original test files.{Colors.ENDC}")
        print("To perform this cleanup, you should:")
        print("1. Verify that all tests have been migrated successfully")
        print("2. Backup the original test files")
        print("3. Run a manual cleanup operation after confirming migration success")
        
        print(f"{Colors.YELLOW}Skipping actual deletion for safety.{Colors.ENDC}")
    
    def run_step(self, step: int, analysis_file: Optional[str] = None) -> Optional[str]:
        """
        Run a specific step of the cleanup process.
        
        Args:
            step: Step number to run
            analysis_file: Path to an existing analysis file (for steps 3+)
            
        Returns:
            Path to the analysis file if generated
        """
        if step == 1:
            return self.analyze_tests()
        elif step == 2:
            self.setup_directory_structure()
        elif step == 3:
            if not analysis_file:
                print(f"{Colors.RED}Analysis file is required for step 3.{Colors.ENDC}")
                sys.exit(1)
            self.prepare_migration(analysis_file)
        elif step == 4:
            if not analysis_file:
                print(f"{Colors.RED}Analysis file is required for step 4.{Colors.ENDC}")
                sys.exit(1)
            self.migrate_tests(analysis_file)
        elif step == 5:
            self.verify_migration()
        elif step == 6:
            self.update_import_paths()
        elif step == 7:
            self.fix_broken_tests()
        elif step == 8:
            self.cleanup_original_tests()
        else:
            print(f"{Colors.RED}Invalid step number: {step}{Colors.ENDC}")
            sys.exit(1)
        
        return None
    
    def run_all_steps(self) -> None:
        """
        Run all steps of the cleanup process in sequence.
        """
        analysis_file = self.run_step(1)
        self.run_step(2)
        self.run_step(3, analysis_file)
        self.run_step(4, analysis_file)
        self.run_step(5)
        self.run_step(6)
        self.run_step(7)
        # Step 8 (cleanup) is intentionally omitted for safety


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Novamind Digital Twin Test Suite Cleanup")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Run all steps in sequence"
    )
    group.add_argument(
        "--step",
        type=int,
        help="Run a specific step"
    )
    group.add_argument(
        "--steps",
        type=str,
        help="Run specific steps (comma-separated list)"
    )
    
    parser.add_argument(
        "--analysis-file",
        type=str,
        help="Path to an existing analysis file"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the test suite cleanup."""
    args = parse_args()
    
    cleanup = TestSuiteCleanup()
    
    if args.all:
        cleanup.run_all_steps()
    elif args.step:
        cleanup.run_step(args.step, args.analysis_file)
    elif args.steps:
        analysis_file = args.analysis_file
        steps = [int(s.strip()) for s in args.steps.split(",")]
        for step in steps:
            if step == 1:
                analysis_file = cleanup.run_step(step, analysis_file)
            else:
                cleanup.run_step(step, analysis_file)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())