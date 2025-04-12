"""
Brain Region entity model for the Digital Twin system.

This module contains the BrainRegion class, which represents a region of the brain
and is used in neurotransmitter mapping and other brain-related analyses.
"""

from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class BrainRegion(str, Enum):
    """Enum representing different brain regions relevant for psychological assessment."""
    
    # Core brain regions used in the digital twin models
    PREFRONTAL_CORTEX = "prefrontal_cortex"
    AMYGDALA = "amygdala"
    HIPPOCAMPUS = "hippocampus"
    HYPOTHALAMUS = "hypothalamus"
    THALAMUS = "thalamus"
    CINGULATE_CORTEX = "cingulate_cortex"
    ANTERIOR_CINGULATE = "anterior_cingulate"  # Alias for compatibility
    BASAL_GANGLIA = "basal_ganglia"
    INSULA = "insula"
    NUCLEUS_ACCUMBENS = "nucleus_accumbens"
    VENTRAL_TEGMENTAL_AREA = "ventral_tegmental_area"
    VENTRAL_TEGMENTAL = "ventral_tegmental"  # Alias for compatibility
    CEREBELLUM = "cerebellum"
    PARIETAL_LOBE = "parietal_lobe"
    TEMPORAL_LOBE = "temporal_lobe"
    OCCIPITAL_LOBE = "occipital_lobe"
    BRAIN_STEM = "brain_stem"
    BRAINSTEM = "brainstem"  # Alias for compatibility
    SUBSTANTIA_NIGRA = "substantia_nigra"
    LOCUS_COERULEUS = "locus_coeruleus"
    RAPHE_NUCLEI = "raphe_nuclei"
    
    # Additional brain regions for enhanced compatibility
    ORBITOFRONTAL_CORTEX = "orbitofrontal_cortex"
    DORSOLATERAL_PREFRONTAL = "dorsolateral_prefrontal"
    
    # Missing brain regions needed for neurotransmitter mapping
    CEREBRAL_CORTEX = "cerebral_cortex"
    BASAL_FOREBRAIN = "basal_forebrain"
    STRIATUM = "striatum"
    MIDBRAIN = "midbrain"
    
    @classmethod
    def get_all(cls) -> list[str]:
        """Get list of all brain region values."""
        return [region.value for region in cls]
    
    @classmethod
    def get_region_for_function(cls, function: str) -> list["BrainRegion"]:
        """Get brain regions associated with a specific cognitive/emotional function."""
        function_map = {
            "executive_function": [cls.PREFRONTAL_CORTEX, cls.BASAL_GANGLIA],
            "emotion_regulation": [cls.AMYGDALA, cls.PREFRONTAL_CORTEX, cls.CINGULATE_CORTEX],
            "memory": [cls.HIPPOCAMPUS, cls.PREFRONTAL_CORTEX, cls.TEMPORAL_LOBE],
            "fear_response": [cls.AMYGDALA, cls.HYPOTHALAMUS],
            "reward": [cls.NUCLEUS_ACCUMBENS, cls.VENTRAL_TEGMENTAL_AREA],
            "attention": [cls.PREFRONTAL_CORTEX, cls.PARIETAL_LOBE, cls.THALAMUS],
            "mood": [cls.PREFRONTAL_CORTEX, cls.AMYGDALA, cls.RAPHE_NUCLEI, cls.LOCUS_COERULEUS],
            "sleep": [cls.HYPOTHALAMUS, cls.BRAIN_STEM, cls.THALAMUS],
        }
        
        return function_map.get(function.lower(), [])


class BrainRegionActivity(BaseModel):
    """Model representing activity in a specific brain region."""
    
    region: BrainRegion
    activity_level: float = Field(
        ...,
        ge=-1.0, 
        le=1.0, 
        description="Normalized activity level from -1.0 (inhibited) to 1.0 (excited)"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence level in this activity assessment (0.0-1.0)"
    )
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True
    )