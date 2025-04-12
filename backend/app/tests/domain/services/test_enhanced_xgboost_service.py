"""
Unit tests for EnhancedXGBoostService.

Tests the treatment response prediction and interaction analysis capabilities
of the XGBoost-based machine learning service.
"""
import uuid
from datetime import datetime, UTC

import pytest
import numpy as np

from app.domain.entities.digital_twin_enums import BrainRegion, Neurotransmitter
from app.domain.services.enhanced_xgboost_service import EnhancedXGBoostService


@pytest.mark.venv_only()
class TestEnhancedXGBoostService:
    """Test suite for the EnhancedXGBoostService."""
    
    @pytest.fixture
    def xgboost_service(self):
        """Create an EnhancedXGBoostService instance for testing."""
        
    return EnhancedXGBoostService()
    
    @pytest.fixture
    def test_patient_id(self):
        """Generate a test patient ID."""
        
    return uuid.uuid4()
    
    @pytest.fixture
    def test_baseline_data(self):
        """Create test baseline data."""
        
    return {
    "baseline_serotonin": 0.4,
    "baseline_dopamine": 0.6,
    "baseline_gaba": 0.5,
    "baseline_glutamate": 0.3,
    "sleep_quality": 0.7,
    "stress_level": 0.6
    }
    
    def test_predict_treatment_response_basic(self, xgboost_service, test_patient_id):
        """Test basic treatment response prediction."""
        # Test prediction for increasing serotonin
        prediction = xgboost_service.predict_treatment_response(
            patient_id=test_patient_id,
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            neurotransmitter=Neurotransmitter.SEROTONIN,
            treatment_effect=0.5
        )
        
        # Verify prediction structure
    assert "predicted_response" in prediction
    assert "confidence" in prediction
    assert "timeframe_days" in prediction
    assert "feature_importance" in prediction
        
        # Verify prediction values are within expected ranges
    assert 0 <= prediction["predicted_response"] <= 1.0
    assert 0 <= prediction["confidence"] <= 1.0
    assert prediction["timeframe_days"] > 0
    assert len(prediction["feature_importance"]) > 0
    
    def test_predict_treatment_response_with_baseline(self, xgboost_service, test_patient_id, test_baseline_data):
        """Test treatment response prediction with baseline data."""
        # Predict with baseline data
        prediction = xgboost_service.predict_treatment_response(
            patient_id=test_patient_id,
            brain_region=BrainRegion.AMYGDALA,
            neurotransmitter=Neurotransmitter.DOPAMINE,
            treatment_effect=0.7,
            baseline_data=test_baseline_data
        )
        
        # Verify prediction
    assert "predicted_response" in prediction
    assert 0 <= prediction["predicted_response"] <= 1.0
        
        # Verify feature importance includes baseline data
    importance = prediction["feature_importance"]
    assert "baseline_dopamine" in importance
    assert "baseline_serotonin" in importance
    
    def test_prediction_different_brain_regions(self, xgboost_service, test_patient_id):
        """Test predictions for different brain regions."""
        # Test prediction for different brain regions
        regions = [
            BrainRegion.PREFRONTAL_CORTEX,
            BrainRegion.AMYGDALA,
            BrainRegion.HIPPOCAMPUS,
            BrainRegion.RAPHE_NUCLEI
        ]
        
        # Get predictions for each region
    predictions = []
    for region in regions:
    prediction = xgboost_service.predict_treatment_response(
    patient_id=test_patient_id,
    brain_region=region,
    neurotransmitter=Neurotransmitter.SEROTONIN,
    treatment_effect=0.5
    )
    predictions.append(prediction["predicted_response"])
        
        # Verify that predictions differ by region
        # Not all predictions should be identical (extremely unlikely with our algorithm)
    assert len(set(predictions)) > 1, "Predictions should differ by brain region"
    
    def test_prediction_different_neurotransmitters(self, xgboost_service, test_patient_id):
        """Test predictions for different neurotransmitters."""
        # Test prediction for different neurotransmitters
        neurotransmitters = [
            Neurotransmitter.SEROTONIN,
            Neurotransmitter.DOPAMINE,
            Neurotransmitter.GABA,
            Neurotransmitter.GLUTAMATE
        ]
        
        # Get predictions for each neurotransmitter
    predictions = []
    for nt in neurotransmitters:
    prediction = xgboost_service.predict_treatment_response(
    patient_id=test_patient_id,
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    neurotransmitter=nt,
    treatment_effect=0.5
    )
    predictions.append(prediction["predicted_response"])
        
        # Verify that predictions differ by neurotransmitter
    assert len(set(predictions)) > 1, "Predictions should differ by neurotransmitter"
    
    def test_positive_vs_negative_treatment_effects(self, xgboost_service, test_patient_id, test_baseline_data):
        """Test that positive and negative treatment effects yield different predictions."""
        # Predict with positive effect
        positive_prediction = xgboost_service.predict_treatment_response(
            patient_id=test_patient_id,
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            neurotransmitter=Neurotransmitter.SEROTONIN,
            treatment_effect=0.5,
            baseline_data=test_baseline_data
        )
        
        # Predict with negative effect
    negative_prediction = xgboost_service.predict_treatment_response(
    patient_id=test_patient_id,
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    neurotransmitter=Neurotransmitter.SEROTONIN,
    treatment_effect=-0.5,
    baseline_data=test_baseline_data
    )
        
        # Predictions should differ for opposite treatment effects
    assert positive_prediction["predicted_response"] != negative_prediction["predicted_response"], \
    "Positive and negative treatment effects should yield different predictions"
    
    def test_analyze_treatment_interactions(self, xgboost_service):
        """Test analysis of interactions between neurotransmitter treatments."""
        # Test interaction analysis
        interactions = xgboost_service.analyze_treatment_interactions(
            primary_neurotransmitter=Neurotransmitter.SEROTONIN,
            primary_effect=0.5,
            secondary_neurotransmitters={
                Neurotransmitter.DOPAMINE: 0.3,
                Neurotransmitter.GABA: -0.2
            }
        )
        
        # Verify structure of interaction analysis
    assert "primary_neurotransmitter" in interactions
    assert "interactions" in interactions
    assert "net_interaction_score" in interactions
    assert "has_significant_interactions" in interactions
        
        # Verify specific interaction data
    assert "dopamine" in interactions["interactions"]
    assert "gaba" in interactions["interactions"]
        
    dopamine_interaction = interactions["interactions"]["dopamine"]
    assert "effect_on_secondary" in dopamine_interaction
    assert "effect_on_primary" in dopamine_interaction
    assert "net_interaction" in dopamine_interaction
    assert "is_synergistic" in dopamine_interaction
    
    def test_feature_encoding(self, xgboost_service):
        """Test that features are correctly encoded."""
        # Test encoding brain region
        region_encoding1 = xgboost_service._encode_brain_region(BrainRegion.PREFRONTAL_CORTEX)
        region_encoding2 = xgboost_service._encode_brain_region(BrainRegion.AMYGDALA)
        
        # Test encoding neurotransmitter
    nt_encoding1 = xgboost_service._encode_neurotransmitter(Neurotransmitter.SEROTONIN)
    nt_encoding2 = xgboost_service._encode_neurotransmitter(Neurotransmitter.DOPAMINE)
        
        # Verify encodings are valid numbers in expected range
    assert 0 <= region_encoding1 <= 1
    assert 0 <= region_encoding2 <= 1
    assert 0 <= nt_encoding1 <= 1
    assert 0 <= nt_encoding2 <= 1
        
        # Different values should have different encodings
    assert region_encoding1  !=  region_encoding2
    assert nt_encoding1  !=  nt_encoding2
    
    def test_consistency_of_predictions(self, xgboost_service, test_patient_id):
        """Test that predictions are consistent for the same inputs."""
        # Make prediction twice with same inputs
        prediction1 = xgboost_service.predict_treatment_response(
            patient_id=test_patient_id,
            brain_region=BrainRegion.PREFRONTAL_CORTEX,
            neurotransmitter=Neurotransmitter.SEROTONIN,
            treatment_effect=0.5
        )
        
    prediction2 = xgboost_service.predict_treatment_response(
    patient_id=test_patient_id,
    brain_region=BrainRegion.PREFRONTAL_CORTEX,
    neurotransmitter=Neurotransmitter.SEROTONIN,
    treatment_effect=0.5
    )
        
        # Predictions should be identical for identical inputs
    assert prediction1["predicted_response"] == prediction2["predicted_response"]
    assert prediction1["confidence"] == prediction2["confidence"]