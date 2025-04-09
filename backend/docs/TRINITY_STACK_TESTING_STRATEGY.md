# Trinity Stack Testing Strategy

## Overview

This document outlines a comprehensive testing strategy for the Trinity Stack components (MentalLLaMA, XGBoost, PAT) of the Novamind Digital Twin platform. The goal is to ensure all components work correctly both individually and as an integrated whole.

## Testing Levels

### 1. Unit Testing

Unit tests verify that individual components function correctly in isolation.

#### MentalLLaMA Tests

```python
# tests/unit/domain/services/trinity_stack/test_mental_llama_service.py
import pytest
from uuid import uuid4, UUID
from datetime import datetime

from app.domain.services.refactored.trinity_stack.mental_llama_service import MentalLLaMAService
from app.infrastructure.services.mock_mentalllama_service import MockMentalLLaMAService
from app.domain.entities.refactored.digital_twin_core import ClinicalInsight

@pytest.fixture
def mental_llama_service() -> MentalLLaMAService:
    return MockMentalLLaMAService()

@pytest.mark.asyncio
async def test_analyze_clinical_notes(mental_llama_service: MentalLLaMAService):
    patient_id = uuid4()
    note_text = "Patient reports feeling depressed with low mood and decreased energy. Sleep has been poor."
    
    insights = await mental_llama_service.analyze_clinical_notes(
        patient_id=patient_id,
        note_text=note_text
    )
    
    # Verify insights were generated
    assert len(insights) > 0
    assert all(isinstance(insight, ClinicalInsight) for insight in insights)
    assert any("Depression" in insight.title for insight in insights)
    assert any("Sleep" in insight.title for insight in insights)
```

#### PAT Tests

```python
# tests/unit/domain/services/trinity_stack/test_pat_service.py
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from app.domain.services.refactored.trinity_stack.pat_service import PATService
from app.infrastructure.services.mock_pat_service import MockPATService

@pytest.fixture
def pat_service() -> PATService:
    return MockPATService()

@pytest.mark.asyncio
async def test_process_actigraphy_data(pat_service: PATService):
    patient_id = uuid4()
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    # Create sample actigraphy data
    actigraphy_data = {
        "steps": [8000, 10000, 6000, 7500, 9000, 5000, 8500],
        "heart_rate": [72, 75, 68, 70, 74, 71, 73],
        "sleep_hours": [7.5, 6.8, 7.2, 8.0, 6.5, 7.0, 7.8]
    }
    
    result = await pat_service.process_actigraphy_data(
        patient_id=patient_id,
        actigraphy_data=actigraphy_data,
        data_source="fitbit",
        start_time=start_time,
        end_time=end_time
    )
    
    # Verify results
    assert "patient_id" in result
    assert "data_source" in result
    assert "analysis_timestamp" in result
    assert "activity_patterns" in result
    assert "sleep_analysis" in result
    assert "behavioral_insights" in result
```

#### XGBoost Tests

```python
# tests/unit/domain/services/trinity_stack/test_xgboost_service.py
import pytest
from uuid import uuid4
from datetime import datetime

from app.domain.services.refactored.trinity_stack.xgboost_service import XGBoostService
from app.infrastructure.services.mock_xgboost_service import MockXGBoostService

@pytest.fixture
def xgboost_service() -> XGBoostService:
    return MockXGBoostService()

@pytest.mark.asyncio
async def test_predict_treatment_response(xgboost_service: XGBoostService):
    patient_id = uuid4()
    digital_twin_state_id = uuid4()
    
    treatment_options = [
        {
            "id": "treatment_1",
            "type": "medication",
            "name": "Sertraline",
            "dosage": "50mg",
            "frequency": "daily"
        },
        {
            "id": "treatment_2",
            "type": "therapy",
            "name": "CBT",
            "sessions": 12,
            "frequency": "weekly"
        }
    ]
    
    result = await xgboost_service.predict_treatment_response(
        patient_id=patient_id,
        digital_twin_state_id=digital_twin_state_id,
        treatment_options=treatment_options,
        time_horizon="medium_term"
    )
    
    # Verify results
    assert "patient_id" in result
    assert "digital_twin_state_id" in result
    assert "treatment_responses" in result
    assert len(result["treatment_responses"]) == 2
    assert all("efficacy_prediction" in tr for tr in result["treatment_responses"])
    assert all("side_effect_prediction" in tr for tr in result["treatment_responses"])
```

