"""
Unit tests for the Treatment entity within the Digital Twin system.

This module contains tests for various treatment representations, including
medications, therapies, and lifestyle interventions, as well as treatment
plans and response predictions.
"""
import unittest
import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Dict, List, Any

from app.domain.entities.digital_twin.treatment import (
    Treatment,
    TreatmentCategory,
    TreatmentFrequency,
    MedicationDetails,
    MedicationType,
    TherapyDetails,
    TherapyType,
    LifestyleIntervention,
    InterventionType,
    TreatmentPlan,
    TreatmentResponse,
    TreatmentAnalysis
)


@pytest.mark.db_required
class TestMedicationTreatment(unittest.TestCase):
    """Tests for the Medication Treatment entity."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.start_date = datetime.utcnow()
        self.patient_id = uuid4()
        
        # Create a medication treatment
        self.medication = Treatment(
            id=uuid4(),
            name="Fluoxetine",
            category=TreatmentCategory.MEDICATION,
            frequency=TreatmentFrequency.DAILY,
            start_date=self.start_date,
            medication_details=MedicationDetails(
                type=MedicationType.SSRI,
                dosage=20.0,
                dosage_unit="mg",
                serotonin_effect=0.5,
                dopamine_effect=0.1,
                norepinephrine_effect=0.1,
                gaba_effect=0.0,
                glutamate_effect=0.0,
                half_life_hours=48,
                primary_targets=["serotonin transporters"],
                secondary_targets=["dopamine receptors"],
                metabolism_route="CYP2D6"
            )
        )
    
    @pytest.mark.db_required
def test_init_medication(self):
        """Test medication initialization."""
        assert self.medication.name == "Fluoxetine"
        assert self.medication.category == TreatmentCategory.MEDICATION
        assert self.medication.frequency == TreatmentFrequency.DAILY
        assert self.medication.start_date == self.start_date
        assert self.medication.end_date is None
        assert self.medication.is_active
        
        # Verify medication details
        assert self.medication.medication_details is not None
        assert self.medication.medication_details.type == MedicationType.SSRI
        assert self.medication.medication_details.dosage == 20.0
        assert self.medication.medication_details.dosage_unit == "mg"
        assert self.medication.medication_details.serotonin_effect == 0.5
        assert self.medication.medication_details.half_life_hours == 48
        assert "serotonin transporters" in self.medication.medication_details.primary_targets
    
    @pytest.mark.db_required
def test_calculate_effects(self):
        """Test calculation of medication effects."""
        # Calculate immediate effects
        immediate_effects = self.medication.calculate_immediate_effects()
        
        # Verify immediate effects
        assert "serotonin_level" in immediate_effects
        assert immediate_effects["serotonin_level"] > 0
        assert "dopamine_level" in immediate_effects
        assert immediate_effects["dopamine_level"] > 0
        assert "norepinephrine_level" in immediate_effects
        assert immediate_effects["norepinephrine_level"] > 0
        
        # Calculate long-term effects (after 4 weeks)
        long_term_effects = self.medication.calculate_long_term_effects(days=28)
        
        # Verify long-term effects (should be stronger)
        assert long_term_effects["serotonin_level"] > immediate_effects["serotonin_level"]
        assert "mood_valence" in long_term_effects
        assert "anxiety_level" in long_term_effects
        assert "rumination" in long_term_effects
    
    @pytest.mark.db_required
def test_medication_withdrawal(self):
        """Test effects of medication withdrawal."""
        # Set end date to simulate discontinuation
        self.medication.end_date = datetime.utcnow()
        
        # Calculate withdrawal effects
        withdrawal_effects = self.medication.calculate_withdrawal_effects(days_since_stop=3)
        
        # Verify withdrawal effects
        assert "serotonin_level" in withdrawal_effects
        assert withdrawal_effects["serotonin_level"] < 0  # Should decrease
        assert "mood_valence" in withdrawal_effects
        assert withdrawal_effects["mood_valence"] < 0  # Should decrease
        assert "anxiety_level" in withdrawal_effects
        assert withdrawal_effects["anxiety_level"] > 0  # Should increase
    
    @pytest.mark.db_required
def test_dose_response_curve(self):
        """Test dose-response relationship."""
        # Test standard dose
        standard_effects = self.medication.calculate_immediate_effects()
        
        # Create higher dose medication
        high_dose_med = Treatment(
            id=uuid4(),
            name="Fluoxetine",
            category=TreatmentCategory.MEDICATION,
            frequency=TreatmentFrequency.DAILY,
            start_date=self.start_date,
            medication_details=MedicationDetails(
                type=MedicationType.SSRI,
                dosage=40.0,  # Double dose
                dosage_unit="mg",
                serotonin_effect=0.5,
                dopamine_effect=0.1,
                norepinephrine_effect=0.1,
                gaba_effect=0.0,
                glutamate_effect=0.0
            )
        )
        
        # Calculate effects with higher dose
        high_dose_effects = high_dose_med.calculate_immediate_effects()
        
        # Verify higher dose produces stronger effects
        assert high_dose_effects["serotonin_level"] > standard_effects["serotonin_level"]
        
        # Create lower dose medication
        low_dose_med = Treatment(
            id=uuid4(),
            name="Fluoxetine",
            category=TreatmentCategory.MEDICATION,
            frequency=TreatmentFrequency.DAILY,
            start_date=self.start_date,
            medication_details=MedicationDetails(
                type=MedicationType.SSRI,
                dosage=10.0,  # Half dose
                dosage_unit="mg",
                serotonin_effect=0.5,
                dopamine_effect=0.1,
                norepinephrine_effect=0.1,
                gaba_effect=0.0,
                glutamate_effect=0.0
            )
        )
        
        # Calculate effects with lower dose
        low_dose_effects = low_dose_med.calculate_immediate_effects()
        
        # Verify lower dose produces weaker effects
        assert low_dose_effects["serotonin_level"] < standard_effects["serotonin_level"]
    
    @pytest.mark.db_required
def test_medication_duration(self):
        """Test effect duration based on medication half-life."""
        # Create medications with different half-lives
        short_half_life = Treatment(
            id=uuid4(),
            name="Short Acting Med",
            category=TreatmentCategory.MEDICATION,
            frequency=TreatmentFrequency.DAILY,
            start_date=self.start_date,
            medication_details=MedicationDetails(
                type=MedicationType.SSRI,
                dosage=20.0,
                dosage_unit="mg",
                half_life_hours=6,  # Short half-life
                serotonin_effect=0.5
            )
        )
        
        long_half_life = Treatment(
            id=uuid4(),
            name="Long Acting Med",
            category=TreatmentCategory.MEDICATION,
            frequency=TreatmentFrequency.DAILY,
            start_date=self.start_date,
            medication_details=MedicationDetails(
                type=MedicationType.SSRI,
                dosage=20.0,
                dosage_unit="mg",
                half_life_hours=72,  # Long half-life
                serotonin_effect=0.5
            )
        )
        
        # Simulate missed dose (24 hours since last dose)
        short_effect_after_miss = short_half_life.calculate_effect_at_time_point(hours_since_dose=24)
        long_effect_after_miss = long_half_life.calculate_effect_at_time_point(hours_since_dose=24)
        
        # Verify long half-life medication maintains more effect
        assert short_effect_after_miss["serotonin_level"] < long_effect_after_miss["serotonin_level"]


@pytest.mark.db_required
class TestTherapyTreatment(unittest.TestCase):
    """Tests for the Therapy Treatment entity."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.start_date = datetime.utcnow()
        self.patient_id = uuid4()
        
        # Create a therapy treatment
        self.therapy = Treatment(
            id=uuid4(),
            name="Cognitive Behavioral Therapy",
            category=TreatmentCategory.THERAPY,
            frequency=TreatmentFrequency.WEEKLY,
            start_date=self.start_date,
            therapy_details=TherapyDetails(
                type=TherapyType.CBT,
                session_duration_minutes=50,
                frequency=TreatmentFrequency.WEEKLY,
                approach="Cognitive restructuring and behavioral activation",
                target_symptoms=["depression", "anxiety"],
                expected_duration_weeks=16,
                domains_addressed=["cognitive", "behavioral", "emotional"],
                techniques=["cognitive restructuring", "behavioral activation", "exposure"]
            ),
            predicted_effects={
                "mood_valence": 0.3,
                "rumination": -0.4,
                "cognitive_distortions": -0.5,
                "anxiety_level": -0.3,
                "social_engagement": 0.3,
                "activity_level": 0.4
            }
        )
    
    @pytest.mark.db_required
