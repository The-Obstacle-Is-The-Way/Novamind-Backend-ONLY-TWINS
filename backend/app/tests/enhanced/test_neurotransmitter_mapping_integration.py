"""
Integration tests for the Neurotransmitter Mapping functionality of the Enhanced Digital Twin.

These tests verify that the neurotransmitter mapping components work correctly with
the rest of the Digital Twin system.
"""
import asyncio
import datetime
import random
import uuid
import pytest
import math
from typing import Dict, List, Tuple, Optional
from uuid import UUID

from app.domain.entities.digital_twin import (
    BrainRegion, ClinicalInsight, ClinicalSignificance, Neurotransmitter,
    DigitalTwinState
)
from app.domain.entities.digital_twin.receptor_subtype import ReceptorSubtype
from app.domain.entities.neurotransmitter_mapping import (
    NeurotransmitterMapping, ReceptorProfile, ReceptorType,
    create_default_neurotransmitter_mapping
)
from app.domain.services.enhanced_digital_twin_core_service import EnhancedDigitalTwinCoreService
from app.infrastructure.factories.enhanced_mock_digital_twin_factory import EnhancedMockDigitalTwinFactory


@pytest.fixture
def enhanced_services() -> Tuple[EnhancedDigitalTwinCoreService, ...]:
    """Fixture to create enhanced mock services for testing."""
    services = EnhancedMockDigitalTwinFactory.create_enhanced_mock_services()
    return (services[0],)  # Only return the Digital Twin service for simplicity


@pytest.fixture
def patient_id() -> UUID:
    """Fixture to create a consistent patient ID for tests."""
    
    return uuid.UUID('12345678-1234-5678-1234-567812345678')


@pytest.fixture
def initial_data() -> Dict:
    """Fixture to provide initial patient data for testing."""
    
    return {
        "diagnoses": ["Major Depressive Disorder", "Generalized Anxiety Disorder"],
        "symptoms": ["fatigue", "insomnia", "worry", "anhedonia"],
        "medications": [
            {"name": "Escitalopram", "dosage": "10mg", "frequency": "daily"},
            {"name": "Bupropion", "dosage": "150mg", "frequency": "twice daily"}
        ]
    }


@pytest.fixture
async def initialized_patient(enhanced_services, patient_id, initial_data) -> DigitalTwinState:
    """Fixture to provide a patient with an initialized Digital Twin state."""
    digital_twin_service, = enhanced_services
    
    # Initialize the Digital Twin
    digital_twin_state, _, _ = await digital_twin_service.initialize_digital_twin(
        patient_id=patient_id,
        initial_data=initial_data
    )
    
#     return digital_twin_state # FIXME: return outside function


@pytest.mark.asyncio()
@pytest.mark.venv_only()
async def test_initialize_neurotransmitter_mapping(enhanced_services, patient_id, initialized_patient):
    """Test initializing a neurotransmitter mapping for a patient."""
    digital_twin_service, = enhanced_services
    
    # Initialize the neurotransmitter mapping
    mapping = await digital_twin_service.initialize_neurotransmitter_mapping(
        patient_id=patient_id,
        use_default_mapping=True
    )
    
    # Check that the mapping was created
    assert mapping is not None
    assert isinstance(mapping, NeurotransmitterMapping)
    
    # Verify that the default mapping has receptor profiles
    assert len(mapping.receptor_profiles) > 0
    
    # Verify that important neurotransmitters have production sites
    for nt in [Neurotransmitter.SEROTONIN, Neurotransmitter.DOPAMINE, Neurotransmitter.GABA]:
        producing_regions = mapping.get_producing_regions(nt)
        assert len(producing_regions) > 0, f"No production sites for {nt}"


