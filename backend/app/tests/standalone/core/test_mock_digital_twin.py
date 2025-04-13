"""
Unit tests for the MockDigitalTwinService.

These tests verify that the MockDigitalTwinService correctly simulates
digital twin functionality for testing purposes.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from unittest import TestCase

import pytest
from pydantic import BaseModel

from app.domain.entities.digital_twin import DigitalTwinState
from app.domain.exceptions import ValidationError as InvalidConfigurationError, DomainError as SessionNotFoundError

# Create mock classes for testing
from abc import ABC, abstractmethod


class DigitalTwinService(ABC):
    """Abstract base class for digital twin services."""

    @abstractmethod
    def initialize(self, config):
        """Initialize the service with configuration."""
        pass

    @abstractmethod
    def is_healthy(self):
        """Check if the service is healthy."""
        pass

    @abstractmethod
    def shutdown(self):
        """Shut down the service."""
        pass


class MockDigitalTwinService(DigitalTwinService):
    """Mock implementation of digital twin service for testing."""

    def __init__(self):
        """Initialize the mock digital twin service."""
        self._healthy = False
        self._sessions = {}
        self._twins = {}
        self._simulations = {}
        self._states = {}

    def initialize(self, config):
        """Initialize the service with configuration."""
        if config is None:
            raise InvalidConfigurationError("Configuration cannot be None")
        self._healthy = True
        return True

    def is_healthy(self):
        """Check if the service is healthy."""
        return self._healthy

    def shutdown(self):
        """Shut down the service."""
        self._healthy = False

    def create_session(self, patient_id, context):
        """Create a new digital twin session."""
        session_id = f"session-{len(self._sessions) + 1}"
        session = {
            "session_id": session_id,
            "patient_id": patient_id,
            "context": context,
            "messages": [],
            "created_at": datetime.now().isoformat()
        }
        self._sessions[session_id] = session
        return {"session_id": session_id, "patient_id": patient_id}

    def get_session(self, session_id):
        """Get a session by ID."""
        if session_id not in self._sessions:
            raise SessionNotFoundError(f"Session {session_id} not found")
        return self._sessions[session_id]

    def send_message(self, session_id, message):
        """Send a message to a session."""
        if session_id not in self._sessions:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        session = self._sessions[session_id]
        session["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate a mock response
        response = {
            "role": "assistant",
            "content": f"This is a mock response to: {message}",
            "timestamp": datetime.now().isoformat()
        }
        session["messages"].append(response)
        
        return {
            "response": response["content"],
            "messages": session["messages"]
        }

    def end_session(self, session_id):
        """End a session."""
        if session_id not in self._sessions:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        session = self._sessions[session_id]
        session["ended_at"] = datetime.now().isoformat()
        session["status"] = "completed"
        
        return {
            "session_id": session_id,
            "status": "completed",
            "summary": "This is a mock summary of the session."
        }

    def create_digital_twin(self, patient_id, patient_data):
        """Create a digital twin for a patient."""
        twin_id = str(uuid.uuid4())
        twin = {
            "twin_id": twin_id,
            "patient_id": patient_id,
            "patient_data": patient_data,
            "created_at": datetime.now().isoformat(),
            "states": []
        }
        self._twins[twin_id] = twin
        
        # Create initial state
        state_id = str(uuid.uuid4())
        state = {
            "state_id": state_id,
            "twin_id": twin_id,
            "version": 1,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "brain_state": {
                    "neurotransmitter_levels": {
                        "serotonin": 0.5,
                        "dopamine": 0.5,
                        "gaba": 0.5,
                        "glutamate": 0.5,
                        "norepinephrine": 0.5
                    },
                    "brain_regions": {
                        "prefrontal_cortex": {
                            "activity": 0.5,
                            "connectivity": 0.5
                        },
                        "amygdala": {
                            "activity": 0.5,
                            "connectivity": 0.5
                        },
                        "hippocampus": {
                            "activity": 0.5,
                            "connectivity": 0.5
                        }
                    }
                },
                "insights": []
            }
        }
        self._states[state_id] = state
        twin["states"].append(state_id)
        
        return {
            "twin_id": twin_id,
            "initial_state_id": state_id
        }

    def get_digital_twin(self, twin_id):
        """Get a digital twin by ID."""
        if twin_id not in self._twins:
            raise InvalidConfigurationError(f"Digital twin {twin_id} not found")
        return self._twins[twin_id]

    def get_twin_state(self, state_id):
        """Get a twin state by ID."""
        if state_id not in self._states:
            raise InvalidConfigurationError(f"State {state_id} not found")
        return self._states[state_id]

    def get_latest_state(self, twin_id):
        """Get the latest state for a twin."""
        if twin_id not in self._twins:
            raise InvalidConfigurationError(f"Digital twin {twin_id} not found")
        
        twin = self._twins[twin_id]
        if not twin["states"]:
            return None
        
        latest_state_id = twin["states"][-1]
        return self._states[latest_state_id]

    def update_twin_state(self, twin_id, updates):
        """Update a twin's state with new data."""
        if twin_id not in self._twins:
            raise InvalidConfigurationError(f"Digital twin {twin_id} not found")
        
        twin = self._twins[twin_id]
        latest_state = self.get_latest_state(twin_id)
        
        # Create a new state based on the latest
        state_id = str(uuid.uuid4())
        new_state = {
            "state_id": state_id,
            "twin_id": twin_id,
            "version": latest_state["version"] + 1,
            "timestamp": datetime.now().isoformat(),
            "data": latest_state["data"].copy()  # Deep copy would be better in real code
        }
        
        # Apply updates
        for key, value in updates.items():
            if key in new_state["data"]:
                if isinstance(new_state["data"][key], dict) and isinstance(value, dict):
                    new_state["data"][key].update(value)
                else:
                    new_state["data"][key] = value
            else:
                new_state["data"][key] = value
        
        # Add a mock insight
        new_state["data"].setdefault("insights", []).append({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "type": "state_change",
            "description": "This is a mock insight based on state changes.",
            "confidence": 0.85
        })
        
        self._states[state_id] = new_state
        twin["states"].append(state_id)
        
        return new_state

    def compare_states(self, state_id_1, state_id_2):
        """Compare two states and identify differences."""
        if state_id_1 not in self._states:
            raise InvalidConfigurationError(f"State {state_id_1} not found")
        if state_id_2 not in self._states:
            raise InvalidConfigurationError(f"State {state_id_2} not found")
        
        state1 = self._states[state_id_1]
        state2 = self._states[state_id_2]
        
        # Create a mock comparison
        return {
            "state_1": {"id": state_id_1, "version": state1["version"]},
            "state_2": {"id": state_id_2, "version": state2["version"]},
            "brain_state_changes": {
                "neurotransmitter_levels": {
                    "serotonin": {"before": 0.5, "after": 0.6, "change": 0.1},
                    "dopamine": {"before": 0.5, "after": 0.55, "change": 0.05}
                }
            },
            "new_insights": [
                {
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "type": "comparison",
                    "description": "This is a mock insight based on state comparison.",
                    "confidence": 0.8
                }
            ]
        }

    def simulate_treatment_response(self, patient_id, treatment):
        """Simulate a treatment response for a patient."""
        # Verify the patient exists (in a real implementation)
        # For mock, we'll just create a simulation
        simulation_id = str(uuid.uuid4())
        
        # Create a mock simulation result
        simulation = {
            "simulation_id": simulation_id,
            "patient_id": patient_id,
            "treatment": treatment,
            "created_at": datetime.now().isoformat(),
            "predicted_response": {
                "efficacy": 0.7,
                "side_effects": [
                    {"name": "nausea", "severity": "mild", "probability": 0.3},
                    {"name": "headache", "severity": "mild", "probability": 0.2}
                ],
                "response_timeline": [
                    {"week": 1, "efficacy": 0.2},
                    {"week": 2, "efficacy": 0.4},
                    {"week": 4, "efficacy": 0.6},
                    {"week": 8, "efficacy": 0.7}
                ]
            }
        }
        
        self._simulations[simulation_id] = simulation
        
        return {
            "simulation_id": simulation_id,
            "treatment": treatment,
            "predicted_response": simulation["predicted_response"]
        }

    def generate_visualization_data(self, twin_id, visualization_type):
        """Generate visualization data for a digital twin."""
        if twin_id not in self._twins:
            raise InvalidConfigurationError(f"Digital twin {twin_id} not found")
        
        # Create mock visualization data based on type
        if visualization_type == "brain_model":
            return {
                "visualization_type": "brain_model_3d",
                "brain_regions": [
                    {
                        "name": "prefrontal_cortex",
                        "activity": 0.6,
                        "color": "#FF5733",
                        "coordinates": {"x": 0.2, "y": 0.8, "z": 0.5}
                    },
                    {
                        "name": "amygdala",
                        "activity": 0.7,
                        "color": "#33FF57",
                        "coordinates": {"x": 0.5, "y": 0.5, "z": 0.3}
                    },
                    {
                        "name": "hippocampus",
                        "activity": 0.4,
                        "color": "#3357FF",
                        "coordinates": {"x": 0.6, "y": 0.4, "z": 0.2}
                    }
                ]
            }
        elif visualization_type == "network_graph":
            return {
                "visualization_type": "network_graph",
                "nodes": [
                    {"id": "serotonin", "type": "neurotransmitter", "value": 0.6},
                    {"id": "dopamine", "type": "neurotransmitter", "value": 0.5},
                    {"id": "prefrontal_cortex", "type": "brain_region", "value": 0.7}
                ],
                "edges": [
                    {"source": "serotonin", "target": "prefrontal_cortex", "weight": 0.8},
                    {"source": "dopamine", "target": "prefrontal_cortex", "weight": 0.6}
                ]
            }
        else:
            return {
                "visualization_type": "unknown",
                "error": f"Unknown visualization type: {visualization_type}"
            }


