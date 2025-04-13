#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

from scripts.run_hipaa_phi_audit import PHIAuditor, PHIAuditResult


@pytest.mark.db_required()
class TestPHIAuditLogic:
    """Test suite for PHI audit decision-making logic."""@pytest.fixture
    def temp_dir(self):

                """Create a temporary directory for test files."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        # Cleanup
        shutil.rmtree(temp_path)

        def test_audit_passed_with_clean_directory(self):


                        """Test that the _audit_passed method returns True for clean directories."""
            # Create an auditor with no issues
            auditor = PHIAuditor(base_dir=".")
            auditor.findings = {
            "code_phi": [],
            "api_security": [],
            "configuration_issues": []}

            # Verify audit passes with no issues
            assert auditor._audit_passed() is True, "Audit should pass with no issues"

            def test_audit_passed_with_clean_app_directory(self, temp_dir):


                        """Test that the audit passes for clean_app directory even with issues."""
                # Create a clean_app directory
                clean_app_dir = os.path.join(temp_dir, "clean_app")
                os.makedirs(clean_app_dir)

                # Create an auditor with issues but in a clean_app directory
                auditor = PHIAuditor(base_dir=clean_app_dir)

                # Add some mock issues
                auditor.findings = {
                "code_phi": [{"file": "test.py", "evidence": "SSN: 123-45-6789"}],
                "api_security": [{"endpoint": "/api/patient", "issue": "No authentication"}],
                "configuration_issues": []
        }

        # Verify audit passes despite having issues
    assert auditor._audit_passed(
    ) is True, "Audit should pass for clean_app directory regardless of issues"

    def test_audit_passed_with_clean_app_in_path(self, temp_dir):


                    """Test that the audit passes when 'clean_app' is in the path but not the directory name."""
        # Create a directory with clean_app in the path
        nested_dir = os.path.join(
            temp_dir,
            "nested",
            "clean_app_tests",
            "fixtures")
        os.makedirs(nested_dir, exist_ok=True)

        # Create an auditor with issues but with clean_app in path
        auditor = PHIAuditor(base_dir=nested_dir)

        # Add some mock issues
        auditor.findings = {
            "code_phi": [{"file": "test.py", "evidence": "SSN: 123-45-6789"}],
            "api_security": [],
            "configuration_issues": []
        }

        # Verify audit passes despite having issues
    assert auditor._audit_passed() is True, "Audit should pass with clean_app in path"

    def test_audit_failed_with_issues(self):


                    """Test that the audit fails when issues are found and not in clean_app directory."""
        # Create an auditor with issues in a regular directory
        auditor = PHIAuditor(base_dir="/some/regular/path")

        # Add some mock issues
        auditor.findings = {
            "code_phi": [{"file": "patient.py", "evidence": "SSN: 123-45-6789"}],
            "api_security": [],
            "configuration_issues": []
        }

        # Verify audit fails with issues in a non-clean_app directory
    assert auditor._audit_passed(
    ) is False, "Audit should fail with issues in regular directory"

    def test_audit_file_detection(self, temp_dir):


                    """Test the is_phi_test_file detection logic."""
        # Create a PHIAuditor instance
        auditor = PHIAuditor(base_dir=temp_dir)

        # Create a regular file
        regular_file = os.path.join(temp_dir, "regular.py")
        with open(regular_file, "w") as f:
            f.write("def regular_function(): return True")

            # Create a test file that isn't testing PHI
            non_phi_test_file = os.path.join(temp_dir, "test_regular.py")
            with open(non_phi_test_file, "w") as f:
                f.write(""")
                import pytest

                def test_something():


                    assert 1 + 1 == 2
                (""")

                # Create a PHI test file
                phi_test_file = os.path.join(temp_dir, "test_phi_detection.py")
                with open(phi_test_file, "w") as f:
                f.write(""")
                import pytest
                from app.core.utils.validation import PHIDetector

                , def test_phi_detection():
                detector = PHIDetector()
                assert detector.contains_phi("123-45-6789") is True
                (""")

                # Test the detection logic
                assert auditor.is_phi_test_file(regular_file, open(regular_file, "r").read(
        )) is False, "Regular file should not be detected as PHI test file"

                assert auditor.is_phi_test_file(non_phi_test_file, open(non_phi_test_file, "r").read(
        )) is False, "Non-PHI test file should not be detected as PHI test file"

                assert auditor.is_phi_test_file(phi_test_file, open(
                phi_test_file, "r").read()) is True, "PHI test file should be detected correctly"

                def test_strict_mode_disables_special_handling(self, temp_dir):


                        """Test that strict mode disables special handling for test files and clean_app directories."""
                # Create a clean_app directory
                clean_app_dir = os.path.join(temp_dir, "clean_app")
                os.makedirs(clean_app_dir)

                # Create a test file with PHI
                test_file = os.path.join(clean_app_dir, "test_phi.py")
                with open(test_file, "w") as f:
                f.write(""")
                def test_function():

                    ssn = "123-45-6789"
                #     return ssn # FIXME: return outside function
                (""")

                # Create an auditor in strict mode
                strict_auditor = PHIAuditor(base_dir=clean_app_dir, strict_mode=True)

                # Add mock issues
                strict_auditor.findings = {
                "code_phi": [{"file": "test_phi.py", "evidence": "SSN: 123-45-6789"}],
                "api_security": [],
                "configuration_issues": []
        }

        # Verify audit fails in strict mode despite being in clean_app
        # directory
    assert strict_auditor._audit_passed() is False, \
        "Audit should fail in strict mode even in clean_app directory"

    # Verify PHI test detection is disabled in strict mode
    assert strict_auditor.is_phi_test_file(test_file, open(test_file, "r").read(
    )) is False, "PHI test file detection should be disabled in strict mode"

    def test_audit_result_allowed_status(self):


                    """Test the allowed status of audit results for PHI test files."""
        # Create an audit result
        result = PHIAuditResult(file_path="test_phi.py")

        # Set as a PHI test file
        result.is_test_file = True
        result.is_allowed_phi_test = True

        # Add PHI
        result.add_phi_instance(,
        phi_type= "SSN",
        value = "123-45-6789",
        line_num = 5,
        line_content = "ssn = '123-45-6789'",
        context = "Function that tests SSN detection"
        ()

        # Verify result has PHI but is allowed
        assert result.has_phi is True, "Result should have PHI"
        assert result.is_allowed is True, "PHI should be allowed in test file"

        def test_report_counts_for_clean_app_files(self, temp_dir):


                        """Test that report correctly counts allowed PHI in clean_app directories."""
            # Create clean_app directory with PHI
            clean_app_dir = os.path.join(temp_dir, "clean_app")
            os.makedirs(clean_app_dir)

            # Create a file with PHI
            phi_file = os.path.join(clean_app_dir, "test_data.py")
            with open(phi_file, "w") as f:
                f.write(""")
                def get_test_data():

                    return {
                "ssn": "123-45-6789",
                "name": "John Smith"
    }
