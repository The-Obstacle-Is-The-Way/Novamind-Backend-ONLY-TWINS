#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified HIPAA Security Suite

This script provides a comprehensive HIPAA security testing framework that:
1. Performs static code analysis to identify security vulnerabilities
2. Checks dependencies for known vulnerabilities
3. Detects Protected Health Information (PHI) patterns in code
4. Validates API endpoint authentication and authorization
5. Verifies proper configuration for HIPAA compliance
6. Checks logging functionality for PHI leakage
7. Runs security-specific unit tests

Usage:
    python scripts/unified_hipaa_security_suite.py [options]

Options:
    --report-dir DIR    Directory to store reports (default: ./security-reports)
    --skip-static       Skip static code analysis
    --skip-deps         Skip dependency vulnerability checks
    --skip-phi          Skip PHI pattern detection
    --skip-api          Skip API security checks
    --skip-config       Skip configuration validation
    --skip-tests        Skip security tests
    --verbose           Enable verbose output
    --html              Generate HTML report
    --json              Generate JSON report
"""

import os
import sys
import argparse
import datetime
import json
import subprocess
import re
import logging
from pathlib import Path
import platform
from typing import Dict, List, Any, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_REPORT_DIR = "./security-reports"


class PHIDetector:
    """PHI Detection class for identifying protected health information."""

    def __init__(self):
        """Initialize the PHI detector with PHI patterns."""
        self.patterns = [
            # SSN pattern - explicit format XXX-XX-XXXX
            r'\b\d{3}-\d{2}-\d{4}\b',
            # SSN without dashes
            r'\b\d{9}\b',
            # Email addresses
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # Phone numbers
            r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',
            r'\b\d{3}-\d{3}-\d{4}\b',
            # Credit card numbers
            r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11})\b',
            # Names (common pattern in code)
            r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s[A-Z][a-z]+ [A-Z][a-z]+\b',
            # Patient identifiers
            r'\bPATIENT[_-]?ID[_-]?\d+\b',
            r'\bPT[_-]?ID[_-]?\d+\b',
            # Medical record numbers
            r'\bMRN[_-]?\d+\b',
            r'\bMEDICAL[_-]?RECORD[_-]?\d+\b',
        ]

    def detect_phi(self, content: str) -> List[Dict[str, Any]]:
        """
        Detect potential PHI in content.
        
        Args:
            content: Text content to scan for PHI
            
        Returns:
            List of PHI matches with pattern and type
        """
        matches = []
        for pattern in self.patterns:
            findings = re.finditer(pattern, content)
            for match in findings:
                pattern_str = match.group(0)
                phi_type = self._determine_phi_type(pattern_str)
                matches.append({
                    "pattern": pattern_str,
                    "type": phi_type
                })
        
        return matches

    def _determine_phi_type(self, pattern: str) -> str:
        """Determine the type of PHI based on the pattern."""
        if re.match(r'\d{3}-\d{2}-\d{4}', pattern):
            return "SSN"
        elif re.match(r'\d{9}$', pattern):
            return "SSN (no dashes)"
        elif '@' in pattern:
            return "Email"
        elif re.match(r'\d{3}-\d{3}-\d{4}', pattern) or re.match(r'\(\d{3}\)', pattern):
            return "Phone"
        elif re.match(r'4[0-9]{12}', pattern) or re.match(r'5[1-5][0-9]{14}', pattern):
            return "Credit Card"
        elif "Mr." in pattern or "Mrs." in pattern or "Ms." in pattern or "Dr." in pattern:
            return "Name"
        elif "PATIENT" in pattern or "PT" in pattern:
            return "Patient ID"
        elif "MRN" in pattern or "MEDICAL" in pattern:
            return "Medical Record Number"
        else:
            return "Unknown PHI"


class HIPAASecuritySuite:
    """Comprehensive HIPAA security testing suite."""

    def __init__(self, args):
        """Initialize the security suite with command line arguments."""
        self.args = args
        self.report_dir = args.report_dir
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {
            "static_analysis": None,
            "dependency_check": None,
            "phi_detection": None,
            "api_security": None,
            "configuration": None,
            "logging": None,
            "security_tests": None
        }
        self.findings = {
            "static_analysis": [],
            "dependency_check": [],
            "phi_detection": [],
            "api_security": [],
            "configuration": [],
            "logging": []
        }
        
        # Create report directory if it doesn't exist
        os.makedirs(self.report_dir, exist_ok=True)
        
        # Set up report file paths
        self.report_files = {
            "static_analysis": os.path.join(self.report_dir, f"static-analysis-{self.timestamp}"),
            "dependency_check": os.path.join(self.report_dir, f"dependency-report-{self.timestamp}"),
            "phi_detection": os.path.join(self.report_dir, f"phi-detection-{self.timestamp}"),
            "api_security": os.path.join(self.report_dir, f"api-security-{self.timestamp}"),
            "configuration": os.path.join(self.report_dir, f"configuration-{self.timestamp}"),
            "logging": os.path.join(self.report_dir, f"logging-{self.timestamp}"),
            "security_tests": os.path.join(self.report_dir, f"security-tests-{self.timestamp}"),
            "summary": os.path.join(self.report_dir, f"hipaa-security-report-{self.timestamp}")
        }

    def run_static_analysis(self) -> bool:
        """Run static code analysis using bandit."""
        if self.args.skip_static:
            logger.info("Skipping static code analysis")
            return True
            
        logger.info("Running static code analysis...")
        
        html_report = f"{self.report_files['static_analysis']}.html"
        json_report = f"{self.report_files['static_analysis']}.json"
        
        cmd = [
            "bandit", "-r", "app/", "-f", "html", "-o", html_report,
            "--exclude", "./venv,./tests,./.git"
        ]
        
        if self.args.verbose:
            logger.info(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Also save JSON report for programmatic analysis
            bandit_json_cmd = [
                "bandit", "-r", "app/", "-f", "json", "-o", json_report,
                "--exclude", "./venv,./tests,./.git"
            ]
            subprocess.run(bandit_json_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Static analysis passed. Report saved to: {html_report}")
            else:
                logger.warning(f"Static analysis found issues. See {html_report} for details.")
                # Parse JSON report to extract findings
                try:
                    with open(json_report, 'r') as f:
                        data = json.load(f)
                        for result in data.get("results", []):
                            self.findings["static_analysis"].append({
                                "file": result.get("filename"),
                                "line": result.get("line_number"),
                                "severity": result.get("issue_severity"),
                                "issue": result.get("issue_text")
                            })
                except Exception as e:
                    logger.error(f"Error parsing static analysis JSON report: {e}")
            
            self.results["static_analysis"] = result.returncode == 0
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error running static analysis: {e}")
            self.results["static_analysis"] = False
            return False

    def run_dependency_check(self) -> bool:
        """Run dependency vulnerability check using safety and pip-audit."""
        if self.args.skip_deps:
            logger.info("Skipping dependency vulnerability check")
            return True
            
        logger.info("Running dependency vulnerability check...")
        
        requirements_files = ["requirements.txt", "requirements-dev.txt", "requirements-security.txt"]
        success = True
        
        for req_file in requirements_files:
            if not os.path.exists(req_file):
                continue
                
            json_report = f"{self.report_files['dependency_check']}-{req_file}.json"
            
            # Use pip-audit for comprehensive checks
            cmd = ["pip-audit", "-r", req_file, "--format", "json"]
            
            if self.args.verbose:
                logger.info(f"Running command: {' '.join(cmd)}")
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                # Save report
                with open(json_report, "w") as f:
                    f.write(result.stdout)
                    
                # Also save text version for human readability
                text_report = f"{self.report_files['dependency_check']}-{req_file}.txt"
                with open(text_report, "w") as f:
                    f.write(f"Dependency check for {req_file}:\n\n")
                    f.write(result.stdout)
                    f.write("\n\n")
                    if result.stderr:
                        f.write(f"Errors:\n{result.stderr}\n")
                
                # Parse results to extract findings
                try:
                    data = json.loads(result.stdout)
                    for vuln in data.get("vulnerabilities", []):
                        self.findings["dependency_check"].append({
                            "package": vuln.get("name"),
                            "installed_version": vuln.get("installed_version"),
                            "vulnerable_version": vuln.get("vulnerable_spec"),
                            "description": vuln.get("description"),
                            "severity": vuln.get("severity", "unknown"),
                            "fix_version": vuln.get("fix_versions", [])[0] if vuln.get("fix_versions") else None
                        })
                except Exception as e:
                    logger.error(f"Error parsing dependency check JSON data: {e}")
                
                if result.returncode != 0:
                    if "requirements-security.txt" in req_file:
                        # Security dependencies should never have vulnerabilities
                        logger.error(f"Critical: Vulnerabilities found in security dependencies!")
                        success = False
                    else:
                        logger.warning(f"Vulnerabilities found in {req_file}")
            except Exception as e:
                logger.error(f"Error checking dependencies in {req_file}: {e}")
                success = False
        
        self.results["dependency_check"] = success
        return success

    def run_phi_detection(self) -> bool:
        """Run PHI pattern detection in code and data files."""
        if self.args.skip_phi:
            logger.info("Skipping PHI pattern detection")
            return True
            
        logger.info("Running PHI pattern detection...")
        
        phi_detector = PHIDetector()
        
        # File extensions to check
        extensions = [".py", ".json", ".yaml", ".yml", ".md", ".txt", ".sql"]
        
        # Directories to exclude
        exclude_dirs = ["venv", ".git", "__pycache__", "node_modules"]
        
        findings = []
        
        # Walk through all files
        for root, dirs, files in os.walk("app/"):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if not any(file.endswith(ext) for ext in extensions):
                    continue
                    
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                        # Check if this is a test file focused on PHI testing
                        is_test_file = "test" in file_path.lower() or "/tests/" in file_path
                        is_phi_test = False
                        
                        if is_test_file:
                            # Check if this file is specifically for testing PHI detection
                            phi_indicators = ["phi", "hipaa", "ssn", "protected health", "sanitize", "redact"]
                            test_keywords = ["test", "mock", "example", "fixture", "sample"]
                            
                            has_phi_indicator = any(indicator in content.lower() for indicator in phi_indicators)
                            has_test_indicator = any(indicator in content.lower() for indicator in test_keywords)
                            
                            # For test files that are specifically about PHI detection, we flag them
                            # as allowed PHI test files
                            if has_phi_indicator and has_test_indicator:
                                is_phi_test = True
                        
                        # Detect PHI patterns
                        matches = phi_detector.detect_phi(content)
                        
                        if matches:
                            # Generate evidence with line numbers
                            lines = content.split("\n")
                            evidence_lines = []
                            
                            for match in matches:
                                pattern = match.get("pattern", "")
                                
                                for i, line in enumerate(lines):
                                    if pattern in line:
                                        evidence_lines.append(f"Line {i+1}: {line}")
                                        break
                            
                            evidence = "\n".join(evidence_lines)
                            
                            # Add to findings if not in a PHI test file, or if it's a PHI detection test
                            if not is_phi_test or "test_phi_audit" in file_path or "test_ssn_pattern_detection" in file_path:
                                findings.append({
                                    "file": file_path,
                                    "is_test_file": is_test_file,
                                    "is_allowed_phi_test": is_phi_test,
                                    "matches": matches,
                                    "evidence": evidence
                                })
                                
                                self.findings["phi_detection"].append({
                                    "file": file_path,
                                    "issue": "PHI detected in file",
                                    "evidence": evidence,
                                    "is_allowed": is_phi_test and not ("test_phi_audit" in file_path or "test_ssn_pattern_detection" in file_path)
                                })
                except Exception as e:
                    if self.args.verbose:
                        logger.error(f"Error reading {file_path}: {e}")
        
        # Save findings to report
        report_json = f"{self.report_files['phi_detection']}.json"
        report_txt = f"{self.report_files['phi_detection']}.txt"
        
        with open(report_json, "w") as f:
            json.dump({
                "timestamp": self.timestamp,
                "findings": findings
            }, f, indent=2)
        
        # Create text report for human readability
        with open(report_txt, "w") as f:
            f.write(f"PHI Detection Report - {datetime.datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
            
            if not findings:
                f.write("No PHI patterns detected.\n")
            else:
                f.write(f"Found {len(findings)} files with potential PHI patterns:\n\n")
                
                for i, finding in enumerate(findings, 1):
                    f.write(f"Finding #{i}: {finding['file']}\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Test file: {'Yes' if finding['is_test_file'] else 'No'}\n")
                    f.write(f"Allowed PHI test: {'Yes' if finding['is_allowed_phi_test'] else 'No'}\n")
                    f.write("\nEvidence:\n")
                    f.write(finding['evidence'] + "\n\n")
                    f.write("Matches:\n")
                    
                    for match in finding['matches']:
                        f.write(f"  - Type: {match['type']}, Pattern: {match['pattern']}\n")
                    
                    f.write("\n" + "=" * 40 + "\n\n")
        
        # Determine if test passed - we allow PHI in designated test files
        non_test_findings = [f for f in findings if not f['is_allowed_phi_test'] or 
                            "test_phi_audit" in f['file'] or "test_ssn_pattern_detection" in f['file']]
        
        if non_test_findings:
            logger.warning(f"Found {len(non_test_findings)} files with PHI patterns not in allowed test files. See {report_txt} for details.")
            self.results["phi_detection"] = False
            return False
        else:
            logger.info("No unauthorized PHI patterns detected.")
            self.results["phi_detection"] = True
            return True

    def check_api_security(self) -> bool:
        """Check API endpoints for proper authentication and authorization."""
        if self.args.skip_api:
            logger.info("Skipping API security checks")
            return True
            
        logger.info("Checking API endpoints for proper security...")
        
        findings = []
        api_files = []
        
        # Find API endpoint files
        api_path_indicators = [
            "/api/", "endpoints", "router", "/controllers/", "/routes/", 
            "app.py", "main.py", "server.py", "fastapi", "flask", "express"
        ]
        
        for root, _, files in os.walk("app/"):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                file_path = os.path.join(root, file)
                
                if any(indicator in file_path.lower() for indicator in api_path_indicators):
                    api_files.append(file_path)
        
        # Check each API file for authentication
        for file_path in api_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                    # Check for endpoints without authentication
                    endpoint_patterns = [
                        r'@app\.route', 
                        r'@router\.(get|post|put|delete|patch)',
                        r'@api_router\.(get|post|put|delete|patch)',
                        r'app\.add_api_route'
                    ]
                    
                    auth_patterns = [
                        r'authenticate', 
                        r'authorize',
                        r'Depends\(',
                        r'security',
                        r'oauth2_scheme',
                        r'jwt',
                        r'token'
                    ]
                    
                    # Check if file contains API endpoints
                    has_endpoints = False
                    for pattern in endpoint_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            has_endpoints = True
                            
                            # Check surrounding lines for authentication
                            start_pos = max(0, match.start() - 200)
                            end_pos = min(len(content), match.end() + 200)
                            context = content[start_pos:end_pos]
                            
                            has_auth = any(re.search(pattern, context) for pattern in auth_patterns)
                            
                            if not has_auth:
                                # Extract the endpoint definition
                                lines = content.split('\n')
                                line_no = content[:match.start()].count('\n')
                                evidence = '\n'.join(lines[max(0, line_no-2):min(len(lines), line_no+5)])
                                
                                findings.append({
                                    "file": file_path,
                                    "line": line_no + 1,
                                    "evidence": evidence,
                                    "issue": "API endpoint without authentication"
                                })
                                
                                self.findings["api_security"].append({
                                    "file": file_path,
                                    "line": line_no + 1,
                                    "issue": "API endpoint without authentication",
                                    "evidence": evidence
                                })
            except Exception as e:
                logger.error(f"Error checking API security in {file_path}: {e}")
        
        # Save findings to report
        report_json = f"{self.report_files['api_security']}.json"
        report_txt = f"{self.report_files['api_security']}.txt"
        
        with open(report_json, "w") as f:
            json.dump({
                "timestamp": self.timestamp,
                "findings": findings
            }, f, indent=2)
        
        # Create text report for human readability
        with open(report_txt, "w") as f:
            f.write(f"API Security Report - {datetime.datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
            
            if not findings:
                f.write("All API endpoints have proper authentication.\n")
            else:
                f.write(f"Found {len(findings)} API endpoints without proper authentication:\n\n")
                
                for i, finding in enumerate(findings, 1):
                    f.write(f"Finding #{i}: {finding['file']} (Line {finding['line']})\n")
                    f.write("-" * 40 + "\n")
                    f.write("\nEvidence:\n")
                    f.write(finding['evidence'] + "\n\n")
                    f.write(f"Issue: {finding['issue']}\n")
                    f.write("\n" + "=" * 40 + "\n\n")
        
        if findings:
            logger.warning(f"Found {len(findings)} API endpoints without proper authentication. See {report_txt} for details.")
            self.results["api_security"] = False
            return False
        else:
            logger.info("All API endpoints have proper authentication.")
            self.results["api_security"] = True
            return True

    def check_configuration(self) -> bool:
        """Check configuration files for proper security settings."""
        if self.args.skip_config:
            logger.info("Skipping configuration checks")
            return True
            
        logger.info("Checking configuration for proper security settings...")
        
        findings = []
        config_files = []
        
        # Find config files
        for root, _, files in os.walk("app/"):
            for file in files:
                file_path = os.path.join(root, file)
                
                if "config" in file_path.lower() or file.endswith('.env') or file.endswith('.env.example'):
                    config_files.append(file_path)
        
        # If no config files found, add an issue
        if not config_files:
            findings.append({
                "file": "N/A",
                "issue": "No configuration files found",
                "evidence": "No configuration files found in the project"
            })
            
            self.findings["configuration"].append({
                "file": "N/A",
                "issue": "No configuration files found",
                "evidence": "No configuration files found in the project"
            })
        
        # Check each config file for security settings
        security_settings = [
            "JWT_SECRET",
            "ENCRYPTION_KEY",
            "SSL_CERT",
            "AUTH_REQUIRED",
            "HIPAA_COMPLIANT",
            "SESSION_TIMEOUT"
        ]
        
        for file_path in config_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                    missing_settings = []
                    for setting in security_settings:
                        if setting not in content:
                            missing_settings.append(setting)
                    
                    if missing_settings:
                        findings.append({
                            "file": file_path,
                            "issue": "Missing security settings",
                            "missing_settings": missing_settings,
                            "evidence": f"Configuration file does not contain: {', '.join(missing_settings)}"
                        })
                        
                        self.findings["configuration"].append({
                            "file": file_path,
                            "issue": "Missing security settings",
                            "missing_settings": missing_settings,
                            "evidence": f"Configuration file does not contain: {', '.join(missing_settings)}"
                        })
            except Exception as e:
                logger.error(f"Error checking configuration in {file_path}: {e}")
        
        # Save findings to report
        report_json = f"{self.report_files['configuration']}.json"
        report_txt = f"{self.report_files['configuration']}.txt"
        
        with open(report_json, "w") as f:
            json.dump({
                "timestamp": self.timestamp,
                "findings": findings
            }, f, indent=2)
        
        # Create text report for human readability
        with open(report_txt, "w") as f:
            f.write(f"Configuration Security Report - {datetime.datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
            
            if not findings:
                f.write("All configuration files have proper security settings.\n")
            else:
                f.write(f"Found {len(findings)} configuration issues:\n\n")
                
                for i, finding in enumerate(findings, 1):
                    f.write(f"Finding #{i}: {finding['file']}\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Issue: {finding['issue']}\n")
                    f.write(f"Evidence: {finding['evidence']}\n")
                    if "missing_settings" in finding:
                        f.write(f"Missing Settings: {', '.join(finding['missing_settings'])}\n")
                    f.write("\n" + "=" * 40 + "\n\n")
        
        if findings:
            logger.warning(f"Found {len(findings)} configuration issues. See {report_txt} for details.")
            self.results["configuration"] = False
            return False
        else:
            logger.info("All configuration files have proper security settings.")
            self.results["configuration"] = True
            return True

    def check_logging(self) -> bool:
        """Check logging for proper PHI sanitization."""
        logger.info("Checking logging for proper PHI sanitization...")
        
        findings = []
        
        # PHI variable patterns to look for
        phi_variable_patterns = [
            r'patient', r'name', r'ssn', r'email', r'address', r'phone',
            r'dob', r'birth', r'medical', r'record', r'mrn', r'diagnosis'
        ]
        
        # Look for logging statements in code
        for root, _, files in os.walk("app/"):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                        # Check for logging without sanitization
                        if re.search(r'(logger\.|logging\.|print\()', content):
                            # Look for potential PHI variables near logging
                            for pattern in phi_variable_patterns:
                                # Look for variables that might contain PHI near logging statements
                                matches = re.finditer(rf'(logger\.|logging\.|print\().*{pattern}', content, re.IGNORECASE | re.MULTILINE)
                                
                                for match in matches:
                                    # Get the line for context
                                    start_pos = max(0, match.start() - 200)
                                    end_pos = min(len(content), match.end() + 200)
                                    context = content[start_pos:end_pos]
                                    
                                    if not re.search(r'sanitize|redact|mask|anonymize', context, re.IGNORECASE):
                                        # Extract the logging statement
                                        lines = content.split('\n')
                                        line_no = content[:match.start()].count('\n')
                                        evidence = '\n'.join(lines[max(0, line_no-2):min(len(lines), line_no+3)])
                                        
                                        findings.append({
                                            "file": file_path,
                                            "line": line_no + 1,
                                            "evidence": evidence,
                                            "issue": f"Potential unsanitized PHI in logging (variable: {pattern})"
                                        })
                                        
                                        self.findings["logging"].append({
                                            "file": file_path,
                                            "line": line_no + 1,
                                            "issue": "Potential unsanitized PHI in logging",
                                            "evidence": evidence
                                        })
                                        break
                except Exception as e:
                    logger.error(f"Error checking logging in {file_path}: {e}")
        
        # Save findings to report
        report_json = f"{self.report_files['logging']}.json"
        report_txt = f"{self.report_files['logging']}.txt"
        
        with open(report_json, "w") as f:
            json.dump({
                "timestamp": self.timestamp,
                "findings": findings
            }, f, indent=2)
        
        # Create text report for human readability
        with open(report_txt, "w") as f:
            f.write(f"Logging Security Report - {datetime.datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
            
            if not findings:
                f.write("All logging statements properly sanitize PHI.\n")
            else:
                f.write(f"Found {len(findings)} logging statements with potential unsanitized PHI:\n\n")
                
                for i, finding in enumerate(findings, 1):
                    f.write(f"Finding #{i}: {finding['file']} (Line {finding['line']})\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Issue: {finding['issue']}\n")
                    f.write("\nEvidence:\n")
                    f.write(finding['evidence'] + "\n\n")
                    f.write("\n" + "=" * 40 + "\n\n")
        
        if findings:
            logger.warning(f"Found {len(findings)} logging statements with potential unsanitized PHI. See {report_txt} for details.")
            self.results["logging"] = False
            return False
        else:
            logger.info("All logging statements properly sanitize PHI.")
            self.results["logging"] = True
            return True

    def run_security_tests(self) -> bool:
        """Run security-specific tests."""
        if self.args.skip_tests:
            logger.info("Skipping security tests")
            return True
            
        logger.info("Running security tests...")
        
        # Run security tests using pytest
        report_xml = f"{self.report_files['security_tests']}.xml"
        
        cmd = [
            "python", "-m", "pytest", "app/tests/security/", "-v", 
            "--junitxml", report_xml
        ]
        
        if self.args.verbose:
            logger.info(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Save logs
            log_file = f"{self.report_files['security_tests']}.log"
            with open(log_file, "w") as f:
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n\nErrors:\n")
                    f.write(result.stderr)
            
            if result.returncode == 0:
                logger.info("All security tests passed.")
            else:
                logger.warning(f"Some security tests failed. See {log_file} for details.")
            
            self.results["security_tests"] = result.returncode == 0
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error running security tests: {e}")
            self.results["security_tests"] = False
            return False

    def generate_reports(self) -> Tuple[str, str]:
        """Generate HTML and JSON summary reports."""
        logger.info("Generating summary reports...")
        
        # Get summary results
        passed_checks = sum(1 for result in self.results.values() if result is True)
        total_checks = sum(1 for result in self.results.values() if result is not None)
        
        # Prepare report data
        report_data = {
            "timestamp": self.timestamp,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overall_result": all(result for result in self.results.values() if result is not None),
            "checks": {
                name: {
                    "status": "PASS" if result else "FAIL" if result is not None else "SKIPPED",
                    "passed": result is True,
                    "skipped": result is None,
                    "findings": self.findings.get(name, [])
                }
                for name, result in self.results.items()
            },
            "summary": {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "failed_checks": total_checks - passed_checks,
                "passing_percentage": round(passed_checks / total_checks * 100) if total_checks > 0 else 0
            }
        }
        
        # Generate JSON report
        json_report = f"{self.report_files['summary']}.json"
        with open(json_report, "w") as f:
            json.dump(report_data, f, indent=2)
        
        # Generate HTML report
        html_report = f"{self.report_files['summary']}.html"
        with open(html_report, "w") as f:
            f.write(self._generate_html_report(report_data))
        
        # Generate text report
        txt_report = f"{self.report_files['summary']}.txt"
        with open(txt_report, "w") as f:
            f.write(self._generate_text_report(report_data))
        
        logger.info(f"Reports generated:")
        logger.info(f"  - JSON: {json_report}")
        logger.info(f"  - HTML: {html_report}")
        logger.info(f"  - Text: {txt_report}")
        
        return html_report, json_report

    def _generate_html_report(self, data: Dict[str, Any]) -> str:
        """Generate HTML report from report data."""
        passed = data["overall_result"]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>HIPAA Security Compliance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ color: #3498db; margin-top: 30px; }}
        .pass {{ color: #27ae60; font-weight: bold; }}
        .fail {{ color: #e74c3c; font-weight: bold; }}
        .warning {{ color: #f39c12; font-weight: bold; }}
        .skipped {{ color: #95a5a6; font-weight: bold; }}
        .result-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .result-table th, .result-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .result-table th {{ background-color: #f8f9fa; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .details {{ margin-top: 50px; }}
        .detail-section {{ margin-bottom: 30px; }}
        .finding {{ margin-bottom: 20px; border-left: 4px solid #e74c3c; padding-left: 10px; }}
        .finding pre {{ background-color: #f8f9f9; padding: 10px; border-radius: 4px; overflow-x: auto; }}
        .summary-box {{ 
            border-radius: 5px; 
            padding: 15px; 
            margin-bottom: 20px; 
            background-color: {'#e8f8f5' if passed else '#fdeeee'}; 
            border: 2px solid {'#27ae60' if passed else '#e74c3c'};
        }}
        .evidence-box {{ 
            background-color: #f8f9fa; 
            border: 1px solid #ddd; 
            padding: 10px; 
            margin: 10px 0; 
            font-family: monospace; 
            white-space: pre-wrap; 
            max-height: 200px; 
            overflow-y: auto; 
        }}
    </style>
</head>
<body>
    <h1>HIPAA Security Compliance Report</h1>
    <p>Generated on: {data["date"]}</p>
    
    <div class="summary-box">
        <h2>Executive Summary</h2>
        <p>Overall Result: <span class="{'pass' if passed else 'fail'}">
            {'PASS - System meets HIPAA security requirements' if passed else 'FAIL - System does not meet HIPAA security requirements'}
        </span></p>
        <p>Passing Checks: {data["summary"]["passed_checks"]} / {data["summary"]["total_checks"]} ({data["summary"]["passing_percentage"]}%)</p>
    </div>
    
    <h2>Check Results</h2>
    <table class="result-table">
        <tr>
            <th>Check</th>
            <th>Status</th>
            <th>Findings</th>
        </tr>
"""
        
        # Add table rows for each check
        checks = {
            "static_analysis": "Static Code Analysis",
            "dependency_check": "Dependency Vulnerability Check",
            "phi_detection": "PHI Pattern Detection",
            "api_security": "API Security Check",
            "configuration": "Configuration Security Check",
            "logging": "Logging Sanitization Check",
            "security_tests": "Security Tests"
        }
        
        for check_id, check_name in checks.items():
            check_data = data["checks"].get(check_id, {})
            status = check_data.get("status", "SKIPPED")
            status_class = "pass" if status == "PASS" else "fail" if status == "FAIL" else "skipped"
            findings_count = len(check_data.get("findings", []))
            
            html += f"""
        <tr>
            <td>{check_name}</td>
            <td class="{status_class}">{status}</td>
            <td>{findings_count} finding{'s' if findings_count != 1 else ''}</td>
        </tr>"""
        
        html += """
    </table>
    
    <div class="details">
        <h2>Detailed Findings</h2>
"""
        
        # Add detailed findings for each check
        for check_id, check_name in checks.items():
            check_data = data["checks"].get(check_id, {})
            findings = check_data.get("findings", [])
            
            if not findings:
                continue
            
            html += f"""
        <div class="detail-section">
            <h3>{check_name}</h3>
            <p>Found {len(findings)} issue{'s' if len(findings) != 1 else ''}:</p>
"""
            
            for i, finding in enumerate(findings, 1):
                html += f"""
            <div class="finding">
                <h4>Finding #{i}: {finding.get('file', 'Unknown file')}</h4>
                <p><strong>Issue:</strong> {finding.get('issue', 'Unknown issue')}</p>
"""
                
                if 'line' in finding:
                    html += f"""
                <p><strong>Line:</strong> {finding['line']}</p>"""
                
                if 'evidence' in finding:
                    html += f"""
                <p><strong>Evidence:</strong></p>
                <div class="evidence-box">{finding['evidence']}</div>"""
                
                html += """
            </div>"""
            
            html += """
        </div>"""
        
        html += """
    </div>
    
    <h2>Recommendations</h2>
    <ul>
"""
        
        # Add recommendations based on findings
        if data["checks"].get("static_analysis", {}).get("status") == "FAIL":
            html += """
        <li>Address all security issues identified in static code analysis</li>"""
            
        if data["checks"].get("dependency_check", {}).get("status") == "FAIL":
            html += """
        <li>Update vulnerable dependencies to their latest secure versions</li>"""
            
        if data["checks"].get("phi_detection", {}).get("status") == "FAIL":
            html += """
        <li>Remove or sanitize PHI from the codebase</li>
        <li>Implement PHI detection in CI/CD pipeline</li>"""
            
        if data["checks"].get("api_security", {}).get("status") == "FAIL":
            html += """
        <li>Add proper authentication to all API endpoints</li>
        <li>Implement role-based access control</li>"""
            
        if data["checks"].get("configuration", {}).get("status") == "FAIL":
            html += """
        <li>Update configuration files with required security settings</li>"""
            
        if data["checks"].get("logging", {}).get("status") == "FAIL":
            html += """
        <li>Implement proper PHI sanitization in all logging statements</li>"""
            
        if data["checks"].get("security_tests", {}).get("status") == "FAIL":
            html += """
        <li>Fix failing security tests</li>"""
            
        if passed:
            html += """
        <li>Continue to maintain high security standards</li>
        <li>Consider implementing regular security scans in CI/CD pipeline</li>"""
        
        html += """
    </ul>
    
    <hr>
    <p>Report generated on {data["date"]} for Novamind Backend HIPAA Security Assessment</p>
</body>
</html>
"""
        
        return html

    def _generate_text_report(self, data: Dict[str, Any]) -> str:
        """Generate text report from report data."""
        passed = data["overall_result"]
        
        report = f"""HIPAA Security Compliance Report
==============================

Generated on: {data["date"]}

Executive Summary
----------------
Overall Result: {'PASS - System meets HIPAA security requirements' if passed else 'FAIL - System does not meet HIPAA security requirements'}
Passing Checks: {data["summary"]["passed_checks"]} / {data["summary"]["total_checks"]} ({data["summary"]["passing_percentage"]}%)

Check Results
------------
"""
        
        # Add check results
        checks = {
            "static_analysis": "Static Code Analysis",
            "dependency_check": "Dependency Vulnerability Check",
            "phi_detection": "PHI Pattern Detection",
            "api_security": "API Security Check",
            "configuration": "Configuration Security Check",
            "logging": "Logging Sanitization Check",
            "security_tests": "Security Tests"
        }
        
        for check_id, check_name in checks.items():
            check_data = data["checks"].get(check_id, {})
            status = check_data.get("status", "SKIPPED")
            findings_count = len(check_data.get("findings", []))
            
            report += f"{check_name}: {status} ({findings_count} finding{'s' if findings_count != 1 else ''})\n"
        
        report += f"""
Detailed Findings
----------------
"""
        
        # Add detailed findings for each check
        for check_id, check_name in checks.items():
            check_data = data["checks"].get(check_id, {})
            findings = check_data.get("findings", [])
            
            if not findings:
                continue
            
            report += f"\n{check_name}\n{'-' * len(check_name)}\n"
            report += f"Found {len(findings)} issue{'s' if len(findings) != 1 else ''}:\n\n"
            
            for i, finding in enumerate(findings, 1):
                report += f"Finding #{i}: {finding.get('file', 'Unknown file')}\n"
                
                if 'line' in finding:
                    report += f"Line: {finding['line']}\n"
                
                report += f"Issue: {finding.get('issue', 'Unknown issue')}\n"
                
                if 'evidence' in finding:
                    report += f"\nEvidence:\n{'-' * 10}\n{finding['evidence']}\n{'-' * 10}\n"
                
                report += f"\n"
        
        report += f"""
Recommendations
--------------
"""
        
        # Add recommendations based on findings
        if data["checks"].get("static_analysis", {}).get("status") == "FAIL":
            report += "- Address all security issues identified in static code analysis\n"
            
        if data["checks"].get("dependency_check", {}).get("status") == "FAIL":
            report += "- Update vulnerable dependencies to their latest secure versions\n"
            
        if data["checks"].get("phi_detection", {}).get("status") == "FAIL":
            report += "- Remove or sanitize PHI from the codebase\n"
            report += "- Implement PHI detection in CI/CD pipeline\n"
            
        if data["checks"].get("api_security", {}).get("status") == "FAIL":
            report += "- Add proper authentication to all API endpoints\n"
            report += "- Implement role-based access control\n"
            
        if data["checks"].get("configuration", {}).get("status") == "FAIL":
            report += "- Update configuration files with required security settings\n"
            
        if data["checks"].get("logging", {}).get("status") == "FAIL":
            report += "- Implement proper PHI sanitization in all logging statements\n"
            
        if data["checks"].get("security_tests", {}).get("status") == "FAIL":
            report += "- Fix failing security tests\n"
            
        if passed:
            report += "- Continue to maintain high security standards\n"
            report += "- Consider implementing regular security scans in CI/CD pipeline\n"
        
        report += f"""
Report generated on {data["date"]} for Novamind Backend HIPAA Security Assessment
"""
        
        return report

    def run_all_checks(self) -> bool:
        """Run all security checks and generate reports."""
        logger.info("Running HIPAA security compliance checks...")
        
        # Run all checks
        self.run_static_analysis()
        self.run_dependency_check()
        self.run_phi_detection()
        self.check_api_security()
        self.check_configuration()
        self.check_logging()
        self.run_security_tests()
        
        # Generate reports
        html_report, json_report = self.generate_reports()
        
        # Determine overall result
        passed = all(result for result in self.results.values() if result is not None)
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info(f"HIPAA Security Compliance - {'PASS' if passed else 'FAIL'}")
        logger.info("=" * 80)
        
        for check_name, result in self.results.items():
            status = "PASS" if result else "FAIL" if result is not None else "SKIPPED"
            logger.info(f"{check_name}: {status}")
        
        logger.info("=" * 80)
        logger.info(f"Reports saved to: {self.report_dir}")
        logger.info(f"HTML Report: {html_report}")
        logger.info(f"JSON Report: {json_report}")
        logger.info("=" * 80)
        
        return passed


