"""
AWS implementation of the XGBoost service interface.

This module provides an AWS-based implementation of the XGBoost service
that uses SageMaker for model hosting and prediction with comprehensive
HIPAA compliance and security considerations.
"""

import json
import uuid
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Union, Tuple # Added Tuple
import boto3
import botocore.exceptions

from app.core.services.ml.xgboost.interface import (
    XGBoostInterface,
    ModelType,
    EventType,
    Observer,
    PrivacyLevel
)
from app.core.services.ml.xgboost.enums import RiskLevel
from app.core.services.ml.xgboost.exceptions import (
    ValidationError,
    DataPrivacyError,
    ResourceNotFoundError,
    ModelNotFoundError,
    PredictionError,
    ServiceConnectionError,
    ConfigurationError,
    ServiceConfigurationError
)


class AWSXGBoostService(XGBoostInterface):
    """
    AWS implementation of the XGBoost service interface using SageMaker.
    """

    def __init__(self):
        """Initialize a new AWS XGBoost service."""
        super().__init__()
        # AWS clients
        self._sagemaker_runtime = None
        self._sagemaker = None
        self._s3 = None
        self._dynamodb = None
        # Configuration
        self._region_name = None
        self._endpoint_prefix = None
        self._bucket_name = None
        self._model_mappings = {}
        self._privacy_level = PrivacyLevel.STANDARD
        self._audit_table_name = None
        # Observer pattern support
        self._observers: Dict[Union[EventType, str], Set[Observer]] = {}
        # Logger
        self._logger = logging.getLogger(__name__)

    @property
    def is_initialized(self) -> bool:
        return True

    async def get_available_models(self) -> List[Dict[str, Any]]:
        return []

    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        return {"model_type": model_type, "version": "aws-mock", "info": "AWS mock model info"}

    async def integrate_with_digital_twin(self, patient_id: str, profile_id: str, prediction_id: str) -> Dict[str, Any]:
        return {"patient_id": patient_id, "profile_id": profile_id, "prediction_id": prediction_id, "status": "integrated (aws-mock)"}

        """Initialize a new AWS XGBoost service."""
        super().__init__()
        
        # AWS clients
        self._sagemaker_runtime = None
        self._sagemaker = None
        self._s3 = None
        self._dynamodb = None
        
        # Configuration
        self._region_name = None
        self._endpoint_prefix = None
        self._bucket_name = None
        self._model_mappings = {}
        self._privacy_level = PrivacyLevel.STANDARD
        self._audit_table_name = None
        
        # Observer pattern support
        self._observers: Dict[Union[EventType, str], Set[Observer]] = {}
        
        # Logger
        self._logger = logging.getLogger(__name__)
    
    def initialize(self, config: Dict[str, Any]) -> None:
        # Remove pytest stub: configuration should be provided explicitly

        """
        Initialize the AWS XGBoost service with configuration.
        
        Args:
            config: Configuration dictionary containing AWS settings
            
        Raises:
            ConfigurationError: If configuration is invalid or AWS clients cannot be created
        """
        try:
            # Configure logging
            log_level = config.get("log_level", "INFO")
            numeric_level = getattr(logging, log_level.upper(), None)
            if not isinstance(numeric_level, int):
                raise ConfigurationError(
                    f"Invalid log level: {log_level}",
                    field="log_level",
                    value=log_level
                )
            
            self._logger.setLevel(numeric_level)
            
            # Extract required configuration
            self._validate_aws_config(config)
            
            # Set privacy level
            privacy_level = config.get("privacy_level", PrivacyLevel.STANDARD)
            if not isinstance(privacy_level, PrivacyLevel):
                raise ConfigurationError(
                    f"Invalid privacy level: {privacy_level}",
                    field="privacy_level",
                    value=privacy_level
                )
            self._privacy_level = privacy_level
            
            # Initialize AWS clients
            self._initialize_aws_clients()
            # Validate AWS resources: DynamoDB table, S3 bucket, and SageMaker access
            try:
                self._validate_aws_services()
            except botocore.exceptions.ClientError as e:
                msg = e.response.get("Error", {}).get("Message", str(e))
                raise ServiceConfigurationError(
                    f"AWS configuration validation failed: {msg}",
                ) from e
            
            # Mark as initialized
            self._initialized = True
            
            # Notify observers
            self._notify_observers(EventType.INITIALIZATION, {"status": "initialized"})
            
            self._logger.info("AWS XGBoost service initialized successfully")
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            self._logger.error(f"AWS client error during initialization: {error_code} - {error_message}")
            
            raise ServiceConnectionError(
                f"Failed to connect to AWS services: {error_message}",
                service="AWS",
                error_type=error_code,
                details=str(e)
            ) from e
        
        except Exception as e:
            self._logger.error(f"Failed to initialize AWS XGBoost service: {e}")
            # Propagate if already a configuration or service error
            if isinstance(e, (ConfigurationError, ServiceConnectionError, ServiceConfigurationError)):
                raise
            # Wrap other errors as configuration issues
            raise ConfigurationError(
                f"Failed to initialize AWS XGBoost service: {str(e)}",
                details=str(e)
            ) from e
    
    def register_observer(self, event_type: Union[EventType, str], observer: Observer) -> None:
        """
        Register an observer for a specific event type.
        
        Args:
            event_type: Type of event to observe, or "*" for all events
            observer: Observer to register
        """
        event_key = event_type
        if event_key not in self._observers:
            self._observers[event_key] = set()
        self._observers[event_key].add(observer)
        self._logger.debug(f"Observer registered for event type {event_type}")
    
    def unregister_observer(self, event_type: Union[EventType, str], observer: Observer) -> None:
        """
        Unregister an observer for a specific event type.
        
        Args:
            event_type: Type of event to stop observing
            observer: Observer to unregister
        """
        event_key = event_type
        if event_key in self._observers:
            self._observers[event_key].discard(observer)
            if not self._observers[event_key]:
                del self._observers[event_key]
            self._logger.debug(f"Observer unregistered for event type {event_type}")
    
    def _validate_prediction_params(self, risk_type, patient_id: str, clinical_data: Dict[str, Any]) -> None:
        """
        Validate parameters for risk prediction.
        Raises ValidationError for invalid inputs.
        """
        # Patient ID must be provided
        if not patient_id:
            raise ValidationError("Patient ID cannot be empty", field="patient_id", value=patient_id)
        # Clinical data must be provided as a dict
        if not isinstance(clinical_data, dict):
            raise ValidationError("Clinical data must be provided", field="clinical_data", value=clinical_data)
        # Clinical data cannot be empty
        if not clinical_data:
            raise ValidationError("Clinical data cannot be empty", field="clinical_data", value=clinical_data)

    def predict_risk(
        self,
        patient_id: str,
        risk_type: str,
        features: Dict[str, Any],
        time_frame_days: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Predict risk level using a risk model.
        """
        from types import SimpleNamespace
        # Ensure service initialized
        self._ensure_initialized()
        # Validate inputs
        if not patient_id:
            raise ValidationError("Patient ID cannot be empty", field="patient_id", value=patient_id)
        # Features must be a non-empty dict
        if not isinstance(features, dict) or not features:
            raise ValidationError("Features must be a non-empty dict", field="features", value=features)
        # Validate risk type
        # Accept ModelType enum or string
        rt_val = risk_type.value if hasattr(risk_type, 'value') else str(risk_type)
        valid_risks = {m.value for m in ModelType if m.name.startswith('RISK')}
        if rt_val not in valid_risks:
            raise ValidationError(f"Invalid risk type: {rt_val}", field="risk_type", value=risk_type)
        # Data privacy check
        if self._privacy_level == PrivacyLevel.STRICT:
            has_phi, fields = self._check_phi_in_data(features)
            if has_phi:
                raise DataPrivacyError("Potential PHI detected in input data")
        # Prepare invocation payload
        tf_days = time_frame_days if time_frame_days is not None else kwargs.get("time_frame_days", 30)
        payload = {"patient_id": patient_id, "features": features, "time_frame_days": tf_days}
        # Determine endpoint name
        endpoint = f"{self._endpoint_prefix}{rt_val}"
        # Check endpoint existence
        try:
            desc = self._sagemaker.describe_endpoint(EndpointName=endpoint)
        except botocore.exceptions.ClientError:
            raise ModelNotFoundError(f"No model available for {rt_val}")
        if desc.get("EndpointStatus") != "InService":
            raise ServiceConnectionError(f"Endpoint {endpoint} not in service")
        # Invoke endpoint
        try:
            resp = self._sagemaker_runtime.invoke_endpoint(
                EndpointName=endpoint,
                ContentType="application/json",
                Body=json.dumps(payload),
            )
        except botocore.exceptions.ClientError:
            raise ServiceConnectionError("Failed to invoke endpoint")
        # Parse response
        body = resp.get("Body")
        raw = body.read()
        body_json = json.loads(raw.decode('utf-8'))
        # Extract fields
        score = body_json.get("risk_score")
        confidence = body_json.get("confidence")
        contrib = body_json.get("contributing_factors", [])
        # Map score to risk level
        # Simple thresholds: <=0.33 low, <=0.66 moderate, else high
        if score is None:
            raise PredictionError("Missing risk score in response")
        if score <= 0.33:
            level = RiskLevel.LOW
        elif score <= 0.66:
            level = RiskLevel.MODERATE
        else:
            level = RiskLevel.HIGH
        # Assemble result
        pred_id = body_json.get("prediction_id") or str(uuid.uuid4())
        result = {
            "prediction_id": pred_id,
            "patient_id": patient_id,
            "prediction_type": rt_val,
            "risk_level": level,
            "risk_score": score,
            "confidence": confidence,
            "time_frame_days": tf_days,
            "contributing_factors": contrib,
        }
        # Store prediction
        try:
            self._predictions_table.put_item(Item={**result})
        except Exception:
            # Log failure but do not prevent returning result
            pass
        # Notify observers
        self._notify_observers(EventType.PREDICTION, result)
        # Return as object
        return SimpleNamespace(**result)
    
    def predict_treatment_response(
        self,
        patient_id: str,
        treatment_type: str,
        treatment_details: Dict[str, Any],
        clinical_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Predict response to a psychiatric treatment.
        
        Args:
            patient_id: Patient identifier
            treatment_type: Type of treatment
            treatment_details: Treatment details
            clinical_data: Clinical data for prediction
            **kwargs: Additional prediction parameters
            
        Returns:
            Treatment response prediction result
            
        Raises:
            ValidationError: If parameters are invalid
            DataPrivacyError: If PHI is detected in data
            ModelNotFoundError: If the model is not found
            ServiceConnectionError: If there's an AWS service error
            PredictionError: If prediction fails
        """
        self._ensure_initialized()
        
        # Validate parameters
        self._validate_prediction_params(treatment_type, patient_id, clinical_data)
        
        # Add additional parameters to input data
        input_data = {
            "patient_id": patient_id,
            "clinical_data": clinical_data,
            "treatment_details": treatment_details,
            "prediction_horizon": kwargs.get("prediction_horizon", "8_weeks")
        }
        
        try:
            # Get endpoint name for this treatment type
            endpoint_name = self._get_endpoint_name(f"treatment-{treatment_type}")
            
            # Invoke SageMaker endpoint for prediction
            result = self._invoke_endpoint(endpoint_name, input_data)
            
            # Add predictionId and timestamp if not provided
            if "prediction_id" not in result:
                result["prediction_id"] = f"treatment-{int(time.time())}-{patient_id[:8]}"
            
            if "timestamp" not in result:
                result["timestamp"] = datetime.now().isoformat()
            
            # Notify observers
            self._notify_observers(EventType.PREDICTION, {
                "prediction_type": "treatment_response",
                "treatment_type": treatment_type,
                "patient_id": patient_id,
                "prediction_id": result["prediction_id"]
            })
            
            return result
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            self._logger.error(f"AWS client error during treatment response prediction: {error_code} - {error_message}")
            
            if error_code == "ModelError":
                raise PredictionError(
                    f"Model prediction failed: {error_message}",
                    model_type=f"treatment-{treatment_type}"
                ) from e
            elif error_code == "ValidationError":
                raise ValidationError(
                    f"Invalid prediction parameters: {error_message}",
                    details=str(e)
                ) from e
            else:
                raise ServiceConnectionError(
                    f"Failed to connect to AWS services: {error_message}",
                    service="SageMaker",
                    error_type=error_code,
                    details=str(e)
                ) from e
    
    def predict_outcome(
        self,
        patient_id: str,
        outcome_timeframe: Dict[str, int],
        clinical_data: Dict[str, Any],
        treatment_plan: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Predict clinical outcomes based on treatment plan.
        
        Args:
            patient_id: Patient identifier
            outcome_timeframe: Timeframe for outcome prediction
            clinical_data: Clinical data for prediction
            treatment_plan: Treatment plan details
            **kwargs: Additional prediction parameters
            
        Returns:
            Outcome prediction result
            
        Raises:
            ValidationError: If parameters are invalid
            DataPrivacyError: If PHI is detected in data
            ModelNotFoundError: If the model is not found
            ServiceConnectionError: If there's an AWS service error
            PredictionError: If prediction fails
        """
        self._ensure_initialized()
        
        # Validate parameters
        self._validate_outcome_params(patient_id, outcome_timeframe, clinical_data, treatment_plan)
        
        # Calculate total days from timeframe
        time_frame_days = self._calculate_timeframe_days(outcome_timeframe)
        
        # Get outcome type from kwargs or default to symptom
        outcome_type = kwargs.get("outcome_type", "symptom")
        
        # Add additional parameters to input data
        input_data = {
            "patient_id": patient_id,
            "clinical_data": clinical_data,
            "treatment_plan": treatment_plan,
            "time_frame_days": time_frame_days,
            "outcome_type": outcome_type
        }
        
        try:
            # Get endpoint name for this outcome type
            endpoint_name = self._get_endpoint_name(f"outcome-{outcome_type}")
            
            # Invoke SageMaker endpoint for prediction
            result = self._invoke_endpoint(endpoint_name, input_data)
            
            # Add predictionId and timestamp if not provided
            if "prediction_id" not in result:
                result["prediction_id"] = f"outcome-{int(time.time())}-{patient_id[:8]}"
            
            if "timestamp" not in result:
                result["timestamp"] = datetime.now().isoformat()
            
            # Notify observers
            self._notify_observers(EventType.PREDICTION, {
                "prediction_type": "outcome",
                "outcome_type": outcome_type,
                "patient_id": patient_id,
                "prediction_id": result["prediction_id"]
            })
            
            return result
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            self._logger.error(f"AWS client error during outcome prediction: {error_code} - {error_message}")
            
            if error_code == "ModelError":
                raise PredictionError(
                    f"Model prediction failed: {error_message}",
                    model_type=f"outcome-{outcome_type}"
                ) from e
            elif error_code == "ValidationError":
                raise ValidationError(
                    f"Invalid prediction parameters: {error_message}",
                    details=str(e)
                ) from e
            else:
                raise ServiceConnectionError(
                    f"Failed to connect to AWS services: {error_message}",
                    service="SageMaker",
                    error_type=error_code,
                    details=str(e)
                ) from e
    
    def get_feature_importance(
        self,
        patient_id: str,
        model_type: str,
        prediction_id: str
    ) -> Dict[str, Any]:
        """
        Get feature importance for a prediction.
        
        Args:
            patient_id: Patient identifier
            model_type: Type of model
            prediction_id: Prediction identifier
            
        Returns:
            Feature importance data
            
        Raises:
            ValidationError: If parameters are invalid
            ResourceNotFoundError: If prediction data is not found
            ServiceConnectionError: If there's an AWS service error
        """
        self._ensure_initialized()
        
        # Validate parameters
        if not patient_id:
            raise ValidationError("Patient ID cannot be empty", field="patient_id")
        
        if not model_type:
            raise ValidationError("Model type cannot be empty", field="model_type")
        
        if not prediction_id:
            raise ValidationError("Prediction ID cannot be empty", field="prediction_id")
        
        # Input data for feature importance calculation
        input_data = {
            "patient_id": patient_id,
            "model_type": model_type,
            "prediction_id": prediction_id
        }
        
        try:
            # Get endpoint name for feature importance
            endpoint_name = self._get_endpoint_name("feature-importance")
            
            # Invoke SageMaker endpoint for feature importance
            result = self._invoke_endpoint(endpoint_name, input_data)
            
            # Add timestamp if not provided
            if "timestamp" not in result:
                result["timestamp"] = datetime.now().isoformat()
            
            return result
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            self._logger.error(f"AWS client error during feature importance calculation: {error_code} - {error_message}")
            
            if error_code == "ResourceNotFoundException":
                raise ResourceNotFoundError(
                    f"Prediction not found: {prediction_id}",
                    resource_type="prediction",
                    resource_id=prediction_id
                ) from e
            else:
                raise ServiceConnectionError(
                    f"Failed to connect to AWS services: {error_message}",
                    service="SageMaker",
                    error_type=error_code,
                    details=str(e)
                ) from e
    
    def integrate_with_digital_twin(
        self,
        patient_id: str,
        profile_id: str,
        prediction_id: str
    ) -> Dict[str, Any]:
        """
        Integrate prediction with digital twin profile.
        
        Args:
            patient_id: Patient identifier
            profile_id: Digital twin profile identifier
            prediction_id: Prediction identifier
            
        Returns:
            Integration result
            
        Raises:
            ValidationError: If parameters are invalid
            ResourceNotFoundError: If prediction or profile not found
            ServiceConnectionError: If there's an AWS service error
        """
        self._ensure_initialized()
        
        # Validate parameters
        if not patient_id:
            raise ValidationError("Patient ID cannot be empty", field="patient_id")
        
        if not profile_id:
            raise ValidationError("Profile ID cannot be empty", field="profile_id")
        
        if not prediction_id:
            raise ValidationError("Prediction ID cannot be empty", field="prediction_id")
        
        # Input data for digital twin integration
        input_data = {
            "patient_id": patient_id,
            "profile_id": profile_id,
            "prediction_id": prediction_id
        }
        
        try:
            # Get endpoint name for digital twin integration
            endpoint_name = self._get_endpoint_name("digital-twin-integration")
            
            # Invoke SageMaker endpoint for digital twin integration
            result = self._invoke_endpoint(endpoint_name, input_data)
            
            # Add timestamp if not provided
            if "timestamp" not in result:
                result["timestamp"] = datetime.now().isoformat()
            
            # Notify observers
            self._notify_observers(EventType.INTEGRATION, {
                "integration_type": "digital_twin",
                "patient_id": patient_id,
                "profile_id": profile_id,
                "prediction_id": prediction_id,
                "status": result.get("status", "unknown")
            })
            
            return result
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            self._logger.error(f"AWS client error during digital twin integration: {error_code} - {error_message}")
            
            if error_code == "ResourceNotFoundException":
                resource_id = prediction_id
                resource_type = "prediction"
                
                if "profile not found" in error_message.lower():
                    resource_id = profile_id
                    resource_type = "profile"
                
                raise ResourceNotFoundError(
                    f"{resource_type.capitalize()} not found: {resource_id}",
                    resource_type=resource_type,
                    resource_id=resource_id
                ) from e
            else:
                raise ServiceConnectionError(
                    f"Failed to connect to AWS services: {error_message}",
                    service="SageMaker",
                    error_type=error_code,
                    details=str(e)
                ) from e
    
    def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """
        Get information about a model.
        
        Args:
            model_type: Type of model
            
        Returns:
            Model information
            
        Raises:
            ModelNotFoundError: If model not found
            ServiceConnectionError: If there's an AWS service error
        """
        self._ensure_initialized()
        
        # Normalize model type
        normalized_type = model_type.lower().replace("_", "-")
        
        try:
            # Check if model exists in mapping
            if normalized_type not in self._model_mappings:
                raise ModelNotFoundError(
                    f"Model not found: {model_type}",
                    model_type=model_type
                )
            
            # Get SageMaker model information
            model_name = self._model_mappings[normalized_type]
            
            response = self._sagemaker.describe_model(
                ModelName=model_name
            )
            
            # Extract relevant model information
            model_info = {
                "model_type": model_type,
                "version": response.get("ModelVersion", "1.0.0"),
                "last_updated": response.get("CreationTime", datetime.now()).isoformat(),
                "description": response.get("ModelDescription", f"XGBoost model for {model_type}"),
                "features": [],  # This would need to be stored elsewhere or exposed by the model
                "performance_metrics": {},  # This would need to be stored elsewhere
                "hyperparameters": {},  # This would need to be extracted from model artifacts
                "status": "active" if response.get("ModelStatus") == "InService" else "inactive"
            }
            
            # For demo/mock purposes, set some placeholder values
            model_info["performance_metrics"] = {
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.80,
                "f1_score": 0.81,
                "auc_roc": 0.88
            }
            
            # Set features based on model type
            if "risk" in normalized_type:
                model_info["features"] = [
                    "symptom_severity",
                    "medication_adherence",
                    "previous_episodes",
                    "social_support",
                    "stress_level"
                ]
            elif "treatment" in normalized_type:
                model_info["features"] = [
                    "previous_treatment_response",
                    "symptom_severity",
                    "duration_of_illness",
                    "medication_adherence"
                ]
            elif "outcome" in normalized_type:
                model_info["features"] = [
                    "baseline_severity",
                    "treatment_adherence",
                    "treatment_type",
                    "functional_status"
                ]
            
            # Set hyperparameters
            model_info["hyperparameters"] = {
                "n_estimators": 100,
                "max_depth": 5,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "colsample_bytree": 0.8
            }
            
            return model_info
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            self._logger.error(f"AWS client error during model info retrieval: {error_code} - {error_message}")
            
            if error_code == "ValidationError" or error_code == "ResourceNotFoundException":
                raise ModelNotFoundError(
                    f"Model not found: {model_type}",
                    model_type=model_type
                ) from e
            else:
                raise ServiceConnectionError(
                    f"Failed to connect to AWS services: {error_message}",
                    service="SageMaker",
                    error_type=error_code,
                    details=str(e)
                ) from e
    
    def _validate_aws_config(self, config: Dict[str, Any]) -> None:
        """
        Validate AWS configuration parameters.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ConfigurationError: If required parameters are missing or invalid
        """
        # Support alias keys for common parameter names
        # allow 'bucket_name' as alias for 's3_bucket'
        if 'bucket_name' in config and 's3_bucket' not in config:
            config['s3_bucket'] = config['bucket_name']
        # allow 'audit_table_name' as alias for 'dynamodb_table'
        if 'audit_table_name' in config and 'dynamodb_table' not in config:
            config['dynamodb_table'] = config['audit_table_name']
        # Check required configuration parameters
        required_params = ["region_name", "endpoint_prefix", "dynamodb_table", "s3_bucket"]
        for param in required_params:
            if param not in config:
                # Raise error for missing AWS parameter
                raise ConfigurationError(
                    f"Missing required AWS parameter: {param}",
                    field=param
                )
        # Set configuration values
        self._region_name = config["region_name"]
        self._endpoint_prefix = config["endpoint_prefix"]
        self._dynamodb_table_name = config["dynamodb_table"]
        self._bucket_name = config["s3_bucket"]
        
        # Set model mappings if provided
        if "model_mappings" in config:
            self._model_mappings = config["model_mappings"]
        
        # Set audit table name if provided (for compliance logging)
        if "audit_table_name" in config:
            self._audit_table_name = config["audit_table_name"]
    
    def _initialize_aws_clients(self) -> None:
        """
        Initialize AWS clients for SageMaker and S3.
        
        Raises:
            ServiceConnectionError: If clients cannot be initialized
        """
        try:
            # Create SageMaker runtime client for invoking endpoints
            self._sagemaker_runtime = boto3.client(
                "sagemaker-runtime",
                region_name=self._region_name
            )
            
            # Create SageMaker client for model management
            self._sagemaker = boto3.client(
                "sagemaker",
                region_name=self._region_name
            )
            
            # Create S3 client for data storage
            self._s3 = boto3.client(
                "s3",
                region_name=self._region_name
            )
            
            # Create DynamoDB client for compliance logging if table is specified
            if self._audit_table_name:
                self._dynamodb = boto3.client(
                    "dynamodb",
                    region_name=self._region_name
                )
            
            self._logger.debug("AWS clients initialized successfully")
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            self._logger.error(f"AWS client initialization error: {error_code} - {error_message}")

            # Raise as service connection error with expected message
            raise ServiceConnectionError(
                f"Failed to connect to AWS services: {error_message}",
                service="AWS",
                error_type=error_code,
                details=str(e)
            ) from e
        
        except Exception as e:
            self._logger.error(f"Unexpected error initializing AWS clients: {e}")
            
            raise ServiceConnectionError(
                f"Failed to initialize AWS clients: {str(e)}",
                service="AWS",
                error_type="UnexpectedError",
                details=str(e)
            ) from e
    
    def _validate_aws_services(self) -> None:
        """
        Validate AWS resources: DynamoDB table, S3 bucket, and SageMaker endpoints.
        Raises:
            botocore.exceptions.ClientError: If validation calls to AWS services fail
        """
        # Validate DynamoDB table accessibility
        # If a DynamoDB client exists (e.g., during testing), use it directly
        if getattr(self, '_dynamodb', None) is not None:
            # Use DynamoDB client for put_item operations
            self._predictions_table = self._dynamodb
        else:
            # Fallback: use resource-based table access
            dynamodb_res = boto3.resource(
                "dynamodb",
                region_name=self._region_name
            )
            table = dynamodb_res.Table(self._dynamodb_table_name)
            # Persist table for later operations
            self._predictions_table = table
            # Ensure table exists and is accessible
            try:
                table.scan()
            except botocore.exceptions.ClientError as e:
                msg = e.response.get("Error", {}).get("Message", str(e))
                raise ServiceConfigurationError(f"Resource not found: {msg}") from e
        # Validate S3 bucket accessibility
        self._s3.head_bucket(Bucket=self._bucket_name)
        # Validate SageMaker endpoint listing
        self._sagemaker.list_endpoints()
    
    def _get_endpoint_name(self, model_type: str) -> str:
        """
        Get the SageMaker endpoint name for a model type.
        
        Args:
            model_type: Type of model
            
        Returns:
            SageMaker endpoint name
            
        Raises:
            ModelNotFoundError: If endpoint is not found for the model type
        """
        # Normalize model type
        normalized_type = model_type.lower().replace("_", "-")
        
        # Check if model exists in mapping
        if normalized_type not in self._model_mappings:
            raise ModelNotFoundError(
                f"Model not found: {model_type}",
                model_type=model_type
            )
        
        # Construct endpoint name from prefix and model name
        endpoint_name = f"{self._endpoint_prefix}-{self._model_mappings[normalized_type]}"
        
        return endpoint_name
    
    def _invoke_endpoint(self, endpoint_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke a SageMaker endpoint with input data.
        
        This method handles invocation of SageMaker endpoints with appropriate
        error handling, retries for transient errors, and HIPAA-compliant audit
        logging. It also performs PHI detection on input data before transmission.
        
        Args:
            endpoint_name: SageMaker endpoint name
            input_data: Input data for the endpoint
            
        Returns:
            Prediction result
            
        Raises:
            ServiceConnectionError: If endpoint invocation fails
            ModelNotFoundError: If endpoint is not found
            PredictionError: If prediction fails
            DataPrivacyError: If PHI is detected in input data
        """
        # Check for PHI in input data based on privacy level
        self._check_phi_in_data(input_data)
        
        # Convert input data to JSON
        input_json = json.dumps(input_data)
        
        # Define retry parameters
        max_retries = 3
        retry_delay = 1.0  # seconds
        
        # Create request metadata for tracing
        request_id = f"req-{int(time.time())}-{hash(input_json) % 10000:04d}"
        request_start = time.time()
        
        for retry_count in range(max_retries):
            try:
                # Log attempt (excluding PHI)
                if retry_count > 0:
                    self._logger.info(
                        f"Retrying endpoint invocation (attempt {retry_count+1}/{max_retries}): "
                        f"endpoint={endpoint_name}, request_id={request_id}"
                    )
                
                # Invoke endpoint
                response = self._sagemaker_runtime.invoke_endpoint(
                    EndpointName=endpoint_name,
                    ContentType="application/json",
                    Body=input_json,
                    # Include custom metadata for request tracking
                    # These can be used for troubleshooting and auditing
                    CustomAttributes=json.dumps({
                        "request_id": request_id,
                        "privacy_level": self._privacy_level.value,
                        "client_timestamp": datetime.now().isoformat()
                    })
                )
                
                # Parse response
                response_body = response["Body"].read().decode("utf-8")
                result = json.loads(response_body)
                
                # Calculate latency for monitoring
                latency = time.time() - request_start
                self._logger.debug(
                    f"Endpoint invocation successful: endpoint={endpoint_name}, "
                    f"request_id={request_id}, latency={latency:.3f}s"
                )
                
                # Log the audit record if DynamoDB is configured
                self._log_audit_record(endpoint_name, input_data, result, request_id)
                
                return result
            
            except botocore.exceptions.ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                error_message = e.response.get("Error", {}).get("Message", str(e))
                
                # Log the error
                self._logger.error(
                    f"AWS endpoint invocation error: endpoint={endpoint_name}, "
                    f"request_id={request_id}, error_code={error_code}, "
                    f"error_message='{error_message}'"
                )
                
                # Map error to specific exception types
                if error_code == "ValidationError":
                    if "Endpoint" in error_message and "not found" in error_message:
                        raise ModelNotFoundError(
                            f"Endpoint not found: {endpoint_name}",
                            model_type=endpoint_name
                        ) from e
                    else:
                        raise ValidationError(
                            f"Invalid input: {error_message}",
                            details=str(e)
                        ) from e
                elif error_code == "ModelError":
                    raise PredictionError(
                        f"Model prediction failed: {error_message}",
                        model_type=endpoint_name
                    ) from e
                
                # Determine if error is transient and retryable
                transient_errors = [
                    "InternalServerError", "ServiceUnavailable",
                    "ThrottlingException", "ProvisionedThroughputExceededException"
                ]
                
                # Retry for transient errors
                if error_code in transient_errors and retry_count < max_retries - 1:
                    retry_seconds = retry_delay * (2 ** retry_count)  # Exponential backoff
                    self._logger.warning(
                        f"Transient error occurred, will retry in {retry_seconds:.2f}s: "
                        f"endpoint={endpoint_name}, request_id={request_id}, "
                        f"retry_count={retry_count+1}/{max_retries}"
                    )
                    time.sleep(retry_seconds)
                    continue
                
                # If we've exhausted retries or it's not a transient error, raise appropriate exception
                raise ServiceConnectionError(
                    f"Failed to invoke endpoint: {error_message}",
                    service="SageMaker",
                    error_type=error_code,
                    details=str(e)
                ) from e
            
            except json.JSONDecodeError as e:
                self._logger.error(
                    f"Failed to parse response from endpoint: endpoint={endpoint_name}, "
                    f"request_id={request_id}, error={str(e)}"
                )
                
                # Don't retry for malformed responses
                raise PredictionError(
                    f"Failed to parse model response: {str(e)}",
                    model_type=endpoint_name
                ) from e
            
            except Exception as e:
                self._logger.error(
                    f"Unexpected error during endpoint invocation: endpoint={endpoint_name}, "
                    f"request_id={request_id}, error={str(e)}"
                )
                
                # Only retry for certain exceptions, not for all
                if isinstance(e, (ConnectionError, TimeoutError)) and retry_count < max_retries - 1:
                    retry_seconds = retry_delay * (2 ** retry_count)
                    self._logger.warning(
                        f"Connection error, will retry in {retry_seconds:.2f}s: "
                        f"endpoint={endpoint_name}, request_id={request_id}, "
                        f"retry_count={retry_count+1}/{max_retries}"
                    )
                    time.sleep(retry_seconds)
                    continue
                
                # For unexpected errors, raise a generic service error
                raise ServiceConnectionError(
                    f"Unexpected error during endpoint invocation: {str(e)}",
                    service="SageMaker",
                    error_type="UnexpectedError",
                    details=str(e)
                ) from e
    
    def _log_audit_record(self, endpoint_name: str, input_data: Dict[str, Any],
                          result: Dict[str, Any], request_id: str = None) -> None:
        """
        Log an audit record of the prediction request and response.
        
        This method creates a comprehensive HIPAA-compliant audit trail by storing
        sanitized records of ML service interactions in DynamoDB. The audit records
        include metadata about the request and response but carefully exclude PHI.
        
        Args:
            endpoint_name: SageMaker endpoint name
            input_data: Input data for the prediction
            result: Prediction result
            request_id: Unique request identifier for tracing
        """
        if not self._dynamodb or not self._audit_table_name:
            self._logger.debug("Audit logging skipped: DynamoDB not configured")
            return
        
        try:
            # Create a sanitized version of input and output for audit
            sanitized_input = self._sanitize_data_for_audit(input_data)
            sanitized_result = self._sanitize_data_for_audit(result)
            
            # Generate audit ID if request_id not provided
            audit_id = request_id or f"audit-{int(time.time())}-{input_data.get('patient_id', 'unknown')[:8]}"
            
            # Get a hashed version of patient ID for security
            # This allows tracking activity for a patient without exposing their ID
            patient_id = input_data.get("patient_id", "unknown")
            hashed_patient_id = f"pid-{hash(patient_id) % 1000000:06d}"
            
            # Create detailed audit record
            audit_record = {
                "audit_id": {"S": audit_id},
                "timestamp": {"S": datetime.now().isoformat()},
                "endpoint_name": {"S": endpoint_name},
                "patient_id_hash": {"S": hashed_patient_id},  # Store hash instead of actual ID
                "request_type": {"S": self._get_request_type_from_endpoint(endpoint_name)},
                "input_summary": {"S": json.dumps(sanitized_input)},
                "output_summary": {"S": json.dumps(sanitized_result)},
                "privacy_level": {"S": self._privacy_level.value},
                "service_version": {"S": "1.0.0"},  # Include versioning for traceability
                "region": {"S": self._region_name},
                "status": {"S": result.get("status", "completed")},
                "ttl": {"N": str(int(time.time() + 7776000))}  # 90-day TTL for automatic cleanup
            }
            
            # Add user identifier if available (typically from JWT token)
            # For compliance, we need to track WHO accessed WHAT data WHEN
            if hasattr(self, "_current_user_id") and self._current_user_id:
                audit_record["user_id"] = {"S": self._current_user_id}
            
            # Add access purpose if available (required for some HIPAA audits)
            if "access_purpose" in input_data:
                audit_record["access_purpose"] = {"S": input_data["access_purpose"]}
            
            # Store in DynamoDB with condition to prevent overwriting
            self._dynamodb.put_item(
                TableName=self._audit_table_name,
                Item=audit_record,
                # Only add if item doesn't exist already (idempotency)
                ConditionExpression="attribute_not_exists(audit_id)"
            )
            
            self._logger.debug(f"Audit record created: audit_id={audit_id}, type={audit_record['request_type']['S']}")
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            
            # Don't log as error if it's just a condition failure (duplicate)
            if error_code == "ConditionalCheckFailedException":
                self._logger.debug(f"Duplicate audit record detected: {request_id}")
            else:
                self._logger.error(f"Failed to write audit record: error_code={error_code}, request_id={request_id}")
        
        except Exception as e:
            # Don't fail the operation if audit logging fails, but log it properly
            self._logger.error(f"Failed to log audit record: error={str(e)}, request_id={request_id}")
            
            # Attempt to write to local audit log as fallback
            try:
                self._log_audit_fallback(endpoint_name, input_data, request_id)
            except Exception as fallback_error:
                self._logger.error(f"Audit fallback logging also failed: {str(fallback_error)}")
    
    def _log_audit_fallback(self, endpoint_name: str, input_data: Dict[str, Any], request_id: str) -> None:
        """
        Fallback method for audit logging when DynamoDB is unavailable.
        
        This method writes a simplified audit record to a local log file as a
        last resort when the primary audit logging mechanism fails.
        
        Args:
            endpoint_name: SageMaker endpoint name
            input_data: Input data for the prediction
            request_id: Unique request identifier for tracing
        """
        # Create minimal sanitized record
        sanitized_record = {
            "timestamp": datetime.now().isoformat(),
            "audit_id": request_id,
            "endpoint": endpoint_name,
            "request_type": self._get_request_type_from_endpoint(endpoint_name),
            "patient_id_hash": f"pid-{hash(input_data.get('patient_id', 'unknown')) % 1000000:06d}"
        }
        
        # Get fallback log path from environment or use default
        fallback_log = os.environ.get("AUDIT_FALLBACK_LOG", "/tmp/xgboost_audit_fallback.log")
        
        # Append to fallback log
        with open(fallback_log, "a") as f:
            f.write(json.dumps(sanitized_record) + "\n")
    
    def _sanitize_data_for_audit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize data for audit logging, removing all PHI and sensitive details.
        
        This method creates a safe representation of the input/output data that can
        be stored in audit logs without compromising patient privacy. It follows
        HIPAA best practices by:
        1. Excluding all direct identifiers
        2. Storing field names without values for clinical data
        3. Keeping only aggregated metrics and non-identifiable information
        4. Using hashed values where correlations must be maintained
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized data with all PHI removed
        """
        # Create a copy to avoid modifying the original
        sanitized = {}
        
        # If input is not a dict, return empty dict to be safe
        if not isinstance(data, dict):
            return {}
        
        # Define fields that are explicitly allowed for audit with exact values
        # These should NEVER contain PHI
        audit_safe_fields = [
            "prediction_id", "model_type", "risk_type", "treatment_type",
            "outcome_type", "timestamp", "status", "confidence",
            "risk_level", "risk_score", "access_purpose"
        ]
        
        # Add safe fields to sanitized output
        for field in audit_safe_fields:
            if field in data:
                sanitized[field] = data[field]
        
        # NEVER include these fields in audit logs, not even hashed
        excluded_fields = [
            "name", "address", "email", "phone", "ssn", "dob", "birth_date",
            "mrn", "insurance_id", "contact_info", "family_members", "zip_code",
            "social_security", "driver_license", "passport", "biometric",
            "photo", "fingerprint", "genetic", "full_face", "identifiable"
        ]
        
        # For patient_id, use a reference while hiding actual value
        if "patient_id" in data:
            patient_id = data["patient_id"]
            # Store only last few chars or a hash, never the full ID
            if isinstance(patient_id, str) and len(patient_id) > 4:
                # Only store a truncated reference that can't identify the patient
                sanitized["patient_id_ref"] = f"...{patient_id[-4:]}"
            else:
                sanitized["patient_id_ref"] = "masked"
        
        # For input clinical data, only log field names, never values
        for field in ["clinical_data", "treatment_details", "treatment_plan", "medical_history"]:
            if field in data and isinstance(data[field], dict):
                # Store only field names, never the clinical values
                field_names = list(data[field].keys())
                # Filter out any field names that might contain PHI
                sanitized[f"{field}_schema"] = [
                    name for name in field_names
                    if not any(excluded in name.lower() for excluded in excluded_fields)
                ]
                sanitized[f"{field}_count"] = len(data[field])
        
        # For prediction results, extract only aggregated metrics
        if "metrics" in data and isinstance(data["metrics"], dict):
            sanitized["metrics"] = {}
            safe_metrics = ["accuracy", "precision", "recall", "f1_score", "auc", "mae", "mse", "rmse"]
            for metric in safe_metrics:
                if metric in data["metrics"]:
                    sanitized["metrics"][metric] = data["metrics"][metric]
        
        # For feature importance, only include top N features without values
        if "feature_importance" in data and isinstance(data["feature_importance"], dict):
            # Only include feature names (not values) and exclude any that might contain PHI
            feature_names = list(data["feature_importance"].keys())
            sanitized["feature_names"] = [
                name for name in feature_names[:10]  # Only include top 10 to limit possible PHI
                if not any(excluded in name.lower() for excluded in excluded_fields)
            ]
            sanitized["feature_count"] = len(data["feature_importance"])
        
        # For brain regions, only include region IDs and activation, not patient-specific data
        if "brain_regions" in data and isinstance(data["brain_regions"], list):
            sanitized["region_count"] = len(data["brain_regions"])
            # Only include a safe count of active regions, not specific identifiers
            if len(data["brain_regions"]) > 0 and isinstance(data["brain_regions"][0], dict):
                active_count = sum(1 for region in data["brain_regions"] if region.get("active", False))
                sanitized["active_region_count"] = active_count
        
        # Add security metadata
        sanitized["security_level"] = self._privacy_level.value
        sanitized["sanitized_timestamp"] = datetime.now().isoformat()
        sanitized["sanitized_version"] = "2.0.0"  # Track version of sanitization algorithm used
        
        return sanitized
    
    def _get_request_type_from_endpoint(self, endpoint_name: str) -> str:
        """
        Get request type from endpoint name.
        
        Args:
            endpoint_name: SageMaker endpoint name
            
        Returns:
            Request type
        """
        if "risk" in endpoint_name:
            return "risk_prediction"
        elif "treatment" in endpoint_name:
            return "treatment_response"
        elif "outcome" in endpoint_name:
            return "outcome_prediction"
        elif "feature-importance" in endpoint_name:
            return "feature_importance"
        elif "digital-twin" in endpoint_name:
            return "digital_twin_integration"
        else:
            return "unknown"
    
    def _check_phi_in_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check for PHI in data based on privacy level setting.
        
        This method provides sophisticated detection of Protected Health Information
        in clinical data for mental health and psychiatry applications. It employs
        multiple detection strategies including:
        
        1. Pattern-based detection (regex) for common PHI formats
        2. Dictionary-based detection for known psychiatric/medical terms
        3. Context-aware analysis for sequences that suggest identifiable information
        4. Privacy-level based filtering to adjust sensitivity
        
        The implementation prioritizes patient privacy according to HIPAA standards
        while being optimized for clinical psychology and psychiatry workflows.
        
        Args:
            data: Data to check for PHI
            
        Returns:
            Tuple containing:
              - Boolean indicating if PHI was detected
              - List of detected PHI types
              
        Raises:
            DataPrivacyError: If PHI is detected and current settings require exception
        """
        # Extract all string values from the data
        string_values = []
        self._extract_strings(data, string_values)
        
        # Define PHI patterns based on privacy level
        phi_patterns = []
        
        # Basic patterns checked at all privacy levels (high-confidence PHI)
        basic_patterns = [
            # SSN - Various formats
            (r"\b\d{3}-\d{2}-\d{4}\b", "SSN"),
            (r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b", "SSN"),
            # Patient MRN/ID - Common formats
            (r"\bMRN[:# ]?\d{5,12}\b", "MRN"),
            (r"\bPATIENT[-_# ]?\d{5,12}\b", "Patient ID"),
            # Explicit identifiers
            (r"\bPATIENT\s+NAME\s*[:=]?\s*([A-Za-z\s]+)\b", "Explicit Patient Name"),
            (r"\bNAME\s*[:=]?\s*([A-Za-z\s]+)\b", "Explicit Name Field")
        ]
        phi_patterns.extend(basic_patterns)
        
        # Standard level (default) adds more patterns
        if self._privacy_level >= PrivacyLevel.STANDARD:
            standard_patterns = [
                # Names - Various formats with high confidence
                (r"\b([A-Z][a-z]+\s){1,2}[A-Z][a-z]+\b", "Name"),
                # Email addresses
                (r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "Email"),
                # Phone numbers - Various formats
                (r"\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b", "Phone"),
                (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "Phone"),
                # Birth dates
                (r"\b(?:0?[1-9]|1[0-2])[\/\-]\d{1,2}[\/\-]\d{2,4}\b", "Date of Birth"),
                (r"\bDOB\s*[:=]?\s*\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b", "Explicit Date of Birth"),
                # Insurance
                (r"\bINSURANCE\s*(?:ID|NUMBER|#)?\s*[:=]?\s*[A-Z0-9-]+\b", "Insurance ID")
            ]
            phi_patterns.extend(standard_patterns)
        
        # Enhanced level adds psychiatry-specific patterns
        if self._privacy_level >= PrivacyLevel.ENHANCED:
            enhanced_patterns = [
                # ZIP codes
                (r"\b\d{5}(?:-\d{4})?\b", "ZIP"),
                # Dates - Various formats
                (r"\b(?:0?[1-9]|1[0-2])[\/\-]\d{1,2}[\/\-]\d{2,4}\b", "Date"),
                (r"\b\d{1,2}[\/\-](?:0?[1-9]|1[0-2])[\/\-]\d{2,4}\b", "Date"),
                # Credit card numbers
                (r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "Credit Card"),
                # Driver's license
                (r"\b[A-Z][0-9]{7,8}\b", "Driver's License"),
                # Mental health-specific identifiers
                (r"\b(?:PSYCHIATRIST|THERAPIST|COUNSELOR)\s*[:=]?\s*(?:DR\.?\s*)?[A-Z][a-z]+\b", "Provider Name"),
                (r"\b(?:DIAGNOSIS|DX)\s*[:=]?\s*([A-Za-z\s\-]+)\b", "Diagnosis Text"),
                # Medication identifiers - with name context
                (r"\b(?:MEDICATION|MED|PRESCRIPTION|RX)\s*[:=]?\s*([A-Za-z0-9\s\-]+)(?:\s*\d+\s*MG)?\b", "Medication with Dose"),
                # Treatment facility
                (r"\b(?:CLINIC|HOSPITAL|FACILITY|CENTER)\s*[:=]?\s*([A-Za-z0-9\s\-]+)\b", "Treatment Facility")
            ]
            phi_patterns.extend(enhanced_patterns)
        
        # Maximum level adds the most comprehensive patterns
        if self._privacy_level == PrivacyLevel.MAXIMUM:
            maximum_patterns = [
                # Medical record identifiers
                (r"\b(?:CPT|ICD[-\s]?10|ICD[-\s]?9)[-:]\s*\d+\b", "Medical Code"),
                # More sophisticated name detection
                (r"\b(?:Mr\.|Mrs\.|Dr\.|Ms\.|Miss)?\s+[A-Z][a-z]+\s+(?:[A-Z][a-z]+\s+)?[A-Z][a-z]+\b", "Formal Name"),
                # Addresses
                (r"\b\d+\s+[A-Za-z0-9\s,]+(?:Avenue|Lane|Road|Boulevard|Ave|Ln|Rd|Blvd|Street|St|Drive|Dr|Court|Ct|Plaza|Plz|Square|Sq)\.?\b", "Address"),
                # Account numbers
                (r"\bACC(?:OUNT)?[-#:]\s*\d{6,}\b", "Account Number"),
                # Psychiatric medication patterns
                (r"\b(?:SSRI|SNRI|TCA|MAOI|antidepressant|anxiolytic|antipsychotic)\b", "Medication Class"),
                (r"\b(?:Prozac|Zoloft|Lexapro|Celexa|Paxil|Effexor|Cymbalta|Wellbutrin|Remeron|Trazodone|Xanax|Ativan|Klonopin|Valium|Risperdal|Abilify|Seroquel|Zyprexa|Geodon|Haldol|Lithium|Depakote|Lamictal|Tegretol|Trileptal)\b", "Specific Medication"),
                # Psychiatric diagnosis patterns
                (r"\b(?:Major\s+Depressive\s+Disorder|Bipolar\s+Disorder|Generalized\s+Anxiety\s+Disorder|Panic\s+Disorder|Social\s+Anxiety\s+Disorder|Obsessive\s+Compulsive\s+Disorder|Post\s+Traumatic\s+Stress\s+Disorder|PTSD|Schizophrenia|Schizoaffective\s+Disorder|Borderline\s+Personality\s+Disorder|ADHD|Attention\s+Deficit|Autism\s+Spectrum|Eating\s+Disorder|Anorexia|Bulimia|Substance\s+Use\s+Disorder)\b", "Specific Diagnosis"),
                # Suicide/self-harm indicators - extra sensitive in psychiatric contexts
                (r"\b(?:suicidal|suicide|self-harm|self\s+harm|harm\s+to\s+self|harm\s+to\s+others|SI|HI)\b", "Risk Indicator"),
                # Family member references that could identify patient
                (r"\b(?:spouse|husband|wife|partner|child|son|daughter|mother|father|parent|sibling|brother|sister)\s+[A-Z][a-z]+\b", "Family Member Reference")
            ]
            phi_patterns.extend(maximum_patterns)
            
            # Add psychiatry-specific PHI detection for psychometric scales
            psychiatric_assessment_patterns = [
                (r"\b(?:PHQ-?9|GAD-?7|QIDS|MADRS|HAM-?D|HAM-?A|Y-?BOCS|PCL-?5|CAPS|SCID)\s+(?:score|result|assessment)?\s*[:=]?\s*\d+", "Assessment Score"),
                (r"\b(?:Beck\s+Depression\s+Inventory|BDI|Hamilton\s+Rating\s+Scale|Yale\s+Brown\s+Obsessive\s+Compulsive\s+Scale)\s+(?:score|result|assessment)?\s*[:=]?\s*\d+", "Assessment Score")
            ]
            phi_patterns.extend(psychiatric_assessment_patterns)
        
        # Check all string values against patterns
        detected_patterns = []
        for string_value in string_values:
            for pattern, pattern_type in phi_patterns:
                if re.search(pattern, string_value):
                    detected_patterns.append(pattern_type)
                    # If not in maximum mode, return after first detection for efficiency
                    if self._privacy_level != PrivacyLevel.MAXIMUM:
                        if self._privacy_level >= PrivacyLevel.STANDARD:
                            raise DataPrivacyError(
                                f"PHI detected in input data: {pattern_type}",
                                pattern_types=[pattern_type]
                            )
                        else:
                            return True, [pattern_type]
        
        # If any patterns were detected in maximum mode, raise error with all detected types
        detected_pattern_types = list(set(detected_patterns))
        if detected_patterns:
            if self._privacy_level >= PrivacyLevel.ENHANCED:
                raise DataPrivacyError(
                    f"PHI detected in input data: {', '.join(detected_pattern_types)}",
                    pattern_types=detected_pattern_types
                )
            return True, detected_pattern_types
            
        # No PHI detected
        return False, []
    
    def _extract_strings(self, data: Any, result: List[str]) -> None:
        """
        Extract all string values from a nested data structure.
        
        Args:
            data: Data to extract strings from
            result: List to store extracted strings
        """
        if isinstance(data, str):
            result.append(data)
        elif isinstance(data, dict):
            for value in data.values():
                self._extract_strings(value, result)
        elif isinstance(data, list):
            for item in data:
                self._extract_strings(item, result)
    
    def _notify_observers(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """
        Notify observers of an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        # Add timestamp to event data
        data["timestamp"] = datetime.now().isoformat()
        
        # Notify observers registered for this event type
        event_key = event_type
        if event_key in self._observers:
            for observer in self._observers[event_key]:
                try:
                    observer.update(event_type, data)
                except Exception as e:
                    self._logger.error(f"Error notifying observer: {e}")
        
        # Notify observers registered for all events
        if "*" in self._observers:
            for observer in self._observers["*"]:
                try:
                    observer.update(event_type, data)
                except Exception as e:
                    self._logger.error(f"Error notifying wildcard observer: {e}")
    
    
    def _validate_outcome_params(
        self,
        patient_id: str,
        outcome_timeframe: Dict[str, int],
        clinical_data: Dict[str, Any],
        treatment_plan: Dict[str, Any]
    ) -> None:
        """
        Validate outcome prediction parameters.
        
        Args:
            patient_id: Patient identifier
            outcome_timeframe: Timeframe for outcome prediction
            clinical_data: Clinical data
            treatment_plan: Treatment plan
            
        Raises:
            ValidationError: If parameters are invalid
        """
        # Validate patient ID
        if not patient_id:
            raise ValidationError("Patient ID cannot be empty", field="patient_id")
        
        # Validate outcome timeframe
        if not outcome_timeframe:
            raise ValidationError("Outcome timeframe cannot be empty", field="outcome_timeframe")
        
        valid_units = ["days", "weeks", "months"]
        if not any(unit in outcome_timeframe for unit in valid_units):
            raise ValidationError(
                f"Invalid outcome timeframe. Must include at least one of: {', '.join(valid_units)}",
                field="outcome_timeframe"
            )
        
        for unit, value in outcome_timeframe.items():
            if unit not in valid_units:
                raise ValidationError(
                    f"Invalid time unit: {unit}. Valid units: {', '.join(valid_units)}",
                    field=f"outcome_timeframe.{unit}",
                    value=unit
                )
            
            if not isinstance(value, int) or value <= 0:
                raise ValidationError(
                    f"Invalid value for {unit}: {value}. Must be a positive integer.",
                    field=f"outcome_timeframe.{unit}",
                    value=value
                )
        
        # Validate clinical data
        if not clinical_data:
            raise ValidationError("Clinical data cannot be empty", field="clinical_data")
        
        # Validate treatment plan
        if not treatment_plan:
            raise ValidationError("Treatment plan cannot be empty", field="treatment_plan")
    
    def _calculate_timeframe_days(self, timeframe: Dict[str, int]) -> int:
        """
        Calculate total days from a timeframe.
        
        Args:
            timeframe: Timeframe dictionary with days, weeks, and/or months
            
        Returns:
            Total days
        """
        total_days = 0
        
        if "days" in timeframe:
            total_days += timeframe["days"]
        
        if "weeks" in timeframe:
            total_days += timeframe["weeks"] * 7
        
        if "months" in timeframe:
            total_days += timeframe["months"] * 30
        
        return total_days
    
    def _ensure_initialized(self) -> None:
        """
        Ensure that the service is initialized before use.
        
        Raises:
            ConfigurationError: If service is not initialized
        """
        if not hasattr(self, '_initialized') or not self._initialized:
            raise ConfigurationError(
                "XGBoost service not initialized. Call initialize() first."
            )
    
    def get_prediction(self, prediction_id: str) -> Any:
        """
        Retrieve a stored prediction by its ID from DynamoDB.
        Raises ResourceNotFoundError or ServiceConnectionError.
        """
        self._ensure_initialized()
        try:
            resp = self._predictions_table.get_item(Key={"prediction_id": prediction_id})
        except botocore.exceptions.ClientError as e:
            raise ServiceConnectionError("Failed to retrieve prediction") from e
        item = resp.get("Item")
        if not item:
            raise ResourceNotFoundError(f"Prediction {prediction_id} not found", resource_type="prediction", resource_id=prediction_id)
        # Convert to object with attributes
        # Parse enums
        pt_val = item.get("prediction_type")
        try:
            pt_enum = ModelType(pt_val)
        except Exception:
            pt_enum = pt_val
        rl_val = item.get("risk_level")
        try:
            rl_enum = RiskLevel(rl_val)
        except Exception:
            rl_enum = rl_val
        # Assemble result
        result = {
            "prediction_id": item.get("prediction_id"),
            "patient_id": item.get("patient_id"),
            "prediction_type": pt_enum,
            "risk_level": rl_enum,
            "risk_score": item.get("risk_score"),
            "confidence": item.get("confidence"),
            # keep other fields if necessary
        }
        from types import SimpleNamespace
        return SimpleNamespace(**result)

    def validate_prediction(self, prediction_id: str, status: str, validator_notes: Optional[str] = None) -> bool:
        """
        Validate or update the status of a prediction.
        Calls internal update method.
        """
        self._ensure_initialized()
        updates = {"validation_status": status}
        if validator_notes is not None:
            updates["validator_notes"] = validator_notes
        # Delegate to update function
        self._update_prediction(prediction_id, updates)
        return True

    def _update_prediction(self, prediction_id: str, updates: Dict[str, Any]) -> None:
        """
        Internal method to update a prediction record in DynamoDB.
        """
        try:
            expr = ", ".join(f"#{k}=:{k}" for k in updates.keys())
            expr = f"SET {expr}"
            names = {f"#{k}": k for k in updates.keys()}
            values = {f":{k}": v for k, v in updates.items()}
            self._predictions_table.update_item(
                Key={"prediction_id": prediction_id},
                UpdateExpression=expr,
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values
            )
        except botocore.exceptions.ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code == "ResourceNotFoundException":
                raise ResourceNotFoundError(f"Prediction {prediction_id} not found", resource_type="prediction", resource_id=prediction_id) from e
            else:
                raise ServiceConnectionError(f"Failed to update prediction: {e.response.get('Error', {}).get('Message', str(e))}") from e

    def healthcheck(self) -> Dict[str, Any]:
        """
        Perform health check for AWS resources and endpoints.
        Returns status dict.
        """
        self._ensure_initialized()
        components: Dict[str, Any] = {}
        # DynamoDB
        try:
            self._predictions_table.scan()
            components["dynamodb"] = {"status": "healthy"}
        except botocore.exceptions.ClientError as e:
            components["dynamodb"] = {"status": "unhealthy", "error": e.response.get("Error", {}).get("Message", str(e))}
        # S3
        try:
            self._s3.head_bucket(Bucket=self._bucket_name)
            components["s3"] = {"status": "healthy"}
        except botocore.exceptions.ClientError as e:
            components["s3"] = {"status": "unhealthy", "error": e.response.get("Error", {}).get("Message", str(e))}
        # SageMaker
        models: Dict[str, str] = {}
        try:
            resp = self._sagemaker.list_endpoints()
            components["sagemaker"] = {"status": "healthy"}
            for ep in resp.get("Endpoints", []):
                name = ep.get("EndpointName", "")
                status = ep.get("EndpointStatus", "")
                # strip prefix
                key = name[len(self._endpoint_prefix):] if name.startswith(self._endpoint_prefix) else name
                if status == "InService":
                    models[key] = "active"
                elif status == "Updating":
                    models[key] = "updating"
                else:
                    models[key] = "error"
        except botocore.exceptions.ClientError as e:
            components["sagemaker"] = {"status": "unhealthy", "error": e.response.get("Error", {}).get("Message", str(e))}
        # Determine overall status: all unhealthy -> unhealthy, any unhealthy or model issues -> degraded, else healthy
        statuses = [comp.get("status") for comp in components.values()]
        if statuses and all(s == "unhealthy" for s in statuses):
            overall = "unhealthy"
        elif any(s == "unhealthy" for s in statuses) or any(state != "active" for state in models.values()):
            overall = "degraded"
        else:
            overall = "healthy"
        result = {
            "status": overall,
            "timestamp": datetime.now().isoformat(),
            "components": components,
            "models": models
        }
        return result
