"""
Integration test for the Digital Twin system.
Demonstrates the interaction between all components.
"""
import asyncio
import uuid
from datetime import datetime, UTC, timedelta

import pytest

from app.domain.entities.patient import Patient # Removed Gender, Diagnosis, Medication
from app.infrastructure.factories.mock_digital_twin_factory import MockDigitalTwinFactory


@pytest.mark.asyncio
async def test_digital_twin_complete_workflow():
    """
    Test a complete Digital Twin workflow from patient creation to treatment recommendations.
    This test demonstrates how all components work together in a typical scenario.
    """
    # Create a complete system using our factory
    system = MockDigitalTwinFactory.create_complete_system()
    
    # Extract components
    patient_repo = system["repositories"]["patient_repository"]
    digital_twin_repo = system["repositories"]["digital_twin_repository"]
    digital_twin_core = system["services"]["digital_twin_core"]
    
    # 1. Create a test patient
    patient_id = uuid.uuid4()
    patient = Patient(
        id=patient_id,
        first_name="Jane",
        last_name="Doe",
        date_of_birth=datetime.now() - timedelta(days=365 * 35),  # 35 years old
        gender="female", # Use string literal
        contact_info={
            "email": "jane.doe@example.com",
            "phone": "+1-555-123-4567"
        },
        # Use strings for diagnoses as per patient.py entity
        diagnoses=[
            "F32.1: Major depressive disorder, single episode, moderate",
            "F41.1: Generalized anxiety disorder"
        ],
        # Use strings for medications as per patient.py entity
        medications=[
            "Sertraline 50mg daily"
        ],
        allergies=["Penicillin"]
    )
    
    # Save the patient
    saved_patient = await patient_repo.save(patient)
    assert saved_patient.id == patient_id
    
    # 2. Initialize Digital Twin
    initial_twin_state = await digital_twin_core.initialize_digital_twin(
        patient_id=patient_id,
        initial_data={
            "clinical_metrics": {
                "phq9_score": 14,  # Moderate depression
                "gad7_score": 12   # Moderate anxiety
            },
            "metadata": {
                "initialized_by": "test_integration",
                "test_mode": True
            }
        }
    )
    
    # Verify the initial state was created
    assert initial_twin_state.patient_id == patient_id
    assert initial_twin_state.version == 1
    assert "phq9_score" in initial_twin_state.clinical_metrics
    assert initial_twin_state.clinical_metrics["phq9_score"] == 14
    
    # 3. Process actigraphy data
    actigraphy_data = {
        "start_time": (datetime.now() - timedelta(days=7)).isoformat(),
        "end_time": datetime.now().isoformat(),
        "daily_activity": [
            {"date": (datetime.now() - timedelta(days=i)).date().isoformat(), 
             "steps": 5000 + i * 500, 
             "active_minutes": 30 + i * 5}
            for i in range(7)
        ],
        "sleep_data": [
            {"date": (datetime.now() - timedelta(days=i)).date().isoformat(), 
             "duration_hours": 6.5 + (i % 3) * 0.5, 
             "efficiency": 0.8 + (i % 5) * 0.02}
            for i in range(7)
        ]
    }
    
    updated_twin_state = await digital_twin_core.update_from_actigraphy(
        patient_id=patient_id,
        actigraphy_data=actigraphy_data,
        data_source="fitbit"
    )
    
    # Verify the state was updated
    assert updated_twin_state.version == 2
    assert len(updated_twin_state.clinical_insights) > 0
    assert "sleep" in updated_twin_state.clinical_metrics  # PAT should have added sleep metrics
    
    # 4. Process clinical notes
    clinical_note = """
    Patient reports continued depressive symptoms with moderate severity.
    Sleep has improved somewhat with current medication, but still experiencing
    early morning awakening. Anxiety symptoms are present but less prominent
    than depression. Patient reports some interest in trying CBT along with
    medication. No suicidal ideation or intent. Will continue Sertraline at
    current dose and refer for CBT evaluation.
    """
    
    updated_twin_state = await digital_twin_core.update_from_clinical_notes(
        patient_id=patient_id,
        note_text=clinical_note,
        note_type="progress_note",
        clinician_id=uuid.uuid4()  # Random clinician ID for the test
    )
    
    # Verify the state was updated with insights from the note
    assert updated_twin_state.version == 3
    assert len(updated_twin_state.clinical_insights) > len(initial_twin_state.clinical_insights)
    
    # Some brain regions should now have activation levels
    assert len(updated_twin_state.brain_state) > 0
    
    # 5. Generate treatment recommendations
    recommendations = await digital_twin_core.generate_treatment_recommendations(
        patient_id=patient_id,
        include_rationale=True
    )
    
    # Verify recommendations were generated
    assert len(recommendations) > 0
    
    # There should be medication and therapy recommendations based on diagnoses
    has_medication = False
    has_therapy = False
    
    for rec in recommendations:
        if rec["type"] == "medication":
            has_medication = True
        elif rec["type"] == "therapy":
            has_therapy = True
    
    assert has_medication
    assert has_therapy
    
    # 6. Get visualization data for the 3D brain model
    visualization_data = await digital_twin_core.get_visualization_data(
        patient_id=patient_id,
        visualization_type="brain_model"
    )
    
    # Verify visualization data was generated
    assert visualization_data["visualization_type"] == "brain_model_3d"
    assert len(visualization_data["brain_regions"]) > 0
    
    # 7. Compare states to see changes over time
    comparison = await digital_twin_core.compare_states(
        patient_id=patient_id,
        state_id_1=initial_twin_state.id,
        state_id_2=updated_twin_state.id
    )
    
    # Verify comparison data
    assert comparison["state_1"]["id"] == str(initial_twin_state.id)
    assert comparison["state_2"]["id"] == str(updated_twin_state.id)
    assert "brain_state_changes" in comparison
    assert "new_insights" in comparison
    assert len(comparison["new_insights"]) > 0
    
    # 8. Generate a comprehensive clinical summary
    summary = await digital_twin_core.generate_clinical_summary(
        patient_id=patient_id,
        include_treatment_history=True,
        include_predictions=True
    )
    
    # Verify summary data
    assert summary["patient"]["id"] == str(patient_id)
    assert summary["patient"]["name"] == "Jane Doe"
    assert "digital_twin_state" in summary
    assert "significant_insights" in summary
    assert "treatment_recommendations" in summary
    assert "treatment_history" in summary
    assert len(summary["treatment_history"]) > 0


if __name__ == "__main__":
    # Run the test directly when the script is executed
    asyncio.run(test_digital_twin_complete_workflow())
    print("Integration test completed successfully!")