@pytest.mark.asyncio()
async def test_custom_neurotransmitter_mapping(enhanced_services, patient_id, initialized_patient):
    """Test creating a custom neurotransmitter mapping for a patient."""
    digital_twin_service, = enhanced_services
    
    # Create a custom mapping
    custom_mapping = NeurotransmitterMapping(patient_id=patient_id)
    
    # Add some receptor profiles
    custom_mapping.add_receptor_profile(
        ReceptorProfile(
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            neurotransmitter=Neurotransmitter.SEROTONIN,
            receptor_type=ReceptorType.EXCITATORY,
            receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
            density=0.85,
            sensitivity=0.9,
            clinical_relevance=ClinicalSignificance.CRITICAL
        )
    )
    
    custom_mapping.add_receptor_profile(
        ReceptorProfile(
            brain_region=BrainRegion.AMYGDALA,
            neurotransmitter=Neurotransmitter.GABA,
            receptor_type=ReceptorType.INHIBITORY,
            receptor_subtype=ReceptorSubtype.GABA_A,
            density=0.7,
            sensitivity=0.8,
            clinical_relevance=ClinicalSignificance.MODERATE
        )
    )
    
    # Add production sites
    custom_mapping.add_production_site(
        Neurotransmitter.SEROTONIN, 
        BrainRegion.RAPHE_NUCLEI
    )
    
    custom_mapping.add_production_site(
        Neurotransmitter.GABA,
        BrainRegion.NUCLEUS_ACCUMBENS
    )
    
    # Initialize with custom mapping
    mapping = await digital_twin_service.initialize_neurotransmitter_mapping(
        patient_id=patient_id,
        use_default_mapping=False,
        custom_mapping=custom_mapping
    )
    
    # Verify custom mapping was used
    assert mapping is not None
    assert len(mapping.receptor_profiles) == 2
    
    # Check specific profile details were retained
    serotonin_profiles = mapping.get_receptor_profiles(
        BrainRegion.PREFRONTAL_CORTEX, 
        Neurotransmitter.SEROTONIN
    )
    assert len(serotonin_profiles) == 1
    assert serotonin_profiles[0].receptor_subtype == ReceptorSubtype.SEROTONIN_5HT2A
    
    # Verify production sites
    serotonin_sites = mapping.get_producing_regions(Neurotransmitter.SEROTONIN)
    assert BrainRegion.RAPHE_NUCLEI in serotonin_sites


@pytest.mark.asyncio()
async def test_update_receptor_profiles(enhanced_services, patient_id, initialized_patient):
    """Test updating receptor profiles in the neurotransmitter mapping."""
    digital_twin_service, = enhanced_services
    
    # Initialize mapping first
    mapping = await digital_twin_service.initialize_neurotransmitter_mapping(
        patient_id=patient_id
    )
    
    # Define new profiles to add
    new_profiles = [
        ReceptorProfile(
            brain_region=BrainRegion.THALAMUS,
            neurotransmitter=Neurotransmitter.GLUTAMATE,
            receptor_type=ReceptorType.EXCITATORY,
            receptor_subtype=ReceptorSubtype.GLUTAMATE_NMDA,
            density=0.6,
            sensitivity=0.75,
            clinical_relevance=ClinicalSignificance.MODERATE
        ),
        ReceptorProfile(
            brain_region=BrainRegion.HIPPOCAMPUS,
            neurotransmitter=Neurotransmitter.ACETYLCHOLINE,
            receptor_type=ReceptorType.EXCITATORY,
            receptor_subtype=ReceptorSubtype.ACETYLCHOLINE_NICOTINIC,
            density=0.5,
            sensitivity=0.65,
            clinical_relevance=ClinicalSignificance.MILD
        )
    ]
    
    # Update the profiles
    updated_mapping = await digital_twin_service.update_receptor_profiles(
        patient_id=patient_id,
        receptor_profiles=new_profiles
    )
    
    # Verify profiles were added
    assert updated_mapping is not None
    
    # Check specific profiles were added
    thalamus_profiles = updated_mapping.get_receptor_profiles(
        BrainRegion.THALAMUS, 
        Neurotransmitter.GLUTAMATE
    )
    assert len(thalamus_profiles) > 0
    assert any(p.receptor_subtype == ReceptorSubtype.GLUTAMATE_NMDA for p in thalamus_profiles)
    
    hippocampus_profiles = updated_mapping.get_receptor_profiles(
        BrainRegion.HIPPOCAMPUS, 
        Neurotransmitter.ACETYLCHOLINE
    )
    assert len(hippocampus_profiles) > 0
    assert any(p.receptor_subtype == ReceptorSubtype.ACETYLCHOLINE_NICOTINIC for p in hippocampus_profiles)


