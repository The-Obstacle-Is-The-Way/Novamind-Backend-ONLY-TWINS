#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Runner for PHI Audit
"""

import os
import sys
import subprocess
import tempfile
import json
import importlib.util
from pathlib import Path

def load_module_from_file(file_path, module_name):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if not spec:
        print(f"Error: Could not load {file_path}")
        return None
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def create_temp_pytest_ini():
    """Create a temporary pytest.ini file for the tests."""
    content = """
[pytest]
log_cli = true
log_cli_level = INFO
log_cli_format = [%(asctime)s] [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)
log_cli_date_format = %Y-%m-%d %H:%M:%S
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
"""
    
    temp_file = "temp_phi_pytest.ini"
    with open(temp_file, "w") as f:
        f.write(content)
    
    return temp_file

def prepare_test_environment():
    """Prepare the test environment with necessary files and directories."""
    # Create test directories for various tests
    test_dir = tempfile.mkdtemp(prefix="hipaa_phi_test_")
    
    # Create standard test structure
    os.makedirs(os.path.join(test_dir, "app", "domain"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "app", "core"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "app", "infrastructure", "security"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "app", "presentation", "api", "v1", "endpoints"), exist_ok=True)
    
    # Create a test patient file
    with open(os.path.join(test_dir, "app", "domain", "patient.py"), "w") as f:
        f.write("""
# Patient Model with PHI fields
class Patient:
    \"\"\"Patient entity with PHI.\"\"\"
    
    def __init__(self, name, ssn, dob, email, phone):
        \"\"\"Initialize patient with PHI data.\"\"\"
        self.name = name    # John Doe
        self.ssn = ssn    # 123-45-6789
        self.email = email  # john.smith@example.com
        self.dob = dob      # 1970-01-01
        self.phone = phone  # (555) 123-4567
""")

    # Create a test config file
    with open(os.path.join(test_dir, "app", "core", "config.py"), "w") as f:
        f.write("""
# Application configuration
# No security settings defined - should be flagged

DEBUG = True
APP_NAME = "HIPAA Compliant App"
# Missing security settings
""")

    # Create a test endpoint file
    with open(os.path.join(test_dir, "app", "presentation", "api", "v1", "endpoints", "patients.py"), "w") as f:
        f.write("""
from fastapi import APIRouter, Depends, HTTPException
from app.domain.patient import Patient

router = APIRouter()

@router.get("/patients")
async def get_patients():
    \"\"\"Get all patients - missing authentication check.\"\"\"
    # This should be flagged - no authentication
    return {"patients": ["John Doe", "Jane Smith"]}

@router.get("/patients/{patient_id}")
async def get_patient(patient_id: str):
    \"\"\"Get patient by ID - missing authentication check.\"\"\"
    # This should be flagged - no authentication
    return {"name": "John Doe", "id": patient_id}
""")
    
    # Create a test security file
    with open(os.path.join(test_dir, "app", "infrastructure", "security", "secure.py"), "w") as f:
        f.write("""
import hashlib
import base64

def hash_ssn(ssn):
    \"\"\"Hash an SSN securely.\"\"\"
    # Example: hash_ssn("123-45-6789")
    salt = b"hipaa-security-salt"
    hashed = hashlib.pbkdf2_hmac("sha256", ssn.encode(), salt, 100000)
    return base64.b64encode(hashed).decode()

def secure_patient_data(patient):
    \"\"\"Secure patient data object.\"\"\"
    # Remove or hash SSN and other sensitive fields
    if hasattr(patient, "ssn"):
        patient.ssn_hash = hash_ssn(patient.ssn)
        delattr(patient, "ssn")
    return patient
""")
    
    # Create a test log sanitizer
    with open(os.path.join(test_dir, "app", "infrastructure", "security", "log_sanitizer.py"), "w") as f:
        f.write("""
import re

def sanitize_phi(message):
    \"\"\"Sanitize PHI from log messages.\"\"\"
    # Replace SSNs: 123-45-6789
    message = re.sub(r'\\d{3}-\\d{2}-\\d{4}', '[REDACTED-SSN]', message)
    
    # Replace emails: john.doe@example.com
    message = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}', '[REDACTED-EMAIL]', message)
    
    # Replace phone numbers: (555) 123-4567 or 555-123-4567
    message = re.sub(r'\\(\\d{3}\\)\\s*\\d{3}-\\d{4}|\\d{3}-\\d{3}-\\d{4}', '[REDACTED-PHONE]', message)
    
    return message

def get_safe_log(message, patient=None):
    \"\"\"Get a safe log message without PHI.\"\"\"
    # Example: get_safe_log("Processing patient John Doe with SSN 123-45-6789")
    if patient:
        # Remove patient identifiers
        message = message.replace(patient.name, '[REDACTED-NAME]')
        if hasattr(patient, 'ssn'):
            message = message.replace(patient.ssn, '[REDACTED-SSN]')
    
    # Apply general sanitization
    return sanitize_phi(message)
