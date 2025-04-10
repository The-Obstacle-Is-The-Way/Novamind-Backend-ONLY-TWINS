"""
Domain service interface for Digital Twin Core operations.
This is the central orchestrating service that coordinates all components.
Pure domain interface with no infrastructure dependencies.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID

from app.domain.entities.digital_twin import ClinicalInsight, DigitalTwinState


class DigitalTwinCoreService(ABC):
    """
    Abstract interface for Digital Twin Core operations.
    Responsible for orchestrating interactions between all components.
    Concrete implementations will be provided in the infrastructure layer.
    """
    
    @abstractmethod
    async def initialize_digital_twin(
        self,
        patient_id: UUID,
        initial_data: Optional[Dict] = None
    ) -> DigitalTwinState:
        """
        Initialize a new Digital Twin state for a patient.
        
        Args:
            patient_id: UUID of the patient
            initial_data: Optional initial data for the Digital Twin
            
        Returns:
            Newly created Digital Twin state
        """
        pass
    
    @abstractmethod
    async def update_from_actigraphy(
        self,
        patient_id: UUID,
        actigraphy_data: Dict,
        data_source: str
    ) -> DigitalTwinState:
        """
        Update Digital Twin with new actigraphy data via PAT.
        
        Args:
            patient_id: UUID of the patient
            actigraphy_data: Raw actigraphy data to process
            data_source: Source of the actigraphy data
            
        Returns:
            Updated Digital Twin state
        """
        pass
    
    @abstractmethod
    async def update_from_clinical_notes(
        self,
        patient_id: UUID,
        note_text: str,
        note_type: str,
        clinician_id: Optional[UUID] = None
    ) -> DigitalTwinState:
        """
        Update Digital Twin with insights from clinical notes via MentalLLaMA.
        
        Args:
            patient_id: UUID of the patient
            note_text: Text of the clinical note
            note_type: Type of clinical note
            clinician_id: Optional ID of the clinician who wrote the note
            
        Returns:
            Updated Digital Twin state
        """
        pass
    
    @abstractmethod
    async def generate_treatment_recommendations(
        self,
        patient_id: UUID,
        digital_twin_state_id: Optional[UUID] = None,
        include_rationale: bool = True
    ) -> List[Dict]:
        """
        Generate treatment recommendations using XGBoost and MentalLLaMA.
        
        Args:
            patient_id: UUID of the patient
            digital_twin_state_id: Optional specific state ID to use
            include_rationale: Whether to include rationale for recommendations
            
        Returns:
            List of treatment recommendations with metadata
        """
        pass
    
    @abstractmethod
    async def get_visualization_data(
        self,
        patient_id: UUID,
        digital_twin_state_id: Optional[UUID] = None,
        visualization_type: str = "brain_model"
    ) -> Dict:
        """
        Get data for 3D visualization of the Digital Twin.
        
        Args:
            patient_id: UUID of the patient
            digital_twin_state_id: Optional specific state ID to use
            visualization_type: Type of visualization to generate
            
        Returns:
            Visualization data for the specified type
        """
        pass
    
    @abstractmethod
    async def merge_insights(
        self,
        patient_id: UUID,
        insights: List[ClinicalInsight],
        source: str
    ) -> DigitalTwinState:
        """
        Merge new insights into the Digital Twin state.
        
        Args:
            patient_id: UUID of the patient
            insights: List of new clinical insights
            source: Source of the insights
            
        Returns:
            Updated Digital Twin state
        """
        pass
    
    @abstractmethod
    async def compare_states(
        self,
        patient_id: UUID,
        state_id_1: UUID,
        state_id_2: UUID
    ) -> Dict:
        """
        Compare two Digital Twin states to identify changes.
        
        Args:
            patient_id: UUID of the patient
            state_id_1: UUID of the first state to compare
            state_id_2: UUID of the second state to compare
            
        Returns:
            Dictionary with comparison results
        """
        pass
    
    @abstractmethod
    async def generate_clinical_summary(
        self,
        patient_id: UUID,
        time_range: Optional[Tuple[str, str]] = None,
        include_treatment_history: bool = True,
        include_predictions: bool = True
    ) -> Dict:
        """
        Generate comprehensive clinical summary from Digital Twin.
        
        Args:
            patient_id: UUID of the patient
            time_range: Optional time range for the summary
            include_treatment_history: Whether to include treatment history
            include_predictions: Whether to include predictions
            
        Returns:
            Dictionary with clinical summary
        """
        pass