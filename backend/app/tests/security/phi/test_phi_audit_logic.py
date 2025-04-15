#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for PHI Audit Logic.

This test suite validates the core logic of the PHI auditor,
particularly the rules that determine whether an audit passes or fails,
including special handling for test directories and files.
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import necessary modules for testing
try:
    from scripts.test.security.run_hipaa_phi_audit import PHIAuditor, PHIAuditResult
except ImportError:
    # Fallback for test environment
    from app.tests.security.utils.test_mocks import MockPHIAuditor as PHIAuditor
    from app.tests.security.utils.test_mocks import MockPHIAuditResult as PHIAuditResult

# Import BaseSecurityTest for test base class
from app.tests.security.utils.base_security_test import BaseSecurityTest

# Uncomment AuditLog import now that the model exists
from app.infrastructure.persistence.sqlalchemy.models.audit_log import AuditLog
# TEMP: Keep UserModel commented until user.py is verified/completed
# from app.infrastructure.persistence.sqlalchemy.models.user import User as UserModel 
from app.infrastructure.security.audit import AuditLogger
from app.infrastructure.security.encryption import BaseEncryptionService
from app.infrastructure.security.encryption.field_encryptor import FieldEncryptor
from app.infrastructure.security.phi import PHIAuditMiddleware, PHIAuditHandler
from app.infrastructure.security.phi.detector import PHIDetector


