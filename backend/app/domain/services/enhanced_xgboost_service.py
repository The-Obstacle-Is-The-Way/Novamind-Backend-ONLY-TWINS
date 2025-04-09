"""
Enhanced XGBoost service for neurotransmitter prediction and analysis.

This module provides advanced prediction capabilities using XGBoost models
that have been enhanced with neuroscience domain knowledge for temporal
neurotransmitter analysis.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set, Optional, Any, Union
import uuid
from uuid import UUID
import math
import random

from app.domain.entities.digital_twin_enums import (
    BrainRegion, 
    Neurotransmitter, 
    ClinicalSignificance,
    NeurotransmitterState,
    TreatmentClass
)
from app.domain.entities.temporal_sequence import TemporalSequence
from app.domain.entities.neurotransmitter_effect import NeurotransmitterEffect


class EnhancedXGBoostService:
    """
    Service for neurotransmitter prediction and analysis using XGBoost models.
    
    This service implements treatment response prediction, neurotransmitter
    level forecasting, and treatment optimization using XGBoost models enhanced
    with neuroscience domain knowledge.
    """
    
    def __init__(self):
        """Initialize a new enhanced XGBoost service."""
        # Initialize treatment response mapping
        # This would normally be loaded from trained models, but using mock data for now
        self.treatment_response_models: Dict[TreatmentClass, Dict[Neurotransmitter, Dict[BrainRegion, float]]] = {
            TreatmentClass.SSRI: {
                Neurotransmitter.SEROTONIN: {
                    BrainRegion.PREFRONTAL_CORTEX: 0.7,
                    BrainRegion.RAPHE_NUCLEI: 0.9,
                    BrainRegion.HIPPOCAMPUS: 0.6,
                    BrainRegion.AMYGDALA: 0.5
                },
                Neurotransmitter.DOPAMINE: {
                    BrainRegion.NUCLEUS_ACCUMBENS: 0.3,
                    BrainRegion.STRIATUM: 0.2
                },
                Neurotransmitter.NOREPINEPHRINE: {
                    BrainRegion.LOCUS_COERULEUS: 0.4,
                    BrainRegion.PREFRONTAL_CORTEX: 0.3
                }
            },
            TreatmentClass.SNRI: {
                Neurotransmitter.SEROTONIN: {
                    BrainRegion.PREFRONTAL_CORTEX: 0.6,
                    BrainRegion.RAPHE_NUCLEI: 0.7,
                    BrainRegion.HIPPOCAMPUS: 0.5
                },
                Neurotransmitter.NOREPINEPHRINE: {
                    BrainRegion.LOCUS_COERULEUS: 0.8,
                    BrainRegion.PREFRONTAL_CORTEX: 0.7,
                    BrainRegion.AMYGDALA: 0.6
                },
                Neurotransmitter.DOPAMINE: {
                    BrainRegion.NUCLEUS_ACCUMBENS: 0.4,
                    BrainRegion.STRIATUM: 0.3
                }
            },
            TreatmentClass.NDRI: {
                Neurotransmitter.DOPAMINE: {
                    BrainRegion.NUCLEUS_ACCUMBENS: 0.8,
                    BrainRegion.PREFRONTAL_CORTEX: 0.7,
                    BrainRegion.STRIATUM: 0.9
                },
                Neurotransmitter.NOREPINEPHRINE: {
                    BrainRegion.LOCUS_COERULEUS: 0.7,
                    BrainRegion.PREFRONTAL_CORTEX: 0.6
                }
            },
            TreatmentClass.ATYPICAL_ANTIPSYCHOTIC: {
                Neurotransmitter.DOPAMINE: {
                    BrainRegion.STRIATUM: -0.7,
                    BrainRegion.NUCLEUS_ACCUMBENS: -0.6,
                    BrainRegion.PREFRONTAL_CORTEX: -0.3
                },
                Neurotransmitter.SEROTONIN: {
                    BrainRegion.PREFRONTAL_CORTEX: 0.4,
                    BrainRegion.RAPHE_NUCLEI: 0.3
                }
            },
            TreatmentClass.BENZODIAZEPINE: {
                Neurotransmitter.GABA: {
                    BrainRegion.AMYGDALA: 0.8,
                    BrainRegion.PREFRONTAL_CORTEX: 0.7,
                    BrainRegion.HIPPOCAMPUS: 0.6
                }
            },
            TreatmentClass.STIMULANT: {
                Neurotransmitter.DOPAMINE: {
                    BrainRegion.PREFRONTAL_CORTEX: 0.8,
                    BrainRegion.NUCLEUS_ACCUMBENS: 0.7,
                    BrainRegion.STRIATUM: 0.9
                },
                Neurotransmitter.NOREPINEPHRINE: {
                    BrainRegion.PREFRONTAL_CORTEX: 0.7,
                    BrainRegion.LOCUS_COERULEUS: 0.8
                }
            }
        }
        
        # Time profile models - how fast different treatments act
        self.time_profiles: Dict[TreatmentClass, Dict[str, float]] = {
            TreatmentClass.SSRI: {
                "onset_days": 14.0,  # Initial effects after 2 weeks
                "peak_days": 42.0,   # Full effect after 6 weeks
                "decay_rate": 0.1    # Slow decay of effect on discontinuation
            },
            TreatmentClass.SNRI: {
                "onset_days": 10.0,  # Initial effects after 10 days
                "peak_days": 35.0,   # Full effect after 5 weeks
                "decay_rate": 0.15   # Moderate decay of effect
            },
            TreatmentClass.NDRI: {
                "onset_days": 7.0,   # Initial effects after 1 week
                "peak_days": 28.0,   # Full effect after 4 weeks
                "decay_rate": 0.2    # Moderate decay of effect
            },
            TreatmentClass.ATYPICAL_ANTIPSYCHOTIC: {
                "onset_days": 3.0,   # Initial effects after 3 days
                "peak_days": 21.0,   # Full effect after 3 weeks
                "decay_rate": 0.3    # Faster decay of effect
            },
            TreatmentClass.BENZODIAZEPINE: {
                "onset_days": 0.125,  # Initial effects after 3 hours
                "peak_days": 0.5,     # Full effect after 12 hours
                "decay_rate": 0.5     # Rapid decay of effect
            },
            TreatmentClass.STIMULANT: {
                "onset_days": 0.04,   # Initial effects after 1 hour
                "peak_days": 0.25,    # Full effect after 6 hours
                "decay_rate": 0.8     # Very rapid decay of effect
            }
        }
        
        # Side effect models - probability of side effects by brain region and neurotransmitter
        self.side_effect_models: Dict[TreatmentClass, Dict[str, float]] = {
            TreatmentClass.SSRI: {
                "nausea": 0.3,
                "sexual_dysfunction": 0.4,
                "insomnia": 0.25,
                "anxiety": 0.2
            },
            TreatmentClass.SNRI: {
                "nausea": 0.35,
                "sexual_dysfunction": 0.35,
                "insomnia": 0.3,
                "hypertension": 0.2
            },
            TreatmentClass.NDRI: {
                "insomnia": 0.4,
                "anxiety": 0.3,
                "dry_mouth": 0.25,
                "seizure": 0.01
            },
            TreatmentClass.ATYPICAL_ANTIPSYCHOTIC: {
                "weight_gain": 0.5,
                "sedation": 0.4,
                "metabolic_changes": 0.3,
                "extrapyramidal": 0.1
            },
            TreatmentClass.BENZODIAZEPINE: {
                "sedation": 0.7,
                "cognitive_impairment": 0.3,
                "dependence": 0.2,
                "ataxia": 0.15
            },
            TreatmentClass.STIMULANT: {
                "appetite_loss": 0.6,
                "insomnia": 0.5,
                "anxiety": 0.3,
                "hypertension": 0.2
            }
        }
    
    def predict_treatment_response(
        self,
        treatment_class: TreatmentClass,
        patient_features: Dict[str, Any],
        target_neurotransmitters: Optional[List[Neurotransmitter]] = None,
        target_regions: Optional[List[BrainRegion]] = None
    ) -> Dict[Neurotransmitter, Dict[BrainRegion, float]]:
        """
        Predict how a patient will respond to a specific treatment class.
        
        Args:
            treatment_class: Type of treatment
            patient_features: Patient characteristics and biomarkers
            target_neurotransmitters: Optional neurotransmitters to focus on
            target_regions: Optional brain regions to focus on
            
        Returns:
            Dictionary mapping neurotransmitters to brain regions to effect size
        """
        # Get base response model for this treatment
        if treatment_class not in self.treatment_response_models:
            raise ValueError(f"No response model available for {treatment_class.value}")
        
        base_response = self.treatment_response_models[treatment_class]
        
        # Filter for target neurotransmitters if specified
        if target_neurotransmitters:
            filtered_response = {nt: regions for nt, regions in base_response.items() 
                               if nt in target_neurotransmitters}
        else:
            filtered_response = base_response.copy()
        
        # Filter for target regions if specified
        if target_regions:
            for nt, regions in filtered_response.items():
                filtered_response[nt] = {region: effect for region, effect in regions.items()
                                       if region in target_regions}
        
        # Apply patient-specific factors
        personalized_response = self._personalize_response(filtered_response, patient_features)
        
        return personalized_response
    
    def _personalize_response(
        self,
        base_response: Dict[Neurotransmitter, Dict[BrainRegion, float]],
        patient_features: Dict[str, Any]
    ) -> Dict[Neurotransmitter, Dict[BrainRegion, float]]:
        """
        Adjust treatment response based on patient features.
        
        Args:
            base_response: Base treatment response model
            patient_features: Patient characteristics and biomarkers
            
        Returns:
            Personalized response predictions
        """
        # Create a deep copy to avoid modifying the base model
        result = {}
        
        # Extract relevant features
        age = patient_features.get("age", 40)
        sex = patient_features.get("sex", "female")
        genetics = patient_features.get("genetics", {})
        baseline_levels = patient_features.get("baseline_levels", {})
        
        # Process each neurotransmitter
        for nt, regions in base_response.items():
            result[nt] = {}
            
            # Get genetic factors for this neurotransmitter
            genetic_factor = genetics.get(nt.value, 1.0)
            
            # Process each brain region
            for region, effect in regions.items():
                # Start with base effect
                adjusted_effect = effect
                
                # Adjust for age
                if age > 65:
                    # Elderly patients may have reduced response
                    adjusted_effect *= 0.8
                elif age < 18:
                    # Adolescents may have different response
                    adjusted_effect *= 0.9
                
                # Adjust for sex differences
                if nt == Neurotransmitter.SEROTONIN and sex == "female":
                    # Some studies suggest stronger serotonergic response in females
                    adjusted_effect *= 1.1
                
                # Adjust for genetic factors
                adjusted_effect *= genetic_factor
                
                # Adjust for baseline levels
                baseline = baseline_levels.get(f"{nt.value}_{region.value}", 0.5)
                if baseline < 0.3:
                    # Greater effect if starting from deficiency
                    adjusted_effect *= 1.2
                elif baseline > 0.7:
                    # Reduced effect if already high
                    adjusted_effect *= 0.8
                
                # Store adjusted effect
                result[nt][region] = min(1.0, max(-1.0, adjusted_effect))
        
        return result
    
    def predict_treatment_time_course(
        self,
        treatment_class: TreatmentClass,
        duration_days: float,
        dose_factor: float = 1.0,
        patient_metabolism: float = 1.0
    ) -> Dict[str, List[Tuple[float, float]]]:
        """
        Predict the time course of treatment effects.
        
        Args:
            treatment_class: Type of treatment
            duration_days: Duration of treatment in days
            dose_factor: Dose relative to standard (0.0-2.0)
            patient_metabolism: Patient's metabolic rate (0.5-2.0)
            
        Returns:
            Dictionary with time course data
        """
        if treatment_class not in self.time_profiles:
            raise ValueError(f"No time profile available for {treatment_class.value}")
        
        # Get base time profile
        profile = self.time_profiles[treatment_class]
        
        # Adjust time parameters based on dose and metabolism
        onset_days = profile["onset_days"] / (dose_factor * patient_metabolism)
        peak_days = profile["peak_days"] / (dose_factor * patient_metabolism)
        decay_rate = profile["decay_rate"] * patient_metabolism
        
        # Generate time points (days)
        time_points = []
        step_size = min(0.25, onset_days / 4)  # At least 4 points during onset
        current_day = 0.0
        
        while current_day <= duration_days + 10:  # Extra 10 days to show decay
            time_points.append(current_day)
            
            # Use smaller steps during onset and withdrawal
            if current_day < onset_days or current_day > duration_days:
                current_day += step_size
            else:
                current_day += max(step_size, min(1.0, (peak_days - onset_days) / 10))
        
        # Generate effect levels
        effect_curve = []
        withdrawal_curve = []
        side_effect_curve = []
        
        for t in time_points:
            # Calculate effect level
            if t < onset_days:
                # Initial onset phase (sigmoid curve)
                effect = self._sigmoid(t / onset_days) * 0.3
            elif t < peak_days:
                # Ramp-up phase (sigmoid curve)
                effect = 0.3 + (0.7 * self._sigmoid((t - onset_days) / (peak_days - onset_days)))
            elif t <= duration_days:
                # Stable phase with slight tolerance development
                time_stable = t - peak_days
                tolerance = min(0.2, time_stable * 0.004)  # Max 20% tolerance
                effect = 1.0 - tolerance
            else:
                # Withdrawal phase (exponential decay)
                time_since_stop = t - duration_days
                effect = max(0, (1.0 - 0.2) * math.exp(-decay_rate * time_since_stop))
            
            # Calculate withdrawal effects (rebound effects after stopping)
            withdrawal = 0.0
            if t > duration_days:
                time_since_stop = t - duration_days
                # Withdrawal peaks at 1-2 days after stopping, then gradually subsides
                withdrawal = (0.5 * time_since_stop * math.exp(-time_since_stop / 2)) * decay_rate
            
            # Calculate side effect intensity
            # Side effects develop quickly, may decrease with tolerance, increase with dose
            if t < onset_days:
                side_effect = self._sigmoid(t / (onset_days * 0.5)) * 0.8
            elif t < peak_days * 2:
                # First increase, then slight adaptation
                side_effect = 0.8 - (0.3 * self._sigmoid((t - onset_days) / peak_days))
            else:
                # Stable with slight further adaptation
                side_effect = 0.5 - (0.1 * self._sigmoid((t - peak_days * 2) / peak_days))
            
            # Adjust side effects for dose
            side_effect *= dose_factor
            
            # Add to curves
            effect_curve.append((t, effect * dose_factor))
            withdrawal_curve.append((t, withdrawal))
            side_effect_curve.append((t, min(1.0, side_effect)))
        
        return {
            "effect": effect_curve,
            "withdrawal": withdrawal_curve,
            "side_effects": side_effect_curve
        }
    
    def _sigmoid(self, x: float) -> float:
        """
        Sigmoid function for smooth transitions.
        
        Args:
            x: Input value
            
        Returns:
            Sigmoid of x (0.0-1.0)
        """
        return 1.0 / (1.0 + math.exp(-10 * (x - 0.5)))
    
    def predict_side_effects(
        self,
        treatment_class: TreatmentClass,
        patient_features: Dict[str, Any],
        dose_factor: float = 1.0
    ) -> Dict[str, float]:
        """
        Predict side effects for a specific treatment and patient.
        
        Args:
            treatment_class: Type of treatment
            patient_features: Patient characteristics and biomarkers
            dose_factor: Dose relative to standard (0.0-2.0)
            
        Returns:
            Dictionary mapping side effects to probabilities
        """
        if treatment_class not in self.side_effect_models:
            raise ValueError(f"No side effect model available for {treatment_class.value}")
        
        # Get base side effect model
        base_side_effects = self.side_effect_models[treatment_class]
        
        # Extract relevant patient features
        age = patient_features.get("age", 40)
        sex = patient_features.get("sex", "female")
        weight = patient_features.get("weight", 70)
        existing_conditions = patient_features.get("conditions", [])
        
        # Adjust side effects based on patient factors
        result = {}
        
        for effect, probability in base_side_effects.items():
            # Start with base probability
            adjusted_prob = probability
            
            # Adjust for dose
            adjusted_prob *= dose_factor
            
            # Adjust for age
            if age > 65:
                # Elderly patients often have more side effects
                adjusted_prob *= 1.5
            elif age < 18:
                # Adolescents may have different side effect profiles
                if effect in ["sexual_dysfunction"]:
                    adjusted_prob *= 0.7
                elif effect in ["agitation", "anxiety", "insomnia"]:
                    adjusted_prob *= 1.3
            
            # Adjust for sex differences
            if sex == "female" and effect in ["nausea", "weight_gain"]:
                adjusted_prob *= 1.2
            elif sex == "male" and effect in ["sexual_dysfunction"]:
                adjusted_prob *= 1.3
            
            # Adjust for weight
            if weight < 55 and effect in ["sedation", "hypotension"]:
                adjusted_prob *= 1.3
            
            # Adjust for existing conditions
            for condition in existing_conditions:
                if condition == "liver_disease" and effect in ["metabolic_changes", "hepatotoxicity"]:
                    adjusted_prob *= 1.5
                elif condition == "kidney_disease":
                    adjusted_prob *= 1.3
                elif condition == "diabetes" and effect in ["weight_gain", "metabolic_changes"]:
                    adjusted_prob *= 1.4
            
            # Ensure probability stays in valid range
            result[effect] = min(1.0, adjusted_prob)
        
        return result
    
    def forecast_neurotransmitter_levels(
        self,
        treatment_class: TreatmentClass,
        duration_days: float,
        current_levels: Dict[Neurotransmitter, Dict[BrainRegion, float]],
        patient_features: Dict[str, Any],
        dose_factor: float = 1.0,
        time_resolution_days: float = 1.0
    ) -> Dict[Neurotransmitter, Dict[BrainRegion, List[Tuple[float, float]]]]:
        """
        Forecast neurotransmitter levels over time during treatment.
        
        Args:
            treatment_class: Type of treatment
            duration_days: Duration of treatment in days
            current_levels: Current neurotransmitter levels by region
            patient_features: Patient characteristics
            dose_factor: Dose relative to standard (0.0-2.0)
            time_resolution_days: Time step for the forecast
            
        Returns:
            Dictionary with forecasted levels
        """
        # Get treatment response
        response = self.predict_treatment_response(
            treatment_class, 
            patient_features
        )
        
        # Get time course of treatment effect
        time_course = self.predict_treatment_time_course(
            treatment_class,
            duration_days,
            dose_factor,
            patient_features.get("metabolism", 1.0)
        )
        
        effect_curve = time_course["effect"]
        
        # Initialize result structure
        result = {}
        
        # Process each neurotransmitter
        for nt, regions in response.items():
            result[nt] = {}
            
            # Get current levels for this neurotransmitter
            nt_current = current_levels.get(nt, {})
            
            # Process each brain region
            for region, effect_size in regions.items():
                # Get current level for this region (default to 0.5 if not provided)
                current = nt_current.get(region, 0.5)
                
                # Generate forecast
                forecast = []
                
                for day, effect_factor in effect_curve:
                    # Calculate effect at this time point
                    effect = effect_size * effect_factor
                    
                    # Calculate new level
                    new_level = current + effect
                    
                    # Ensure level stays in valid range
                    new_level = min(1.0, max(0.0, new_level))
                    
                    # Add to forecast
                    forecast.append((day, new_level))
                
                # Add to result
                result[nt][region] = forecast
        
        return result
    
    def recommend_treatment(
        self,
        patient_features: Dict[str, Any],
        target_neurotransmitters: Dict[Neurotransmitter, Dict[BrainRegion, float]],
        available_treatments: Optional[List[TreatmentClass]] = None,
        side_effect_weights: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recommend optimal treatments based on patient features and targets.
        
        Args:
            patient_features: Patient characteristics
            target_neurotransmitters: Target levels by region
            available_treatments: Treatments to consider
            side_effect_weights: Weights for different side effects
            
        Returns:
            List of treatment recommendations with scores
        """
        # Use all available treatments if not specified
        if not available_treatments:
            available_treatments = list(self.treatment_response_models.keys())
        
        # Default side effect weights
        if not side_effect_weights:
            side_effect_weights = {
                "sexual_dysfunction": 0.7,
                "weight_gain": 0.8,
                "sedation": 0.6,
                "nausea": 0.5,
                "insomnia": 0.6,
                "anxiety": 0.7,
                "hypertension": 0.7,
                "metabolic_changes": 0.8,
                "extrapyramidal": 0.9,
                "seizure": 1.0
            }
        
        # Evaluate each treatment
        recommendations = []
        
        for treatment in available_treatments:
            # Predict response
            response = self.predict_treatment_response(
                treatment,
                patient_features
            )
            
            # Predict side effects
            side_effects = self.predict_side_effects(
                treatment,
                patient_features
            )
            
            # Calculate efficacy score
            efficacy_score = self._calculate_efficacy_score(response, target_neurotransmitters)
            
            # Calculate side effect score
            side_effect_score = self._calculate_side_effect_score(side_effects, side_effect_weights)
            
            # Calculate overall score (higher is better)
            overall_score = efficacy_score - side_effect_score
            
            # Add to recommendations
            recommendations.append({
                "treatment": treatment.value,
                "overall_score": overall_score,
                "efficacy_score": efficacy_score,
                "side_effect_score": side_effect_score,
                "predicted_response": self._summarize_response(response),
                "predicted_side_effects": side_effects
            })
        
        # Sort by overall score (descending)
        recommendations.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return recommendations
    
    def _calculate_efficacy_score(
        self,
        response: Dict[Neurotransmitter, Dict[BrainRegion, float]],
        targets: Dict[Neurotransmitter, Dict[BrainRegion, float]]
    ) -> float:
        """
        Calculate how well treatment response matches target neurotransmitter levels.
        
        Args:
            response: Predicted treatment response
            targets: Target neurotransmitter levels
            
        Returns:
            Efficacy score (0.0-1.0)
        """
        score = 0.0
        count = 0
        
        # Compare response to targets
        for nt, target_regions in targets.items():
            if nt not in response:
                continue
                
            for region, target_level in target_regions.items():
                if region not in response[nt]:
                    continue
                
                # Get predicted effect
                effect = response[nt][region]
                
                # Calculate match score
                # Is the effect in the right direction and magnitude?
                match_score = 0.0
                
                if target_level > 0.5 and effect > 0:
                    # Want to increase, treatment increases
                    match_score = min(1.0, effect / (target_level - 0.5) * 2)
                elif target_level < 0.5 and effect < 0:
                    # Want to decrease, treatment decreases
                    match_score = min(1.0, abs(effect) / (0.5 - target_level) * 2)
                elif target_level == 0.5 and abs(effect) < 0.1:
                    # Want to maintain, treatment has minimal effect
                    match_score = 1.0 - abs(effect) * 10
                
                # Add to score
                score += match_score
                count += 1
        
        # Calculate average score
        if count > 0:
            return score / count
        else:
            return 0.0
    
    def _calculate_side_effect_score(
        self,
        side_effects: Dict[str, float],
        weights: Dict[str, float]
    ) -> float:
        """
        Calculate weighted side effect score.
        
        Args:
            side_effects: Predicted side effects with probabilities
            weights: Weights for each side effect
            
        Returns:
            Weighted side effect score (higher means worse)
        """
        score = 0.0
        total_weight = 0.0
        
        for effect, probability in side_effects.items():
            weight = weights.get(effect, 0.5)
            score += probability * weight
            total_weight += weight
        
        if total_weight > 0:
            return score / total_weight
        else:
            return 0.0
    
    def _summarize_response(
        self,
        response: Dict[Neurotransmitter, Dict[BrainRegion, float]]
    ) -> Dict[str, Any]:
        """
        Create a summary of the treatment response.
        
        Args:
            response: Detailed treatment response
            
        Returns:
            Summarized response
        """
        summary = {}
        
        for nt, regions in response.items():
            effects = list(regions.values())
            
            if not effects:
                continue
                
            avg_effect = sum(effects) / len(effects)
            max_effect = max(effects, key=abs)
            max_region = next(region for region, effect in regions.items() 
                            if abs(effect) == abs(max_effect))
            
            summary[nt.value] = {
                "average_effect": avg_effect,
                "strongest_effect": max_effect,
                "strongest_region": max_region.value,
                "regions_affected": len(regions)
            }
        
        return summary