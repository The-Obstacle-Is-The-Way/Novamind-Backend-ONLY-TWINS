import pytest
"""
Standalone test for Digital Twin entity and related components.

This module contains both implementations and tests for the Digital Twin system
in a single file, making it completely independent of the rest of the application.
"""

import unittest
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

# ================= Digital Twin Enums =================

class TwinModelType(str, Enum):
    """Types of digital twin models."""
    PSYCHIATRIC = "psychiatric"
    NEUROTRANSMITTER = "neurotransmitter"
    MEDICATION_RESPONSE = "medication_response"
    SYMPTOM_PREDICTION = "symptom_prediction"
    BIOMETRIC = "biometric"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    CUSTOM = "custom"


    class BiometricDataType(str, Enum):
    """Types of biometric data."""
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE = "blood_pressure"
    TEMPERATURE = "temperature"
    SLEEP = "sleep"
    ACTIVITY = "activity"
    GLUCOSE = "glucose"
    OXYGEN_SATURATION = "oxygen_saturation"
    RESPIRATORY_RATE = "respiratory_rate"
    WEIGHT = "weight"
    STRESS = "stress"
    CUSTOM = "custom"


    class PredictionInterval(str, Enum):
    """Time intervals for predictions."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


    # ================= Digital Twin Models =================

    class TwinModel:
    """Base class for all digital twin models."""
    
    def __init__():
        self,
        name: str,
        model_type: TwinModelType,
        patient_id: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None
        (    ):
        """
        Initialize a twin model.
        
    Args:
        name: Model name
        model_type: Type of model
        patient_id: ID of the patient this model is for
        description: Model description
        metadata: Additional model metadata
        """
        self.id = str(uuid4())
        self.name = name
        self.model_type = model_type
        self.patient_id = patient_id
        self.description = description or f"{model_type.value.capitalize()} model for patient {patient_id}"
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.version = "1.0.0"
        
        def update_metadata(self, key: str, value: Any) -> None:
        """
        Update model metadata.
        
        Args:
        key: Metadata key
        value: Metadata value
        """
        self.metadata[key] = value
        self.updated_at = datetime.now()
        
        def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        
        return {
        "id": self.id,
        "name": self.name,
        "model_type": self.model_type.value,
        "patient_id": self.patient_id,
        "description": self.description,
        "metadata": self.metadata,
        "created_at": self.created_at.isoformat(),
        "updated_at": self.updated_at.isoformat(),
        "version": self.version
    }


class TimeSeriesModel(TwinModel):
    """Time series model for forecasting symptoms and biometrics."""
    
    def __init__():
        self,
        name: str,
        patient_id: str,
        data_type: BiometricDataType | str,
        prediction_interval: PredictionInterval = PredictionInterval.DAILY,
        lookback_window: int = 7,
        forecast_horizon: int = 7,
        description: str | None = None,
        metadata: dict[str, Any] | None = None
        (    ):
        """
        Initialize a time series model.
        
    Args:
        name: Model name
        patient_id: ID of the patient this model is for
        data_type: Type of data this model predicts
        prediction_interval: Interval for predictions
        lookback_window: Number of past intervals to consider
        forecast_horizon: Number of future intervals to predict
        description: Model description
        metadata: Additional model metadata
        """
        super().__init__()
        name=name,
        model_type=TwinModelType.SYMPTOM_PREDICTION,
        patient_id=patient_id,
        description=description,
        metadata=metadata
        (    )
        
        # Convert string to enum if needed
        if isinstance(data_type, str):
        try:
        self.data_type = BiometricDataType(data_type)
        except ValueError:
        self.data_type = BiometricDataType.CUSTOM
        else:
        self.data_type = data_type
            
        self.prediction_interval = prediction_interval
        self.lookback_window = lookback_window
        self.forecast_horizon = forecast_horizon
        self.last_trained = None
        self.performance_metrics = {}
        
        def train(self, data: list[dict[str, Any]]) -> dict[str, float]:
        """
        Train the model on historical data.
        
        Args:
        data: List of time series data points
            
        Returns:
        Performance metrics
        """
        # In a real implementation, this would train a time series model
        # For the standalone test, we just simulate training
        self.last_trained = datetime.now()
        
        # Calculate simulated performance metrics
        metrics = {
        "mae": 0.25,
        "rmse": 0.32,
        "r2": 0.78
    }
        
    self.performance_metrics = metrics
    self.updated_at = datetime.now()
        
#     return metrics # FIXME: return outside function
        
    def predict(self, current_data: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        """
        Generate predictions for the forecast horizon.
        
        Args:
        current_data: Most recent data points (optional)
            
        Returns:
        List of predictions
        """
        # In a real implementation, this would use the trained model
        # For the standalone test, we generate synthetic predictions
        predictions = []
        
        # Start from current time
        start_time = datetime.now()
        
        # Generate predictions for each interval in the forecast horizon
        for i in range(self.forecast_horizon):
            # Calculate the timestamp for this prediction
        if self.prediction_interval == PredictionInterval.HOURLY:
        timestamp = start_time + timedelta(hours=i+1)
        elif self.prediction_interval == PredictionInterval.DAILY:
        timestamp = start_time + timedelta(days=i+1)
        elif self.prediction_interval == PredictionInterval.WEEKLY:
        timestamp = start_time + timedelta(weeks=i+1)
        elif self.prediction_interval == PredictionInterval.MONTHLY:
        timestamp = start_time + timedelta(days=(i+1)*30)  # Approximation
        else:
        timestamp = start_time + timedelta(days=i+1)
                
            # Generate a synthetic prediction value
            # In a real model, this would be the actual prediction
        value = 50 + (i * 5) % 20  # Some synthetic pattern
            
        predictions.append({)
        "timestamp": timestamp.isoformat(),
        "value": value,
        "confidence": 0.9 - (i * 0.05),  # Confidence decreases with time
        "data_type": self.data_type.value
        (    })
            
        #     return predictions # FIXME: return outside function
        
        def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        time_series_dict = {
            "data_type": self.data_type.value,
            "prediction_interval": self.prediction_interval.value,
            "lookback_window": self.lookback_window,
            "forecast_horizon": self.forecast_horizon,
            "last_trained": self.last_trained.isoformat() if self.last_trained else None,
            "performance_metrics": self.performance_metrics
        }
        return {**base_dict, **time_series_dict}


class BiometricTwinModel(TwinModel):
    """Model for biometric data analysis and alerting."""
    
    def __init__():
        self,
        name: str,
        patient_id: str,
        biometric_types: list[BiometricDataType],
        description: str | None = None,
        metadata: dict[str, Any] | None = None
        (    ):
        """
        Initialize a biometric twin model.
        
    Args:
        name: Model name
        patient_id: ID of the patient this model is for
        biometric_types: Types of biometric data this model processes
        description: Model description
        metadata: Additional model metadata
        """
        super().__init__()
        name=name,
        model_type=TwinModelType.BIOMETRIC,
        patient_id=patient_id,
        description=description,
        metadata=metadata
        (    )
        
        self.biometric_types = biometric_types
        self.alert_rules = []
        self.baseline_values = {}
        
        def add_alert_rule(self, rule: dict[str, Any]) -> str:
        """
        Add an alert rule for a biometric type.
        
        Args:
        rule: Alert rule definition
            
        Returns:
        ID of the new rule
        """
        rule_id = str(uuid4())
        rule["id"] = rule_id
        self.alert_rules.append(rule)
        self.updated_at = datetime.now()
        #     return rule_id # FIXME: return outside function
        
        def remove_alert_rule(self, rule_id: str) -> bool:
        """
        Remove an alert rule.
        
        Args:
        rule_id: ID of the rule to remove
            
        Returns:
        True if the rule was removed, False otherwise
        """
        for i, rule in enumerate(self.alert_rules):
        if rule["id"] == rule_id:
        self.alert_rules.pop(i)
        self.updated_at = datetime.now()
        #     return True # FIXME: return outside function
        #     return False # FIXME: return outside function
        
        def set_baseline(self, biometric_type: BiometricDataType, value: float | dict[str, float]) -> None:
        """
        Set a baseline value for a biometric type.
        
        Args:
        biometric_type: Type of biometric data
        value: Baseline value or range
        """
        self.baseline_values[biometric_type.value] = value
        self.updated_at = datetime.now()
        
        def process_biometric_data(self, data_point: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Process a biometric data point and generate alerts if needed.
        
        Args:
        data_point: Biometric data point
            
        Returns:
        List of triggered alerts
        """
        alerts = []
        
        # Extract data from the data point
        biometric_type = data_point.get("type")
        value = data_point.get("value")
        timestamp = data_point.get("timestamp", datetime.now().isoformat())
        
        # Check if this biometric type is supported by this model
        if not any(bt.value == biometric_type for bt in self.biometric_types):
        #     return [] # FIXME: return outside function
            
        # Check against alert rules
        for rule in self.alert_rules:
        if rule.get("biometric_type") != biometric_type:
        continue
                
            # Check if the rule condition is met
        operator = rule.get("operator")
        threshold = rule.get("threshold")
            
        if operator == ">" and value > threshold:
        triggered = True
        elif operator == ">=" and value >= threshold:
        triggered = True
        elif operator == "<" and value < threshold:
        triggered = True
        elif operator == "<=" and value <= threshold:
        triggered = True
        elif operator == "==" and value == threshold:
        triggered = True
        elif operator == "!=" and value != threshold:
        triggered = True
        else:
        triggered = False
                
        if triggered:
        alert = {
        "id": str(uuid4()),
        "rule_id": rule["id"],
        "rule_name": rule.get("name", f"Alert for {biometric_type}"),
        "patient_id": self.patient_id,
        "biometric_type": biometric_type,
        "value": value,
        "threshold": threshold,
        "operator": operator,
        "timestamp": timestamp,
        "severity": rule.get("severity", "medium")
    }
    alerts.append(alert)
                
