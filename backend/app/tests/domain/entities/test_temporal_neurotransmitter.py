"""
Tests for the temporal neurotransmitter mapping components.
Ensures proper functionality of the temporal extensions to the Digital Twin.
"""
import datetime
import math
import uuid
from unittest import mock
import pytest
import numpy as np
from typing import Dict, List, Set, Tuple

from app.domain.entities.digital_twin_enums import ()
BrainRegion,
Neurotransmitter,
ClinicalSignificance,
ConnectionType,

from app.domain.entities.temporal_events import CorrelatedEvent, EventChain
from app.domain.entities.temporal_sequence import TemporalSequence
from app.domain.entities.neurotransmitter_effect import NeurotransmitterEffect
from app.domain.entities.neurotransmitter_mapping import ()
NeurotransmitterMapping,
ReceptorProfile,
ReceptorType,
ReceptorSubtype,
create_default_neurotransmitter_mapping,

from app.domain.entities.temporal_neurotransmitter_mapping import ()
extend_neurotransmitter_mapping,

from app.domain.services.visualization_preprocessor import ()
NeurotransmitterVisualizationPreprocessor,
NeurotransmitterEffectVisualizer,



@pytest.mark.db_required()
class TestTemporalEvents:
    """Test suite for temporal event correlation tracking."""

    def test_correlated_event_creation(self):
        """Test creation of correlated events."""
        # Create a root event
        root_event = CorrelatedEvent()
        event_type="test_event", metadata={"test_key": "test_value"}
        

        # Verify root event properties
        assert root_event.event_type == "test_event"
        assert root_event.metadata["test_key"] == "test_value"
        assert root_event.parent_event_id is None
        assert root_event.id is not None
        assert root_event.correlation_id is not None

        # Create a child event
        child_event = CorrelatedEvent.create_child_event()
        parent_event=root_event,
        event_type="child_event",
        additional_data="child_data",
        

        # Verify child event properties
        assert child_event.event_type == "child_event"
        assert child_event.metadata["additional_data"] == "child_data"
        assert child_event.parent_event_id == root_event.id
        assert child_event.correlation_id == root_event.correlation_id
        assert child_event.id is not None
        assert child_event.id != root_event.id

        def test_event_chain_creation(self):
        """Test creation and manipulation of event chains."""
        # Create an event chain
        chain = EventChain()

        # Verify initial state
        assert len(chain.events) == 0

        # Add events to the chain
        event1 = CorrelatedEvent(event_type="event1")
        event2 = CorrelatedEvent(event_type="event2")
        event3 = CorrelatedEvent(event_type="event3")

        chain.add_event(event1)
        chain.add_event(event2)
        chain.add_event(event3)

        # Verify events were added in order
        assert len(chain.events) == 3
        assert chain.events[0] == event1
        assert chain.events[1] == event2
        assert chain.events[2] == event3

        # Test getting events by type
        event_type1_events = chain.get_events_by_type("event1")
        assert len(event_type1_events) == 1
        assert event_type1_events[0] == event1

        # Test getting events by correlation ID
        correlated_events = chain.get_events_by_correlation_id(event1.correlation_id)
        assert len(correlated_events) == 1
        assert correlated_events[0] == event1

        # Add a child event
        child_event = CorrelatedEvent.create_child_event()
        parent_event=event1, event_type="child_event"
        
        chain.add_event(child_event)

        # Verify child event was added
        assert len(chain.events) == 4
        assert chain.events[3] == child_event

        # Test getting events by parent ID
        child_events = chain.get_events_by_parent_id(event1.id)
        assert len(child_events) == 1
        assert child_events[0] == child_event

        # Test getting events by correlation ID now returns both parent and child
        correlated_events = chain.get_events_by_correlation_id(event1.correlation_id)
        assert len(correlated_events) == 2
        assert event1 in correlated_events
        assert child_event in correlated_events


