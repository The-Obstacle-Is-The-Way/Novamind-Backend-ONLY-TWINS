from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from typing import Dict
from app.domain.patient import Patient
from app.exceptions.patient_not_found_error import PatientNotFoundError

@patch('app.application.services.patient_service.PatientService.get_by_id')
# @patch('app.presentation.api.dependencies.auth.verify_patient_access')
@patch('app.presentation.api.v1.endpoints.patient.phi_sanitizer')
def test_access_patient_phi_data_success(
    # mock_verify_patient_access: MagicMock,
    mock_phi_sanitizer: MagicMock,
    mock_get_patient_by_id: MagicMock,
    client: TestClient,
    test_patient: Patient,
    provider_token_headers: Dict[str, str]
):
    # ... existing code ...
    # mock_verify_patient_access.return_value = None
    mock_get_patient_by_id.return_value = test_patient
    mock_phi_sanitizer.return_value = sanitized_data

    # ... existing code ...

# @patch('app.presentation.api.dependencies.auth.verify_patient_access')
@patch('app.presentation.api.v1.endpoints.patient.phi_sanitizer')
def test_access_patient_phi_data_unauthorized(
    # mock_verify_patient_access: MagicMock,
    mock_phi_sanitizer: MagicMock,
    client: TestClient,
    test_patient: Patient,
    provider_token_headers: Dict[str, str]
):
    # ... existing code ...
    # mock_verify_patient_access.side_effect = HTTPException(status_code=403, detail="Forbidden")

    # ... existing code ...

@patch('app.application.services.patient_service.PatientService.get_by_id')
def test_access_patient_phi_data_patient_not_found(
    mock_get_patient_by_id: MagicMock,
    client: TestClient,
    test_patient: Patient,
    provider_token_headers: Dict[str, str]
):
    # ... existing code ...
    mock_get_patient_by_id.side_effect = PatientNotFoundError(patient_id="unknown_patient_id")

    # ... existing code ... 