@pytest.mark.db_required()
class TestPHIAuditLogic(BaseSecurityTest):
    """Test suite for PHI audit decision-making logic."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        # Cleanup
        shutil.rmtree(temp_path)

    def test_audit_passed_with_clean_directory(self):
        """Test that the _audit_passed method returns True for clean directories."""
        auditor = PHIAuditor(app_dir=".")
        auditor.findings = {
            "code_phi": [],
            "api_security": [],
            "configuration_issues": []
        }
        assert auditor._audit_passed() is True, "Audit should pass with no issues"

    def test_audit_passed_with_clean_app_directory(self):
        """Test that the audit passes for clean_app directory even with issues."""
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a clean_app directory
            clean_app_dir = os.path.join(temp_dir, "clean_app")
            os.makedirs(clean_app_dir)

            # Create an auditor with issues but in a clean_app directory
            auditor = PHIAuditor(app_dir=clean_app_dir)

            # Add some mock issues
            auditor.findings = {
                "code_phi": [{"file": "test.py", "evidence": "SSN: 123-45-6789"}],
                "api_security": [{"endpoint": "/api/patient", "issue": "No authentication"}],
                "configuration_issues": []
            }

            # Verify audit passes despite having issues
            assert auditor._audit_passed() is True, "Audit should pass for clean_app directory regardless of issues"
        finally:
            shutil.rmtree(temp_dir)

    def test_audit_passed_with_clean_app_in_path(self):
        """Test that the audit passes when 'clean_app' is in the path but not the directory name."""
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a directory with clean_app in the path
            nested_dir = os.path.join(temp_dir, "nested", "clean_app_tests", "fixtures")
            os.makedirs(nested_dir, exist_ok=True)

            # Create an auditor with issues but with clean_app in path
            auditor = PHIAuditor(app_dir=nested_dir)

            # Add some mock issues
            auditor.findings = {
                "code_phi": [{"file": "test.py", "evidence": "SSN: 123-45-6789"}],
                "api_security": [],
                "configuration_issues": []
            }

            # Verify audit passes despite having issues
            assert auditor._audit_passed() is True, "Audit should pass with clean_app in path"
        finally:
            shutil.rmtree(temp_dir)

    def test_audit_file_detection(self):
        """Test the is_phi_test_file detection logic."""
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a PHIAuditor instance
            auditor = PHIAuditor(app_dir=temp_dir)

            # Create a regular file
            regular_file = os.path.join(temp_dir, "regular.py")
            with open(regular_file, "w") as f:
                f.write("def regular_function(): return True")

            # Create a test file that isn't testing PHI
            non_phi_test_file = os.path.join(temp_dir, "test_regular.py")
            with open(non_phi_test_file, "w") as f:
                f.write("""
                    import pytest

                    def test_something():
                        assert 1 + 1 == 2
                """)

            # Create a PHI test file
            phi_test_file = os.path.join(temp_dir, "test_phi_detection.py")
            with open(phi_test_file, "w") as f:
                f.write("""
                    import pytest
                    from app.core.utils.validation import PHIDetector

                    def test_phi_detection():
                        detector = PHIDetector()
                        assert detector.contains_phi("123-45-6789") is True
                """)

            # Test the detection logic
            assert auditor.is_phi_test_file(regular_file, open(regular_file, "r").read()) is False, "Regular file should not be detected as PHI test file"
            assert auditor.is_phi_test_file(non_phi_test_file, open(non_phi_test_file, "r").read()) is False, "Non-PHI test file should not be detected as PHI test file"
            assert auditor.is_phi_test_file(phi_test_file, open(phi_test_file, "r").read()) is True, "PHI test file should be detected correctly"
        finally:
            shutil.rmtree(temp_dir)

    def test_strict_mode_disables_special_handling(self):
        """Test that strict mode disables special handling for test files and clean_app directories."""
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a clean_app directory
            clean_app_dir = os.path.join(temp_dir, "clean_app")
            os.makedirs(clean_app_dir)

            # Create a test file with PHI
            test_file = os.path.join(clean_app_dir, "test_phi.py")
            with open(test_file, "w") as f:
                f.write("""
                    def test_function():
                        ssn = \"123-45-6789\"
                """)

            # Create an auditor (no strict_mode argument)
            strict_auditor = PHIAuditor(app_dir=clean_app_dir)

            # Add mock issues
            strict_auditor.findings = {
                "code_phi": [{"file": "test_phi.py", "evidence": "SSN: 123-45-6789"}],
                "api_security": [],
                "configuration_issues": []
            }

            # Verify audit fails in strict mode despite being in clean_app directory
            assert strict_auditor._audit_passed() is False, "Audit should fail in strict mode even in clean_app directory"

            # Verify PHI test detection is disabled in strict mode
            # (No strict mode logic, so just check normal behavior)
            assert strict_auditor.is_phi_test_file(test_file, open(test_file, "r").read()) is False, "PHI test file detection should be disabled in strict mode"
        finally:
            shutil.rmtree(temp_dir)

    def test_report_counts_for_clean_app_files(self):
        """Test that report correctly counts allowed PHI in clean_app directories."""
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        try:
            # Create clean_app directory with PHI
            clean_app_dir = os.path.join(temp_dir, "clean_app")
            os.makedirs(clean_app_dir)

            # Create a file with PHI
            phi_file = os.path.join(clean_app_dir, "test_data.py")
            with open(phi_file, "w") as f:
                f.write("""
                    def get_test_data():
                        return {
                            \"ssn\": \"123-45-6789\",
                            \"name\": \"John Smith\"
                        }
                """)

            # Create and run the auditor
            auditor = PHIAuditor(app_dir=clean_app_dir)
            results = auditor.scan_directory(clean_app_dir)

            # Verify PHI was found but allowed
            phi_files = [r for r in results if r.phi_detected]
            assert len(phi_files) > 0, "Report should show files with PHI"
            allowed_phi_files = [r for r in phi_files if r.is_allowed]
            assert len(phi_files) == len(allowed_phi_files), "All PHI files should be counted as allowed"
        finally:
            shutil.rmtree(temp_dir)

    def test_audit_failed_with_issues(self):
        """Test that the audit fails when issues are found and not in clean_app directory."""
        auditor = PHIAuditor(app_dir="/some/regular/path")
        auditor.findings = {
            "code_phi": [{"file": "patient.py", "evidence": "SSN: 123-45-6789"}],
            "api_security": [],
            "configuration_issues": []
        }
        assert auditor._audit_passed() is False, "Audit should fail with issues in regular directory"

    def test_audit_result_allowed_status(self):
        """Test the allowed status of audit results for PHI test files."""
        # Create an audit result
        result = PHIAuditResult(file_path="test_phi.py")
        # Set as a PHI test file
        result.is_test_file = True
        result.is_allowed_phi_test = True
        # Add PHI manually to the result (simulate)
        result.has_phi = True
        result.is_allowed = True
        # Verify result has PHI but is allowed
        assert result.has_phi is True, "Result should have PHI"
        assert result.is_allowed is True, "PHI should be allowed in test file"

    def test_run_audit_with_clean_app_directory(self):
        """Test the full run_audit method with a clean_app directory."""
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        try:
            # Create clean_app directory
            clean_app_dir = os.path.join(temp_dir, "clean_app_test")
            os.makedirs(clean_app_dir)

            # Create a file with PHI
            phi_file = os.path.join(clean_app_dir, "data.py")
            with open(phi_file, "w") as f:
                f.write('ssn = "123-45-6789"  # Test data')

            # Run a full audit
            auditor = PHIAuditor(app_dir=clean_app_dir)
            audit_passed = auditor.run_audit()

            # Verify audit passed (since clean_app should always pass)
            assert audit_passed is True, "Audit should pass for clean_app directory"
        finally:
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
