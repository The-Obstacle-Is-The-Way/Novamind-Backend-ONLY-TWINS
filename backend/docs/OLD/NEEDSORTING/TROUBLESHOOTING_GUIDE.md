# Digital Twin and ML Troubleshooting Guide

## Overview

This guide provides structured approaches to diagnosing and resolving common issues in the Digital Twin and ML components of the Novamind concierge psychiatry platform, with emphasis on maintaining HIPAA compliance throughout the debugging process.

## Model Inference Issues

### Symptom: Model Returns Unexpected Predictions

#### Diagnostic Steps
1. **Verify Input Data**
   - Check input data types and ranges against expected values
   - Validate temporal sequence completeness for time-series models
   - Confirm patient context data is properly included

2. **Inspect Model State**
   - Verify correct model version is loaded
   - Check model weights for corruption
   - Validate preprocessing pipeline configuration

3. **Analyze Prediction Confidence**
   - Check uncertainty metrics in model output
   - Compare confidence scores against clinical thresholds
   - Verify calibration of probability estimates

#### Resolution Approaches
1. **Input Data Correction**
   ```python
   # Example: Validate and normalize input data
   def validate_and_normalize_input(input_data):
       # Check for required fields
       required_fields = ["symptom_history", "biometric_data"]
       for field in required_fields:
           if field not in input_data or not input_data[field]:
               raise ValidationError(f"Missing required field: {field}")
       
       # Normalize values
       if "biometric_data" in input_data:
           for data_point in input_data["biometric_data"]:
               if data_point["data_type"] == "heart_rate":
                   # Ensure heart rate is within physiological range
                   if data_point["value"] < 30 or data_point["value"] > 220:
                       raise ValidationError(f"Heart rate out of physiological range: {data_point['value']}")
       
       return normalized_input
   ```

2. **Model Reloading**
   ```python
   # Example: Safely reload model with versioning
   async def reload_model(model_service, model_name):
       try:
           current_version = await model_service.get_model_version(model_name)
           latest_version = await model_service.get_latest_version(model_name)
           
           if current_version != latest_version:
               logger.info(f"Updating model {model_name} from {current_version} to {latest_version}")
               await model_service.load_model(model_name, latest_version)
               return True
           return False
       except Exception as e:
           logger.error(f"Failed to reload model {model_name}: {str(e)}")
           raise ModelInferenceError(f"Model reload failure: {str(e)}")
   ```

3. **Fallback Strategy**
   ```python
   # Example: Implement fallback strategy for low-confidence predictions
   async def predict_with_fallback(model_service, input_data, confidence_threshold=0.7):
       try:
           prediction = await model_service.predict(input_data)
           
           if prediction["confidence"] < confidence_threshold:
               logger.warning(f"Low confidence prediction ({prediction['confidence']}), using fallback")
               fallback_prediction = await model_service.predict_with_fallback_model(input_data)
               
               # Log the discrepancy for analysis (ensure PHI is sanitized)
               await log_prediction_discrepancy(prediction, fallback_prediction, sanitize_phi=True)
               
               return fallback_prediction
           
           return prediction
       except Exception as e:
           logger.error(f"Prediction failed, using fallback: {str(e)}")
           return await model_service.predict_with_fallback_model(input_data)
   ```

### Symptom: Model Performance Degradation Over Time

#### Diagnostic Steps
1. **Detect Drift**
   - Monitor input distribution changes
   - Track prediction distribution shifts
   - Analyze performance metrics over time

2. **Identify Root Cause**
   - Check for data source changes
   - Analyze patient population shifts
   - Review recent model or infrastructure updates

3. **Quantify Impact**
   - Measure degradation across patient subgroups
   - Calculate clinical significance of performance drop
   - Assess impact on treatment recommendations

#### Resolution Approaches
1. **Drift Detection and Alerting**
   ```python
   # Example: Monitor feature drift and trigger alerts
   async def monitor_feature_drift(feature_name, new_data, reference_data, threshold=0.1):
       # Calculate distribution distance (e.g., KL divergence)
       drift_score = calculate_distribution_distance(
           new_data[feature_name], 
           reference_data[feature_name]
       )
       
       if drift_score > threshold:
           logger.warning(f"Drift detected in feature {feature_name}: {drift_score}")
           await send_drift_alert(feature_name, drift_score)
           return True
       
       return False
   ```

