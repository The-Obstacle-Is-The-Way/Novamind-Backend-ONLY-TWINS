"""
Unit tests for MockMentaLLaMA service.

This module tests the mock implementation of the MentaLLaMA service,
ensuring it correctly implements the interface and provides consistent
behavior for testing purposes. The tests verify initialization, error handling,
and all core psychiatry analysis features.
"""

import pytest
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List

from app.core.exceptions import (
    InvalidConfigurationError,
    InvalidRequestError,
    ModelNotFoundError,
    ServiceUnavailableError,
)
from app.core.services.ml.mock import MockMentaLLaMA
from app.tests.unit.base_test_unit import (
    BaseUnitTest,
)  # Updated import path after rename


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
            "I wonder if life is worth living, but I wouldn't actually hurt myself.")

    def tearDown(self) -> None:
        """Clean up after each test."""
        if hasattr(self, "service") and self.service.is_healthy():
            self.service.shutdown()
            super().tearDown()

            def test_initialization(self) -> None:
        """Test initialization with valid and invalid configurations."""
        # Test default initialization
        service = MockMentaLLaMA()
        service.initialize({})
        self.assertTrue(service.is_healthy())

        # Test initialization with custom mock responses
        custom_responses = {
            "general": {
                "custom": True,
                "model_type": "general"}}
        service = MockMentaLLaMA()
        service.initialize({"mock_responses": custom_responses})
        self.assertTrue(service.is_healthy())

        # Test shutdown
        service.shutdown()
        self.assertFalse(service.is_healthy())

        # Test initialization failure
        service = MockMentaLLaMA()
        with self.assertRaises(InvalidConfigurationError):
            # Pass invalid config that would cause error during processing
            service.initialize({"mock_responses": "not-a-dict"})

            def test_process_with_invalid_inputs(self) -> None:
        """Test process method with invalid inputs ensuring proper error handling."""
        # Test empty text
        with self.assertRaises(InvalidRequestError):
            self.service.process("")

            # Test non-string text
            with self.assertRaises(InvalidRequestError):
            self.service.process(123)  # type: ignore

            # Test invalid model type
            with self.assertRaises(ModelNotFoundError):
            self.service.process("Some text", "nonexistent_model_type")

            # Test with uninitialized service
            uninitialized_service = MockMentaLLaMA()
            with self.assertRaises(ServiceUnavailableError):
            uninitialized_service.process("Some text")

            def test_process_returns_expected_structure(self) -> None:
        """Test that process returns the expected response structure with all required fields."""
        # Test general model (default)
        result = self.service.process(self.sample_text)
        self.assertIsInstance(result, dict)
        self.assertIn("model_type", result)
        self.assertEqual(result["model_type"], "general")
        self.assertIn("timestamp", result)
        self.assertIn("content", result)

        # Verify timestamp is recent ISO format
        timestamp = datetime.fromisoformat(result["timestamp"].rstrip("Z"))
        self.assertLess((datetime.now(UTC) - timestamp).total_seconds(), 10)

        # Test all available model types
        for model_type in [
            "depression_detection",
            "risk_assessment",
            "sentiment_analysis",
            "wellness_dimensions",
            "digital_twin",
        ]:
            result = self.service.process(self.sample_text, model_type)
            self.assertEqual(result["model_type"], model_type)

            def test_detect_depression(self) -> None:
        """Test depression detection functionality ensuring clinical metrics are present."""
        result = self.service.detect_depression(self.sample_text)
        self.assertIn("depression_signals", result)
        self.assertIn("severity", result["depression_signals"])
        self.assertIn("confidence", result["depression_signals"])
        self.assertIn("key_indicators", result["depression_signals"])
        self.assertIsInstance(
            result["depression_signals"]["key_indicators"], list)

        # Verify clinical recommendations
        self.assertIn("recommendations", result)
        self.assertIn("suggested_assessments", result["recommendations"])

        def test_assess_risk(self) -> None:
        """Test risk assessment functionality for self-harm detection."""
        # Test without specific risk type
        result = self.service.assess_risk(self.sample_text)
        self.assertIn("risk_assessment", result)
        self.assertIn("overall_risk_level", result["risk_assessment"])
        self.assertIn("identified_risks", result["risk_assessment"])

        # Test with specific risk type
        result = self.service.assess_risk(self.sample_text, "self-harm")
        self.assertIn("risk_assessment", result)
        # Check that only self-harm risks are included
        for risk in result["risk_assessment"]["identified_risks"]:
            self.assertEqual(risk["risk_type"], "self-harm")

            # Verify clinical recommendations exist
            self.assertIn("recommendations", result)

            def test_analyze_sentiment(self) -> None:
        """Test sentiment analysis functionality for emotional valence detection."""
        result = self.service.analyze_sentiment(self.sample_text)
        self.assertIn("sentiment", result)
        self.assertIn("emotions", result)
        self.assertIn("overall_score", result["sentiment"])
        self.assertIn("primary_emotions", result["emotions"])
        self.assertIsInstance(result["emotions"]["primary_emotions"], list)

        # Check emotional insights
        self.assertIn("analysis", result)
        self.assertIn("emotional_themes", result["analysis"])

        def test_analyze_wellness_dimensions(self) -> None:
        """Test wellness dimensions analysis functionality with comprehensive measures."""
        # Test without specific dimensions
        result = self.service.analyze_wellness_dimensions(self.sample_text)
        self.assertIn("wellness_dimensions", result)
        self.assertIsInstance(result["wellness_dimensions"], list)

        # Test with specific dimensions
        result = self.service.analyze_wellness_dimensions(
            self.sample_text, dimensions=["emotional", "social"]
        )
        self.assertIn("wellness_dimensions", result)
        dimensions = [dim["dimension"]
                      for dim in result["wellness_dimensions"]]
        self.assertIn("emotional", dimensions)

        # Ensure analysis and recommendations are provided
        self.assertIn("analysis", result)
        self.assertIn("recommendations", result)

    def test_digital_twin_session_workflow(self) -> None:
        """Test the complete digital twin session workflow from creation to insights."""
        # Create a digital twin
        twin_result = self.service.generate_digital_twin(
            text_data=[self.sample_text],
            demographic_data={"age": 35, "gender": "female"},
            medical_history={"conditions": ["anxiety", "insomnia"]},
            treatment_history={"medications": ["escitalopram"]},
        )
        self.assertIn("digital_twin_id", twin_result)
        twin_id = twin_result["digital_twin_id"]

        # Create a session with the digital twin
        session_result = self.service.create_digital_twin_session(
            twin_id, session_type="therapy"
        )
        self.assertIn("session_id", session_result)
        session_id = session_result["session_id"]

        # Get session details
        session_details = self.service.get_digital_twin_session(session_id)
        self.assertEqual(session_details["twin_id"], twin_id)
        self.assertEqual(session_details["status"], "active")

        # Send message to session
        message_result = self.service.send_message_to_session(
            session_id, "How can I manage my anxiety better?"
        )
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