def test_init_therapy(self):
        """Test therapy initialization."""
        assert self.therapy.name == "Cognitive Behavioral Therapy"
        assert self.therapy.category == TreatmentCategory.THERAPY
        assert self.therapy.frequency == TreatmentFrequency.WEEKLY
        assert self.therapy.start_date == self.start_date
        assert self.therapy.is_active
        
        # Verify therapy details
        assert self.therapy.therapy_details is not None
        assert self.therapy.therapy_details.type == TherapyType.CBT
        assert self.therapy.therapy_details.session_duration_minutes == 50
        assert self.therapy.therapy_details.expected_duration_weeks == 16
        assert "depression" in self.therapy.therapy_details.target_symptoms
        assert "cognitive restructuring" in self.therapy.therapy_details.techniques
    
    @pytest.mark.db_required
def test_calculate_effects(self):
        """Test calculation of therapy effects."""
        # Calculate session effects (immediate after a session)
        session_effects = self.therapy.calculate_session_effects()
        
        # Verify session effects
        assert "mood_valence" in session_effects
        assert session_effects["mood_valence"] > 0
        assert "rumination" in session_effects
        assert session_effects["rumination"] < 0  # Should decrease
        assert "cognitive_distortions" in session_effects
        assert session_effects["cognitive_distortions"] < 0  # Should decrease
        
        # Calculate long-term effects (after 8 weeks)
        long_term_effects = self.therapy.calculate_long_term_effects(weeks=8)
        
        # Verify long-term effects (should be stronger)
        assert long_term_effects["mood_valence"] > session_effects["mood_valence"]
        assert long_term_effects["rumination"] < session_effects["rumination"]
        assert "social_engagement" in long_term_effects
        assert long_term_effects["social_engagement"] > 0
    
    @pytest.mark.db_required