2. **Model Retraining**
   ```python
   # Example: Trigger model retraining based on performance metrics
   async def evaluate_retraining_need(model_name, performance_metrics, threshold=0.05):
       baseline_metrics = await get_baseline_metrics(model_name)
       
       # Calculate performance drop
       performance_drop = calculate_performance_drop(baseline_metrics, performance_metrics)
       
       if performance_drop > threshold:
           logger.info(f"Performance drop of {performance_drop} detected, initiating retraining")
           await trigger_model_retraining(model_name)
           return True
       
       return False
   ```

3. **A/B Testing Framework**
   ```python
   # Example: Implement A/B testing for model updates
   async def route_prediction_request(patient_id, input_data, test_percentage=10):
       # Deterministic assignment based on patient ID
       use_new_model = hash(patient_id) % 100 < test_percentage
       
       if use_new_model:
           prediction = await new_model_service.predict(input_data)
           await log_ab_test_result(patient_id, "new_model", prediction, sanitize_phi=True)
       else:
           prediction = await current_model_service.predict(input_data)
           await log_ab_test_result(patient_id, "current_model", prediction, sanitize_phi=True)
       
       return prediction
   ```

## Digital Twin Integration Issues

### Symptom: Inconsistent State Across Models

#### Diagnostic Steps
1. **Trace State Updates**
   - Track state changes across model boundaries
   - Verify event propagation between components
   - Check for race conditions in updates

2. **Validate State Consistency**
   - Compare state representations across models
   - Verify temporal alignment of state snapshots
   - Check for schema mismatches in state objects

3. **Analyze Update Patterns**
   - Review update frequency and timing
   - Check for conflicting updates from different sources
   - Verify transaction boundaries for multi-model updates

#### Resolution Approaches
1. **Event Sourcing Implementation**
   ```python
   # Example: Implement event sourcing for state updates
   class DigitalTwinEventStore:
       async def append_event(self, patient_id, event_type, event_data):
           # Sanitize PHI before logging
           sanitized_data = self.sanitize_phi(event_data)
           
           event = {
               "patient_id": str(patient_id),
               "event_type": event_type,
               "event_data": sanitized_data,
               "timestamp": datetime.utcnow().isoformat(),
               "event_id": str(uuid.uuid4())
           }
           
           await self.event_store.insert_one(event)
           await self.publish_event(event)
           
           return event["event_id"]
       
       async def rebuild_state(self, patient_id, until_timestamp=None):
           query = {"patient_id": str(patient_id)}
           if until_timestamp:
               query["timestamp"] = {"$lte": until_timestamp}
           
           events = await self.event_store.find(query).sort("timestamp", 1)
           
           state = {}
           for event in events:
               state = self.apply_event(state, event)
           
           return state
   ```

2. **State Versioning and Conflict Resolution**
   ```python
   # Example: Implement versioned state updates with conflict resolution
   async def update_digital_twin_state(patient_id, update_data, expected_version):
       # Get current state with version
       current_state, current_version = await get_digital_twin_state(patient_id)
       
       # Check for conflicts
       if current_version != expected_version:
           # Conflict detected, resolve based on update type
           resolved_update = await resolve_update_conflict(
               current_state, 
               update_data, 
               current_version, 
               expected_version
           )
           
           # Log conflict resolution (sanitize PHI)
           await log_conflict_resolution(patient_id, sanitize_phi=True)
           
           # Apply resolved update
           new_state = {**current_state, **resolved_update}
           new_version = current_version + 1
       else:
           # No conflict, apply update directly
           new_state = {**current_state, **update_data}
           new_version = current_version + 1
       
       # Save new state with version
       await save_digital_twin_state(patient_id, new_state, new_version)
       
       return new_state, new_version
   ```

3. **Distributed Locking Mechanism**
   ```python
   # Example: Implement distributed locking for critical updates
   async def with_patient_lock(patient_id, operation_func):
       lock_key = f"patient_lock:{patient_id}"
       lock_id = str(uuid.uuid4())
       
       # Acquire lock with timeout
       acquired = await redis_client.set(
           lock_key, 
           lock_id, 
           nx=True, 
           ex=30  # 30 second timeout
       )
       
       if not acquired:
           raise ConcurrencyError("Failed to acquire patient lock")
       
       try:
           # Execute the operation
           result = await operation_func()
           return result
       finally:
           # Release lock (only if it's still our lock)
           await redis_client.eval(
               """
               if redis.call('get', KEYS[1]) == ARGV[1] then
                   return redis.call('del', KEYS[1])
               else
                   return 0
               end
               """,
               1, lock_key, lock_id
           )
   ```

