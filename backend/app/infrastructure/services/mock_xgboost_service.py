"""
Mock implementation of XGBoostService for testing.
Provides synthetic predictions without requiring the actual XGBoost model.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import random

from app.domain.entities.digital_twin import BrainRegion, DigitalTwinState
from app.domain.services.xgboost_service import XGBoostService


class MockXGBoostService(XGBoostService):
    """
    Mock implementation of XGBoostService.
    Generates synthetic predictions for testing and development.
    """
    
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
        # Initialize response structure
        response = {
            "patient_id": str(patient_id),
            "digital_twin_state_id": str(digital_twin_state_id),
            "prediction_timestamp": datetime.now().isoformat(),
            "time_horizon": time_horizon,
            "treatment_responses": [],
            "model_version": "mock-xgboost-v1.0",
            "confidence_adjustment": 0.9 if time_horizon == "short_term" else 
                                    0.7 if time_horizon == "medium_term" else 0.5
        }
        
        # Generate synthetic predictions for each treatment option
        for i, treatment in enumerate(treatment_options):
            treatment_type = treatment.get("type", "medication")
            treatment_name = treatment.get("name", f"Treatment {i+1}")
            
            # Base prediction values
            base_efficacy = random.uniform(0.5, 0.9)
            base_side_effects = random.uniform(0.1, 0.4)
            
            # Adjust based on treatment type
            if treatment_type == "medication":
                if "SSRI" in treatment_name or "sertraline" in treatment_name.lower():
                    base_efficacy = random.uniform(0.65, 0.85)
                    base_side_effects = random.uniform(0.2, 0.4)
                elif "therapy" in treatment_name.lower() or "CBT" in treatment_name:
                    base_efficacy = random.uniform(0.6, 0.8)
                    base_side_effects = random.uniform(0.05, 0.15)
            
            # Adjust by time horizon (longer term has more uncertainty)
            if time_horizon == "medium_term":
                confidence_mod = 0.9
            elif time_horizon == "long_term":
                confidence_mod = 0.7
            else:
                confidence_mod = 1.0
            
            # Create prediction
            treatment_response = {
                "treatment_id": treatment.get("id", f"treatment_{i}"),
                "treatment_name": treatment_name,
                "treatment_type": treatment_type,
                "efficacy_prediction": {
                    "value": round(base_efficacy, 2),
                    "confidence": round(confidence_mod * random.uniform(0.7, 0.9), 2)
                },
                "side_effect_prediction": {
                    "value": round(base_side_effects, 2),
                    "confidence": round(confidence_mod * random.uniform(0.7, 0.9), 2)
                },
                "adherence_prediction": {
                    "value": round(random.uniform(0.6, 0.95), 2),
                    "confidence": round(confidence_mod * random.uniform(0.7, 0.85), 2)
                },
                "time_to_response": {
                    "value": random.randint(1, 8),  # weeks
                    "confidence": round(confidence_mod * random.uniform(0.6, 0.8), 2)
                }
            }
            
            response["treatment_responses"].append(treatment_response)
        
        return response
    
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
        # Initialize response structure
        response = {
            "patient_id": str(patient_id),
            "digital_twin_state_id": str(digital_twin_state_id),
            "forecast_timestamp": datetime.now().isoformat(),
            "time_points": time_points,
            "with_treatment": with_treatment is not None,
            "treatment_details": with_treatment if with_treatment else None,
            "symptom_trajectories": [],
            "model_version": "mock-xgboost-v1.0"
        }
        
        # Generate trajectories for each symptom
        for symptom in symptoms:
            # Random starting severity (0-10 scale)
            current_severity = random.uniform(5.0, 8.0)
            
            # Treatment effect modifier
            treatment_effect = 0
            if with_treatment:
                treatment_type = with_treatment.get("type", "")
                if "medication" in treatment_type:
                    treatment_effect = -0.1  # Medications reduce severity faster
                elif "therapy" in treatment_type:
                    treatment_effect = -0.05  # Therapy reduces severity more gradually
            
            # Generate forecast points
            forecast_points = []
            confidence_intervals = []
            
            for day in time_points:
                # Calculate expected severity change
                # Without treatment: slight natural improvement over time
                # With treatment: faster improvement
                natural_change = -0.02 * day
                treatment_change = treatment_effect * day if with_treatment else 0
                
                # Add some randomness to make it realistic
                random_factor = random.uniform(-0.5, 0.5)
                
                # Calculate forecast severity, ensuring it stays in 0-10 range
                forecast_severity = max(0, min(10, current_severity + natural_change + treatment_change + random_factor))
                
                # Wider confidence intervals for later predictions
                ci_width = 0.5 + (day / 30) * 1.5
                lower_bound = max(0, forecast_severity - ci_width)
                upper_bound = min(10, forecast_severity + ci_width)
                
                # Add to forecast points
                forecast_points.append({
                    "day": day,
                    "severity": round(forecast_severity, 2)
                })
                
                confidence_intervals.append({
                    "day": day,
                    "lower_bound": round(lower_bound, 2),
                    "upper_bound": round(upper_bound, 2),
                    "confidence_level": 0.9
                })
            
            # Add symptom trajectory to response
            response["symptom_trajectories"].append({
                "symptom": symptom,
                "forecast_points": forecast_points,
                "confidence_intervals": confidence_intervals
            })
        
        return response
    
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
        # Generate synthetic risk factors based on target outcome
        risk_factors = []
        
        if "depression" in target_outcome.lower() or "mood" in target_outcome.lower():
            risk_factors = [
                {
                    "factor": "Sleep Disruption",
                    "importance_score": round(random.uniform(0.7, 0.9), 2),
                    "confidence": round(random.uniform(0.75, 0.9), 2),
                    "description": "Irregular sleep patterns contribute significantly to mood disorders.",
                    "actionable": True,
                    "related_brain_regions": ["HYPOTHALAMUS", "PREFRONTAL_CORTEX"]
                },
                {
                    "factor": "Social Isolation",
                    "importance_score": round(random.uniform(0.6, 0.85), 2),
                    "confidence": round(random.uniform(0.7, 0.85), 2),
                    "description": "Reduced social interaction is associated with increased depressive symptoms.",
                    "actionable": True,
                    "related_brain_regions": ["INSULA", "ANTERIOR_CINGULATE"]
                },
                {
                    "factor": "Physical Inactivity",
                    "importance_score": round(random.uniform(0.5, 0.8), 2),
                    "confidence": round(random.uniform(0.7, 0.85), 2),
                    "description": "Low levels of physical activity correlate with higher depression risk.",
                    "actionable": True,
                    "related_brain_regions": ["HIPPOCAMPUS"]
                }
            ]
        elif "anxiety" in target_outcome.lower():
            risk_factors = [
                {
                    "factor": "Catastrophic Thinking",
                    "importance_score": round(random.uniform(0.7, 0.9), 2),
                    "confidence": round(random.uniform(0.75, 0.9), 2),
                    "description": "Tendency to assume worst outcomes contributes to anxiety.",
                    "actionable": True,
                    "related_brain_regions": ["AMYGDALA", "PREFRONTAL_CORTEX"]
                },
                {
                    "factor": "Avoidance Behaviors",
                    "importance_score": round(random.uniform(0.65, 0.85), 2),
                    "confidence": round(random.uniform(0.7, 0.85), 2),
                    "description": "Avoidance of anxiety-provoking situations reinforces anxiety patterns.",
                    "actionable": True,
                    "related_brain_regions": ["AMYGDALA", "ANTERIOR_CINGULATE"]
                },
                {
                    "factor": "Irregular Breathing Patterns",
                    "importance_score": round(random.uniform(0.5, 0.7), 2),
                    "confidence": round(random.uniform(0.6, 0.8), 2),
                    "description": "Shallow, irregular breathing can trigger or worsen anxiety symptoms.",
                    "actionable": True,
                    "related_brain_regions": ["INSULA"]
                }
            ]
        else:
            # Generic risk factors
            risk_factors = [
                {
                    "factor": "Stress Levels",
                    "importance_score": round(random.uniform(0.6, 0.85), 2),
                    "confidence": round(random.uniform(0.7, 0.85), 2),
                    "description": "Elevated stress levels impact multiple health outcomes.",
                    "actionable": True,
                    "related_brain_regions": ["AMYGDALA", "PREFRONTAL_CORTEX"]
                },
                {
                    "factor": "Sleep Quality",
                    "importance_score": round(random.uniform(0.55, 0.8), 2),
                    "confidence": round(random.uniform(0.7, 0.85), 2),
                    "description": "Sleep quality affects cognitive function and emotional regulation.",
                    "actionable": True,
                    "related_brain_regions": ["HYPOTHALAMUS", "PREFRONTAL_CORTEX"]
                }
            ]
        
        return risk_factors
    
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
        # Generate synthetic feature importance scores
        feature_importance = []
        
        base_features = [
            "Sleep Quality",
            "Physical Activity Level",
            "Social Interaction Frequency",
            "Medication Adherence",
            "Stress Level",
            "Cognitive Function",
            "Emotional Regulation",
            "Nutritional Status"
        ]
        
        # Assign random importance scores
        total_importance = 0
        raw_scores = []
        
        for feature in base_features:
            # Random score between 0 and 1
            score = random.uniform(0.1, 1.0)
            raw_scores.append((feature, score))
            total_importance += score
        
        # Normalize scores to sum to 1
        for feature, score in raw_scores:
            normalized_score = score / total_importance
            
            feature_importance.append({
                "feature_name": feature,
                "importance_score": round(normalized_score, 3),
                "direction": "positive" if random.random() > 0.3 else "negative",
                "confidence": round(random.uniform(0.7, 0.9), 2),
                "description": f"Impact of {feature.lower()} on {prediction_type}."
            })
        
        # Sort by importance (descending)
        feature_importance.sort(key=lambda x: x["importance_score"], reverse=True)
        
        return feature_importance
    
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
        # Generate synthetic activation levels for all brain regions
        activations = {}
        
        for region in BrainRegion:
            # Generate random activation level between 0.3 and 0.9
            activation_level = random.uniform(0.3, 0.9)
            activations[region] = round(activation_level, 2)
        
        # Increase some correlations that would make neurological sense
        # (e.g., if amygdala is highly active, anterior cingulate might be too)
        if activations[BrainRegion.AMYGDALA] > 0.7:
            activations[BrainRegion.ANTERIOR_CINGULATE] = min(
                0.9, activations[BrainRegion.ANTERIOR_CINGULATE] + 0.2
            )
        
        if activations[BrainRegion.PREFRONTAL_CORTEX] < 0.5:
            activations[BrainRegion.AMYGDALA] = min(
                0.9, activations[BrainRegion.AMYGDALA] + 0.15
            )
        
        return activations
    
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
        results = []
        
        for treatment in treatment_options:
            treatment_type = treatment.get("type", "unknown")
            treatment_name = treatment.get("name", "Unknown Treatment")
            
            # Generate synthetic evaluation results
            evaluation = {}
            
            for metric in evaluation_metrics:
                metric_lower = metric.lower()
                
                if "efficacy" in metric_lower or "effectiveness" in metric_lower:
                    # Medications tend to be more effective for certain conditions
                    if treatment_type == "medication":
                        base_score = random.uniform(0.65, 0.85)
                    else:
                        base_score = random.uniform(0.6, 0.8)
                    
                    evaluation[metric] = {
                        "score": round(base_score, 2),
                        "confidence_interval": [
                            round(base_score - random.uniform(0.05, 0.15), 2),
                            round(base_score + random.uniform(0.05, 0.15), 2)
                        ],
                        "confidence": round(random.uniform(0.7, 0.9), 2)
                    }
                
                elif "side_effect" in metric_lower or "adverse" in metric_lower:
                    # Medications tend to have more side effects
                    if treatment_type == "medication":
                        base_score = random.uniform(0.2, 0.4)
                    else:
                        base_score = random.uniform(0.05, 0.2)
                    
                    evaluation[metric] = {
                        "score": round(base_score, 2),
                        "confidence_interval": [
                            round(base_score - random.uniform(0.05, 0.1), 2),
                            round(base_score + random.uniform(0.05, 0.1), 2)
                        ],
                        "confidence": round(random.uniform(0.7, 0.85), 2)
                    }
                
                elif "adherence" in metric_lower or "compliance" in metric_lower:
                    # Adherence can vary by treatment complexity
                    if "complex" in treatment_name.lower():
                        base_score = random.uniform(0.5, 0.7)
                    else:
                        base_score = random.uniform(0.7, 0.9)
                    
                    evaluation[metric] = {
                        "score": round(base_score, 2),
                        "confidence_interval": [
                            round(base_score - random.uniform(0.05, 0.15), 2),
                            round(base_score + random.uniform(0.05, 0.15), 2)
                        ],
                        "confidence": round(random.uniform(0.7, 0.85), 2)
                    }
                
                else:
                    # Generic metric
                    evaluation[metric] = {
                        "score": round(random.uniform(0.5, 0.8), 2),
                        "confidence_interval": [
                            round(random.uniform(0.4, 0.6), 2),
                            round(random.uniform(0.7, 0.9), 2)
                        ],
                        "confidence": round(random.uniform(0.7, 0.85), 2)
                    }
            
            results.append((treatment, evaluation))
        
        return results