@pytest.mark.asyncio()
async def test_get_neurotransmitter_effects(enhanced_services, patient_id, initialized_patient):
    """Test getting neurotransmitter effects on brain regions."""
    digital_twin_service, = enhanced_services
    
    # Initialize mapping first
    await digital_twin_service.initialize_neurotransmitter_mapping(
        patient_id=patient_id
    )
    
    # Test for serotonin
    serotonin_effects = await digital_twin_service.get_neurotransmitter_effects(
        patient_id=patient_id,
        neurotransmitter=Neurotransmitter.SEROTONIN,
        brain_regions=[
            BrainRegion.PREFRONTAL_CORTEX,
            BrainRegion.AMYGDALA,
            BrainRegion.HIPPOCAMPUS
        ]
    )
    
    # Check results
    assert serotonin_effects is not None
    assert BrainRegion.PREFRONTAL_CORTEX in serotonin_effects
    assert BrainRegion.AMYGDALA in serotonin_effects
    assert BrainRegion.HIPPOCAMPUS in serotonin_effects
    
    # Check structure of effect data
    pfc_effect = serotonin_effects[BrainRegion.PREFRONTAL_CORTEX]
    assert "net_effect" in pfc_effect
    assert "confidence" in pfc_effect
    assert "receptor_types" in pfc_effect
    assert "receptor_count" in pfc_effect
    assert "is_produced_here" in pfc_effect


@pytest.mark.asyncio()
async def test_get_brain_region_neurotransmitter_sensitivity(enhanced_services, patient_id, initialized_patient):
    """Test getting brain region sensitivity to neurotransmitters."""
    digital_twin_service, = enhanced_services
    
    # Initialize mapping first
    await digital_twin_service.initialize_neurotransmitter_mapping(
        patient_id=patient_id
    )
    
    # Test for prefrontal cortex
    pfc_sensitivities = await digital_twin_service.get_brain_region_neurotransmitter_sensitivity(
        patient_id=patient_id,
        brain_region=BrainRegion.PREFRONTAL_CORTEX,
        neurotransmitters=[
            Neurotransmitter.SEROTONIN,
            Neurotransmitter.DOPAMINE,
            Neurotransmitter.GABA
        ]
    )
    
    # Check results
    assert pfc_sensitivities is not None
    assert len(pfc_sensitivities) > 0
    
    # Check that major neurotransmitters are included
    assert Neurotransmitter.SEROTONIN in pfc_sensitivities
    
    # Check structure of sensitivity data
    serotonin_data = pfc_sensitivities.get(Neurotransmitter.SEROTONIN)
    if serotonin_data:  # May not be present depending on mock implementation
        assert "sensitivity" in serotonin_data
        assert "receptor_count" in serotonin_data
        assert "receptor_types" in serotonin_data
        assert "dominant_receptor_type" in serotonin_data
        assert "clinical_relevance" in serotonin_data
        assert "is_produced_here" in serotonin_data


@pytest.mark.asyncio()
async def test_simulate_neurotransmitter_cascade(enhanced_services, patient_id, initialized_patient):
    """Test simulating neurotransmitter cascade effects."""
    digital_twin_service, = enhanced_services
    
    # Initialize mapping first
    await digital_twin_service.initialize_neurotransmitter_mapping(
        patient_id=patient_id
    )
    
    # Define initial changes for simulation
    initial_changes = {
        Neurotransmitter.SEROTONIN: 0.3,  # Increase serotonin
        Neurotransmitter.DOPAMINE: 0.2,   # Increase dopamine
        Neurotransmitter.GABA: -0.1       # Decrease GABA
    }
    
    # Run simulation
    simulation_results = await digital_twin_service.simulate_neurotransmitter_cascade(
        patient_id=patient_id,
        initial_changes=initial_changes,
        simulation_steps=3,
        min_effect_threshold=0.1
    )
    
    # Check results
    assert simulation_results is not None
    assert "steps_data" in simulation_results
    assert "pathways" in simulation_results
    assert "most_affected_regions" in simulation_results
    assert "simulation_parameters" in simulation_results
    
    # Check step data structure
    steps_data = simulation_results["steps_data"]
    assert len(steps_data) == 3  # Should have 3 steps as requested
    
    first_step = steps_data[0]
    assert "step" in first_step
    assert "neurotransmitter_levels" in first_step
    assert "region_effects" in first_step
    
    # Check pathways
    pathways = simulation_results["pathways"]
    assert len(pathways) > 0
    
    # Check parameters were recorded correctly
    params = simulation_results["simulation_parameters"]
    assert params["simulation_steps"] == 3
    assert params["min_effect_threshold"] == 0.1
    assert "initial_changes" in params


