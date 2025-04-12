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
    ConnectionType
()
from app.domain.entities.temporal_events import CorrelatedEvent, EventChain
from app.domain.entities.temporal_sequence import TemporalSequence
from app.domain.entities.neurotransmitter_effect import NeurotransmitterEffect
from app.domain.entities.neurotransmitter_mapping import ()
    NeurotransmitterMapping,   
    ReceptorProfile,  
    ReceptorType,  
    ReceptorSubtype,  
    create_default_neurotransmitter_mapping
()
from app.domain.entities.temporal_neurotransmitter_mapping import ()
    extend_neurotransmitter_mapping
()
from app.domain.services.visualization_preprocessor import ()
    NeurotransmitterVisualizationPreprocessor,  
    NeurotransmitterEffectVisualizer
()


@pytest.mark.db_required()
class TestTemporalEvents:
    """Test suite for temporal event correlation tracking."""
    
    def test_correlated_event_creation(self):
        """Test creation of correlated events."""
        # Create a root event
        root_event = CorrelatedEvent()
            event_type="test_event",
            metadata={"test_key": "test_value"}
(        )
        
        # Verify root event properties
    assert root_event.event_type  ==  "test_event"
    assert root_event.metadata["test_key"] == "test_value"
    assert root_event.parent_event_id is None
    assert root_event.id is not None
    assert root_event.correlation_id is not None
        
        # Create a child event
    child_event = CorrelatedEvent.create_child_event()
    parent_event=root_event,
    event_type="child_event",
    additional_data="child_data"
(    )
        
        # Verify child event properties
    assert child_event.event_type  ==  "child_event"
    assert child_event.metadata["additional_data"] == "child_data"
    assert child_event.parent_event_id  ==  root_event.id
    assert child_event.correlation_id  ==  root_event.correlation_id
    assert child_event.id  !=  root_event.id
    
    def test_event_chain(self):
        """Test event chain functionality."""
        # Create a chain and some events
        correlation_id = uuid.uuid4()
        chain = EventChain(correlation_id=correlation_id)
        
    root_event = CorrelatedEvent()
    event_type="root",
    correlation_id=correlation_id
(    )
        
    child1 = CorrelatedEvent()
    event_type="child1",
    correlation_id=correlation_id,
    parent_event_id=root_event.id
(    )
        
    child2 = CorrelatedEvent()
    event_type="child2",
    correlation_id=correlation_id,
    parent_event_id=root_event.id
(    )
        
    grandchild = CorrelatedEvent()
    event_type="grandchild",
    correlation_id=correlation_id,
    parent_event_id=child1.id
(    )
        
        # Add events to chain
    chain.add_event(root_event)
    chain.add_event(child1)
    chain.add_event(child2)
    chain.add_event(grandchild)
        
        # Test chain functionality
    assert len(chain.events) == 4
    assert chain.get_root_event() == root_event
    assert set(chain.get_child_events(root_event.id)) == {child1, child2}
    assert chain.get_child_events(child1.id) == [grandchild]
    assert chain.get_event_by_id(child2.id) == child2
    assert set(chain.get_events_by_type("child1")) == {child1}
        
        # Test event tree construction
    tree = chain.build_event_tree()
    assert tree[root_event.id] == [child1.id, child2.id]
    assert tree[child1.id] == [grandchild.id]
    assert child2.id not in tree  # No children
        
        # Test error case - event with wrong correlation ID
    wrong_event = CorrelatedEvent()
    event_type="wrong",
    correlation_id=uuid.uuid4()  # Different correlation ID
(    )
        
    with pytest.raises(ValueError):
    chain.add_event(wrong_event)


class TestTemporalSequence:
    """Test suite for temporal sequences."""
    
    def test_temporal_sequence_creation(self):
        """Test creation of temporal sequences."""
        # Create test data
        now = datetime.datetime.now()
        timestamps = [now + datetime.timedelta(hours=i) for i in range(5)]
        feature_names = ["feature1", "feature2"]
        values = [
            [0.1, 0.2],
            [0.3, 0.4],
            [0.5, 0.6],
            [0.7, 0.8],
            [0.9, 1.0]
        ]
        patient_id = uuid.uuid4()
        
        # Create sequence
    sequence = TemporalSequence()
    sequence_id=uuid.uuid4(),
    feature_names=feature_names,
    timestamps=timestamps,
    values=values,
    patient_id=patient_id,
    metadata={"source": "test"}
(    )
        
        # Verify properties
    assert sequence.sequence_length  ==  5
    assert sequence.feature_dimension  ==  2
    assert sequence.metadata["source"] == "test"
        
        # Test factory method
    sequence2 = TemporalSequence.create()
    feature_names=feature_names,
    timestamps=timestamps,
    values=values,
    patient_id=patient_id