### 2. Component Testing

Component tests validate that individual Trinity Stack components can perform their core functions correctly.

```python
# tests/component/test_mental_llama_component.py
import pytest
from uuid import uuid4

from app.infrastructure.factories.trinity_stack_factory import TrinityStackFactory
from app.domain.entities.refactored.digital_twin_core import ClinicalSignificance

@pytest.mark.asyncio
async def test_mental_llama_clinical_insights():
    # Create service
    service = TrinityStackFactory.create_mental_llama_service()
    patient_id = uuid4()
    
    # Test multiple types of clinical notes
    test_cases = [
        {
            "notes": "Patient reports severe depression with suicidal ideation.",
            "expected_significance": ClinicalSignificance.HIGH,
            "expected_keywords": ["depression", "suicidal"]
        },
        {
            "notes": "Patient is sleeping well and mood has improved.",
            "expected_significance": ClinicalSignificance.LOW,
            "expected_keywords": ["sleep", "mood", "improved"]
        },
        {
            "notes": "Patient reports anxiety in social situations.",
            "expected_significance": ClinicalSignificance.MODERATE,
            "expected_keywords": ["anxiety", "social"]
        }
    ]
    
    for case in test_cases:
        insights = await service.analyze_clinical_notes(
            patient_id=patient_id,
            note_text=case["notes"]
        )
        
        # Check if insights match expected patterns
        assert len(insights) > 0
        
        # Check if any insight matches expected significance
        assert any(insight.clinical_significance == case["expected_significance"] 
                  for insight in insights)
        
        # Check if keywords are found in insights
        for keyword in case["expected_keywords"]:
            assert any(keyword.lower() in insight.description.lower() 
                      or keyword.lower() in insight.title.lower() 
                      for insight in insights)
```

### 3. Integration Testing

Integration tests verify that all components work together correctly.

```python
# tests/integration/test_trinity_stack_integration.py
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from app.domain.services.refactored.digital_twin_core_service import DigitalTwinCoreService
from app.infrastructure.factories.trinity_stack_factory import TrinityStackFactory

@pytest.fixture
def digital_twin_core_service() -> DigitalTwinCoreService:
    return TrinityStackFactory.create_digital_twin_core_service()

@pytest.mark.asyncio
async def test_multimodal_data_integration(digital_twin_core_service: DigitalTwinCoreService):
    # Set up test data
    patient_id = uuid4()
    
    # Initialize digital twin
    twin_state, knowledge_graph, belief_network = await digital_twin_core_service.initialize_digital_twin(
        reference_id=patient_id,
        enable_knowledge_graph=True,
        enable_belief_network=True
    )
    
    assert twin_state is not None
    assert knowledge_graph is not None
    assert belief_network is not None
    
    # Prepare multimodal data
    text_data = {
        "clinical_notes": "Patient reports feeling depressed with low energy and poor sleep. Anxiety in social situations."
    }
    
    physiological_data = {
        "heart_rate": {
            "timestamps": [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)],
            "values": [70 + (i % 10) for i in range(24)]
        },
        "sleep": {
            "duration_hours": 6.2,
            "efficiency": 0.75,
            "awakenings": 3
        }
    }
    
    behavioral_data = {
        "daily_steps": 4500,
        "active_minutes": 25,
        "social_interactions": "decreased"
    }
    
    # Process multimodal data
    updated_state, results = await digital_twin_core_service.process_multimodal_data(
        reference_id=patient_id,
        text_data=text_data,
        physiological_data=physiological_data,
        behavioral_data=behavioral_data
    )
    
    # Verify results
    assert updated_state is not None
    assert len(updated_state.clinical_insights) > 0
    
    # Verify that all three components contributed to the results
    sources = {insight.source for insight in updated_state.clinical_insights}
    assert "MentalLLaMA" in sources
    assert "PAT" in sources or "Actigraphy" in sources
    assert "XGBoost" in sources or "Prediction" in sources
    
    # Verify that knowledge graph was updated
    updated_graph = await digital_twin_core_service.update_knowledge_graph(
        reference_id=patient_id,
        new_data={"clinical_insights": [insight.to_dict() for insight in updated_state.clinical_insights]},
        data_source="integration_test"
    )
    
    assert len(updated_graph.nodes) > len(knowledge_graph.nodes)
```

