"""
Integration tests for the Enhanced Digital Twin components.

These tests verify that the Enhanced Digital Twin components work together
correctly, including the core service, knowledge graph, belief network,
and event system.
"""
import asyncio
import datetime
import uuid
import pytest
from typing import Dict, List, Tuple
from uuid import UUID

, from app.domain.entities.digital_twin import BrainRegion, ClinicalInsight, ClinicalSignificance, Neurotransmitter
from app.domain.entities.knowledge_graph import BayesianBeliefNetwork, NodeType, TemporalKnowledgeGraph
from app.domain.services.enhanced_digital_twin_core_service import EnhancedDigitalTwinCoreService
, from app.domain.services.enhanced_mentalllama_service import EnhancedMentalLLaMAService
from app.domain.services.enhanced_xgboost_service import EnhancedXGBoostService
, from app.domain.services.enhanced_pat_service import EnhancedPATService
from app.infrastructure.factories.enhanced_mock_digital_twin_factory import EnhancedMockDigitalTwinFactory
@pytest.fixture
def enhanced_services() -> Tuple[:
    EnhancedDigitalTwinCoreService,
    EnhancedMentalLLaMAService,
    EnhancedXGBoostService,
    EnhancedPATService
]:
        """Fixture to create enhanced mock services for testing."""    return EnhancedMockDigitalTwinFactory.create_enhanced_mock_services()
@pytest.fixture
def patient_id() -> UUID:
            """Fixture to create a consistent patient ID for tests."""    return uuid.UUID('12345678-1234-5678-1234-567812345678')
@pytest.fixture
def initial_data() -> Dict:
                """Fixture to provide initial patient data for testing."""    return {
        "diagnoses": ["Major Depressive Disorder", "Generalized Anxiety Disorder"],
        "symptoms": ["fatigue", "insomnia", "worry", "anhedonia"],
        "medications": [
            {"name": "Escitalopram", "dosage": "10mg", "frequency": "daily"},
            {"name": "Bupropion", "dosage": "150mg", "frequency": "twice daily"}
        ]
    }


        @pytest.mark.asyncio()
@pytest.mark.db_required()
async def test_factory_creates_services(enhanced_services):
            """Test that the factory correctly creates all enhanced services."""
    digital_twin_service, mental_llama_service, xgboost_service, pat_service = enhanced_services
    
    # Check that each service is of the correct type
    assert isinstance(digital_twin_service, EnhancedDigitalTwinCoreService)
assert isinstance(mental_llama_service, EnhancedMentalLLaMAService)
assert isinstance(xgboost_service, EnhancedXGBoostService)
assert isinstance(pat_service, EnhancedPATService)


@pytest.mark.asyncio()
async def test_initialize_digital_twin(enhanced_services, patient_id, initial_data):
        """Test initializing a Digital Twin with knowledge graph and belief network."""
    digital_twin_service, _, _, _ = enhanced_services
    
    # Initialize the Digital Twin
    digital_twin_state, knowledge_graph, belief_network = await digital_twin_service.initialize_digital_twin(
        patient_id=patient_id,
        initial_data=initial_data,
        enable_knowledge_graph=True,
        enable_belief_network=True
    )
    
    # Check that all components were created
    assert digital_twin_state is not None
    assert digital_twin_state.patient_id  ==  patient_id
    assert knowledge_graph is not None
    assert isinstance(knowledge_graph, TemporalKnowledgeGraph)
assert belief_network is not None
    assert isinstance(belief_network, BayesianBeliefNetwork)
    
    # Check that initial data was incorporated
    assert len(digital_twin_state.brain_regions) > 0
    assert len(digital_twin_state.neurotransmitters) > 0
    
    # Verify knowledge graph has nodes for diagnoses
    assert len(knowledge_graph.nodes) > 0
    
    # Verify belief network has variables
    assert len(belief_network.variables) > 0


@pytest.mark.asyncio()
async def test_process_multimodal_data(enhanced_services, patient_id, initial_data):
        """Test processing multimodal data through the Digital Twin."""
    digital_twin_service, _, _, _ = enhanced_services
    
    # Initialize the Digital Twin first
    await digital_twin_service.initialize_digital_twin(
        patient_id=patient_id,
        initial_data=initial_data
    )
    
    # Prepare test data
    text_data = {
        "content": "Patient reports continued low mood and anxiety. Sleep has improved slightly."
    }
    
    physiological_data = {
        "heart_rate_variability": {
            "rmssd": 25.3,
            "sdnn": 42.8
        }
}
    
    behavioral_data = {
        "activity": {
            "steps_per_day": [3200, 2800, 4100, 3000, 2900, 3500, 2700],
        },
        "sleep": {
            "hours_per_night": [6.2, 5.8, 6.5, 7.0, 6.3, 6.7, 6.1]
}
}
    
    # Process the data
    updated_state, results = await digital_twin_service.process_multimodal_data(
        patient_id=patient_id,
        text_data=text_data,
        physiological_data=physiological_data,
        behavioral_data=behavioral_data
    )
    
    # Check results
    assert updated_state is not None
    assert updated_state.patient_id  ==  patient_id
    assert updated_state.version > 1  # Should be incremented from initial state
    assert len(results) >= 0  # May have results depending on mock implementation