@pytest.mark.asyncio()
async def test_analyze_treatment_neurotransmitter_effects(enhanced_services, patient_id, initialized_patient):
    """Test analyzing treatment effects on neurotransmitters over time."""
    digital_twin_service, = enhanced_services
    
    # Initialize mapping first
    await digital_twin_service.initialize_neurotransmitter_mapping(
        patient_id=patient_id
    )
    
    # Create a treatment ID
    treatment_id = uuid.uuid4()
    
    # Define time points for analysis (over 4 weeks)
    time_points = [
        datetime.datetime.now() + datetime.timedelta(days=i*7)
        for i in range(5)  # 0, 7, 14, 21, 28 days:
    ]
    
    # Run analysis
    analysis_results = await digital_twin_service.analyze_treatment_neurotransmitter_effects(
        patient_id=patient_id,
        treatment_id=treatment_id,
        time_points=time_points,
        neurotransmitters=[
            Neurotransmitter.SEROTONIN,
            Neurotransmitter.DOPAMINE,
            Neurotransmitter.NOREPINEPHRINE
        ]
    )
    
    # Check results
    assert analysis_results is not None
    assert "treatment" in analysis_results
    assert "neurotransmitter_timeline" in analysis_results
    assert "affected_brain_regions" in analysis_results
    assert "analysis_timestamp" in analysis_results
    
    # Check treatment info
    assert analysis_results["treatment"]["id"] == str(treatment_id)
    
    # Check timeline data
    timeline = analysis_results["neurotransmitter_timeline"]
    assert Neurotransmitter.SEROTONIN.value in timeline
    assert len(timeline[Neurotransmitter.SEROTONIN.value]) == len(time_points)
    
    # Check time point data structure
    time_point_data = timeline[Neurotransmitter.SEROTONIN.value][0]
    assert "time" in time_point_data
    assert "value" in time_point_data
    assert "change_from_baseline" in time_point_data
    assert "confidence" in time_point_data
    
    # Check affected regions
    affected_regions = analysis_results["affected_brain_regions"]
    assert len(affected_regions) > 0
    
    # Check region data structure
    region_data = affected_regions[0]
    assert "brain_region" in region_data
    assert "neurotransmitter" in region_data
    assert "effect" in region_data
    assert "confidence" in region_data
    assert "clinical_significance" in region_data


@pytest.mark.asyncio()
async def test_integrated_neurotransmitter_mapping_with_visualization(enhanced_services, patient_id, initialized_patient):
    """Test integration of neurotransmitter mapping with visualization data generation."""
    digital_twin_service, = enhanced_services
    
    # Initialize mapping first
    mapping = await digital_twin_service.initialize_neurotransmitter_mapping(
        patient_id=patient_id
    )
    
    # Simulate medication effect
    initial_changes = {
        Neurotransmitter.SEROTONIN: 0.3,  # Increase serotonin (like SSRI)
    }
    
    # Run simulation to generate state changes
    await digital_twin_service.simulate_neurotransmitter_cascade(
        patient_id=patient_id,
        initial_changes=initial_changes,
        simulation_steps=2
    )
    
    # Generate visualization data
    brain_viz = await digital_twin_service.generate_visualization_data(
        patient_id=patient_id,
        visualization_type="brain_model",
        parameters={
            "highlight_neurotransmitters": True,
            "primary_neurotransmitter": Neurotransmitter.SEROTONIN
        }
    )
    
    # Check visualization data
    assert brain_viz is not None
    assert "regions" in brain_viz
    
    # Check that there are activated regions
    activated_regions = [r for r in brain_viz["regions"] if r.get("activation", 0) > 0.5]
    assert len(activated_regions) > 0
    
    # Check that neurotransmitter data is included
    assert "neurotransmitters" in brain_viz
    # Look for a neurotransmitter object with the correct id
    assert any(nt["id"] == Neurotransmitter.SEROTONIN.value for nt in brain_viz["neurotransmitters"])