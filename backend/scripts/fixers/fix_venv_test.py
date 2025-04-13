#!/usr/bin/env python3
"""
Fix 'return outside function' syntax errors in the temporal neurotransmitter test
"""
import re

file_path = 'app/tests/venv/test_temporal_neurotransmitter_analysis.py'

with open(file_path, 'r') as file:
    content = file.read()

# Fix the "return outside function" error - indentation issue in to_dict method
pattern = r'def to_dict\(\) -> Dict\[str, Any\]:\s+"""Convert to dictionary."""\s+\n(\s*)return'
fixed_content = re.sub(pattern, 'def to_dict(self) -> Dict[str, Any]:\n        """Convert to dictionary."""\n        return', content)

# Check for any other return statements with incorrect indentation
lines = fixed_content.split('\n')
fixed_lines = []
in_method = False
method_indent = ""
current_class = None

for i, line in enumerate(lines):
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())
    spaces = ' ' * indent

    # Method detection
    if re.match(r'\s*def\s+\w+\(', line) and ')' in line and ':' in line:
        in_method = True
        method_indent = spaces
    # Class detection
    elif re.match(r'\s*class\s+\w+', line) and ':' in line:
        current_class = re.search(r'class\s+(\w+)', line).group(1)
        in_method = False

    # Fix return statements that might be at the wrong indentation level
    if in_method and stripped.startswith('return ') and spaces != method_indent + '    ':
        # This is a return statement with wrong indentation
        fixed_lines.append(method_indent + '    ' + stripped)
    else:
        fixed_lines.append(line)

fixed_content = '\n'.join(fixed_lines)

with open(file_path, 'w') as file:
    file.write(fixed_content)

print(f"Fixed 'return outside function' errors in {file_path}")
