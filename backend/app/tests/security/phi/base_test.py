"""
Base test class for PHI-related security tests in Novamind Digital Twin Platform.

This class provides specialized fixtures and utilities for testing
PHI detection, redaction, and protection mechanisms.
"""

from typing import Dict, Any, List, Optional
from unittest import mock

from app.tests.security.base_test import BaseSecurityTest


class BasePHITest(BaseSecurityTest):
    """Base class for all PHI-related tests."""
    
    def setUp(self) -> None:
        """Set up PHI test fixtures."""
        super().setUp()
        
        # Initialize test PHI data with synthetic examples
        # None of this is real PHI - just test data
        self.test_phi_data = {
            "name": "John Test Patient",
            "dob": "1980-01-01",
            "ssn": "123-45-6789",
            "mrn": "MRN12345678",
            "address": "123 Test Street, Testville, TS 12345",
            "phone": "(555) 123-4567",
            "email": "test.patient@example.com",
        }
        
        # Setup PHI detection mock
        self.phi_detection_patcher = mock.patch(
            "app.core.services.ml.phi_detection.PHIDetectionService"
        )
        self.mock_phi_detection = self.phi_detection_patcher.start()
        
        # Set up mock behavior for PHI detection
        self.mock_phi_detection.return_value.detect_phi.side_effect = self._mock_detect_phi
        self.mock_phi_detection.return_value.redact_phi.side_effect = self._mock_redact_phi
        
    def tearDown(self) -> None:
        """Tear down PHI test fixtures."""
        # Stop all patchers
        self.phi_detection_patcher.stop()
        
        super().tearDown()
    
    def _mock_detect_phi(self, text: str, 
                       sensitivity: str = "high") -> Dict[str, Any]:
        """Mock PHI detection implementation.
        
        Args:
            text: Text to check for PHI
            sensitivity: Detection sensitivity level
            
        Returns:
            Dictionary with PHI detection results
        """
        detected = {
            "has_phi": False,
            "phi_elements": [],
            "risk_score": 0.0
        }
        
        # Check for name
        if self.test_phi_data["name"] in text:
            detected["has_phi"] = True
            detected["phi_elements"].append({
                "type": "NAME",
                "value": self.test_phi_data["name"],
                "position": (text.find(self.test_phi_data["name"]), 
                             text.find(self.test_phi_data["name"]) + 
                             len(self.test_phi_data["name"])),
                "confidence": 0.98
            })
            detected["risk_score"] += 0.7
        
        # Check for SSN
        if self.test_phi_data["ssn"] in text:
            detected["has_phi"] = True
            detected["phi_elements"].append({
                "type": "SSN",
                "value": self.test_phi_data["ssn"],
                "position": (text.find(self.test_phi_data["ssn"]), 
                             text.find(self.test_phi_data["ssn"]) + 
                             len(self.test_phi_data["ssn"])),
                "confidence": 0.99
            })
            detected["risk_score"] += 0.9
        
        # Check for DOB
        if self.test_phi_data["dob"] in text:
            detected["has_phi"] = True
            detected["phi_elements"].append({
                "type": "DATE",
                "value": self.test_phi_data["dob"],
                "position": (text.find(self.test_phi_data["dob"]), 
                             text.find(self.test_phi_data["dob"]) + 
                             len(self.test_phi_data["dob"])),
                "confidence": 0.95
            })
            detected["risk_score"] += 0.6
            
        # Cap risk score at 1.0
        detected["risk_score"] = min(detected["risk_score"], 1.0)
        
        return detected
    
    def _mock_redact_phi(self, text: str, 
                        replacement: str = "[REDACTED]") -> str:
        """Mock PHI redaction implementation.
        
        Args:
            text: Text to redact PHI from
            replacement: Text to replace PHI with
            
        Returns:
            Redacted text
        """
        redacted = text
        
        # Redact name
        if self.test_phi_data["name"] in redacted:
            redacted = redacted.replace(
                self.test_phi_data["name"], 
                replacement
            )
        
        # Redact SSN
        if self.test_phi_data["ssn"] in redacted:
            redacted = redacted.replace(
                self.test_phi_data["ssn"], 
                replacement
            )
        
        # Redact DOB
        if self.test_phi_data["dob"] in redacted:
            redacted = redacted.replace(
                self.test_phi_data["dob"], 
                replacement
            )
            
        return redacted
    
    def assert_phi_detected(self, result: Dict[str, Any], 
                           expected_types: Optional[List[str]] = None) -> None:
        """Assert that PHI was properly detected.
        
        Args:
            result: PHI detection result
            expected_types: List of expected PHI types
        """
        self.assertTrue(result["has_phi"], "PHI should be detected")
        
        if expected_types:
            detected_types = [element["type"] for element in result["phi_elements"]]
            for expected_type in expected_types:
                self.assertIn(
                    expected_type, 
                    detected_types,
                    f"PHI type {expected_type} should be detected"
                )
                
    def assert_phi_redacted(self, original: str, redacted: str) -> None:
        """Assert that PHI was properly redacted.
        
        Args:
            original: Original text
            redacted: Redacted text
        """
        # Check that the redacted text doesn't contain any test PHI
        for key, value in self.test_phi_data.items():
            self.assertNotIn(
                value, 
                redacted,
                f"PHI {key} should be redacted"
            )
            
        # The redacted text should be different from the original
        if any(value in original for value in self.test_phi_data.values()):
            self.assertNotEqual(original, redacted, "Text should be redacted")