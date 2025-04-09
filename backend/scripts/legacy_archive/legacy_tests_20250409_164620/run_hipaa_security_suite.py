#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# HIPAA Security Test Suite - Unified Runner
# 
# This script provides a consistent interface for running HIPAA security tests
# from both Windows and WSL2 environments.
# =============================================================================

import argparse
import os
import subprocess
import sys
import datetime
import json
from pathlib import Path

# Configuration
DEFAULT_REPORT_DIR = "./security-reports"

def get_timestamp():
    """Return current timestamp in a format suitable for filenames."""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def setup_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Unified HIPAA Security Testing Suite")
    parser.add_argument("--report-dir", default=DEFAULT_REPORT_DIR, 
                      help=f"Directory to store reports (default: {DEFAULT_REPORT_DIR})")
    parser.add_argument("--verbose", action="store_true", 
                      help="Enable verbose output")
    parser.add_argument("--skip-static", action="store_true", 
                      help="Skip static code analysis")
    parser.add_argument("--skip-dependency", action="store_true", 
                      help="Skip dependency vulnerability checks")
    parser.add_argument("--skip-phi", action="store_true", 
                      help="Skip PHI pattern detection")
    
    return parser.parse_args()

def ensure_directory(path):
    """Ensure directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)
    return path

def run_static_analysis(report_dir, verbose=False):
    """Run static code analysis using bandit."""
    print("Running static code analysis...")
    
    timestamp = get_timestamp()
    html_report = os.path.join(report_dir, f"static-analysis-{timestamp}.html")
    json_report = os.path.join(report_dir, f"static-analysis-{timestamp}.json")
    
    cmd = [
        "bandit", "-r", ".", "-f", "html", "-o", html_report,
        "--exclude", "./venv,./tests,./.git"
    ]
    
    if verbose:
        print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        # Also save JSON report for programmatic analysis
        with open(json_report, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "command": " ".join(cmd),
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }, f, indent=2)
            
        print(f"Static analysis report saved to: {html_report}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running static analysis: {e}")
        return False

def run_dependency_check(report_dir, verbose=False):
    """Run dependency vulnerability check using safety."""
    print("Running dependency vulnerability check...")
    
    timestamp = get_timestamp()
    json_report = os.path.join(report_dir, f"dependency-report-{timestamp}.json")
    
    requirements_files = ["requirements.txt", "requirements-dev.txt", "requirements-security.txt"]
    success = True
    
    for req_file in requirements_files:
        if not os.path.exists(req_file):
            continue
            
        cmd = ["pip-audit", "-r", req_file, "--format", "json"]
        
        if verbose:
            print(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Save report
            report_file = os.path.join(report_dir, f"dependency-check-{req_file}.json")
            with open(report_file, "w") as f:
                f.write(result.stdout)
                
            # Also save text version for human readability
            text_report_file = os.path.join(report_dir, f"dependency-check-{req_file}.txt")
            with open(text_report_file, "w") as f:
                f.write(f"Dependency check for {req_file}:\n\n")
                f.write(result.stdout)
                f.write("\n\n")
                if result.stderr:
                    f.write(f"Errors:\n{result.stderr}\n")
            
            success = success and (result.returncode == 0)
        except Exception as e:
            print(f"Error checking dependencies in {req_file}: {e}")
            success = False
    
    # Aggregate results in main report
    with open(json_report, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "requirements_files": requirements_files,
            "success": success
        }, f, indent=2)
        
    return success

def run_phi_pattern_detection(report_dir, verbose=False):
    """Run PHI pattern detection in code and data files."""
    print("Running PHI pattern detection...")
    
    # PHI patterns to look for (regex patterns)
    phi_patterns = [
        # Social Security Numbers
        r"\b\d{3}-\d{2}-\d{4}\b",
        # Common PHI prefixes with numbers
        r"\b(patient|medical|record|diagnosis|treatment|ssn|dob|mrn)\s*[#:]?\s*\w+\b",
        # Email addresses 
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        # Dates of birth
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        # IP Addresses
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
    ]
    
    # File extensions to check
    extensions = [".py", ".json", ".yaml", ".yml", ".md", ".txt", ".sql"]
    
    # Directories to exclude
    exclude_dirs = ["venv", ".git", "__pycache__", "node_modules"]
    
    findings = []
    
    # Walk through all files
    for root, dirs, files in os.walk("."):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if not any(file.endswith(ext) for ext in extensions):
                continue
                
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                    for pattern in phi_patterns:
                        import re
                        matches = re.finditer(pattern, content)
                        
                        for match in matches:
                            findings.append({
                                "file": file_path,
                                "pattern": pattern,
                                "match": match.group(),
                                "line_number": content[:match.start()].count("\n") + 1
                            })
            except Exception as e:
                if verbose:
                    print(f"Error reading {file_path}: {e}")
    
    # Save findings to report
    timestamp = get_timestamp()
    report_file = os.path.join(report_dir, f"hipaa_security_report_{timestamp}.json")
    
    with open(report_file, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "phi_patterns_checked": phi_patterns,
            "files_checked": extensions,
            "findings": findings
        }, f, indent=2)
    
    if findings:
        print(f"Found {len(findings)} potential PHI patterns. See {report_file} for details.")
        return False
    else:
        print("No PHI patterns detected.")
        return True

def generate_summary(report_dir, results):
    """Generate a summary report of all test results."""
    timestamp = get_timestamp()
    summary_file = os.path.join(report_dir, "security-report.json")
    summary_html = os.path.join(report_dir, "security-report.html")
    summary_md = os.path.join(report_dir, "security-report.md")
    
    summary = {
        "timestamp": timestamp,
        "overall_result": all(results.values()),
        "tests": results
    }
    
    # Write JSON summary
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    # Write HTML summary
    with open(summary_html, "w") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>HIPAA Security Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #333366; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
</head>
<body>
    <h1>HIPAA Security Report</h1>
    <p>Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    
    <h2>Summary</h2>
    <p>Overall Result: <span class="{'success' if all(results.values()) else 'failure'}">
        {'PASS' if all(results.values()) else 'FAIL'}
    </span></p>
    
    <table>
        <tr>
            <th>Test</th>
            <th>Result</th>
        </tr>
""")
        # Add table rows separately to avoid f-string backslash issues
        for test, result in results.items():
            result_class = "success" if result else "failure"
            f.write(f"        <tr><td>{test}</td><td class=\"{result_class}\">{result}</td></tr>\n")
        
        f.write(f"""    </table>
    
    <h2>Recommendations</h2>
    <p>Please review the detailed reports in the {report_dir} directory for specific findings and recommendations.</p>
</body>
</html>""")
    
    # Write Markdown summary
    with open(summary_md, "w") as f:
        f.write(f"""# HIPAA Security Report

Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

Overall Result: **{'PASS' if all(results.values()) else 'FAIL'}**

| Test | Result |
|------|--------|
{chr(10).join(f"| {test} | {'✅ PASS' if result else '❌ FAIL'} |" for test, result in results.items())}

## Recommendations

Please review the detailed reports in the `{report_dir}` directory for specific findings and recommendations.
""")
    
    return summary