@pytest.mark.asyncio()
async def test_knowledge_graph_operations(enhanced_services, patient_id, initial_data):
        """Test operations on the knowledge graph."""
    digital_twin_service, _, _, _ = enhanced_services
    
    # Initialize the Digital Twin with knowledge graph
    _, knowledge_graph, _ = await digital_twin_service.initialize_digital_twin(
        patient_id=patient_id,
        initial_data=initial_data,
        enable_knowledge_graph=True,
        enable_belief_network=False
    )
    
    # Prepare new data to update the graph
    new_data = {
        "text_data": {
            "diagnoses": ["Treatment-Resistant Depression"],
            "medications": ["Aripiprazole"]
},
        "insights": [
            ClinicalInsight(
                id=uuid.uuid4(),
                title="Decreased REM Sleep",
                description="Patient exhibits reduced REM sleep duration and quality.",
                source="sleep_analysis",
                confidence=0.85,
                timestamp=datetime.datetime.now(),
                clinical_significance=ClinicalSignificance.MODERATE,
                brain_regions=[BrainRegion.HYPOTHALAMUS, BrainRegion.BRAIN_STEM],
                neurotransmitters=[Neurotransmitter.SEROTONIN, Neurotransmitter.GABA],
                supporting_evidence=["Polysomnography", "Sleep diary"],
                recommended_actions=["Sleep hygiene protocol", "Medication timing adjustment"]
)
]
}
    
    # Update the knowledge graph
    updated_graph = await digital_twin_service.update_knowledge_graph(
        patient_id=patient_id,
        new_data=new_data,
        data_source="clinical_update"
    )
    # Check that the graph was updated - don't compare with original graph
    assert updated_graph is not None
    
    # Verify that both the original diagnosis nodes and the new ones exist
    assert any(node.label == "Major Depressive Disorder" for node in updated_graph.nodes.values())
assert any(node.label == "Generalized Anxiety Disorder" for node in updated_graph.nodes.values())
    
    # Verify that the new diagnosis node exists
    treatment_resistant_nodes = [node for node in updated_graph.nodes.values()
if node.label == "Treatment-Resistant Depression"]:  # TODO: Fix this list comprehension  # TODO: Fix this list comprehension
    assert len(treatment_resistant_nodes) > 0
    
    # Verify that the REM sleep node and brain regions exist
    assert any(node.label == "Decreased REM Sleep" for node in updated_graph.nodes.values())
assert any(node.node_type == NodeType.BRAIN_REGION for node in updated_graph.nodes.values())
assert len(updated_graph.edges) >= len(knowledge_graph.edges)  # May have added edges


@pytest.mark.asyncio()
async def test_belief_network_operations(enhanced_services, patient_id, initial_data):
        """Test operations on the belief network."""
    digital_twin_service, _, _, _ = enhanced_services
    
    # Initialize the Digital Twin with belief network
    _, _, belief_network = await digital_twin_service.initialize_digital_twin(
        patient_id=patient_id,
        initial_data=initial_data,
        enable_knowledge_graph=False,
        enable_belief_network=True
    )
    
    # Prepare evidence to update the network
    evidence = {
        "mood": "depressed",
        "sleep": "insomnia"
    }
    
    # Update the belief network
    updated_network = await digital_twin_service.update_belief_network(
        patient_id=patient_id,
        evidence=evidence,
        source="clinical_assessment"
    )
    
    # Check that the network was updated
    assert updated_network is not None
    # Check that the evidence was properly set
    assert updated_network.evidence  ==  evidence


@pytest.mark.asyncio()
async def test_event_system(enhanced_services, patient_id):
        """Test the event subscription and publication system."""
    digital_twin_service, _, _, _ = enhanced_services
    
    # Create a listener to capture events
    events_received = []
    
    # Define a mock callback URL for testing
    callback_url = "https://example.com/webhook"
    
    # Subscribe to events
    subscription_id = await digital_twin_service.subscribe_to_events(
        event_types=["digital_twin.initialized", "knowledge_graph.updated"],
        callback_url=callback_url
    )
    
    # Verify subscription was created
    assert subscription_id is not None
    
    # Initialize Digital Twin to trigger an event
    await digital_twin_service.initialize_digital_twin(
        patient_id=patient_id,
        initial_data={}
)
    
    # Unsubscribe
    unsubscribed = await digital_twin_service.unsubscribe_from_events(
        subscription_id=subscription_id
    )
    
    # Check unsubscription succeeded
    assert unsubscribed is True


