"""
Unit tests for the NeurotransmitterMapping entity and related functionality.

These tests verify that the neurotransmitter mapping models behave correctly
and perform calculations accurately.
"""
import pytest
from app.domain.entities.digital_twin import (
    BrainRegion,   Neurotransmitter,   ClinicalSignificance
)
from app.domain.entities.neurotransmitter_mapping import (
    NeurotransmitterMapping,   ReceptorProfile,   ReceptorType,   ReceptorSubtype,  
    create_default_neurotransmitter_mapping
)


@pytest.mark.venv_only
def test_neurotransmitter_mapping_creation():
    """Test creating a new neurotransmitter mapping."""
    mapping = NeurotransmitterMapping()
    
    assert mapping is not None
    assert isinstance(mapping, NeurotransmitterMapping)
    assert len(mapping.receptor_profiles) == 0
    assert len(mapping.production_map) == 0


def test_add_receptor_profile():
    """Test adding receptor profiles to a mapping."""
    mapping = NeurotransmitterMapping()
    
    # Create a receptor profile
    profile = ReceptorProfile(
        brain_region=BrainRegion.PREFRONTAL_CORTEX,
        neurotransmitter=Neurotransmitter.SEROTONIN,
        receptor_type=ReceptorType.EXCITATORY,
        receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
        density=0.7,
        sensitivity=0.8,
        clinical_relevance=ClinicalSignificance.MODERATE
    )
    
    # Add it to the mapping
    mapping.add_receptor_profile(profile)
    
    # Verify it was added
    assert len(mapping.receptor_profiles) == 1
    assert mapping.receptor_profiles[0] == profile
    
    # Add another profile for the same region but different neurotransmitter
    profile2 = ReceptorProfile(
        brain_region=BrainRegion.PREFRONTAL_CORTEX,
        neurotransmitter=Neurotransmitter.DOPAMINE,
        receptor_type=ReceptorType.EXCITATORY,
        receptor_subtype=ReceptorSubtype.DOPAMINE_D1,
        density=0.6,
        sensitivity=0.7,
        clinical_relevance=ClinicalSignificance.MODERATE
    )
    
    mapping.add_receptor_profile(profile2)
    
    # Verify both were added
    assert len(mapping.receptor_profiles) == 2


def test_get_receptor_profiles():
    """Test retrieving receptor profiles for specific region and neurotransmitter."""
    mapping = NeurotransmitterMapping()
    
    # Add multiple profiles
    profiles = [
        ReceptorProfile(
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            neurotransmitter=Neurotransmitter.SEROTONIN,
            receptor_type=ReceptorType.EXCITATORY,
            receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
            density=0.7,
            sensitivity=0.8,
            clinical_relevance=ClinicalSignificance.MODERATE
        ),
        ReceptorProfile(
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            neurotransmitter=Neurotransmitter.SEROTONIN,
            receptor_type=ReceptorType.INHIBITORY,
            receptor_subtype=ReceptorSubtype.SEROTONIN_5HT1A,
            density=0.5,
            sensitivity=0.6,
            clinical_relevance=ClinicalSignificance.MILD
        ),
        ReceptorProfile(
            brain_region=BrainRegion.AMYGDALA,
            neurotransmitter=Neurotransmitter.GABA,
            receptor_type=ReceptorType.INHIBITORY,
            receptor_subtype=ReceptorSubtype.GABA_A,
            density=0.8,
            sensitivity=0.9,
            clinical_relevance=ClinicalSignificance.CRITICAL
        )
    ]
    
    for profile in profiles:
        mapping.add_receptor_profile(profile)
    
    # Test getting profiles for a specific combination
    pfc_serotonin_profiles = mapping.get_receptor_profiles(
        BrainRegion.PREFRONTAL_CORTEX,
        Neurotransmitter.SEROTONIN
    )
    
    assert len(pfc_serotonin_profiles) == 2
    assert all(p.brain_region == BrainRegion.PREFRONTAL_CORTEX for p in pfc_serotonin_profiles)
    assert all(p.neurotransmitter == Neurotransmitter.SEROTONIN for p in pfc_serotonin_profiles)
    
    # Test getting profiles for a combination with only one profile
    amygdala_gaba_profiles = mapping.get_receptor_profiles(
        BrainRegion.AMYGDALA,
        Neurotransmitter.GABA
    )
    
    assert len(amygdala_gaba_profiles) == 1
    assert amygdala_gaba_profiles[0].brain_region == BrainRegion.AMYGDALA
    assert amygdala_gaba_profiles[0].neurotransmitter == Neurotransmitter.GABA
    
    # Test getting profiles for a combination with no profiles
    hippocampus_dopamine_profiles = mapping.get_receptor_profiles(
        BrainRegion.HIPPOCAMPUS,
        Neurotransmitter.DOPAMINE
    )
    
    assert len(hippocampus_dopamine_profiles) == 0


