"""
Test fixtures for encryption tests.

These provide consistent test data for encryption and field encryption tests
following HIPAA Security Rule requirements.
"""

# Test fixture for sensitive data tests
TEST_SENSITIVE_DATA = {
    "patient_id": "12345",
    "name": "John Smith",
    "ssn": "123-45-6789",
    "address": "123 Main St, Anytown, USA",
    "date_of_birth": "1980-01-01",
    "diagnosis": "F41.1",
    "medication": "Sertraline 50mg",
    "notes": "Patient reports improved mood following therapy sessions."
}

# String to use for address field tests
ADDRESS_TEST_STR = "v1:encrypted_address_for_test_123"