"""
Unit tests for Mock Digital Twin service.

This module tests the mock implementation of the Digital Twin service,
ensuring it correctly simulates patient digital twins and provides
realistic psychiatric session modeling for testing purposes.
"""

import pytest
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List

from app.core.exceptions import (
    InvalidConfigurationError,  
    InvalidRequestError,  
    ModelNotFoundError,  
    ServiceUnavailableError,  
    ResourceNotFoundError
)
from app.core.services.ml.mock_dt import MockDigitalTwinService
from app.tests.unit.base_test_unit import BaseUnitTest # Updated import path after rename


@pytest.mark.db_required()
class TestMockDigitalTwinService(BaseUnitTest):
    """
    Test suite for MockDigitalTwinService class.
    
    Tests comprehensive patient digital twin session workflows including
    creation, sessions, message exchange, and clinical insights generation.
    """
    
    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        super().setUp()
        self.service = MockDigitalTwinService()
        self.service.initialize({})
        
        self.patient_data = {
            "patient_id": "test-patient-123",
            "demographic_data": {
                "age": 35,
                "gender": "female",
                "ethnicity": "caucasian"
            },
            "clinical_data": {
                "diagnoses": ["Major Depressive Disorder", "Generalized Anxiety Disorder"],
                "medications": ["sertraline", "buspirone"],
                "treatment_history": [
                    {"type": "CBT", "duration": "6 months", "outcome": "moderate improvement"}
                ]
            },
            "biometric_data": {
                "sleep_quality": [6, 5, 7, 4, 6],
                "heart_rate": [72, 78, 75, 80, 73],
                "activity_level": [3500, 2800, 4200, 3000, 3700]
            }
        }
        
        # Create a twin to use in tests
        result = self.service.create_digital_twin(self.patient_data)
        self.twin_id = result["twin_id"]
        
        # Sample message for testing
        self.sample_message = "I've been feeling anxious in social situations lately."

    def tearDown(self) -> None:
        """Clean up after each test."""
        if hasattr(self, 'service') and self.service.is_healthy():
            self.service.shutdown()
        super().tearDown()

    def test_initialization(self) -> None:
        """Test service initialization with various configurations."""
        # Test default initialization
        service = MockDigitalTwinService()
        service.initialize({})
        self.assert True(service.is_healthy())
        
        # Test with custom configuration
        custom_config = {
            "response_style": "detailed",
            "session_duration_minutes": 60
        }
        service = MockDigitalTwinService()
        service.initialize(custom_config)
        self.assert True(service.is_healthy())
        
        # Test initialization with invalid configuration
        service = MockDigitalTwinService()
        with self.assert Raises(InvalidConfigurationError):
            service.initialize({"response_style": 123})  # type: ignore
            
        # Test shutdown
        service.shutdown()
        self.assert False(service.is_healthy())

    def test_create_session(self) -> None:
        """Test creating a digital twin therapy session."""
        # Test with different session types
        for session_type in ["therapy", "assessment", "medication_review"]:
            result = self.service.create_session(
                twin_id=self.twin_id,
                session_type=session_type
            )
            
            # Verify result structure
            self.assert In("session_id", result)
            self.assert In("twin_id", result)
            self.assert In("session_type", result)
            self.assert In("start_time", result)
            self.assert In("status", result)
            
            # Verify values
            self.assert Equal(result["twin_id"], self.twin_id)
            self.assert Equal(result["session_type"], session_type)
            self.assert Equal(result["status"], "active")
            
            # Check that start_time is a recent timestamp
            start_time = datetime.fromisoformat(result["start_time"].rstrip("Z"))
            self.assert Less((datetime.now(UTC) - start_time).total_seconds(), 10)

    def test_get_session(self) -> None:
        """Test retrieving a digital twin therapy session."""
        # Create a session
        create_result = self.service.create_session(
            twin_id=self.twin_id,
            session_type="therapy"
        )
        session_id = create_result["session_id"]
        
        # Get the session
        get_result = self.service.get_session(session_id)
        
        # Verify result structure and values
        self.assert Equal(get_result["session_id"], session_id)
        self.assert Equal(get_result["twin_id"], self.twin_id)
        self.assert Equal(get_result["status"], "active")
        self.assert In("messages", get_result)
        self.assert IsInstance(get_result["messages"], list)
        
        # Test getting non-existent session
        with self.assert Raises(ResourceNotFoundError):
            self.service.get_session("nonexistent-session-id")

    def test_send_message(self) -> None:
        """Test sending a message to a digital twin therapy session."""
        # Create a session
        create_result = self.service.create_session(
            twin_id=self.twin_id,
            session_type="therapy"
        )
        session_id = create_result["session_id"]
        
        # Send a message
        message_result = self.service.send_message(
            session_id=session_id,
            message=self.sample_message
        )
        
        # Verify result structure
        self.assert In("response", message_result)
        self.assert In("messages", message_result)
        self.assert IsInstance(message_result["messages"], list)
        self.assert Equal(len(message_result["messages"]), 2)  # User message + twin response
        
        # Verify message content
        self.assert Equal(message_result["messages"][0]["content"], self.sample_message)
        self.assert Equal(message_result["messages"][0]["sender"], "user")
        self.assert Equal(message_result["messages"][1]["sender"], "twin")
        
        # Test sending to a non-existent session
        with self.assert Raises(ResourceNotFoundError):
            self.service.send_message(
                session_id="nonexistent-session-id",
                message=self.sample_message
            )

    def test_message_response_types(self) -> None:
        """Test different types of responses based on message content."""
        # Create a session
        create_result = self.service.create_session(
            twin_id=self.twin_id,
            session_type="therapy"
        )
        session_id = create_result["session_id"]
        
        # Test different message types
        test_messages = {
            "depression": "I've been feeling so hopeless lately.",
            "anxiety": "I'm constantly worried about everything.",
            "medication": "I'm not sure if my medication is working.",
            "sleep": "I haven't been sleeping well.",
            "exercise": "I've started walking every day."
        }
        
        for topic, message in test_messages.items():
            result = self.service.send_message(session_id=session_id, message=message)
            self.assert In("response", result)
            response = result["response"]
            
            # Response should be relevant to the topic
            self.assert True(
                any(keyword in response.lower() for keyword in [topic, topic[:-1]]),
                f"Response '{response}' not relevant to topic '{topic}'"
            )

    def test_end_session(self) -> None:
        """Test ending a digital twin therapy session."""
        # Create a session
        create_result = self.service.create_session(
            twin_id=self.twin_id,
            session_type="therapy"
        )
        session_id = create_result["session_id"]
        
        # Send a message to have some content
        self.service.send_message(
            session_id=session_id,
            message=self.sample_message
        )
        
        # End the session
        end_result = self.service.end_session(session_id)
        
        # Verify result structure
        self.assert In("session_id", end_result)
        self.assert In("status", end_result)
        self.assert In("duration", end_result)
        self.assert In("summary", end_result)
        
        # Verify values
        self.assert Equal(end_result["session_id"], session_id)
        self.assert Equal(end_result["status"], "completed")
        self.assert In("minutes", end_result["duration"])
        
        # Test ending a non-existent session
        with self.assert Raises(ResourceNotFoundError):
            self.service.end_session("nonexistent-session-id")
        
        # Test ending an already ended session
        with self.assert Raises(InvalidRequestError):
            self.service.end_session(session_id)

    def test_get_insights(self) -> None:
        """Test getting insights from a completed digital twin session."""
        # Create and complete a session with some messages
        session_result = self.service.create_session(
            twin_id=self.twin_id,
            session_type="therapy"
        )
        session_id = session_result["session_id"]
        
        # Send multiple messages to generate meaningful insights
        messages = [
            "I've been feeling anxious about work lately.",
            "My sleep has been disrupted, and I'm tired all the time.",
            "I tried the breathing exercises you suggested last time.",
            "I'm still taking my medication regularly."
        ]
        
        for message in messages:
            self.service.send_message(session_id=session_id, message=message)
        
        # End the session
        self.service.end_session(session_id)
        
        # Get insights
        insights_result = self.service.get_insights(session_id)
        
        # Verify result structure
        self.assert In("session_id", insights_result)
        self.assert In("insights", insights_result)
        self.assert In("themes", insights_result["insights"])
        self.assert In("sentiment_analysis", insights_result["insights"])
        self.assert In("recommendations", insights_result["insights"])
        
        # Verify values
        self.assert Equal(insights_result["session_id"], session_id)
        self.assert IsInstance(insights_result["insights"]["themes"], list)
        self.assert IsInstance(insights_result["insights"]["recommendations"], list)

    def test_mood_insights(self) -> None:
        """Test mood tracking insights from digital twin sessions."""
        # Create and complete multiple sessions to track mood
        mood_messages = {
            "session1": ["I feel pretty good today", "Work went well"],
            "session2": ["I'm feeling down today", "Everything seems hopeless"],
            "session3": ["I'm feeling a bit better", "Still struggling but trying"]
        }
        
        session_ids = []
        for session_name, messages in mood_messages.items():
            # Create session
            session_result = self.service.create_session(
                twin_id=self.twin_id,
                session_type="therapy"
            )
            session_id = session_result["session_id"]
            session_ids.append(session_id)
            
            # Send messages
            for message in messages:
                self.service.send_message(session_id=session_id, message=message)
            
            # End session
            self.service.end_session(session_id)
        
        # Get mood insights for the patient
        mood_insights = self.service.get_mood_insights(self.twin_id)
        
        # Verify result structure
        self.assert In("twin_id", mood_insights)
        self.assert In("mood_data", mood_insights)
        self.assert In("trend", mood_insights)
        self.assert In("analysis", mood_insights)
        
        # Verify values
        self.assert Equal(mood_insights["twin_id"], self.twin_id)
        self.assert IsInstance(mood_insights["mood_data"], list)
        self.assert GreaterEqual(len(mood_insights["mood_data"]), 3)  # One per session

    def test_activity_insights(self) -> None:
        """Test activity tracking insights from digital twin."""
        # Generate activity insights
        activity_insights = self.service.get_activity_insights(self.twin_id)
        
        # Verify result structure
        self.assert In("twin_id", activity_insights)
        self.assert In("activity_data", activity_insights)
        self.assert In("averages", activity_insights)
        self.assert In("trends", activity_insights)
        self.assert In("recommendations", activity_insights)

    def test_sleep_insights(self) -> None:
        """Test sleep tracking insights from digital twin."""
        # Generate sleep insights
        sleep_insights = self.service.get_sleep_insights(self.twin_id)
        
        # Verify result structure
        self.assert In("twin_id", sleep_insights)
        self.assert In("sleep_data", sleep_insights)
        self.assert In("average_duration", sleep_insights)
        self.assert In("quality_trend", sleep_insights)
        self.assert In("patterns", sleep_insights)
        self.assert In("recommendations", sleep_insights)

    def test_medication_insights(self) -> None:
        """Test medication insights from digital twin."""
        # Generate medication insights
        medication_insights = self.service.get_medication_insights(self.twin_id)
        
        # Verify result structure
        self.assert In("twin_id", medication_insights)
        self.assert In("medications", medication_insights)
        self.assert In("adherence", medication_insights)
        self.assert In("reported_effects", medication_insights)
        self.assert In("recommendations", medication_insights)

    def test_treatment_insights(self) -> None:
        """Test treatment response insights from digital twin."""
        # Generate treatment insights
        treatment_insights = self.service.get_treatment_insights(self.twin_id)
        
        # Verify result structure
        self.assert In("twin_id", treatment_insights)
        self.assert In("treatments", treatment_insights)
        self.assert In("efficacy", treatment_insights)
        self.assert In("progress", treatment_insights)
        self.assert In("recommendations", treatment_insights)