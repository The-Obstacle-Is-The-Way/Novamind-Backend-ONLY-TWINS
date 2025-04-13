#!/usr/bin/env python3
"""
NovaMind Test Suite Indentation Fixer

This script automatically fixes common indentation issues in the test suite files:
1. Properly indents fixture definitions
2. Fixes nested test method definitions
3. Corrects misaligned docstrings
4. Handles import syntax errors

Usage:
    python novamind_test_fixer.py [path_to_file]
"""

import os
import re
import sys
from pathlib import Path

def fix_indentation_issues(file_path):
    """Fix indentation issues in the specified Python file."""
    print(f"Processing file: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix nested fixture declarations
    content = re.sub(r'(\s+)@pytest\.fixture\n\s+def', r'@pytest.fixture\ndef', content)
    
    # Fix docstring indentation
    content = re.sub(r'def ([^\n]+):\n([^\n]+"""[^\n]+""")', r'def \1:\n    \2', content)
    
    # Fix nested class declarations
    content = re.sub(r'(\s+)class ([^\n]+):', r'class \2:', content)
    
    # Fix broken parameter lists in function/constructor calls
    content = re.sub(r'\)\n(\s+)([a-zA-Z_][a-zA-Z0-9_]*) =', r',\n\1\2=', content)
    
    # Fix import statements with trailing parentheses
    content = re.sub(r'from ([^\s]+) import\s*\n([^\)]+)\(\)', r'from \1 import (\n\2)', content)
    
    # Fix improperly indented method definitions within classes
    content = re.sub(r'(\s+)def ([^\n]+):\n([^\n]+)', r'\1def \2:\n\1    \3', content)
    
    # Write the fixed content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed indentation issues in {file_path}")
    return True

def main():
    """Main function to process command line arguments."""
    if len(sys.argv) > 1:
        # Single file mode
        file_path = sys.argv[1]
        if os.path.isfile(file_path) and file_path.endswith('.py'):
            fix_indentation_issues(file_path)
        else:
            print(f"Error: {file_path} is not a Python file or doesn't exist.")
    else:
        # Batch mode - process all test files
        test_dir = Path('/Users/ray/Desktop/GITHUB/Novamind-Backend-ONLY-TWINS/backend/app/tests')
        for test_file in test_dir.glob('**/test_*.py'):
            fix_indentation_issues(str(test_file))

if __name__ == "__main__":
    main()
