"""
Unit tests for MockMentaLLaMA service.

This module tests the mock implementation of the MentaLLaMA service,
ensuring it correctly implements the interface and provides consistent
behavior for testing purposes. The tests verify initialization, error handling,
and all core psychiatry analysis features.
"""

import pytest
from datetime import datetime, timedelta
from app.domain.utils.datetime_utils import UTC
from typing import Dict, Any, List

from app.core.exceptions import (
    InvalidConfigurationError,
    InvalidRequestError,
    ModelNotFoundError,
    ServiceUnavailableError,
)

from app.infrastructure.ml.mentallama.mock import MockMentaLLaMA # Corrected import path


@pytest.fixture(scope="function")
def mock_mentallama_service_standalone(request):
    """Pytest fixture to set up and tear down MockMentaLLaMA for each standalone test."""
    service = MockMentaLLaMA()
    service.initialize({})
    
    sample_text = (
        "I've been feeling down for several weeks. I'm constantly tired, "
        "have trouble sleeping, and don't enjoy things anymore. Sometimes "
        "I wonder if life is worth living, but I wouldn't actually hurt myself."
    )
    
    # Store service and common data on the test instance via request
    request.instance.service = service
    request.instance.sample_text = sample_text
    
    yield service # Provide the service to the test function

    # Teardown: Shutdown the service
    if hasattr(request.instance, "service") and request.instance.service.is_healthy():
        request.instance.service.shutdown()


