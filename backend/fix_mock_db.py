with open('app/tests/fixtures/mock_db_fixture.py', 'r') as file:
    lines = file.readlines()

# Fix indentation issues with return statements
for i in range(len(lines)):
    if lines[i].strip().startswith('return ') and i > 0 and not lines[i-1].strip().endswith('{') and not lines[i-1].strip().endswith(':'):
        # This is likely a return outside a function
        lines[i] = '        ' + lines[i].lstrip()

with open('app/tests/fixtures/mock_db_fixture.py', 'w') as file:
    file.writelines(lines)

print("Fixed indentation issues in mock_db_fixture.py")