def test_different_therapy_types(self):
        """Test different types of therapy."""
        # Create IPT therapy
        ipt_therapy = Treatment(
            id=uuid4(),
            name="Interpersonal Therapy",
            category=TreatmentCategory.THERAPY,
            frequency=TreatmentFrequency.WEEKLY,
            start_date=self.start_date,
            therapy_details=TherapyDetails(
                type=TherapyType.IPT,
                session_duration_minutes=50,
                frequency=TreatmentFrequency.WEEKLY,
                approach="Resolving interpersonal problems",
                target_symptoms=["depression"],
                expected_duration_weeks=16,
                domains_addressed=["interpersonal", "emotional"],
                techniques=["role playing", "communication analysis"]
            ),
            predicted_effects={
                "mood_valence": 0.3,
                "social_engagement": 0.5,
                "interpersonal_functioning": 0.6
            }
        )
        
        # Create DBT therapy
        dbt_therapy = Treatment(
            id=uuid4(),
            name="Dialectical Behavior Therapy",
            category=TreatmentCategory.THERAPY,
            frequency=TreatmentFrequency.WEEKLY,
            start_date=self.start_date,
            therapy_details=TherapyDetails(
                type=TherapyType.DBT,
                session_duration_minutes=90,
                frequency=TreatmentFrequency.WEEKLY,
                approach="Skills training and emotional regulation",
                target_symptoms=["emotion dysregulation", "impulsivity"],
                expected_duration_weeks=24,
                domains_addressed=["emotional", "behavioral", "cognitive"],
                techniques=["mindfulness", "distress tolerance", "emotion regulation"]
            ),
            predicted_effects={
                "emotional_regulation": 0.6,
                "distress_tolerance": 0.5,
                "impulsivity": -0.4
            }
        )
        
        # Compare effects
        cbt_effects = self.therapy.calculate_long_term_effects(weeks=12)
        ipt_effects = ipt_therapy.calculate_long_term_effects(weeks=12)
        dbt_effects = dbt_therapy.calculate_long_term_effects(weeks=12)
        
        # Verify each therapy has strongest effect in its target domain
        assert cbt_effects["cognitive_distortions"] < ipt_effects.get("cognitive_distortions", 0)
        assert ipt_effects["social_engagement"] > cbt_effects.get("social_engagement", 0)
        assert dbt_effects["emotional_regulation"] > cbt_effects.get("emotional_regulation", 0)
        assert dbt_effects["emotional_regulation"] > ipt_effects.get("emotional_regulation", 0)
    
    @pytest.mark.db_required
def test_therapy_adherence_effects(self):
        """Test how adherence affects therapy outcomes."""
        # Calculate standard effects (full adherence)
        full_adherence = self.therapy.calculate_long_term_effects(weeks=12)
        
        # Calculate effects with partial adherence
        partial_adherence = self.therapy.calculate_long_term_effects(
            weeks=12, adherence_rate=0.5
        )
        
        # Calculate effects with poor adherence
        poor_adherence = self.therapy.calculate_long_term_effects(
            weeks=12, adherence_rate=0.2
        )
        
        # Verify adherence impacts outcomes
        assert full_adherence["mood_valence"] > partial_adherence["mood_valence"]
        assert partial_adherence["mood_valence"] > poor_adherence["mood_valence"]
        
        assert full_adherence["rumination"] < partial_adherence["rumination"]
        assert partial_adherence["rumination"] < poor_adherence["rumination"]


