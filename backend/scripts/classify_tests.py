#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Classification Tool for Novamind Digital Twin Platform

This script analyzes the test files to determine their dependency requirements and
optionally adds appropriate markers to the test files.

The dependency levels are:
- Standalone: No dependencies beyond Python itself
- VENV-dependent: Require Python packages but no external services
- DB-dependent: Require database connections or other external services

Usage:
    python -m scripts.classify_tests [options]

Options:
    --update           Update test files with appropriate markers (default: False)
    --verbose          Show detailed classification information (default: False)
    --dry-run          Show what would be updated without making changes (default: False)
    --report-only      Only generate reports without any file operations (default: False)
"""

import argparse
import logging
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union, Iterator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@dataclass
class TestFileInfo:
    """Information about a test file."""
    path: Path
    imports: Set[str]
    markers: Set[str]
    dependencies: Set[str]
    skipped: bool = False
    
    @property
    def category(self) -> str:
        """Determine the test category based on dependencies."""
        if self.skipped:
            return "skipped"
        if len(self.dependencies) == 0:
            return "standalone"
        if any(dep in self.dependencies for dep in ["database", "redis", "external_api", "network"]):
            return "db_required"
        return "venv_only"


class TestClassifier:
    """
    Test classifier for categorizing test files by dependency.
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize the classifier.
        
        Args:
            project_root: Path to the project root
        """
        self.project_root = project_root
        self.test_dir = project_root / "app" / "tests"
        self.standalone_dir = self.test_dir / "standalone"
        self.test_files: Dict[Path, TestFileInfo] = {}

    def find_test_files(self) -> List[Path]:
        """
        Find all test files in the project.
        
        Returns:
            List of paths to test files
        """
        test_files = []
        
        # Walk through the test directory
        for root, _, files in os.walk(self.test_dir):
            root_path = Path(root)
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    test_files.append(root_path / file)
        
        return test_files

    def extract_imports(self, content: str) -> Set[str]:
        """
        Extract import statements from file content.
        
        Args:
            content: File content
            
        Returns:
            Set of imported modules
        """
        imports = set()
        
        # Find all import statements
        import_pattern = re.compile(r'^(?:from|import)\s+([\w.]+)', re.MULTILINE)
        for match in import_pattern.finditer(content):
            imports.add(match.group(1).split('.')[0])
        
        return imports

    def extract_markers(self, content: str) -> Set[str]:
        """
        Extract pytest markers from file content.
        
        Args:
            content: File content
            
        Returns:
            Set of pytest markers
        """
        markers = set()
        
        # Find all pytest markers
        marker_pattern = re.compile(r'@pytest\.mark\.(\w+)')
        for match in marker_pattern.finditer(content):
            markers.add(match.group(1))
        
        return markers

    def determine_dependencies(self, imports: Set[str], file_path: Path, content: str) -> Set[str]:
        """
        Determine dependencies based on imports and file content.
        
        Args:
            imports: Set of imported modules
            file_path: Path to the file
            content: File content
            
        Returns:
            Set of dependencies
        """
        dependencies = set()
        
        # Database dependencies
        db_indicators = ["sqlalchemy", "databases", "postgres", "mysql", "sqlite", "mongodb"]
        if any(indicator in imports for indicator in db_indicators) or "database" in content.lower():
            dependencies.add("database")
        
        # Redis dependencies
        redis_indicators = ["redis", "aioredis"]
        if any(indicator in imports for indicator in redis_indicators) or "redis" in content.lower():
            dependencies.add("redis")
        
        # External API dependencies
        api_indicators = ["requests", "aiohttp", "httpx"]
        if any(indicator in imports for indicator in api_indicators) or re.search(r'https?://', content):
            dependencies.add("external_api")
        
        # Network dependencies
        network_indicators = ["socket", "asyncio.streams"]
        if any(indicator in imports for indicator in network_indicators):
            dependencies.add("network")
        
        # Check for pytest.mark.db_required or similar markers
        if "db_required" in self.extract_markers(content):
            dependencies.add("database")
        
        # Exclude standalone tests
        if "standalone" in self.extract_markers(content) or "standalone" in file_path.parts:
            # Standalone tests should have no dependencies
            return set()
        
        return dependencies

    def is_skipped(self, content: str) -> bool:
        """
        Check if the test file is skipped.
        
        Args:
            content: File content
            
        Returns:
            True if the test file is skipped, False otherwise
        """
        # Check for pytest.mark.skip
        if re.search(r'@pytest\.mark\.skip', content):
            return True
        
        # Check for pytest.mark.skipif
        if re.search(r'@pytest\.mark\.skipif', content):
            return True
        
        return False

    def classify_file(self, file_path: Path) -> TestFileInfo:
        """
        Classify a test file.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            TestFileInfo object
        """
        with open(file_path, 'r') as f:
            content = f.read()
        
        imports = self.extract_imports(content)
        markers = self.extract_markers(content)
        dependencies = self.determine_dependencies(imports, file_path, content)
        skipped = self.is_skipped(content)
        
        return TestFileInfo(
            path=file_path,
            imports=imports,
            markers=markers,
            dependencies=dependencies,
            skipped=skipped
        )

    def classify_all_files(self) -> None:
        """Classify all test files."""
        test_files = self.find_test_files()
        logger.info(f"Found {len(test_files)} test files")
        
        for file_path in test_files:
            file_info = self.classify_file(file_path)
            self.test_files[file_path] = file_info

    def get_marker_for_category(self, category: str) -> str:
        """
        Get the appropriate pytest marker for a category.
        
        Args:
            category: Test category
            
        Returns:
            Pytest marker
        """
        if category == "standalone":
            return "standalone"
        elif category == "venv_only":
            return "venv_only"
        elif category == "db_required":
            return "db_required"
        else:
            return ""

    def update_test_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """
        Update a test file with appropriate markers.
        
        Args:
            file_path: Path to the test file
            dry_run: Whether to perform a dry run
            
        Returns:
            True if the file was updated, False otherwise
        """
        file_info = self.test_files[file_path]
        marker = self.get_marker_for_category(file_info.category)
        
        # Don't add markers to skipped tests
        if file_info.skipped or not marker:
            return False
        
        # Read the content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if the marker is already present
        if f"@pytest.mark.{marker}" in content:
            return False
        
        # Find test functions and classes
        class_pattern = re.compile(r'^class\s+(\w+)(?:\([^)]*\))?:', re.MULTILINE)
        function_pattern = re.compile(r'^def\s+test_\w+\(', re.MULTILINE)
        
        # Add markers to test classes
        modified_content = content
        for match in class_pattern.finditer(content):
            marker_line = f"@pytest.mark.{marker}\n"
            # Check if there are already markers
            if "@pytest.mark." not in content[max(0, match.start() - 100):match.start()]:
                insert_pos = match.start()
                modified_content = modified_content[:insert_pos] + marker_line + modified_content[insert_pos:]
        
        # Add markers to test functions (if they're not already in a marked class)
        for match in function_pattern.finditer(content):
            marker_line = f"@pytest.mark.{marker}\n"
            context = content[max(0, match.start() - 200):match.start()]
            # If this function is not part of a class or the class doesn't have our marker
            if "class " not in context or f"@pytest.mark.{marker}" not in context:
                # And it doesn't already have our marker
                if f"@pytest.mark.{marker}" not in context:
                    insert_pos = match.start()
                    modified_content = modified_content[:insert_pos] + marker_line + modified_content[insert_pos:]
        
        # Check if we made any changes
        if content == modified_content:
            return False
        
        # Write the updated content
        if not dry_run:
            with open(file_path, 'w') as f:
                f.write(modified_content)
            logger.info(f"Updated {file_path.relative_to(self.project_root)} with {marker} marker")
        else:
            logger.info(f"Would update {file_path.relative_to(self.project_root)} with {marker} marker (dry run)")
        
        return True

    def update_all_files(self, dry_run: bool = False) -> int:
        """
        Update all test files with appropriate markers.
        
        Args:
            dry_run: Whether to perform a dry run
            
        Returns:
            Number of updated files
        """
        updated_count = 0
        
        for file_path in self.test_files:
            if self.update_test_file(file_path, dry_run):
                updated_count += 1
                
        return updated_count

    def generate_report(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Generate a report of test file classification.
        
        Args:
            verbose: Whether to include detailed information
            
        Returns:
            Report dictionary
        """
        # Count by category
        category_counts = defaultdict(int)
        categories = {}
        
        for file_path, file_info in self.test_files.items():
            relative_path = file_path.relative_to(self.project_root)
            category = file_info.category
            category_counts[category] += 1
            
            if category not in categories:
                categories[category] = []
                
            if verbose:
                categories[category].append({
                    "path": str(relative_path),
                    "imports": list(file_info.imports),
                    "markers": list(file_info.markers),
                    "dependencies": list(file_info.dependencies),
                    "skipped": file_info.skipped
                })
            else:
                categories[category].append(str(relative_path))
        
        report = {
            "total_files": len(self.test_files),
            "category_counts": dict(category_counts),
            "categories": categories
        }
        
        return report

    def print_report(self, verbose: bool = False) -> None:
        """
        Print a report of test file classification.
        
        Args:
            verbose: Whether to include detailed information
        """
        report = self.generate_report(verbose)
        
        print("\n" + "="*80)
        print("Test Classification Report")
        print("="*80)
        
        print(f"\nTotal test files: {report['total_files']}")
        
        # Print counts by category
        print("\nCounts by category:")
        for category, count in report['category_counts'].items():
            print(f"  {category}: {count}")
        
        # Print categories
        if verbose:
            print("\nDetailed report by category:")
            for category, files in report['categories'].items():
                print(f"\n{category.upper()} ({len(files)} files):")
                for file_info in files:
                    print(f"  {file_info['path']}")
                    print(f"    imports: {', '.join(file_info['imports'])}")
                    print(f"    markers: {', '.join(file_info['markers'])}")
                    print(f"    dependencies: {', '.join(file_info['dependencies'])}")
                    print(f"    skipped: {file_info['skipped']}")
        else:
            # Print just file counts per category for non-verbose mode
            print("\nTest files by category (counts):")
            for category, files in report['categories'].items():
                print(f"\n{category.upper()} ({len(files)} files)")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Classify test files by dependency")
    parser.add_argument(
        "--update", action="store_true", help="Update test files with appropriate markers"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed classification information"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be updated without making changes"
    )
    parser.add_argument(
        "--report-only", action="store_true", help="Only generate reports without any file operations"
    )
    
    args = parser.parse_args()
    
    # Find the project root
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent  # Assuming this script is in the scripts directory
    
    # Create classifier
    classifier = TestClassifier(project_root)
    
    # Classify all files
    classifier.classify_all_files()
    
    # Print report
    classifier.print_report(args.verbose)
    
    # Update files if requested
    if args.update and not args.report_only:
        updated_count = classifier.update_all_files(dry_run=args.dry_run)
        if args.dry_run:
            logger.info(f"Would update {updated_count} files (dry run)")
        else:
            logger.info(f"Updated {updated_count} files")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())