(    )
        
    assert sequence2.sequence_length  ==  5
    assert sequence2.feature_dimension  ==  2
        
        # Test validation
    with pytest.raises(ValueError):
            # Mismatched timestamps and values
    TemporalSequence()
    sequence_id=uuid.uuid4(),
    feature_names=feature_names,
    timestamps=timestamps[:-1],  # One less timestamp
    values=values,
    patient_id=patient_id
(    )
        
    with pytest.raises(ValueError):
            # Mismatched feature names and values
    TemporalSequence()
    sequence_id=uuid.uuid4(),
    feature_names=feature_names + ["extra"],  # One more feature
    timestamps=timestamps,
    values=values,
    patient_id=patient_id
(    )
    
    def test_temporal_sequence_operations(self):
        """Test operations on temporal sequences."""
        # Create test data
        now = datetime.datetime.now()
        timestamps = [now + datetime.timedelta(hours=i) for i in range(10)]
        feature_names = ["f1", "f2"]
        
        # Create increasing values for f1, decreasing for f2
    values = []
    for i in range(10):
    values.append([i/10.0, 1.0 - i/10.0])
        
    sequence = TemporalSequence.create()
    feature_names=feature_names,
    timestamps=timestamps,
    values=values,
    patient_id=uuid.uuid4()
(    )
        
        # Test numpy conversion
    X, y = sequence.to_numpy_arrays()
    assert X.shape  ==  (9, 2)  # 9 input time steps (last is target)
    assert y.shape  ==  (9, 2)  # 9 target time steps (first is input)
    assert np.array_equal(X[0], [0.0, 1.0])
    assert np.array_equal(y[0], [0.1, 0.9])
        
        # Test padded tensor
    padded = sequence.to_padded_tensor(max_length=15)
    assert padded["values"].shape == (15, 2)
    assert padded["mask"].shape == (15,)
    assert padded["seq_len"] == 10
    assert np.sum(padded["mask"]) == 10  # 10 valid entries
        
        # Test subsequence extraction
    subsequence = sequence.extract_subsequence(2, 7)
    assert subsequence.sequence_length  ==  5
    assert subsequence.feature_dimension  ==  2
    assert subsequence.values[0][0] == 0.2  # First value of extracted sequence
        
        # Test statistics
    stats = sequence.get_feature_statistics()
    assert "f1" in stats
    assert "f2" in stats
    assert stats["f1"]["min"] == 0.0
    assert stats["f1"]["max"] == 0.9
    assert abs(stats["f2"]["min"] - 0.1) < 1e-10  # Use approximation for float comparison
    assert stats["f2"]["max"] == 1.0
        
        # Test dictionary conversion
    seq_dict = sequence.to_dict()
    assert seq_dict["sequence_length"] == 10
    assert seq_dict["feature_dimension"] == 2
    assert len(seq_dict["timestamps"]) == 10
    assert len(seq_dict["values"]) == 10


class TestNeurotransmitterEffect:
    """Test suite for neurotransmitter effect metrics."""
    
    def test_neurotransmitter_effect_creation(self):
        """Test creation of neurotransmitter effects."""
        # Create a basic effect
        effect = NeurotransmitterEffect()
            neurotransmitter=Neurotransmitter.DOPAMINE,
            effect_size=0.75,
            confidence_interval=(0.5, 1.0),
            p_value=0.03,
            sample_size=30,
            clinical_significance=ClinicalSignificance.MODERATE
(        )
        
        # Verify properties
    assert effect.neurotransmitter  ==  Neurotransmitter.DOPAMINE
    assert effect.effect_size  ==  0.75
    assert effect.is_statistically_significant is True
    assert effect.precision  ==  2.0  # 1.0 / (1.0 - 0.5)
    assert effect.effect_magnitude  ==  "medium"
    assert effect.direction  ==  "increase"
        
        # Test validation
    with pytest.raises(ValueError):
            # Invalid p-value
    NeurotransmitterEffect()
    neurotransmitter=Neurotransmitter.DOPAMINE,
    effect_size=0.75,
    confidence_interval=(0.5, 1.0),
    p_value=1.5,  # Invalid (>1.0)
    sample_size=30,
    clinical_significance=ClinicalSignificance.MODERATE
(    )
        
    with pytest.raises(ValueError):
            # Invalid confidence interval
    NeurotransmitterEffect()
    neurotransmitter=Neurotransmitter.DOPAMINE,
    effect_size=0.75,
    confidence_interval=(1.0, 0.5),  # Reversed
    p_value=0.03,
    sample_size=30,
    clinical_significance=ClinicalSignificance.MODERATE
