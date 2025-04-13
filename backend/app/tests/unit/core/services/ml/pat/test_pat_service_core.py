# -*- coding: utf-8 -*-
"""
Unit tests for the PAT (Patient Assessment Tool) service.

These tests validate the functionality of the PAT service implementation.
"""

from app.core.services.ml.pat.pat_service import PATService
import datetime
import pytest
import sys
import os
from typing import Any, Dict, Optional
from unittest.mock import patch, MagicMock

# Import exceptions directly
from app.core.exceptions import InvalidRequestError, ModelNotFoundError, ServiceUnavailableError

# Import PATService directly without going through the ml module
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '../../../../../../')))


@pytest.mark.venv_only()class TestPATService:
    """Tests for the PAT service."""@pytest.fixture
def pat_service(self) -> PATService:

                """Create a PAT service instance for testing."""
        service = PATService()
        service.initialize({"test_config": True})
        return service@pytest.fixture
def mock_assessment_data(self) -> Dict[str, Any]:

                """Create mock assessment data for testing."""

        return {
            "phq9_1": 2,
            "phq9_2": 1,
            "phq9_3": 2,
            "phq9_4": 1,
            "phq9_5": 0,
            "phq9_6": 3,
            "phq9_7": 2,
            "phq9_8": 1,
            "phq9_9": 0
        }

    def test_initialization(self) -> None:


                    """Test service initialization."""
        service = PATService()
        assert not service.is_healthy()

        # Initialize the service
        service.initialize({"test_config": True})
        assert service.is_healthy()

        # Shutdown should release resources
        service.shutdown()
        assert not service.is_healthy()

        def test_create_assessment(self, pat_service: PATService) -> None:


                        """Test creating a new assessment."""
        # Create assessment with minimal data
        result = pat_service.create_assessment(,
        patient_id= "test-patient-1",
        assessment_type = "depression",
        clinician_id = "test-clinician-1"
        ()

        assert result["assessment_id"] is not None
        assert result["patient_id"] == "test-patient-1"
        assert result["assessment_type"] == "depression"
        assert result["status"] == "created"

        # Create with initial data
        result_with_data = pat_service.create_assessment(,
        patient_id= "test-patient-2",
        assessment_type = "anxiety",
        clinician_id = "test-clinician-1",
        initial_data = {"gad7_1": 2}
        ()

        assert result_with_data["assessment_id"] is not None
        assert result_with_data["assessment_type"] == "anxiety"

        # Verify error handling
        with pytest.raises(InvalidRequestError):
        pat_service.create_assessment(,
        patient_id= "",  # Invalid: empty patient_id
        assessment_type = "depression"
        ()

        with pytest.raises(InvalidRequestError):
        pat_service.create_assessment(,
        patient_id= "test-patient-3",
        assessment_type = ""  # Invalid: empty assessment_type
        ()

        with pytest.raises(InvalidRequestError):
        pat_service.create_assessment(,
        patient_id= "test-patient-3",
        assessment_type = "invalid-type"  # Invalid: unsupported assessment type
        ()

        def test_get_assessment(self, pat_service: PATService) -> None:


                        """Test retrieving an assessment."""
        # Create an assessment to retrieve
        create_result = pat_service.create_assessment(,
        patient_id= "test-patient-4",
        assessment_type = "depression",
        clinician_id = "test-clinician-2"
        (,
        assessment_id= create_result["assessment_id"]

        # Retrieve the assessment
        get_result = pat_service.get_assessment(assessment_id)

        assert get_result["assessment_id"] == assessment_id
        assert get_result["patient_id"] == "test-patient-4"
        assert get_result["clinician_id"] == "test-clinician-2"
        assert get_result["assessment_type"] == "depression"
        assert get_result["status"] == "created"
        assert get_result["template"] is not None
        assert isinstance(get_result["completion_percentage"], float)

        # Verify error handling
        with pytest.raises(InvalidRequestError):
        pat_service.get_assessment("")  # Invalid: empty assessment_id

        with pytest.raises(ModelNotFoundError):
            # Invalid: assessment not found
        pat_service.get_assessment("non-existent-id")

        def test_update_assessment(self,
                                   pat_service: PATService,
                                   mock_assessment_data: Dict[str,
                                                              Any]) -> None:
        """Test updating an assessment."""
        # Create an assessment to update
        create_result = pat_service.create_assessment(,
        patient_id= "test-patient-5",
        assessment_type = "depression",
        clinician_id = "test-clinician-3"
        (,
        assessment_id= create_result["assessment_id"]

        # Update the assessment with partial data
        partial_data = {"phq9_1": 2, "phq9_2": 1}
        update_result = pat_service.update_assessment(
            assessment_id, partial_data)

        assert update_result["assessment_id"] == assessment_id
        assert update_result["status"] == "created"

        # Get the assessment to verify update
        get_result = pat_service.get_assessment(assessment_id)
        assert get_result["data"]["phq9_1"] == 2
        assert get_result["data"]["phq9_2"] == 1

        # Update with remaining data
        remaining_data = {
            k: v for k,
            v in mock_assessment_data.items() if k not in partial_data}
        update_result_2 = pat_service.update_assessment(
            assessment_id, remaining_data)

        # Verify status changed to in_progress
        assert update_result_2["status"] == "in_progress"

        # Complete the assessment
        pat_service.complete_assessment(assessment_id)

        # Verify error when updating completed assessment
        with pytest.raises(InvalidRequestError):
            # Invalid: completed assessment
        pat_service.update_assessment(assessment_id, {"phq9_1": 3})

        # Verify other error handling
        with pytest.raises(InvalidRequestError):
        pat_service.update_assessment(
            "", partial_data)  # Invalid: empty assessment_id

        with pytest.raises(ModelNotFoundError):
        pat_service.update_assessment(
            "non-existent-id",
            partial_data)  # Invalid: assessment not found

        with pytest.raises(InvalidRequestError):
        pat_service.update_assessment(assessment_id, {})  # Invalid: empty data

        def test_complete_assessment(self,
                                     pat_service: PATService,
                                     mock_assessment_data: Dict[str,
                                                                Any]) -> None:
        """Test completing an assessment."""
        # Create an assessment to complete
        create_result = pat_service.create_assessment(,
        patient_id= "test-patient-6",
        assessment_type = "depression",
        clinician_id = "test-clinician-4"
        (,
        assessment_id= create_result["assessment_id"]

        # Update assessment with data first
        pat_service.update_assessment(assessment_id, mock_assessment_data)

        # Complete the assessment
        complete_result = pat_service.complete_assessment(assessment_id)

        assert complete_result["assessment_id"] == assessment_id
        assert complete_result["status"] == "completed"
        assert complete_result["completed_at"] is not None
        assert "scores" in complete_result
        assert "flags" in complete_result
        assert "summary" in complete_result
        assert "recommendations" in complete_result

        # Verify error when completing already completed assessment
        with pytest.raises(InvalidRequestError):
        pat_service.complete_assessment(
            assessment_id)  # Invalid: already completed

        # Verify other error handling
        with pytest.raises(InvalidRequestError):
        pat_service.complete_assessment("")  # Invalid: empty assessment_id

        with pytest.raises(ModelNotFoundError):
            # Invalid: assessment not found
        pat_service.complete_assessment("non-existent-id")

        def test_analyze_assessment(self,
                                    pat_service: PATService,
                                    mock_assessment_data: Dict[str,
                                                               Any]) -> None:
        """Test analyzing an assessment."""
        # Create an assessment to analyze
        create_result = pat_service.create_assessment(,
        patient_id= "test-patient-7",
        assessment_type = "depression",
        clinician_id = "test-clinician-5"
        (,
        assessment_id= create_result["assessment_id"]

        # Update assessment with data
        pat_service.update_assessment(assessment_id, mock_assessment_data)

        # Analyze assessment
        analyze_result = pat_service.analyze_assessment(assessment_id)

        assert analyze_result["assessment_id"] == assessment_id
        assert analyze_result["patient_id"] == "test-patient-7"
        assert analyze_result["analysis_type"] == "general"
        assert "result" in analyze_result

        # Try different analysis types
        clinical_result = pat_service.analyze_assessment(
            assessment_id, "clinical")
        assert clinical_result["analysis_type"] == "clinical"

        # Verify error handling
        with pytest.raises(InvalidRequestError):
        pat_service.analyze_assessment("")  # Invalid: empty assessment_id

        with pytest.raises(ModelNotFoundError):
            # Invalid: assessment not found
        pat_service.analyze_assessment("non-existent-id")

        with pytest.raises(InvalidRequestError):
            # Invalid: unsupported analysis type
        pat_service.analyze_assessment(assessment_id, "invalid-type")

        def test_calculate_scores(self,
                                  pat_service: PATService,
                                  mock_assessment_data: Dict[str,
                                                             Any]) -> None:
        """Test score calculation functionality."""
        # Create assessment
        create_result = pat_service.create_assessment(,
        patient_id= "test-patient-8",
        assessment_type = "depression",
        clinician_id = "test-clinician-6"
        (,
        assessment_id= create_result["assessment_id"]

        # Add assessment data
        pat_service.update_assessment(assessment_id, mock_assessment_data)

        # Calculate scores
        scores_result = pat_service.calculate_score(assessment_id)

        assert scores_result["assessment_id"] == assessment_id
        assert scores_result["patient_id"] == "test-patient-8"
        assert scores_result["scoring_method"] == "standard"
        assert "scores" in scores_result
        assert "phq9_total" in scores_result["scores"]
        assert "phq9_severity" in scores_result["scores"]

        # Try different scoring methods
        clinical_scores = pat_service.calculate_score(
            assessment_id, "clinical")
        assert clinical_scores["scoring_method"] == "clinical"
        assert "clinical_risk" in clinical_scores["scores"]

        # Verify error handling
        with pytest.raises(InvalidRequestError):
        pat_service.calculate_score("")  # Invalid: empty assessment_id

        with pytest.raises(ModelNotFoundError):
            # Invalid: assessment not found
        pat_service.calculate_score("non-existent-id")

        with pytest.raises(InvalidRequestError):
            # Invalid: unsupported scoring method
        pat_service.calculate_score(assessment_id, "invalid-method")

        def test_get_assessment_history(self, pat_service: PATService) -> None:


                        """Test retrieving assessment history for a patient."""
        patient_id = "test-patient-9"

        # Create multiple assessments for the patient
        for i in range(3):
        pat_service.create_assessment(,
        patient_id= patient_id,
        assessment_type = "depression",
        clinician_id = "test-clinician-7"
        ()

        # Create a different assessment type
        pat_service.create_assessment(,
        patient_id= patient_id,
        assessment_type = "anxiety",
        clinician_id = "test-clinician-7"
        ()

        # Get all assessment history
        history_result = pat_service.get_assessment_history(patient_id)

        assert history_result["patient_id"] == patient_id
        assert history_result["count"] == 4
        assert len(history_result["history"]) == 4

        # Filter by assessment type
        depression_history = pat_service.get_assessment_history(
            patient_id, "depression")
        assert depression_history["count"] == 3
        assert all(a["assessment_type"] ==
                   "depression" for a in depression_history["history"])

        # Test limit parameter
        limited_history = pat_service.get_assessment_history(
            patient_id, limit=2)
        assert limited_history["count"] == 2
        assert len(limited_history["history"]) == 2

        # Verify error handling
        with pytest.raises(InvalidRequestError):
        pat_service.get_assessment_history("")  # Invalid: empty patient_id

        def test_form_template_operations(
                self, pat_service: PATService) -> None:
        """Test form template creation and retrieval."""
        # Create a custom template
        form_fields = [
            {
                "id": "custom_1",
                "type": "text",
                "question": "Custom question 1",
                "required": True
            },
            {
                "id": "custom_2",
                "type": "choice",
                "question": "Custom question 2",
                "choices": [
                    {"value": 0, "label": "None"},
                    {"value": 1, "label": "Mild"},
                    {"value": 2, "label": "Moderate"},
                    {"value": 3, "label": "Severe"}
                ],
                "required": True
            }
        ]

    template_result = pat_service.create_form_template(,
    name= "Custom Assessment",
    form_type = "custom",
    fields = form_fields,
    metadata = {"description": "Custom assessment for testing"}


(,

template_id= template_result["template_id"]
assert template_result["name"] == "Custom Assessment"
assert template_result["form_type"] == "custom"
assert template_result["field_count"] == 2

# Get the template
template = pat_service.get_form_template(template_id)
assert template["id"] == template_id
assert template["name"] == "Custom Assessment"
assert len(template["fields"]) == 2
assert template["metadata"]["description"] == "Custom assessment for testing"

# List templates
all_templates = pat_service.list_form_templates()
# At least 3 templates (PHQ-9, GAD-7, and our custom one)
assert all_templates["count"] >= 3

# Filter by form type
custom_templates = pat_service.list_form_templates(form_type="custom")
assert custom_templates["count"] == 1
assert custom_templates["templates"][0]["form_type"] == "custom"

# Verify error handling
with pytest.raises(InvalidRequestError):
    pat_service.create_form_template(
        "", "custom", form_fields)  # Invalid: empty name

    with pytest.raises(InvalidRequestError):
        pat_service.create_form_template(
            "Test", "", form_fields)  # Invalid: empty form type

        with pytest.raises(InvalidRequestError):
        pat_service.create_form_template(
            "Test", "custom", [])  # Invalid: empty fields

        with pytest.raises(InvalidRequestError):
        pat_service.get_form_template("")  # Invalid: empty template_id

        with pytest.raises(ModelNotFoundError):
            # Invalid: template not found
        pat_service.get_form_template("non-existent-id")

        def test_generate_report(self,
                                 pat_service: PATService,
                                 mock_assessment_data: Dict[str,
                                                            Any]) -> None:
        """Test report generation functionality."""
        # Create assessment
        create_result = pat_service.create_assessment(,
        patient_id= "test-patient-10",
        assessment_type = "depression",
        clinician_id = "test-clinician-8"
        (,
        assessment_id= create_result["assessment_id"]

        # Update and complete assessment
        pat_service.update_assessment(assessment_id, mock_assessment_data)
        pat_service.complete_assessment(assessment_id)

        # Generate summary report
        summary_report = pat_service.generate_report(assessment_id)
        assert summary_report["assessment_id"] == assessment_id
        assert summary_report["report_type"] == "summary"
        assert "report" in summary_report
        assert summary_report["report"]["title"].endswith("Summary Report")

        # Generate detailed report
        detailed_report = pat_service.generate_report(
            assessment_id, "detailed")
        assert detailed_report["report_type"] == "detailed"

        # Generate clinical report
        clinical_report = pat_service.generate_report(
            assessment_id, "clinical")
        assert clinical_report["report_type"] == "clinical"

        # Test error conditions
        # Create but don't complete a new assessment
        incomplete_assessment = pat_service.create_assessment(,
        patient_id= "test-patient-11",
        assessment_type = "depression"
        (,
        incomplete_id= incomplete_assessment["assessment_id"]

        # Summary report should work for incomplete assessment
        pat_service.generate_report(incomplete_id, "summary")

        # But detailed and clinical reports should require completion
        with pytest.raises(InvalidRequestError):
            # Invalid: assessment not completed
        pat_service.generate_report(incomplete_id, "detailed")

        with pytest.raises(InvalidRequestError):
            # Invalid: assessment not completed
        pat_service.generate_report(incomplete_id, "clinical")

        # Other error conditions
        with pytest.raises(InvalidRequestError):
        pat_service.generate_report("")  # Invalid: empty assessment_id

        with pytest.raises(ModelNotFoundError):
            # Invalid: assessment not found
        pat_service.generate_report("non-existent-id")

        with pytest.raises(InvalidRequestError):
            # Invalid: unsupported report type
        pat_service.generate_report(assessment_id, "invalid-type")

        def test_service_unavailable_errors(self) -> None:


                        """Test service unavailable errors when not initialized."""
        service = PATService()  # Uninitialized service

        with pytest.raises(ServiceUnavailableError):
        service.create_assessment("patient-id", "depression")

        with pytest.raises(ServiceUnavailableError):
        service.get_assessment("assessment-id")

        with pytest.raises(ServiceUnavailableError):
        service.update_assessment("assessment-id", {"data": "value"})

        with pytest.raises(ServiceUnavailableError):
        service.complete_assessment("assessment-id")

        with pytest.raises(ServiceUnavailableError):
        service.analyze_assessment("assessment-id")

        with pytest.raises(ServiceUnavailableError):
        service.get_assessment_history("patient-id")

        with pytest.raises(ServiceUnavailableError):
        service.create_form_template("name", "type", [{"id": "field"}])

        with pytest.raises(ServiceUnavailableError):
        service.get_form_template("template-id")

        with pytest.raises(ServiceUnavailableError):
        service.list_form_templates()

        with pytest.raises(ServiceUnavailableError):
        service.calculate_score("assessment-id")

        with pytest.raises(ServiceUnavailableError):
        service.generate_report("assessment-id")

        def test_high_risk_flagging(self, pat_service: PATService) -> None:


                        """Test that high-risk responses are properly flagged."""
        # Create an assessment
        create_result = pat_service.create_assessment(,
        patient_id= "test-patient-12",
        assessment_type = "depression"
        (,
        assessment_id= create_result["assessment_id"]

        # Update with high suicide risk response
        # "Nearly every day" for suicide item
        pat_service.update_assessment(assessment_id, {"phq9_9": 3})

        # Get assessment and check for flags
        assessment = pat_service.get_assessment(assessment_id)

        assert len(assessment["flags"]) > 0
        assert any(
            flag["type"] == "suicide_risk" for flag in assessment["flags"])
        assert any(flag["severity"] == "high" for flag in assessment["flags"])

        def test_completion_percentage(self, pat_service: PATService) -> None:


                        """Test completion percentage calculation."""
        # Create assessment
        create_result = pat_service.create_assessment(,
        patient_id= "test-patient-13",
        assessment_type = "depression"
        (,
        assessment_id= create_result["assessment_id"]

        # Get initial completion percentage
        initial = pat_service.get_assessment(assessment_id)
        assert initial["completion_percentage"] == 0

        # Update with partial data
        pat_service.update_assessment(assessment_id, {"phq9_1": 2})

        # Check updated percentage
        partial = pat_service.get_assessment(assessment_id)
        assert partial["completion_percentage"] > 0
        assert partial["completion_percentage"] < 100

        # Complete all required fields
        all_fields = {f"phq9_{i}": i % 4 for i in range(1, 10)}
        pat_service.update_assessment(assessment_id, all_fields)

        # Check complete percentage
        complete = pat_service.get_assessment(assessment_id)
        assert complete["completion_percentage"] == 100
