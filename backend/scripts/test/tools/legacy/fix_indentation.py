"""
Script to fix indentation in test_provider.py
"""

def fix_indentation():
    file_path = "app/tests/standalone/test_provider.py"
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "@pytest.mark.standalone" in line and i + 1 < len(lines):
            # Get the decorator line
            fixed_lines.append(line)
            
            # Get the function definition line
            def_line = lines[i + 1]
            
            # If the function definition is not indented properly, indent it
            if not def_line.startswith("    def "):
                def_line = "    " + def_line
            
            fixed_lines.append(def_line)
            
            # Skip the already processed line
            i += 2
            
            # Fix the indentation of the function body until the next decorator or end of file
            while i < len(lines) and "@pytest.mark.standalone" not in lines[i]:
                # If this line is part of the function body and not a blank line
                if lines[i].strip() and not lines[i].startswith("    "):
                    fixed_lines.append("    " + lines[i])
                else:
                    fixed_lines.append(lines[i])
                i += 1
        else:
            fixed_lines.append(line)
            i += 1
    
    with open(file_path, 'w') as file:
        file.writelines(fixed_lines)
    
    print(f"Indentation fixed for {file_path}")

if __name__ == "__main__":
    fix_indentation()