@pytest.mark.db_required()
class TestTemporalSequence:
    """Test suite for temporal sequence functionality."""

    def test_temporal_sequence_creation(self):
        """Test creation of temporal sequences."""
        # Create a patient ID
        patient_id = uuid.uuid4()

        # Create a temporal sequence
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        sequence = TemporalSequence()
        patient_id=patient_id,
        timestamp=timestamp,
        events=[],
        metadata={"source": "test"},
        

        # Verify sequence properties
        assert sequence.patient_id == patient_id
        assert sequence.timestamp == timestamp
        assert len(sequence.events) == 0
        assert sequence.metadata["source"] == "test"
        assert sequence.id is not None

        def test_add_events_to_sequence(self):
        """Test adding events to a temporal sequence."""
        # Create a patient ID
        patient_id = uuid.uuid4()

        # Create a temporal sequence
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        sequence = TemporalSequence()
        patient_id=patient_id,
        timestamp=timestamp,
        events=[],
        metadata={"source": "test"},
        

        # Create events
        event1 = CorrelatedEvent(event_type="event1")
        event2 = CorrelatedEvent(event_type="event2")

        # Add events to the sequence
        sequence.add_event(event1)
        sequence.add_event(event2)

        # Verify events were added
        assert len(sequence.events) == 2
        assert sequence.events[0] == event1
        assert sequence.events[1] == event2

        # Test getting events by type
        event_type1_events = sequence.get_events_by_type("event1")
        assert len(event_type1_events) == 1
        assert event_type1_events[0] == event1

        def test_sequence_with_initial_events(self):
        """Test creating a sequence with initial events."""
        # Create a patient ID
        patient_id = uuid.uuid4()

        # Create events
        event1 = CorrelatedEvent(event_type="event1")
        event2 = CorrelatedEvent(event_type="event2")

        # Create a temporal sequence with initial events
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        sequence = TemporalSequence()
        patient_id=patient_id,
        timestamp=timestamp,
        events=[event1, event2],
        metadata={"source": "test"},
        

        # Verify events were added
        assert len(sequence.events) == 2
        assert sequence.events[0] == event1
        assert sequence.events[1] == event2


@pytest.mark.db_required()
class TestTemporalNeurotransmitterMapping:
    """Test suite for temporal neurotransmitter mapping functionality."""

    def test_extend_neurotransmitter_mapping(self):
        """Test extending a neurotransmitter mapping with temporal data."""
        # Create a patient ID
        patient_id = uuid.uuid4()

        # Create a basic neurotransmitter mapping
        mapping = create_default_neurotransmitter_mapping(patient_id)

        # Extend the mapping with temporal data
        extended_mapping = extend_neurotransmitter_mapping(mapping)

        # Verify the extended mapping
        assert extended_mapping.patient_id == patient_id
        assert len(extended_mapping.receptor_profiles) >= len(mapping.receptor_profiles)

        # Check that the extended mapping has temporal properties
            for profile in extended_mapping.receptor_profiles:
                assert hasattr(profile, "temporal_dynamics")
                assert profile.temporal_dynamics is not None

            def test_temporal_dynamics_properties(self):
        """Test the properties of temporal dynamics in extended mappings."""
        # Create a patient ID
        patient_id = uuid.uuid4()

        # Create a basic neurotransmitter mapping
        mapping = create_default_neurotransmitter_mapping(patient_id)

        # Extend the mapping with temporal data
        extended_mapping = extend_neurotransmitter_mapping(mapping)

        # Check temporal dynamics properties for each profile
            for profile in extended_mapping.receptor_profiles:
        dynamics = profile.temporal_dynamics
        assert "response_time_ms" in dynamics
        assert "decay_rate" in dynamics
        assert "refractory_period_ms" in dynamics
        assert "adaptation_rate" in dynamics

        # Verify reasonable values
        assert dynamics["response_time_ms"] > 0
        assert 0 <= dynamics["decay_rate"] <= 1
        assert dynamics["refractory_period_ms"] >= 0
        assert 0 <= dynamics["adaptation_rate"] <= 1

            def test_temporal_response_simulation(self):
        """Test simulating temporal responses in the extended mapping."""
        # Create a patient ID
        patient_id = uuid.uuid4()

        # Create a basic neurotransmitter mapping
        mapping = create_default_neurotransmitter_mapping(patient_id)

        # Extend the mapping with temporal data
        extended_mapping = extend_neurotransmitter_mapping(mapping)

        # Get a profile to test
        profile = extended_mapping.receptor_profiles[0]

        # Simulate a response
        stimulus_strength = 0.8
        response = profile.simulate_temporal_response(stimulus_strength)

        # Verify the response
        assert "peak_amplitude" in response
        assert "time_to_peak_ms" in response
        assert "duration_ms" in response
        assert "response_curve" in response

        # Check reasonable values
        assert 0 <= response["peak_amplitude"] <= 1
        assert response["time_to_peak_ms"] > 0
        assert response["duration_ms"] > response["time_to_peak_ms"]
        assert len(response["response_curve"]) > 0

        # Check that stronger stimuli produce stronger responses
        weak_stimulus = 0.3
        weak_response = profile.simulate_temporal_response(weak_stimulus)
        assert weak_response["peak_amplitude"] < response["peak_amplitude"]


