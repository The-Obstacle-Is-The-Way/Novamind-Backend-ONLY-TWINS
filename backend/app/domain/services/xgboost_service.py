"""
Domain service interface for XGBoost prediction engine.
Pure domain interface with no infrastructure dependencies.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.domain.entities.digital_twin import BrainRegion, DigitalTwinState


class XGBoostService(ABC):
    """
    Abstract interface for XGBoost prediction operations.
    Concrete implementations will be provided in the infrastructure layer.
    """
    
    @abstractmethod
    async def predict_treatment_response(
        self,
        patient_id: UUID,
        digital_twin_state_id: UUID,
        treatment_options: List[Dict],
        time_horizon: str = "short_term"  # "short_term", "medium_term", "long_term"
    ) -> Dict:
        """
        Predict response to treatment options based on Digital Twin state.
        
        Args:
            patient_id: UUID of the patient
            digital_twin_state_id: UUID of the current Digital Twin state
            treatment_options: List of treatment options to evaluate
            time_horizon: Time horizon for prediction
            
        Returns:
            Dictionary with treatment response predictions and confidence scores
        """
        pass
    
    @abstractmethod
    async def forecast_symptom_progression(
        self,
        patient_id: UUID,
        digital_twin_state_id: UUID,
        symptoms: List[str],
        time_points: List[int],  # days into the future
        with_treatment: Optional[Dict] = None
    ) -> Dict:
        """
        Forecast symptom progression over time with or without treatment.
        
        Args:
            patient_id: UUID of the patient
            digital_twin_state_id: UUID of the current Digital Twin state
            symptoms: List of symptoms to forecast
            time_points: List of time points (in days) for forecasting
            with_treatment: Optional treatment to consider in forecast
            
        Returns:
            Dictionary with symptom trajectories and confidence intervals
        """
        pass
    
    @abstractmethod
    async def identify_risk_factors(
        self,
        patient_id: UUID,
        digital_twin_state_id: UUID,
        target_outcome: str
    ) -> List[Dict]:
        """
        Identify risk factors for a specific outcome based on the Digital Twin state.
        
        Args:
            patient_id: UUID of the patient
            digital_twin_state_id: UUID of the current Digital Twin state
            target_outcome: Specific outcome to analyze risk factors for
            
        Returns:
            List of risk factors with importance scores and confidence levels
        """
        pass
    
    @abstractmethod
    async def calculate_feature_importance(
        self,
        patient_id: UUID,
        digital_twin_state_id: UUID,
        prediction_type: str
    ) -> List[Dict]:
        """
        Calculate feature importance for a specific prediction type.
        
        Args:
            patient_id: UUID of the patient
            digital_twin_state_id: UUID of the current Digital Twin state
            prediction_type: Type of prediction to explain
            
        Returns:
            List of features with importance scores using SHAP values
        """
        pass
    
    @abstractmethod
    async def generate_brain_region_activations(
        self,
        patient_id: UUID,
        digital_twin_state_id: UUID
    ) -> Dict[BrainRegion, float]:
        """
        Generate activation levels for brain regions based on the Digital Twin state.
        
        Args:
            patient_id: UUID of the patient
            digital_twin_state_id: UUID of the current Digital Twin state
            
        Returns:
            Dictionary mapping brain regions to activation levels (0.0 to 1.0)
        """
        pass
    
    @abstractmethod
    async def compare_treatment_options(
        self,
        patient_id: UUID,
        digital_twin_state_id: UUID,
        treatment_options: List[Dict],
        evaluation_metrics: List[str]
    ) -> List[Tuple[Dict, Dict]]:
        """
        Compare multiple treatment options based on predicted outcomes.
        
        Args:
            patient_id: UUID of the patient
            digital_twin_state_id: UUID of the current Digital Twin state
            treatment_options: List of treatment options to compare
            evaluation_metrics: Metrics to use for evaluation
            
        Returns:
            List of tuples with treatment option and evaluation results
        """
        pass