@pytest.mark.db_required
class TestLifestyleIntervention(unittest.TestCase):
    """Tests for the Lifestyle Intervention entity."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.start_date = datetime.utcnow()
        self.patient_id = uuid4()
        
        # Create an exercise intervention
        self.exercise = Treatment(
            id=uuid4(),
            name="Aerobic Exercise Program",
            category=TreatmentCategory.LIFESTYLE,
            frequency=TreatmentFrequency.DAILY,
            start_date=self.start_date,
            lifestyle_details=LifestyleIntervention(
                type=InterventionType.EXERCISE,
                intensity="moderate",
                frequency=TreatmentFrequency.DAILY,
                duration_minutes=30,
                description="30 minutes of moderate aerobic exercise",
                target_systems=["cardiovascular", "neurotransmitter", "stress response"],
                recommended_schedule="Morning"
            ),
            predicted_effects={
                "bdnf_level": 0.3,
                "serotonin_level": 0.2,
                "dopamine_level": 0.2,
                "stress_reactivity": -0.3,
                "mood_valence": 0.3,
                "sleep_quality": 0.2,
                "energy_level": 0.4
            }
        )
        
        # Create a sleep hygiene intervention
        self.sleep_hygiene = Treatment(
            id=uuid4(),
            name="Sleep Hygiene Protocol",
            category=TreatmentCategory.LIFESTYLE,
            frequency=TreatmentFrequency.DAILY,
            start_date=self.start_date,
            lifestyle_details=LifestyleIntervention(
                type=InterventionType.SLEEP,
                intensity="moderate",
                frequency=TreatmentFrequency.DAILY,
                description="Regular sleep schedule with pre-sleep routine",
                implementation_steps=[
                    "Regular sleep/wake times",
                    "No screens 1 hour before bed",
                    "Bedroom only for sleep",
                    "No caffeine after 2pm"
                ],
                target_systems=["circadian rhythm", "sleep regulation"]
            ),
            predicted_effects={
                "sleep_quality": 0.4,
                "sleep_duration": 1.0,  # 1 hour increase
                "circadian_rhythm": 0.5,
                "cognitive_function": 0.3,
                "mood_stability": 0.3
            }
        )
    
    @pytest.mark.db_required
def test_init_lifestyle(self):
        """Test lifestyle intervention initialization."""
        assert self.exercise.name == "Aerobic Exercise Program"
        assert self.exercise.category == TreatmentCategory.LIFESTYLE
        assert self.exercise.frequency == TreatmentFrequency.DAILY
        assert self.exercise.start_date == self.start_date
        assert self.exercise.is_active
        
        # Verify intervention details
        assert self.exercise.lifestyle_details is not None
        assert self.exercise.lifestyle_details.type == InterventionType.EXERCISE
        assert self.exercise.lifestyle_details.intensity == "moderate"
        assert self.exercise.lifestyle_details.duration_minutes == 30
        assert "cardiovascular" in self.exercise.lifestyle_details.target_systems
    
    @pytest.mark.db_required
def test_calculate_effects(self):
        """Test calculation of lifestyle intervention effects."""
        # Calculate immediate effects of exercise
        immediate_effects = self.exercise.calculate_immediate_effects()
        
        # Verify immediate effects
        assert "bdnf_level" in immediate_effects
        assert immediate_effects["bdnf_level"] > 0
        assert "serotonin_level" in immediate_effects
        assert immediate_effects["serotonin_level"] > 0
        assert "mood_valence" in immediate_effects
        assert immediate_effects["mood_valence"] > 0
        
        # Calculate cumulative effects (after 4 weeks)
        cumulative_effects = self.exercise.calculate_long_term_effects(weeks=4)
        
        # Verify cumulative effects
        assert cumulative_effects["bdnf_level"] > immediate_effects["bdnf_level"]
        assert "stress_reactivity" in cumulative_effects
        assert cumulative_effects["stress_reactivity"] < 0  # Should decrease
        assert "neuroplasticity" in cumulative_effects
        assert cumulative_effects["neuroplasticity"] > 0
    
    @pytest.mark.db_required
def test_sleep_intervention_effects(self):
        """Test effects of sleep hygiene intervention."""
        # Calculate immediate effects
        immediate_effects = self.sleep_hygiene.calculate_immediate_effects()
        
        # Verify immediate effects
        assert "sleep_quality" in immediate_effects
        assert immediate_effects["sleep_quality"] > 0
        assert "sleep_duration" in immediate_effects
        assert immediate_effects["sleep_duration"] > 0
        
        # Calculate cumulative effects (after 3 weeks)
        cumulative_effects = self.sleep_hygiene.calculate_long_term_effects(weeks=3)
        
        # Verify cumulative effects
        assert cumulative_effects["sleep_quality"] > immediate_effects["sleep_quality"]
        assert "circadian_rhythm" in cumulative_effects
        assert cumulative_effects["circadian_rhythm"] > 0
        assert "cognitive_function" in cumulative_effects
        assert cumulative_effects["cognitive_function"] > 0
        assert "mood_stability" in cumulative_effects
        assert cumulative_effects["mood_stability"] > 0
    
    @pytest.mark.db_required
def test_intervention_combinations(self):
        """Test combined effects of multiple lifestyle interventions."""
        # Calculate individual effects
        exercise_effects = self.exercise.calculate_long_term_effects(weeks=4)
        sleep_effects = self.sleep_hygiene.calculate_long_term_effects(weeks=4)
        
        # Create nutrition intervention
        nutrition = Treatment(
            id=uuid4(),
            name="Mediterranean Diet",
            category=TreatmentCategory.LIFESTYLE,
            frequency=TreatmentFrequency.DAILY,
            start_date=self.start_date,
            lifestyle_details=LifestyleIntervention(
                type=InterventionType.NUTRITION,
                intensity="moderate",
                frequency=TreatmentFrequency.DAILY,
                description="Mediterranean diet with emphasis on omega-3s",
                implementation_steps=[
                    "Increase fish consumption",
                    "Olive oil as primary fat",
                    "Increase vegetable intake",
                    "Reduce processed foods"
                ],
                target_systems=["inflammation", "gut-brain axis", "oxidative stress"]
            ),
            predicted_effects={
                "inflammation_markers": -0.3,
                "bdnf_level": 0.2,
                "gut_microbiome_diversity": 0.4,
                "oxidative_stress": -0.3
            }
        )
        
        # Calculate nutrition effects
        nutrition_effects = nutrition.calculate_long_term_effects(weeks=4)
        
        # Create combined intervention
        combined_plan = TreatmentPlan(
            id=uuid4(),
            patient_id=self.patient_id,
            name="Comprehensive Lifestyle Plan",
            treatments=[self.exercise, self.sleep_hygiene, nutrition],
            start_date=self.start_date,
            status="active"
        )
        
        # Calculate synergistic effects
        combined_effects = combined_plan.calculate_combined_effects(weeks=4)
        
        # Verify synergistic effects are greater than sum of parts for some domains
        individual_mood_effects = (
            exercise_effects.get("mood_valence", 0) +
            sleep_effects.get("mood_valence", 0) +
            nutrition_effects.get("mood_valence", 0)
        )
        assert combined_effects["mood_valence"] > individual_mood_effects
        
        individual_bdnf_effects = (
            exercise_effects.get("bdnf_level", 0) +
            nutrition_effects.get("bdnf_level", 0)
        )
        assert combined_effects["bdnf_level"] > individual_bdnf_effects


@pytest.mark.db_required
class TestTreatmentPlan(unittest.TestCase):
    """Tests for the TreatmentPlan entity."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.start_date = datetime.utcnow()
        self.patient_id = uuid4()
        
        # Create treatments
        self.medication = Treatment(
            id=uuid4(),
            name="Escitalopram",
            category=TreatmentCategory.MEDICATION,
            frequency=TreatmentFrequency.DAILY,
            start_date=self.start_date,
            medication_details=MedicationDetails(
                type=MedicationType.SSRI,
                dosage=10.0,
                dosage_unit="mg",
                serotonin_effect=0.5,
                dopamine_effect=0.0,
                norepinephrine_effect=0.0
            )
        )
        
        self.therapy = Treatment(
            id=uuid4(),
            name="Cognitive Behavioral Therapy",
            category=TreatmentCategory.THERAPY,
            frequency=TreatmentFrequency.WEEKLY,
            start_date=self.start_date,
            therapy_details=TherapyDetails(
                type=TherapyType.CBT,
                session_duration_minutes=50,
                frequency=TreatmentFrequency.WEEKLY,
                approach="Cognitive restructuring",
                target_symptoms=["depression", "anxiety"]
            )
        )
        
        self.exercise = Treatment(
            id=uuid4(),
            name="Walking Program",
            category=TreatmentCategory.LIFESTYLE,
            frequency=TreatmentFrequency.DAILY,
            start_date=self.start_date,
            lifestyle_details=LifestyleIntervention(
                type=InterventionType.EXERCISE,
                intensity="moderate",
                frequency=TreatmentFrequency.DAILY,
                duration_minutes=30
            )
        )
        
        # Create treatment plan
        self.treatment_plan = TreatmentPlan(
            id=uuid4(),
            patient_id=self.patient_id,
            name="Depression Treatment Plan",
            description="Comprehensive plan for moderate depression",
            treatments=[self.medication, self.therapy, self.exercise],
            start_date=self.start_date,
            target_conditions=["depression", "anxiety"],
            target_symptoms=["mood", "rumination", "sleep", "energy"],
            expected_duration_weeks=12,
            status="active"
        )
    
    @pytest.mark.db_required
