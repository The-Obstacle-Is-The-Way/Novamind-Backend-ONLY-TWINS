"""
VENV-dependent tests for the Patient Service.

These tests require Python packages but mock database access.
They test service layer functionality in isolation from actual database.
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.services.patient_service import PatientService
from app.domain.entities.patient import Patient
from app.domain.exceptions.patient_exceptions import PatientNotFoundError


@pytest.mark.db_required()
class TestPatientService:
    """Test suite for PatientService."""

    def setup_method(self):


        """Set up test fixtures for each test method."""
        # Create mock repository
        self.mock_repository = AsyncMock()
        self.mock_logger = MagicMock()

        # Create service with mock dependencies
        self.service = PatientService(,)
        repository= self.mock_repository,
        logger = self.mock_logger
        ()

        # Setup sample patient data
        self.patient_id = "test-patient-id"
        self.patient_data = {
        "id": self.patient_id,
        "name": "John Doe",
        "date_of_birth": "1980-01-01",
        "gender": "male",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "address": "123 Main St",
        "insurance_number": "INS12345",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
        }

        # Create a patient entity
        self.patient = Patient(**self.patient_data)

    async def test_get_patient_by_id_success(self):
        """Test successfully retrieving a patient by ID."""
        # Setup mock return value
        self.mock_repository.get_by_id.return_value = self.patient

        # Call the service method
        result = await self.service.get_by_id(self.patient_id)

        # Assertions
        assert result == self.patient
        self.mock_repository.get_by_id.assert_called_once_with(self.patient_id)

        async def test_get_patient_by_id_not_found(self):
            """Test retrieving a non-existent patient by ID."""
            # Setup mock to return None
            self.mock_repository.get_by_id.return_value = None

            # Expect exception
            with pytest.raises(PatientNotFoundError):
                await self.service.get_by_id(self.patient_id)

                # Verify mock was called
                self.mock_repository.get_by_id.assert_called_once_with(self.patient_id)

                async def test_create_patient_success(self):
                """Test successfully creating a patient."""
                # Setup mock to return the new patient
                self.mock_repository.create.return_value = self.patient

                # Call the service method
                result = await self.service.create(self.patient_data)

                # Assertions
                assert result == self.patient
                self.mock_repository.create.assert_called_once()

                # Verify logger was called
                self.mock_logger.info.assert_called_once()

                async def test_update_patient_success(self):
                """Test successfully updating a patient."""
                # Setup mocks
                self.mock_repository.get_by_id.return_value = self.patient
                self.mock_repository.update.return_value = self.patient

                # Updated data
                updated_data = {"name": "Jane Doe"}

                # Call the service method
                result = await self.service.update(self.patient_id, updated_data)

                # Assertions
                assert result == self.patient
                self.mock_repository.get_by_id.assert_called_once_with(self.patient_id)
                self.mock_repository.update.assert_called_once()

                async def test_delete_patient_success(self):
                """Test successfully deleting a patient."""
                # Setup mocks
                self.mock_repository.get_by_id.return_value = self.patient
                self.mock_repository.delete.return_value = True

                # Call the service method
                result = await self.service.delete(self.patient_id)

                # Assertions
                assert result is True
                self.mock_repository.get_by_id.assert_called_once_with(self.patient_id)
                self.mock_repository.delete.assert_called_once_with(self.patient_id)
