#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Tests for PHI in Code Patterns.

This test suite specifically validates PHI detection in common code patterns
where Protected Health Information might be accidentally included.
"""

import pytest
import tempfile
import os
import re
from pathlib import Path
from unittest.mock import patch, mock_open

from app.core.utils.validation import PHIDetector


class TestPHIInCodePatterns:
    """Test suite for PHI detection in common code patterns."""
    
    @pytest.fixture
    def detector(self):
        """Create a PHI detector for testing."""
        return PHIDetector()
    
    def test_phi_in_variable_assignment(self, detector):
        """Test detection of PHI in variable assignments."""
        # Different programming languages and assignment styles
        code_samples = [
            # Python
            'ssn = "123-45-6789"',
            'patient_name = "John Smith"',
            'patient = {"ssn": "123-45-6789", "name": "John Smith"}',
            
            # JavaScript/TypeScript
            'const ssn = "123-45-6789";',
            'let patientName = "John Smith";',
            'var patient = {ssn: "123-45-6789", name: "John Smith"};',
            
            # Java/C#
            'String ssn = "123-45-6789";',
            'Patient patient = new Patient("John Smith", "123-45-6789");',
            
            # SQL
            "INSERT INTO patients (name, ssn) VALUES ('John Smith', '123-45-6789')",
            "UPDATE patients SET ssn = '123-45-6789' WHERE id = 123"
        ]
        
        # Verify PHI is detected in all samples
        for code in code_samples:
            assert detector.contains_phi(code), f"Failed to detect PHI in: {code}"
    
    def test_phi_in_function_calls(self, detector):
        """Test detection of PHI in function and method calls."""
        code_samples = [
            # Direct function calls
            'process_patient("John Smith", "123-45-6789")',
            'validate_ssn("123-45-6789")',
            
            # Method calls
            'patient.set_ssn("123-45-6789")',
            'patient.update({"name": "John Smith", "ssn": "123-45-6789"})',
            
            # Chained calls
            'db.patients.find_one({"ssn": "123-45-6789"}).update()',
            'get_patient("John Smith").set_ssn("123-45-6789").save()'
        ]
        
        # Verify PHI is detected in all samples
        for code in code_samples:
            assert detector.contains_phi(code), f"Failed to detect PHI in: {code}"
    
    def test_phi_in_config_files(self, detector):
        """Test detection of PHI in configuration patterns."""
        config_samples = [
            # JSON configs
            '{"api": {"test_ssn": "123-45-6789", "test_user": "John Smith"}}',
            
            # YAML-like configs
            """
            database:
              test_credentials:
                username: admin
                password: password123
              test_data:
                patient_ssn: 123-45-6789
                patient_name: John Smith
            """,
            
            # INI-like configs
            """
            [test_data]
            patient_ssn = 123-45-6789
            patient_name = John Smith
            """,
            
            # Environment vars
            'TEST_PATIENT_SSN=123-45-6789',
            'export TEST_PATIENT_NAME="John Smith"'
        ]
        
        # Verify PHI is detected in all samples
        for config in config_samples:
            assert detector.contains_phi(config), f"Failed to detect PHI in config: {config}"
    
    def test_phi_in_api_examples(self, detector):
        """Test detection of PHI in API examples and documentation."""
        api_samples = [
            # JSON API request example
            """
            // Example request
            POST /api/patients
            {
                "name": "John Smith",
                "ssn": "123-45-6789",
                "dob": "01/02/1980"
            }
            """,
            
            # API response example
            """
            // Example response
            {
                "id": "PT12345",
                "name": "John Smith",
                "ssn": "123-45-6789",
                "dob": "01/02/1980"
            }
            """,
            
            # Swagger/OpenAPI example
            """
            paths:
              /patients:
                post:
                  requestBody:
                    content:
                      application/json:
                        example:
                          name: John Smith
                          ssn: 123-45-6789
            """
        ]
        
        # Verify PHI is detected in all samples
        for api_doc in api_samples:
            assert detector.contains_phi(api_doc), f"Failed to detect PHI in API example: {api_doc}"
    
    def test_phi_in_test_cases(self, detector):
        """Test detection of PHI in test cases and fixtures."""
        test_samples = [
            # Python pytest test
            """
            def test_process_patient():
                patient = {
                    "name": "John Smith",
                    "ssn": "123-45-6789"
                }
                result = process_patient(patient)
                assert result.status == "success"
            """,
            
            # JavaScript/Jest test
            """
            test('processes patient correctly', () => {
                const patient = {
                    name: 'John Smith',
                    ssn: '123-45-6789'
                };
                const result = processPatient(patient);
                expect(result.status).toBe('success');
            });
            """,
            
            # Test fixture
            """
            @pytest.fixture
            def test_patient_data():
                return {
                    "name": "John Smith",
                    "ssn": "123-45-6789",
                    "medical_records": [...]
                }
            """
        ]
        
        # Verify PHI is detected in all samples
        for test_code in test_samples:
            assert detector.contains_phi(test_code), f"Failed to detect PHI in test: {test_code}"
    
    def test_phi_in_logs_and_errors(self, detector):
        """Test detection of PHI in logging statements and error messages."""
        log_samples = [
            # Python logging
            'logger.info(f"Processing patient {patient_name} with SSN {ssn}")',
            'logger.error(f"Failed to find patient with SSN: 123-45-6789")',
            
            # JavaScript console logs
            'console.log(`Processing patient ${name} with SSN ${ssn}`);',
            'console.error("Failed to process patient John Smith with SSN 123-45-6789");',
            
            # Error messages
            'raise ValueError(f"Invalid SSN format: {ssn}")',
            'throw new Error(`Patient not found: ${patientName} (SSN: ${ssn})");'
        ]
        
        # Verify PHI is detected in all samples
        for log in log_samples:
            assert detector.contains_phi(log), f"Failed to detect PHI in log: {log}"
    
    def test_phi_in_comments(self, detector):
        """Test detection of PHI in code comments."""
        comment_samples = [
            # Single line comments
            '# TODO: Remove test patient John Smith with SSN 123-45-6789',
            '// FIXME: Need to validate SSN format (123-45-6789)',
            
            # Multi-line comments
            """
            /*
             * Test data:
             * Patient: John Smith
             * SSN: 123-45-6789
             */
            """,
            
            # Documentation comments
            """
            /**
             * Processes a patient record
             * @example
             * // Example usage:
             * processPatient({
             *   name: 'John Smith',
             *   ssn: '123-45-6789'
             * });
             */
            """
        ]
        
        # Verify PHI is detected in all samples
        for comment in comment_samples:
            assert detector.contains_phi(comment), f"Failed to detect PHI in comment: {comment}"
    
    def test_phi_in_complex_code(self, detector):
        """Test detection of PHI in more complex, realistic code samples."""
        complex_code = """
        def process_patient_data(patient_data):
            """Process patient data and store in database.
            
            Example:
                process_patient_data({
                    'name': 'John Smith',
                    'ssn': '123-45-6789',
                    'dob': '01/02/1980'
                })
            """
            # Validate SSN format
            if not is_valid_ssn(patient_data.get('ssn')):
                # Example of invalid SSN: 123-456-7890 (too many digits)
                logger.error(f"Invalid SSN format for patient: {patient_data.get('name')}")
                raise ValueError(f"Invalid SSN: {patient_data.get('ssn')}")
                
            # Process patient data
            try:
                # TODO: Remove hardcoded test data before production
                if patient_data.get('ssn') == '123-45-6789':
                    # This is our test patient (John Smith)
                    return {'status': 'success', 'test_mode': True}
                    
                result = db.patients.insert_one({
                    'name': patient_data.get('name'),
                    'ssn_hash': hash_ssn(patient_data.get('ssn')),
                    'dob': patient_data.get('dob')
                })
                
                return {'status': 'success', 'id': str(result.inserted_id)}
            except Exception as e:
                # Try with backup database
                # Example: If inserting patient John Smith (SSN: 123-45-6789) fails
                logger.error(f"Database error: {str(e)}")
                return {'status': 'error', 'message': str(e)}
        """
        
        # Verify PHI is detected in complex code
        assert detector.contains_phi(complex_code)
        
        # Verify specific PHI instances are detected
        matches = detector.detect_phi(complex_code)
        ssn_matches = [m for m in matches if m.phi_type == "SSN"]
        name_matches = [m for m in matches if m.phi_type == "NAME"]
        
        assert len(ssn_matches) >= 4  # At least 4 instances of SSN
        assert len(name_matches) >= 3  # At least 3 instances of name
    
    def test_phi_in_multiline_strings(self, detector):
        """Test detection of PHI in multiline strings and text blocks."""
        multiline_samples = [
            # Python triple-quoted strings
            '''"""
            Patient Information:
            Name: John Smith
            SSN: 123-45-6789
            DOB: 01/02/1980
            """''',
            
            # JavaScript template literals
            '''`
            Patient Information:
            Name: John Smith
            SSN: 123-45-6789
            DOB: 01/02/1980
            `''',
            
            # Markdown/documentation samples
            '''```
            # Patient Example
            
            | Field | Value         |
            |-------|---------------|
            | Name  | John Smith    |
            | SSN   | 123-45-6789   |
            | DOB   | 01/02/1980    |
            ```'''
        ]
        
        # Verify PHI is detected in all samples
        for multiline in multiline_samples:
            assert detector.contains_phi(multiline), f"Failed to detect PHI in multiline string: {multiline}"
    
    def test_phi_in_html_templates(self, detector):
        """Test detection of PHI in HTML templates."""
        html_samples = [
            # Basic HTML
            """
            <div class="patient-info">
                <h2>Patient Information</h2>
                <p>Name: John Smith</p>
                <p>SSN: 123-45-6789</p>
            </div>
            """,
            
            # JSX/React
            """
            function PatientCard() {
                return (
                    <div className="patient-card">
                        <h3>{patient.name || 'John Smith'}</h3>
                        <p>SSN: {patient.ssn || '123-45-6789'}</p>
                    </div>
                );
            }
            """,
            
            # Template with variables
            """
            <template>
                <div class="patient-info">
                    <h2>{{ patient.name || 'John Smith' }}</h2>
                    <p>SSN: {{ patient.ssn || '123-45-6789' }}</p>
                </div>
            </template>
            """
        ]
        
        # Verify PHI is detected in all samples
        for html in html_samples:
            assert detector.contains_phi(html), f"Failed to detect PHI in HTML: {html}"
    
    def test_phi_in_database_queries(self, detector):
        """Test detection of PHI in database queries and ORM operations."""
        query_samples = [
            # SQL queries
            "SELECT * FROM patients WHERE ssn = '123-45-6789'",
            "INSERT INTO patients (name, ssn) VALUES ('John Smith', '123-45-6789')",
            
            # MongoDB/NoSQL queries
            """
            db.patients.find({
                'ssn': '123-45-6789',
                'name': 'John Smith'
            })
            """,
            
            # ORM operations
            """
            Patient.objects.filter(ssn='123-45-6789', name='John Smith').first()
            """,
            
            # SQLAlchemy
            """
            session.query(Patient).filter(
                Patient.ssn == '123-45-6789',
                Patient.name == 'John Smith'
            ).first()
            """
        ]
        
        # Verify PHI is detected in all samples
        for query in query_samples:
            assert detector.contains_phi(query), f"Failed to detect PHI in query: {query}"


class TestPHIInSourceFiles:
    """Test PHI detection in various file types."""
    
    @pytest.fixture
    def detector(self):
        """Create a PHI detector for testing."""
        return PHIDetector()
    
    def _create_temp_file(self, content, extension=".py"):
        """Helper to create a temporary file with given content."""
        fd, path = tempfile.mkstemp(suffix=extension)
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(content)
            return path
        except Exception:
            os.unlink(path)
            raise
    
    def test_python_file_with_phi(self, detector):
        """Test detection of PHI in Python source files."""
        python_code = """
        #!/usr/bin/env python3
        # Test file with PHI data
        
        def get_test_patient():
            \"\"\"Return test patient data.\"\"\"
            return {
                "name": "John Smith",
                "ssn": "123-45-6789",
                "dob": "01/02/1980"
            }
        
        # TODO: Remove hardcoded SSN before production
        DEFAULT_SSN = "123-45-6789"
        
        class Patient:
            def __init__(self, name="John Smith", ssn="123-45-6789"):
                self.name = name
                self.ssn = ssn
        
        if __name__ == "__main__":
            # Test code
            patient = Patient()
            print(f"Patient: {patient.name}, SSN: {patient.ssn}")
        """
        
        path = self._create_temp_file(python_code)
        try:
            # Read the file
            with open(path, 'r') as f:
                file_content = f.read()
            
            # Verify PHI is detected
            assert detector.contains_phi(file_content)
            
            # Check specific patterns
            matches = detector.detect_phi(file_content)
            ssn_matches = [m for m in matches if m.phi_type == "SSN"]
            name_matches = [m for m in matches if m.phi_type == "NAME"]
            
            assert len(ssn_matches) >= 4  # At least 4 instances of SSN
            assert len(name_matches) >= 3  # At least 3 instances of name
        finally:
            # Clean up
            os.unlink(path)
    
    def test_js_file_with_phi(self, detector):
        """Test detection of PHI in JavaScript source files."""
        js_code = """
        // Test file with PHI data
        
        function getTestPatient() {
            /**
             * Return test patient data
             * @returns {Object} Patient data
             */
            return {
                name: "John Smith",
                ssn: "123-45-6789",
                dob: "01/02/1980"
            };
        }
        
        // TODO: Remove hardcoded SSN before production
        const DEFAULT_SSN = "123-45-6789";
        
        class Patient {
            constructor(name = "John Smith", ssn = "123-45-6789") {
                this.name = name;
                this.ssn = ssn;
            }
        }
        
        // Test code
        const patient = new Patient();
        console.log(`Patient: ${patient.name}, SSN: ${patient.ssn}`);
        """
        
        path = self._create_temp_file(js_code, ".js")
        try:
            # Read the file
            with open(path, 'r') as f:
                file_content = f.read()
            
            # Verify PHI is detected
            assert detector.contains_phi(file_content)
            
            # Check specific patterns
            matches = detector.detect_phi(file_content)
            ssn_matches = [m for m in matches if m.phi_type == "SSN"]
            name_matches = [m for m in matches if m.phi_type == "NAME"]
            
            assert len(ssn_matches) >= 4  # At least 4 instances of SSN
            assert len(name_matches) >= 3  # At least 3 instances of name
        finally:
            # Clean up
            os.unlink(path)
    
    def test_config_file_with_phi(self, detector):
        """Test detection of PHI in configuration files."""
        config_content = """
        # Test configuration file
        
        [app]
        name = "Patient Portal"
        version = "1.0.0"
        
        [database]
        host = "localhost"
        port = 5432
        username = "admin"
        password = "password123"
        
        [test_data]
        # Test patient data
        patient_name = "John Smith"
        patient_ssn = "123-45-6789"
        patient_dob = "01/02/1980"
        
        [logging]
        level = "INFO"
        file = "app.log"
        """
        
        path = self._create_temp_file(config_content, ".ini")
        try:
            # Read the file
            with open(path, 'r') as f:
                file_content = f.read()
            
            # Verify PHI is detected
            assert detector.contains_phi(file_content)
            
            # Check specific patterns
            matches = detector.detect_phi(file_content)
            ssn_matches = [m for m in matches if m.phi_type == "SSN"]
            name_matches = [m for m in matches if m.phi_type == "NAME"]
            
            assert len(ssn_matches) >= 1  # At least 1 instance of SSN
            assert len(name_matches) >= 1  # At least 1 instance of name
        finally:
            # Clean up
            os.unlink(path)


if __name__ == "__main__":
    pytest.main(["-v", __file__])