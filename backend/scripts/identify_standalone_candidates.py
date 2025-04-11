#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone Test Candidate Identifier for Novamind Digital Twin Backend

This script analyzes existing unit tests to identify those that could potentially
be converted to standalone tests (tests with no external dependencies).

Unlike the main test classifier, this script:
- Does NOT modify any files
- Only provides recommendations
- Focuses on finding unit tests that could be easily converted

Usage:
    python identify_standalone_candidates.py
    python identify_standalone_candidates.py --verbose
    python identify_standalone_candidates.py --output candidates.txt
"""

import os
import re
import ast
import sys
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("standalone_identifier")

# Path to the app directory
APP_DIR = Path(__file__).parent.parent
TESTS_DIR = APP_DIR / "app" / "tests"
UNIT_TESTS_DIR = TESTS_DIR / "unit"
STANDALONE_DIR = TESTS_DIR / "standalone"

# Database and network dependency indicators in imports
DATABASE_INDICATORS = {
    "asyncpg", "sqlalchemy", "postgres", "redis", "mongodb", "pymongo", 
    "alembic", "motor", "sqlmodel", "databases", "tortoise", "peewee",
    "pony", "gino", "ormar", "prisma", "neo4j"
}

NETWORK_INDICATORS = {
    "aiohttp", "requests", "httpx", "urllib", "boto", "s3", "azure", 
    "google.cloud", "sagemaker", "http.client", "socket", "websocket",
    "ftplib", "poplib", "imaplib", "smtplib", "telnetlib", "paramiko"
}

# Patterns that indicate specific dependencies
PATTERNS = {
    "database": [
        r"await\s+.*\bquery\b", r"await\s+.*\bexecute\b", r"connection\.fetch", 
        r"\bdatabase\b", r"\bdb\.[a-zA-Z_]+\(", r"session\.query",
        r"\.connect\(", r"psycopg2", r"store_[a-z_]+_in_db", r"repository\.[a-z_]+"
    ],
    "network": [
        r"await\s+.*\.(get|post|put|delete|patch)\(", r"requests\.", r"aiohttp\.", 
        r"httpx\.", r"urlopen\(", r"http://", r"https://", r"socket\.",
        r"client\.get\(", r"client\.post\("
    ]
}

# Classes/functions that indicate mocking instead of real dependencies
MOCK_INDICATORS = [
    r"@?mock", r"MagicMock", r"patch", r"AsyncMock", r"Mock\(", 
    r"@pytest.fixture", r"pytest.fixture"
]

def extract_imports(file_path: Path) -> Dict[str, Set[str]]:
    """Extract all imports from a Python file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        logger.warning(f"Could not parse {file_path}")
        return {"modules": set(), "from_imports": set()}
    
    modules = set()
    from_imports = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                modules.add(name.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                from_imports.add(node.module.split(".")[0])
                for name in node.names:
                    from_imports.add(f"{node.module}.{name.name}")
    
    return {"modules": modules, "from_imports": from_imports}

def analyze_content(file_path: Path) -> Dict[str, bool]:
    """Analyze file content for dependency indicators."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    results = {
        "has_database_dependency": False,
        "has_network_dependency": False,
        "has_mocks": False,
        "has_pytest_marks": False,
        "existing_marks": []
    }
    
    # Check for existing pytest marks
    if "@pytest.mark." in content:
        results["has_pytest_marks"] = True
        mark_matches = re.findall(r"@pytest\.mark\.([a-zA-Z_]+)", content)
        if mark_matches:
            results["existing_marks"] = mark_matches
    
    # Check for mocking
    for pattern in MOCK_INDICATORS:
        if re.search(pattern, content, re.IGNORECASE):
            results["has_mocks"] = True
            break
    
    # Check for database patterns
    for pattern in PATTERNS["database"]:
        if re.search(pattern, content, re.IGNORECASE):
            results["has_database_dependency"] = True
            break
    
    # Check for network patterns
    for pattern in PATTERNS["network"]:
        if re.search(pattern, content, re.IGNORECASE):
            results["has_network_dependency"] = True
            break
    
    return results

def is_standalone_candidate(
    file_path: Path,
    imports: Dict[str, Set[str]],
    content_analysis: Dict[str, bool]
) -> Dict[str, any]:
    """Determine if a test file is a candidate for standalone conversion."""
    
    # Check if it's already in standalone or has standalone marker
    if "standalone" in str(file_path) or "standalone" in content_analysis.get("existing_marks", []):
        return {
            "is_candidate": False,
            "reason": "Already a standalone test",
            "confidence": 1.0
        }
    
    # Check if it has database or network dependencies without mocks
    all_imports = imports["modules"].union(imports["from_imports"])
    has_db_imports = any(db in all_imports for db in DATABASE_INDICATORS)
    has_net_imports = any(net in all_imports for net in NETWORK_INDICATORS)
    
    if (has_db_imports or content_analysis["has_database_dependency"]) and not content_analysis["has_mocks"]:
        return {
            "is_candidate": False,
            "reason": "Has database dependencies without mocking",
            "confidence": 0.9
        }
    
    if (has_net_imports or content_analysis["has_network_dependency"]) and not content_analysis["has_mocks"]:
        return {
            "is_candidate": False,
            "reason": "Has network dependencies without mocking",
            "confidence": 0.9
        }
    
    # If it has external dependencies but also has mocks, it's a potential candidate
    if (has_db_imports or has_net_imports or 
        content_analysis["has_database_dependency"] or 
        content_analysis["has_network_dependency"]) and content_analysis["has_mocks"]:
        return {
            "is_candidate": True,
            "reason": "Has mocked dependencies",
            "confidence": 0.7
        }
    
    # If no external dependencies detected, it's a strong candidate
    return {
        "is_candidate": True,
        "reason": "No external dependencies detected",
        "confidence": 0.9
    }

def count_test_functions(file_path: Path) -> int:
    """Count the number of test functions in a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return 0
    
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            count += 1
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            # Count methods in test classes
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name.startswith("test_"):
                    count += 1
    
    return count

def find_unit_test_files() -> List[Path]:
    """Find all unit test files."""
    result = []
    if UNIT_TESTS_DIR.exists():
        for root, _, files in os.walk(UNIT_TESTS_DIR):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    result.append(Path(root) / file)
    return result

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Identify unit tests that could be converted to standalone tests"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", help="Output report to file")
    args = parser.parse_args()
    
    logger.info("Finding unit test files...")
    unit_test_files = find_unit_test_files()
    logger.info(f"Found {len(unit_test_files)} unit test files")
    
    candidates = []
    non_candidates = []
    
    for file_path in unit_test_files:
        # Extract file information
        imports = extract_imports(file_path)
        content_analysis = analyze_content(file_path)
        analysis = is_standalone_candidate(file_path, imports, content_analysis)
        test_count = count_test_functions(file_path)
        
        # Add file info to appropriate list
        file_info = {
            "path": str(file_path.relative_to(APP_DIR)),
            "test_count": test_count,
            "reason": analysis["reason"],
            "confidence": analysis["confidence"],
            "has_mocks": content_analysis["has_mocks"],
            "existing_marks": content_analysis.get("existing_marks", [])
        }
        
        if analysis["is_candidate"]:
            candidates.append(file_info)
        else:
            non_candidates.append(file_info)
    
    # Sort candidates by confidence (highest first)
    candidates.sort(key=lambda x: (x["confidence"], x["test_count"]), reverse=True)
    
    # Generate report
    report = "\n" + "=" * 80 + "\n"
    report += "NOVAMIND STANDALONE TEST CANDIDATE REPORT\n"
    report += "=" * 80 + "\n\n"
    
    total_candidates = len(candidates)
    total_tests = sum(item["test_count"] for item in candidates)
    
    report += f"Total unit test files analyzed: {len(unit_test_files)}\n"
    report += f"Potential standalone test files: {total_candidates}\n"
    report += f"Potential standalone test functions: {total_tests}\n\n"
    
    report += "TOP STANDALONE CANDIDATES:\n"
    report += "-" * 40 + "\n"
    
    # List top candidates
    for i, candidate in enumerate(candidates[:20]):  # Show top 20
        path = candidate["path"]
        tests = candidate["test_count"]
        reason = candidate["reason"]
        confidence = candidate["confidence"] * 100
        
        report += f"{i+1}. {path}\n"
        report += f"   Tests: {tests}, Confidence: {confidence:.0f}%, Reason: {reason}\n"
        
        if args.verbose:
            marks = ", ".join(candidate["existing_marks"]) if candidate["existing_marks"] else "None"
            report += f"   Existing markers: {marks}\n"
            report += f"   Has mocks: {'Yes' if candidate['has_mocks'] else 'No'}\n"
            
        report += "\n"
    
    # Conversion recommendations
    report += "RECOMMENDATIONS:\n"
    report += "-" * 40 + "\n"
    
    report += "1. Start with high-confidence candidates (90%+) that have few tests\n"
    report += "2. Create a copy in the standalone directory rather than moving\n"
    report += "3. Add the @pytest.mark.standalone decorator to tests\n"
    report += "4. Run the tests to verify they pass in standalone mode\n"
    report += "5. If successful, consider moving to the standalone directory\n\n"
    
    # Example conversion
    report += "EXAMPLE CONVERSION:\n"
    report += "-" * 40 + "\n"
    if candidates:
        example = candidates[0]["path"]
        report += f"For test file {example}:\n"
        report += "1. Create a copy in the standalone directory:\n"
        report += f"   cp {example} app/tests/standalone/\n\n"
        report += "2. Add standalone marker to tests in the copied file:\n"
        report += "   @pytest.mark.standalone\n"
        report += "   def test_function():\n"
        report += "       ...\n\n"
        report += "3. Test the standalone version:\n"
        report += "   python -m pytest app/tests/standalone/test_specific_file.py -v\n"
    
    # Write report to file or print
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"Report written to {args.output}")
    else:
        print(report)

if __name__ == "__main__":
    main()