def test_init_treatment_plan(self):
        """Test treatment plan initialization."""
        assert self.treatment_plan.name == "Depression Treatment Plan"
        assert self.treatment_plan.patient_id == self.patient_id
        assert len(self.treatment_plan.treatments) == 3
        assert self.treatment_plan.start_date == self.start_date
        assert self.treatment_plan.end_date is None
        assert self.treatment_plan.status == "active"
        assert "depression" in self.treatment_plan.target_conditions
        assert "sleep" in self.treatment_plan.target_symptoms
        assert self.treatment_plan.expected_duration_weeks == 12
    
    @pytest.mark.db_required
def test_get_active_treatments(self):
        """Test retrieving active treatments."""
        # All treatments should be active
        active_treatments = self.treatment_plan.get_active_treatments()
        assert len(active_treatments) == 3
        
        # End one treatment
        self.medication.end_date = datetime.utcnow()
        self.medication.status = "completed"
        
        # Check active treatments again
        active_treatments = self.treatment_plan.get_active_treatments()
        assert len(active_treatments) == 2
        assert self.medication not in active_treatments
        assert self.therapy in active_treatments
        assert self.exercise in active_treatments
    
    @pytest.mark.db_required
def test_calculate_combined_effects(self):
        """Test calculation of combined treatment effects."""
        # Calculate combined effects after 4 weeks
        combined_effects = self.treatment_plan.calculate_combined_effects(weeks=4)
        
        # Verify combined effects
        assert "serotonin_level" in combined_effects
        assert "mood_valence" in combined_effects
        assert "rumination" in combined_effects
        assert "anxiety_level" in combined_effects
        assert "activity_level" in combined_effects
        assert "cognitive_distortions" in combined_effects
        
        # Calculate individual effects
        med_effects = self.medication.calculate_long_term_effects(weeks=4)
        therapy_effects = self.therapy.calculate_long_term_effects(weeks=4)
        exercise_effects = self.exercise.calculate_long_term_effects(weeks=4)
        
        # Verify synergistic effects
        assert combined_effects["mood_valence"] > (
            med_effects.get("mood_valence", 0) +
            therapy_effects.get("mood_valence", 0) +
            exercise_effects.get("mood_valence", 0)
        )
    
    @pytest.mark.db_required
