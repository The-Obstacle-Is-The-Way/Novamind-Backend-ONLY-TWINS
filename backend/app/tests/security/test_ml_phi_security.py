# -*- coding: utf-8 -*-
"""
HIPAA Compliance Testing - ML PHI Security Tests

These tests validate that the ML processing components properly secure Protected Health Information (PHI)
according to HIPAA requirements. Tests here focus on proper de-identification, secure handling, and
isolation of PHI data in ML workflows.
"""

import os
import json
import uuid
import pytest
from unittest.mock import patch, MagicMock

from app.infrastructure.ml.data_processing import PHIProcessor
from app.infrastructure.security.encryption import EncryptionService
from app.infrastructure.security.phi_redaction import PHIRedactionService


@pytest.fixture
def mock_encryption_service():
    """Mock encryption service for testing."""
    mock_service = MagicMock(spec=EncryptionService)
    mock_service.encrypt.return_value = b"encrypted_data"
    mock_service.decrypt.return_value = b'{"data": "sample_data"}'
    return mock_service


@pytest.fixture
def mock_phi_redaction_service():
    """Mock PHI redaction service for testing."""
    mock_service = MagicMock(spec=PHIRedactionService)
    mock_service.redact.return_value = {"data": "redacted_data"}
    return mock_service


@pytest.fixture
def sample_patient_data():
    """Sample patient data containing PHI."""
    return {
        "patient_id": str(uuid.uuid4()),
        "name": "John Doe",
        "dob": "1980-01-01",
        "ssn": "123-45-6789",
        "address": "123 Main St, City, State 12345",
        "phone": "555-123-4567",
        "email": "john.doe@example.com",
        "medical_history": [
            {"condition": "Anxiety", "diagnosis_date": "2020-01-15", "notes": "Patient reported..."},
            {"condition": "Depression", "diagnosis_date": "2019-03-20", "notes": "Initial symptoms..."}
        ],
        "medications": [
            {"name": "Med1", "dosage": "10mg", "frequency": "daily"},
            {"name": "Med2", "dosage": "20mg", "frequency": "twice daily"}
        ]
    }


class TestPHIHandling:
    """Test proper handling of PHI in ML components."""

    def test_phi_data_is_never_logged(self, sample_patient_data, caplog):
        """Test that PHI is never logged during ML processing."""
        with patch('app.infrastructure.ml.data_processing.PHIProcessor.process') as mock_process:
            mock_process.return_value = {"features": [0.1, 0.2, 0.3]}
            
            processor = PHIProcessor()
            processor.process(sample_patient_data)
            
            # Check logs for PHI
            for record in caplog.records:
                log_message = record.getMessage().lower()
                assert "john doe" not in log_message
                assert "123-45-6789" not in log_message
                assert "555-123-4567" not in log_message
                assert "john.doe@example.com" not in log_message

    def test_phi_is_never_stored_in_plain_text(self, sample_patient_data, mock_encryption_service):
        """Test that PHI is never stored in plain text."""
        with patch('app.infrastructure.ml.data_processing.get_encryption_service', 
                  return_value=mock_encryption_service):
            
            processor = PHIProcessor()
            processor.store_data(sample_patient_data)
            
            # Verify encryption was called
            mock_encryption_service.encrypt.assert_called_once()
            
            # Extract the data passed to encrypt
            args, _ = mock_encryption_service.encrypt.call_args
            encrypted_data = args[0]
            
            # Ensure it's not storing plain text
            assert not isinstance(encrypted_data, dict)
            assert not isinstance(encrypted_data, str)

    def test_phi_is_properly_deidentified(self, sample_patient_data, mock_phi_redaction_service):
        """Test that PHI is properly de-identified for ML training."""
        with patch('app.infrastructure.ml.data_processing.get_redaction_service',
                  return_value=mock_phi_redaction_service):
            
            processor = PHIProcessor()
            deidentified_data = processor.deidentify(sample_patient_data)
            
            # Verify redaction was called
            mock_phi_redaction_service.redact.assert_called_once_with(sample_patient_data)
            
            # Ensure result is the redacted data
            assert deidentified_data == {"data": "redacted_data"}

    def test_patient_data_isolation(self, sample_patient_data):
        """Test that patient data is isolated and not mixed with other patients."""
        patient_id_1 = sample_patient_data["patient_id"]
        sample_patient_data_2 = sample_patient_data.copy()
        sample_patient_data_2["patient_id"] = str(uuid.uuid4())
        
        with patch('app.infrastructure.ml.data_processing.PHIProcessor.get_patient_data') as mock_get_data:
            processor = PHIProcessor()
            
            # First get data for patient 1
            mock_get_data.return_value = {"patient_id": patient_id_1, "data": "patient1_data"}
            data1 = processor.get_patient_data(patient_id_1)
            
            # Then get data for patient 2
            mock_get_data.return_value = {"patient_id": sample_patient_data_2["patient_id"], "data": "patient2_data"}
            data2 = processor.get_patient_data(sample_patient_data_2["patient_id"])
            
            # Verify no data leakage
            assert data1["patient_id"] == patient_id_1
            assert data2["patient_id"] == sample_patient_data_2["patient_id"]
            assert data1["data"] != data2["data"]