def test_add_production_site():
    """Test adding neurotransmitter production sites."""
    mapping = NeurotransmitterMapping()
    
    # Add production sites
    mapping.add_production_site(Neurotransmitter.SEROTONIN, BrainRegion.RAPHE_NUCLEI)
    mapping.add_production_site(Neurotransmitter.DOPAMINE, BrainRegion.VENTRAL_STRIATUM)
    mapping.add_production_site(Neurotransmitter.DOPAMINE, BrainRegion.VENTRAL_TEGMENTAL_AREA)
    
    # Verify they were added
    assert Neurotransmitter.SEROTONIN in mapping.production_map
    assert Neurotransmitter.DOPAMINE in mapping.production_map
    assert len(mapping.production_map[Neurotransmitter.SEROTONIN]) == 1
    assert len(mapping.production_map[Neurotransmitter.DOPAMINE]) == 2
    
    # Add duplicate (should not increase count)
    mapping.add_production_site(Neurotransmitter.SEROTONIN, BrainRegion.RAPHE_NUCLEI)
    assert len(mapping.production_map[Neurotransmitter.SEROTONIN]) == 1


def test_get_producing_regions():
    """Test retrieving regions that produce a specific neurotransmitter."""
    mapping = NeurotransmitterMapping()
    
    # Add production sites
    mapping.add_production_site(Neurotransmitter.SEROTONIN, BrainRegion.RAPHE_NUCLEI)
    mapping.add_production_site(Neurotransmitter.DOPAMINE, BrainRegion.DORSAL_STRIATUM)
    mapping.add_production_site(Neurotransmitter.DOPAMINE, BrainRegion.VENTRAL_TEGMENTAL_AREA)
    
    # Get producing regions
    serotonin_regions = mapping.get_producing_regions(Neurotransmitter.SEROTONIN)
    dopamine_regions = mapping.get_producing_regions(Neurotransmitter.DOPAMINE)
    gaba_regions = mapping.get_producing_regions(Neurotransmitter.GABA)
    
    # Verify
    assert len(serotonin_regions) == 1
    assert BrainRegion.RAPHE_NUCLEI in serotonin_regions
    
    assert len(dopamine_regions) == 2
    assert BrainRegion.DORSAL_STRIATUM in dopamine_regions
    assert BrainRegion.VENTRAL_TEGMENTAL_AREA in dopamine_regions
    
    assert len(gaba_regions) == 0  # No GABA production sites defined


def test_calculate_region_response():
    """Test calculating neurotransmitter effect on a brain region."""
    mapping = NeurotransmitterMapping()
    
    # Add profiles with different receptor types (excitatory vs inhibitory)
    profiles = [
        ReceptorProfile(
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            neurotransmitter=Neurotransmitter.SEROTONIN,
            receptor_type=ReceptorType.EXCITATORY,  # Excitatory - positive effect
            receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
            density=0.7,
            sensitivity=0.8,
            clinical_relevance=ClinicalSignificance.MODERATE
        ),
        ReceptorProfile(
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            neurotransmitter=Neurotransmitter.SEROTONIN,
            receptor_type=ReceptorType.INHIBITORY,  # Inhibitory - negative effect
            receptor_subtype=ReceptorSubtype.SEROTONIN_5HT1A,
            density=0.5,
            sensitivity=0.6,
            clinical_relevance=ClinicalSignificance.MILD
        )
    ]
    
    for profile in profiles:
        mapping.add_receptor_profile(profile)
    
    # Calculate response with normal levels
    effect, confidence = mapping.calculate_region_response(
        brain_region=BrainRegion.PREFRONTAL_CORTEX,
        neurotransmitter=Neurotransmitter.SEROTONIN,
        neurotransmitter_level=0.5  # Normal level
    )
    
    # At normal levels, the net effect should be close to 0 (balance)
    assert -0.3 <= effect <= 0.3
    assert 0.3 <= confidence <= 1.0  # Confidence should be reasonably high given our test setup
    
    # Calculate response with elevated levels
    effect_high, confidence_high = mapping.calculate_region_response(
        brain_region=BrainRegion.PREFRONTAL_CORTEX,
        neurotransmitter=Neurotransmitter.SEROTONIN,
        neurotransmitter_level=0.9  # High level
    )
    
    # The net effect should be different from normal levels
    assert effect_high != effect
    
    # Calculate response for region with no receptors
    effect_none, confidence_none = mapping.calculate_region_response(
        brain_region=BrainRegion.CEREBELLUM,
        neurotransmitter=Neurotransmitter.SEROTONIN,
        neurotransmitter_level=0.5
    )
    
    # Should have zero effect and low confidence
    assert effect_none == 0
    assert confidence_none == 0


