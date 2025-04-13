"""
Unit tests for the NeurotransmitterMapping entity and related functionality.

These tests verify that the neurotransmitter mapping models behave correctly
and perform calculations accurately.
"""
import pytest
import uuid
from uuid import UUID
from app.domain.entities.digital_twin import ()
BrainRegion,
Neurotransmitter,
ClinicalSignificance,

from app.domain.entities.neurotransmitter_mapping import ()
NeurotransmitterMapping,
ReceptorProfile,
ReceptorType,
ReceptorSubtype,
create_default_neurotransmitter_mapping,



@pytest.mark.venv_only()
def test_neurotransmitter_mapping_creation():
    """Test creating a new neurotransmitter mapping."""
    test_patient_id = uuid.uuid4()
    mapping = NeurotransmitterMapping(patient_id=test_patient_id)

    assert mapping is not None
    assert isinstance(mapping, NeurotransmitterMapping)
    assert len(mapping.receptor_profiles) == 0
    assert mapping.patient_id == test_patient_id


def test_add_receptor_profile():
    """Test adding receptor profiles to a mapping."""
    test_patient_id = uuid.uuid4()
    mapping = NeurotransmitterMapping(patient_id=test_patient_id)

    # Create a receptor profile
    profile = ReceptorProfile()
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    neurotransmitter=Neurotransmitter.SEROTONIN,
    receptor_type=ReceptorType.EXCITATORY,
    receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
    density=0.7,
    sensitivity=0.8,
    clinical_relevance=ClinicalSignificance.MODERATE,
    

    # Add it to the mapping
    mapping.add_receptor_profile(profile)

    # Verify it was added
    assert len(mapping.receptor_profiles) == 1
    assert mapping.receptor_profiles[0] == profile

    # Add another profile for the same region but different neurotransmitter
    profile2 = ReceptorProfile()
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    neurotransmitter=Neurotransmitter.DOPAMINE,
    receptor_type=ReceptorType.EXCITATORY,
    receptor_subtype=ReceptorSubtype.DOPAMINE_D1,
    density=0.6,
    sensitivity=0.7,
    clinical_relevance=ClinicalSignificance.MODERATE,
    

    mapping.add_receptor_profile(profile2)

    # Verify it was added
    assert len(mapping.receptor_profiles) == 2
    assert mapping.receptor_profiles[1] == profile2


def test_get_profiles_by_brain_region():
    """Test retrieving profiles by brain region."""
    test_patient_id = uuid.uuid4()
    mapping = NeurotransmitterMapping(patient_id=test_patient_id)

    # Add profiles for different brain regions
    profiles = []
    ReceptorProfile()
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    neurotransmitter=Neurotransmitter.SEROTONIN,
    receptor_type=ReceptorType.EXCITATORY,
    receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
    density=0.7,
    sensitivity=0.8,
    clinical_relevance=ClinicalSignificance.MODERATE,
    ),
    ReceptorProfile()
    brain_region=BrainRegion.AMYGDALA,
    neurotransmitter=Neurotransmitter.GABA,
    receptor_type=ReceptorType.INHIBITORY,
    receptor_subtype=ReceptorSubtype.GABA_A,
    density=0.8,
    sensitivity=0.6,
    clinical_relevance=ClinicalSignificance.HIGH,
    ),
    ReceptorProfile()
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    neurotransmitter=Neurotransmitter.DOPAMINE,
    receptor_type=ReceptorType.EXCITATORY,
    receptor_subtype=ReceptorSubtype.DOPAMINE_D1,
    density=0.6,
    sensitivity=0.7,
    clinical_relevance=ClinicalSignificance.MODERATE,
    ),
    

    for profile in profiles:
        mapping.add_receptor_profile(profile)

    # Get profiles for PFC
    pfc_profiles = mapping.get_profiles_by_brain_region(BrainRegion.PREFRONTAL_CORTEX)
    assert len(pfc_profiles) == 2
    assert all(p.brain_region == BrainRegion.PREFRONTAL_CORTEX for p in pfc_profiles)

    # Get profiles for amygdala
    amygdala_profiles = mapping.get_profiles_by_brain_region(BrainRegion.AMYGDALA)
    assert len(amygdala_profiles) == 1
    assert all(p.brain_region == BrainRegion.AMYGDALA for p in amygdala_profiles)

    # Get profiles for a region with no profiles
    hippocampus_profiles = mapping.get_profiles_by_brain_region(BrainRegion.HIPPOCAMPUS)
    assert len(hippocampus_profiles) == 0