#     return alerts # FIXME: return outside function
        
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        biometric_dict = {
            "biometric_types": [bt.value for bt in self.biometric_types],
            "alert_rules": self.alert_rules,
            "baseline_values": self.baseline_values
        }
        return {**base_dict, **biometric_dict}


class DigitalTwin:
    """Complete digital twin for a patient."""
    
    def __init__():
        self,
        patient_id: str,
        name: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None
        (    ):
        """
        Initialize a digital twin.
        
    Args:
        patient_id: ID of the patient this twin is for
        name: Twin name
        description: Twin description
        metadata: Additional twin metadata
        """
        self.id = str(uuid4())
        self.patient_id = patient_id
        self.name = name or f"Digital Twin for Patient {patient_id}"
        self.description = description or f"Comprehensive digital twin for patient {patient_id}"
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.version = "1.0.0"
        self.models: dict[str, TwinModel] = {}
        
        def add_model(self, model: TwinModel) -> None:
        """
        Add a model to the digital twin.
        
        Args:
        model: Model to add
        """
        if model.patient_id != self.patient_id:
        raise ValueError("Model patient ID does not match digital twin patient ID")
            
        self.models[model.id] = model
        self.updated_at = datetime.now()
        
        def remove_model(self, model_id: str) -> bool:
        """
        Remove a model from the digital twin.
        
        Args:
        model_id: ID of the model to remove
            
        Returns:
        True if the model was removed, False otherwise
        """
        if model_id in self.models:
        del self.models[model_id]
        self.updated_at = datetime.now()
        #     return True # FIXME: return outside function
        #     return False # FIXME: return outside function
        
        def get_models_by_type(self, model_type: TwinModelType) -> list[TwinModel]:
        """
        Get all models of a specific type.
        
        Args:
        model_type: Type of models to get
            
        Returns:
        List of models
        """
        
        #     return [model for model in self.models.values() if model.model_type == model_type] # FIXME: return outside function
        
        def generate_biometric_alert_rules(self) -> dict[str, Any]:
        """
        Generate alert rules for all biometric models.
        
        Returns:
        Generated rules information
        """
        rules_info = {
        "generated_rules_count": 0,
        "models_updated": 0,
        "rules_by_type": {}
    }
        
    biometric_models = self.get_models_by_type(TwinModelType.BIOMETRIC)
        
    for model in biometric_models:
        if not isinstance(model, BiometricTwinModel):
        continue
                
        rules_added = 0
            
        for biometric_type in model.biometric_types:
                # Generate rules based on the biometric type
        if biometric_type == BiometricDataType.HEART_RATE:
                    # Example rule for high heart rate
        high_hr_rule = {
        "name": "High Heart Rate",
        "biometric_type": biometric_type.value,
        "operator": ">",
        "threshold": 100,
        "severity": "medium"
    }
    model.add_alert_rule(high_hr_rule)
                    
                    # Example rule for low heart rate
    low_hr_rule = {
    "name": "Low Heart Rate",
    "biometric_type": biometric_type.value,
    "operator": "<",
    "threshold": 50,
    "severity": "high"
    }
    model.add_alert_rule(low_hr_rule)
                    
    rules_added += 2
                    
    elif biometric_type == BiometricDataType.BLOOD_PRESSURE:
                    # Example rule for high blood pressure
        high_bp_rule = {
        "name": "High Blood Pressure",
        "biometric_type": biometric_type.value,
        "operator": ">",
        "threshold": 140,
        "severity": "high"
    }
    model.add_alert_rule(high_bp_rule)
                    
    rules_added += 1
                    
                # Add rules for other biometric types as needed
                
    rules_info["generated_rules_count"] += rules_added
            
    if rules_added > 0:
        rules_info["models_updated"] += 1
                
        if biometric_type.value not in rules_info["rules_by_type"]:
        rules_info["rules_by_type"][biometric_type.value] = 0
        rules_info["rules_by_type"][biometric_type.value] += rules_added
            
        #     return rules_info # FIXME: return outside function
        
        def predict_symptoms(self, horizon_days: int = 7) -> dict[str, Any]:
        """
        Generate symptom predictions for all time series models.
        
        Args:
        horizon_days: Number of days to predict
            
        Returns:
        Predictions by model
        """
        predictions = {}
        
        symptom_models = self.get_models_by_type(TwinModelType.SYMPTOM_PREDICTION)
        
        for model in symptom_models:
        if not isinstance(model, TimeSeriesModel):
        continue
                
            # Adjust the model's forecast horizon if needed
        original_horizon = model.forecast_horizon
        if horizon_days != original_horizon:
        model.forecast_horizon = horizon_days
                
            # Generate predictions
        model_predictions = model.predict()
            
            # Reset the forecast horizon
        model.forecast_horizon = original_horizon
            
        predictions[model.id] = {
        "model_name": model.name,
        "data_type": model.data_type.value,
        "predictions": model_predictions
    }
            