(    )
    
    def test_neurotransmitter_effect_factory(self):
        """Test factory method for neurotransmitter effects."""
        # Create test data (higher values in intervention vs baseline)
        baseline_data = [0.5, 0.4, 0.6, 0.5, 0.4]
        intervention_data = [0.8, 0.7, 0.9, 0.8, 0.7]
        
        # Create effect using factory
    effect = NeurotransmitterEffect.create()
    neurotransmitter=Neurotransmitter.SEROTONIN,
    raw_data=intervention_data,
    baseline_data=baseline_data,
    clinical_significance=ClinicalSignificance.MODERATE
(    )
        
        # Verify calculated properties
    assert effect.neurotransmitter  ==  Neurotransmitter.SEROTONIN
    assert effect.sample_size  ==  10  # 5 baseline + 5 intervention
    assert effect.effect_size > 0  # Should be positive
    assert effect.p_value < 0.05  # Should be significant
    assert effect.is_statistically_significant is True
    assert effect.direction  ==  "increase"
        
        # Test visualization data
    viz_data = effect.to_visualization_data()
    assert viz_data["neurotransmitter"] == "serotonin"
    assert viz_data["effect_size"] > 0
    assert viz_data["is_significant"] is True
    assert viz_data["clinical_significance"] == "moderate"


class TestTemporalNeurotransmitterMapping:
    """Test suite for temporal neurotransmitter mapping extensions."""
    
    @pytest.fixture
    def extended_mapping(self):
        """Create an extended neurotransmitter mapping for tests."""
        # Start with the default mapping
        base_mapping = create_default_neurotransmitter_mapping()
    
        # Extend with temporal methods
    extended = extend_neurotransmitter_mapping(base_mapping)
        
        # Copy over the key components from the base mapping
    extended.production_map = base_mapping.production_map
    extended.receptor_profiles = base_mapping.receptor_profiles
    extended._build_lookup_maps()
        
#     return extended # FIXME: return outside function
    
    def test_generate_temporal_sequence(self, extended_mapping):
        """Test generation of temporal sequences from neurotransmitter mapping."""
        # Create test data
        now = datetime.datetime.now()
        timestamps = [now + datetime.timedelta(hours=i) for i in range(10)]
        
        # Generate a sequence for serotonin in prefrontal cortex
    sequence = extended_mapping.generate_temporal_sequence()
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    neurotransmitter=Neurotransmitter.SEROTONIN,
    timestamps=timestamps
(    )
        
        # Verify the sequence
    assert sequence.sequence_length  ==  10
    assert len(sequence.feature_names) == len(Neurotransmitter)
    assert sequence.metadata["brain_region"] == BrainRegion.PREFRONTAL_CORTEX.value
    assert sequence.metadata["primary_neurotransmitter"] == Neurotransmitter.SEROTONIN.value
    
    def test_predict_cascade_effect(self, extended_mapping):
        """Test prediction of cascade effects across brain regions."""
        # Simulate cascade from amygdala
        cascade_results = extended_mapping.predict_cascade_effect()
            starting_region=BrainRegion.AMYGDALA,
            neurotransmitter=Neurotransmitter.SEROTONIN,
            initial_level=0.8,
            time_steps=5
(        )
        
        # Verify the cascade results
    assert BrainRegion.AMYGDALA in cascade_results
    assert cascade_results[BrainRegion.AMYGDALA][0] == 0.8  # Initial value
        
        # Check that the effect propagates to at least some other regions
    propagated = False
    for region, levels in cascade_results.items():
    if region != BrainRegion.AMYGDALA and max(levels) > 0.01:
    propagated = True
    break
        
    assert propagated, "Cascade effect did not propagate to any other regions"
    
    def test_analyze_temporal_response(self, extended_mapping):
        """Test analysis of temporal response to neurotransmitter changes."""
        # Create test data with increasing serotonin levels
        now = datetime.datetime.now()
        baseline_end = now + datetime.timedelta(hours=5)
        
        # 10 hours of data: first 5 at baseline, next 5 increasing
    timestamps = [now + datetime.timedelta(hours=i) for i in range(10)]
    levels = [0.5] * 5 + [0.6, 0.7, 0.8, 0.9, 1.0]  # Increase after baseline
        
    time_series_data = list(zip(timestamps, levels))
        
        # Analyze the temporal response
    effect = extended_mapping.analyze_temporal_response()
    patient_id=uuid.uuid4(),
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    neurotransmitter=Neurotransmitter.SEROTONIN,
    time_series_data=time_series_data,
    baseline_period=(timestamps[0], timestamps[4])
