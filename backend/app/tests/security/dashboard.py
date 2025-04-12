"""
NovaMind Digital Twin Security Test Dashboard

A quantum-level security testing system that provides comprehensive test collection,
execution, and visualization for the NovaMind Digital Twin platform's HIPAA compliance
and encryption capabilities.
"""

import os
import sys
import json
import subprocess
from typing import Dict, List, Any, Tuple
from datetime import datetime
import webbrowser
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))


class SecurityTestDashboard:
    """Military-grade security test dashboard for HIPAA-compliant test visualization."""
    
    def __init__(self, output_dir: str = None):
        """Initialize the dashboard.
        
        Args:
            output_dir: Directory for dashboard outputs
        """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = output_dir or os.path.join(self.base_dir, 'dashboard')
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Test categories in priority order
        self.categories = [
            {
                'name': 'Encryption',
                'description': 'Military-grade encryption for HIPAA-compliant data protection',
                'patterns': ['test_ml_encryption.py', 'test_encryption.py'],
                'priority': 'Critical'
            },
            {
                'name': 'Field Encryption',
                'description': 'Granular field-level encryption for PHI protection',
                'patterns': ['test_address_helper.py', 'test_fixtures.py'],
                'priority': 'Critical'
            },
            {
                'name': 'Authentication',
                'description': 'JWT-based authentication and authorization',
                'patterns': ['test_jwt*.py', 'test_auth*.py'],
                'priority': 'High'
            },
            {
                'name': 'HIPAA Compliance',
                'description': 'Regulatory compliance with HIPAA requirements',
                'patterns': ['test_hipaa*.py', 'test_phi*.py'],
                'priority': 'Critical'
            },
            {
                'name': 'Audit Logging',
                'description': 'Compliant audit logging for PHI access',
                'patterns': ['test_audit*.py', 'test_log*.py'],
                'priority': 'High'
            },
            {
                'name': 'API Security',
                'description': 'REST API security patterns and protections',
                'patterns': ['test_api*.py'],
                'priority': 'High'
            },
            {
                'name': 'Database Security',
                'description': 'Database access and security patterns',
                'patterns': ['test_db*.py', 'test_repository*.py', 'test_unit_of_work.py'],
                'priority': 'Medium'
            }
        ]
        
        # Dashboard state
        self.results = {}
        self.html_report_path = None
    
    def find_test_files(self, patterns: List[str]) -> List[str]:
        """Find test files matching any of the patterns.
        
        Args:
            patterns: List of file patterns to match
            
        Returns:
            Matched test files
        """
        matches = []
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith('.py'):
                    for pattern in patterns:
                        if pattern == '*' or pattern in file:
                            matches.append(os.path.join(root, file))
                            break
        return sorted(matches)
    
    def run_test_file(self, test_file: str) -> Dict[str, Any]:
        """Run a single test file and collect results.
        
        Args:
            test_file: Path to test file
            
        Returns:
            Test results
        """
        print(f"Running {os.path.basename(test_file)}...")
        result = subprocess.run(
            ['python', '-m', 'pytest', test_file, '-v', '--no-header'],
            cwd=os.path.abspath(os.path.join(self.base_dir, '../../..')),
            capture_output=True,
            text=True
        )
        
        # Parse pytest output for test results
        return {
            'file': os.path.basename(test_file),
            'success': result.returncode == 0,
            'passed': result.stdout.count('PASSED'),
            'failed': result.stdout.count('FAILED'),
            'errors': result.stdout.count('ERROR'),
            'skipped': result.stdout.count('SKIPPED'),
            'output': result.stdout,
            'error_output': result.stderr
        }
    
    def run_category(self, category: Dict[str, Any]) -> Dict[str, Any]:
        """Run all tests for a category.
        
        Args:
            category: Category definition
            
        Returns:
            Category test results
        """
        print(f"\n{'=' * 50}")
        print(f"Testing Category: {category['name']} ({category['priority']} Priority)")
        print(f"Description: {category['description']}")
        print(f"{'=' * 50}")
        
        # Find test files for this category
        test_files = self.find_test_files(category['patterns'])
        
        if not test_files:
            print(f"No test files found for patterns: {', '.join(category['patterns'])}")
            return {
                'name': category['name'],
                'description': category['description'],
                'priority': category['priority'],
                'patterns': category['patterns'],
                'files_found': 0,
                'tests_run': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'skipped': 0,
                'results': []
            }
        
        # Run each test file
        results = []
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        total_skipped = 0
        
        for test_file in test_files:
            result = self.run_test_file(test_file)
            results.append(result)
            
            total_tests += result['passed'] + result['failed'] + result['errors'] + result['skipped']
            total_passed += result['passed']
            total_failed += result['failed']
            total_errors += result['errors']
            total_skipped += result['skipped']
        
        # Summarize category results
        category_results = {
            'name': category['name'],
            'description': category['description'],
            'priority': category['priority'],
            'patterns': category['patterns'],
            'files_found': len(test_files),
            'tests_run': total_tests,
            'passed': total_passed,
            'failed': total_failed,
            'errors': total_errors,
            'skipped': total_skipped,
            'results': results
        }
        
        # Print category summary
        print(f"\nSummary for {category['name']}:")
        print(f"  Files tested: {len(test_files)}")
        print(f"  Tests run: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_failed}")
        print(f"  Errors: {total_errors}")
        print(f"  Skipped: {total_skipped}")
        print(f"  Success rate: {(total_passed / total_tests * 100) if total_tests else 0:.2f}%")
        
        return category_results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories.
        
        Returns:
            Complete test results
        """
        start_time = datetime.now()
        
        # Initialize results structure
        self.results = {
            'timestamp': start_time.isoformat(),
            'categories': [],
            'summary': {
                'total_files': 0,
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'skipped': 0
            }
        }
        
        # Run each category
        for category in self.categories:
            category_results = self.run_category(category)
            self.results['categories'].append(category_results)
            
            # Update summary
            self.results['summary']['total_files'] += category_results['files_found']
            self.results['summary']['total_tests'] += category_results['tests_run']
            self.results['summary']['passed'] += category_results['passed']
            self.results['summary']['failed'] += category_results['failed']
            self.results['summary']['errors'] += category_results['errors']
            self.results['summary']['skipped'] += category_results['skipped']
        
        # Calculate duration
        end_time = datetime.now()
        self.results['duration_seconds'] = (end_time - start_time).total_seconds()
        
        # Print final summary
        print("\n" + "=" * 60)
        print("SECURITY TEST SUMMARY")
        print("=" * 60)
        print(f"Total files tested: {self.results['summary']['total_files']}")
        print(f"Total tests run: {self.results['summary']['total_tests']}")
        print(f"Tests passed: {self.results['summary']['passed']}")
        print(f"Tests failed: {self.results['summary']['failed']}")
        print(f"Tests with errors: {self.results['summary']['errors']}")
        print(f"Tests skipped: {self.results['summary']['skipped']}")
        
        if self.results['summary']['total_tests'] > 0:
            success_rate = self.results['summary']['passed'] / self.results['summary']['total_tests'] * 100
            print(f"Overall success rate: {success_rate:.2f}%")
        
        print(f"Total duration: {self.results['duration_seconds']:.2f} seconds")
        
        # Save results as JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_path = os.path.join(self.output_dir, f'security_results_{timestamp}.json')
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed JSON results saved to: {json_path}")
        
        return self.results
    
    def generate_html_report(self) -> str:
        """Generate HTML dashboard from test results.
        
        Returns:
            Path to HTML report
        """
        if not self.results:
            raise ValueError("No test results available. Run tests first.")
        
        # Create timestamp for report
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Generate HTML content
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovaMind Digital Twin - Security Test Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background-color: #343a40;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        h1 {{
            margin: 0;
            font-size: 2.2em;
        }}
        .subtitle {{
            font-style: italic;
            margin-top: 10px;
        }}
        .summary-card {{
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            padding: 20px;
            margin: 20px 0;
        }}
        .summary-stats {{
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            margin-top: 20px;
        }}
        .stat-box {{
            flex: 1;
            min-width: 120px;
            text-align: center;
            padding: 15px;
            margin: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 0.9em;
            color: #666;
        }}
        .passed {{
            background-color: #d4edda;
            color: #155724;
        }}
        .failed {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .error {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .skipped {{
            background-color: #fff3cd;
            color: #856404;
        }}
        .total {{
            background-color: #e2e3e5;
            color: #383d41;
        }}
        .category-card {{
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            padding: 20px;
            margin: 20px 0;
        }}
        .category-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        .category-name {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        .category-priority {{
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .priority-Critical {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .priority-High {{
            background-color: #fff3cd;
            color: #856404;
        }}
        .priority-Medium {{
            background-color: #d1ecf1;
            color: #0c5460;
        }}
        .priority-Low {{
            background-color: #d4edda;
            color: #155724;
        }}
        .category-description {{
            margin-bottom: 15px;
            color: #666;
        }}
        .test-results {{
            margin-top: 20px;
        }}
        .test-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .test-table th, .test-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .test-table th {{
            background-color: #f2f2f2;
        }}
        .test-table tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .success-true {{
            color: #155724;
            font-weight: bold;
        }}
        .success-false {{
            color: #721c24;
            font-weight: bold;
        }}
        footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            border-top: 1px solid #eee;
        }}
        .meter {{
            height: 10px;
            position: relative;
            background: #f3f3f3;
            border-radius: 5px;
            margin-top: 5px;
        }}
        .meter > span {{
            display: block;
            height: 100%;
            border-radius: 5px;
            position: relative;
            overflow: hidden;
        }}
        .progress-good {{
            background-color: #28a745;
        }}
        .progress-warning {{
            background-color: #ffc107;
        }}
        .progress-bad {{
            background-color: #dc3545;
        }}
        details {{
            margin: 10px 0;
        }}
        summary {{
            cursor: pointer;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }}
        .error-output {{
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            white-space: pre-wrap;
            margin-top: 10px;
            font-size: 0.9em;
            color: #721c24;
            border-left: 3px solid #dc3545;
        }}
    </style>
</head>
<body>
    <header>
        <h1>NovaMind Digital Twin</h1>
        <div class="subtitle">Security Test Dashboard</div>
    </header>
    <div class="container">
        <div class="summary-card">
            <h2>Test Summary</h2>
            <p>Generated on: {timestamp}</p>
            <p>Test Duration: {self.results['duration_seconds']:.2f} seconds</p>
            
            <div class="summary-stats">
                <div class="stat-box total">
                    <div class="stat-number">{self.results['summary']['total_tests']}</div>
                    <div class="stat-label">Total Tests</div>
                </div>
                <div class="stat-box passed">
                    <div class="stat-number">{self.results['summary']['passed']}</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat-box failed">
                    <div class="stat-number">{self.results['summary']['failed']}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat-box error">
                    <div class="stat-number">{self.results['summary']['errors']}</div>
                    <div class="stat-label">Errors</div>
                </div>
                <div class="stat-box skipped">
                    <div class="stat-number">{self.results['summary']['skipped']}</div>
                    <div class="stat-label">Skipped</div>
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <h3>Overall Success Rate:</h3>
                <div class="meter">
                    <span style="width: {(self.results['summary']['passed'] / self.results['summary']['total_tests'] * 100) if self.results['summary']['total_tests'] else 0}%"
                          class="{
                              'progress-good' if (self.results['summary']['passed'] / self.results['summary']['total_tests'] * 100 if self.results['summary']['total_tests'] else 0) > 75 else
                              'progress-warning' if (self.results['summary']['passed'] / self.results['summary']['total_tests'] * 100 if self.results['summary']['total_tests'] else 0) > 50 else
                              'progress-bad'
                          }"></span>
                </div>
                <p style="text-align: right; margin-top: 5px;">
                    {(self.results['summary']['passed'] / self.results['summary']['total_tests'] * 100) if self.results['summary']['total_tests'] else 0:.2f}%
                </p>
            </div>
        </div>
        
        <h2>Test Categories</h2>
"""
        
        # Generate HTML for each category
        for category in self.results['categories']:
            success_rate = (category['passed'] / category['tests_run'] * 100) if category['tests_run'] > 0 else 0
            
            html += f"""
        <div class="category-card">
            <div class="category-header">
                <div class="category-name">{category['name']}</div>
                <div class="category-priority priority-{category['priority']}">{category['priority']}</div>
            </div>
            <div class="category-description">{category['description']}</div>
            
            <div>
                <strong>Files Found:</strong> {category['files_found']}
                <br>
                <strong>Tests Run:</strong> {category['tests_run']}
                <br>
                <strong>Success Rate:</strong> {success_rate:.2f}%
                <div class="meter">
                    <span style="width: {success_rate}%"
                          class="{
                              'progress-good' if success_rate > 75 else
                              'progress-warning' if success_rate > 50 else
                              'progress-bad'
                          }"></span>
                </div>
            </div>
"""
            
            # Only show test table if there are results
            if category['files_found'] > 0:
                html += """
            <div class="test-results">
                <h3>Test Results</h3>
                <table class="test-table">
                    <thead>
                        <tr>
                            <th>Test File</th>
                            <th>Success</th>
                            <th>Passed</th>
                            <th>Failed</th>
                            <th>Errors</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
"""
                
                for result in category['results']:
                    html += f"""
                        <tr>
                            <td>{result['file']}</td>
                            <td class="success-{str(result['success']).lower()}">{result['success']}</td>
                            <td>{result['passed']}</td>
                            <td>{result['failed']}</td>
                            <td>{result['errors']}</td>
                            <td>
                                <details>
                                    <summary>View Details</summary>
                                    <pre style="white-space: pre-wrap; font-size: 0.8em;">{result['output']}</pre>
                                    {f'<div class="error-output">{result["error_output"]}</div>' if result['error_output'] else ''}
                                </details>
                            </td>
                        </tr>
"""
                
                html += """
                    </tbody>
                </table>
            </div>
"""
            
            html += """
        </div>
"""
        
        # Complete HTML
        html += """
        <footer>
            <p>NovaMind Digital Twin - HIPAA Compliance and Security Testing Suite</p>
            <p>Quantum Security Analytics for Healthcare Data Protection</p>
        </footer>
    </div>
</body>
</html>
"""
        
        # Save HTML report
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.html_report_path = os.path.join(self.output_dir, f'security_dashboard_{timestamp_str}.html')
        
        with open(self.html_report_path, 'w') as f:
            f.write(html)
        
        print(f"\nInteractive dashboard generated at: {self.html_report_path}")
        return self.html_report_path
    
    def launch_dashboard(self) -> None:
        """Open the dashboard in a web browser."""
        if not self.html_report_path:
            raise ValueError("No dashboard has been generated yet. Run generate_html_report() first.")
        
        # Convert to file:// URL format
        url = Path(self.html_report_path).as_uri()
        
        print(f"Opening dashboard in browser: {url}")
        webbrowser.open(url)


if __name__ == "__main__":
    dashboard = SecurityTestDashboard()
    dashboard.run_all_tests()
    report_path = dashboard.generate_html_report()
    
    # Uncomment to automatically open in browser
    # dashboard.launch_dashboard()