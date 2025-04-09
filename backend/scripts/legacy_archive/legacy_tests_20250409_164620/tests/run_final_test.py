#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Test Runner for PHI Audit - Applying all fixes and running tests
"""

import os
import sys
import subprocess
import importlib.util
import time

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
    """Create a temporary pytest.ini file for running tests."""
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
    
    temp_file = "temp_final_pytest.ini"
    with open(temp_file, "w") as f:
        f.write(content)
    
    return temp_file

def run_final_test():
    """Run PHI audit tests with final fixes applied."""
    print("\n" + "="*80)
    print("🔒 HIPAA PHI Audit Final Test Runner")
    print("="*80 + "\n")
    
    # Load and apply final fix module
    print("📋 Step 1: Applying final comprehensive fixes to PHI audit code...")
    try:
        fix_module = load_module_from_file("final_comprehensive_fix.py", "final_comprehensive_fix")
        if not fix_module or not fix_module.apply_final_fix():
            print("❌ Failed to apply final fixes")
            return False
        
        print("✅ Successfully applied all final fixes to PHI audit code")
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        return False
    
    # Create temporary pytest.ini
    pytest_ini = create_temp_pytest_ini()
    print(f"📝 Created temporary pytest configuration: {pytest_ini}")
    
    # Run the security tests with verbose output
    print("\n" + "="*80)
    print("🧪 Step 2: Running PHI Audit Tests with Final Fixes")
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
        if test_result.stderr:
            print("STDERR:", test_result.stderr)
        
        # Display test results summary
        print("\n" + "="*80)
        if test_result.returncode == 0:
            print(f"✅ All PHI audit tests PASSED in {test_duration:.2f} seconds!")
            
            # Run coverage check
            print("\n" + "="*80)
            print("📊 Step 3: Running Coverage Check")
            print("="*80 + "\n")
            
            coverage_command = [
                sys.executable, "-m", "pytest",
                "--cov=app",
                "--cov-report=term-missing",
                "tests/",
                "-c", pytest_ini
            ]
            
            try:
                coverage_result = subprocess.run(coverage_command, text=True, capture_output=True)
                
                # Print coverage output
                print(coverage_result.stdout)
                
                # Check if coverage is at or above 80%
                coverage_achieved = False
                for line in coverage_result.stdout.split('\n'):
                    if "TOTAL" in line and "%" in line:
                        try:
                            # Extract coverage percentage
                            parts = line.split()
                            for part in parts:
                                if "%" in part:
                                    coverage_percentage = float(part.strip('%'))
                                    coverage_achieved = coverage_percentage >= 80
                                    break
                        except:
                            pass
                
                if coverage_achieved:
                    print("\n" + "="*80)
                    print("🎉 SUCCESS: All PHI audit tests pass and coverage target achieved!")
                    print("="*80)
                else:
                    print("\n" + "="*80)
                    print("⚠️ WARNING: Coverage check did not reach the 80% target")
                    print("="*80)
            except Exception as e:
                print(f"❌ Error running coverage check: {e}")
        else:
            print(f"❌ Some PHI audit tests FAILED after {test_duration:.2f} seconds")
            print("="*80 + "\n")
            
            # Analyze failures
            print("Analyzing test failures...")
            failures = []
            current_failure = None
            failure_details = []
            
            for line in test_result.stdout.split('\n'):
                if "FAILED" in line and "test_" in line:
                    if current_failure:
                        failures.append((current_failure, '\n'.join(failure_details)))
                        failure_details = []
                    
                    test_name = line.split("FAILED")[0].strip()
                    current_failure = test_name
                elif current_failure and "E " in line:
                    failure_details.append(line)
            
            # Add the last failure if exists
            if current_failure and failure_details:
                failures.append((current_failure, '\n'.join(failure_details)))
            
            # Print failure details
            for i, (test, details) in enumerate(failures, 1):
                print(f"\nFailure {i}: {test}")
                print("-" * 40)
                print(details)
                print()
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False
    finally:
        # Clean up
        try:
            os.remove(pytest_ini)
            print(f"🧹 Cleaned up temporary pytest configuration: {pytest_ini}")
        except:
            pass
    
    # Return success if tests passed
    return test_result.returncode == 0

if __name__ == "__main__":
    try:
        success = run_final_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ ERROR: Test runner failed: {e}")
        sys.exit(1)