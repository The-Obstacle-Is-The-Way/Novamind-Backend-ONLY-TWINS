"""
MentalLLaMA Service Interface.
Domain interface for the large language model component of the Trinity Stack.
"""
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from backend.app.domain.entities.refactored.digital_twin_core import (
    BrainRegion,
    ClinicalInsight,
    Neurotransmitter,
)


class MentalLLaMAService(ABC):
    """
    Abstract interface for MentalLLaMA operations.
    MentalLLaMA is the advanced language model component of the Trinity Stack,
    specializing in clinical text understanding and reasoning.
    """
    
    @abstractmethod
    async def analyze_clinical_text(
        self, 
        text: str,
        context: dict[str, Any] | None = None,
        reference_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Analyze clinical text to extract insights, entities, and relationships.
        
        Args:
            text: The clinical text to analyze
            context: Optional additional context
            reference_id: Optional reference ID for tracing
            
        Returns:
            Analysis results including entities, relationships, and insights
        """
        pass
    
    @abstractmethod
    async def generate_clinical_insights(
        self,
        clinical_data: dict[str, Any],
        digital_twin_state_id: UUID | None = None
    ) -> list[ClinicalInsight]:
        """
        Generate clinical insights from structured clinical data.
        
        Args:
            clinical_data: Structured clinical data
            digital_twin_state_id: Optional reference to Digital Twin state
            
        Returns:
            List of clinical insights derived from the data
        """
        pass
    
    @abstractmethod
    async def map_brain_regions(
        self,
        symptoms: list[str],
        intensity: dict[str, float] | None = None
    ) -> dict[BrainRegion, float]:
        """
        Map symptoms to brain regions with activation levels.
        
        Args:
            symptoms: List of symptoms to map
            intensity: Optional dictionary of symptom intensities
            
        Returns:
            Dictionary mapping brain regions to activation levels
        """
        pass
    
    @abstractmethod
    async def map_neurotransmitters(
        self,
        symptoms: list[str],
        medications: list[str] | None = None
    ) -> dict[Neurotransmitter, float]:
        """
        Map symptoms and medications to neurotransmitter levels.
        
        Args:
            symptoms: List of symptoms to map
            medications: Optional list of medications
            
        Returns:
            Dictionary mapping neurotransmitters to levels
        """
        pass
    
    @abstractmethod
    async def explain_treatment_mechanism(
        self,
        treatment: str,
        condition: str | None = None,
        detail_level: str = "medium"
    ) -> dict[str, Any]:
        """
        Explain the mechanism of action for a treatment.
        
        Args:
            treatment: The treatment to explain
            condition: Optional condition being treated
            detail_level: Level of detail ("low", "medium", "high")
            
        Returns:
            Explanation of the treatment mechanism
        """
        pass
    
    @abstractmethod
    async def generate_recommendations(
        self,
        clinical_data: dict[str, Any],
        current_treatments: list[str] | None = None,
        constraints: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Generate treatment recommendations based on clinical data.
        
        Args:
            clinical_data: Clinical data to base recommendations on
            current_treatments: Optional list of current treatments
            constraints: Optional constraints on recommendations
            
        Returns:
            List of treatment recommendations with rationales
        """
        pass
    
    @abstractmethod
    async def generate_clinical_summary(
        self,
        clinical_data: dict[str, Any],
        length: str = "medium",
        include_recommendations: bool = True
    ) -> str:
        """
        Generate a comprehensive clinical summary from structured data.
        
        Args:
            clinical_data: Clinical data to summarize
            length: Length of summary ("short", "medium", "long")
            include_recommendations: Whether to include recommendations
            
        Returns:
            Generated clinical summary text
        """
        pass
    
    @abstractmethod
    async def translate_clinical_description(
        self,
        clinical_text: str,
        target_audience: str = "patient",
        explanation_depth: str = "moderate"
    ) -> str:
        """
        Translate clinical description to target audience level.
        
        Args:
            clinical_text: Clinical text to translate
            target_audience: Audience ("patient", "caregiver", "clinician")
            explanation_depth: Depth of explanation
            
        Returns:
            Translated text appropriate for the target audience
        """
        pass