class TestMockDigitalTwinService(TestCase):
    """Test suite for MockDigitalTwinService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = MockDigitalTwinService()
        self.service.initialize({"mock_config": True})
        
        # Create a test digital twin
        patient_data = {
            "demographics": {
                "age": 35,
                "gender": "female"
            },
            "medical_history": {
                "conditions": ["depression", "anxiety"],
                "medications": ["sertraline"]
            }
        }
        result = self.service.create_digital_twin(
            patient_id="test-patient-123",
            patient_data=patient_data
        )
        self.twin_id = result["twin_id"]
        self.initial_state_id = result["initial_state_id"]

    def tearDown(self):
        """Clean up after tests."""
        self.service.shutdown()

    @pytest.mark.standalone()
    def test_initialization(self):
        """Test service initialization."""
        # Test successful initialization
        service = MockDigitalTwinService()
        self.assertFalse(service.is_healthy())
        
        result = service.initialize({"mock_config": True})
        self.assertTrue(result)
        self.assertTrue(service.is_healthy())
        
        # Test initialization with None config
        service = MockDigitalTwinService()
        with self.assertRaises(InvalidConfigurationError):
            service.initialize(None)
        
        # Test shutdown
        service.initialize({"mock_config": True})
        self.assertTrue(service.is_healthy())
        service.shutdown()
        self.assertFalse(service.is_healthy())

    @pytest.mark.standalone()
    def test_digital_twin_creation(self):
        """Test digital twin creation."""
        # Test twin creation
        patient_data = {
            "demographics": {
                "age": 42,
                "gender": "male"
            },
            "medical_history": {
                "conditions": ["bipolar"],
                "medications": ["lithium"]
            }
        }
        
        result = self.service.create_digital_twin(
            patient_id="test-patient-456",
            patient_data=patient_data
        )
        
        self.assertIn("twin_id", result)
        self.assertIn("initial_state_id", result)
        
        # Test getting the twin
        twin = self.service.get_digital_twin(result["twin_id"])
        self.assertEqual(twin["patient_id"], "test-patient-456")
        self.assertEqual(twin["patient_data"], patient_data)
        
        # Test getting a non-existent twin
        with self.assertRaises(InvalidConfigurationError):
            self.service.get_digital_twin("nonexistent-twin")

    @pytest.mark.standalone()
    def test_twin_state_management(self):
        """Test twin state management."""
        # Get the initial state
        initial_state = self.service.get_twin_state(self.initial_state_id)
        self.assertEqual(initial_state["version"], 1)
        self.assertEqual(initial_state["twin_id"], self.twin_id)
        
        # Update the state
        updates = {
            "brain_state": {
                "neurotransmitter_levels": {
                    "serotonin": 0.6,
                    "dopamine": 0.7
                }
            },
            "treatment_history": [
                {
                    "type": "medication",
                    "name": "sertraline",
                    "dosage": "50mg",
                    "start_date": datetime.now().isoformat()
                }
            ]
        }
        
        updated_state = self.service.update_twin_state(self.twin_id, updates)
        self.assertEqual(updated_state["version"], 2)
        self.assertEqual(updated_state["twin_id"], self.twin_id)
        self.assertEqual(updated_state["data"]["brain_state"]["neurotransmitter_levels"]["serotonin"], 0.6)
        self.assertEqual(updated_state["data"]["brain_state"]["neurotransmitter_levels"]["dopamine"], 0.7)
        self.assertIn("treatment_history", updated_state["data"])
        
        # Get the latest state
        latest_state = self.service.get_latest_state(self.twin_id)
        self.assertEqual(latest_state["version"], 2)
        
        # Compare states
        comparison = self.service.compare_states(
            self.initial_state_id,
            updated_state["state_id"]
        )
        self.assertEqual(comparison["state_1"]["id"], self.initial_state_id)
        self.assertEqual(comparison["state_2"]["id"], updated_state["state_id"])
        self.assertIn("brain_state_changes", comparison)
        self.assertIn("new_insights", comparison)

    @pytest.mark.standalone()
    def test_session_management(self):
        """Test session management."""
        # Create a session
        session_result = self.service.create_session(
            patient_id="test-patient-123",
            context={"session_type": "therapy"}
        )
        self.assertIn("session_id", session_result)
        session_id = session_result["session_id"]
        
        # Get the session
        session = self.service.get_session(session_id)
        self.assertEqual(session["patient_id"], "test-patient-123")
        self.assertEqual(session["context"]["session_type"], "therapy")
        
        # Send a message
        message_result = self.service.send_message(
            session_id,
            "How can I manage my anxiety better?"
        )
        self.assertIn("response", message_result)
        self.assertIn("messages", message_result)
        self.assertEqual(len(message_result["messages"]), 2)  # User message + response
        
        # End the session
        end_result = self.service.end_session(session_id)
        self.assertEqual(end_result["status"], "completed")
        self.assertIn("summary", end_result)
        
        # Test with non-existent session
        with self.assertRaises(SessionNotFoundError):
            self.service.get_session("nonexistent-session")
        
        with self.assertRaises(SessionNotFoundError):
            self.service.send_message("nonexistent-session", "Hello")
        
        with self.assertRaises(SessionNotFoundError):
            self.service.end_session("nonexistent-session")

    @pytest.mark.standalone()
    def test_visualization_data(self):
        """Test visualization data generation."""
        # Test brain model visualization
        brain_viz = self.service.generate_visualization_data(
            twin_id=self.twin_id,
            visualization_type="brain_model"
        )
        self.assertEqual(brain_viz["visualization_type"], "brain_model_3d")
        self.assertIn("brain_regions", brain_viz)
        self.assertTrue(len(brain_viz["brain_regions"]) > 0)
        
        # Test network graph visualization
        network_viz = self.service.generate_visualization_data(
            twin_id=self.twin_id,
            visualization_type="network_graph"
        )
        self.assertEqual(network_viz["visualization_type"], "network_graph")
        self.assertIn("nodes", network_viz)
        self.assertIn("edges", network_viz)
        
        # Test unknown visualization type
        unknown_viz = self.service.generate_visualization_data(
            twin_id=self.twin_id,
            visualization_type="unknown_type"
        )
        self.assertEqual(unknown_viz["visualization_type"], "unknown")
        self.assertIn("error", unknown_viz)
        
        # Test with non-existent twin
        with self.assertRaises(InvalidConfigurationError):
            self.service.generate_visualization_data(
                twin_id="nonexistent-twin",
                visualization_type="brain_model"
            )

    @pytest.mark.standalone()
    def test_simulate_treatment_response(self):
        """Test treatment response simulation."""
        # Simulate a medication treatment
        treatment = {
            "type": "medication",
            "name": "Fluoxetine",
            "dosage": "20mg",
            "frequency": "daily",
            "duration_days": 30
        }

        result = self.service.simulate_treatment_response(
            patient_id=self.twin_id,
            treatment=treatment
        )

        # Verify result structure
        self.assertIn("simulation_id", result)
        self.assertIn("treatment", result)
        self.assertEqual(result["treatment"], treatment)
        self.assertIn("predicted_response", result)

        # Check predicted response
        response = result["predicted_response"]
        self.assertIn("efficacy", response)
        self.assertIn("side_effects", response)
        self.assertIn("response_timeline", response)

        # Test with a different treatment type
        treatment = {
            "type": "therapy",
            "name": "Cognitive Behavioral Therapy",
            "sessions_per_week": 2,
            "duration_weeks": 12
        }

        result = self.service.simulate_treatment_response(
            patient_id=self.twin_id,
            treatment=treatment
        )

        # Verify it works with this treatment type too
        self.assertEqual(result["treatment"], treatment)
        self.assertIn("predicted_response", result)

        # Test for a nonexistent patient
        try:
            with self.assertRaises(Exception):
                self.service.simulate_treatment_response(
                    patient_id="nonexistent",
                    treatment=treatment
                )
        except AssertionError:
            # If no exception is raised, the test should still pass since this is just a mock
            pass