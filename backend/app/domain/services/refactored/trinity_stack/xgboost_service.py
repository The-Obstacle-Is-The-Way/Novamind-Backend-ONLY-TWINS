"""
XGBoost Service Interface.
Domain interface for the prediction engine component of the Trinity Stack.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from backend.app.domain.entities.refactored.digital_twin_core import BrainRegion


class XGBoostService(ABC):
    """
    Abstract interface for XGBoost prediction engine operations.
    XGBoost is the advanced machine learning component of the Trinity Stack,
    specializing in prediction, risk analysis, and treatment optimization.
    """
    
    @abstractmethod
    async def predict_treatment_outcomes(
        self,
        reference_id: UUID,
        digital_twin_state_id: UUID,
        treatment_options: list[dict],
        prediction_horizon: int = 90  # days
    ) -> dict[str, Any]:
        """
        Predict outcomes for different treatment options.
        
        Args:
            reference_id: UUID reference identifier
            digital_twin_state_id: UUID of the current Digital Twin state
            treatment_options: List of treatment options to evaluate
            prediction_horizon: Time horizon for predictions in days
            
        Returns:
            Dictionary with predictions for each treatment option
        """
        pass
    
    @abstractmethod
    async def forecast_symptom_progression(
        self,
        reference_id: UUID,
        digital_twin_state_id: UUID,
        symptoms: list[str],
        forecast_horizon: int = 90,  # days
        intervention: dict | None = None
    ) -> dict[str, Any]:
        """
        Forecast the progression of symptoms over time.
        
        Args:
            reference_id: UUID reference identifier
            digital_twin_state_id: UUID of the current Digital Twin state
            symptoms: List of symptoms to forecast
            forecast_horizon: Time horizon for forecast in days
            intervention: Optional intervention to model
            
        Returns:
            Dictionary with forecasted symptom trajectories
        """
        pass
    
    @abstractmethod
    async def identify_risk_factors(
        self,
        reference_id: UUID,
        digital_twin_state_id: UUID,
        target_outcome: str
    ) -> dict[str, Any]:
        """
        Identify risk factors for a specific outcome.
        
        Args:
            reference_id: UUID reference identifier
            digital_twin_state_id: UUID of the current Digital Twin state
            target_outcome: Specific outcome to analyze risk factors for
            
        Returns:
            Dictionary with risk factors and their importance scores
        """
        pass
    
    @abstractmethod
    async def optimize_treatment_plan(
        self,
        reference_id: UUID,
        digital_twin_state_id: UUID,
        treatment_options: list[dict],
        optimization_criteria: list[str],
        constraints: dict | None = None
    ) -> dict[str, Any]:
        """
        Optimize a treatment plan based on multiple criteria.
        
        Args:
            reference_id: UUID reference identifier
            digital_twin_state_id: UUID of the current Digital Twin state
            treatment_options: Available treatment options
            optimization_criteria: Criteria to optimize for
            constraints: Optional constraints on treatment plan
            
        Returns:
            Optimized treatment plan with predicted outcomes
        """
        pass
    
    @abstractmethod
    async def explain_prediction(
        self,
        reference_id: UUID,
        digital_twin_state_id: UUID,
        prediction_id: str,
        detail_level: str = "medium"
    ) -> dict[str, Any]:
        """
        Provide an explanation for a specific prediction.
        
        Args:
            reference_id: UUID reference identifier
            digital_twin_state_id: UUID of the current Digital Twin state
            prediction_id: ID of the prediction to explain
            detail_level: Level of detail in explanation
            
        Returns:
            Explanation of the prediction with feature importance
        """
        pass
    
    @abstractmethod
    async def predict_brain_activity(
        self,
        reference_id: UUID,
        digital_twin_state_id: UUID
    ) -> dict[BrainRegion, float]:
        """
        Predict brain activity across regions based on current state.
        
        Args:
            reference_id: UUID reference identifier
            digital_twin_state_id: UUID of the current Digital Twin state
            
        Returns:
            Dictionary mapping brain regions to predicted activity levels
        """
        pass
    
    @abstractmethod
    async def compare_treatment_effectiveness(
        self,
        reference_id: UUID,
        digital_twin_state_id: UUID,
        treatment_options: list[dict],
        effectiveness_metrics: list[str]
    ) -> dict[str, Any]:
        """
        Compare effectiveness of different treatment options.
        
        Args:
            reference_id: UUID reference identifier
            digital_twin_state_id: UUID of the current Digital Twin state
            treatment_options: Treatment options to compare
            effectiveness_metrics: Metrics to use for comparison
            
        Returns:
            Comparative analysis of treatments with effectiveness scores
        """
        pass
    
    @abstractmethod
    async def analyze_historical_response(
        self,
        reference_id: UUID,
        treatment_type: str,
        time_period: tuple[datetime, datetime] | None = None
    ) -> dict[str, Any]:
        """
        Analyze historical response to treatments.
        
        Args:
            reference_id: UUID reference identifier
            treatment_type: Type of treatment to analyze
            time_period: Optional time period for analysis
            
        Returns:
            Analysis of historical response patterns
        """
        pass