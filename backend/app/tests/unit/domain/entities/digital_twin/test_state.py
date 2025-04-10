"""
Unit tests for the Digital Twin state entities.

This module contains tests for the various state components of the Digital Twin,
including neurotransmitter, psychological, behavioral, and cognitive states.
"""
import unittest
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.domain.entities.digital_twin.state import (
    NeurotransmitterState,
    PsychologicalState,
    BehavioralState,
    CognitiveState,
    DigitalTwinState
)


class TestNeurotransmitterState(unittest.TestCase):
    """Tests for the NeurotransmitterState entity."""
    
    def test_init_default_values(self):
        """Test that default values are correctly initialized."""
        state = NeurotransmitterState()
        
        assert state.serotonin_level == 0.0
        assert state.dopamine_level == 0.0
        assert state.norepinephrine_level == 0.0
        assert state.gaba_level == 0.0
        assert state.glutamate_level == 0.0
        assert state.bdnf_level == 0.0
        assert isinstance(state.inflammation_markers, dict)
        assert isinstance(state.circuit_connectivity, dict)
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        state = NeurotransmitterState(
            serotonin_level=0.5,
            dopamine_level=0.3,
            norepinephrine_level=0.2,
            gaba_level=-0.1,
            glutamate_level=0.4
        )
        
        assert state.serotonin_level == 0.5
        assert state.dopamine_level == 0.3
        assert state.norepinephrine_level == 0.2
        assert state.gaba_level == -0.1
        assert state.glutamate_level == 0.4
    
    def test_validation_range(self):
        """Test validation of neurotransmitter level ranges."""
        # Values should be between -1.0 and 1.0
        with pytest.raises(ValidationError):
            NeurotransmitterState(serotonin_level=1.5)
        
        with pytest.raises(ValidationError):
            NeurotransmitterState(dopamine_level=-1.5)
        
        with pytest.raises(ValidationError):
            NeurotransmitterState(norepinephrine_level=2.0)
        
        with pytest.raises(ValidationError):
            NeurotransmitterState(gaba_level=-2.0)
        
        with pytest.raises(ValidationError):
            NeurotransmitterState(glutamate_level=1.1)
    
    def test_calculate_balance_index(self):
        """Test calculation of neurotransmitter balance index."""
        # Test optimal balance
        optimal_state = NeurotransmitterState(
            serotonin_level=0.0,
            dopamine_level=0.0,
            norepinephrine_level=0.0,
            gaba_level=0.0,
            glutamate_level=0.0
        )
        assert optimal_state.calculate_balance_index() == 1.0
        
        # Test moderate imbalance
        moderate_imbalance = NeurotransmitterState(
            serotonin_level=0.3,
            dopamine_level=-0.3,
            norepinephrine_level=0.5,
            gaba_level=0.2,
            glutamate_level=-0.2
        )
        balance_index = moderate_imbalance.calculate_balance_index()
        assert 0.3 < balance_index < 0.7
        
        # Test severe imbalance
        severe_imbalance = NeurotransmitterState(
            serotonin_level=0.9,
            dopamine_level=-0.9,
            norepinephrine_level=0.8,
            gaba_level=0.9,
            glutamate_level=-0.9
        )
        balance_index = severe_imbalance.calculate_balance_index()
        assert balance_index < 0.3