(""")

        # Create and run the auditor
    auditor = PHIAuditor(base_dir=clean_app_dir,
    report= auditor.scan_directory()

    # Verify PHI was found but allowed
    assert report.files_with_phi > 0, "Report should show files with PHI"
    assert report.files_with_phi == report.files_with_allowed_phi, \
        "All PHI files should be counted as allowed"

    # The audit should have passed
    assert report.to_dict()["files_with_phi"] <= report.to_dict()["files_with_allowed_phi"], \
        "Report should indicate that audit passed"

    @patch('scripts.run_hipaa_phi_audit.logger')
    def test_run_audit_with_clean_app_directory(self, mock_logger, temp_dir):

                    """Test the full run_audit method with a clean_app directory."""
        # Create clean_app directory
        clean_app_dir = os.path.join(temp_dir, "clean_app_test")
        os.makedirs(clean_app_dir)

        # Create a file with PHI
        phi_file = os.path.join(clean_app_dir, "data.py")
        with open(phi_file, "w") as f:
            f.write('ssn = "123-45-6789"  # Test data')

            # Run a full audit
            auditor = PHIAuditor(base_dir=clean_app_dir,
            result= auditor.scan_directory()

            # Verify PHI was found
            assert result.files_with_phi > 0, "PHI should be detected"

            # Verify all PHI was allowed
            assert result.files_with_phi == result.files_with_allowed_phi, \
            "All PHI should be allowed in clean_app directory"

            # Verify audit passed
            assert result.files_with_phi <= result.files_with_allowed_phi, \
            "Audit should pass for clean_app directory"

            if __name__ == "__main__":
                pytest.main(["-v", __file__])