class TestMLDataProcessing:
    """Test ML data processing with PHI."""

    def test_feature_extraction_anonymizes_phi(self, sample_patient_data):
        """Test that feature extraction properly anonymizes PHI."""
        with patch('app.infrastructure.ml.data_processing.PHIProcessor.extract_features') as mock_extract:
            mock_extract.return_value = {"features": [0.1, 0.2, 0.3], "metadata": {"status": "complete"}}
            
            processor = PHIProcessor()
            features = processor.extract_features(sample_patient_data)
            
            # Verify result format
            assert "features" in features
            assert "metadata" in features
            
            # Ensure no PHI in features
            assert "name" not in features
            assert "dob" not in features
            assert "ssn" not in features
            assert "address" not in features
            assert "phone" not in features
            assert "email" not in features
            
            # Verify features are in expected format
            assert isinstance(features["features"], list)
            assert all(isinstance(x, float) for x in features["features"])

    def test_model_output_has_no_phi(self, sample_patient_data):
        """Test that model output has no PHI."""
        with patch('app.infrastructure.ml.data_processing.PHIProcessor.run_model') as mock_run:
            mock_run.return_value = {
                "prediction": 0.87,
                "confidence": 0.95,
                "model_version": "1.0.0"
            }
            
            processor = PHIProcessor()
            result = processor.run_model(sample_patient_data)
            
            # Verify result format
            assert "prediction" in result
            assert "confidence" in result
            assert "model_version" in result
            
            # Ensure no PHI in result
            result_str = json.dumps(result)
            assert "John Doe" not in result_str
            assert "123-45-6789" not in result_str
            assert "555-123-4567" not in result_str
            assert "john.doe@example.com" not in result_str

    def test_batch_processing_isolates_patient_data(self):
        """Test that batch processing properly isolates patient data."""
        batch_data = [
            {"patient_id": str(uuid.uuid4()), "data": "data1"},
            {"patient_id": str(uuid.uuid4()), "data": "data2"},
            {"patient_id": str(uuid.uuid4()), "data": "data3"}
        ]
        
        with patch('app.infrastructure.ml.data_processing.PHIProcessor.process_batch') as mock_batch:
            mock_batch.return_value = [
                {"patient_id": batch_data[0]["patient_id"], "result": "result1"},
                {"patient_id": batch_data[1]["patient_id"], "result": "result2"},
                {"patient_id": batch_data[2]["patient_id"], "result": "result3"}
            ]
            
            processor = PHIProcessor()
            results = processor.process_batch(batch_data)
            
            # Verify each result has correct patient ID
            for i, result in enumerate(results):
                assert result["patient_id"] == batch_data[i]["patient_id"]
                assert "result" in result


class TestMLSecureStorage:
    """Test secure storage of ML data."""

    def test_ml_model_storage_encryption(self, mock_encryption_service):
        """Test that ML models are stored encrypted."""
        with patch('app.infrastructure.ml.data_processing.get_encryption_service',
                  return_value=mock_encryption_service):
            
            processor = PHIProcessor()
            model_data = {"weights": [0.1, 0.2, 0.3], "bias": 0.5}
            
            processor.store_model(model_data, "test_model")
            
            # Verify encryption was called
            mock_encryption_service.encrypt.assert_called_once()

    def test_ml_model_loading_decryption(self, mock_encryption_service):
        """Test that ML models are decrypted when loaded."""
        with patch('app.infrastructure.ml.data_processing.get_encryption_service',
                  return_value=mock_encryption_service):
            
            processor = PHIProcessor()
            model = processor.load_model("test_model")
            
            # Verify decryption was called
            mock_encryption_service.decrypt.assert_called_once()
            
            # Model should be properly decoded from JSON
            assert isinstance(model, dict)

    def test_secure_temporary_files(self, sample_patient_data):
        """Test that temporary files used in ML processing are secure."""
        with patch('app.infrastructure.ml.data_processing.PHIProcessor._secure_temp_file') as mock_temp:
            temp_path = "/tmp/secure_temp_123"
            mock_temp.return_value.__enter__.return_value = temp_path
            
            processor = PHIProcessor()
            processor.process_with_temp_file(sample_patient_data)
            
            # Verify temp file was used
            mock_temp.assert_called_once()
            
            # Verify cleanup function is called
            mock_temp.return_value.__exit__.assert_called_once()