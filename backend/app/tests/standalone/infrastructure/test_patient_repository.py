"""
Tests for the PatientRepository implementation.

This module tests the PatientRepository using the MockAsyncSession
to ensure proper database operations without requiring a real database.
"""
import pytest
import uuid
from uuid import uuid4, UUID
from datetime import datetime
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.patient import Patient
from app.infrastructure.repositories.mock_patient_repository import MockPatientRepository as PatientRepository
from app.tests.fixtures.mock_db_fixture import MockAsyncSession
from app.infrastructure.security.encryption.base_encryption_service import BaseEncryptionService


@pytest.fixture
def mock_db_session():
    """Fixture for a mock database session."""
    return AsyncMock()

@pytest.fixture
def mock_encryption_service():
    """Fixture for a mock encryption service."""
    mock_service = MagicMock(spec=BaseEncryptionService)
    mock_service.encrypt.side_effect = lambda x: f"enc_{x}" if x else None
    mock_service.decrypt.side_effect = lambda x: x[4:] if x and x.startswith("enc_") else x
    return mock_service

@pytest.fixture
def repository(mock_db_session, mock_encryption_service):
    """Fixture for PatientRepository with mocked dependencies."""
    return PatientRepository(session=mock_db_session, encryption_service=mock_encryption_service)

@pytest.fixture
def sample_patient_data():
    """Fixture for sample patient data."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Jane Doe",
        "date_of_birth": "1990-01-01",
        "gender": "female",
        "email": "jane.doe@example.com"
    }

@pytest.mark.asyncio
class TestPatientRepository:
    """Tests for the PatientRepository."""

    @pytest.fixture(autouse=True)
    async def setup_method(self, mock_db_session, mock_encryption_service):
        """Setup method for TestPatientRepository class."""
        self.mock_db = mock_db_session
        self.mock_encryption_service = mock_encryption_service
        self.repository = PatientRepository(session=self.mock_db, encryption_service=self.mock_encryption_service)
        self.mock_db.reset_mock()
        self.mock_encryption_service.reset_mock()

        # Create sample patients for testing
        self.patient_1 = self._create_test_patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime(1980, 1, 15),
            email="john.doe@example.com"
        )
        self.patient_2 = self._create_test_patient(
            first_name="Jane",
            last_name="Smith",
            date_of_birth=datetime(1985, 5, 20),
            email="jane.smith@example.com"
        )
        self.patient_3 = self._create_test_patient(
            first_name="Robert",
            last_name="Johnson",
            date_of_birth=datetime(1975, 10, 8),
            email="robert.johnson@example.com"
        )

    def _create_test_patient(self,
                      first_name: str,
                      last_name: str,
                      date_of_birth: datetime,
                      email: str,
                      patient_id: Optional[UUID] = None) -> Patient:
        """Create a test patient entity for testing."""
        return Patient(
            id=patient_id or uuid4(),
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            email=email,
            phone_number="555-123-4567",
            address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="94321",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    async def test_create_patient(self, repository, sample_patient_data):
        """Test creating a patient."""
        patient = Patient(**sample_patient_data)
        await repository.create(patient)
        repository.session.add.assert_called_once_with(patient)
        repository.session.commit.assert_called_once()

    async def test_get_patient_by_id(self, repository, sample_patient_data):
        """Test retrieving a patient by ID."""
        mock_patient = Patient(**sample_patient_data)
        repository.session.get.return_value = mock_patient
        retrieved_patient = await repository.get_by_id(mock_patient.id)
        assert retrieved_patient == mock_patient
        repository.session.get.assert_called_once_with(Patient, mock_patient.id)

    async def test_get_patient_by_id_not_found(self, repository):
        """Test retrieving a non-existent patient by ID."""
        repository.session.get.return_value = None
        retrieved_patient = await repository.get_by_id(str(uuid4()))
        assert retrieved_patient is None
        repository.session.get.assert_called_once()

    async def test_update_patient(self, repository, sample_patient_data):
        """Test updating a patient."""
        patient = Patient(**sample_patient_data)
        repository.session.merge.return_value = patient
        repository.session.get.return_value = patient
        
        update_data = {"name": "Jane Smith Updated"}
        updated_patient = await repository.update(patient.id, update_data)
        
        assert updated_patient.name == "Jane Smith Updated"
        repository.session.commit.assert_called_once()

    async def test_delete_patient(self, repository, sample_patient_data):
        """Test deleting a patient."""
        patient = Patient(**sample_patient_data)
        repository.session.get.return_value = patient
        await repository.delete(patient.id)
        repository.session.delete.assert_called_once_with(patient)
        repository.session.commit.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.db_required
    async def test_get_all_patients(self):
        """Test retrieving all patients."""
        # Configure mock to return our test patients
        patients = [self.patient_1, self.patient_2, self.patient_3]
        self.mock_db._query_results = patients

        # Get all patients
        result = await self.repository.get_all()

        # Verify query was executed and correct results returned
        assert self.mock_db._last_executed_query is not None
        assert len(result) == 3
        assert set(result) == set(patients)

    @pytest.mark.asyncio
    @pytest.mark.db_required
    async def test_get_patients_by_last_name(self):
        """Test retrieving patients by last name."""
        # Configure mock to return filtered results
        self.mock_db._query_results = [self.patient_1]

        # Get patients by last name
        result = await self.repository.get_by_last_name("Doe")

        # Verify query was executed and correct results returned
        assert self.mock_db._last_executed_query is not None
        assert len(result) == 1
        assert result[0] == self.patient_1

    @pytest.mark.asyncio
    @pytest.mark.db_required
    async def test_get_active_patients(self):
        """Test retrieving active patients."""
        # Configure mock to return active patients
        active_patients = [self.patient_1, self.patient_2]
        self.mock_db._query_results = active_patients

        # Get active patients
        result = await self.repository.get_active_patients()

        # Verify query was executed and correct results returned
        assert self.mock_db._last_executed_query is not None
        assert len(result) == 2
        assert set(result) == set(active_patients)