def setup_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Unified HIPAA Security Suite")
    
    parser.add_argument("--report-dir", default=DEFAULT_REPORT_DIR, 
                      help=f"Directory to store reports (default: {DEFAULT_REPORT_DIR})")
    parser.add_argument("--skip-static", action="store_true", 
                      help="Skip static code analysis")
    parser.add_argument("--skip-deps", action="store_true", 
                      help="Skip dependency vulnerability checks")
    parser.add_argument("--skip-phi", action="store_true", 
                      help="Skip PHI pattern detection")
    parser.add_argument("--skip-api", action="store_true", 
                      help="Skip API security checks")
    parser.add_argument("--skip-config", action="store_true", 
                      help="Skip configuration validation")
    parser.add_argument("--skip-tests", action="store_true", 
                      help="Skip security tests")
    parser.add_argument("--verbose", action="store_true", 
                      help="Enable verbose output")
    
    return parser.parse_args()


def main() -> int:
    """Main entry point for the script."""
    args = setup_args()
    
    print("=" * 80)
    print("NOVAMIND UNIFIED HIPAA SECURITY SUITE")
    print("=" * 80)
    
    # Create and run security suite
    security_suite = HIPAASecuritySuite(args)
    passed = security_suite.run_all_checks()
    
    # Return exit code based on overall result
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())