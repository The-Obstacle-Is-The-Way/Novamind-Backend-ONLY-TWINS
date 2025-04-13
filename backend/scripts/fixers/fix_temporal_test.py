#!/usr/bin/env python3
"""
Fix syntax error in temporal neurotransmitter analysis test
"""

with open('app/tests/venv_only/test_temporal_neurotransmitter_analysis.py', 'r') as file:
    lines = file.readlines()

fixed_lines = []
for i, line in enumerate(lines):
    # Fix the line with invalid syntax (line 14 with the extra comma)
    if i == 13 and line.strip().startswith(','):
        # Remove the leading comma
        fixed_lines.append(line.lstrip(','))
    else:
        fixed_lines.append(line)

with open('app/tests/venv_only/test_temporal_neurotransmitter_analysis.py', 'w') as file:
    file.writelines(fixed_lines)

print("Fixed syntax error in test_temporal_neurotransmitter_analysis.py")
