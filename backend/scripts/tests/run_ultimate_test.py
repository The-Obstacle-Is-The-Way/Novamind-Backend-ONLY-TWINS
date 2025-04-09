#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultimate Test Runner for PHI Audit - Final Version
This script applies the ultimate fixes and runs the tests to verify everything passes
"""

import os
import sys
import subprocess
import importlib.util
import time
import json
from pathlib import Path

def run_ultimate_test():
    """Run PHI audit tests with the ultimate fixes applied."""
    print("\n" + "="*80)
    print("🔒 HIPAA PHI Audit Ultimate Test Runner")
    print("="*80 + "\n")
    
    # Load and apply the ultimate fix module
    print("📋 Step 1: Applying ultimate comprehensive fixes to PHI audit code...")
    
    try:
        # Import the module dynamically
        fix_module_path = os.path.join(os.getcwd(), "ultimate_phi_fix.py")
        spec = importlib.util.spec_from_file_location("ultimate_phi_fix", fix_module_path)
        fix_module = importlib.util.module_from_spec(spec)
        sys.modules["ultimate_phi_fix"] = fix_module
        spec.loader.exec_module(fix_module)
        
        # Apply the fixes
        if not fix_module.apply_ultimate_fix():
            print("❌ Failed to apply ultimate fixes")
            return False
        
        print("✅ Successfully applied all ultimate fixes to PHI audit code")
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Create a temporary pytest.ini file
    pytest_ini = "temp_ultimate_pytest.ini"
    with open(pytest_ini, "w") as f:
        f.write("""
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
""")
    
    print(f"📝 Created temporary pytest configuration: {pytest_ini}")
    
    # Run the security tests with verbose output
    print("\n" + "="*80)
    print("🧪 Step 2: Running PHI Audit Tests with Ultimate Fixes")
    print("="*80 + "\n")
    
    test_command = [
        sys.executable, "-m", "pytest",
        "tests/security/test_phi_audit.py", 
        "-v",
        "--capture=tee-sys",  # Capture stdout/stderr but also show in terminal
        "-c", pytest_ini
    ]
    
    try:
        start_time = time.time()
        test_result = subprocess.run(test_command, text=True, capture_output=True)
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Print test output
        print(test_result.stdout)
        if test_result.stderr and "PYTHONWARNING" not in test_result.stderr:
            print("STDERR:", test_result.stderr)
        
        # Count passes and failures
        passed_count = test_result.stdout.count("PASSED")
        failed_count = test_result.stdout.count("FAILED")
        
        # Check if all tests passed
        if test_result.returncode == 0:
            # Run coverage check
            print("\n" + "="*80)
            print("📊 Step 3: Running Coverage Check")
            print("="*80 + "\n")
            
            # Create coverage report directory if it doesn't exist
            coverage_dir = Path("coverage-reports")
            coverage_dir.mkdir(exist_ok=True)
            
            # Run pytest with coverage
            coverage_command = [
                sys.executable, "-m", "pytest",
                "--cov=app",
                "--cov-report=term-missing",
                "--cov-report=html:coverage-reports/html",
                "--cov-report=json:coverage-reports/coverage.json",
                "tests/",
                "-c", pytest_ini,
                "-q"  # Quiet mode for cleaner output
            ]
            
            try:
                coverage_result = subprocess.run(coverage_command, text=True, capture_output=True)
                
                # Print coverage output
                print(coverage_result.stdout)
                
                # Extract coverage percentage
                coverage_pct = None
                for line in coverage_result.stdout.split('\n'):
                    if "TOTAL" in line and "%" in line:
                        parts = line.split()
                        for part in parts:
                            if "%" in part:
                                coverage_pct = float(part.strip('%'))
                                print(f"📊 Test coverage: {coverage_pct:.2f}%")
                                break
                
                # Save coverage results to a summary file
                summary_file = "HIPAA_TEST_COVERAGE_README.md"
                with open(summary_file, "w") as f:
                    f.write(f"""# HIPAA Compliance Test Coverage

## Summary
- **Test Coverage: {coverage_pct:.2f}%**
- **Status: {'✅ PASSED' if coverage_pct >= 80 else '⚠️ NEEDS IMPROVEMENT'}**
- **Date: {time.strftime('%Y-%m-%d %H:%M:%S')}**

## Security PHI Audit Tests
- **PHI Audit Tests: {passed_count} passed, {failed_count} failed**
- **Test Duration: {test_duration:.2f} seconds**

## Compliance Requirements
- HIPAA-compliant code requires thorough testing, especially for security-critical components
- All PHI (Protected Health Information) handling code must be tested extensively
- Minimum coverage target: 80%

## Coverage Details
```
{coverage_result.stdout}
```

## Next Steps
{'All tests are passing with sufficient coverage! The codebase is now compliant with HIPAA testing requirements.' 
if coverage_pct >= 80 else 'Additional tests needed to reach the 80% coverage requirement. Focus on untested modules.'}
""")
                
                # Display final results
                print("\n" + "="*80)
                if coverage_pct >= 80:
                    print(f"🎉 SUCCESS! Coverage is at {coverage_pct:.2f}%, exceeding the 80% target!")
                    print("All PHI audit tests are passing and HIPAA compliance requirements are met.")
                    print(f"✅ Summary saved to {summary_file}")
                else:
                    print(f"⚠️ PARTIAL SUCCESS: Tests pass but coverage is at {coverage_pct:.2f}%, below the 80% target.")
                    print("Additional testing is required to meet HIPAA compliance requirements.")
                    print(f"📝 Next steps documented in {summary_file}")
                print("="*80)
                
                # Clean up temporary files only if successful
                if os.path.exists(pytest_ini):
                    os.remove(pytest_ini)
                    print(f"🧹 Cleaned up temporary pytest configuration: {pytest_ini}")
                
            except Exception as e:
                print(f"❌ Error during coverage check: {e}")
                return False
        else:
            print("\n" + "="*80)
            print(f"❌ {failed_count} PHI audit tests FAILED after {test_duration:.2f} seconds")
            print(f"✅ {passed_count} tests passed")
            print("="*80)
            
            # Keep temporary files for debugging if tests failed
            print(f"ℹ️ Temporary pytest configuration retained for debugging: {pytest_ini}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error during test execution: {e}")
        return False
    
    return True

if __name__ == "__main__":
    run_ultimate_test()