def main():
    """Main entry point for the script."""
    args = setup_args()
    report_dir = ensure_directory(args.report_dir)
    
    print("=" * 80)
    print("NOVAMIND HIPAA Security Test Suite")
    print("=" * 80)
    print(f"Report directory: {report_dir}")
    print(f"Verbose mode: {'enabled' if args.verbose else 'disabled'}")
    print(f"Skip static analysis: {'yes' if args.skip_static else 'no'}")
    print(f"Skip dependency check: {'yes' if args.skip_dependency else 'no'}")
    print(f"Skip PHI pattern detection: {'yes' if args.skip_phi else 'no'}")
    print("=" * 80)
    
    results = {}
    
    # Run tests based on configuration
    if not args.skip_static:
        results["static_analysis"] = run_static_analysis(report_dir, args.verbose)
    
    if not args.skip_dependency:
        results["dependency_check"] = run_dependency_check(report_dir, args.verbose)
    
    if not args.skip_phi:
        results["phi_pattern_detection"] = run_phi_pattern_detection(report_dir, args.verbose)
    
    # Generate summary report
    summary = generate_summary(report_dir, results)
    
    # Print final results
    print("\n" + "=" * 80)
    print(f"HIPAA Security Test Suite - {'PASS' if all(results.values()) else 'FAIL'}")
    print("=" * 80)
    for test, result in results.items():
        print(f"{test}: {'PASS' if result else 'FAIL'}")
    print("=" * 80)
    print(f"Reports saved to: {report_dir}")
    print("=" * 80)
    
    # Return exit code based on overall result
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())