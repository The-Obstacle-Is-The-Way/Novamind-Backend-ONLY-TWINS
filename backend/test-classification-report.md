# Test Classification Report

## Summary
- Standalone Tests: 24
- VENV Tests: 77
- Integration Tests: 84

Total Tests: 185

## Misclassified Tests

26 tests are in the wrong directory:

### Should be STANDALONE tests:
- app/tests/enhanced/test_neurotransmitter_mapping_integration.py (currently in integration)
   - 
- app/tests/infrastructure/ml/test_digital_twin_integration.py (currently in integration)
   - 
- app/tests/unit/domain/entities/digital_twin/test_patient_integration.py (currently in integration)
   - 

### Should be VENV tests:
- app/tests/integration/test_mentallama_api.py (currently in integration)
   - Uses external service dependencies
   - Uses non-standalone imports: fastapi, app
- app/tests/integration/api/test_patient_api.py (currently in integration)
   - Uses external service dependencies
- app/tests/integration/api/test_actigraphy_api_integration.py (currently in integration)
   - Uses external service dependencies
   - Uses non-standalone imports: fastapi, app
- app/tests/integration/api/test_actigraphy_api.py (currently in integration)
   - Uses external service dependencies
- app/tests/standalone/test_biometric_event_processor.py (currently in standalone)
   - Uses external service dependencies
   - Uses non-standalone imports: app
- app/tests/standalone/test_utils.py (currently in standalone)
   - Uses non-standalone imports: app
- app/tests/standalone/test_mfa_service.py (currently in standalone)
   - Uses external service dependencies
   - Uses non-standalone imports: time, app
- app/tests/standalone/test_patient_api.py (currently in standalone)
   - Uses external service dependencies
- app/tests/standalone/test_patient.py (currently in standalone)
   - Uses non-standalone imports: time, app
- app/tests/standalone/test_debugging.py (currently in standalone)
   - Uses non-standalone imports: sys
- app/tests/standalone/test_appointment.py (currently in standalone)
   - Uses non-standalone imports: app
- app/tests/standalone/test_pat_mock.py (currently in standalone)
   - Uses non-standalone imports: logging, app
- app/tests/standalone/test_provider.py (currently in standalone)
   - Uses non-standalone imports: time, app
- app/tests/standalone/test_phi_sanitizer_fix.py (currently in standalone)
   - Uses non-standalone imports: app
- app/tests/standalone/test_standalone_pat_mock.py (currently in standalone)
   - Uses non-standalone imports: app
- app/tests/standalone/test_phi_sanitizer.py (currently in standalone)
   - Uses external service dependencies
   - Uses non-standalone imports: time, app
- app/tests/standalone/test_standalone_biometric_processor.py (currently in standalone)
   - Uses external service dependencies
- app/tests/api/integration/test_xgboost_integration.py (currently in integration)
   - Uses external service dependencies
   - Uses session-scoped or autouse fixtures
   - Uses non-standalone imports: fastapi, app

### Should be INTEGRATION tests:
- app/tests/venv_only/test_temporal_neurotransmitter_analysis.py (currently in venv)
   - Uses database dependencies
   - Uses non-standalone imports: pandas, numpy
- app/tests/standalone/test_standalone_digital_twin.py (currently in standalone)
   - Uses database dependencies
- app/tests/standalone/test_standalone_phi_sanitizer.py (currently in standalone)
   - Uses database dependencies
   - Uses non-standalone imports: logging
- app/tests/standalone/test_sqlalchemy_repositories.py (currently in standalone)
   - Uses database dependencies
- app/tests/standalone/test_enhanced_log_sanitizer.py (currently in standalone)
   - Uses database dependencies
   - Uses external service dependencies
   - Uses non-standalone imports: logging, app

## Correctly Classified Tests

### STANDALONE tests:
- app/tests/standalone/test_patient_flow.py
- app/tests/standalone/test_create_patient.py
- app/tests/standalone/test_generate_digital_twin.py
- app/tests/standalone/test_standalone_ml_exceptions.py
- app/tests/standalone/test_ml_exceptions.py
- ... and 5 more

### VENV tests:
- app/tests/venv_only/test_sample_venv.py

### INTEGRATION tests:
- app/tests/integration/test_patient_repository_int.py
- app/tests/integration/test_digital_twin_integration_int.py
- app/tests/integration/test_temporal_neurotransmitter_integration.py
- app/tests/integration/test_temporal_wrapper.py
- app/tests/integration/security/test_phi_sanitization_integration.py
- ... and 7 more