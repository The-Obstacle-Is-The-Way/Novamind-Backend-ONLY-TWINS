"""
NovaMind Digital Twin Test Runner

This script executes the security test suite for the NovaMind Digital Twin backend,
collecting and reporting on test results in a structured manner.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add the root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))


class TestRunner:
    """Quantum-grade test collector and runner for NovaMind security tests."""
    
    def __init__(self, output_path: str = None):
        """Initialize test runner with output path.
        
        Args:
            output_path: Path to save test reports
        """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_path = output_path or os.path.join(self.base_dir, 'test_results')
        
        # Ensure output directory exists
        os.makedirs(self.output_path, exist_ok=True)
        
        # Test categories in priority order
        self.test_categories = [
            {'name': 'Core Encryption', 'pattern': 'test_ml_encryption.py'},
            {'name': 'PHI Handling', 'pattern': 'test_address_helper.py'},
            {'name': 'JWT Authentication', 'pattern': 'test_jwt*.py'},
            {'name': 'HIPAA Compliance', 'pattern': 'test_hipaa*.py'},
            {'name': 'PHI Protection', 'pattern': 'test_phi*.py'},
            {'name': 'Security Patterns', 'pattern': 'test_*security*.py'},
            {'name': 'Audit Logging', 'pattern': 'test_audit*.py'},
            {'name': 'API Security', 'pattern': 'test_api*.py'},
        ]
        
        # Test results collection
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': 0
            },
            'categories': {}
        }
    
    def find_test_files(self, pattern: str) -> List[str]:
        """Find test files matching pattern.
        
        Args:
            pattern: File pattern to search for
            
        Returns:
            List of matching test files
        """
        matches = []
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith('.py') and (pattern == '*' or pattern in file):
                    matches.append(os.path.join(root, file))
        return sorted(matches)
    
    def run_test(self, test_file: str) -> Tuple[bool, Dict[str, Any]]:
        """Run a single test file.
        
        Args:
            test_file: Path to test file
            
        Returns:
            Success status and test results
        """
        print(f"Running test: {os.path.basename(test_file)}")
        
        # Run the test using pytest
        result = subprocess.run(
            ['python', '-m', 'pytest', test_file, '-v', '--no-header'],
            cwd=os.path.abspath(os.path.join(self.base_dir, '../../..')),
            capture_output=True,
            text=True
        )
        
        success = result.returncode == 0
        
        # Parse output to get test counts
        output = result.stdout
        error_output = result.stderr
        
        # Simple parsing of pytest output
        test_results = {
            'file': os.path.basename(test_file),
            'success': success,
            'output': output,
            'error': error_output,
            'tests': {
                'total': output.count('PASSED') + output.count('FAILED') + output.count('SKIPPED') + output.count('ERROR'),
                'passed': output.count('PASSED'),
                'failed': output.count('FAILED'),
                'skipped': output.count('SKIPPED'),
                'errors': output.count('ERROR')
            }
        }
        
        return success, test_results
    
    def run_category(self, category: Dict[str, str]) -> None:
        """Run tests for a specific category.
        
        Args:
            category: Test category definition
        """
        name = category['name']
        pattern = category['pattern']
        
        print(f"\n{'=' * 40}")
        print(f"Running {name} Tests")
        print(f"{'=' * 40}")
        
        test_files = self.find_test_files(pattern)
        category_results = {
            'name': name,
            'pattern': pattern,
            'files_found': len(test_files),
            'tests': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': 0
            },
            'results': []
        }
        
        for test_file in test_files:
            success, test_result = self.run_test(test_file)
            category_results['results'].append(test_result)
            
            # Update category stats
            for key in ['total', 'passed', 'failed', 'skipped', 'errors']:
                category_results['tests'][key] += test_result['tests'][key]
            
            # Update global summary
            for key in ['total', 'passed', 'failed', 'skipped', 'errors']:
                self.results['summary'][key] += test_result['tests'][key]
        
        # Store category results
        self.results['categories'][name] = category_results
        
        # Print category summary
        print(f"\nSummary for {name}:")
        print(f"Files found: {category_results['files_found']}")
        print(f"Tests passed: {category_results['tests']['passed']}/{category_results['tests']['total']}")
        print(f"Tests failed: {category_results['tests']['failed']}")
        print(f"Tests with errors: {category_results['tests']['errors']}")
    
    def run_all_tests(self) -> None:
        """Run all test categories."""
        start_time = datetime.now()
        self.results['start_time'] = start_time.isoformat()
        
        # Run tests by category
        for category in self.test_categories:
            self.run_category(category)
        
        end_time = datetime.now()
        self.results['end_time'] = end_time.isoformat()
        self.results['duration_seconds'] = (end_time - start_time).total_seconds()
        
        # Output final summary
        print("\n" + "=" * 60)
        print("FINAL TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests: {self.results['summary']['total']}")
        print(f"Tests passed: {self.results['summary']['passed']}")
        print(f"Tests failed: {self.results['summary']['failed']}")
        print(f"Tests skipped: {self.results['summary']['skipped']}")
        print(f"Tests with errors: {self.results['summary']['errors']}")
        print(f"Duration: {self.results['duration_seconds']:.2f} seconds")
        
        # Save results to file
        report_filename = f"security_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(self.output_path, report_filename)
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()