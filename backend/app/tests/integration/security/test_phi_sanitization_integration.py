# -*- coding: utf-8 -*-
"""
Integration tests for HIPAA-compliant PHI handling across database and logging.

This test suite verifies that:
1. PHI is properly encrypted in the database
2. PHI is sanitized in logs
3. Exception handling never exposes PHI
"""

import pytest
import asyncio
import logging
import uuid
from datetime import date
from typing import List, Dict, Any, Optional
from io import StringIO

from app.domain.entities.patient import Patient
from app.domain.value_objects.address import Address
from app.domain.value_objects.emergency_contact import EmergencyContact
from app.infrastructure.persistence.sqlalchemy.models.patient import PatientModel
from app.infrastructure.persistence.sqlalchemy.config.database import get_db_session
from app.core.utils.phi_sanitizer import PHIDetector, PHISanitizer
# Removed incorrect import
# Import the correct function for getting a sanitized logger
from app.infrastructure.security.log_sanitizer import get_sanitized_logger


@pytest.fixture
@pytest.mark.db_required
async def test_patient() -> Patient:
    """Create a test patient with PHI for testing."""
    patient_id = uuid.uuid4()
    return Patient(
        id=patient_id,
        first_name="Integration",
        last_name="Test",
        date_of_birth=date(1980, 1, 1),
        email="integration.test@example.com",
        phone="555-987-6543",
        address=Address(
            line1="123 Integration St",
            line2="Suite 500",
            city="Testville",
            state="TS",
            postal_code="12345",
            country="Testland"
        ),
        emergency_contact=EmergencyContact(
            name="Emergency Contact",
            phone="555-123-4567",
            relationship="Test Relative"
        ),
        insurance=None,
        active=True,
        created_by=None
    )


@pytest.fixture
def log_capture() -> StringIO:
    """Capture logs for analysis."""
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    
    # Use basic formatter to be able to see actual log content
    handler.setFormatter(logging.Formatter('%(message)s'))
    
    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    # Store original level and set to DEBUG
    original_level = root_logger.level
    root_logger.setLevel(logging.DEBUG)
    
    yield log_stream
    
    # Clean up
    root_logger.removeHandler(handler)
    root_logger.setLevel(original_level)