def test_treatment_interactions(self):
        """Test detection of treatment interactions."""
        # Add a treatment with potential interactions
        interacting_med = Treatment(
            id=uuid4(),
            name="Bupropion",
            category=TreatmentCategory.MEDICATION,
            frequency=TreatmentFrequency.DAILY,
            start_date=self.start_date,
            medication_details=MedicationDetails(
                type=MedicationType.NDRI,
                dosage=150.0,
                dosage_unit="mg",
                serotonin_effect=0.0,
                dopamine_effect=0.4,
                norepinephrine_effect=0.3,
                interactions=["SSRI", "MAOI"],
                interaction_risk="moderate"
            )
        )
        
        # Add to treatment plan
        self.treatment_plan.add_treatment(interacting_med)
        
        # Check for interactions
        interactions = self.treatment_plan.check_for_interactions()
        
        # Verify interactions detected
        assert len(interactions) > 0
        assert any(interaction["severity"] == "moderate" for interaction in interactions)
        assert any(
            interaction["involved_treatments"] == [self.medication.id, interacting_med.id]
            for interaction in interactions
        )
    
    @pytest.mark.db_required
def test_treatment_adjustment(self):
        """Test adjusting treatments within a plan."""
        # Initial dosage
        assert self.medication.medication_details.dosage == 10.0
        
        # Adjust medication dosage
        adjusted_medication = self.medication.copy(deep=True)
        adjusted_medication.medication_details.dosage = 20.0
        
        # Update treatment in plan
        self.treatment_plan.update_treatment(adjusted_medication)
        
        # Verify update
        updated_med = next(
            (t for t in self.treatment_plan.treatments if t.id == self.medication.id),
            None
        )
        assert updated_med is not None
        assert updated_med.medication_details.dosage == 20.0
        
        # Calculate effects with updated treatment
        effects_before = self.treatment_plan.calculate_combined_effects(weeks=4)
        
        # Record effects before adding new treatment
        mood_before = effects_before["mood_valence"]
        
        # Add augmentation treatment
        augmentation = Treatment(
            id=uuid4(),
            name="Lithium",
            category=TreatmentCategory.MEDICATION,
            frequency=TreatmentFrequency.DAILY,
            start_date=datetime.utcnow(),
            medication_details=MedicationDetails(
                type=MedicationType.MOOD_STABILIZER,
                dosage=300.0,
                dosage_unit="mg",
                serotonin_effect=0.1,
                dopamine_effect=0.1,
                norepinephrine_effect=0.0,
                predicted_augmentation_factor=1.3  # 30% boost to primary antidepressant
            )
        )
        
        # Add augmentation to plan
        self.treatment_plan.add_treatment(augmentation)
        
        # Calculate effects after augmentation
        effects_after = self.treatment_plan.calculate_combined_effects(weeks=4)
        
        # Verify augmentation increased effects
        assert effects_after["mood_valence"] > mood_before
    
    @pytest.mark.db_required