@pytest.mark.db_required()
class TestNeurotransmitterVisualization:
    """Test suite for neurotransmitter visualization preprocessing."""

    def test_visualization_preprocessor(self):
        """Test the neurotransmitter visualization preprocessor."""
        # Create a preprocessor
        preprocessor = NeurotransmitterVisualizationPreprocessor()

        # Create sample data
        data = {
        Neurotransmitter.SEROTONIN: {
        BrainRegion.PREFRONTAL_CORTEX: 0.8,
        BrainRegion.AMYGDALA: 0.6,
        },
        Neurotransmitter.DOPAMINE: {
        BrainRegion.PREFRONTAL_CORTEX: 0.7,
        BrainRegion.STRIATUM: 0.9,
        },
        }

        # Process the data
        processed_data = preprocessor.process(data)

        # Verify the processed data
        assert "nodes" in processed_data
        assert "links" in processed_data
        assert "metadata" in processed_data

        # Check nodes
        nodes = processed_data["nodes"]
        assert len(nodes) >= 4  # At least 4 nodes (2 neurotransmitters + 2 regions)
        
        # Check that all brain regions and neurotransmitters are represented
        node_types = [node["type"] for node in nodes]
        assert "neurotransmitter" in node_types
        assert "brain_region" in node_types
        
        # Check links
        links = processed_data["links"]
        assert len(links) >= 4  # At least 4 connections
        
        # Check metadata
        metadata = processed_data["metadata"]
        assert "timestamp" in metadata
        assert "version" in metadata

        def test_effect_visualizer(self):
        """Test the neurotransmitter effect visualizer."""
        # Create a visualizer
        visualizer = NeurotransmitterEffectVisualizer()

        # Create sample effects
        effects = []
        NeurotransmitterEffect()
        neurotransmitter=Neurotransmitter.DOPAMINE,
        effect_size=0.8,
        confidence_interval=(0.6, 1.0),
        p_value=0.01,
        sample_size=40,
        clinical_significance=ClinicalSignificance.MODERATE,
        ),
        NeurotransmitterEffect()
        neurotransmitter=Neurotransmitter.SEROTONIN,
        effect_size=0.5,
        confidence_interval=(0.3, 0.7),
        p_value=0.04,
        sample_size=40,
        clinical_significance=ClinicalSignificance.MILD,
        ),
        NeurotransmitterEffect()
        neurotransmitter=Neurotransmitter.GABA,
        effect_size=-0.3,
        confidence_interval=(-0.5, -0.1),
        p_value=0.06,  # Not significant
        sample_size=40,
        clinical_significance=ClinicalSignificance.MINIMAL,
        ),
        

        # Generate comparison visualization
        comparison = visualizer.generate_effect_comparison(effects)

        # Verify the comparison
        assert "effects" in comparison
        assert "comparison_metrics" in comparison
        assert len(comparison["effects"]) == 3

        # Check rankings
        metrics = comparison["comparison_metrics"]
        assert metrics["most_significant"] == Neurotransmitter.DOPAMINE.value
        assert metrics["largest_effect"] == Neurotransmitter.DOPAMINE.value
        assert metrics["magnitude_ranking"][0] == Neurotransmitter.DOPAMINE.value

        # Test timeline visualization
        timeline = visualizer.generate_effect_timeline(effects[0])

        # Verify the timeline
        assert "neurotransmitter" in timeline
        assert "timeline" in timeline
        assert "metrics" in timeline
        # Should have multiple time points
        assert len(timeline["timeline"]) > 1
        # Initial effect size
        assert timeline["timeline"][0]["effect_size"] == 0.8
        assert ()
        timeline["timeline"][-1]["is_prediction"] is True
        )  # Last point is a prediction