#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix the indentation issue in the _audit_passed method.
"""
import re

def fix_indentation():
    """Fix the indentation of the _audit_passed method in run_hipaa_phi_audit.py."""
    filepath = "scripts/run_hipaa_phi_audit.py"
    
    # Read the file contents
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find the _audit_passed method with its current incorrect indentation
    pattern = r'(\s+)def _audit_passed\(self\).*?(?=\n\s*def|\Z)'
    
    # Function to properly reindent each line of the match
    def fix_indent(match):
        lines = match.group(0).split('\n')
        # Determine the current indentation level of the method definition
        current_indent = len(match.group(1))
        # We want a standard 4-space indentation for methods
        target_indent = 4
        # Fix the indentation of each line
        fixed_lines = []
        for line in lines:
            if line.strip():  # Non-empty line
                # Remove the current indentation and add the target indentation
                stripped = line.lstrip()
                # Method definition gets 4 spaces, method body gets 8 spaces
                if stripped.startswith('def '):
                    fixed_lines.append(' ' * target_indent + stripped)
                else:
                    fixed_lines.append(' ' * (target_indent + 4) + stripped)
            else:
                fixed_lines.append('')  # Keep empty lines as-is
        
        return '\n'.join(fixed_lines)
    
    # Apply the indentation fix using regex substitution
    fixed_content = re.sub(pattern, fix_indent, content, flags=re.DOTALL)
    
    # Write the fixed content back to the file
    with open(filepath, 'w') as f:
        f.write(fixed_content)
    
    print(f"Successfully fixed indentation in {filepath}")
    return True

if __name__ == "__main__":
    fix_indentation()