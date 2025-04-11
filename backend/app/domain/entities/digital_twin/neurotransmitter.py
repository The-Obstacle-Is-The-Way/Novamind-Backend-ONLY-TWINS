"""
Neurotransmitter entity model for the Digital Twin system.

This module contains the Neurotransmitter class, which represents a neurotransmitter
and is used in neurotransmitter mapping and brain-related analyses.
"""

from enum import Enum

from pydantic import BaseModel, Field


class Neurotransmitter(str, Enum):
    """Enum representing different neurotransmitters relevant for psychological assessment."""
    
    SEROTONIN = "serotonin"
    DOPAMINE = "dopamine"
    NOREPINEPHRINE = "norepinephrine"
    GABA = "gaba"
    GLUTAMATE = "glutamate"
    ACETYLCHOLINE = "acetylcholine"
    ENDORPHINS = "endorphins"
    OXYTOCIN = "oxytocin"
    VASOPRESSIN = "vasopressin"
    SUBSTANCE_P = "substance_p"
    HISTAMINE = "histamine"
    MELATONIN = "melatonin"
    
    @classmethod
    def get_all(cls) -> list[str]:
        """Get list of all neurotransmitter values."""
        return [neurotransmitter.value for neurotransmitter in cls]
    
    @classmethod
    def get_neurotransmitters_for_condition(cls, condition: str) -> list["Neurotransmitter"]:
        """Get neurotransmitters associated with a specific psychiatric condition."""
        condition_map = {
            "depression": [cls.SEROTONIN, cls.DOPAMINE, cls.NOREPINEPHRINE],
            "anxiety": [cls.GABA, cls.SEROTONIN, cls.NOREPINEPHRINE],
            "adhd": [cls.DOPAMINE, cls.NOREPINEPHRINE],
            "schizophrenia": [cls.DOPAMINE, cls.GLUTAMATE],
            "bipolar": [cls.DOPAMINE, cls.SEROTONIN, cls.NOREPINEPHRINE, cls.GLUTAMATE],
            "ocd": [cls.SEROTONIN, cls.GLUTAMATE],
            "ptsd": [cls.SEROTONIN, cls.NOREPINEPHRINE, cls.GABA],
            "addiction": [cls.DOPAMINE, cls.GLUTAMATE, cls.GABA, cls.ENDORPHINS],
            "insomnia": [cls.MELATONIN, cls.GABA, cls.SEROTONIN],
        }
        
        return condition_map.get(condition.lower(), [])


class NeurotransmitterLevel(BaseModel):
    """Model representing level of a specific neurotransmitter."""
    
    neurotransmitter: Neurotransmitter
    level: float = Field(
        ...,
        ge=-1.0, 
        le=1.0, 
        description="Normalized level from -1.0 (deficiency) to 1.0 (excess), with 0 being normal"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence level in this assessment (0.0-1.0)"
    )
    trend: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Rate of change in level, from -1.0 (rapidly decreasing) to 1.0 (rapidly increasing)"
    )
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True