def test_get_profiles_by_neurotransmitter():
    """Test retrieving profiles by neurotransmitter."""
    test_patient_id = uuid.uuid4()
    mapping = NeurotransmitterMapping(patient_id=test_patient_id)

    # Add profiles for different neurotransmitters
    profiles = []
    ReceptorProfile()
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    neurotransmitter=Neurotransmitter.SEROTONIN,
    receptor_type=ReceptorType.EXCITATORY,
    receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
    density=0.7,
    sensitivity=0.8,
    clinical_relevance=ClinicalSignificance.MODERATE,
    ),
    ReceptorProfile()
    brain_region=BrainRegion.AMYGDALA,
    neurotransmitter=Neurotransmitter.GABA,
    receptor_type=ReceptorType.INHIBITORY,
    receptor_subtype=ReceptorSubtype.GABA_A,
    density=0.8,
    sensitivity=0.6,
    clinical_relevance=ClinicalSignificance.HIGH,
    ),
    ReceptorProfile()
    brain_region=BrainRegion.HIPPOCAMPUS,
    neurotransmitter=Neurotransmitter.SEROTONIN,
    receptor_type=ReceptorType.EXCITATORY,
    receptor_subtype=ReceptorSubtype.SEROTONIN_5HT1A,
    density=0.5,
    sensitivity=0.9,
    clinical_relevance=ClinicalSignificance.HIGH,
    ),
    

    for profile in profiles:
        mapping.add_receptor_profile(profile)

    # Get profiles for serotonin
    serotonin_profiles = mapping.get_profiles_by_neurotransmitter(Neurotransmitter.SEROTONIN)
    assert len(serotonin_profiles) == 2
    assert all(p.neurotransmitter == Neurotransmitter.SEROTONIN for p in serotonin_profiles)

    # Get profiles for GABA
    gaba_profiles = mapping.get_profiles_by_neurotransmitter(Neurotransmitter.GABA)
    assert len(gaba_profiles) == 1
    assert all(p.neurotransmitter == Neurotransmitter.GABA for p in gaba_profiles)

    # Get profiles for a neurotransmitter with no profiles
    dopamine_profiles = mapping.get_profiles_by_neurotransmitter(Neurotransmitter.DOPAMINE)
    assert len(dopamine_profiles) == 0


def test_create_default_mapping():
    """Test creating a default neurotransmitter mapping."""
    test_patient_id = uuid.uuid4()
    mapping = create_default_neurotransmitter_mapping(test_patient_id)

    assert mapping is not None
    assert isinstance(mapping, NeurotransmitterMapping)
    assert mapping.patient_id == test_patient_id
    assert len(mapping.receptor_profiles) > 0

    # Check that key brain regions are represented
    pfc_profiles = mapping.get_profiles_by_brain_region(BrainRegion.PREFRONTAL_CORTEX)
    amygdala_profiles = mapping.get_profiles_by_brain_region(BrainRegion.AMYGDALA)
    hippocampus_profiles = mapping.get_profiles_by_brain_region(BrainRegion.HIPPOCAMPUS)

    assert len(pfc_profiles) > 0
    assert len(amygdala_profiles) > 0
    assert len(hippocampus_profiles) > 0


def test_receptor_profile_creation():
    """Test creating and manipulating receptor profiles."""
    # Create a profile
    profile = ReceptorProfile()
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    neurotransmitter=Neurotransmitter.SEROTONIN,
    receptor_type=ReceptorType.EXCITATORY,
    receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
    density=0.7,
    sensitivity=0.8,
    clinical_relevance=ClinicalSignificance.MODERATE,
    

    # Check attributes
    assert profile.brain_region == BrainRegion.PREFRONTAL_CORTEX
    assert profile.neurotransmitter == Neurotransmitter.SEROTONIN
    assert profile.receptor_type == ReceptorType.EXCITATORY
    assert profile.receptor_subtype == ReceptorSubtype.SEROTONIN_5HT2A
    assert profile.density == 0.7
    assert profile.sensitivity == 0.8
    assert profile.clinical_relevance == ClinicalSignificance.MODERATE

    # Test equality
    profile2 = ReceptorProfile()
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    neurotransmitter=Neurotransmitter.SEROTONIN,
    receptor_type=ReceptorType.EXCITATORY,
    receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
    density=0.7,
    sensitivity=0.8,
    clinical_relevance=ClinicalSignificance.MODERATE,
    

    profile3 = ReceptorProfile()
    brain_region=BrainRegion.AMYGDALA,  # Different region
    neurotransmitter=Neurotransmitter.SEROTONIN,
    receptor_type=ReceptorType.EXCITATORY,
    receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
    density=0.7,
    sensitivity=0.8,
    clinical_relevance=ClinicalSignificance.MODERATE,
    

    assert profile == profile2  # Same attributes
    assert profile != profile3  # Different brain region

    # Test string representation
    assert "PREFRONTAL_CORTEX" in str(profile)
    assert "SEROTONIN" in str(profile)
    assert "SEROTONIN_5HT2A" in str(profile)