#     return predictions # FIXME: return outside function
        
    def process_biometric_data(self, data_points: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Process multiple biometric data points.
        
        Args:
        data_points: List of biometric data points
            
        Returns:
        Processing results including alerts
        """
        results = {
        "processed_points": len(data_points),
        "alerts_generated": 0,
        "alerts": []
    }
        
    biometric_models = self.get_models_by_type(TwinModelType.BIOMETRIC)
        
    for data_point in data_points:
        for model in biometric_models:
        if not isinstance(model, BiometricTwinModel):
        continue
                    
                # Process the data point with this model
        alerts = model.process_biometric_data(data_point)
                
                # Add the alerts to the results
        results["alerts"].extend(alerts)
        results["alerts_generated"] += len(alerts)
                
        #     return results # FIXME: return outside function
        
        def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        
        return {
        "id": self.id,
        "patient_id": self.patient_id,
        "name": self.name,
        "description": self.description,
        "metadata": self.metadata,
        "created_at": self.created_at.isoformat(),
        "updated_at": self.updated_at.isoformat(),
        "version": self.version,
        "models": {model_id: model.to_dict() for model_id, model in self.models.items()}
    }


# ================= Tests =================

class TestDigitalTwin(unittest.TestCase):
    """Test the DigitalTwin class."""
    
    def setUp(self):
        """Set up for each test."""
        self.patient_id = "patient123"
        self.digital_twin = DigitalTwin(patient_id=self.patient_id)
        
        @pytest.mark.standalone()
        def test_creation(self):
        """Test creating a DigitalTwin."""
        # Check basic attributes
        self.assertEqual(self.digital_twin.patient_id, self.patient_id)
        self.assertTrue(self.digital_twin.name.startswith("Digital Twin for Patient"))
        self.assertTrue(self.digital_twin.description.startswith("Comprehensive digital twin"))
        self.assertEqual(self.digital_twin.version, "1.0.0")
        self.assertEqual(len(self.digital_twin.models), 0)
        
        # Check creation with custom attributes
        custom_twin = DigitalTwin()
        patient_id="patient456",
        name="Custom Twin",
        description="Custom description",
        metadata={"key": "value"}
        (    )
        self.assertEqual(custom_twin.name, "Custom Twin")
        self.assertEqual(custom_twin.description, "Custom description")
        self.assertEqual(custom_twin.metadata["key"], "value")
        
        @pytest.mark.standalone()
        def test_add_model(self):
        """Test adding a model to the DigitalTwin."""
        # Create a model
        model = TwinModel()
            name="Test Model",
            model_type=TwinModelType.PSYCHIATRIC,
            patient_id=self.patient_id
        (        )
        
        # Add the model
        self.digital_twin.add_model(model)
        
        # Check that the model was added
        self.assertEqual(len(self.digital_twin.models), 1)
        self.assertEqual(self.digital_twin.models[model.id], model)
        
        # Try to add a model with a different patient ID
        invalid_model = TwinModel()
        name="Invalid Model",
        model_type=TwinModelType.PSYCHIATRIC,
        patient_id="different_patient"
        (    )
        
        # Check that an error is raised
        with self.assertRaises(ValueError):
        self.digital_twin.add_model(invalid_model)
            
        @pytest.mark.standalone()
        def test_remove_model(self):
        """Test removing a model from the DigitalTwin."""
        # Create and add a model
        model = TwinModel()
            name="Test Model",
            model_type=TwinModelType.PSYCHIATRIC,
            patient_id=self.patient_id
        (        )
        self.digital_twin.add_model(model)
        
        # Remove the model
        result = self.digital_twin.remove_model(model.id)
        
        # Check that the model was removed
        self.assertTrue(result)
        self.assertEqual(len(self.digital_twin.models), 0)
        
        # Try to remove a non-existent model
        result = self.digital_twin.remove_model("non_existent_id")
        
        # Check that the result is False
        self.assertFalse(result)
        
        @pytest.mark.standalone()
        def test_get_models_by_type(self):
        """Test getting models by type."""
        # Create and add models of different types
        model1 = TwinModel()
            name="Psychiatric Model",
            model_type=TwinModelType.PSYCHIATRIC,
            patient_id=self.patient_id
        (        )
        model2 = TwinModel()
            name="Biometric Model",
            model_type=TwinModelType.BIOMETRIC,
            patient_id=self.patient_id
        (        )
        model3 = TwinModel()
            name="Another Psychiatric Model",
            model_type=TwinModelType.PSYCHIATRIC,
            patient_id=self.patient_id
        (        )
        
        self.digital_twin.add_model(model1)
        self.digital_twin.add_model(model2)
        self.digital_twin.add_model(model3)
        
        # Get models by type
        psychiatric_models = self.digital_twin.get_models_by_type(TwinModelType.PSYCHIATRIC)
        biometric_models = self.digital_twin.get_models_by_type(TwinModelType.BIOMETRIC)
        custom_models = self.digital_twin.get_models_by_type(TwinModelType.CUSTOM)
        
        # Check the results
        self.assertEqual(len(psychiatric_models), 2)
        self.assertEqual(len(biometric_models), 1)
        self.assertEqual(len(custom_models), 0)
        
        self.assertIn(model1, psychiatric_models)
        self.assertIn(model3, psychiatric_models)
        self.assertIn(model2, biometric_models)
        
        @pytest.mark.standalone()
        def test_generate_biometric_alert_rules(self):
        """Test generating biometric alert rules."""
        # Create and add a biometric model
        model = BiometricTwinModel()
            name="Heart Rate Model",
            patient_id=self.patient_id,
            biometric_types=[BiometricDataType.HEART_RATE, BiometricDataType.BLOOD_PRESSURE]
        (        )
        self.digital_twin.add_model(model)
        
        # Generate alert rules
        rules_info = self.digital_twin.generate_biometric_alert_rules()
        
        # Check the results
        self.assertEqual(rules_info["models_updated"], 1)
        self.assertGreater(rules_info["generated_rules_count"], 0)
        self.assertIn(BiometricDataType.BLOOD_PRESSURE.value, rules_info["rules_by_type"])
        self.assertIn(BiometricDataType.BLOOD_PRESSURE.value, rules_info["rules_by_type"])
        
        # Check that rules were added to the model
        self.assertGreater(len(model.alert_rules), 0)
        
        @pytest.mark.standalone()
        def test_process_biometric_data(self):
        """Test processing biometric data."""
        # Create and add a biometric model
        model = BiometricTwinModel()
            name="Heart Rate Model",
            patient_id=self.patient_id,
            biometric_types=[BiometricDataType.HEART_RATE]
        (        )
        self.digital_twin.add_model(model)
        
        # Add alert rules
        high_hr_rule = {
        "name": "High Heart Rate",
        "biometric_type": BiometricDataType.HEART_RATE.value,
        "operator": ">",
        "threshold": 100,
        "severity": "medium"
    }
    model.add_alert_rule(high_hr_rule)
        
        # Create test data points
    data_points = [
    {
    "type": BiometricDataType.HEART_RATE.value,
    "value": 120,  # Should trigger the alert
    "timestamp": datetime.now().isoformat()
    },
    {
    "type": BiometricDataType.HEART_RATE.value,
    "value": 80,  # Should not trigger the alert
    "timestamp": datetime.now().isoformat()
    }
    ]
        
        # Process the data
    results = self.digital_twin.process_biometric_data(data_points)
        
        # Check the results
    self.assertEqual(results["processed_points"], 2)
    self.assertEqual(results["alerts_generated"], 1)
    self.assertEqual(len(results["alerts"]), 1)
        
    alert = results["alerts"][0]
    self.assertEqual(alert["patient_id"], self.patient_id)
    self.assertEqual(alert["biometric_type"], BiometricDataType.HEART_RATE.value)
    self.assertEqual(alert["value"], 120)
    self.assertEqual(alert["threshold"], 100)
    self.assertEqual(alert["operator"], ">")
        
    @pytest.mark.standalone()
    def test_predict_symptoms(self):
        """Test predicting symptoms."""
        # Create and add a time series model
        model = TimeSeriesModel()
            name="Heart Rate Prediction",
            patient_id=self.patient_id,
            data_type=BiometricDataType.HEART_RATE,
            prediction_interval=PredictionInterval.DAILY,
            forecast_horizon=7
        (        )
        self.digital_twin.add_model(model)
        
        # Predict symptoms
        predictions = self.digital_twin.predict_symptoms(horizon_days=5)
        
        # Check the results
        self.assertEqual(len(predictions), 1)
        self.assertIn(model.id, predictions)
        
        model_predictions = predictions[model.id]
        self.assertEqual(model_predictions["model_name"], model.name)
        self.assertEqual(model_predictions["data_type"], BiometricDataType.HEART_RATE.value)
        self.assertEqual(len(model_predictions["predictions"]), 5)  # 5 days of predictions
        
        # Check that the forecast horizon was reset
        self.assertEqual(model.forecast_horizon, 7)
        
        @pytest.mark.standalone()
        def test_to_dict(self):
        """Test converting to dictionary."""
        # Create and add a model
        model = TwinModel()
            name="Test Model",
            model_type=TwinModelType.PSYCHIATRIC,
            patient_id=self.patient_id
        (        )
        self.digital_twin.add_model(model)
        
        # Convert to dictionary
        twin_dict = self.digital_twin.to_dict()
        
        # Check the dictionary
        self.assertEqual(twin_dict["patient_id"], self.patient_id)
        self.assertEqual(twin_dict["name"], self.digital_twin.name)
        self.assertEqual(twin_dict["version"], "1.0.0")
        self.assertIn(model.id, twin_dict["models"])
        self.assertEqual(twin_dict["models"][model.id]["name"], model.name)


        class TestTimeSeriesModel(unittest.TestCase):
    """Test the TimeSeriesModel class."""
    
    def setUp(self):
        """Set up for each test."""
        self.patient_id = "patient123"
        self.model = TimeSeriesModel()
            name="Heart Rate Prediction",
            patient_id=self.patient_id,
            data_type=BiometricDataType.HEART_RATE,
            prediction_interval=PredictionInterval.DAILY,
            forecast_horizon=7
        (        )
        
        @pytest.mark.standalone()
        def test_creation(self):
        """Test creating a TimeSeriesModel."""
        # Check basic attributes
        self.assertEqual(self.model.name, "Heart Rate Prediction")
        self.assertEqual(self.model.patient_id, self.patient_id)
        self.assertEqual(self.model.data_type, BiometricDataType.HEART_RATE)
        self.assertEqual(self.model.prediction_interval, PredictionInterval.DAILY)
        self.assertEqual(self.model.forecast_horizon, 7)
        self.assertEqual(self.model.lookback_window, 7)
        self.assertIsNone(self.model.last_trained)
        self.assertEqual(self.model.performance_metrics, {})
        
        # Check creation with a string data type
        string_model = TimeSeriesModel()
        name="Custom Prediction",
        patient_id=self.patient_id,
        data_type="custom_data_type",
        prediction_interval=PredictionInterval.WEEKLY
        (    )
        self.assertEqual(string_model.data_type, BiometricDataType.CUSTOM)
        self.assertEqual(string_model.prediction_interval, PredictionInterval.WEEKLY)
        
        @pytest.mark.standalone()
        def test_train(self):
        """Test training the model."""
        # Create sample data
        data = [
            {"timestamp": "2025-01-01T00:00:00", "value": 70},
            {"timestamp": "2025-01-02T00:00:00", "value": 75},
            {"timestamp": "2025-01-03T00:00:00", "value": 72},
            {"timestamp": "2025-01-04T00:00:00", "value": 68},
            {"timestamp": "2025-01-05T00:00:00", "value": 73}
        ]
        
        # Train the model
        metrics = self.model.train(data)
        
        # Check the results
        self.assertIsNotNone(self.model.last_trained)
        self.assertEqual(self.model.performance_metrics, metrics)
        self.assertIn("mae", metrics)
        self.assertIn("rmse", metrics)
        self.assertIn("r2", metrics)
        
        @pytest.mark.standalone()
        def test_predict(self):
        """Test generating predictions."""
        # Generate predictions
        predictions = self.model.predict()
        
        # Check the results
        self.assertEqual(len(predictions), 7)  # 7 days of predictions
        
        first_prediction = predictions[0]
        self.assertIn("timestamp", first_prediction)
        self.assertIn("value", first_prediction)
        self.assertIn("confidence", first_prediction)
        self.assertEqual(first_prediction["data_type"], BiometricDataType.HEART_RATE.value)
        
        # Check that predictions have different timestamps
        timestamps = [p["timestamp"] for p in predictions]
        self.assertEqual(len(set(timestamps)), 7)  # All timestamps should be unique
        
        # Check with different prediction interval
        model = TimeSeriesModel()
        name="Hourly Prediction",
        patient_id=self.patient_id,
        data_type=BiometricDataType.HEART_RATE,
        prediction_interval=PredictionInterval.HOURLY,
        forecast_horizon=5
        (    )
        hourly_predictions = model.predict()
        
        # Check the results
        self.assertEqual(len(hourly_predictions), 5)  # 5 hours of predictions
        
        @pytest.mark.standalone()
        def test_to_dict(self):
        """Test converting to dictionary."""
        # Train the model to populate performance metrics
        data = [
            {"timestamp": "2025-01-01T00:00:00", "value": 70},
            {"timestamp": "2025-01-02T00:00:00", "value": 75}
        ]
        self.model.train(data)
        
        # Convert to dictionary
        model_dict = self.model.to_dict()
        
        # Check the dictionary
        self.assertEqual(model_dict["name"], self.model.name)
        self.assertEqual(model_dict["model_type"], TwinModelType.SYMPTOM_PREDICTION.value)
        self.assertEqual(model_dict["patient_id"], self.patient_id)
        self.assertEqual(model_dict["data_type"], BiometricDataType.HEART_RATE.value)
        self.assertEqual(model_dict["prediction_interval"], PredictionInterval.DAILY.value)
        self.assertEqual(model_dict["forecast_horizon"], 7)
        self.assertEqual(model_dict["lookback_window"], 7)
        self.assertIsNotNone(model_dict["last_trained"])
        self.assertIn("performance_metrics", model_dict)


        class TestBiometricTwinModel(unittest.TestCase):
    """Test the BiometricTwinModel class."""
    
    def setUp(self):
        """Set up for each test."""
        self.patient_id = "patient123"
        self.model = BiometricTwinModel()
            name="Biometric Monitor",
            patient_id=self.patient_id,
            biometric_types=[BiometricDataType.HEART_RATE, BiometricDataType.BLOOD_PRESSURE]
        (        )
        
        @pytest.mark.standalone()
        def test_creation(self):
        """Test creating a BiometricTwinModel."""
        # Check basic attributes
        self.assertEqual(self.model.name, "Biometric Monitor")
        self.assertEqual(self.model.patient_id, self.patient_id)
        self.assertEqual(len(self.model.biometric_types), 2)
        self.assertEqual(self.model.biometric_types[0], BiometricDataType.HEART_RATE)
        self.assertEqual(self.model.biometric_types[1], BiometricDataType.BLOOD_PRESSURE)
        self.assertEqual(self.model.alert_rules, [])
        self.assertEqual(self.model.baseline_values, {})
        
        @pytest.mark.standalone()
        def test_add_alert_rule(self):
        """Test adding an alert rule."""
        # Create a rule
        rule = {
            "name": "High Heart Rate",
            "biometric_type": BiometricDataType.HEART_RATE.value,
            "operator": ">",
            "threshold": 100,
            "severity": "medium"
        }
        
        # Add the rule
    rule_id = self.model.add_alert_rule(rule)
        
        # Check the results
    self.assertEqual(len(self.model.alert_rules), 1)
    self.assertEqual(self.model.alert_rules[0]["name"], "High Heart Rate")
    self.assertEqual(self.model.alert_rules[0]["id"], rule_id)
        
    @pytest.mark.standalone()
    def test_remove_alert_rule(self):
        """Test removing an alert rule."""
        # Add a rule
        rule = {
            "name": "High Heart Rate",
            "biometric_type": BiometricDataType.HEART_RATE.value,
            "operator": ">",
            "threshold": 100
        }
        rule_id = self.model.add_alert_rule(rule)
        
        # Remove the rule
    result = self.model.remove_alert_rule(rule_id)
        
        # Check the results
    self.assertTrue(result)
    self.assertEqual(len(self.model.alert_rules), 0)
        
        # Try to remove a non-existent rule
    result = self.model.remove_alert_rule("non_existent_id")
        
        # Check the result
    self.assertFalse(result)
        
    @pytest.mark.standalone()
    def test_set_baseline(self):
        """Test setting a baseline value."""
        # Set a baseline
        self.model.set_baseline(BiometricDataType.HEART_RATE, 70)
        
        # Check the result
        self.assertEqual(self.model.baseline_values[BiometricDataType.HEART_RATE.value], 70)
        
        # Set a range baseline
        range_baseline = {"min": 60, "max": 100}
        self.model.set_baseline(BiometricDataType.BLOOD_PRESSURE, range_baseline)
        
        # Check the result
        self.assertEqual(self.model.baseline_values[BiometricDataType.BLOOD_PRESSURE.value], range_baseline)
        
        @pytest.mark.standalone()
        def test_process_biometric_data(self):
        """Test processing biometric data."""
        # Add alert rules
        high_hr_rule = {
            "name": "High Heart Rate",
            "biometric_type": BiometricDataType.HEART_RATE.value,
            "operator": ">",
            "threshold": 100,
            "severity": "medium"
        }
        self.model.add_alert_rule(high_hr_rule)
        
    low_hr_rule = {
    "name": "Low Heart Rate",
    "biometric_type": BiometricDataType.HEART_RATE.value,
    "operator": "<",
    "threshold": 50,
    "severity": "high"
    }
    self.model.add_alert_rule(low_hr_rule)
        
        # Create test data points
    high_hr_data = {
    "type": BiometricDataType.HEART_RATE.value,
    "value": 120,  # Should trigger the high HR alert
    "timestamp": datetime.now().isoformat()
    }
        
    normal_hr_data = {
    "type": BiometricDataType.HEART_RATE.value,
    "value": 70,  # Should not trigger any alerts
    "timestamp": datetime.now().isoformat()
    }
        
    low_hr_data = {
    "type": BiometricDataType.HEART_RATE.value,
    "value": 45,  # Should trigger the low HR alert
    "timestamp": datetime.now().isoformat()
    }
        
    bp_data = {
    "type": BiometricDataType.BLOOD_PRESSURE.value,
    "value": 130,  # No rules for BP, so no alerts
    "timestamp": datetime.now().isoformat()
    }
        
        # Process the data
    high_alerts = self.model.process_biometric_data(high_hr_data)
    normal_alerts = self.model.process_biometric_data(normal_hr_data)
    low_alerts = self.model.process_biometric_data(low_hr_data)
    bp_alerts = self.model.process_biometric_data(bp_data)
        
        # Check the results
    self.assertEqual(len(high_alerts), 1)
    self.assertEqual(len(normal_alerts), 0)
    self.assertEqual(len(low_alerts), 1)
    self.assertEqual(len(bp_alerts), 0)
        
        # Check the high HR alert
    high_alert = high_alerts[0]
    self.assertEqual(high_alert["rule_name"], "High Heart Rate")
    self.assertEqual(high_alert["biometric_type"], BiometricDataType.HEART_RATE.value)
    self.assertEqual(high_alert["value"], 120)
    self.assertEqual(high_alert["threshold"], 100)
    self.assertEqual(high_alert["operator"], ">")
    self.assertEqual(high_alert["severity"], "medium")
        
        # Check the low HR alert
    low_alert = low_alerts[0]
    self.assertEqual(low_alert["rule_name"], "Low Heart Rate")
    self.assertEqual(low_alert["biometric_type"], BiometricDataType.HEART_RATE.value)
    self.assertEqual(low_alert["value"], 45)
    self.assertEqual(low_alert["threshold"], 50)
    self.assertEqual(low_alert["operator"], "<")
    self.assertEqual(low_alert["severity"], "high")
        
    @pytest.mark.standalone()
    def test_to_dict(self):
        """Test converting to dictionary."""
        # Add a rule and baseline
        rule = {
            "name": "High Heart Rate",
            "biometric_type": BiometricDataType.HEART_RATE.value,
            "operator": ">",
            "threshold": 100
        }
        self.model.add_alert_rule(rule)
        self.model.set_baseline(BiometricDataType.HEART_RATE, 70)
        
        # Convert to dictionary
    model_dict = self.model.to_dict()
        
        # Check the dictionary
    self.assertEqual(model_dict["name"], self.model.name)
    self.assertEqual(model_dict["model_type"], TwinModelType.BIOMETRIC.value)
    self.assertEqual(model_dict["patient_id"], self.patient_id)
    self.assertEqual(model_dict["biometric_types"], [BiometricDataType.HEART_RATE.value, BiometricDataType.BLOOD_PRESSURE.value])
    self.assertEqual(len(model_dict["alert_rules"]), 1)
    self.assertEqual(model_dict["alert_rules"][0]["name"], "High Heart Rate")
    self.assertEqual(model_dict["baseline_values"][BiometricDataType.HEART_RATE.value], 70)


if __name__ == "__main__":
    unittest.main()