def test_default_mapping_creation():
    """Test creating a default scientific mapping."""
    mapping = create_default_neurotransmitter_mapping()
    
    # Verify it's not empty
    assert mapping is not None
    assert len(mapping.receptor_profiles) > 0
    assert len(mapping.production_map) > 0
    
    # Check that major neurotransmitters have production sites
    assert Neurotransmitter.SEROTONIN in mapping.production_map
    assert Neurotransmitter.DOPAMINE in mapping.production_map
    assert Neurotransmitter.GABA in mapping.production_map
    
    # Check that major brain regions have receptors
    pfc_profiles = [p for p in mapping.receptor_profiles if p.brain_region == BrainRegion.PREFRONTAL_CORTEX]
    amygdala_profiles = [p for p in mapping.receptor_profiles if p.brain_region == BrainRegion.AMYGDALA]
    hippocampus_profiles = [p for p in mapping.receptor_profiles if p.brain_region == BrainRegion.HIPPOCAMPUS]
    
    assert len(pfc_profiles) > 0
    assert len(amygdala_profiles) > 0
    assert len(hippocampus_profiles) > 0


def test_receptor_profile_creation():
    """Test creating and manipulating receptor profiles."""
    # Create a profile
    profile = ReceptorProfile(
        brain_region=BrainRegion.PREFRONTAL_CORTEX,
        neurotransmitter=Neurotransmitter.SEROTONIN,
        receptor_type=ReceptorType.EXCITATORY,
        receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
        density=0.7,
        sensitivity=0.8,
        clinical_relevance=ClinicalSignificance.MODERATE
    )
    
    # Check attributes
    assert profile.brain_region == BrainRegion.PREFRONTAL_CORTEX
    assert profile.neurotransmitter == Neurotransmitter.SEROTONIN
    assert profile.receptor_type == ReceptorType.EXCITATORY
    assert profile.receptor_subtype == ReceptorSubtype.SEROTONIN_5HT2A
    assert profile.density == 0.7
    assert profile.sensitivity == 0.8
    assert profile.clinical_relevance == ClinicalSignificance.MODERATE
    
    # Test equality
    profile2 = ReceptorProfile(
        brain_region=BrainRegion.PREFRONTAL_CORTEX,
        neurotransmitter=Neurotransmitter.SEROTONIN,
        receptor_type=ReceptorType.EXCITATORY,
        receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
        density=0.7,
        sensitivity=0.8,
        clinical_relevance=ClinicalSignificance.MODERATE
    )
    
    profile3 = ReceptorProfile(
        brain_region=BrainRegion.AMYGDALA,  # Different region
        neurotransmitter=Neurotransmitter.SEROTONIN,
        receptor_type=ReceptorType.EXCITATORY,
        receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
        density=0.7,
        sensitivity=0.8,
        clinical_relevance=ClinicalSignificance.MODERATE
    )
    
    assert profile == profile2  # Same attributes
    assert profile != profile3  # Different brain region
    
    # Test string representation
    assert "PREFRONTAL_CORTEX" in str(profile)
    assert "SEROTONIN" in str(profile)
    assert "SEROTONIN_5HT2A" in str(profile)