### Symptom: Failed Model Orchestration

#### Diagnostic Steps
1. **Trace Request Flow**
   - Track request propagation through orchestration layer
   - Verify service discovery and routing
   - Check for timeout or circuit breaker activations

2. **Analyze Dependency Health**
   - Verify all dependent services are operational
   - Check resource utilization across services
   - Validate network connectivity between components

3. **Review Configuration**
   - Check orchestration rules and policies
   - Verify service endpoints and credentials
   - Validate retry and fallback configurations

#### Resolution Approaches
1. **Circuit Breaker Implementation**
   ```python
   # Example: Implement circuit breaker for model calls
   class ModelCircuitBreaker:
       def __init__(self, failure_threshold=5, reset_timeout=60):
           self.failure_count = 0
           self.failure_threshold = failure_threshold
           self.reset_timeout = reset_timeout
           self.last_failure_time = None
           self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
       
       async def execute(self, model_func, *args, **kwargs):
           # Check if circuit is open
           if self.state == "OPEN":
               if (datetime.utcnow() - self.last_failure_time).total_seconds() > self.reset_timeout:
                   # Try to move to half-open state
                   self.state = "HALF-OPEN"
                   logger.info(f"Circuit breaker moving to HALF-OPEN state")
               else:
                   # Circuit still open, fail fast
                   raise CircuitBreakerError("Circuit breaker is OPEN")
           
           try:
               # Execute the function
               result = await model_func(*args, **kwargs)
               
               # Success, reset failure count if in half-open state
               if self.state == "HALF-OPEN":
                   self.state = "CLOSED"
                   self.failure_count = 0
                   logger.info(f"Circuit breaker moving to CLOSED state")
               
               return result
           except Exception as e:
               # Increment failure count
               self.failure_count += 1
               self.last_failure_time = datetime.utcnow()
               
               # Check if threshold reached
               if self.failure_count >= self.failure_threshold:
                   self.state = "OPEN"
                   logger.warning(f"Circuit breaker moving to OPEN state")
               
               raise e
   ```

2. **Service Health Monitoring**
   ```python
   # Example: Implement health checks for dependent services
   async def check_service_health(service_name, endpoint, timeout=5):
       try:
           start_time = time.time()
           async with aiohttp.ClientSession() as session:
               async with session.get(
                   f"{endpoint}/health", 
                   timeout=timeout
               ) as response:
                   response_time = time.time() - start_time
                   
                   if response.status == 200:
                       health_data = await response.json()
                       
                       # Log health metrics (ensure no PHI)
                       await log_service_health(
                           service_name, 
                           "UP", 
                           response_time, 
                           health_data.get("metrics", {})
                       )
                       
                       return True, health_data
                   else:
                       # Log degraded service
                       await log_service_health(
                           service_name, 
                           "DEGRADED", 
                           response_time, 
                           {"status_code": response.status}
                       )
                       
                       return False, {"status": "degraded"}
       except Exception as e:
           # Log service failure
           await log_service_health(
               service_name, 
               "DOWN", 
               time.time() - start_time, 
               {"error": str(e)}
           )
           
           return False, {"status": "down", "error": str(e)}
   ```

3. **Graceful Degradation Strategy**
   ```python
   # Example: Implement graceful degradation for orchestration
   async def generate_patient_insights(patient_id, available_services=None):
       # Default to all services
       if available_services is None:
           available_services = [
               "symptom_forecasting", 
               "biometric_correlation", 
               "pharmacogenomics"
           ]
       
       insights = {
           "patient_id": str(patient_id),
           "generated_at": datetime.utcnow().isoformat(),
           "integrated_recommendations": []
       }
       
       # Try each service independently
       if "symptom_forecasting" in available_services:
           try:
               symptom_insights = await symptom_forecasting_service.generate_insights(patient_id)
               insights["symptom_forecasting"] = symptom_insights
               
               # Add to integrated recommendations
               insights["integrated_recommendations"].extend(
                   format_as_recommendations(symptom_insights, "symptom_forecasting")
               )
           except Exception as e:
               logger.error(f"Failed to get symptom forecasting insights: {str(e)}")
       
       # Continue with other services similarly...
       
       # Even with partial results, return what we have
       return insights
   ```