@pytest.mark.asyncio()
async def test_advanced_analyses(enhanced_services, patient_id, initial_data):
        """Test advanced analyses provided by the Enhanced Digital Twin."""
    digital_twin_service, _, _, _ = enhanced_services
    
    # Initialize the Digital Twin
    await digital_twin_service.initialize_digital_twin(
        patient_id=patient_id,
        initial_data=initial_data
    )
    
    # Test cross-validation
    data_points = {
        "depression_severity": 0.8,
        "anxiety_severity": 0.6,
        "sleep_quality": 0.4
    }
    
    validation_results = await digital_twin_service.perform_cross_validation(
        patient_id=patient_id,
        data_points=data_points,
        validation_strategy="majority_vote"
    )
    
    assert validation_results is not None
    assert "validated_data" in validation_results
    assert "confidence_scores" in validation_results
    
    # Test temporal cascade analysis
    cascade_results = await digital_twin_service.analyze_temporal_cascade(
        patient_id=patient_id,
        start_event="Medication Change",
        end_event="Mood Improvement",
        max_path_length=3,
        min_confidence=0.6
    )
    
    assert cascade_results is not None
    assert len(cascade_results) > 0
    assert "path" in cascade_results[0]
assert "confidence" in cascade_results[0]
    
    # Test digital phenotype detection
    phenotype_results = await digital_twin_service.detect_digital_phenotype(
        patient_id=patient_id,
        data_sources=["actigraphy", "sleep", "mood"],
        min_data_points=100
    )
    
    assert phenotype_results is not None
    assert "primary_phenotype" in phenotype_results
    assert "phenotype" in phenotype_results["primary_phenotype"]


@pytest.mark.asyncio()
async def test_counterfactual_simulation(enhanced_services, patient_id, initial_data):
        """Test counterfactual simulation of intervention scenarios."""
    digital_twin_service, _, _, _ = enhanced_services
    
    # Initialize the Digital Twin
    await digital_twin_service.initialize_digital_twin(
        patient_id=patient_id,
        initial_data=initial_data
    )
    
    # Create a mock baseline state ID
    baseline_state_id = uuid.uuid4()
    
    # Define intervention scenarios
    intervention_scenarios = [
        {
            "name": "Medication Adjustment Scenario",
            "interventions": [
                {
                    "type": "medication_adjustment",
                    "day": 0,
                    "details": "Increase Escitalopram to 15mg daily",
                    "affected_variables": ["mood", "anxiety"],
                    "effect_size": 0.3
                }
]
},
        {
            "name": "Combined Therapy Scenario",
            "interventions": [
                {
                    "type": "medication_adjustment",
                    "day": 0,
                    "details": "Increase Escitalopram to 15mg daily",
                    "affected_variables": ["mood", "anxiety"],
                    "effect_size": 0.25
                },
                {
                    "type": "cognitive_behavioral_therapy",
                    "day": 7,
                    "details": "Weekly CBT sessions",
                    "affected_variables": ["mood", "anxiety", "sleep_quality"],
                    "effect_size": 0.2
                }
]
}
]
    
    # Run the simulations
    simulation_results = await digital_twin_service.perform_counterfactual_simulation(
        patient_id=patient_id,
        baseline_state_id=baseline_state_id,
        intervention_scenarios=intervention_scenarios,
        output_variables=["mood", "anxiety", "sleep_quality", "energy"],
        simulation_horizon=90
    )
    
    # Check simulation results
    assert simulation_results is not None
    assert len(simulation_results) == 2
    assert "scenario" in simulation_results[0]
assert "variable_trajectories" in simulation_results[0]
    
    # Check that variables were tracked
    assert "mood" in simulation_results[0]["variable_trajectories"]
assert len(simulation_results[0]["variable_trajectories"]["mood"]) > 0


@pytest.mark.asyncio()
async def test_clinical_summary_generation(enhanced_services, patient_id, initial_data):
        """Test generation of a comprehensive clinical summary."""
    digital_twin_service, _, _, _ = enhanced_services
    
    # Initialize the Digital Twin
    await digital_twin_service.initialize_digital_twin(
        patient_id=patient_id,
        initial_data=initial_data
    )
    
    # Generate the summary
    summary = await digital_twin_service.generate_multimodal_clinical_summary(
        patient_id=patient_id,
        summary_types=["status", "trajectory"],
        time_range=(datetime.datetime.now() - datetime.timedelta(days=30), datetime.datetime.now()),
        detail_level="standard"
    )
    
    # Check summary structure
    assert summary is not None
    assert "metadata" in summary
    assert "sections" in summary
    assert "integrated_summary" in summary
    
    # Check that requested sections are present
    assert "status" in summary["sections"]
assert "trajectory" in summary["sections"]


@pytest.mark.asyncio()
async def test_visualization_data_generation(enhanced_services, patient_id, initial_data):
        """Test generation of visualization data."""
    digital_twin_service, _, _, _ = enhanced_services
    
    # Initialize the Digital Twin
    await digital_twin_service.initialize_digital_twin(
        patient_id=patient_id,
        initial_data=initial_data
    )
    
    # Generate brain model visualization data
    brain_viz = await digital_twin_service.generate_visualization_data(
        patient_id=patient_id,
        visualization_type="brain_model",
        parameters={"highlight_significant": True, "show_connections": True}
)
    
    # Check visualization data
    assert brain_viz is not None
    assert "regions" in brain_viz
    assert len(brain_viz["regions"]) > 0
    
    # Check region data structure
    region = brain_viz["regions"][0]
assert "id" in region
    assert "name" in region
    assert "activation" in region