import re

def fix_indentation_issues(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Fix method indentation issues - after a method definition followed by a docstring
    # Find all method definitions followed by docstrings
    pattern = r'(def\s+\w+\([^)]*\)[^:]*:[\s\n]+"""[^"]*"""[\s\n]+)(\s*)return'
    fixed_content = re.sub(pattern, lambda m: m.group(1) + m.group(2) + '    return', content)
    
    # If there are still return statements at wrong indentation levels
    lines = fixed_content.split('\n')
    fixed_lines = []
    in_method = False
    method_indent = ""
    
    for line in lines:
        stripped = line.lstrip()
        
        # Detect method start
        if re.match(r'def\s+\w+\([^)]*\)[^:]*:', line):
            in_method = True
            method_indent = line[:line.index('def')]
        
        # Fix return statement indentation
        if in_method and stripped.startswith('return ') and not line.startswith(method_indent + '    '):
            indent_level = method_indent + '    '
            fixed_lines.append(indent_level + stripped)
        else:
            fixed_lines.append(line)
    
    fixed_content = '\n'.join(fixed_lines)
    
    with open(file_path, 'w') as file:
        file.write(fixed_content)
    
    print(f"Fixed indentation issues in {file_path}")

# Fix the test file
file_path = 'app/tests/venv/domain/test_temporal_neurotransmitter_analysis.py'
fix_indentation_issues(file_path)
