"""
Neurotransmitter Mapping entity model for the Digital Twin system.

This module contains the NeurotransmitterMapping class, which represents
the complete mapping of neurotransmitters, their production sites,
receptor profiles, and interactions within the brain.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
from uuid import UUID

from app.domain.entities.digital_twin.brain_region import BrainRegion
from app.domain.entities.digital_twin.clinical_insight import ClinicalSignificance
from app.domain.entities.digital_twin.neurotransmitter import Neurotransmitter
from app.domain.entities.digital_twin.receptor_subtype import ReceptorSubtype
from .receptor_profile import ReceptorProfile, ReceptorType


@dataclass
class NeurotransmitterMapping:
    """
    Represents the complete mapping of neurotransmitters in the brain for a specific patient.
    
    This entity encapsulates the complex relationships between neurotransmitters,
    brain regions, and receptor profiles, serving as a core component of the
    neurochemical simulation capabilities of the Digital Twin.
    """
    patient_id: UUID
    production_sites: Dict[Neurotransmitter, List[BrainRegion]] = field(default_factory=dict)
    receptor_profiles: List[ReceptorProfile] = field(default_factory=list)
    brain_region_connectivity: Dict[BrainRegion, Dict[BrainRegion, float]] = field(default_factory=dict)
    feedback_mechanisms: Dict[Tuple[Neurotransmitter, BrainRegion], Dict[Neurotransmitter, float]] = field(default_factory=dict)
    version: int = 1
    
    def get_receptor_profiles_for_region(self, region: BrainRegion) -> List[ReceptorProfile]:
        """Get all receptor profiles for a specific brain region."""
        return [profile for profile in self.receptor_profiles 
                if profile.brain_region == region]
    
    def get_receptor_profiles_for_neurotransmitter(self, neurotransmitter: Neurotransmitter) -> List[ReceptorProfile]:
        """Get all receptor profiles for a specific neurotransmitter."""
        return [profile for profile in self.receptor_profiles 
                if profile.neurotransmitter == neurotransmitter]
    
    def get_producing_regions(self, neurotransmitter: Neurotransmitter) -> List[BrainRegion]:
        """Get all brain regions that produce a specific neurotransmitter."""
        if neurotransmitter not in self.production_sites:
            return []
        return self.production_sites[neurotransmitter]
    
    def get_receptor_profiles(self, brain_region: BrainRegion, neurotransmitter: Neurotransmitter) -> List[ReceptorProfile]:
        """Get receptor profiles for a specific brain region and neurotransmitter combination."""
        return [profile for profile in self.receptor_profiles 
                if profile.brain_region == brain_region and profile.neurotransmitter == neurotransmitter]
    
    def add_receptor_profile(self, profile: ReceptorProfile) -> None:
        """Add a new receptor profile to the mapping."""
        # Check if a profile for this region/neurotransmitter already exists
        existing_profiles = [p for p in self.receptor_profiles 
                            if p.brain_region == profile.brain_region 
                            and p.neurotransmitter == profile.neurotransmitter]
        
        # If it exists, replace it
        if existing_profiles:
            self.receptor_profiles.remove(existing_profiles[0])
            
        self.receptor_profiles.append(profile)
    
    def add_production_site(self, neurotransmitter: Neurotransmitter, region: BrainRegion) -> None:
        """Add a production site for a neurotransmitter."""
        if neurotransmitter not in self.production_sites:
            self.production_sites[neurotransmitter] = []
            
        if region not in self.production_sites[neurotransmitter]:
            self.production_sites[neurotransmitter].append(region)
    
    def calculate_region_sensitivity(self, region: BrainRegion, neurotransmitter: Neurotransmitter) -> float:
        """
        Calculate the overall sensitivity of a brain region to a neurotransmitter.
        
        Returns:
            float: Sensitivity score from 0.0 (no response) to 1.0 (highly sensitive)
        """
        profiles = [p for p in self.receptor_profiles 
                   if p.brain_region == region and p.neurotransmitter == neurotransmitter]
        
        if not profiles:
            return 0.0
            
        return profiles[0].sensitivity
    
    def calculate_region_response(self, brain_region: BrainRegion, neurotransmitter: Neurotransmitter, 
                               neurotransmitter_level: float) -> Tuple[float, float]:
        """
        Calculate how a specific brain region responds to a neurotransmitter level.
        
        Args:
            brain_region: The brain region to calculate response for
            neurotransmitter: The neurotransmitter affecting the region
            neurotransmitter_level: Current level of the neurotransmitter (0.0-1.0)
            
        Returns:
            Tuple of (net_effect, confidence) where net_effect ranges from -1.0 to 1.0
        """
        # Check if we have receptor profiles for this combination
        profiles = [p for p in self.receptor_profiles 
                   if p.brain_region == brain_region and p.neurotransmitter == neurotransmitter]
        
        if not profiles:
            return 0.0, 0.0  # No effect if no receptor profiles exist
            
        profile = profiles[0]
        response = profile.calculate_response(neurotransmitter_level)
        
        # Calculate confidence based on receptor density and sensitivity
        confidence = min(1.0, max(0.2, profile.sensitivity * 0.8))
        
        return response, confidence
    
    def get_neurotransmitter_effects(self, neurotransmitter: Neurotransmitter, 
                                    level_change: float) -> Dict[BrainRegion, Dict[str, float]]:
        """
        Get the effects of a specific neurotransmitter level change on all brain regions.
        
        Args:
            neurotransmitter: The neurotransmitter being changed
            level_change: Amount of change in the neurotransmitter level (-1.0 to 1.0)
            
        Returns:
            Dict mapping brain regions to their response metrics
        """
        results = {}
        baseline_level = 0.5  # Assumed baseline
        new_level = max(0.0, min(1.0, baseline_level + level_change))
        
        # Get all profiles for this neurotransmitter
        profiles = self.get_receptor_profiles_for_neurotransmitter(neurotransmitter)
        
        for profile in profiles:
            response, confidence = self.calculate_region_response(
                brain_region=profile.brain_region,
                neurotransmitter=neurotransmitter,
                neurotransmitter_level=new_level
            )
            
            results[profile.brain_region] = {
                "effect": response,
                "confidence": confidence,
                "change_from_baseline": response - profile.calculate_response(baseline_level)
            }
            
        return results
    
    def get_brain_region_neurotransmitter_profile(self, region: BrainRegion) -> Dict[Neurotransmitter, Dict[str, float]]:
        """
        Get a complete neurotransmitter sensitivity profile for a brain region.
        
        Args:
            region: Brain region to get profile for
            
        Returns:
            Dict mapping neurotransmitters to their effect metrics for this region
        """
        profiles = self.get_receptor_profiles_for_region(region)
        result = {}
        
        for profile in profiles:
            result[profile.neurotransmitter] = {
                "sensitivity": profile.sensitivity,
                "receptor_density": sum(profile.receptor_subtypes.values()),
                "receptor_types": [t.value for t in set(profile.receptor_types.values())]
            }
            
        return result
        
    def simulate_cascade(self, initial_changes: Dict[Neurotransmitter, float], 
                        steps: int = 3) -> Dict[BrainRegion, Dict[str, float]]:
        """
        Simulate the cascade effects of neurotransmitter changes across brain regions.
        
        Args:
            initial_changes: Dict mapping neurotransmitters to their level changes
            steps: Number of propagation steps to simulate
            
        Returns:
            Dict mapping brain regions to their response metrics
        """
        results = {region: {"activation": 0.0, "confidence": 0.0} for region in BrainRegion}
        
        # First-order effects (direct neurotransmitter impacts)
        for neurotransmitter, change in initial_changes.items():
            # Only process if we have production sites for this neurotransmitter
            if neurotransmitter not in self.production_sites or not self.production_sites[neurotransmitter]:
                continue
                
            profiles = self.get_receptor_profiles_for_neurotransmitter(neurotransmitter)
            
            for profile in profiles:
                response = profile.calculate_response(0.5 + change)  # Baseline + change
                results[profile.brain_region]["activation"] += response
                results[profile.brain_region]["confidence"] = max(
                    results[profile.brain_region]["confidence"], 
                    0.7  # Base confidence for direct effects
                )
        
        # Propagate through brain region connectivity for subsequent steps
        for step in range(1, steps):
            step_changes = {}
            
            # Start with regions that have been activated in previous steps
            for region, data in results.items():
                if abs(data["activation"]) > 0.1:  # Only significant activations propagate
                    confidence_decay = 0.8 ** step  # Confidence decreases with each step
                    
                    # Propagate to connected regions
                    if region in self.brain_region_connectivity:
                        for target, strength in self.brain_region_connectivity[region].items():
                            if target not in step_changes:
                                step_changes[target] = 0.0
                                
                            # Propagate activation scaled by connection strength
                            propagated_activation = data["activation"] * strength
                            step_changes[target] += propagated_activation
                            
                            # Update confidence
                            new_confidence = data["confidence"] * confidence_decay
                            results[target]["confidence"] = max(
                                results[target]["confidence"],
                                new_confidence
                            )
            
            # Apply the propagated changes
            for region, change in step_changes.items():
                results[region]["activation"] += change
                
            # Clamp activations to reasonable ranges
            for region in results:
                results[region]["activation"] = max(-1.0, min(1.0, results[region]["activation"]))
        
        # Filter out regions with minimal response
        return {region: data for region, data in results.items() 
                if abs(data["activation"]) > 0.05}


def create_default_neurotransmitter_mapping(patient_id: UUID) -> NeurotransmitterMapping:
    """
    Create a default neurotransmitter mapping with standard receptor profiles.
    
    This function initializes a basic mapping with scientifically valid defaults
    for neurotransmitter production sites and receptor profiles.
    
    Args:
        patient_id: UUID of the patient to create the mapping for
        
    Returns:
        NeurotransmitterMapping: A complete neurotransmitter mapping with defaults
    """
    mapping = NeurotransmitterMapping(patient_id=patient_id)
    
    # Set up production sites based on neuroscience research
    # Serotonin
    mapping.add_production_site(Neurotransmitter.SEROTONIN, BrainRegion.RAPHE_NUCLEI)
    mapping.add_production_site(Neurotransmitter.SEROTONIN, BrainRegion.HYPOTHALAMUS)
    
    # Dopamine
    mapping.add_production_site(Neurotransmitter.DOPAMINE, BrainRegion.SUBSTANTIA_NIGRA)
    mapping.add_production_site(Neurotransmitter.DOPAMINE, BrainRegion.VENTRAL_TEGMENTAL_AREA)
    
    # GABA
    mapping.add_production_site(Neurotransmitter.GABA, BrainRegion.CEREBELLUM)
    mapping.add_production_site(Neurotransmitter.GABA, BrainRegion.BASAL_GANGLIA)
    mapping.add_production_site(Neurotransmitter.GABA, BrainRegion.HIPPOCAMPUS)
    
    # Glutamate
    mapping.add_production_site(Neurotransmitter.GLUTAMATE, BrainRegion.CEREBRAL_CORTEX)
    mapping.add_production_site(Neurotransmitter.GLUTAMATE, BrainRegion.HIPPOCAMPUS)
    mapping.add_production_site(Neurotransmitter.GLUTAMATE, BrainRegion.THALAMUS)
    
    # Acetylcholine
    mapping.add_production_site(Neurotransmitter.ACETYLCHOLINE, BrainRegion.BASAL_FOREBRAIN)
    mapping.add_production_site(Neurotransmitter.ACETYLCHOLINE, BrainRegion.BRAINSTEM)
    
    # Norepinephrine
    mapping.add_production_site(Neurotransmitter.NOREPINEPHRINE, BrainRegion.LOCUS_COERULEUS)
    mapping.add_production_site(Neurotransmitter.NOREPINEPHRINE, BrainRegion.HYPOTHALAMUS)
    
    # Set up basic receptor profiles
    # Each profile includes relevant receptor subtypes and their relative densities
    
    # Prefrontal Cortex - Serotonin 5HT2A receptor profile
    pfc_serotonin = ReceptorProfile(
        brain_region=BrainRegion.PREFRONTAL_CORTEX,
        neurotransmitter=Neurotransmitter.SEROTONIN,
        receptor_type=ReceptorType.EXCITATORY,
        receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2A,
        density=0.6,
        sensitivity=0.8,
        clinical_relevance=ClinicalSignificance.MODERATE
    )
    mapping.add_receptor_profile(pfc_serotonin)
    
    # Prefrontal Cortex - Dopamine D1 receptor profile
    pfc_dopamine_d1 = ReceptorProfile(
        brain_region=BrainRegion.PREFRONTAL_CORTEX,
        neurotransmitter=Neurotransmitter.DOPAMINE,
        receptor_type=ReceptorType.EXCITATORY,
        receptor_subtype=ReceptorSubtype.DOPAMINE_D1,
        density=0.5,
        sensitivity=1.1,
        clinical_relevance=ClinicalSignificance.MODERATE
    )
    mapping.add_receptor_profile(pfc_dopamine_d1)
    
    # Prefrontal Cortex - Dopamine D2 receptor profile
    pfc_dopamine_d2 = ReceptorProfile(
        brain_region=BrainRegion.PREFRONTAL_CORTEX,
        neurotransmitter=Neurotransmitter.DOPAMINE,
        receptor_type=ReceptorType.INHIBITORY,
        receptor_subtype=ReceptorSubtype.DOPAMINE_D2,
        density=0.5,
        sensitivity=1.1,
        clinical_relevance=ClinicalSignificance.MODERATE
    )
    mapping.add_receptor_profile(pfc_dopamine_d2)
    
    # Hippocampus - Serotonin 5HT1A receptor profile
    hippocampus_serotonin_5ht1a = ReceptorProfile(
        brain_region=BrainRegion.HIPPOCAMPUS,
        neurotransmitter=Neurotransmitter.SEROTONIN,
        receptor_type=ReceptorType.INHIBITORY,
        receptor_subtype=ReceptorSubtype.SEROTONIN_5HT1A,
        density=0.7,
        sensitivity=1.0,
        clinical_relevance=ClinicalSignificance.MODERATE
    )
    mapping.add_receptor_profile(hippocampus_serotonin_5ht1a)
    
    # Hippocampus - Serotonin 5HT2C receptor profile
    hippocampus_serotonin_5ht2c = ReceptorProfile(
        brain_region=BrainRegion.HIPPOCAMPUS,
        neurotransmitter=Neurotransmitter.SEROTONIN,
        receptor_type=ReceptorType.EXCITATORY,
        receptor_subtype=ReceptorSubtype.SEROTONIN_5HT2C,
        density=0.3,
        sensitivity=1.0,
        clinical_relevance=ClinicalSignificance.MILD
    )
    mapping.add_receptor_profile(hippocampus_serotonin_5ht2c)
    
    # Amygdala
    # Amygdala - GABA_A receptor profile
    amygdala_gaba_a = ReceptorProfile(
        brain_region=BrainRegion.AMYGDALA,
        neurotransmitter=Neurotransmitter.GABA,
        receptor_type=ReceptorType.INHIBITORY,
        receptor_subtype=ReceptorSubtype.GABA_A,
        density=0.8,
        sensitivity=1.3,
        clinical_relevance=ClinicalSignificance.HIGH
    )
    mapping.add_receptor_profile(amygdala_gaba_a)
    
    # Amygdala - GABA_B receptor profile
    amygdala_gaba_b = ReceptorProfile(
        brain_region=BrainRegion.AMYGDALA,
        neurotransmitter=Neurotransmitter.GABA,
        receptor_type=ReceptorType.INHIBITORY,
        receptor_subtype=ReceptorSubtype.GABA_B,
        density=0.2,
        sensitivity=1.3,
        clinical_relevance=ClinicalSignificance.MODERATE
    )
    mapping.add_receptor_profile(amygdala_gaba_b)
    
    # Nucleus Accumbens - Dopamine D1 receptor profile
    nucleus_accumbens_dopamine_d1 = ReceptorProfile(
        brain_region=BrainRegion.NUCLEUS_ACCUMBENS,
        neurotransmitter=Neurotransmitter.DOPAMINE,
        receptor_type=ReceptorType.EXCITATORY,
        receptor_subtype=ReceptorSubtype.DOPAMINE_D1,
        density=0.6,
        sensitivity=1.5,
        clinical_relevance=ClinicalSignificance.HIGH
    )
    mapping.add_receptor_profile(nucleus_accumbens_dopamine_d1)
    
    # Nucleus Accumbens - Dopamine D2 receptor profile
    nucleus_accumbens_dopamine_d2 = ReceptorProfile(
        brain_region=BrainRegion.NUCLEUS_ACCUMBENS,
        neurotransmitter=Neurotransmitter.DOPAMINE,
        receptor_type=ReceptorType.INHIBITORY,
        receptor_subtype=ReceptorSubtype.DOPAMINE_D2,
        density=0.4,
        sensitivity=1.5,
        clinical_relevance=ClinicalSignificance.HIGH
    )
    mapping.add_receptor_profile(nucleus_accumbens_dopamine_d2)
    
    # Set up brain region connectivity (simplified)
    # Format: {source_region: {target_region: connection_strength}}
    connectivity = {
        BrainRegion.PREFRONTAL_CORTEX: {
            BrainRegion.AMYGDALA: 0.6,
            BrainRegion.NUCLEUS_ACCUMBENS: 0.5,
            BrainRegion.HIPPOCAMPUS: 0.4
        },
        BrainRegion.AMYGDALA: {
            BrainRegion.HYPOTHALAMUS: 0.7,
            BrainRegion.HIPPOCAMPUS: 0.5
        },
        BrainRegion.HIPPOCAMPUS: {
            BrainRegion.PREFRONTAL_CORTEX: 0.4,
            BrainRegion.AMYGDALA: 0.3
        },
        BrainRegion.NUCLEUS_ACCUMBENS: {
            BrainRegion.VENTRAL_TEGMENTAL_AREA: 0.6,
            BrainRegion.PREFRONTAL_CORTEX: 0.4
        },
        BrainRegion.RAPHE_NUCLEI: {
            BrainRegion.PREFRONTAL_CORTEX: 0.5,
            BrainRegion.HIPPOCAMPUS: 0.5,
            BrainRegion.AMYGDALA: 0.4
        },
        BrainRegion.LOCUS_COERULEUS: {
            BrainRegion.PREFRONTAL_CORTEX: 0.6,
            BrainRegion.AMYGDALA: 0.5,
            BrainRegion.HIPPOCAMPUS: 0.4
        }
    }
    mapping.brain_region_connectivity = connectivity
    
    return mapping