### 4. End-to-End Testing

E2E tests validate the entire system works correctly through the API endpoints.

```python
# tests/e2e/test_digital_twin_api.py
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.api.dependencies.services import get_digital_twin_core_service
from app.infrastructure.factories.trinity_stack_factory import TrinityStackFactory

@pytest.fixture
def client():
    # Override services with mock implementations
    app.dependency_overrides[get_digital_twin_core_service] = lambda: TrinityStackFactory.create_digital_twin_core_service()
    return TestClient(app)

def test_create_digital_twin(client):
    patient_id = str(uuid4())
    
    response = client.post(
        f"/api/v1/digital-twin/",
        json={
            "patient_id": patient_id,
            "enable_knowledge_graph": True,
            "enable_belief_network": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "digital_twin_state_id" in data
    assert data["reference_id"] == patient_id

def test_process_multimodal_data(client):
    patient_id = str(uuid4())
    
    # First create a digital twin
    create_response = client.post(
        f"/api/v1/digital-twin/",
        json={
            "patient_id": patient_id,
            "enable_knowledge_graph": True,
            "enable_belief_network": True
        }
    )
    
    assert create_response.status_code == 200
    twin_data = create_response.json()
    
    # Then process multimodal data
    process_response = client.post(
        f"/api/v1/digital-twin/{patient_id}/process-data",
        json={
            "text_data": {
                "clinical_notes": "Patient reports feeling depressed with low energy."
            },
            "physiological_data": {
                "heart_rate": [72, 75, 68, 70, 74],
                "sleep_hours": 6.5
            },
            "behavioral_data": {
                "daily_steps": 4500,
                "social_interactions": "decreased"
            }
        }
    )
    
    assert process_response.status_code == 200
    data = process_response.json()
    assert "digital_twin_state" in data
    assert "clinical_insights" in data["digital_twin_state"]
    assert len(data["digital_twin_state"]["clinical_insights"]) > 0
```

## Test Coverage Requirements

The following test coverage requirements should be met:

1. **Domain Layer**: 90% code coverage
2. **Application Layer**: 85% code coverage
3. **Infrastructure Layer**: 80% code coverage
4. **API Layer**: 85% code coverage

## Test Focus Areas

### 1. Interface Conformance

Ensure all implementations correctly implement their interfaces:

```python
# tests/unit/test_interface_conformance.py
import pytest
import inspect
from typing import Type, get_type_hints

from app.domain.services.refactored.trinity_stack.mental_llama_service import MentalLLaMAService
from app.domain.services.refactored.trinity_stack.pat_service import PATService
from app.domain.services.refactored.trinity_stack.xgboost_service import XGBoostService
from app.infrastructure.services.mock_mentalllama_service import MockMentalLLaMAService
from app.infrastructure.services.mock_pat_service import MockPATService
from app.infrastructure.services.mock_xgboost_service import MockXGBoostService

def verify_interface_implementation(interface_cls, implementation_cls):
    """Verify that a class correctly implements an interface."""
    # Get all abstract methods defined in the interface
    interface_methods = {name for name, method in inspect.getmembers(interface_cls, inspect.isfunction)
                        if getattr(method, '__isabstractmethod__', False)}
    
    # Verify all abstract methods are implemented
    for method_name in interface_methods:
        assert hasattr(implementation_cls, method_name), f"Method {method_name} not implemented"
        
        # Get the method from the interface and implementation
        interface_method = getattr(interface_cls, method_name)
        implementation_method = getattr(implementation_cls, method_name)
        
        # Check signature compatibility
        interface_sig = inspect.signature(interface_method)
        implementation_sig = inspect.signature(implementation_method)
        
        # Check parameters compatibility
        for param_name in interface_sig.parameters:
            if param_name == 'self':
                continue
            assert param_name in implementation_sig.parameters, f"Parameter {param_name} missing in implementation"
            
        # Check return type compatibility
        interface_return = get_type_hints(interface_method).get('return')
        implementation_return = get_type_hints(implementation_method).get('return')
        
        if interface_return and implementation_return:
            assert implementation_return == interface_return or issubclass(implementation_return, interface_return), \
                f"Return type mismatch: {implementation_return} vs {interface_return}"

def test_mentalllama_interface_conformance():
    verify_interface_implementation(MentalLLaMAService, MockMentalLLaMAService)

def test_pat_interface_conformance():
    verify_interface_implementation(PATService, MockPATService)

def test_xgboost_interface_conformance():
    verify_interface_implementation(XGBoostService, MockXGBoostService)
```

