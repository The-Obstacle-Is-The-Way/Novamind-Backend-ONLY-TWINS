"""
Receptor Subtype entity model for the Digital Twin system.

This module contains the ReceptorSubtype enum, which represents different
receptor subtypes in the brain that interact with neurotransmitters.
"""

from enum import Enum


class ReceptorSubtype(str, Enum):
    """Enum representing different receptor subtypes in the brain."""
    
    # Serotonin receptors
    SEROTONIN_5HT1A = "5ht1a"
    SEROTONIN_5HT2A = "5ht2a"
    SEROTONIN_5HT2C = "5ht2c"
    SEROTONIN_5HT3 = "5ht3"
    SEROTONIN_5HT4 = "5ht4"
    SEROTONIN_5HT6 = "5ht6"
    SEROTONIN_5HT7 = "5ht7"
    
    # Dopamine receptors
    DOPAMINE_D1 = "d1"
    DOPAMINE_D2 = "d2"
    DOPAMINE_D3 = "d3"
    DOPAMINE_D4 = "d4"
    DOPAMINE_D5 = "d5"
    
    # GABA receptors
    GABA_A = "gaba_a"
    GABA_B = "gaba_b"
    
    # Glutamate receptors
    GLUTAMATE_NMDA = "nmda"
    GLUTAMATE_AMPA = "ampa"
    GLUTAMATE_KAINATE = "kainate"
    GLUTAMATE_METABOTROPIC = "metabotropic"
    
    # Acetylcholine receptors
    ACETYLCHOLINE_NICOTINIC = "nicotinic"
    ACETYLCHOLINE_MUSCARINIC_M1 = "muscarinic_m1"
    ACETYLCHOLINE_MUSCARINIC_M2 = "muscarinic_m2"
    ACETYLCHOLINE_MUSCARINIC_M3 = "muscarinic_m3"
    ACETYLCHOLINE_MUSCARINIC_M4 = "muscarinic_m4"
    ACETYLCHOLINE_MUSCARINIC_M5 = "muscarinic_m5"
    
    # Norepinephrine receptors
    NOREPINEPHRINE_ALPHA1 = "alpha1"
    NOREPINEPHRINE_ALPHA2 = "alpha2"
    NOREPINEPHRINE_BETA1 = "beta1"
    NOREPINEPHRINE_BETA2 = "beta2"
    NOREPINEPHRINE_BETA3 = "beta3"
    
    # Histamine receptors
    HISTAMINE_H1 = "h1"
    HISTAMINE_H2 = "h2"
    HISTAMINE_H3 = "h3"
    HISTAMINE_H4 = "h4"
    
    # Opioid receptors
    OPIOID_MU = "mu"
    OPIOID_DELTA = "delta"
    OPIOID_KAPPA = "kappa"
    
    # Cannabinoid receptors
    CANNABINOID_CB1 = "cb1"
    CANNABINOID_CB2 = "cb2"
    
    @classmethod
    def get_receptors_for_neurotransmitter(cls, neurotransmitter: str) -> list[str]:
        """Get list of receptor subtypes for a specific neurotransmitter."""
        neurotransmitter = neurotransmitter.lower()
        
        mapping = {
            "serotonin": [
                cls.SEROTONIN_5HT1A, cls.SEROTONIN_5HT2A, cls.SEROTONIN_5HT2C,
                cls.SEROTONIN_5HT3, cls.SEROTONIN_5HT4, cls.SEROTONIN_5HT6,
                cls.SEROTONIN_5HT7
            ],
            "dopamine": [
                cls.DOPAMINE_D1, cls.DOPAMINE_D2, cls.DOPAMINE_D3,
                cls.DOPAMINE_D4, cls.DOPAMINE_D5
            ],
            "gaba": [cls.GABA_A, cls.GABA_B],
            "glutamate": [
                cls.GLUTAMATE_NMDA, cls.GLUTAMATE_AMPA,
                cls.GLUTAMATE_KAINATE, cls.GLUTAMATE_METABOTROPIC
            ],
            "acetylcholine": [
                cls.ACETYLCHOLINE_NICOTINIC, cls.ACETYLCHOLINE_MUSCARINIC_M1,
                cls.ACETYLCHOLINE_MUSCARINIC_M2, cls.ACETYLCHOLINE_MUSCARINIC_M3,
                cls.ACETYLCHOLINE_MUSCARINIC_M4, cls.ACETYLCHOLINE_MUSCARINIC_M5
            ],
            "norepinephrine": [
                cls.NOREPINEPHRINE_ALPHA1, cls.NOREPINEPHRINE_ALPHA2,
                cls.NOREPINEPHRINE_BETA1, cls.NOREPINEPHRINE_BETA2, 
                cls.NOREPINEPHRINE_BETA3
            ],
            "histamine": [
                cls.HISTAMINE_H1, cls.HISTAMINE_H2, cls.HISTAMINE_H3, cls.HISTAMINE_H4
            ],
            "endorphins": [cls.OPIOID_MU, cls.OPIOID_DELTA, cls.OPIOID_KAPPA],
            "cannabinoid": [cls.CANNABINOID_CB1, cls.CANNABINOID_CB2]
        }
        
        return mapping.get(neurotransmitter, [])
