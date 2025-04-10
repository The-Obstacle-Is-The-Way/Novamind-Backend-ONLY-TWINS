"""
Integration tests for the Digital Twin and Patient entities.

This module tests the integration between the Digital Twin and Patient domain entities,
ensuring they work together properly within the domain layer.
"""
import unittest
import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Dict, List, Any, Optional

from app.domain.entities.digital_twin.digital_twin import (
    DigitalTwin,
    # ModelConfidence # Removed non-existent import
)
from app.domain.entities.digital_twin.state import DigitalTwinState
from app.domain.entities.digital_twin.treatment import (
    Treatment,
    TreatmentCategory,
    TreatmentFrequency,
    TreatmentPlan
)
from app.domain.entities.patient.patient import (
    Patient,
    PatientStatus,
    PatientDemographics,
    MedicalRecord
)
from app.domain.entities.patient.assessment import (
    Assessment,
    AssessmentType,
    AssessmentStatus
)


class TestPatientDigitalTwinIntegration(unittest.TestCase):
    """Tests for the integration between Patient and DigitalTwin entities."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a patient
        self.patient_id = uuid4()
        self.patient = Patient(
            id=self.patient_id,
            status=PatientStatus.ACTIVE,
            demographics=PatientDemographics(
                age=35,
                gender="female",
                race="white",
                ethnicity="non-hispanic",
                education_level="college",
                employment_status="employed"
            ),
            medical_record=MedicalRecord(
                diagnoses=["major depressive disorder", "generalized anxiety disorder"],
                medications=[
                    {"name": "fluoxetine", "dosage": "20mg", "status": "active"}
                ],
                allergies=["penicillin"],
                family_history=["depression", "anxiety"],
                previous_treatments=["CBT", "SSRIs"]
            ),
            genetic_data={
                "cyp2d6_metabolizer": "normal",
                "cyp2c19_metabolizer": "rapid"
            },
            contact_information={
                "phone": "555-123-4567",
                "email": "patient@example.com",
                "address": "123 Main St, Anytown, USA"
            },
            preferences={
                "contact_method": "email",
                "appointment_reminder": True,
                "data_sharing_consent": True
            },
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow()
        )
        
        # Create a digital twin
        self.digital_twin = DigitalTwin(
            patient_id=self.patient_id,
            current_state=DigitalTwinState(),
            demographic_factors={
                "age": 35,
                "gender": "female",
                "education_level": "college"
            },
            genetic_factors={
                "cyp2d6_metabolizer": "normal",
                "cyp2c19_metabolizer": "rapid"
            },
            medical_history={
                "diagnoses": ["major depressive disorder", "generalized anxiety disorder"],
                "previous_treatments": ["CBT", "SSRIs"]
            },
            environmental_factors={
                "employment_status": "employed",
                "social_support": "moderate",
                "stress_level": "moderate"
            },
            confidence_level=0.7 # Replaced with float value
        )
        
        # Create assessments
        self.initial_assessment = Assessment(
            id=uuid4(),
            patient_id=self.patient_id,
            type=AssessmentType.PHQ9,
            status=AssessmentStatus.COMPLETED,
            score=15,
            responses={
                "q1": 2,  # Little interest or pleasure
                "q2": 2,  # Feeling down or depressed
                "q3": 2,  # Trouble sleeping
                "q4": 1,  # Feeling tired
                "q5": 1,  # Poor appetite or overeating
                "q6": 2,  # Feeling bad about yourself
                "q7": 1,  # Trouble concentrating
                "q8": 2,  # Moving slowly or fidgety
                "q9": 2   # Thoughts of self-harm
            },
            administered_at=datetime.utcnow() - timedelta(days=29),
            completed_at=datetime.utcnow() - timedelta(days=29),
            clinician_notes="Initial assessment shows moderate to severe depression",
            interpretation="Moderate to severe depression requiring treatment"
        )
        
        self.anxiety_assessment = Assessment(
            id=uuid4(),
            patient_id=self.patient_id,
            type=AssessmentType.GAD7,
            status=AssessmentStatus.COMPLETED,
            score=12,
            responses={
                "q1": 2,  # Feeling nervous or anxious
                "q2": 1,  # Can't stop worrying
                "q3": 2,  # Worrying too much
                "q4": 2,  # Trouble relaxing
                "q5": 1,  # Restlessness
                "q6": 2,  # Easily annoyed
                "q7": 2   # Feeling afraid
            },
            administered_at=datetime.utcnow() - timedelta(days=29),
            completed_at=datetime.utcnow() - timedelta(days=29),
            interpretation="Moderate anxiety"
        )
        
        self.follow_up_assessment = Assessment(
            id=uuid4(),
            patient_id=self.patient_id,
            type=AssessmentType.PHQ9,
            status=AssessmentStatus.COMPLETED,
            score=10,
            responses={
                "q1": 1,  # Little interest or pleasure
                "q2": 2,  # Feeling down or depressed
                "q3": 1,  # Trouble sleeping
                "q4": 1,  # Feeling tired
                "q5": 1,  # Poor appetite or overeating
                "q6": 1,  # Feeling bad about yourself
                "q7": 1,  # Trouble concentrating
                "q8": 1,  # Moving slowly or fidgety
                "q9": 1   # Thoughts of self-harm
            },
            administered_at=datetime.utcnow() - timedelta(days=15),
            completed_at=datetime.utcnow() - timedelta(days=15),
            clinician_notes="Some improvement since starting medication",
            interpretation="Moderate depression with slight improvement"
        )
        
        # Add assessments to patient
        self.patient.assessment_history = [
            self.initial_assessment,
            self.anxiety_assessment,
            self.follow_up_assessment
        ]
        
        # Create a treatment plan
        medication = Treatment(
            id=uuid4(),
            name="Fluoxetine",
            category=TreatmentCategory.MEDICATION,
            frequency=TreatmentFrequency.DAILY,
            start_date=datetime.utcnow() - timedelta(days=28),
            medication_details={
                "type": "SSRI",
                "dosage": 20.0,
                "dosage_unit": "mg"
            }
        )
        
        therapy = Treatment(
            id=uuid4(),
            name="Cognitive Behavioral Therapy",
            category=TreatmentCategory.THERAPY,
            frequency=TreatmentFrequency.WEEKLY,
            start_date=datetime.utcnow() - timedelta(days=21),
            therapy_details={
                "type": "CBT",
                "session_duration_minutes": 50,
                "frequency": "WEEKLY"
            }
        )
        
        self.treatment_plan = TreatmentPlan(
            id=uuid4(),
            patient_id=self.patient_id,
            name="Depression Treatment Plan",
            treatments=[medication, therapy],
            start_date=datetime.utcnow() - timedelta(days=28),
            status="active"
        )
        
        # Add treatment plan to patient
        self.patient.treatment_plans = [self.treatment_plan]
    
    def test_create_digital_twin_from_patient(self):
        """Test creating a digital twin from patient data."""
        # Create a factory function to generate a digital twin from patient data
        def create_digital_twin_from_patient(patient: Patient) -> DigitalTwin:
            """Factory function to create a digital twin from patient data."""
            # Extract demographic factors
            demographic_factors = {
                "age": patient.demographics.age,
                "gender": patient.demographics.gender,
                "education_level": patient.demographics.education_level,
                "employment_status": patient.demographics.employment_status
            }
            
            # Extract medical history
            medical_history = {
                "diagnoses": patient.medical_record.diagnoses,
                "previous_treatments": patient.medical_record.previous_treatments,
                "family_history": patient.medical_record.family_history
            }
            
            # Create the digital twin
            return DigitalTwin(
                patient_id=patient.id,
                current_state=DigitalTwinState(),
                demographic_factors=demographic_factors,
                genetic_factors=patient.genetic_data,
                medical_history=medical_history,
                confidence_level=0.7 # Replaced with float value
            )
        
        # Create a digital twin from the patient
        twin = create_digital_twin_from_patient(self.patient)
        
        # Verify the digital twin has the correct data
        assert twin.patient_id == self.patient.id
        assert twin.demographic_factors["age"] == self.patient.demographics.age
        assert twin.demographic_factors["gender"] == self.patient.demographics.gender
        assert twin.genetic_factors == self.patient.genetic_data
        assert "diagnoses" in twin.medical_history
        assert "major depressive disorder" in twin.medical_history["diagnoses"]
    
    def test_update_digital_twin_from_assessment(self):
        """Test updating a digital twin based on assessment data."""
        # Define a function to update the digital twin from assessment
        def update_digital_twin_from_assessment(
            twin: DigitalTwin, 
            assessment: Assessment
        ) -> DigitalTwin:
            """Update digital twin based on assessment data."""
            # Extract relevant data based on assessment type
            if assessment.type == AssessmentType.PHQ9:
                # Map PHQ-9 responses to digital twin state
                update_data = {
                    "psychological_data": {
                        "mood": {
                            "valence": map_phq9_to_mood_valence(assessment.score),
                            "stability": map_phq9_to_mood_stability(assessment.responses)
                        },
                        "thought_patterns": {
                            "rumination": map_phq9_to_rumination(assessment.responses),
                            "anhedonia": map_phq9_to_anhedonia(assessment.responses.get("q1", 0))
                        }
                    },
                    "behavioral_data": {
                        "sleep": {
                            "quality": map_phq9_to_sleep_quality(assessment.responses.get("q3", 0))
                        },
                        "energy": {
                            "level": map_phq9_to_energy_level(assessment.responses.get("q4", 0))
                        },
                        "appetite": {
                            "level": map_phq9_to_appetite(assessment.responses.get("q5", 0))
                        },
                        "psychomotor": {
                            "changes": map_phq9_to_psychomotor(assessment.responses.get("q8", 0))
                        }
                    },
                    "cognitive_data": {
                        "concentration": {
                            "level": map_phq9_to_concentration(assessment.responses.get("q7", 0))
                        }
                    }
                }
            elif assessment.type == AssessmentType.GAD7:
                # Map GAD-7 responses to digital twin state
                update_data = {
                    "psychological_data": {
                        "anxiety": {
                            "level": map_gad7_to_anxiety_level(assessment.score),
                            "worry": map_gad7_to_worry(assessment)
                        },
                        "stress_reactivity": map_gad7_to_stress_reactivity(assessment)
                    },
                    "behavioral_data": {
                        "restlessness": {
                            "level": map_gad7_to_restlessness(assessment.responses.get("q5", 0))
                        }
                    }
                }
            else:
                # Handle other assessment types
                update_data = {}
            
            # Update the digital twin
            twin.update_state(update_data)
            return twin
        
        # Define mapping functions
        def map_phq9_to_mood_valence(score: int) -> float:
            """Map PHQ-9 score to mood valence."""
            # PHQ9 ranges from 0-27, map to -1.0 to 1.0 range
            # Higher PHQ9 = more depression = more negative valence
            if score == 0:
                return 0.5  # Normal mood
            elif score <= 5:
                return 0.3  # Mild depression
            elif score <= 10:
                return 0.0  # Moderate depression
            elif score <= 15:
                return -0.3  # Moderately severe depression
            elif score <= 20:
                return -0.6  # Severe depression
            else:
                return -0.9  # Very severe depression
        
        def map_phq9_to_mood_stability(responses: Dict[str, int]) -> float:
            """Map PHQ-9 responses to mood stability."""
            # Use variance in responses as a proxy for stability
            values = list(responses.values())
            variance = sum((x - sum(values)/len(values))**2 for x in values) / len(values)
            # Higher variance = lower stability
            return max(0.0, 1.0 - (variance / 2.0))
        
        def map_phq9_to_rumination(responses: Dict[str, int]) -> float:
            """Map PHQ-9 responses to rumination level."""
            # Use questions 2 and 6 as proxies for rumination
            q2 = responses.get("q2", 0)  # Feeling down/depressed
            q6 = responses.get("q6", 0)  # Feeling bad about yourself
            
            # Scale to 0.0-1.0 range
            return (q2 + q6) / 6.0
        
        def map_phq9_to_anhedonia(q1_value: int) -> float:
            """Map PHQ-9 question 1 to anhedonia level."""
            # Question 1 directly assesses anhedonia
            return q1_value / 3.0
        
        def map_phq9_to_sleep_quality(q3_value: int) -> float:
            """Map PHQ-9 question 3 to sleep quality."""
            # Question 3 assesses sleep problems
            # Invert since higher q3 = worse sleep = lower sleep quality
            return 1.0 - (q3_value / 3.0)
        
        def map_phq9_to_energy_level(q4_value: int) -> float:
            """Map PHQ-9 question 4 to energy level."""
            # Question 4 assesses fatigue
            # Invert since higher q4 = more fatigue = lower energy
            return 1.0 - (q4_value / 3.0)
        
        def map_phq9_to_appetite(q5_value: int) -> float:
            """Map PHQ-9 question 5 to appetite level."""
            # Question 5 assesses appetite changes
            # This is tricky as it could be increased or decreased
            if q5_value == 0:
                return 0.5  # Normal appetite
            else:
                return 0.5 - (q5_value / 6.0)  # Deviation from normal
        
        def map_phq9_to_psychomotor(q8_value: int) -> float:
            """Map PHQ-9 question 8 to psychomotor changes."""
            # Question 8 assesses psychomotor retardation or agitation
            # This is bidirectional, so use as severity of deviation
            return q8_value / 3.0
        
        def map_phq9_to_concentration(q7_value: int) -> float:
            """Map PHQ-9 question 7 to concentration level."""
            # Question 7 assesses concentration problems
            # Invert since higher q7 = worse concentration
            return 1.0 - (q7_value / 3.0)
        
        def map_gad7_to_anxiety_level(score: int) -> float:
            """Map GAD-7 score to anxiety level."""
            # GAD7 ranges from 0-21, map to 0.0 to 1.0 range
            # Higher GAD7 = more anxiety
            return min(1.0, score / 21.0)
        
        def map_gad7_to_worry(assessment: Assessment) -> float:
            """Map GAD-7 responses to worry level."""
            # Questions 1-3 assess worry
            q1 = assessment.responses.get("q1", 0)
            q2 = assessment.responses.get("q2", 0)
            q3 = assessment.responses.get("q3", 0)
            
            # Scale to 0.0-1.0 range
            return (q1 + q2 + q3) / 9.0
        
        def map_gad7_to_stress_reactivity(assessment: Assessment) -> float:
            """Map GAD-7 responses to stress reactivity."""
            # Use average of all responses as proxy for stress reactivity
            values = list(assessment.responses.values())
            return sum(values) / (len(values) * 3.0)
        
        def map_gad7_to_restlessness(q5_value: int) -> float:
            """Map GAD-7 question 5 to restlessness level."""
            # Question 5 directly assesses restlessness
            return q5_value / 3.0
        
        # Update the digital twin with the initial PHQ-9 assessment
        update_digital_twin_from_assessment(self.digital_twin, self.initial_assessment)
        
        # Verify the digital twin state was updated correctly
        assert self.digital_twin.current_state.psychological.mood_valence < 0
        assert self.digital_twin.current_state.behavioral.sleep_quality < 0.5
        
        # Update again with the follow-up assessment
        update_digital_twin_from_assessment(self.digital_twin, self.follow_up_assessment)
        
        # Verify the digital twin state shows improvement
        assert self.digital_twin.current_state.psychological.mood_valence > -0.5
        
        # Update with anxiety assessment
        update_digital_twin_from_assessment(self.digital_twin, self.anxiety_assessment)
        
        # Verify anxiety state was updated
        assert self.digital_twin.current_state.psychological.anxiety_level > 0.5
    
    def test_predict_treatment_response_from_patient_data(self):
        """Test predicting treatment response using patient data."""
        # Define a function to enhance twin prediction with patient data
        def predict_with_patient_context(
            twin: DigitalTwin,
            patient: Patient,
            treatment_id: UUID
        ) -> Dict[str, Any]:
            """Predict treatment response with context from patient data."""
            # Find the treatment in the patient's plan
            treatment = None
            for plan in patient.treatment_plans:
                for t in plan.treatments:
                    if t.id == treatment_id:
                        treatment = t
                        break
                if treatment:
                    break
            
            if not treatment:
                raise ValueError(f"Treatment {treatment_id} not found in patient plans")
            
            # Enhance prediction with patient-specific factors
            prediction_factors = {
                "genetic_factors": patient.genetic_data,
                "previous_response": get_previous_response(patient, treatment.name),
                "comorbidities": patient.medical_record.diagnoses,
                "adherence_factors": get_adherence_factors(patient)
            }
            
            # Get baseline prediction from digital twin
            baseline_prediction = twin.predict_treatment_response(treatment, time_horizon_days=28)
            
            # Adjust prediction based on patient factors
            adjusted_prediction = adjust_prediction_with_patient_factors(
                baseline_prediction, 
                prediction_factors
            )
            
            return adjusted_prediction
        
        def get_previous_response(patient: Patient, treatment_name: str) -> Optional[str]:
            """Get patient's previous response to similar treatments."""
            for treatment in patient.medical_record.previous_treatments:
                if treatment.lower() in treatment_name.lower():
                    return "positive"  # Simplified for test
            return None
        
        def get_adherence_factors(patient: Patient) -> Dict[str, Any]:
            """Get factors affecting medication adherence."""
            return {
                "social_support": "moderate",
                "complexity": "low",
                "side_effects": "moderate",
                "patient_beliefs": "positive"
            }
        
        def adjust_prediction_with_patient_factors(
            baseline_prediction: Dict[str, Any],
            patient_factors: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Adjust treatment prediction based on patient factors."""
            # Copy baseline prediction
            adjusted = baseline_prediction.copy()
            
            # Adjust efficacy based on genetic factors
            if "genetic_factors" in patient_factors:
                # Example: adjust SSRI efficacy based on CYP2C19 status
                if "cyp2c19_metabolizer" in patient_factors["genetic_factors"]:
                    status = patient_factors["genetic_factors"]["cyp2c19_metabolizer"]
                    if status == "poor":
                        adjusted["efficacy"] *= 1.2  # Better response
                    elif status == "rapid":
                        adjusted["efficacy"] *= 0.8  # Worse response
            
            # Adjust based on previous response
            if patient_factors.get("previous_response") == "positive":
                adjusted["efficacy"] *= 1.15
                adjusted["time_to_response"] = int(adjusted["time_to_response"] * 0.9)
            
            # Adjust based on adherence factors
            adherence = patient_factors.get("adherence_factors", {})
            adherence_score = 0.0
            
            if adherence.get("social_support") == "high":
                adherence_score += 0.1
            if adherence.get("complexity") == "low":
                adherence_score += 0.1
            if adherence.get("patient_beliefs") == "positive":
                adherence_score += 0.1
            
            # Apply adherence adjustment
            actual_efficacy = adjusted["efficacy"] * (1.0 + adherence_score)
            adjusted["efficacy"] = min(1.0, actual_efficacy)
            
            return adjusted
        
        # Find a treatment ID from the patient's plan
        treatment_id = self.patient.treatment_plans[0].treatments[0].id
        
        # Predict response with patient context
        prediction = predict_with_patient_context(
            self.digital_twin,
            self.patient,
            treatment_id
        )
        
        # Verify prediction has expected fields
        assert "efficacy" in prediction
        assert "time_to_response" in prediction
        assert "side_effects" in prediction
        assert isinstance(prediction["efficacy"], float)
        assert isinstance(prediction["time_to_response"], int)
    
    def test_integrate_assessment_history_with_digital_twin(self):
        """Test integrating assessment history with digital twin trajectory."""
        # Define a function to map assessment history to trajectory points
        def map_assessments_to_trajectory(
            assessments: List[Assessment]
        ) -> Dict[str, List[Any]]:
            """Map assessment history to trajectory points."""
            # Sort assessments by date
            sorted_assessments = sorted(
                assessments,
                key=lambda a: a.completed_at
            )
            
            # Initialize trajectory data
            trajectory = {
                "timestamps": [],
                "mood_values": [],
                "anxiety_values": [],
                "functional_impairment": []
            }
            
            # Map each assessment to trajectory points
            for assessment in sorted_assessments:
                if assessment.status != AssessmentStatus.COMPLETED:
                    continue
                
                trajectory["timestamps"].append(assessment.completed_at)
                
                if assessment.type == AssessmentType.PHQ9:
                    # Map PHQ-9 to mood and functional impairment
                    mood_valence = map_phq9_to_mood_valence(assessment.score)
                    trajectory["mood_values"].append(mood_valence)
                    
                    # Calculate functional impairment from PHQ-9
                    q5 = assessment.responses.get("q5", 0)  # Appetite
                    q7 = assessment.responses.get("q7", 0)  # Concentration
                    q8 = assessment.responses.get("q8", 0)  # Psychomotor
                    
                    functional_impairment = (q5 + q7 + q8) / 9.0
                    trajectory["functional_impairment"].append(functional_impairment)
                    
                    # If this is only a PHQ-9, use last anxiety value or 0
                    if trajectory["anxiety_values"]:
                        trajectory["anxiety_values"].append(trajectory["anxiety_values"][-1])
                    else:
                        trajectory["anxiety_values"].append(0.0)
                    
                elif assessment.type == AssessmentType.GAD7:
                    # Map GAD-7 to anxiety
                    anxiety_level = map_gad7_to_anxiety_level(assessment.score)
                    trajectory["anxiety_values"].append(anxiety_level)
                    
                    # If this is only a GAD-7, use last mood and functional values or 0
                    if trajectory["mood_values"]:
                        trajectory["mood_values"].append(trajectory["mood_values"][-1])
                    else:
                        trajectory["mood_values"].append(0.0)
                    
                    if trajectory["functional_impairment"]:
                        trajectory["functional_impairment"].append(
                            trajectory["functional_impairment"][-1]
                        )
                    else:
                        trajectory["functional_impairment"].append(0.0)
            
            return trajectory
        
        # Map the assessment history to a trajectory
        trajectory = map_assessments_to_trajectory(self.patient.assessment_history)
        
        # Verify trajectory
        assert len(trajectory["timestamps"]) == 3
        assert len(trajectory["mood_values"]) == 3
        assert len(trajectory["anxiety_values"]) == 3
        
        # Verify the trajectory shows improvement
        assert trajectory["mood_values"][2] > trajectory["mood_values"][0]
        
        # Verify trajectory can be used to forecast future state
        if self.digital_twin.temporal_dynamics is None:
            from app.domain.entities.digital_twin.temporal import TemporalDynamics
            self.digital_twin.temporal_dynamics = TemporalDynamics()
        
        # Update digital twin with the trajectory
        for i in range(len(trajectory["timestamps"])):
            # Create a state point from trajectory values
            state = DigitalTwinState()
            state.psychological.mood_valence = trajectory["mood_values"][i]
            state.psychological.anxiety_level = trajectory["anxiety_values"][i]
            
            # Record state point
            self.digital_twin.temporal_dynamics.record_state_point(
                state, 
                timestamp=trajectory["timestamps"][i]
            )
        
        # Forecast future trajectory
        if len(self.digital_twin.temporal_dynamics.state_history) >= 3:
            # Initialize forecasters
            self.digital_twin.temporal_dynamics.initialize_forecasters()
            
            # Forecast trajectory
            forecast = self.digital_twin.temporal_dynamics.forecast_trajectory(days=30)
            
            # Verify forecast exists
            assert forecast is not None
            assert len(forecast.time_points) > 0
            assert len(forecast.mood_values) > 0


class TestDigitalTwinTreatmentPlanIntegration(unittest.TestCase):
    """Tests for the integration between DigitalTwin and TreatmentPlan entities."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create patient ID
        self.patient_id = uuid4()
        
        # Create a digital twin
        self.digital_twin = DigitalTwin(
            patient_id=self.patient_id,
            current_state=DigitalTwinState(),
            demographic_factors={"age": 40, "gender": "male"}
        )
        
        # Create treatment plan with multiple treatments
        self.ssri = Treatment(
            id=uuid4(),
            name="Escitalopram",
            category=TreatmentCategory.MEDICATION,
            frequency=TreatmentFrequency.DAILY,
            start_date=datetime.utcnow() - timedelta(days=30),
            medication_details={
                "type": "SSRI",
                "dosage": 10.0,
                "dosage_unit": "mg"
            }
        )
        
        self.therapy = Treatment(
            id=uuid4(),
            name="Cognitive Behavioral Therapy",
            category=TreatmentCategory.THERAPY,
            frequency=TreatmentFrequency.WEEKLY,
            start_date=datetime.utcnow() - timedelta(days=28),
            therapy_details={
                "type": "CBT",
                "session_duration_minutes": 50
            }
        )
        
        self.exercise = Treatment(
            id=uuid4(),
            name="Aerobic Exercise",
            category=TreatmentCategory.LIFESTYLE,
            frequency=TreatmentFrequency.DAILY,
            start_date=datetime.utcnow() - timedelta(days=25),
            lifestyle_details={
                "type": "EXERCISE",
                "duration_minutes": 30
            }
        )
        
        self.treatment_plan = TreatmentPlan(
            id=uuid4(),
            patient_id=self.patient_id,
            name="Depression Treatment Plan",
            treatments=[self.ssri, self.therapy, self.exercise],
            start_date=datetime.utcnow() - timedelta(days=30),
            status="active"
        )
    
    def test_evaluate_treatment_plan_with_digital_twin(self):
        """Test evaluating a treatment plan using digital twin predictions."""
        # Define a function to evaluate a treatment plan
        def evaluate_treatment_plan(
            twin: DigitalTwin,
            plan: TreatmentPlan
        ) -> Dict[str, Any]:
            """Evaluate effectiveness of a treatment plan using digital twin."""
            # Get active treatments
            active_treatments = plan.get_active_treatments()
            
            # Generate individual predictions for each treatment
            treatment_predictions = {}
            for treatment in active_treatments:
                prediction = twin.predict_treatment_response(
                    treatment,
                    time_horizon_days=60
                )
                treatment_predictions[treatment.id] = prediction
            
            # Calculate combined effect
            combined_prediction = twin.predict_treatment_response(
                active_treatments,
                time_horizon_days=60
            )
            
            # Analyze synergistic effects
            synergy_analysis = analyze_treatment_synergy(
                treatment_predictions,
                combined_prediction
            )
            
            # Generate recommendations
            recommendations = generate_recommendations(
                twin,
                plan,
                treatment_predictions,
                combined_prediction
            )
            
            return {
                "individual_predictions": treatment_predictions,
                "combined_prediction": combined_prediction,
                "synergy_analysis": synergy_analysis,
                "recommendations": recommendations,
                "evaluation_date": datetime.utcnow()
            }
        
        def analyze_treatment_synergy(
            individual_predictions: Dict[UUID, Dict[str, Any]],
            combined_prediction: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Analyze synergistic effects between treatments."""
            # Calculate expected combined efficacy (sum of individual effects)
            expected_efficacy = sum(
                p.get("efficacy", 0) for p in individual_predictions.values()
            )
            
            # Compare with actual combined efficacy
            actual_efficacy = combined_prediction.get("efficacy", 0)
            
            # Calculate synergy factor
            synergy_factor = actual_efficacy / expected_efficacy if expected_efficacy > 0 else 1.0
            
            # Analyze time to response
            individual_times = [
                p.get("time_to_response", 60) for p in individual_predictions.values()
                if "time_to_response" in p
            ]
            expected_time = min(individual_times) if individual_times else 60
            actual_time = combined_prediction.get("time_to_response", 60)
            
            # Calculate time synergy
            time_synergy = expected_time / actual_time if actual_time > 0 else 1.0
            
            return {
                "efficacy_synergy": synergy_factor,
                "time_synergy": time_synergy,
                "synergistic_domains": identify_synergistic_domains(
                    individual_predictions,
                    combined_prediction
                )
            }
        
        def identify_synergistic_domains(
            individual_predictions: Dict[UUID, Dict[str, Any]],
            combined_prediction: Dict[str, Any]
        ) -> List[str]:
            """Identify domains with synergistic effects."""
            # Get symptom changes from each prediction
            individual_changes = {}
            for pred in individual_predictions.values():
                if "symptom_changes" in pred:
                    for domain, value in pred["symptom_changes"].items():
                        if domain not in individual_changes:
                            individual_changes[domain] = []
                        individual_changes[domain].append(value)
            
            # Compare with combined changes
            combined_changes = combined_prediction.get("symptom_changes", {})
            
            # Identify synergistic domains
            synergistic_domains = []
            for domain, values in individual_changes.items():
                if domain in combined_changes:
                    # Calculate expected change (sum of individual changes)
                    expected_change = sum(values)
                    actual_change = combined_changes[domain]
                    
                    # Check if actual change is significantly better
                    if abs(actual_change) > abs(expected_change) * 1.2:
                        synergistic_domains.append(domain)
            
            return synergistic_domains
        
        def generate_recommendations(
            twin: DigitalTwin,
            plan: TreatmentPlan,
            individual_predictions: Dict[UUID, Dict[str, Any]],
            combined_prediction: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Generate recommendations for treatment plan optimization."""
            # Check if any treatments have low efficacy
            low_efficacy_treatments = [
                t_id for t_id, pred in individual_predictions.items()
                if pred.get("efficacy", 0) < 0.3
            ]
            
            # Check for treatments with high side effects
            high_side_effect_treatments = [
                t_id for t_id, pred in individual_predictions.items()
                if pred.get("side_effect_severity", 0) > 0.7
            ]
            
            # Generate optimization recommendations
            optimizations = []
            
            if low_efficacy_treatments:
                optimizations.append({
                    "type": "REPLACEMENT",
                    "treatment_ids": low_efficacy_treatments,
                    "reason": "Low predicted efficacy",
                    "suggested_alternatives": suggest_alternatives(
                        twin, low_efficacy_treatments, plan
                    )
                })
            
            if high_side_effect_treatments:
                optimizations.append({
                    "type": "ADJUSTMENT",
                    "treatment_ids": high_side_effect_treatments,
                    "reason": "High predicted side effects",
                    "suggested_adjustments": suggest_adjustments(
                        high_side_effect_treatments, plan
                    )
                })
            
            # Analyze for missing treatment components
            missing_components = analyze_missing_components(twin, plan)
            if missing_components:
                optimizations.append({
                    "type": "ADDITION",
                    "reason": "Missing treatment components",
                    "suggested_additions": missing_components
                })
            
            return {
                "optimizations": optimizations,
                "overall_recommendation": generate_overall_recommendation(
                    combined_prediction, optimizations
                )
            }
        
        def suggest_alternatives(
            twin: DigitalTwin,
            treatment_ids: List[UUID],
            plan: TreatmentPlan
        ) -> Dict[UUID, List[Dict[str, Any]]]:
            """Suggest alternative treatments for low efficacy treatments."""
            # Simplified implementation for test purposes
            alternatives = {}
            
            for t_id in treatment_ids:
                treatment = next((t for t in plan.treatments if t.id == t_id), None)
                if treatment and treatment.category == TreatmentCategory.MEDICATION:
                    alternatives[t_id] = [
                        {
                            "name": "Alternative Medication 1",
                            "category": "MEDICATION",
                            "predicted_efficacy": 0.6
                        },
                        {
                            "name": "Alternative Medication 2",
                            "category": "MEDICATION",
                            "predicted_efficacy": 0.5
                        }
                    ]
                elif treatment and treatment.category == TreatmentCategory.THERAPY:
                    alternatives[t_id] = [
                        {
                            "name": "Alternative Therapy 1",
                            "category": "THERAPY",
                            "predicted_efficacy": 0.5
                        }
                    ]
            
            return alternatives
        
        def suggest_adjustments(
            treatment_ids: List[UUID],
            plan: TreatmentPlan
        ) -> Dict[UUID, List[Dict[str, Any]]]:
            """Suggest adjustments for treatments with high side effects."""
            # Simplified implementation for test purposes
            adjustments = {}
            
            for t_id in treatment_ids:
                treatment = next((t for t in plan.treatments if t.id == t_id), None)
                if treatment and treatment.category == TreatmentCategory.MEDICATION:
                    adjustments[t_id] = [
                        {
                            "type": "DOSAGE_REDUCTION",
                            "details": "Reduce dosage by 25%",
                            "predicted_side_effect_reduction": 0.3
                        },
                        {
                            "type": "TIMING_CHANGE",
                            "details": "Take with food",
                            "predicted_side_effect_reduction": 0.2
                        }
                    ]
            
            return adjustments
        
        def analyze_missing_components(
            twin: DigitalTwin,
            plan: TreatmentPlan
        ) -> List[Dict[str, Any]]:
            """Analyze for missing treatment components."""
            # Check for treatment categories
            has_medication = any(
                t.category == TreatmentCategory.MEDICATION
                for t in plan.treatments
            )
            has_therapy = any(
                t.category == TreatmentCategory.THERAPY
                for t in plan.treatments
            )
            has_lifestyle = any(
                t.category == TreatmentCategory.LIFESTYLE
                for t in plan.treatments
            )
            
            # Generate suggestions for missing components
            missing = []
            
            if not has_medication:
                missing.append({
                    "category": "MEDICATION",
                    "recommendation": "Consider adding medication",
                    "options": ["SSRI", "SNRI", "Atypical antidepressant"]
                })
            
            if not has_therapy:
                missing.append({
                    "category": "THERAPY",
                    "recommendation": "Consider adding psychotherapy",
                    "options": ["CBT", "IPT", "Mindfulness-based therapy"]
                })
            
            if not has_lifestyle:
                missing.append({
                    "category": "LIFESTYLE",
                    "recommendation": "Consider adding lifestyle intervention",
                    "options": ["Exercise program", "Sleep hygiene", "Nutrition plan"]
                })
            
            return missing
        
        def generate_overall_recommendation(
            combined_prediction: Dict[str, Any],
            optimizations: List[Dict[str, Any]]
        ) -> str:
            """Generate overall recommendation for the treatment plan."""
            efficacy = combined_prediction.get("efficacy", 0)
            
            if efficacy > 0.7 and not optimizations:
                return "MAINTAIN - Treatment plan is effective with good predicted outcomes"
            elif efficacy > 0.5 and optimizations:
                return "ADJUST - Treatment plan is moderately effective but could benefit from adjustments"
            elif efficacy > 0.3:
                return "MODIFY - Treatment plan requires modifications to improve effectiveness"
            else:
                return "RECONSIDER - Treatment plan is unlikely to be effective and should be reconsidered"
        
        # Evaluate the treatment plan
        evaluation = evaluate_treatment_plan(self.digital_twin, self.treatment_plan)
        
        # Verify evaluation structure
        assert "individual_predictions" in evaluation
        assert "combined_prediction" in evaluation
        assert "synergy_analysis" in evaluation
        assert "recommendations" in evaluation
        
        # Verify individual predictions
        assert len(evaluation["individual_predictions"]) == 3
        
        # Verify synergy analysis
        assert "efficacy_synergy" in evaluation["synergy_analysis"]
        assert "time_synergy" in evaluation["synergy_analysis"]
        
        # Verify recommendations
        assert "optimizations" in evaluation["recommendations"]
        assert "overall_recommendation" in evaluation["recommendations"]
    
    def test_simulate_treatment_plan_effects(self):
        """Test simulating the effects of a treatment plan over time."""
        # Define a function to simulate the progression of state over time
        def simulate_treatment_effects(
            twin: DigitalTwin,
            plan: TreatmentPlan,
            weeks: int
        ) -> Dict[str, Any]:
            """Simulate the effects of a treatment plan over time."""
            # Get active treatments
            active_treatments = plan.get_active_treatments()
            if not active_treatments:
                return {"error": "No active treatments in plan"}
            
            # Store the original state to restore later
            original_state = twin.current_state.copy(deep=True)
            
            # Initialize simulation results
            simulation = {
                "timestamps": [],
                "states": [],
                "treatment_effects": []
            }
            
            # Set initial timestamp
            current_time = datetime.utcnow()
            simulation["timestamps"].append(current_time)
            simulation["states"].append(twin.current_state.copy(deep=True))
            simulation["treatment_effects"].append({})
            
            # Simulate each week
            for week in range(1, weeks + 1):
                # Calculate effects for this week
                effects = {}
                for treatment in active_treatments:
                    # Calculate weekly effect based on treatment duration
                    treatment_duration_days = (current_time - treatment.start_date).days
                    treatment_effect = treatment.calculate_effect_at_time_point(
                        days_since_start=treatment_duration_days + 7
                    )
                    
                    # Add to effects dict
                    for key, value in treatment_effect.items():
                        if key in effects:
                            effects[key] += value
                        else:
                            effects[key] = value
                
                # Update the digital twin state with these effects
                update_data = {
                    "neurotransmitter_data": {},
                    "psychological_data": {},
                    "behavioral_data": {},
                    "cognitive_data": {}
                }
                
                # Map effects to update data structure
                for key, value in effects.items():
                    if key.endswith("_level"):
                        if key.startswith(("serotonin", "dopamine", "norepinephrine")):
                            update_data["neurotransmitter_data"][key] = {"level": value}
                        elif key == "anxiety_level":
                            update_data["psychological_data"]["anxiety"] = {"level": value}
                        elif key == "activity_level":
                            update_data["behavioral_data"]["activity"] = {"level": value}
                    elif key == "mood_valence":
                        update_data["psychological_data"]["mood"] = {"valence": value}
                    elif key == "sleep_quality":
                        update_data["behavioral_data"]["sleep"] = {"quality": value}
                    # Add mappings for other effect types
                
                # Update the twin's state
                twin.update_state(update_data)
                
                # Advance time
                current_time += timedelta(days=7)
                
                # Record this state
                simulation["timestamps"].append(current_time)
                simulation["states"].append(twin.current_state.copy(deep=True))
                simulation["treatment_effects"].append(effects)
            
            # Restore the original state
            twin.current_state = original_state
            
            return simulation
        
        # Simulate 8 weeks of treatment
        simulation = simulate_treatment_effects(self.digital_twin, self.treatment_plan, 8)
        
        # Verify simulation structure
        assert "timestamps" in simulation
        assert "states" in simulation
        assert "treatment_effects" in simulation
        
        # Verify simulation length
        assert len(simulation["timestamps"]) == 9  # Initial + 8 weeks
        assert len(simulation["states"]) == 9
        assert len(simulation["treatment_effects"]) == 9
        
        # Verify progressive improvement
        initial_state = simulation["states"][0]
        final_state = simulation["states"][-1]
        
        # Check for improvements in key metrics, if they exist in the states
        if hasattr(initial_state.psychological, "mood_valence") and hasattr(final_state.psychological, "mood_valence"):
            assert final_state.psychological.mood_valence >= initial_state.psychological.mood_valence
            
        if hasattr(initial_state.psychological, "anxiety_level") and hasattr(final_state.psychological, "anxiety_level"):
            assert final_state.psychological.anxiety_level <= initial_state.psychological.anxiety_level


if __name__ == '__main__':
    unittest.main()