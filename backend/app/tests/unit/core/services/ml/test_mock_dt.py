# -*- coding: utf-8 -*-
"""
Unit tests for Mock Digital Twin Service.

This module tests the mock implementation of the Digital Twin service
to ensure it correctly simulates patient interaction and provides consistent
responses for testing purposes.
"""

import pytest
import time
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List
import re
import uuid

from app.core.exceptions import (
    InvalidConfigurationError,  
    InvalidRequestError,  
    ServiceUnavailableError,  
)
from app.core.services.ml.mock_dt import MockDigitalTwinService

# Import the correct interface
from app.core.services.ml.interface import DigitalTwinInterface


@pytest.mark.db_required()
class TestMockDigitalTwinService:
    """Test suite for MockDigitalTwinService class."""

    @pytest.fixture
    def mock_service(self) -> MockDigitalTwinService:
        """Create and initialize a MockDigitalTwinService instance."""
        service = MockDigitalTwinService()
        service.initialize({"mock_config": True})
        return service

    @pytest.fixture
    def sample_patient_id(self) -> str:
        """Create a sample patient ID for testing."""
        
    return f"test-patient-{uuid.uuid4()}"

    def test_initialization(self):
        """Test initialization with valid and invalid configurations."""
        # Test default initialization
        service = MockDigitalTwinService()
        service.initialize({"mock_config": True})
        assert service.is_healthy()
        
        # Test shutdown
        service.shutdown()
        assert not service.is_healthy()
        
        # Test initialization with empty config
        service = MockDigitalTwinService()
        with pytest.raises(InvalidConfigurationError):
            service.initialize({})
        assert not service.is_healthy()
        
        # Test initialization with invalid config
        service = MockDigitalTwinService()
        with pytest.raises(InvalidConfigurationError):
            service.initialize("not-a-dict")
        assert not service.is_healthy()

    def test_create_session(self, mock_service, sample_patient_id):
        """Test creating a new Digital Twin session."""
        # Test with minimal parameters
        result = mock_service.create_session(sample_patient_id)
        assert "session_id" in result
        assert result["patient_id"] == sample_patient_id
        assert "created_at" in result
        assert "expires_at" in result
        assert "processing_time" in result
        assert "metadata" in result
        assert result["metadata"]["mock"] is True
        
        # Test with additional context
        context = {"demographic": {"age": 35, "gender": "female"}}
        result = mock_service.create_session(sample_patient_id, context=context)
        assert "session_id" in result
        
        # Test with uninitialized service
        uninitialized_service = MockDigitalTwinService()
        with pytest.raises(ServiceUnavailableError):
            uninitialized_service.create_session(sample_patient_id)

    def test_get_session(self, mock_service, sample_patient_id):
        """Test retrieving a Digital Twin session."""
        # Create a session first
        create_result = mock_service.create_session(sample_patient_id)
        session_id = create_result["session_id"]
        
        # Get the session
        result = mock_service.get_session(session_id)
        assert result["session_id"] == session_id
        assert result["patient_id"] == sample_patient_id
        assert "created_at" in result
        assert "expires_at" in result
        assert "history" in result
        assert "context" in result
        assert "metadata" in result
        
        # Test getting a non-existent session (should create a new session)
        non_existent_id = str(uuid.uuid4())
        result = mock_service.get_session(non_existent_id)
        assert "session_id" in result  # New session created
        
        # Test with uninitialized service
        uninitialized_service = MockDigitalTwinService()
        with pytest.raises(ServiceUnavailableError):
            uninitialized_service.get_session(session_id)

    def test_send_message(self, mock_service, sample_patient_id):
        """Test sending messages to a Digital Twin session."""
        # Create a session first
        create_result = mock_service.create_session(sample_patient_id)
        session_id = create_result["session_id"]
        
        # Test sending a greeting message
        message = "Hello, how are you?"
        result = mock_service.send_message(session_id, message)
        assert result["session_id"] == session_id
        assert result["patient_id"] == sample_patient_id
        assert result["message"] == message
        assert "response" in result
        assert len(result["response"]) > 0
        assert "timestamp" in result
        assert "processing_time" in result
        assert "metadata" in result
        
        # Get session to check history
        session = mock_service.get_session(session_id)
        assert len(session["history"]) == 2  # User message and response
        
        # Test sending a medication-related message
        message = "I have a question about my medication"
        result = mock_service.send_message(session_id, message)
        assert "medication" in result["response"].lower()
        
        # Test sending a symptom-related message
        message = "I'm feeling very anxious today"
        result = mock_service.send_message(session_id, message)
        assert result["response"] is not None
        
        # Test sending to a non-existent session (should create a new session)
        non_existent_id = str(uuid.uuid4())
        result = mock_service.send_message(non_existent_id, "Test message")
        assert "session_id" in result  # New session created
        
        # Test with uninitialized service
        uninitialized_service = MockDigitalTwinService()
        with pytest.raises(ServiceUnavailableError):
            uninitialized_service.send_message(session_id, "Test message")

    def test_message_response_types(self, mock_service, sample_patient_id):
        """Test different types of message responses."""
        # Create a session
        create_result = mock_service.create_session(sample_patient_id)
        session_id = create_result["session_id"]
        
        # Test greeting messages
        for greeting in ["hello", "hi", "hey", "greetings"]:
            result = mock_service.send_message(session_id, greeting)
            assert "hello" in result["response"].lower()
        
        # Test "how are you" message
        result = mock_service.send_message(session_id, "How are you?")
        assert "how are you feeling" in result["response"].lower()
        
        # Test medication questions
        for med_term in ["medication", "meds", "pills", "prescription"]:
            result = mock_service.send_message(session_id, f"Question about my {med_term}")
            assert "medication" in result["response"].lower()
        
        # Test appointment questions
        for appt_term in ["appointment", "schedule", "visit", "doctor"]:
            result = mock_service.send_message(session_id, f"Need to {appt_term}")
            assert "appointment" in result["response"].lower()
            assert re.search(r"\b[A-Z][a-z]+day, [A-Z][a-z]+ \d+\b", result["response"])  # Date format
        
        # Test symptom questions
        for symptom_term in ["symptom", "feeling", "pain", "hurt", "sick"]:
            result = mock_service.send_message(session_id, f"I'm {symptom_term}")
            assert "symptom" in result["response"].lower() or "feeling" in result["response"].lower()
        
        # Test wellness questions
        for wellness_term in ["wellness", "exercise", "diet", "sleep", "stress"]:
            result = mock_service.send_message(session_id, f"About my {wellness_term}")
            assert "wellness" in result["response"].lower() or "sleep" in result["response"].lower()
        
        # Test therapy questions
        for therapy_term in ["therapy", "therapist", "counseling", "counselor"]:
            result = mock_service.send_message(session_id, f"My {therapy_term}")
            assert "therapy" in result["response"].lower()

    def test_end_session(self, mock_service, sample_patient_id):
        """Test ending a Digital Twin session."""
        # Create a session first
        create_result = mock_service.create_session(sample_patient_id)
        session_id = create_result["session_id"]
        
        # End the session
        result = mock_service.end_session(session_id)
        assert result["session_id"] == session_id
        assert result["patient_id"] == sample_patient_id
        assert "ended_at" in result
        assert result["metadata"]["status"] == "ended"
        
        # Verify session no longer exists
        with pytest.raises(InvalidRequestError):
            mock_service.end_session(session_id)
        
        # Test ending a non-existent session
        non_existent_id = str(uuid.uuid4())
        with pytest.raises(InvalidRequestError):
            mock_service.end_session(non_existent_id)
        
        # Test with uninitialized service
        uninitialized_service = MockDigitalTwinService()
        with pytest.raises(ServiceUnavailableError):
            uninitialized_service.end_session(session_id)

    def test_get_insights(self, mock_service, sample_patient_id):
        """Test getting Digital Twin insights."""
        # Test with default parameters
        result = mock_service.get_insights(sample_patient_id)
        assert result["patient_id"] == sample_patient_id
        assert result["insight_type"] == "all"
        assert result["time_period"] == "last_30_days"
        assert "generated_at" in result
        assert "insights" in result
        assert "processing_time" in result
        assert "metadata" in result
        
        # Verify structure of all insights
        insights = result["insights"]
        assert "mood" in insights
        assert "activity" in insights
        assert "sleep" in insights
        assert "medication" in insights
        assert "treatment" in insights
        assert "summary" in insights
        assert "overall_status" in insights["summary"]
        assert "key_observations" in insights["summary"]
        assert "recommendations" in insights["summary"]
        
        # Test specific insight types
        for insight_type in ["mood", "activity", "sleep", "medication", "treatment"]:
            result = mock_service.get_insights(sample_patient_id, insight_type=insight_type)
            assert result["insight_type"] == insight_type
            assert "data" in result["insights"]
        
        # Test different time periods
        result = mock_service.get_insights(sample_patient_id, time_period="last_7_days")
        assert result["time_period"] == "last_7_days"
        
        # Test with uninitialized service
        uninitialized_service = MockDigitalTwinService()
        with pytest.raises(ServiceUnavailableError):
            uninitialized_service.get_insights(sample_patient_id)

    def test_mood_insights(self, mock_service, sample_patient_id):
        """Test mood insights specifically."""
        result = mock_service.get_insights(sample_patient_id, insight_type="mood")
        mood_data = result["insights"]["data"]
        
        # Verify structure
        assert "entries" in mood_data
        assert len(mood_data["entries"]) > 0
        assert "average_mood" in mood_data
        assert "mood_trend" in mood_data
        assert "mood_variability" in mood_data
        
        # Verify entries format
        first_entry = mood_data["entries"][0]
        assert "date" in first_entry
        assert "mood_value" in first_entry
        assert "mood_label" in first_entry
        assert "factors" in first_entry
        
        # Verify mood mapping
        mood_labels = [entry["mood_label"] for entry in mood_data["entries"]]
        for label in mood_labels:
            assert label in ["very negative", "negative", "neutral", "positive", "very positive"]

    def test_activity_insights(self, mock_service, sample_patient_id):
        """Test activity insights specifically."""
        result = mock_service.get_insights(sample_patient_id, insight_type="activity")
        activity_data = result["insights"]["data"]
        
        # Verify structure
        assert "daily_activity" in activity_data
        assert len(activity_data["daily_activity"]) > 0
        assert "activity_trend" in activity_data
        assert "activity_recommendations" in activity_data
        
        # Verify daily activity format
        first_entry = activity_data["daily_activity"][0]
        assert "date" in first_entry
        assert "steps" in first_entry
        assert "active_minutes" in first_entry
        assert "activity_level" in first_entry

    def test_sleep_insights(self, mock_service, sample_patient_id):
        """Test sleep insights specifically."""
        result = mock_service.get_insights(sample_patient_id, insight_type="sleep")
        sleep_data = result["insights"]["data"]
        
        # Verify structure
        assert "sleep_records" in sleep_data
        assert len(sleep_data["sleep_records"]) > 0
        assert "average_sleep_duration" in sleep_data
        assert "sleep_quality_trend" in sleep_data
        assert "sleep_recommendations" in sleep_data
        
        # Verify sleep records format
        first_entry = sleep_data["sleep_records"][0]
        assert "date" in first_entry
        assert "duration_hours" in first_entry
        assert "quality" in first_entry
        assert "interruptions" in first_entry

    def test_medication_insights(self, mock_service, sample_patient_id):
        """Test medication insights specifically."""
        result = mock_service.get_insights(sample_patient_id, insight_type="medication")
        med_data = result["insights"]["data"]
        
        # Verify structure
        assert "medications" in med_data
        assert len(med_data["medications"]) > 0
        assert "adherence_rate" in med_data
        assert "side_effects" in med_data
        assert "medication_recommendations" in med_data
        
        # Verify medication format
        first_med = med_data["medications"][0]
        assert "name" in first_med
        assert "dosage" in first_med
        assert "adherence" in first_med
        assert "reported_effects" in first_med

    def test_treatment_insights(self, mock_service, sample_patient_id):
        """Test treatment insights specifically."""
        result = mock_service.get_insights(sample_patient_id, insight_type="treatment")
        treatment_data = result["insights"]["data"]
        
        # Verify structure
        assert "treatment_plan" in treatment_data
        assert "progress" in treatment_data
        assert "engagement" in treatment_data
        assert "treatment_recommendations" in treatment_data
        
        # Verify treatment plan format
        assert "therapies" in treatment_data["treatment_plan"]
        assert "goals" in treatment_data["treatment_plan"]
        assert len(treatment_data["treatment_plan"]["therapies"]) > 0
        assert len(treatment_data["treatment_plan"]["goals"]) > 0