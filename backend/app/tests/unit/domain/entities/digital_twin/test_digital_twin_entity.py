"""
Unit tests for the Digital Twin entity.

This module contains tests for the core Digital Twin entity, verifying its ability
to represent and simulate a patient's psychiatric state.
"""
import unittest
import pytest
from datetime import datetime, UTC, timedelta
from app.domain.utils.datetime_utils import UTC
from uuid import UUID, uuid4
from typing import Dict, List, Any

# Removed ModelConfidence
from app.domain.entities.digital_twin.digital_twin import DigitalTwin
# Removed import of non-existent state module and 
classes
# Removed import of non-existent treatment module and 
classes
# Removed import of non-existent temporal module and 
classes


@pytest.mark.venv_only()
class TestDigitalTwin(unittest.TestCase):
    """Tests for the DigitalTwin entity."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a patient ID
        self.patient_id = uuid4()

        # Create a basic state
        self.initial_state = DigitalTwinState(
            neurotransmitter=NeurotransmitterState(
                serotonin_level=-0.3,
                dopamine_level=-0.2,
                norepinephrine_level=0.1,
                gaba_level=-0.1,
                glutamate_level=0.2
            ),
            psychological=PsychologicalState(
                mood_valence=-0.4,
                mood_arousal=0.2,
                mood_stability=0.3,
                anxiety_level=0.6,
                stress_reactivity=0.5,
                rumination=0.4,
                anhedonia=0.5
            ),
            behavioral=BehavioralState(
                activity_level=-0.3,
                psychomotor_changes=0.1,
                sleep_quality=0.4,
                sleep_duration=6.5,
                circadian_rhythm=0.3,
                appetite_level=-0.2,
                social_engagement=0.3
            ),
            cognitive=CognitiveState(
                attention_level=0.5,
                concentration=0.4,
                working_memory=0.5,
                executive_function=0.4,
                decision_making=0.3
            )
        )
        self.initial_state.update_derived_values()

        # Create test treatments
        self.ssri_treatment = Treatment(
            id=uuid4(),
            name="Fluoxetine",
            category=TreatmentCategory.MEDICATION,
            frequency=TreatmentFrequency.DAILY,
            start_date=datetime.now(UTC),
            medication_details=MedicationDetails(
                type=MedicationType.SSRI,
                dosage=20.0,
                dosage_unit="mg",
                serotonin_effect=0.5,
                dopamine_effect=0.1,
                norepinephrine_effect=0.1,
                gaba_effect=0.0,
                glutamate_effect=0.0
            )
        )

        self.therapy_treatment = Treatment(
            id=uuid4(),
            name="Cognitive Behavioral Therapy",
            category=TreatmentCategory.THERAPY,
            frequency=TreatmentFrequency.WEEKLY,
            start_date=datetime.now(UTC),
            # Removed therapy_details due to missing TherapyDetails/TherapyType
            predicted_effects={
                "serotonin": 0.2,
                "rumination": -0.3,
                "cognitive_distortions": -0.4
            }  # Keep predicted_effects if needed
        )

        # Create treatment plan
        self.treatment_plan = TreatmentPlan(
            id=uuid4(),
            patient_id=self.patient_id,
            name="Depression Treatment Plan",
            treatments=[self.ssri_treatment, self.therapy_treatment],
            start_date=datetime.now(UTC),
            status="active"
        )

        # Create a basic digital twin
        self.digital_twin = DigitalTwin(
            patient_id=self.patient_id,
            current_state=self.initial_state,
            confidence_level=0.5  # Replaced enum with float
        )

    def test_init_default_values(self):
        """Test that default values are correctly initialized."""
        twin = DigitalTwin(
            patient_id=self.patient_id,
            current_state=self.initial_state
        )

        assert twin.patient_id == self.patient_id
        assert twin.version == "1.0.0"
        assert isinstance(twin.created_at, datetime)
        assert isinstance(twin.updated_at, datetime)
        assert twin.last_calibration is None
        assert twin.state_history == []
        assert isinstance(twin.demographic_factors, dict)
        assert isinstance(twin.genetic_factors, dict)
        assert isinstance(twin.medical_history, dict)
        assert isinstance(twin.environmental_factors, dict)
        assert twin.confidence_level == 0.5  # Replaced enum with float
        assert twin.calibration_score == 0.0
        assert isinstance(twin.validation_metrics, dict)
        assert twin.temporal_dynamics is None

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        created_at = datetime.now(UTC) - timedelta(days=10)
        last_calibration = datetime.now(UTC) - timedelta(days=5)

        twin = DigitalTwin(
            patient_id=self.patient_id,
            current_state=self.initial_state,
            version="1.1.0",
            created_at=created_at,
            last_calibration=last_calibration,
            demographic_factors={"age": 35, "gender": "female"},
            genetic_factors={"cyp2d6_metabolizer": "extensive"},
            medical_history={"prior_treatments": ["SSRIs", "CBT"]},
            confidence_level=0.85,  # Replaced enum with float
            calibration_score=0.85
        )

        assert twin.patient_id == self.patient_id
        assert twin.version == "1.1.0"
        assert twin.created_at == created_at
        assert twin.last_calibration == last_calibration
        assert twin.demographic_factors == {"age": 35, "gender": "female"}
        assert twin.genetic_factors == {"cyp2d6_metabolizer": "extensive"}
        assert twin.medical_history == {"prior_treatments": ["SSRIs", "CBT"]}
        assert twin.confidence_level == 0.85  # Replaced enum with float
        assert twin.calibration_score == 0.85

    def test_update_state(self):
        """Test updating the digital twin state."""
        # Create initial state snapshot
        initial_state_copy = self.digital_twin.current_state.copy(deep=True)

        # Update with new data
        new_data = {
            "neurotransmitter_data": {
                "serotonin": {"level": 0.1},
                "dopamine": {"level": 0.0}
            },
            "psychological_data": {
                "mood": {"valence": -0.2},
                "anxiety": {"level": 0.4}
            },
            "behavioral_data": {
                "sleep": {"quality": 0.6},
                "activity": {"level": 0.0}
            },
            "cognitive_data": {
                "attention": {"level": 0.6},
                "memory": {"working_memory": 0.6}
            }
        }

        # Update state
        self.digital_twin.update_state(new_data)

    # Verify state history updated
    assert len(self.digital_twin.state_history) == 1
    assert self.digital_twin.state_history[0][1] == initial_state_copy

    # Verify current state updated
    assert self.digital_twin.current_state.neurotransmitter.serotonin_level == 0.1
    assert self.digital_twin.current_state.neurotransmitter.dopamine_level == 0.0
    assert self.digital_twin.current_state.psychological.mood_valence == -0.2
    assert self.digital_twin.current_state.psychological.anxiety_level == 0.4
    assert self.digital_twin.current_state.behavioral.sleep_quality == 0.6
    assert self.digital_twin.current_state.behavioral.activity_level == 0.0
    assert self.digital_twin.current_state.cognitive.attention_level == 0.6
    assert self.digital_twin.current_state.cognitive.working_memory == 0.6

    # Verify update timestamp
    assert self.digital_twin.updated_at > self.digital_twin.created_at

                    def test_predict_treatment_response(self):


    """Test prediction of treatment response."""
    # Add temporal dynamics for prediction
    from app.domain.entities.digital_twin.temporal import TemporalDynamics
    , self.digital_twin.temporal_dynamics = TemporalDynamics()

    # Predict response
    treatment_response = self.digital_twin.predict_treatment_response(,)
    treatment= self.ssri_treatment,
    time_horizon_days = 30
    ()

    # Verify response properties
    assert isinstance(treatment_response, TreatmentResponse)
    assert treatment_response.treatment_id == self.ssri_treatment.id
    assert treatment_response.patient_id == self.patient_id
    assert treatment_response.digital_twin_id == self.digital_twin.id
    assert isinstance(treatment_response.efficacy, float)
    assert isinstance(treatment_response.side_effects, dict)
    assert isinstance(treatment_response.time_to_response, int)
    assert isinstance(treatment_response.remission_probability, float)
    assert isinstance(treatment_response.trajectory, TrajectoryPrediction)
    # Assuming confidence_level is now a float on TreatmentResponse too, or removing check
    # Let's assume it mirrors DigitalTwin and is a float
    assert isinstance(treatment_response.confidence_level, float)

        def test_compare_treatments(self):


            """Test comparison of multiple treatments."""
            # Add temporal dynamics for prediction
            from app.domain.entities.digital_twin.temporal import TemporalDynamics
            , self.digital_twin.temporal_dynamics = TemporalDynamics()

            # Compare treatments
            treatment_analysis = self.digital_twin.compare_treatments(,)
            treatments= [self.ssri_treatment, self.therapy_treatment],
            time_horizon_days = 30
            ()

            # Verify analysis properties
            assert treatment_analysis.patient_id == self.patient_id
            assert treatment_analysis.digital_twin_id == self.digital_twin.id
            assert len(treatment_analysis.treatment_responses) == 2
            assert len(treatment_analysis.rankings) == 2
            assert isinstance(treatment_analysis.recommendations, dict)
            assert "recommended_treatment_id" in treatment_analysis.recommendations
            # Assuming confidence_level is now a float on TreatmentAnalysis too, or
            # removing check
            assert isinstance(treatment_analysis.confidence_level, float)

            def test_detect_patterns(self):


                """Test detection of temporal patterns."""
                # Create temporal dynamics with pattern detectors
                from app.domain.entities.digital_twin.temporal import ()
                TemporalDynamics,
                SeasonalPatternDetector,
                EpisodicPatternDetector
        

                self.digital_twin.temporal_dynamics = TemporalDynamics(,)
    pattern_detectors= {
    "seasonal": SeasonalPatternDetector(),
    "episodic": EpisodicPatternDetector()
    }


()

# Add some state history
                    for i in range(5):
state = self.initial_state.copy(deep=True)
state.psychological.mood_valence = -0.4 + (i * 0.1)
self.digital_twin.temporal_dynamics.record_state_point(state)

# Detect patterns
patterns = self.digital_twin.detect_patterns()

# Verify patterns
assert "seasonal" in patterns
assert "episodic" in patterns
assert isinstance(patterns["seasonal"], PatternStrength)
assert isinstance(patterns["episodic"], PatternStrength)

       def test_calibrate(self):


           """Test calibration of the model."""
           # Create observed data
           observed_data = {
           "mood_valence": -0.2,
           "anxiety_level": 0.5,
           "sleep_quality": 0.6,
           "serotonin_level": 0.0,
           "treatment_response": {
           "ssri": 0.6,
           "therapy": 0.5
           }
}

# Calibrate the model
calibration_score = self.digital_twin.calibrate(observed_data)

# Verify calibration
assert isinstance(calibration_score, float)
assert 0.0 <= calibration_score <= 1.0
assert self.digital_twin.calibration_score ==  calibration_score
assert self.digital_twin.last_calibration is not None

            def test_evaluate_accuracy(self):


                """Test evaluation of model accuracy."""
# Create validation data
validation_data = {
"actual_values": {
"mood_valence": [-0.3, -0.2, -0.1, 0.0, 0.1],
"anxiety_level": [0.6, 0.5, 0.5, 0.4, 0.3],
"sleep_quality": [0.4, 0.5, 0.5, 0.6, 0.7]
},
"predicted_values": {
"mood_valence": [-0.35, -0.25, -0.15, -0.05, 0.05],
"anxiety_level": [0.65, 0.55, 0.45, 0.35, 0.25],
"sleep_quality": [0.45, 0.5, 0.55, 0.6, 0.65]
},
"binary_outcomes": {
"actual": [1, 0, 1, 1, 0],
"predicted": [1, 0, 0, 1, 0]
}
}

# Evaluate accuracy
metrics = self.digital_twin.evaluate_accuracy(validation_data)

# Verify metrics
assert "rmse" in metrics
assert "mae" in metrics
assert "r_squared" in metrics
assert "auc" in metrics
assert all(0.0 <= value <= 1.0 for value in metrics.values())
assert self.digital_twin.validation_metrics ==  metrics

        def test_neurotransmitter_update(self):


            """Test updating neurotransmitter state."""
# Create neurotransmitter data
neurotransmitter_data = {
"serotonin": {
"level": 0.3,
"receptor_sensitivity": 0.4
},
"dopamine": {
"level": 0.2
},
"norepinephrine": {
"receptor_sensitivity": 0.1
}
}

# Get current values
original_serotonin = self.digital_twin.current_state.neurotransmitter.serotonin_level
original_dopamine = self.digital_twin.current_state.neurotransmitter.dopamine_level
original_norepinephrine_sensitivity = self.digital_twin.current_state.neurotransmitter.norepinephrine_receptor_sensitivity

# Update neurotransmitter state
self.digital_twin._update_neurotransmitter_state(neurotransmitter_data)

# Verify updates
assert self.digital_twin.current_state.neurotransmitter.serotonin_level ==  0.3
assert self.digital_twin.current_state.neurotransmitter.serotonin_receptor_sensitivity ==  0.4
assert self.digital_twin.current_state.neurotransmitter.dopamine_level ==  0.2
assert self.digital_twin.current_state.neurotransmitter.norepinephrine_receptor_sensitivity ==  0.1

# Verify unchanged values remain the same
assert self.digital_twin.current_state.neurotransmitter.dopamine_receptor_sensitivity ==  self.initial_state.neurotransmitter.dopamine_receptor_sensitivity
assert self.digital_twin.current_state.neurotransmitter.norepinephrine_level ==  self.initial_state.neurotransmitter.norepinephrine_level

        def test_psychological_update(self):


            """Test updating psychological state."""
# Create psychological data
psychological_data = {
"mood": {
"valence": 0.1,
"arousal": 0.3,
"stability": 0.5
},
"anxiety": {
"level": 0.3
},
"thought_patterns": {
"rumination": 0.2
}
}

# Update psychological state
self.digital_twin._update_psychological_state(psychological_data)

# Verify updates
assert self.digital_twin.current_state.psychological.mood_valence ==  0.1
assert self.digital_twin.current_state.psychological.mood_arousal ==  0.3
assert self.digital_twin.current_state.psychological.mood_stability ==  0.5
assert self.digital_twin.current_state.psychological.anxiety_level ==  0.3
assert self.digital_twin.current_state.psychological.rumination ==  0.2

# Verify unchanged values remain the same
assert self.digital_twin.current_state.psychological.stress_reactivity ==  self.initial_state.psychological.stress_reactivity
assert self.digital_twin.current_state.psychological.anhedonia ==  self.initial_state.psychological.anhedonia

        def test_behavioral_update(self):


            """Test updating behavioral state."""
# Create behavioral data
behavioral_data = {
"activity": {
"level": 0.2,
"psychomotor_changes": 0.1
},
"sleep": {
"quality": 0.7,
"duration": 7.5
},
"appetite": {
"level": 0.1
}
}

# Update behavioral state
self.digital_twin._update_behavioral_state(behavioral_data)

# Verify updates
assert self.digital_twin.current_state.behavioral.activity_level ==  0.2
assert self.digital_twin.current_state.behavioral.psychomotor_changes ==  0.1
assert self.digital_twin.current_state.behavioral.sleep_quality ==  0.7
assert self.digital_twin.current_state.behavioral.sleep_duration ==  7.5
assert self.digital_twin.current_state.behavioral.appetite_level ==  0.1

# Verify unchanged values remain the same
assert self.digital_twin.current_state.behavioral.circadian_rhythm ==  self.initial_state.behavioral.circadian_rhythm
assert self.digital_twin.current_state.behavioral.weight_changes ==  self.initial_state.behavioral.weight_changes
assert self.digital_twin.current_state.behavioral.social_engagement ==  self.initial_state.behavioral.social_engagement

        def test_cognitive_update(self):


            """Test updating cognitive state."""
# Create cognitive data
cognitive_data = {
"attention": {
"level": 0.7,
"concentration": 0.6
},
"memory": {
"working_memory": 0.7,
"long_term_memory": 0.8
},
"executive_function": {
"level": 0.6,
"decision_making": 0.5
}
}

# Update cognitive state
self.digital_twin._update_cognitive_state(cognitive_data)

# Verify updates
assert self.digital_twin.current_state.cognitive.attention_level ==  0.7
assert self.digital_twin.current_state.cognitive.concentration ==  0.6
assert self.digital_twin.current_state.cognitive.working_memory ==  0.7
assert self.digital_twin.current_state.cognitive.long_term_memory ==  0.8
assert self.digital_twin.current_state.cognitive.executive_function ==  0.6
assert self.digital_twin.current_state.cognitive.decision_making ==  0.5

# Verify unchanged values remain the same
assert self.digital_twin.current_state.cognitive.processing_speed ==  self.initial_state.cognitive.processing_speed
assert self.digital_twin.current_state.cognitive.cognitive_flexibility ==  self.initial_state.cognitive.cognitive_flexibility
assert self.digital_twin.current_state.cognitive.insight ==  self.initial_state.cognitive.insight


# Missing imports
# Removed import of non-existent TherapyType, TherapyDetails


            if __name__ == '__main__':
unittest.main()