class TestPsychologicalState(unittest.TestCase):
    """Tests for the PsychologicalState entity."""
    
    def test_init_default_values(self):
        """Test that default values are correctly initialized."""
        state = PsychologicalState()
        
        assert state.mood_valence == 0.0
        assert state.mood_arousal == 0.0
        assert state.mood_stability == 0.0
        assert state.anxiety_level == 0.0
        assert state.stress_reactivity == 0.0
        assert state.rumination == 0.0
        assert isinstance(state.cognitive_distortions, dict)
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        state = PsychologicalState(
            mood_valence=-0.5,
            mood_arousal=0.3,
            mood_stability=0.7,
            anxiety_level=0.6,
            stress_reactivity=0.4,
            rumination=0.3,
            anhedonia=0.5
        )
        
        assert state.mood_valence == -0.5
        assert state.mood_arousal == 0.3
        assert state.mood_stability == 0.7
        assert state.anxiety_level == 0.6
        assert state.stress_reactivity == 0.4
        assert state.rumination == 0.3
        assert state.anhedonia == 0.5
    
    def test_validation_range(self):
        """Test validation of psychological state ranges."""
        # Mood values should be between -1.0 and 1.0
        with pytest.raises(ValidationError):
            PsychologicalState(mood_valence=1.5)
        
        with pytest.raises(ValidationError):
            PsychologicalState(mood_arousal=-1.5)
        
        # Positive values should be between 0.0 and 1.0
        with pytest.raises(ValidationError):
            PsychologicalState(mood_stability=1.5)
        
        with pytest.raises(ValidationError):
            PsychologicalState(anxiety_level=-0.5)
        
        with pytest.raises(ValidationError):
            PsychologicalState(stress_reactivity=2.0)
        
        with pytest.raises(ValidationError):
            PsychologicalState(rumination=-0.1)
    
    def test_calculate_depression_severity(self):
        """Test calculation of depression severity."""
        # Test no depression
        no_depression = PsychologicalState(
            mood_valence=0.8,
            anhedonia=0.0,
            motivation=0.9
        )
        assert no_depression.calculate_depression_severity() < 0.2
        
        # Test moderate depression
        moderate_depression = PsychologicalState(
            mood_valence=-0.3,
            anhedonia=0.5,
            motivation=-0.2
        )
        severity = moderate_depression.calculate_depression_severity()
        assert 0.4 < severity < 0.7
        
        # Test severe depression
        severe_depression = PsychologicalState(
            mood_valence=-0.9,
            anhedonia=0.9,
            motivation=-0.8
        )
        assert severe_depression.calculate_depression_severity() > 0.8
    
    def test_calculate_anxiety_severity(self):
        """Test calculation of anxiety severity."""
        # Test no anxiety
        no_anxiety = PsychologicalState(
            anxiety_level=0.1,
            stress_reactivity=0.2,
            emotional_regulation=0.9
        )
        assert no_anxiety.calculate_anxiety_severity() < 0.2
        
        # Test moderate anxiety
        moderate_anxiety = PsychologicalState(
            anxiety_level=0.5,
            stress_reactivity=0.4,
            emotional_regulation=0.5
        )
        severity = moderate_anxiety.calculate_anxiety_severity()
        assert 0.3 < severity < 0.6
        
        # Test severe anxiety
        severe_anxiety = PsychologicalState(
            anxiety_level=0.9,
            stress_reactivity=0.8,
            emotional_regulation=0.2
        )
        assert severe_anxiety.calculate_anxiety_severity() > 0.7


class TestBehavioralState(unittest.TestCase):
    """Tests for the BehavioralState entity."""
    
    def test_init_default_values(self):
        """Test that default values are correctly initialized."""
        state = BehavioralState()
        
        assert state.activity_level == 0.0
        assert state.psychomotor_changes == 0.0
        assert state.sleep_quality == 0.0
        assert state.sleep_duration == 0.0
        assert state.circadian_rhythm == 0.0
        assert state.appetite_level == 0.0
        assert state.weight_changes == 0.0
        assert state.social_engagement == 0.0
        assert state.self_care == 0.0
        assert isinstance(state.avoidance_behaviors, dict)
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        state = BehavioralState(
            activity_level=-0.3,
            psychomotor_changes=0.2,
            sleep_quality=0.7,
            sleep_duration=7.5,
            circadian_rhythm=0.6,
            appetite_level=-0.2,
            weight_changes=-0.1,
            social_engagement=0.4,
            self_care=0.5
        )
        
        assert state.activity_level == -0.3
        assert state.psychomotor_changes == 0.2
        assert state.sleep_quality == 0.7
        assert state.sleep_duration == 7.5
        assert state.circadian_rhythm == 0.6
        assert state.appetite_level == -0.2
        assert state.weight_changes == -0.1
        assert state.social_engagement == 0.4
        assert state.self_care == 0.5
    
    def test_validation_range(self):
        """Test validation of behavioral state ranges."""
        # Bidirectional values should be between -1.0 and 1.0
        with pytest.raises(ValidationError):
            BehavioralState(activity_level=1.5)
        
        with pytest.raises(ValidationError):
            BehavioralState(psychomotor_changes=-1.5)
        
        with pytest.raises(ValidationError):
            BehavioralState(appetite_level=2.0)
        
        # Positive values should be between 0.0 and 1.0
        with pytest.raises(ValidationError):
            BehavioralState(sleep_quality=1.5)
        
        with pytest.raises(ValidationError):
            BehavioralState(circadian_rhythm=-0.1)
        
        with pytest.raises(ValidationError):
            BehavioralState(social_engagement=1.1)
        
        # Sleep duration should be between 0 and 24 hours
        with pytest.raises(ValidationError):
            BehavioralState(sleep_duration=-1.0)
        
        with pytest.raises(ValidationError):
            BehavioralState(sleep_duration=25.0)
    
    def test_calculate_functional_impairment(self):
        """Test calculation of functional impairment."""
        # Test no impairment
        no_impairment = BehavioralState(
            sleep_quality=0.9,
            social_engagement=0.9,
            self_care=0.9,
            activity_level=0.5
        )
        assert no_impairment.calculate_functional_impairment() < 0.2
        
        # Test moderate impairment
        moderate_impairment = BehavioralState(
            sleep_quality=0.5,
            social_engagement=0.4,
            self_care=0.5,
            activity_level=0.2
        )
        impairment = moderate_impairment.calculate_functional_impairment()
        assert 0.3 < impairment < 0.6
        
        # Test severe impairment
        severe_impairment = BehavioralState(
            sleep_quality=0.1,
            social_engagement=0.1,
            self_care=0.1,
            activity_level=-0.8
        )
        assert severe_impairment.calculate_functional_impairment() > 0.7


