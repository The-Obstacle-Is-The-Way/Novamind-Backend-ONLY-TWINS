#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Test generator script for modules with low coverage.
This script identifies modules with low test coverage and generates
appropriate test files for them, focusing on HIPAA-critical modules first.
"""

import os
import sys
import importlib
import inspect
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional


def run_coverage_analysis():
    """Run coverage analysis to identify modules with low coverage."""
    print("Running coverage analysis...")
    
    # Run pytest with coverage
    subprocess.run(
        ["pytest", "--cov=app", "--cov-report=json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Check if coverage JSON was generated
    if not os.path.exists(".coverage.json"):
        print("Error: Failed to generate coverage data.")
        return None
    
    # Parse coverage data
    with open(".coverage.json", "r") as f:
        coverage_data = json.load(f)
    
    return coverage_data


def identify_low_coverage_modules(coverage_data, threshold=50):
    """Identify modules with coverage below the threshold."""
    if not coverage_data or "files" not in coverage_data:
        print("No coverage data found.")
        return []
    
    low_coverage = []
    for file_path, file_data in coverage_data["files"].items():
        # Skip __init__.py files
        if file_path.endswith("__init__.py"):
            continue
            
        # Skip frontend code
        if "/web/" in file_path:
            continue
            
        # Calculate coverage percentage
        if file_data["summary"]["num_statements"] > 0:
            covered = file_data["summary"]["covered_lines"]
            total = file_data["summary"]["num_statements"]
            coverage_pct = (covered / total) * 100
            
            if coverage_pct < threshold:
                low_coverage.append({
                    "path": file_path,
                    "coverage": coverage_pct,
                    "covered_lines": covered,
                    "total_lines": total,
                    "missing_lines": total - covered
                })
    
    # Sort by coverage (ascending)
    low_coverage.sort(key=lambda x: x["coverage"])
    
    return low_coverage


def prioritize_modules(modules):
    """
    Prioritize modules based on their importance for security and PHI handling.
    Returns a sorted list of modules with priority indicators.
    """
    priorities = {
        "app/infrastructure/security/": "HIGH",
        "app/core/utils/": "HIGH",
        "app/domain/entities/": "MEDIUM", 
        "app/domain/services/": "MEDIUM",
        "app/application/services/": "MEDIUM"
    }
    
    prioritized = []
    
    for module in modules:
        path = module["path"]
        
        # Determine priority
        priority = "LOW"
        for key, value in priorities.items():
            if key in path:
                priority = value
                break
                
        module_with_priority = module.copy()
        module_with_priority["priority"] = priority
        prioritized.append(module_with_priority)
    
    # Sort by priority (HIGH, MEDIUM, LOW) and then by coverage
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    prioritized.sort(key=lambda x: (priority_order[x["priority"]], x["coverage"]))
    
    return prioritized


def get_test_file_path(module_path):
    """Convert a module path to a test file path."""
    # Convert from app/path/to/module.py to tests/unit/path/to/test_module.py
    if not module_path.startswith("app/"):
        return None
        
    rel_path = module_path[4:]  # Remove "app/"
    dir_path = os.path.dirname(rel_path)
    filename = os.path.basename(rel_path)
    test_filename = f"test_{filename}"
    
    return os.path.join("tests/unit", dir_path, test_filename)


def is_module_excluded(module_path):
    """Check if a module should be excluded from test generation."""
    excluded_patterns = [
        r"__init__\.py$",
        r"/web/",
        r"migrations/",
        r"alembic/"
    ]
    
    for pattern in excluded_patterns:
        if re.search(pattern, module_path):
            return True
    
    return False


def extract_module_info(module_path):
    """Extract module information for test generation."""
    try:
        # Convert path to module name for importing
        module_name = module_path.replace("/", ".").replace(".py", "")
        
        # Try to import the module
        module = importlib.import_module(module_name)
        
        classes = []
        functions = []
        
        # Extract classes and functions
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and obj.__module__ == module_name:
                methods = []
                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                    if not method_name.startswith("_") or method_name == "__init__":
                        params = inspect.signature(method).parameters
                        methods.append({
                            "name": method_name,
                            "params": list(params.keys()),
                            "is_async": inspect.iscoroutinefunction(method)
                        })
                
                classes.append({
                    "name": obj.__name__,
                    "methods": methods
                })
            elif inspect.isfunction(obj) and obj.__module__ == module_name:
                if not name.startswith("_"):
                    params = inspect.signature(obj).parameters
                    functions.append({
                        "name": name,
                        "params": list(params.keys()),
                        "is_async": inspect.iscoroutinefunction(obj)
                    })
        
        return {
            "module_name": module_name,
            "classes": classes,
            "functions": functions
        }
        
    except (ImportError, AttributeError) as e:
        print(f"Error extracting info from {module_path}: {e}")
        return None


def generate_test_content(module_info):
    """Generate test file content from module information."""
    if not module_info:
        return None
    
    module_name = module_info["module_name"]
    content = []
    
    # Add header
    content.append('#!/usr/bin/env python3')
    content.append('# -*- coding: utf-8 -*-')
    content.append('"""')
    content.append(f'Unit tests for {module_name}.')
    content.append('"""')
    content.append('')
    content.append('import pytest')
    content.append('from unittest.mock import patch, MagicMock')
    content.append('')
    content.append(f'from {module_name} import *')
    content.append('')
    
    # Generate test classes
    for cls in module_info["classes"]:
        class_name = cls["name"]
        content.append(f'class Test{class_name}:')
        content.append(f'    """Test suite for {class_name}."""')
        content.append('')
        
        # Create fixture for class instance
        content.append('    @pytest.fixture')
        content.append(f'    def {class_name.lower()}_instance(self):')
        content.append(f'        """Create a {class_name} instance for testing."""')
        
        # Check if we have an __init__ method to identify parameters
        init_params = []
        for method in cls["methods"]:
            if method["name"] == "__init__":
                init_params = method["params"]
                if "self" in init_params:
                    init_params.remove("self")
                break
        
        # Generate mock parameters for constructor if needed
        if init_params:
            for param in init_params:
                content.append(f'        {param} = MagicMock()')
            
            param_str = ", ".join(init_params)
            content.append(f'        return {class_name}({param_str})')
        else:
            content.append(f'        return {class_name}()')
        
        content.append('')
        
        # Generate test methods
        for method in cls["methods"]:
            if method["name"] != "__init__":
                method_name = method["name"]
                content.append(f'    def test_{method_name}(self, {class_name.lower()}_instance):')
                content.append(f'        """Test {method_name} method."""')
                
                # Generate mocks for method parameters if needed
                params = method["params"]
                if "self" in params:
                    params.remove("self")
                
                if params:
                    for param in params:
                        content.append(f'        {param} = MagicMock()')
                    
                    # Call method with mocks
                    param_str = ", ".join(params)
                    content.append(f'        result = {class_name.lower()}_instance.{method_name}({param_str})')
                    content.append('        # Add assertions here')
                else:
                    content.append(f'        result = {class_name.lower()}_instance.{method_name}()')
                    content.append('        # Add assertions here')
                
                content.append('        assert True  # Replace with actual assertions')
                content.append('')
    
    # Generate test functions
    for func in module_info["functions"]:
        func_name = func["name"]
        content.append(f'def test_{func_name}():')
        content.append(f'    """Test {func_name} function."""')
        
        # Generate mocks for function parameters if needed
        params = func["params"]
        if params:
            for param in params:
                content.append(f'    {param} = MagicMock()')
            
            # Call function with mocks
            param_str = ", ".join(params)
            content.append(f'    result = {func_name}({param_str})')
            content.append('    # Add assertions here')
        else:
            content.append(f'    result = {func_name}()')
            content.append('    # Add assertions here')
        
        content.append('    assert True  # Replace with actual assertions')
        content.append('')
    
    return "\n".join(content)