@pytest.mark.usefixtures("mock_mentallama_service_standalone")
@pytest.mark.db_required()
class TestMockMentaLLaMA:
    """Test suite for MockMentaLLaMA class (pytest style)."""

    @pytest.mark.standalone()
    def test_initialization(self) -> None:
        """Test initialization with valid and invalid configurations."""
        # Test default initialization
        service = MockMentaLLaMA()
        service.initialize({})  # type: ignore
        assert service.is_healthy()

        # Test with specific model configuration
        service = MockMentaLLaMA()
        service.initialize({"model": "mock-psychiatric-gpt-4"})  # type: ignore
        assert service.is_healthy()

        # Test with invalid model
        service = MockMentaLLaMA()
        with pytest.raises(ModelNotFoundError):
            service.initialize({"model": "nonexistent-model"})  # type: ignore

        # Test with invalid configuration
        service = MockMentaLLaMA()
        with pytest.raises(InvalidConfigurationError):
            service.initialize({"invalid_param": True})  # type: ignore

    @pytest.mark.standalone()
    def test_health_check(self) -> None:
        """Test health check functionality."""
        # Service should be healthy after initialization
        assert self.service.is_healthy()

        # Service should be unhealthy after shutdown
        self.service.shutdown()
        assert not self.service.is_healthy()

    @pytest.mark.standalone()
    def test_analyze_text(self) -> None:
        """Test text analysis functionality."""
        # Test with valid text
        result = self.service.analyze_text(self.sample_text)
        assert isinstance(result, dict)
        assert "sentiment" in result
        assert "entities" in result
        assert "keywords" in result
        assert "categories" in result

        # Test with empty text
        with pytest.raises(InvalidRequestError):
            self.service.analyze_text("")

        # Test with None
        with pytest.raises(InvalidRequestError):
            self.service.analyze_text(None)  # type: ignore

    @pytest.mark.standalone()
    def test_detect_mental_health_conditions(self) -> None:
        """Test mental health condition detection."""
        # Test with text indicating depression
        result = self.service.detect_mental_health_conditions(self.sample_text)
        assert isinstance(result, dict)
        assert "conditions" in result
        assert isinstance(result["conditions"], list)

        # Check for depression in detected conditions
        conditions = [c["condition"].lower() for c in result["conditions"]]
        assert "depression" in conditions

        # Test with text not indicating mental health issues
        result = self.service.detect_mental_health_conditions(
            "Today is a beautiful day. I'm going for a walk in the park."
        )
        assert isinstance(result, dict)
        assert "conditions" in result
        assert len(result["conditions"]) == 0

    @pytest.mark.standalone()
    def test_generate_therapeutic_response(self) -> None:
        """Test therapeutic response generation."""
        # Test with valid input
        result = self.service.generate_therapeutic_response(
            self.sample_text,
            context={"previous_sessions": 2}
        )
        assert isinstance(result, dict)
        assert "response" in result
        assert "techniques" in result

        # Test with invalid input
        with pytest.raises(InvalidRequestError):
            self.service.generate_therapeutic_response("")

    @pytest.mark.standalone()
    def test_assess_suicide_risk(self) -> None:
        """Test suicide risk assessment."""
        # Test with text indicating some risk
        result = self.service.assess_suicide_risk(self.sample_text)
        assert isinstance(result, dict)
        assert "risk_level" in result
        assert "risk_factors" in result
        assert "recommendations" in result

        # Test with high-risk text
        high_risk_text = (
            "I can't take it anymore. I've written my note and made my plan. "
            "No one will miss me anyway. I'll be gone by tomorrow."
        )
        result = self.service.assess_suicide_risk(high_risk_text)
        assert result["risk_level"] == "high"

        # Test with low-risk text
        low_risk_text = "I'm feeling great today. Life is wonderful."
        result = self.service.assess_suicide_risk(low_risk_text)
        assert result["risk_level"] == "low"

    @pytest.mark.standalone()
    def test_generate_treatment_plan(self) -> None:
        """Test treatment plan generation."""
        # Test with valid input
        result = self.service.generate_treatment_plan(
            patient_data={
                "age": 35,
                "gender": "female",
                "symptoms": self.sample_text,
                "medical_history": ["anxiety"],
                "previous_treatments": ["cbt"]
            }
        )
        assert isinstance(result, dict)
        assert "plan" in result
        assert "goals" in result
        assert "interventions" in result
        assert "timeline" in result

        # Test with invalid input
        with pytest.raises(InvalidRequestError):
            self.service.generate_treatment_plan(patient_data={})

    @pytest.mark.standalone()
    def test_analyze_session_transcript(self) -> None:
        """Test session transcript analysis."""
        # Create a mock transcript
        transcript = [
            {"role": "therapist", "content": "How have you been feeling lately?"},
            {"role": "patient", "content": self.sample_text},
            {
                "role": "therapist",
                "content": "That sounds difficult. Have you had these feelings before?",
            },
            {"role": "patient", "content": "Yes, a few years ago when I went through a divorce."},
        ]

        # Test with valid transcript
        result = self.service.analyze_session_transcript(transcript)
        assert isinstance(result, dict)
        assert "themes" in result
        assert "patient_insights" in result
        assert "therapist_insights" in result
        assert "recommendations" in result

        # Test with invalid transcript
        with pytest.raises(InvalidRequestError):
            self.service.analyze_session_transcript([])

    @pytest.mark.standalone()
    def test_generate_progress_report(self) -> None:
        """Test progress report generation."""
        # Test with valid input
        result = self.service.generate_progress_report(
            patient_id="test-patient-123",
            start_date=datetime.now(UTC) - timedelta(days=30),
            end_date=datetime.now(UTC),
            sessions_data=[
                {"date": datetime.now(UTC) - timedelta(days=25), "notes": "Initial assessment."},
                {"date": datetime.now(UTC) - timedelta(days=18), "notes": "Patient reported improved sleep."},
                {"date": datetime.now(UTC) - timedelta(days=11), "notes": "Discussed coping strategies."},
                {"date": datetime.now(UTC) - timedelta(days=4), "notes": "Patient reported reduced anxiety."},
            ]
        )
        assert isinstance(result, dict)
        assert "summary" in result
        assert "progress" in result
        assert "goals" in result
        assert "recommendations" in result

        # Test with invalid input
        with pytest.raises(InvalidRequestError):
            self.service.generate_progress_report(
                patient_id="test-patient-123",
                start_date=None,  # type: ignore
                end_date=None,  # type: ignore
                sessions_data=[]
            )

    @pytest.mark.standalone()
    def test_analyze_medication_response(self) -> None:
        """Test medication response analysis."""
        # Test with valid input
        result = self.service.analyze_medication_response(
            medication="escitalopram",
            dosage="10mg",
            duration_days=30,
            side_effects=["nausea", "insomnia"],
            symptom_changes={"anxiety": "reduced", "sleep": "unchanged"}
        )
        assert isinstance(result, dict)
        assert "response_summary" in result
        assert "side_effects_analysis" in result
        assert "recommendations" in result

        # Test with invalid input
        with pytest.raises(InvalidRequestError):
            self.service.analyze_medication_response(
                medication="", dosage="", duration_days=0, side_effects=[], symptom_changes={}
            )

    @pytest.mark.standalone()
    def test_digital_twin_session_workflow(self) -> None:
        """Test the complete digital twin session workflow from creation to insights."""
        # Create a digital twin
        twin_result = self.service.generate_digital_twin(
            text_data=[self.sample_text],
            demographic_data={"age": 35, "gender": "female"},
            medical_history={"conditions": ["anxiety", "insomnia"]},
            treatment_history={"medications": ["escitalopram"]},
        )
        assert "digital_twin_id" in twin_result
        twin_id = twin_result["digital_twin_id"]

        # Create a session with the digital twin
        session_result = self.service.create_digital_twin_session(twin_id, session_type="therapy")
        assert "session_id" in session_result
        session_id = session_result["session_id"]

        # Get session details
        session_details = self.service.get_digital_twin_session(session_id)
        assert session_details["twin_id"] == twin_id
        assert session_details["status"] == "active"

        # Send message to session
        message_result = self.service.send_message_to_session(session_id, "How can I manage my anxiety better?")
        assert "response" in message_result
        assert "messages" in message_result
        assert len(message_result["messages"]) > 0

        # End session
        end_result = self.service.end_digital_twin_session(session_id)
        assert end_result["status"] == "completed"
        assert "summary" in end_result

        # Get session insights
        insights = self.service.get_session_insights(session_id)
        assert "insights" in insights
        assert "themes" in insights["insights"]
        assert "recommendations" in insights["insights"]