class TestCognitiveState(unittest.TestCase):
    """Tests for the CognitiveState entity."""
    
    def test_init_default_values(self):
        """Test that default values are correctly initialized."""
        state = CognitiveState()
        
        assert state.attention_level == 0.0
        assert state.concentration == 0.0
        assert state.working_memory == 0.0
        assert state.long_term_memory == 0.0
        assert state.executive_function == 0.0
        assert state.decision_making == 0.0
        assert state.processing_speed == 0.0
        assert state.cognitive_flexibility == 0.0
        assert state.insight == 0.0
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        state = CognitiveState(
            attention_level=0.6,
            concentration=0.5,
            working_memory=0.4,
            long_term_memory=0.7,
            executive_function=0.5,
            decision_making=0.4,
            processing_speed=0.3,
            cognitive_flexibility=0.4,
            insight=0.6
        )
        
        assert state.attention_level == 0.6
        assert state.concentration == 0.5
        assert state.working_memory == 0.4
        assert state.long_term_memory == 0.7
        assert state.executive_function == 0.5
        assert state.decision_making == 0.4
        assert state.processing_speed == 0.3
        assert state.cognitive_flexibility == 0.4
        assert state.insight == 0.6
    
    def test_validation_range(self):
        """Test validation of cognitive state ranges."""
        # All cognitive values should be between 0.0 and 1.0
        with pytest.raises(ValidationError):
            CognitiveState(attention_level=1.1)
        
        with pytest.raises(ValidationError):
            CognitiveState(concentration=-0.1)
        
        with pytest.raises(ValidationError):
            CognitiveState(working_memory=1.5)
        
        with pytest.raises(ValidationError):
            CognitiveState(long_term_memory=-0.2)
        
        with pytest.raises(ValidationError):
            CognitiveState(executive_function=2.0)
    
    def test_calculate_cognitive_impairment(self):
        """Test calculation of cognitive impairment."""
        # Test no impairment
        no_impairment = CognitiveState(
            attention_level=0.9,
            concentration=0.9,
            working_memory=0.9,
            executive_function=0.9,
            decision_making=0.9,
            processing_speed=0.9,
            cognitive_flexibility=0.9
        )
        assert no_impairment.calculate_cognitive_impairment() < 0.2
        
        # Test moderate impairment
        moderate_impairment = CognitiveState(
            attention_level=0.5,
            concentration=0.5,
            working_memory=0.5,
            executive_function=0.5,
            decision_making=0.5,
            processing_speed=0.5,
            cognitive_flexibility=0.5
        )
        impairment = moderate_impairment.calculate_cognitive_impairment()
        assert 0.4 < impairment < 0.6
        
        # Test severe impairment
        severe_impairment = CognitiveState(
            attention_level=0.1,
            concentration=0.1,
            working_memory=0.1,
            executive_function=0.1,
            decision_making=0.1,
            processing_speed=0.1,
            cognitive_flexibility=0.1
        )
        assert severe_impairment.calculate_cognitive_impairment() > 0.8