def generate_test_file(module_path):
    """Generate a test file for a module with low coverage."""
    if is_module_excluded(module_path):
        print(f"Skipping excluded module: {module_path}")
        return None
    
    test_file_path = get_test_file_path(module_path)
    if not test_file_path:
        print(f"Could not determine test file path for {module_path}")
        return None
    
    # Check if test file already exists
    if os.path.exists(test_file_path):
        print(f"Test file already exists: {test_file_path}")
        return test_file_path
    
    # Extract module information
    module_info = extract_module_info(module_path)
    if not module_info:
        print(f"Could not extract module information from {module_path}")
        return None
    
    # Generate test content
    content = generate_test_content(module_info)
    if not content:
        print(f"Could not generate test content for {module_path}")
        return None
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
    
    # Write test file
    with open(test_file_path, "w") as f:
        f.write(content)
    
    print(f"Generated test file: {test_file_path}")
    return test_file_path


def run_linting_and_formatting(file_path):
    """Run black and flake8 on a file."""
    print(f"\nRunning linting and formatting on {file_path}...")
    
    # Run black
    print("Running black...")
    result = subprocess.run(
        ["black", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error running black: {result.stderr}")
    else:
        print("✅ black formatting successful")
    
    # Run flake8
    print("Running flake8...")
    result = subprocess.run(
        ["flake8", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode != 0:
        print(f"⚠️ flake8 warnings: {result.stdout}")
    else:
        print("✅ flake8 check passed")
    
    return True


def main():
    """Main function to run test generation."""
    print("Starting test file generation...")
    
    # Run coverage analysis
    coverage_data = run_coverage_analysis()
    if not coverage_data:
        return 1
    
    # Identify modules with low coverage
    low_coverage_modules = identify_low_coverage_modules(coverage_data)
    if not low_coverage_modules:
        print("No modules found with coverage below 50%.")
        return 0
    
    # Prioritize modules
    prioritized_modules = prioritize_modules(low_coverage_modules)
    
    # Print summary of modules to test
    print("\n===== Modules with Low Coverage =====")
    for module in prioritized_modules:
        print(f"{module['priority']} Priority: {module['path']} ({module['coverage']:.2f}% coverage)")
    
    # Generate test files
    generated_files = []
    for module in prioritized_modules:
        test_file = generate_test_file(module["path"])
        if test_file:
            generated_files.append(test_file)
            
            # Run linting and formatting
            run_linting_and_formatting(test_file)
    
    # Print summary
    print("\n===== Summary =====")
    print(f"Found {len(prioritized_modules)} modules with coverage below 50%")
    print(f"Generated {len(generated_files)} test files")
    
    if generated_files:
        print("\nNext steps:")
        print("1. Review and complete the generated test files")
        print("2. Run pytest to run the tests")
        print("3. Check coverage again with run_coverage_check.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())