class TestPHISanitizationIntegration:
    """
    Integration test suite for PHI sanitization across database and logs.
    
    These tests verify that PHI is properly protected throughout the system,
    even when crossing module boundaries and during exception handling.
    """
    
    @pytest.mark.asyncio
    async def test_patient_phi_database_encryption(self, test_patient: Patient):
        """Test that PHI is encrypted in database and decrypted when retrieved."""
        # Convert to model (encrypts PHI)
        patient_model = PatientModel.from_domain(test_patient)
        
        # Save to database
        async with await get_db_session() as session:
            session.add(patient_model)
            await session.commit()
            
            # Get patient ID for later lookup
            patient_id = patient_model.id
            
            # Close session to clear cache
            await session.close()
            
            # Get a new session
            async with await get_db_session() as new_session:
                # Get raw data directly with SQL to verify encryption
                result = await new_session.execute(f"""
                    SELECT first_name, last_name, email, phone 
                    FROM patients WHERE id = '{patient_id}'
                """)
                row = result.fetchone()
                
                # Verify PHI is stored encrypted (raw DB values)
                assert row.first_name != test_patient.first_name, "First name not encrypted in database"
                assert row.email != test_patient.email, "Email not encrypted in database"
                assert row.phone != test_patient.phone, "Phone not encrypted in database"
                
                # Retrieve through ORM and convert back to domain
                db_patient_model = await new_session.get(PatientModel, patient_id)
                retrieved_patient = db_patient_model.to_domain()
                
                # Verify domain entity has decrypted PHI
                assert retrieved_patient.first_name == test_patient.first_name, "First name mismatch"
                assert retrieved_patient.email == test_patient.email, "Email mismatch"
                assert retrieved_patient.phone == test_patient.phone, "Phone mismatch"
                
                # Clean up test data
                await new_session.delete(db_patient_model)
                await new_session.commit()
    
    @pytest.mark.asyncio
    async def test_phi_sanitization_in_logs(self, test_patient: Patient, log_capture: StringIO):
        """Test that PHI is properly sanitized in logs."""
        # Set up logger
        logger = get_sanitized_logger("test.phi.integration") # Use correct function
        
        # Log some PHI
        logger.info(
            f"Processing patient record",
            {
                "patient_id": str(test_patient.id),
                "email": test_patient.email,
                "phone": test_patient.phone,
                "dob": str(test_patient.date_of_birth)
            }
        )
        
        # Get log content
        log_content = log_capture.getvalue()
        
        # Verify PHI is not in logs
        assert test_patient.email not in log_content, "Email found in logs"
        assert test_patient.phone not in log_content, "Phone found in logs"
        assert str(test_patient.date_of_birth) not in log_content, "Date of birth found in logs"
        
        # Verify patient ID (non-PHI) is in logs
        assert str(test_patient.id) in log_content, "Patient ID should be in logs"
    
    @pytest.mark.asyncio
    async def test_phi_sanitization_during_errors(self, test_patient: Patient, log_capture: StringIO):
        """Test that PHI is sanitized even during error handling."""
        # Set up logger
        logger = get_sanitized_logger("test.phi.error") # Use correct function
        
        try:
            # Simulate an error with PHI in the message
            error_message = (
                f"Error processing patient {test_patient.first_name} {test_patient.last_name} "
                f"(DOB: {test_patient.date_of_birth}, Email: {test_patient.email})"
            )
            raise ValueError(error_message)
        except ValueError as e:
            # Log the error
            logger.error(
                f"An error occurred: {str(e)}",
                {
                    "patient_id": str(test_patient.id),
                    "error_details": str(e)
                }
            )
        
        # Get log content
        log_content = log_capture.getvalue()
        
        # Verify PHI is not in logs
        assert test_patient.email not in log_content, "Email found in logs during error"
        assert test_patient.first_name not in log_content, "First name found in logs during error"
        assert test_patient.last_name not in log_content, "Last name found in logs during error"
        assert str(test_patient.date_of_birth) not in log_content, "DOB found in logs during error"
        
        # Verify sanitized placeholders are in logs instead
        assert "ANONYMIZED" in log_content or "REDACTED" in log_content, "No sanitization markers found"
    
    @pytest.mark.asyncio
    async def test_cross_module_phi_protection(self, test_patient: Patient, log_capture: StringIO):
        """Test PHI protection across module boundaries."""
        # This test simulates a full pipeline that processes patient data
        
        # Convert to model (simulating data access layer)
        patient_model = PatientModel.from_domain(test_patient)
        
        # Simulate processing in service layer
        def process_patient_data(model: PatientModel) -> Dict[str, Any]:
            """Simulate processing in another module."""
            logger = get_sanitized_logger("service.patient") # Use correct function
            
            # Log the processing (with PHI that should be sanitized)
            logger.info(
                f"Processing patient: {model.first_name} {model.last_name}",
                {"email": model.email, "phone": model.phone}
            )
            
            # Return processed data
            return {
                "id": model.id,
                "contact_info": f"{model.email} / {model.phone}",
                "full_name": f"{model.first_name} {model.last_name}",
                "status": "processed"
            }
        
        # Process the patient
        processed_data = process_patient_data(patient_model)
        
        # Verify the processed data still contains PHI (no sanitization of actual data)
        assert test_patient.email in processed_data["contact_info"], "Email missing from processed data"
        assert test_patient.phone in processed_data["contact_info"], "Phone missing from processed data"
        assert test_patient.first_name in processed_data["full_name"], "First name missing from processed data"
        
        # Get log content
        log_content = log_capture.getvalue()
        
        # Verify logs do not contain PHI
        assert test_patient.email not in log_content, "Email found in logs during cross-module processing"
        assert test_patient.phone not in log_content, "Phone found in logs during cross-module processing"
        assert test_patient.first_name not in log_content, "First name found in logs during cross-module processing"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])