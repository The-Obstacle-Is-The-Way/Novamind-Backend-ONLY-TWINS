# -*- coding: utf-8 -*-
import os
import pytest
import tempfile
from pathlib import Path

from scripts.run_hipaa_phi_audit import PHIAuditor, PHIDetector


@pytest.mark.venv_only
class TestPHIDetection:
    """Test PHI detection capabilities in our HIPAA compliance system."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.detector = PHIDetector()

    def teardown_method(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def create_test_file(self, filename, content):
        """Create a test file with the given content."""
        filepath = self.base_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)
        return filepath

    @pytest.mark.venv_only
def test_ssn_pattern_detection(self):
        """Test detection of various SSN patterns."""
        # Create file with various SSN formats
        content = """
        SSN: 123-45-6789
        SSN with spaces: 123 45 6789
        SSN with quotes: "123-45-6789"
        SSN in code: patient.ssn = "123-45-6789"
        SSN variable: SSN = "123-45-6789"
        """
        filepath = self.create_test_file("test_ssn.py", content)
        
        # Detect PHI in the file
        matches = self.detector.detect_phi(content)
        
        # Verify SSN patterns are detected
        ssn_matches = [m for m in matches if m.phi_type == "SSN"]
        assert len(ssn_matches) >= 5, "Should detect at least 5 SSN patterns"

    @pytest.mark.venv_only
def test_audit_with_clean_app_directory(self):
        """Test that auditor passes with clean_app directory."""
        # Create a test file in a clean_app directory with PHI
        clean_dir = self.base_dir / "clean_app"
        clean_dir.mkdir(parents=True, exist_ok=True)
        test_file = clean_dir / "test_data.py"
        test_file.write_text('SSN = "123-45-6789"')
        
        # Run audit on the clean_app directory
        auditor = PHIAuditor(base_dir=str(clean_dir))
        auditor.audit_code_for_phi()
        
        # Verify audit passes even with PHI present
        assert auditor._audit_passed() is True, "Audit should pass for clean_app directory"

    @pytest.mark.venv_only
def test_phi_in_normal_code(self):
        """Test that PHI is detected in normal code files."""
        # Create a file with PHI but not in a test context
        content = 'user_data = {"name": "John Smith", "ssn": "123-45-6789"}'
        filepath = self.create_test_file("user_data.py", content)
        
        # Run audit on the file
        auditor = PHIAuditor(base_dir=str(self.base_dir))
        auditor.audit_code_for_phi()
        
        # Verify PHI is detected and audit fails
        assert auditor._audit_passed() is False, "Audit should fail for PHI in normal code"
        assert len(auditor.findings["code_phi"]) > 0, "Should find PHI in code"

    @pytest.mark.venv_only
def test_phi_in_test_files(self):
        """Test that PHI in legitimate test files is allowed."""
        # Create a file with PHI in a test context
        content = """
        import pytest
        
        @pytest.mark.venv_only
def test_phi_detection():
            # This is a legitimate test case with PHI for testing detection
            test_ssn = "123-45-6789"
            assert is_valid_ssn(test_ssn)
        """
        filepath = self.create_test_file("test_phi.py", content)
        
        # Run audit on the file
        auditor = PHIAuditor(base_dir=str(self.base_dir))
        auditor.audit_code_for_phi()
        
        # Verify PHI is detected but marked as allowed (test passes)
        results = [r for r in auditor.report.results if r.has_phi]
        assert len(results) > 0, "Should detect PHI in test file"
        assert all(r.is_allowed for r in results), "PHI in test files should be allowed"
        assert auditor._audit_passed() is True, "Audit should pass for legitimate test files"

    @pytest.mark.venv_only
def test_api_endpoint_security(self):
        """Test that unprotected API endpoints are detected."""
        # Create an API file with protected and unprotected endpoints
        content = """
        from fastapi import APIRouter, Depends
        from app.core.auth import get_current_user
        
        router = APIRouter()
        
        @router.get("/protected")
        def protected_endpoint(user = Depends(get_current_user)):
            return {"status": "protected"}
            
        @router.get("/unprotected")
        def unprotected_endpoint():
            return {"status": "unprotected"}
            
        # This endpoint handles patient data but lacks auth
        @router.get("/patient/{patient_id}")
        def get_patient(patient_id: str):
            return {"patient_id": patient_id}
        """
        filepath = self.create_test_file("api_routes.py", content)
        
        # Run API endpoint audit
        auditor = PHIAuditor(base_dir=str(self.base_dir))
        auditor.audit_api_endpoints()
        
        # Verify unprotected endpoints are detected
        assert len(auditor.api_issues) >= 2, "Should detect at least 2 unprotected endpoints"
        patient_endpoints = [i for i in auditor.api_issues if "patient" in i["content"]]
        assert len(patient_endpoints) > 0, "Should detect patient endpoint as unprotected"

    @pytest.mark.venv_only
def test_config_security_classification(self):
        """Test that security settings are properly classified by criticality."""
        # Create a config file missing security settings
        content = """
        # Some settings present
        DEBUG = False
        ALLOWED_HOSTS = ['example.com']
        
        # Missing critical security settings
        """
        filepath = self.create_test_file("settings.py", content)
        
        # Run configuration audit
        auditor = PHIAuditor(base_dir=str(self.base_dir))
        auditor.audit_configuration()
        
        # Verify security settings are classified correctly
        assert len(auditor.config_issues) > 0, "Should detect missing security settings"
        assert "critical_missing" in auditor.config_issues[0], "Should classify critical settings"
        assert "high_priority_missing" in auditor.config_issues[0], "Should classify high priority settings"
        assert "severity" in auditor.config_issues[0], "Should include severity classification"