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
from app.tests.unit.base_test_unit import BaseUnitTest # Updated import path after rename


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
        if hasattr(self, 'service') and self.service.is_healthy():
            self.service.shutdown()
        super().tearDown()

    def test_initialization(self) -> None:
        """Test initialization with valid and invalid configurations."""
        # Test default initialization
        service = MockMentaLLaMA()
        service.initialize({})
        self.assert True(service.is_healthy())
        
        # Test initialization with custom mock responses
        custom_responses = {
            "general": {"custom": True, "model_type": "general"}
        }
        service = MockMentaLLaMA()
        service.initialize({"mock_responses": custom_responses})
        self.assert True(service.is_healthy())
        
        # Test shutdown
        service.shutdown()
        self.assert False(service.is_healthy())
        
        # Test initialization failure
        service = MockMentaLLaMA()
        with self.assert Raises(InvalidConfigurationError):
            # Pass invalid config that would cause error during processing
            service.initialize({"mock_responses": "not-a-dict"})

    def test_process_with_invalid_inputs(self) -> None:
        """Test process method with invalid inputs ensuring proper error handling."""
        # Test empty text
        with self.assert Raises(InvalidRequestError):
            self.service.process("")
        
        # Test non-string text
        with self.assert Raises(InvalidRequestError):
            self.service.process(123)  # type: ignore
        
        # Test invalid model type
        with self.assert Raises(ModelNotFoundError):
            self.service.process("Some text", "nonexistent_model_type")
        
        # Test with uninitialized service
        uninitialized_service = MockMentaLLaMA()
        with self.assert Raises(ServiceUnavailableError):
            uninitialized_service.process("Some text")

    def test_process_returns_expected_structure(self) -> None:
        """Test that process returns the expected response structure with all required fields."""
        # Test general model (default)
        result = self.service.process(self.sample_text)
        self.assert IsInstance(result, dict)
        self.assert In("model_type", result)
        self.assert Equal(result["model_type"], "general")
        self.assert In("timestamp", result)
        self.assert In("content", result)
        
        # Verify timestamp is recent ISO format
        timestamp = datetime.fromisoformat(result["timestamp"].rstrip("Z"))
        self.assert Less((datetime.now(UTC) - timestamp).total_seconds(), 10)
        
        # Test all available model types
        for model_type in ["depression_detection", "risk_assessment", "sentiment_analysis"
                        "wellness_dimensions", "digital_twin"]:
            result = self.service.process(self.sample_text, model_type)
            self.assert Equal(result["model_type"], model_type)

    def test_detect_depression(self) -> None:
        """Test depression detection functionality ensuring clinical metrics are present."""
        result = self.service.detect_depression(self.sample_text)
        self.assert In("depression_signals", result)
        self.assert In("severity", result["depression_signals"])
        self.assert In("confidence", result["depression_signals"])
        self.assert In("key_indicators", result["depression_signals"])
        self.assert IsInstance(result["depression_signals"]["key_indicators"], list)
        
        # Verify clinical recommendations
        self.assert In("recommendations", result)
        self.assert In("suggested_assessments", result["recommendations"])

    def test_assess_risk(self) -> None:
        """Test risk assessment functionality for self-harm detection."""
        # Test without specific risk type
        result = self.service.assess_risk(self.sample_text)
        self.assert In("risk_assessment", result)
        self.assert In("overall_risk_level", result["risk_assessment"])
        self.assert In("identified_risks", result["risk_assessment"])
        
        # Test with specific risk type
        result = self.service.assess_risk(self.sample_text, "self-harm")
        self.assert In("risk_assessment", result)
        # Check that only self-harm risks are included
        for risk in result["risk_assessment"]["identified_risks"]:
            self.assert Equal(risk["risk_type"], "self-harm")
            
        # Verify clinical recommendations exist
        self.assert In("recommendations", result)

    def test_analyze_sentiment(self) -> None:
        """Test sentiment analysis functionality for emotional valence detection."""
        result = self.service.analyze_sentiment(self.sample_text)
        self.assert In("sentiment", result)
        self.assert In("emotions", result)
        self.assert In("overall_score", result["sentiment"])
        self.assert In("primary_emotions", result["emotions"])
        self.assert IsInstance(result["emotions"]["primary_emotions"], list)
        
        # Check emotional insights
        self.assert In("analysis", result)
        self.assert In("emotional_themes", result["analysis"])

    def test_analyze_wellness_dimensions(self) -> None:
        """Test wellness dimensions analysis functionality with comprehensive measures."""
        # Test without specific dimensions
        result = self.service.analyze_wellness_dimensions(self.sample_text)
        self.assert In("wellness_dimensions", result)
        self.assert IsInstance(result["wellness_dimensions"], list)
        
        # Test with specific dimensions
        result = self.service.analyze_wellness_dimensions(
            self.sample_text, dimensions=["emotional", "social"]
        )
        self.assert In("wellness_dimensions", result)
        dimensions = [dim["dimension"] for dim in result["wellness_dimensions"]]
        self.assert In("emotional", dimensions)
        
        # Ensure analysis and recommendations are provided
        self.assert In("analysis", result)
        self.assert In("recommendations", result)

    def test_digital_twin_session_workflow(self) -> None:
        """Test the complete digital twin session workflow from creation to insights."""
        # Create a digital twin
        twin_result = self.service.generate_digital_twin(
            text_data=[self.sample_text],
            demographic_data={"age": 35, "gender": "female"},
            medical_history={"conditions": ["anxiety", "insomnia"]},
            treatment_history={"medications": ["escitalopram"]}
        )
        self.assert In("digital_twin_id", twin_result)
        twin_id = twin_result["digital_twin_id"]
        
        # Create a session with the digital twin
        session_result = self.service.create_digital_twin_session(
            twin_id, session_type="therapy"
        )
        self.assert In("session_id", session_result)
        session_id = session_result["session_id"]
        
        # Get session details
        session_details = self.service.get_digital_twin_session(session_id)
        self.assert Equal(session_details["twin_id"], twin_id)
        self.assert Equal(session_details["status"], "active")
        
        # Send message to session
        message_result = self.service.send_message_to_session(
            session_id, "How can I manage my anxiety better?"
        )
        self.assert In("response", message_result)
        self.assert In("messages", message_result)
        self.assert Greater(len(message_result["messages"]), 0)
        
        # End session
        end_result = self.service.end_digital_twin_session(session_id)
        self.assert Equal(end_result["status"], "completed")
        self.assert In("summary", end_result)
        
        # Get session insights
        insights = self.service.get_session_insights(session_id)
        self.assert In("insights", insights)
        self.assert In("themes", insights["insights"])
        self.assert In("recommendations", insights["insights"])