# -*- coding: utf-8 -*-
"""
Application Configuration for NOVAMIND.

This module configures the main application components and dependencies,
following Clean Architecture principles and ensuring proper separation of concerns.
"""

import os
from typing import Any, Dict

from app.domain.repositories.digital_twin_repository import DigitalTwinRepository
from app.domain.repositories.patient_repository import PatientRepository
from app.domain.services.digital_twin_service import DigitalTwinService
from app.infrastructure.config.ml_service_config import MLServiceConfig
from app.infrastructure.database.database_config import DatabaseConfig
from app.infrastructure.repositories.digital_twin_repository_impl import (
    DigitalTwinRepositoryImpl,
)
from app.infrastructure.repositories.patient_repository_impl import (
    PatientRepositoryImpl,
)


class AppConfig:
    """
    Main application configuration.

    This class provides factory methods for creating application components,
    following the dependency injection pattern to ensure proper separation of
    concerns and testability.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the application configuration.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Create database configuration
        self.db_config = DatabaseConfig(config.get("database", {}))

        # Create ML service configuration
        self.ml_config = MLServiceConfig(config.get("ml_services", {}))

    def create_digital_twin_repository(self) -> DigitalTwinRepository:
        """
        Create a digital twin repository.

        Returns:
            Digital twin repository
        """
        return DigitalTwinRepositoryImpl(
            db_session_factory=self.db_config.create_session_factory()
        )

    def create_patient_repository(self) -> PatientRepository:
        """
        Create a patient repository.

        Returns:
            Patient repository
        """
        return PatientRepositoryImpl(
            db_session_factory=self.db_config.create_session_factory()
        )

    def create_digital_twin_service(self) -> DigitalTwinService:
        """
        Create a digital twin service.

        Returns:
            Digital twin service
        """
        # Create repositories
        digital_twin_repo = self.create_digital_twin_repository()
        patient_repo = self.create_patient_repository()

        # Create ML service adapters
        adapters = self.ml_config.create_all_adapters()

        # Create digital twin service
        return DigitalTwinService(
            digital_twin_repository=digital_twin_repo,
            patient_repository=patient_repo,
            digital_twin_service=adapters["digital_twin"],
            symptom_forecasting_service=adapters["symptom_forecasting"],
            biometric_correlation_service=adapters["biometric_correlation"],
            pharmacogenomics_service=adapters["pharmacogenomics"],
        )

    def create_application(self) -> Dict[str, Any]:
        """
        Create the main application components.

        Returns:
            Dictionary containing application components
        """
        return {
            "digital_twin_service": self.create_digital_twin_service(),
            # Add other services as needed
        }