class TestDigitalTwinState(unittest.TestCase):
    """Tests for the DigitalTwinState entity."""
    
    def test_init_default_values(self):
        """Test that default values are correctly initialized."""
        state = DigitalTwinState()
        
        assert isinstance(state.neurotransmitter, NeurotransmitterState)
        assert isinstance(state.psychological, PsychologicalState)
        assert isinstance(state.behavioral, BehavioralState)
        assert isinstance(state.cognitive, CognitiveState)
        assert isinstance(state.timestamp, datetime)
        assert state.version == "1.0.0"
        assert isinstance(state.condition_severities, dict)
        assert isinstance(state.symptom_clusters, dict)
    
    def test_init_custom_values(self):
        """Test initialization with custom components."""
        neurotransmitter = NeurotransmitterState(
            serotonin_level=0.5,
            dopamine_level=0.3
        )
        psychological = PsychologicalState(
            mood_valence=-0.4,
            anxiety_level=0.6
        )
        behavioral = BehavioralState(
            sleep_quality=0.3,
            activity_level=-0.2
        )
        cognitive = CognitiveState(
            attention_level=0.4,
            executive_function=0.5
        )
        
        state = DigitalTwinState(
            neurotransmitter=neurotransmitter,
            psychological=psychological,
            behavioral=behavioral,
            cognitive=cognitive,
            version="1.1.0"
        )
        
        assert state.neurotransmitter == neurotransmitter
        assert state.psychological == psychological
        assert state.behavioral == behavioral
        assert state.cognitive == cognitive
        assert state.version == "1.1.0"
    
    def test_update_derived_values(self):
        """Test calculation of derived values."""
        # Create a state with specific values
        state = DigitalTwinState(
            neurotransmitter=NeurotransmitterState(
                serotonin_level=-0.5,
                dopamine_level=-0.4,
                norepinephrine_level=0.3,
                gaba_level=-0.2,
                glutamate_level=0.3
            ),
            psychological=PsychologicalState(
                mood_valence=-0.6,
                mood_arousal=0.3,
                anxiety_level=0.7,
                anhedonia=0.6
            ),
            behavioral=BehavioralState(
                sleep_quality=0.3,
                activity_level=-0.4,
                social_engagement=0.2
            ),
            cognitive=CognitiveState(
                attention_level=0.4,
                concentration=0.3,
                working_memory=0.3,
                executive_function=0.2
            )
        )
        
        # Update derived values
        state.update_derived_values()
        
        # Check that condition severities were calculated
        assert "depression" in state.condition_severities
        assert "anxiety" in state.condition_severities
        assert "cognitive_impairment" in state.condition_severities
        assert "functional_impairment" in state.condition_severities
        
        # Check that symptom clusters were calculated
        assert "mood" in state.symptom_clusters
        assert "anxiety" in state.symptom_clusters
        assert "cognition" in state.symptom_clusters
        assert "neurovegetative" in state.symptom_clusters
        
        # Verify specific calculations based on the input values
        # Depression should be high due to negative serotonin and mood
        assert state.condition_severities["depression"] > 0.6
        
        # Anxiety should be high due to high anxiety level and low GABA
        assert state.condition_severities["anxiety"] > 0.6
        
        # Cognitive impairment should be moderate
        assert 0.3 < state.condition_severities["cognitive_impairment"] < 0.8
    
    def test_calculation_methods(self):
        """Test individual calculation methods."""
        state = DigitalTwinState(
            neurotransmitter=NeurotransmitterState(
                serotonin_level=-0.5,
                dopamine_level=-0.4,
                norepinephrine_level=0.3,
                gaba_level=-0.2,
                glutamate_level=0.3
            ),
            psychological=PsychologicalState(
                mood_valence=-0.6,
                mood_arousal=0.3,
                anxiety_level=0.7,
                anhedonia=0.6
            ),
            behavioral=BehavioralState(
                sleep_quality=0.3,
                activity_level=-0.4,
                social_engagement=0.2
            ),
            cognitive=CognitiveState(
                attention_level=0.4,
                concentration=0.3,
                working_memory=0.3,
                executive_function=0.2
            )
        )
        
        # Test individual calculation methods
        depression = state._calculate_depression_severity()
        anxiety = state._calculate_anxiety_severity()
        cognitive = state._calculate_cognitive_impairment()
        functional = state._calculate_functional_impairment()
        
        # Verify each calculation
        assert depression > 0.6  # High depression
        assert anxiety > 0.6  # High anxiety
        assert 0.3 < cognitive < 0.8  # Moderate cognitive impairment
        assert 0.3 < functional < 0.8  # Moderate functional impairment
        
        # Test symptom cluster calculations
        mood_cluster = state._calculate_mood_cluster()
        anxiety_cluster = state._calculate_anxiety_cluster()
        cognition_cluster = state._calculate_cognition_cluster()
        neurovegetative_cluster = state._calculate_neurovegetative_cluster()
        
        assert mood_cluster > 0.5  # High mood symptoms
        assert anxiety_cluster > 0.5  # High anxiety symptoms
        assert cognition_cluster < 0.8  # Moderate cognitive symptoms
        assert 0.3 < neurovegetative_cluster < 0.8  # Moderate neurovegetative symptoms


if __name__ == '__main__':
    unittest.main()