def test_treatment_plan_progress(self):
        """Test monitoring treatment plan progress."""
        # Simulate starting the plan
        self.treatment_plan.status = "active"
        start_date = datetime.utcnow() - timedelta(weeks=6)
        self.treatment_plan.start_date = start_date
        
        for treatment in self.treatment_plan.treatments:
            treatment.start_date = start_date
        
        # Calculate progress at 6 weeks
        progress = self.treatment_plan.calculate_progress()
        
        # Verify progress metrics
        assert "weeks_elapsed" in progress
        assert progress["weeks_elapsed"] == 6
        assert "percent_complete" in progress
        assert progress["percent_complete"] == 50.0  # 6/12 weeks
        assert "current_phase" in progress
        assert "remaining_weeks" in progress
        assert progress["remaining_weeks"] == 6


@pytest.mark.db_required
class TestTreatmentResponse(unittest.TestCase):
    """Tests for the TreatmentResponse entity."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.patient_id = uuid4()
        self.digital_twin_id = uuid4()
        self.treatment_id = uuid4()
        
        # Create a treatment response
        self.treatment_response = TreatmentResponse(
            id=uuid4(),
            patient_id=self.patient_id,
            digital_twin_id=self.digital_twin_id,
            treatment_id=self.treatment_id,
            prediction_date=datetime.utcnow(),
            efficacy=0.7,
            side_effects={
                "nausea": 0.3,
                "insomnia": 0.2,
                "headache": 0.1
            },
            time_to_response=21,  # days
            time_to_remission=42,  # days
            remission_probability=0.6,
            relapse_risk=0.3,
            confidence_level="MODERATE",
            symptom_changes={
                "mood_valence": 0.4,
                "anxiety_level": -0.3,
                "rumination": -0.4,
                "sleep_quality": 0.2
            }
        )
    
    @pytest.mark.db_required
def test_init_treatment_response(self):
        """Test treatment response initialization."""
        assert self.treatment_response.patient_id == self.patient_id
        assert self.treatment_response.digital_twin_id == self.digital_twin_id
        assert self.treatment_response.treatment_id == self.treatment_id
        assert isinstance(self.treatment_response.prediction_date, datetime)
        assert self.treatment_response.efficacy == 0.7
        assert self.treatment_response.side_effects["nausea"] == 0.3
        assert self.treatment_response.time_to_response == 21
        assert self.treatment_response.time_to_remission == 42
        assert self.treatment_response.remission_probability == 0.6
        assert self.treatment_response.relapse_risk == 0.3
        assert self.treatment_response.confidence_level == "MODERATE"
        assert self.treatment_response.symptom_changes["mood_valence"] == 0.4
    
    @pytest.mark.db_required
def test_calculate_benefit_risk_ratio(self):
        """Test calculation of benefit-risk ratio."""
        ratio = self.treatment_response.calculate_benefit_risk_ratio()
        
        # Verify ratio
        assert isinstance(ratio, float)
        assert ratio > 1.0  # Benefits outweigh risks
        
        # Create a response with more severe side effects
        high_risk_response = TreatmentResponse(
            id=uuid4(),
            patient_id=self.patient_id,
            digital_twin_id=self.digital_twin_id,
            treatment_id=self.treatment_id,
            efficacy=0.5,
            side_effects={
                "severe_nausea": 0.7,
                "severe_insomnia": 0.6,
                "severe_headache": 0.5
            }
        )
        
        # Calculate ratio for high-risk response
        high_risk_ratio = high_risk_response.calculate_benefit_risk_ratio()
        
        # Verify high-risk ratio is lower
        assert high_risk_ratio < ratio
    
    @pytest.mark.db_required
def test_compare_to_population(self):
        """Test comparison to population norms."""
        population_norms = {
            "efficacy": {
                "mean": 0.5,
                "std_dev": 0.15
            },
            "side_effects": {
                "nausea": {
                    "mean": 0.25,
                    "std_dev": 0.1
                },
                "insomnia": {
                    "mean": 0.3,
                    "std_dev": 0.15
                }
            },
            "time_to_response": {
                "mean": 28,
                "std_dev": 7
            }
        }
        
        # Compare to population
        comparison = self.treatment_response.compare_to_population(population_norms)
        
        # Verify comparison
        assert "efficacy_percentile" in comparison
        assert 0 <= comparison["efficacy_percentile"] <= 100
        assert "side_effects_severity" in comparison
        assert "time_to_response_percentile" in comparison
        assert comparison["time_to_response_percentile"] > 50  # Faster than average
    
    @pytest.mark.db_required
def test_predict_adherence(self):
        """Test prediction of treatment adherence."""
        patient_factors = {
            "prior_adherence": 0.8,
            "side_effect_sensitivity": 0.6,
            "treatment_beliefs": 0.7,
            "social_support": 0.5
        }
        
        # Predict adherence
        adherence_prediction = self.treatment_response.predict_adherence(patient_factors)
        
        # Verify prediction
        assert "adherence_probability" in adherence_prediction
        assert 0.0 <= adherence_prediction["adherence_probability"] <= 1.0
        assert "key_factors" in adherence_prediction
        assert "recommendations" in adherence_prediction
    
    @pytest.mark.db_required
def test_trajectory_prediction(self):
        """Test prediction of treatment trajectory."""
        from app.domain.entities.digital_twin.temporal import TrajectoryPrediction
        
        # Create trajectory prediction
        trajectory = TrajectoryPrediction(
            time_points=[0, 7, 14, 21, 28, 35, 42],
            mood_values=[-0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2],
            anxiety_values=[0.6, 0.6, 0.5, 0.5, 0.4, 0.4, 0.3],
            confidence_intervals={
                "mood": [
                    [-0.5, -0.3], [-0.4, -0.2], [-0.3, -0.1],
                    [-0.2, 0.0], [-0.1, 0.1], [0.0, 0.2], [0.1, 0.3]
                ],
                "anxiety": [
                    [0.5, 0.7], [0.5, 0.7], [0.4, 0.6],
                    [0.4, 0.6], [0.3, 0.5], [0.3, 0.5], [0.2, 0.4]
                ]
            }
        )
        
        # Add trajectory to response
        self.treatment_response.trajectory = trajectory
        
        # Verify trajectory
        assert self.treatment_response.trajectory.time_points == [0, 7, 14, 21, 28, 35, 42]
        assert len(self.treatment_response.trajectory.mood_values) == 7
        assert len(self.treatment_response.trajectory.anxiety_values) == 7
        
        # Calculate slope of improvement
        mood_slope = trajectory.calculate_slope("mood")
        anxiety_slope = trajectory.calculate_slope("anxiety")
        
        # Verify slopes
        assert mood_slope > 0  # Mood improves (increases)
        assert anxiety_slope < 0  # Anxiety improves (decreases)
    
    @pytest.mark.db_required
def test_treatment_analysis(self):
        """Test treatment analysis entity."""
        # Create a second treatment response
        treatment_id_2 = uuid4()
        response_2 = TreatmentResponse(
            id=uuid4(),
            patient_id=self.patient_id,
            digital_twin_id=self.digital_twin_id,
            treatment_id=treatment_id_2,
            efficacy=0.6,
            side_effects={
                "nausea": 0.1,
                "dizziness": 0.2
            },
            time_to_response=28,
            remission_probability=0.5,
            symptom_changes={
                "mood_valence": 0.3,
                "anxiety_level": -0.4,
                "energy_level": 0.2
            }
        )
        
        # Create treatment analysis
        treatment_analysis = TreatmentAnalysis(
            id=uuid4(),
            patient_id=self.patient_id,
            digital_twin_id=self.digital_twin_id,
            treatment_responses=[self.treatment_response, response_2],
            analysis_date=datetime.utcnow(),
            rankings=[
                {"treatment_id": self.treatment_id, "rank": 1, "reason": "Higher efficacy"},
                {"treatment_id": treatment_id_2, "rank": 2, "reason": "Slower response time"}
            ],
            recommendations={
                "recommended_treatment_id": self.treatment_id,
                "rationale": "Better overall efficacy and faster response time",
                "alternative_options": [treatment_id_2],
                "patient_specific_factors": ["Fast response needed", "Prior good SSRI response"]
            },
            confidence_level="MODERATE"
        )
        
        # Verify analysis
        assert treatment_analysis.patient_id == self.patient_id
        assert len(treatment_analysis.treatment_responses) == 2
        assert len(treatment_analysis.rankings) == 2
        assert treatment_analysis.rankings[0]["rank"] == 1
        assert treatment_analysis.rankings[0]["treatment_id"] == self.treatment_id
        assert treatment_analysis.recommendations["recommended_treatment_id"] == self.treatment_id
        assert "alternative_options" in treatment_analysis.recommendations
        assert treatment_analysis.confidence_level == "MODERATE"


if __name__ == '__main__':
    unittest.main()