"""
Tests for the PatientRepository implementation.

This module tests the PatientRepository using the MockAsyncSession
to ensure proper database operations without requiring a real database.
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime
from typing import List, Optional
from unittest.mock import MagicMock # Import MagicMock

from app.domain.entities.patient import Patient
# Import the concrete implementation and the required dependency interface
from app.infrastructure.persistence.sqlalchemy.patient_repository import SQLAlchemyPatientRepository
from app.core.services.security.encryption_interface import BaseEncryptionService
from app.tests.fixtures.mock_db_fixture import MockAsyncSession

class TestPatientRepository:
    """Tests for the SQLAlchemyPatientRepository."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_db = MockAsyncSession()
        # Create a mock encryption service
        self.mock_encryption_service = MagicMock(spec=BaseEncryptionService)
        # Instantiate the correct repository with both dependencies
        self.repository = SQLAlchemyPatientRepository(self.mock_db, self.mock_encryption_service)

        # Create sample patients for testing using the correct Patient dataclass fields
        self.patient_1 = self._create_test_patient(
            name="John Doe",
            date_of_birth=datetime(1980, 1, 15),
            gender="Male", # Gender is required by Patient dataclass
            email="john.doe@example.com"
        )

        self.patient_2 = self._create_test_patient(
            name="Jane Smith",
            date_of_birth=datetime(1985, 5, 20),
            gender="Female",
            email="jane.smith@example.com"
        )

        self.patient_3 = self._create_test_patient(
            name="Robert Johnson",
            date_of_birth=datetime(1975, 10, 8),
            gender="Male",
            email="robert.johnson@example.com"
        )

    def _create_test_patient(
        self,
        name: str, # Use 'name' instead of first/last
        date_of_birth: datetime,
        gender: str, # Add gender
        email: str,
        patient_id: Optional[UUID] = None,
        **kwargs # Allow extra args for flexibility if needed later
    ) -> Patient:
        """Create a test patient entity for testing."""
        # Use Patient dataclass fields
        return Patient(
            id=patient_id or uuid4(),
            name=name,
            date_of_birth=date_of_birth,
            gender=gender,
            email=email,
            phone="555-123-4567", # Example phone
            address="123 Main St, Anytown, CA 94321", # Example address string
            # medical_history=[], # Add defaults if needed by tests
            # medications=[],
            # allergies=[],
            # treatment_notes=[],
            created_at=datetime.now(), # Add default if not handled by __post_init__
            updated_at=datetime.now()  # Add default if not handled by __post_init__
        )

    @pytest.mark.asyncio
    @pytest.mark.db_required
    async def test_create_patient(self):
        """Test creating a new patient."""
        # Configure mock to track the add operation
        self.mock_db._committed_objects = []

        # Create a new patient
        result = await self.repository.create(self.patient_1)

        # Verify patient was added and committed
        assert self.patient_1 in self.mock_db._committed_objects
        assert result == self.patient_1

    @pytest.mark.asyncio
    @pytest.mark.db_required
    async def test_get_patient_by_id(self):
        """Test retrieving a patient by ID."""
        # Configure mock to return our test patient
        self.mock_db._query_results = [self.patient_1]

        # Get patient by ID
        result = await self.repository.get_by_id(self.patient_1.id)

        # Verify query was executed and correct result returned
        assert self.mock_db._last_executed_query is not None
        assert result == self.patient_1

    @pytest.mark.asyncio
    @pytest.mark.db_required
    async def test_get_patient_by_id_not_found(self):
        """Test retrieving a non-existent patient."""
        # Configure mock to return no results
        self.mock_db._query_results = []

        # Get patient by ID that doesn't exist
        non_existent_id = uuid4()
        result = await self.repository.get_by_id(non_existent_id)

        # Verify query was executed and no result returned
        assert self.mock_db._last_executed_query is not None
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.db_required
    async def test_update_patient(self):
        """Test updating an existing patient."""
        # Configure mock to track update operation
        self.mock_db._committed_objects = []

        # Create a new patient instance for update to avoid modifying the fixture directly
        # Ensure all required fields are present
        updated_patient_data = {
             "id": self.patient_1.id,
             "name": "Jonathan Doe", # Updated name
             "date_of_birth": self.patient_1.date_of_birth,
             "gender": self.patient_1.gender,
             "email": "jonathan.doe@example.com", # Updated email
             "phone": self.patient_1.phone,
             "address": self.patient_1.address,
             "medical_history": self.patient_1.medical_history,
             "medications": self.patient_1.medications,
             "allergies": self.patient_1.allergies,
             "treatment_notes": self.patient_1.treatment_notes,
             "created_at": self.patient_1.created_at,
             "updated_at": datetime.now() # Update timestamp
        }
        updated_patient = Patient(**updated_patient_data)


        # Update patient
        result = await self.repository.update(updated_patient)

        # Verify patient was updated and committed
        assert updated_patient in self.mock_db._committed_objects
        assert result == updated_patient
        assert result.name == "Jonathan Doe" # Check updated name
        assert result.email == "jonathan.doe@example.com"

    @pytest.mark.asyncio
    @pytest.mark.db_required
    async def test_delete_patient(self):
        """Test deleting a patient."""
        # Configure mock to track delete operation
        self.mock_db._deleted_objects = []

        # Delete patient
        await self.repository.delete(self.patient_1)

        # Verify patient was deleted
        assert self.patient_1 in self.mock_db._deleted_objects

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
        """Test retrieving only active patients."""
        # Configure mock to return active patients
        active_patients = [self.patient_1, self.patient_2]
        self.mock_db._query_results = active_patients

        # Get active patients
        result = await self.repository.get_active_patients()
        
        # Verify query was executed and correct results returned
        assert self.mock_db._last_executed_query is not None
        assert len(result) == 2
        assert set(result) == set(active_patients)

    @pytest.mark.asyncio
    @pytest.mark.db_required
    async def test_get_active_patients(self):
        """Test retrieving only active patients."""
        # Configure mock to return active patients
        active_patients = [self.patient_1, self.patient_2]
        self.mock_db._query_results = active_patients

        # Get active patients
        result = await self.repository.get_active_patients()
        
        # Verify query was executed and correct results returned
        assert self.mock_db._last_executed_query is not None
        assert len(result) == 2
        assert set(result) == set(active_patients)