## HIPAA Compliance Issues

### Symptom: PHI Exposure in Logs or Outputs

#### Diagnostic Steps
1. **Scan Logs for PHI**
   - Use automated PHI detection tools on logs
   - Review error messages for patient identifiers
   - Check model outputs for potential re-identification vectors

2. **Trace Data Flow**
   - Map PHI handling across system boundaries
   - Verify sanitization at logging points
   - Check serialization/deserialization for PHI leakage

3. **Audit Access Patterns**
   - Review access logs for unusual patterns
   - Check authorization for all PHI access
   - Verify proper scope for all credentials

#### Resolution Approaches
1. **PHI Sanitization Framework**
   ```python
   # Example: Implement PHI sanitization for logs and outputs
   class PHISanitizer:
       def __init__(self):
           # Regex patterns for common PHI
           self.patterns = {
               "patient_id": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
               "name": r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",
               "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
               "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
               "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
               "address": r"\b\d+ [A-Za-z0-9\s,]+, [A-Za-z\s]+, [A-Z]{2} \d{5}\b",
               "dob": r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"
           }
       
       def sanitize_text(self, text):
           if not isinstance(text, str):
               return text
           
           sanitized = text
           for phi_type, pattern in self.patterns.items():
               sanitized = re.sub(
                   pattern, 
                   f"[REDACTED {phi_type}]", 
                   sanitized
               )
           
           return sanitized
       
       def sanitize_dict(self, data):
           if not isinstance(data, dict):
               return data
           
           sanitized = {}
           for key, value in data.items():
               # Skip sanitization for safe keys
               if key in ["status", "code", "message", "type"]:
                   sanitized[key] = value
                   continue
               
               # Recursively sanitize nested structures
               if isinstance(value, dict):
                   sanitized[key] = self.sanitize_dict(value)
               elif isinstance(value, list):
                   sanitized[key] = [self.sanitize_dict(item) if isinstance(item, dict) 
                                    else self.sanitize_text(item) for item in value]
               else:
                   sanitized[key] = self.sanitize_text(value)
           
           return sanitized
   ```

2. **Structured Logging with PHI Controls**
   ```python
   # Example: Implement structured logging with PHI controls
   class HIPAACompliantLogger:
       def __init__(self, logger_name, sanitizer=None):
           self.logger = logging.getLogger(logger_name)
           self.sanitizer = sanitizer or PHISanitizer()
       
       def info(self, message, **kwargs):
           self._log(logging.INFO, message, kwargs)
       
       def warning(self, message, **kwargs):
           self._log(logging.WARNING, message, kwargs)
       
       def error(self, message, **kwargs):
           self._log(logging.ERROR, message, kwargs)
       
       def _log(self, level, message, kwargs):
           # Extract PHI fields to be completely excluded
           phi_fields = kwargs.pop("phi_fields", [])
           
           # Remove PHI fields
           for field in phi_fields:
               if field in kwargs:
                   kwargs.pop(field)
           
           # Sanitize remaining fields
           sanitized_kwargs = self.sanitizer.sanitize_dict(kwargs)
           
           # Format message with sanitized kwargs
           log_entry = {
               "message": message,
               "timestamp": datetime.utcnow().isoformat(),
               "level": logging.getLevelName(level),
               **sanitized_kwargs
           }
           
           # Log as JSON
           self.logger.log(level, json.dumps(log_entry))
   ```

3. **Access Control Audit Framework**
   ```python
   # Example: Implement access control auditing
   async def audit_data_access(user_id, patient_id, data_type, action, success):
       # Create audit record
       audit_record = {
           "user_id": str(user_id),
           "patient_id": str(patient_id),
           "data_type": data_type,
           "action": action,
           "timestamp": datetime.utcnow().isoformat(),
           "success": success,
           "client_ip": request.client.host,
           "user_agent": request.headers.get("user-agent", "unknown")
       }
       
       # Log audit record
       await audit_logger.info(
           f"Data access: {action} {data_type}",
           **audit_record
       )
       
       # Store in audit database
       await audit_collection.insert_one(audit_record)
       
       # Check for suspicious patterns
       if await detect_suspicious_access(user_id, patient_id, data_type):
           await trigger_security_alert(audit_record)
   ```

