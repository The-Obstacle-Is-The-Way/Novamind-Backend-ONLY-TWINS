#!/usr/bin/env python3
"""
Fix indentation issues in the mock PAT service test file
"""

with open('app/tests/unit/services/ml/pat/test_mock_pat_service.py', 'r') as file:
    lines = file.readlines()

fixed_lines = []
for i, line in enumerate(lines):
    # Fix docstring indentation in initialized_mock_pat fixture
    if i == 29:
        fixed_lines.append('    """Create and initialize a MockPAT instance."""\n')
    # Fix return statement indentation in initialized_mock_pat fixture
    elif i == 32:
        fixed_lines.append(line)
        fixed_lines.append('    return pat\n')
    # Skip the original return line if it was standalone
    elif i == 33 and line.strip() == "return pat":
        continue
    else:
        fixed_lines.append(line)

with open('app/tests/unit/services/ml/pat/test_mock_pat_service.py', 'w') as file:
    file.writelines(fixed_lines)

print("Fixed indentation issues in test_mock_pat_service.py")
