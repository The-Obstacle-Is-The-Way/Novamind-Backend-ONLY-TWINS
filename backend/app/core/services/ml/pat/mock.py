"""
Mock implementation of the PAT service.

This module provides a mock implementation of the Patient Activity Tracking (PAT)
service for development, testing, and demonstration purposes.
"""

import json
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from app.core.services.ml.pat.base import PATBase
from app.core.services.ml.pat.exceptions import (
    AnalysisError,
    AuthorizationError,
    EmbeddingError,
    InitializationError,
    ResourceNotFoundError,
    ValidationError,
)


class MockPAT(PATBase):
    """Mock implementation of the PAT service for testing and development."""

    def __init__(self) -> None:
        """Initialize the MockPAT service."""
        self._initialized = False
        self._configured = False
        self._model_id = "mock-model-v1"
        self._s3_bucket = "mock-s3-bucket"
        self._dynamodb_table = "mock-dynamodb-table"
        self._delay_ms = 0
        
    @property
    def configured(self) -> bool:
        """Get whether the service is configured."""
        return self._configured
        
    @property
    def delay_ms(self) -> int:
        """Get the configured delay in milliseconds."""
        return self._delay_ms
        self._data_store = {
            "analyses": {},
            "embeddings": {},
            "integrations": {},
            "patient_analyses": {},
        }

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the service with configuration parameters.
        
        Args:
            config: Configuration parameters
                - pat_s3_bucket: S3 bucket name for storage
                - pat_dynamodb_table: DynamoDB table name for metadata
                - pat_bedrock_model_id: Bedrock model ID
                
        Raises:
            InitializationError: If required configuration is missing
        """
        # In mock implementation, these configs are optional with defaults
        self._s3_bucket = config.get("pat_s3_bucket", "mock-s3-bucket")
        self._dynamodb_table = config.get("pat_dynamodb_table", "mock-dynamodb-table")
        self._model_id = config.get("pat_bedrock_model_id", "mock-model-v1")
        
        # Optional delay for simulating latency
        self._delay_ms = config.get("delay_ms", 0)
        
        # Add simulated delay for testing
        if self._delay_ms > 0:
            import time
            time.sleep(self._delay_ms / 1000.0)
            
        # Mark as initialized
        self._initialized = True
        self._configured = True

    def _validate_initialized(self) -> None:
        """Validate that the service is initialized.
        
        Raises:
            InitializationError: If the service is not initialized
        """
        if not self._initialized:
            raise InitializationError("Service is not initialized")

    def analyze_actigraphy(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float,
        device_info: Dict[str, Any],
        analysis_types: List[str],
    ) -> Dict[str, Any]:
        """Analyze actigraphy data to extract insights.
        
        Args:
            patient_id: Unique patient identifier
            readings: List of actigraphy readings, each with timestamp and x,y,z values
            start_time: ISO-8601 timestamp for start of data collection
            end_time: ISO-8601 timestamp for end of data collection
            sampling_rate_hz: Data sampling rate in Hz
            device_info: Information about the recording device
            analysis_types: List of analysis types to perform
            
        Returns:
            A dictionary containing analysis results
            
        Raises:
            ValidationError: If input validation fails
            AnalysisError: If analysis fails for any reason
        """
        self._validate_initialized()
        
        # Validate inputs
        if not patient_id:
            raise ValidationError("patient_id is required")
            
        if len(readings) < 10:
            raise ValidationError("At least 10 readings are required")
            
        if not analysis_types:
            raise ValidationError("At least one analysis_type is required")
            
        invalid_types = [t for t in analysis_types if t not in ["sleep", "activity", "stress", "movement"]]
        if invalid_types:
            raise ValidationError(f"Invalid analysis types: {', '.join(invalid_types)}")
        
        # Create analysis ID
        analysis_id = f"analysis_{uuid.uuid4()}"
        created_at = datetime.now(timezone.utc).isoformat()
        
        # Generate mock results
        results = {}
        
        if "sleep" in analysis_types:
            results["sleep"] = {
                "efficiency": random.uniform(70, 95),
                "duration_hours": random.uniform(5, 9),
                "deep_sleep_percentage": random.uniform(10, 30),
                "rem_sleep_percentage": random.uniform(20, 30),
                "light_sleep_percentage": random.uniform(40, 60),
                "awake_minutes": random.uniform(10, 60),
                "sleep_score": random.uniform(50, 100),
                "sleep_onset_minutes": random.uniform(5, 30),
            }
            
        if "activity" in analysis_types:
            results["activity"] = {
                "active_minutes": random.uniform(30, 300),
                "sedentary_minutes": random.uniform(300, 900),
                "steps": random.randint(2000, 15000),
                "distance_km": random.uniform(1, 12),
                "calories_burned": random.uniform(1000, 3000),
                "activity_score": random.uniform(50, 100),
            }
            
        if "stress" in analysis_types:
            results["stress"] = {
                "average_stress_level": random.uniform(1, 5),
                "peak_stress_level": random.uniform(3, 5),
                "stress_duration_minutes": random.uniform(10, 300),
                "recovery_periods": random.randint(1, 10),
                "stress_score": random.uniform(50, 100),
            }
            
        if "movement" in analysis_types:
            results["movement"] = {
                "movement_intensity": [random.uniform(0, 5) for _ in range(24)],
                "movement_consistency": random.uniform(0, 1),
                "restlessness_index": random.uniform(0, 100),
                "movement_score": random.uniform(50, 100),
            }
        
        # Create analysis record
        analysis = {
            "analysis_id": analysis_id,
            "patient_id": patient_id,
            "created_at": created_at,
            "start_time": start_time,
            "end_time": end_time,
            "sampling_rate_hz": sampling_rate_hz,
            "device_info": device_info,
            "analysis_types": analysis_types,
            "results": results,
            "model_version": "mock-model-1.0.0",
        }
        
        # Store analysis
        self._data_store["analyses"][analysis_id] = analysis
        
        # Store patient analysis index
        if patient_id not in self._data_store["patient_analyses"]:
            self._data_store["patient_analyses"][patient_id] = []
        self._data_store["patient_analyses"][patient_id].append({
            "analysis_id": analysis_id,
            "created_at": created_at,
            "analysis_types": analysis_types
        })
        
        return analysis

    def get_actigraphy_embeddings(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float,
    ) -> Dict[str, Any]:
        """Generate embeddings from actigraphy data for similarity comparison.
        
        Args:
            patient_id: Unique patient identifier
            readings: List of actigraphy readings, each with timestamp and x,y,z values
            start_time: ISO-8601 timestamp for start of data collection
            end_time: ISO-8601 timestamp for end of data collection
            sampling_rate_hz: Data sampling rate in Hz
            
        Returns:
            A dictionary containing embedding vector and metadata
            
        Raises:
            ValidationError: If input validation fails
            EmbeddingError: If embedding generation fails
        """
        self._validate_initialized()
        
        # Validate inputs
        if not patient_id:
            raise ValidationError("patient_id is required")
            
        if len(readings) < 10:
            raise ValidationError("At least 10 readings are required")
        
        # Create embedding ID
        embedding_id = f"embedding_{uuid.uuid4()}"
        created_at = datetime.now(timezone.utc).isoformat()
        
        # Generate mock embedding vector
        dimensions = 64
        embedding = [random.uniform(-1, 1) for _ in range(dimensions)]
        
        # Create embedding record
        embedding_record = {
            "embedding_id": embedding_id,
            "patient_id": patient_id,
            "created_at": created_at,
            "start_time": start_time,
            "end_time": end_time,
            "sampling_rate_hz": sampling_rate_hz,
            "embedding": embedding,
            "dimensions": dimensions,
            "model_version": "test-model-1.0.0",
        }
        
        # Store embedding
        self._data_store["embeddings"][embedding_id] = embedding_record
        
        return embedding_record

    def get_analysis_by_id(self, analysis_id: str) -> Dict[str, Any]:
        """Retrieve an analysis by its ID.
        
        Args:
            analysis_id: The ID of the analysis to retrieve
            
        Returns:
            The analysis record
            
        Raises:
            ResourceNotFoundError: If the analysis is not found
        """
        self._validate_initialized()
        
        if analysis_id not in self._data_store["analyses"]:
            raise ResourceNotFoundError(f"Analysis with ID {analysis_id} not found")
            
        return self._data_store["analyses"][analysis_id]

    def get_patient_analyses(
        self, patient_id: str, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """Retrieve analyses for a patient.
        
        Args:
            patient_id: The patient's ID
            limit: Maximum number of analyses to return
            offset: Starting index for pagination
            
        Returns:
            Dictionary with analyses and pagination metadata
        """
        self._validate_initialized()
        
        if patient_id not in self._data_store["patient_analyses"]:
            return {
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False
            }
            
        analyses = self._data_store["patient_analyses"][patient_id]
        total = len(analyses)
        
        # Sort by created_at in descending order
        sorted_analyses = sorted(
            analyses, 
            key=lambda x: x["created_at"], 
            reverse=True
        )
        
        # Apply pagination
        paginated = sorted_analyses[offset:offset + limit]
        
        return {
            "items": paginated,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the underlying model.
        
        Returns:
            Dictionary with model information
        """
        self._validate_initialized()
        
        return {
            "name": "MockPAT",
            "model_id": self._model_id,
            "s3_bucket": self._s3_bucket,
            "dynamodb_table": self._dynamodb_table,
            "capabilities": [
                "Sleep analysis",
                "Activity analysis",
                "Stress analysis",
                "Movement analysis",
                "Digital twin integration"
            ],
            "input_format": {
                "readings": "List of x,y,z accelerometer readings with timestamps",
                "sampling_rate": "Frequency in Hz",
                "analysis_types": ["sleep", "activity", "stress", "movement"]
            }
        }

    def integrate_with_digital_twin(
        self, patient_id: str, profile_id: str, analysis_id: str
    ) -> Dict[str, Any]:
        """Integrate actigraphy analysis with a digital twin profile.
        
        Args:
            patient_id: Patient ID
            profile_id: Digital twin profile ID
            analysis_id: Analysis ID to integrate
            
        Returns:
            Dictionary with integration results
            
        Raises:
            ResourceNotFoundError: If the analysis is not found
            AuthorizationError: If the analysis doesn't belong to the patient
        """
        self._validate_initialized()
        
        # Validate analysis exists
        try:
            analysis = self.get_analysis_by_id(analysis_id)
        except ResourceNotFoundError:
            raise ResourceNotFoundError(f"Analysis with ID {analysis_id} not found")
            
        # Validate patient ownership
        if analysis["patient_id"] != patient_id:
            raise AuthorizationError("Analysis does not belong to the patient")
            
        # Create integration ID
        integration_id = f"integration_{uuid.uuid4()}"
        created_at = datetime.now(timezone.utc).isoformat()
        
        # Generate mock integration results
        integration = {
            "integration_id": integration_id,
            "patient_id": patient_id,
            "profile_id": profile_id,
            "analysis_id": analysis_id,
            "created_at": created_at,
            "status": "completed",
            "insights_added": random.randint(3, 8),
            "profile_update_summary": {
                "sleep_pattern_updated": True,
                "activity_level_updated": True,
                "stress_indicators_updated": "stress" in analysis["analysis_types"],
                "movement_patterns_updated": "movement" in analysis["analysis_types"],
            }
        }
        
        # Store integration
        self._data_store["integrations"][integration_id] = integration
        
        return integration