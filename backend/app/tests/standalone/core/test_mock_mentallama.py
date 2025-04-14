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

from app.core.services.ml.mock import MockMentaLLaMA
from app.tests.unit.base_test_unit import BaseUnitTest  # Updated import path after rename


@pytest.mark.db_required()
class TestMockMentaLLaMA(BaseUnitTest):
    """Test suite for MockMentaLLaMA class that provides psychiatric analysis."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        super().setUp()
        self.service = MockMentaLLaMA()
        self.service.initialize({})
        self.sample_text = (
            "I've been feeling down for several weeks. I'm constantly tired, "
            "have trouble sleeping, and don't enjoy things anymore. Sometimes "
            "I wonder if life is worth living, but I wouldn't actually hurt myself."
        )

    def tearDown(self) -> None:
        """Clean up after each test."""
        if hasattr(self, "service") and self.service.is_healthy():
            self.service.shutdown()
        super().tearDown()

    @pytest.mark.standalone()
    def test_initialization(self) -> None:
        """Test initialization with valid and invalid configurations."""
        # Test default initialization
        service = MockMentaLLaMA()
        service.initialize({})  # type: ignore
        self.assertTrue(service.is_healthy())

        # Test with specific model configuration
        service = MockMentaLLaMA()
        service.initialize({"model": "mock-psychiatric-gpt-4"})  # type: ignore
        self.assertTrue(service.is_healthy())

        # Test with invalid model
        service = MockMentaLLaMA()
        with self.assertRaises(ModelNotFoundError):
            service.initialize({"model": "nonexistent-model"})  # type: ignore

        # Test with invalid configuration
        service = MockMentaLLaMA()
        with self.assertRaises(InvalidConfigurationError):
            service.initialize({"invalid_param": True})  # type: ignore

    @pytest.mark.standalone()
    def test_health_check(self) -> None:
        """Test health check functionality."""
        # Service should be healthy after initialization
        self.assertTrue(self.service.is_healthy())

        # Service should be unhealthy after shutdown
        self.service.shutdown()
        self.assertFalse(self.service.is_healthy())

        # Reinitialize for other tests (done in setUp)
        # self.service = MockMentaLLaMA()
        # self.service.initialize({})

    @pytest.mark.standalone()
    def test_analyze_text(self) -> None:
        """Test text analysis functionality."""
        # Test with valid text
        result = self.service.analyze_text(self.sample_text)
        self.assertIsInstance(result, dict)
        self.assertIn("sentiment", result)
        self.assertIn("entities", result)
        self.assertIn("keywords", result)
        self.assertIn("categories", result)

        # Test with empty text
        with self.assertRaises(InvalidRequestError):
            self.service.analyze_text("")

        # Test with None
        with self.assertRaises(InvalidRequestError):
            self.service.analyze_text(None)  # type: ignore

    @pytest.mark.standalone()
    def test_detect_mental_health_conditions(self) -> None:
        """Test mental health condition detection."""
        # Test with text indicating depression
        result = self.service.detect_mental_health_conditions(self.sample_text)
        self.assertIsInstance(result, dict)
        self.assertIn("conditions", result)
        self.assertIsInstance(result["conditions"], list)

        # Check for depression in detected conditions
        conditions = [c["condition"].lower() for c in result["conditions"]]
        self.assertIn("depression", conditions)

        # Test with text not indicating mental health issues
        result = self.service.detect_mental_health_conditions(
            "Today is a beautiful day. I'm going for a walk in the park."
        )
        self.assertIsInstance(result, dict)
        self.assertIn("conditions", result)
        self.assertEqual(len(result["conditions"]), 0)

    @pytest.mark.standalone()
    def test_generate_therapeutic_response(self) -> None:
        """Test therapeutic response generation."""
        # Test with valid input
        result = self.service.generate_therapeutic_response(
            self.sample_text,
            context={"previous_sessions": 2}
        )
        self.assertIsInstance(result, dict)
        self.assertIn("response", result)
        self.assertIn("techniques", result)

        # Test with invalid input
        with self.assertRaises(InvalidRequestError):
            self.service.generate_therapeutic_response("")

    @pytest.mark.standalone()
    def test_assess_suicide_risk(self) -> None:
        """Test suicide risk assessment."""
        # Test with text indicating some risk
        result = self.service.assess_suicide_risk(self.sample_text)
        self.assertIsInstance(result, dict)
        self.assertIn("risk_level", result)
        self.assertIn("risk_factors", result)
        self.assertIn("recommendations", result)

        # Test with high-risk text
        high_risk_text = (
            "I can't take it anymore. I've written my note and made my plan. "
            "No one will miss me anyway. I'll be gone by tomorrow."
        )
        result = self.service.assess_suicide_risk(high_risk_text)
        self.assertEqual(result["risk_level"], "high")

        # Test with low-risk text
        low_risk_text = "I'm feeling great today. Life is wonderful."
        result = self.service.assess_suicide_risk(low_risk_text)
        self.assertEqual(result["risk_level"], "low")

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
        self.assertIsInstance(result, dict)
        self.assertIn("plan", result)
        self.assertIn("goals", result)
        self.assertIn("interventions", result)
        self.assertIn("timeline", result)

        # Test with invalid input
        with self.assertRaises(InvalidRequestError):
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
        self.assertIsInstance(result, dict)
        self.assertIn("themes", result)
        self.assertIn("patient_insights", result)
        self.assertIn("therapist_insights", result)
        self.assertIn("recommendations", result)

        # Test with invalid transcript
        with self.assertRaises(InvalidRequestError):
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
        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("progress", result)
        self.assertIn("goals", result)
        self.assertIn("recommendations", result)

        # Test with invalid input
        with self.assertRaises(InvalidRequestError):
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
            symptom_changes={"depression": "improved", "anxiety": "slightly improved"}
        )
        self.assertIsInstance(result, dict)
        self.assertIn("effectiveness", result)
        self.assertIn("side_effect_analysis", result)
        self.assertIn("recommendations", result)

        # Test with invalid input
        with self.assertRaises(InvalidRequestError):
            self.service.analyze_medication_response(
                medication="",
                dosage="",
                duration_days=0,
                side_effects=[],
                symptom_changes={}
            )

    @pytest.mark.standalone()
    def test_digital_twin_session_workflow(self) -> None:
        """Test the complete digital twin session workflow from creation to insights."""
        # Create a digital twin
        twin_result = self.service.generate_digital_twin(
            text_data=[self.sample_text],
            demographic_data={"age": 35, "gender": "female"},
            medical_history={"conditions": ["anxiety", "insomnia"]},
            treatment_history={"medications": ["escitalopram"]}
        )
        self.assertIn("digital_twin_id", twin_result)
        twin_id = twin_result["digital_twin_id"]

        # Create a session with the digital twin
        session_result = self.service.create_digital_twin_session(twin_id, session_type="therapy")
        self.assertIn("session_id", session_result)
        session_id = session_result["session_id"]

        # Get session details
        session_details = self.service.get_digital_twin_session(session_id)
        self.assertEqual(session_details["twin_id"], twin_id)
        self.assertEqual(session_details["status"], "active")

        # Send message to session
        message_result = self.service.send_message_to_session(session_id, "How can I manage my anxiety better?")
        self.assertIn("response", message_result)
        self.assertIn("messages", message_result)
        self.assertGreater(len(message_result["messages"]), 0)

        # End session
        end_result = self.service.end_digital_twin_session(session_id)
        self.assertEqual(end_result["status"], "completed")
        self.assertIn("summary", end_result)

        # Get session insights
        insights = self.service.get_session_insights(session_id)
        self.assertIn("insights", insights)
        self.assertIn("themes", insights["insights"])
        self.assertIn("recommendations", insights["insights"])