(    )
        
        # Verify the analysis
    assert effect.neurotransmitter  ==  Neurotransmitter.SEROTONIN
    assert effect.effect_size > 0  # Should be positive
    assert effect.is_statistically_significant  ==  True  # Compare to Python boolean
    assert effect.effect_magnitude in ["large", "medium"]  # Should be substantial
    assert effect.direction  ==  "increase"
    
    def test_simulate_treatment_response(self, extended_mapping):
        """Test simulation of treatment response."""
        # Create test data
        now = datetime.datetime.now()
        timestamps = [now + datetime.timedelta(hours=i) for i in range(10)]
        
        # Simulate treatment increasing serotonin
    responses = extended_mapping.simulate_treatment_response()
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    target_neurotransmitter=Neurotransmitter.SEROTONIN,
    treatment_effect=0.5,  # Positive effect (increase)
    timestamps=timestamps
(    )
        
        # Verify responses
    assert Neurotransmitter.SEROTONIN in responses
    serotonin_seq = responses[Neurotransmitter.SEROTONIN]
        
        # Check for direct effect on serotonin
    serotonin_idx = list(Neurotransmitter).index(Neurotransmitter.SEROTONIN)
    initial_level = serotonin_seq.values[0][serotonin_idx]
    max_level = max(ts[serotonin_idx] for ts in serotonin_seq.values)
        
    assert max_level > initial_level, "Treatment had no effect on serotonin levels"
        
        # Check for indirect effects on other neurotransmitters - Less strict threshold
    indirect_effects = False
    for nt, seq in responses.items():
    if nt != Neurotransmitter.SEROTONIN:
    nt_idx = list(Neurotransmitter).index(nt)
    initial = seq.values[0][nt_idx]
    maximum = max(ts[nt_idx] for ts in seq.values)
                # Use a smaller threshold for detection
    if abs(maximum - initial) > 0.01:  # Smaller threshold
    indirect_effects = True
    break
        
    assert indirect_effects, "No indirect effects on other neurotransmitters"


class TestVisualizationPreprocessor:
    """Test suite for visualization preprocessors."""
    
    def test_precompute_cascade_geometry(self):
        """Test precomputation of geometry for cascade visualization."""
        # Create test data
        preprocessor = NeurotransmitterVisualizationPreprocessor()
        
        # Create a simple cascade simulation result
    cascade_data = {
    BrainRegion.AMYGDALA: [0.8, 0.7, 0.6, 0.5, 0.4],
    BrainRegion.PREFRONTAL_CORTEX: [0.0, 0.3, 0.5, 0.7, 0.8],
    BrainRegion.HIPPOCAMPUS: [0.0, 0.0, 0.2, 0.4, 0.6]
    }
        
        # Precompute geometry
    geometry = preprocessor.precompute_cascade_geometry(cascade_data)
        
        # Verify the result
    assert "vertices_by_time" in geometry
    assert "colors_by_time" in geometry
    assert "connections" in geometry
    assert "time_steps" in geometry
    assert geometry["time_steps"] == 5
        
        # First time step should have only amygdala active
    active_t0 = len(geometry["vertices_by_time"][0]) // 3  # 3 coordinates per point
    assert active_t0  ==  1  # Just amygdala
        
        # Last time step should have all regions active
    active_t4 = len(geometry["vertices_by_time"][4]) // 3
    assert active_t4  ==  3  # All 3 regions
    
    def test_neurotransmitter_effect_visualizer(self):
        """Test visualization of neurotransmitter effects."""
        # Create test data
        visualizer = NeurotransmitterEffectVisualizer()
        
        # Create some test effects
    effects = [
    NeurotransmitterEffect()
    neurotransmitter=Neurotransmitter.DOPAMINE,
    effect_size=0.8,
    confidence_interval=(0.6, 1.0),
    p_value=0.01,
    sample_size=40,
    clinical_significance=ClinicalSignificance.MODERATE
(    ),
    NeurotransmitterEffect()
    neurotransmitter=Neurotransmitter.SEROTONIN,
    effect_size=0.5,
    confidence_interval=(0.3, 0.7),
    p_value=0.04,
    sample_size=40,
    clinical_significance=ClinicalSignificance.MILD
(    ),
    NeurotransmitterEffect()
    neurotransmitter=Neurotransmitter.GABA,
    effect_size=-0.3,
    confidence_interval=(-0.5, -0.1),
    p_value=0.06,  # Not significant
    sample_size=40,
    clinical_significance=ClinicalSignificance.MINIMAL
(    )
    ]
        
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
    assert len(timeline["timeline"]) > 1  # Should have multiple time points
    assert timeline["timeline"][0]["effect_size"] == 0.8  # Initial effect size
    assert timeline["timeline"][-1]["is_prediction"] is True  # Last point is a prediction