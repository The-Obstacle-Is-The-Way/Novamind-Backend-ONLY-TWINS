"""
Test fixtures for standalone tests.

This file contains pytest fixtures that are available to all standalone tests.
These fixtures should have no external dependencies and should use only mocks and stubs.
"""

import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_patient():
    """Provides a mock patient entity."""
    return Mock(
        id="123e4567-e89b-12d3-a456-426614174000",
        name="Test Patient",
        date_of_birth="1990-01-01",
        medical_record_number="MRN12345"
    )


@pytest.fixture
def mock_repository():
    """Provides a mock repository that can be used for any entity."""
    repo = Mock()
    repo.get.return_value = None
    repo.get_all.return_value = []
    repo.add.return_value = True
    repo.update.return_value = True
    repo.delete.return_value = True
    return repo


@pytest.fixture
def mock_service():
    """Provides a mock service that can be used for any domain service."""
    service = Mock()
    service.process.return_value = {"status": "success"}
    service.validate.return_value = True
    service.calculate.return_value = 0
    return service