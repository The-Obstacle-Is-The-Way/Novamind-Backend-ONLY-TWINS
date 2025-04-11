#!/usr/bin/env python3
"""
PAT Mock Service Fix Script

This script creates a modified version of the PAT mock service that addresses 
test failures and ensures proper validation and error handling.
"""

import os
import sys
import re
from pathlib import Path

def get_source_file():
    """Get the path to the PAT mock service source file."""
    base_dir = Path(__file__).resolve().parent.parent
    mock_path = base_dir / "app" / "core" / "services" / "ml" / "pat" / "mock.py"
    if not mock_path.exists():
        print(f"ERROR: Could not find mock service at {mock_path}")
        sys.exit(1)
    return mock_path

def read_source_file(file_path):
    """Read the contents of the source file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"ERROR: Failed to read source file: {e}")
        sys.exit(1)

def fix_initialize_method(content):
    """Fix the initialize method to ensure it's handled correctly in tests."""
    # Look for the initialize method
    initialize_pattern = r'def initialize\(self,.*?\).*?:.*?""".*?"""(.*?)(?=def|\Z)'
    initialize_match = re.search(initialize_pattern, content, re.DOTALL)
    
    if not initialize_match:
        print("WARNING: Could not find initialize method")
        return content
    
    # Add code to set the initialized flag
    initialize_code = initialize_match.group(1)
    
    if "_initialized = True" not in initialize_code:
        # Add the initialization flag
        fixed_initialize = initialize_code.replace(
            "self.logger.info(\"Mock PAT service initialized\")", 
            "self.logger.info(\"Mock PAT service initialized\")\n        self._initialized = True"
        )
        
        content = content.replace(initialize_code, fixed_initialize)
    
    return content

def fix_validation_methods(content):
    """Add proper validation methods to ensure tests pass."""
    
    # Add imports if needed
    if "from app.core.services.ml.pat.exceptions import ValidationError" not in content:
        imports_section = content.split('\n\n')[0]
        new_imports = imports_section + "\nfrom app.core.services.ml.pat.exceptions import ValidationError\n\n"
        content = content.replace(imports_section, new_imports)
    
    # Add a method to validate device info
    validation_method = """
    def _validate_device_info(self, device_info: Dict[str, Any]) -> None:
        \"\"\"Validate actigraphy device info.\"\"\"
        if not device_info or not isinstance(device_info, dict):
            raise ValidationError("Device info must be a non-empty dictionary")
            
        required_fields = ["device_type", "manufacturer"]
        for field in required_fields:
            if field not in device_info:
                raise ValidationError(f"Device info missing required field: {field}")
    
    def _validate_analysis_types(self, analysis_types: List[str]) -> None:
        \"\"\"Validate analysis types.\"\"\"
        if not analysis_types or not isinstance(analysis_types, list):
            raise ValidationError("Analysis types must be a non-empty list")
            
        valid_types = ["sleep", "activity", "stress", "movement"]
        for analysis_type in analysis_types:
            if analysis_type not in valid_types:
                raise ValidationError(f"Invalid analysis type: {analysis_type}")
    """
    
    # Insert the validation methods before the analyze_actigraphy method
    analyze_pattern = r'def analyze_actigraphy\('
    if re.search(analyze_pattern, content) and "_validate_device_info" not in content:
        content = re.sub(analyze_pattern, validation_method + "\n    " + analyze_pattern, content)
    
    return content

def update_analyze_actigraphy_method(content):
    """Update the analyze_actigraphy method to use proper validation."""
    # Find the analyze_actigraphy method
    analyze_pattern = r'def analyze_actigraphy\(.*?\).*?:.*?""".*?"""(.*?)(?=def|\Z)'
    analyze_match = re.search(analyze_pattern, content, re.DOTALL)
    
    if not analyze_match:
        print("WARNING: Could not find analyze_actigraphy method")
        return content
    
    analyze_code = analyze_match.group(1)
    
    # Add validation calls
    if "_validate_device_info" not in analyze_code:
        validation_calls = """
        # Validate inputs
        if not patient_id:
            raise ValueError("Patient ID is required")
            
        if not readings or not isinstance(readings, list):
            raise ValueError("Readings must be a non-empty list")
            
        for reading in readings:
            if not all(key in reading for key in ['x', 'y', 'z']):
                raise ValueError("Each reading must contain x, y, z values")
                
        if sampling_rate_hz <= 0:
            raise ValueError("Sampling rate must be positive")
            
        # Validate device info and analysis types
        self._validate_device_info(device_info)
        self._validate_analysis_types(analysis_types)
        """
        
        # Find where to insert the validation code (after self._check_initialized())
        check_initialized_pos = analyze_code.find("self._check_initialized()")
        if check_initialized_pos != -1:
            end_of_line = analyze_code.find("\n", check_initialized_pos) + 1
            fixed_analyze = analyze_code[:end_of_line] + validation_calls + analyze_code[end_of_line:]
            content = content.replace(analyze_code, fixed_analyze)
    
    return content

def add_analysis_id_field(content):
    """Ensure the analysis_id field is consistently set in all analysis responses."""
    # Find the place where analysis data is generated
    analysis_pattern = r'analysis = {.*?}'
    if "analysis_id" not in content or not re.search(analysis_pattern, content, re.DOTALL):
        print("WARNING: Could not find analysis data generation pattern")
        return content
    
    # Make sure all analysis objects have an analysis_id
    modified_content = re.sub(
        r'analysis = {',
        r'analysis = {\n            "analysis_id": str(uuid.uuid4()),',
        content
    )
    
    return modified_content

def fix_pat_mock_service():
    """Main function to fix the PAT mock service."""
    source_path = get_source_file()
    content = read_source_file(source_path)
    
    # Make a backup of the original file
    backup_path = source_path.with_suffix('.py.bak')
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"Created backup at {backup_path}")
    
    # Apply fixes
    content = fix_initialize_method(content)
    content = fix_validation_methods(content)
    content = update_analyze_actigraphy_method(content)
    content = add_analysis_id_field(content)
    
    # Write the fixed content back to the file
    with open(source_path, 'w') as f:
        f.write(content)
    
    print(f"Successfully updated {source_path}")
    print("Run the tests again to verify the fixes.")

if __name__ == "__main__":
    fix_pat_mock_service()