### 2. Data Consistency

Ensure data consistency across components:

```python
# tests/integration/test_data_consistency.py
import pytest
from uuid import uuid4

from app.infrastructure.factories.trinity_stack_factory import TrinityStackFactory

@pytest.mark.asyncio
async def test_data_consistency():
    # Create all services
    llama_service = TrinityStackFactory.create_mental_llama_service()
    pat_service = TrinityStackFactory.create_pat_service()
    xgboost_service = TrinityStackFactory.create_xgboost_service()
    dt_service = TrinityStackFactory.create_digital_twin_core_service()
    
    patient_id = uuid4()
    
    # Initialize a digital twin
    twin_state, _, _ = await dt_service.initialize_digital_twin(
        reference_id=patient_id
    )
    
    # Get clinical insights from MentalLLaMA
    llama_insights = await llama_service.analyze_clinical_notes(
        patient_id=patient_id,
        note_text="Patient reports depression with suicidal ideation."
    )
    
    # Use insights to update the digital twin
    updated_state, _ = await dt_service.process_multimodal_data(
        reference_id=patient_id,
        text_data={"clinical_notes": "Patient reports depression with suicidal ideation."}
    )
    
    # Verify insights are preserved
    for llama_insight in llama_insights:
        matching_insights = [i for i in updated_state.clinical_insights 
                            if i.title == llama_insight.title]
        assert len(matching_insights) > 0
    
    # Get predictions from XGBoost using the updated state
    treatment_options = [
        {
            "id": "treatment_1",
            "type": "medication",
            "name": "Sertraline"
        }
    ]
    
    predictions = await xgboost_service.predict_treatment_response(
        patient_id=patient_id,
        digital_twin_state_id=updated_state.state_id,
        treatment_options=treatment_options
    )
    
    # Verify predictions reference the correct state
    assert str(predictions["digital_twin_state_id"]) == str(updated_state.state_id)
```

### 3. Error Handling and Edge Cases

Test error handling and edge cases:

```python
# tests/unit/test_error_handling.py
import pytest
from uuid import uuid4

from app.infrastructure.factories.trinity_stack_factory import TrinityStackFactory

@pytest.mark.asyncio
async def test_empty_data_handling():
    dt_service = TrinityStackFactory.create_digital_twin_core_service()
    patient_id = uuid4()
    
    # Initialize digital twin
    twin_state, _, _ = await dt_service.initialize_digital_twin(
        reference_id=patient_id
    )
    
    # Process empty data
    updated_state, results = await dt_service.process_multimodal_data(
        reference_id=patient_id,
        text_data={},
        physiological_data={},
        behavioral_data={}
    )
    
    # Should handle gracefully without errors
    assert updated_state is not None
    assert updated_state.state_id != twin_state.state_id  # Should be a new state

@pytest.mark.asyncio
async def test_invalid_reference_id():
    dt_service = TrinityStackFactory.create_digital_twin_core_service()
    
    # Try to get a non-existent digital twin
    with pytest.raises(ValueError):
        await dt_service.get_latest_digital_twin_state(uuid4())
        
@pytest.mark.asyncio
async def test_malformed_data_handling():
    llama_service = TrinityStackFactory.create_mental_llama_service()
    patient_id = uuid4()
    
    # Process malformed data
    with pytest.raises(ValueError):
        await llama_service.analyze_clinical_notes(
            patient_id=patient_id,
            note_text=None  # None instead of string
        )
```

## Test Execution Strategy

1. **CI Pipeline Integration**:
   - Run unit tests on every commit
   - Run component tests on every PR
   - Run integration tests on merge to main
   - Run E2E tests on release candidates

2. **Test Environment**:
   - Unit tests: Use mock implementations
   - Component tests: Use mock implementations
   - Integration tests: Use mock implementations
   - E2E tests: Use containerized services (Docker)

3. **Test Data Management**:
   - Use fixtures for deterministic test data
   - Avoid using production data in tests
   - Create synthetic data generators for comprehensive testing

## Conclusion

This testing strategy provides a comprehensive approach to ensuring the Trinity Stack components work correctly both individually and together. By following this strategy, the team can have confidence in the reliability and correctness of the Digital Twin platform.