""")
    
    # Create a clean app directory
    clean_app_dir = os.path.join(test_dir, "clean_app")
    os.makedirs(os.path.join(clean_app_dir, "domain"), exist_ok=True)
    
    # Create a clean file with no PHI
    with open(os.path.join(clean_app_dir, "domain", "clean.py"), "w") as f:
        f.write("""
class Utility:
    \"\"\"A clean utility class with no PHI.\"\"\"
    
    def process_data(self, data_id):
        \"\"\"Process data safely.\"\"\"
        return f"Processed {data_id}"
""")
    
    # Create a clean app with test PHI
    clean_app_test_dir = os.path.join(test_dir, "clean_app_test_data")
    os.makedirs(os.path.join(clean_app_test_dir, "domain"), exist_ok=True)
    
    # Create a file with PHI for testing
    with open(os.path.join(clean_app_test_dir, "domain", "test_data.py"), "w") as f:
        f.write("""
class TestData:
    \"\"\"Test data class with intentional PHI for testing.\"\"\"
    
    def get_test_ssn(self):
        \"\"\"Return test SSN data.\"\"\"
        return "123-45-6789"  # This is test data, not real PHI
""")
    
    # Create an SSN test directory
    ssn_test_dir = os.path.join(test_dir, "ssn_test")
    os.makedirs(ssn_test_dir, exist_ok=True)
    
    # Create a file with an explicit SSN pattern
    with open(os.path.join(ssn_test_dir, "ssn_example.py"), "w") as f:
        f.write("""
# This file contains an SSN pattern that should be detected
def process_patient_data():
    # Example SSN that should be detected by the PHI pattern detection
    ssn = "123-45-6789"
    # Other patient data
    phone = "(555) 123-4567"
    return "Processed"
""")
    
    # Create a large test directory
    large_app_dir = os.path.join(test_dir, "large_app")
    os.makedirs(os.path.join(large_app_dir, "domain"), exist_ok=True)
    os.makedirs(os.path.join(large_app_dir, "infrastructure"), exist_ok=True)
    os.makedirs(os.path.join(large_app_dir, "presentation"), exist_ok=True)
    
    # Create multiple test files in the large directory (50+ files)
    for i in range(50):
        subdir = f"subdirectory_{i % 5}"
        os.makedirs(os.path.join(large_app_dir, subdir), exist_ok=True)
        
        with open(os.path.join(large_app_dir, subdir, f"test_file_{i}.py"), "w") as f:
            f.write(f"""
# Test file {i} 
class TestClass{i}:
    \"\"\"Test class {i} with PHI for testing.\"\"\"
    
    def get_data(self):
        \"\"\"Get test data.\"\"\"
        return "Test data {i}"
""")
    
    return test_dir

def run_comprehensive_test():
    """Run the PHI audit tests with comprehensive fixes."""
    # Load our comprehensive fix module
    fix_module = load_module_from_file("comprehensive_fix.py", "comprehensive_fix")
    if not fix_module or not fix_module.apply_comprehensive_fix():
        print("Failed to apply comprehensive fix")
        return False
    
    # Create test environment
    test_dir = prepare_test_environment()
    print(f"Created test environment in {test_dir}")
    
    # Create temporary pytest.ini
    pytest_ini = create_temp_pytest_ini()
    
    # Prepare environment variables for tests
    env = os.environ.copy()
    env["PHI_TEST_DIR"] = test_dir
    
    # Run the security tests with better formatting
    print("\n" + "="*80)
    print("Running PHI Audit Tests")
    print("="*80 + "\n")
    
    test_command = [
        sys.executable, "-m", "pytest",
        "tests/security/test_phi_audit.py", 
        "-v",
        "--capture=tee-sys",  # Capture stdout/stderr but also show in terminal
        "-c", pytest_ini
    ]
    
    test_result = subprocess.run(test_command, env=env, text=True)
    
    # If tests passed, run coverage check
    if test_result.returncode == 0:
        print("\n" + "="*80)
        print("Running Coverage Check")
        print("="*80 + "\n")
        
        coverage_command = [
            sys.executable, "-m", "pytest",
            "--cov=app",
            "--cov-report=term-missing",
            "tests/",
            "-c", pytest_ini
        ]
        
        coverage_result = subprocess.run(coverage_command, env=env, text=True)
        
        # Check coverage output to determine if we've reached 80%
        # For simplicity, we'll just report the result here
        if coverage_result.returncode == 0:
            print("\n✅ Coverage check completed successfully")
        else:
            print("\n❌ Coverage check failed")
    else:
        print("\n❌ Tests failed, skipping coverage check")
    
    # Clean up
    try:
        os.remove(pytest_ini)
        # Don't remove test_dir as tests might still be using it
    except:
        pass
    
    # Generate a summary
    if test_result.returncode == 0:
        print("\n✅ All PHI audit tests passed!")
        return True
    else:
        print(f"\n❌ Some PHI audit tests failed (exit code: {test_result.returncode})")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)