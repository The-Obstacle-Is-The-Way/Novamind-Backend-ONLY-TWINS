# -*- coding: utf-8 -*-
"""
Mock Digital Twin Service Implementation.

This module provides a mock implementation of the Digital Twin service
for development and testing purposes.
"""

import uuid
from typing import Any, Dict, List, Optional

from app.core.services.ml.interface import DigitalTwinInterface
from app.core.exceptions import (
    InvalidConfigurationError,
    InvalidRequestError,
    ServiceUnavailableError,
    ResourceNotFoundError
)
from app.core.utils.logging import get_logger

logger = get_logger(__name__)

class MockDigitalTwinService(DigitalTwinInterface):
    """
    Mock implementation of the Digital Twin service.
    Simulates twin creation, status checks, updates, insights, and interactions.
    """

    def __init__(self) -> None:
        """Initialize the mock service."""
        self._initialized = False
        self._config: Dict[str, Any] = {}
        self._twins: Dict[str, Dict[str, Any]] = {} # Store mock twin data

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the mock service with configuration.

        Args:
            config: Configuration dictionary (can be empty for mock).
        """
        try:
            self._config = config or {}
            self._initialized = True
            logger.info("Mock Digital Twin service initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize mock Digital Twin service: {e}", exc_info=True)
            self._initialized = False
            raise InvalidConfigurationError(f"Failed to initialize mock Digital Twin service: {e}")

    def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        return self._initialized

    def shutdown(self) -> None:
        """Shutdown the mock service."""
        self._initialized = False
        self._twins.clear()
        logger.info("Mock Digital Twin service shut down.")

    def create_digital_twin(self, patient_id: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock creation of a new digital twin for a patient.

        Args:
            patient_id: The ID of the patient.
            initial_data: Initial data to populate the twin.

        Returns:
            A dictionary containing the status and ID of the created twin.
        """
        if not self._initialized:
            raise ServiceUnavailableError("Mock Digital Twin service is not initialized.")
        if not patient_id:
            raise InvalidRequestError("Patient ID cannot be empty.")

        twin_id = f"mock_twin_{uuid.uuid4()}"
        self._twins[twin_id] = {
            "patient_id": patient_id,
            "status": "active",
            "data": initial_data or {},
            "insights_cache": {},
            "interaction_history": []
        }
        logger.info(f"Mock digital twin created for patient {patient_id} with ID {twin_id}")
        return {"twin_id": twin_id, "status": "created"}

    def get_twin_status(self, twin_id: str) -> Dict[str, Any]:
        """
        Get the mock status of a digital twin.

        Args:
            twin_id: The ID of the digital twin.

        Returns:
            A dictionary containing the status information.
        """
        if not self._initialized:
            raise ServiceUnavailableError("Mock Digital Twin service is not initialized.")

        twin = self._twins.get(twin_id)
        if not twin:
            raise ResourceNotFoundError(f"Mock digital twin with ID {twin_id} not found.")

        return {"twin_id": twin_id, "status": twin.get("status", "unknown"), "patient_id": twin.get("patient_id")}

    def update_twin_data(self, twin_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock update of the data associated with a digital twin.

        Args:
            twin_id: The ID of the digital twin.
            data: The data to update.

        Returns:
            A dictionary confirming the update status.
        """
        if not self._initialized:
            raise ServiceUnavailableError("Mock Digital Twin service is not initialized.")
        if not data:
            raise InvalidRequestError("Update data cannot be empty.")

        twin = self._twins.get(twin_id)
        if not twin:
            raise ResourceNotFoundError(f"Mock digital twin with ID {twin_id} not found.")

        twin["data"].update(data)
        # Invalidate cache on update
        twin["insights_cache"] = {}
        logger.info(f"Mock digital twin data updated for twin ID {twin_id}")
        return {"twin_id": twin_id, "status": "updated"}

    def get_insights(self, twin_id: str, insight_types: List[str]) -> Dict[str, Any]:
        """
        Generate mock insights from the digital twin's data.

        Args:
            twin_id: The ID of the digital twin.
            insight_types: A list of specific insight types to generate.

        Returns:
            A dictionary containing the requested mock insights.
        """
        if not self._initialized:
            raise ServiceUnavailableError("Mock Digital Twin service is not initialized.")
        if not insight_types:
            raise InvalidRequestError("Insight types list cannot be empty.")

        twin = self._twins.get(twin_id)
        if not twin:
            raise ResourceNotFoundError(f"Mock digital twin with ID {twin_id} not found.")

        insights: Dict[str, Any] = {}
        for insight_type in insight_types:
            # Check cache first
            if insight_type in twin["insights_cache"]:
                insights[insight_type] = twin["insights_cache"][insight_type]
                continue

            # Generate mock insight if not cached
            mock_insight_data: Any
            if insight_type == "mood_trend":
                mock_insight_data = {"trend": "stable", "average_score": 0.6, "confidence": 0.8}
            elif insight_type == "risk_prediction":
                mock_insight_data = {"level": "low", "factors": ["stress", "sleep"], "confidence": 0.75}
            elif insight_type == "treatment_effectiveness":
                 mock_insight_data = {"medication_X": "effective", "therapy_Y": "partially_effective", "confidence": 0.82}
            else:
                mock_insight_data = {"summary": f"Mock insight for {insight_type}", "confidence": 0.9}

            insights[insight_type] = mock_insight_data
            # Cache the generated insight
            twin["insights_cache"][insight_type] = mock_insight_data

        logger.info(f"Generated mock insights for twin ID {twin_id}: {list(insights.keys())}")
        return {"twin_id": twin_id, "insights": insights}

    def interact(self, twin_id: str, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Mock interaction with the digital twin.

        Args:
            twin_id: The ID of the digital twin.
            query: The interaction query or command.
            context: Optional context for the interaction.

        Returns:
            A dictionary containing the mock result of the interaction.
        """
        if not self._initialized:
            raise ServiceUnavailableError("Mock Digital Twin service is not initialized.")
        if not query:
            raise InvalidRequestError("Query cannot be empty.")

        twin = self._twins.get(twin_id)
        if not twin:
            raise ResourceNotFoundError(f"Mock digital twin with ID {twin_id} not found.")

        # Generate a simple mock response based on the query
        response_text = f"Mock response to query: '{query}'. Context provided: {bool(context)}"
        mock_result = {
            "response": response_text,
            "confidence": 0.95,
            "metadata": {"interaction_type": "query_response"}
        }

        # Log interaction
        twin["interaction_history"].append({"query": query, "response": response_text})
        logger.info(f"Mock interaction with twin ID {twin_id}. Query: '{query}'")

        return {"twin_id": twin_id, "interaction_result": mock_result}