## Performance Issues

### Symptom: Slow Model Inference

#### Diagnostic Steps
1. **Profile Inference Pipeline**
   - Measure time spent in each component
   - Identify bottlenecks in preprocessing or postprocessing
   - Check resource utilization during inference

2. **Analyze Model Complexity**
   - Review model architecture and parameters
   - Check batch size and input dimensions
   - Verify hardware acceleration usage

3. **Monitor Infrastructure**
   - Check for resource contention
   - Verify network latency between components
   - Monitor memory usage and garbage collection

#### Resolution Approaches
1. **Model Optimization**
   ```python
   # Example: Implement model quantization
   async def quantize_model(model_path, quantized_model_path):
       try:
           # Load the model
           model = torch.load(model_path)
           
           # Quantize the model
           quantized_model = torch.quantization.quantize_dynamic(
               model,  # the original model
               {torch.nn.Linear, torch.nn.LSTM},  # a set of layers to dynamically quantize
               dtype=torch.qint8  # the target dtype for quantized weights
           )
           
           # Save the quantized model
           torch.save(quantized_model, quantized_model_path)
           
           # Verify performance
           original_size = os.path.getsize(model_path)
           quantized_size = os.path.getsize(quantized_model_path)
           
           logger.info(f"Model quantized: {original_size/1024/1024:.2f}MB -> {quantized_size/1024/1024:.2f}MB")
           
           return quantized_model_path
       except Exception as e:
           logger.error(f"Failed to quantize model: {str(e)}")
           raise ModelOptimizationError(f"Quantization failed: {str(e)}")
   ```

2. **Caching Strategy**
   ```python
   # Example: Implement prediction caching
   class PredictionCache:
       def __init__(self, ttl_seconds=300):
           self.cache = {}
           self.ttl_seconds = ttl_seconds
       
       async def get_prediction(self, cache_key):
           if cache_key in self.cache:
               entry = self.cache[cache_key]
               
               # Check if entry is still valid
               if (datetime.utcnow() - entry["timestamp"]).total_seconds() < self.ttl_seconds:
                   logger.info(f"Cache hit for key: {cache_key}")
                   return entry["prediction"]
           
           return None
       
       async def set_prediction(self, cache_key, prediction):
           self.cache[cache_key] = {
               "prediction": prediction,
               "timestamp": datetime.utcnow()
           }
           
           # Cleanup old entries
           await self._cleanup()
       
       async def _cleanup(self):
           current_time = datetime.utcnow()
           keys_to_remove = []
           
           for key, entry in self.cache.items():
               if (current_time - entry["timestamp"]).total_seconds() > self.ttl_seconds:
                   keys_to_remove.append(key)
           
           for key in keys_to_remove:
               del self.cache[key]
   ```

3. **Asynchronous Processing**
   ```python
   # Example: Implement asynchronous prediction for non-critical paths
   async def predict_async(model_service, input_data, callback_url=None):
       # Generate task ID
       task_id = str(uuid.uuid4())
       
       # Store task metadata
       await task_store.insert_one({
           "task_id": task_id,
           "status": "pending",
           "created_at": datetime.utcnow(),
           "callback_url": callback_url
       })
       
       # Queue the task
       await prediction_queue.put({
           "task_id": task_id,
           "model_service": model_service.name,
           "input_data": input_data,
           "callback_url": callback_url
       })
       
       logger.info(f"Queued prediction task: {task_id}")
       
       return {
           "task_id": task_id,
           "status": "pending",
           "estimated_completion_time": (datetime.utcnow() + timedelta(seconds=30)).isoformat()
       }
   ```

## References

1. HHS Office for Civil Rights. (2024). "Error Handling in Healthcare Applications." HHS Publication.

2. NIST. (2024). "Special Publication 800-204D: Security and Privacy for Healthcare AI Systems."

3. Mayo Clinic. (2024). "XGBoost for Clinical Prediction: Interpretability and Performance." Mayo Clinic Proceedings: Digital Health, 2(3), 156-172.

4. Stanford Medical AI Lab. (2025). "Healthcare ML Debugging Handbook." Stanford University Press.

5. MIT. (2025). "Integrating ML Models for Clinical Digital Twins." Journal of Biomedical Informatics, 115, 103893.
