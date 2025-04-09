# -*- coding: utf-8 -*-
"""
Machine Learning Service Interface for NOVAMIND.

This module defines the interfaces for ML services following Clean Architecture
principles, ensuring that the domain layer remains independent of infrastructure
implementations while enabling access to ML capabilities.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


class SymptomForecastingInterface(ABC):
    """Interface for symptom forecasting ML services."""

    @abstractmethod
    async def forecast_symptoms(
        self,
        patient_id: UUID,
        symptom_history: List[Dict[str, Any]],
        forecast_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Forecast patient symptoms based on historical data.

        Args:
            patient_id: UUID of the patient
            symptom_history: List of historical symptom records
            forecast_days: Number of days to forecast

        Returns:
            Dictionary containing forecast results
        """
        pass

    @abstractmethod
    async def detect_symptom_patterns(
        self, patient_id: UUID, symptom_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect patterns in patient symptom history.

        Args:
            patient_id: UUID of the patient
            symptom_history: List of historical symptom records

        Returns:
            Dictionary containing pattern detection results
        """
        pass

    @abstractmethod
    async def get_model_status(self, patient_id: UUID) -> Dict[str, Any]:
        """
        Get the status of a patient's symptom forecasting model.

        Args:
            patient_id: UUID of the patient

        Returns:
            Dictionary containing model status
        """
        pass


class BiometricCorrelationInterface(ABC):
    """Interface for biometric correlation ML services."""

    @abstractmethod
    async def analyze_correlations(
        self,
        patient_id: UUID,
        biometric_data: List[Dict[str, Any]],
        mental_health_indicators: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Analyze correlations between biometric data and mental health indicators.

        Args:
            patient_id: UUID of the patient
            biometric_data: List of biometric data records
            mental_health_indicators: List of mental health indicator records

        Returns:
            Dictionary containing correlation analysis results
        """
        pass

    @abstractmethod
    async def detect_anomalies(
        self,
        patient_id: UUID,
        biometric_data: List[Dict[str, Any]],
        mental_health_indicators: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Detect anomalies in biometric data and mental health indicators.

        Args:
            patient_id: UUID of the patient
            biometric_data: List of biometric data records
            mental_health_indicators: List of mental health indicator records

        Returns:
            Dictionary containing anomaly detection results
        """
        pass

    @abstractmethod
    async def get_model_status(self, patient_id: UUID) -> Dict[str, Any]:
        """
        Get the status of a patient's biometric correlation model.

        Args:
            patient_id: UUID of the patient

        Returns:
            Dictionary containing model status
        """
        pass


class PharmacogenomicsInterface(ABC):
    """Interface for pharmacogenomics ML services."""

    @abstractmethod
    async def predict_medication_responses(
        self,
        patient_id: UUID,
        patient_data: Dict[str, Any],
        medications: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Predict patient responses to psychiatric medications.

        Args:
            patient_id: UUID of the patient
            patient_data: Patient data including genetic markers
            medications: Optional list of medications to predict (defaults to all)

        Returns:
            Dictionary containing prediction results
        """
        pass

    @abstractmethod
    async def analyze_gene_medication_interactions(
        self, patient_id: UUID, patient_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze interactions between patient's genetic markers and medications.

        Args:
            patient_id: UUID of the patient
            patient_data: Patient data including genetic markers

        Returns:
            Dictionary containing interaction analysis
        """
        pass

    @abstractmethod
    async def predict_side_effects(
        self, patient_id: UUID, patient_data: Dict[str, Any], medications: List[str]
    ) -> Dict[str, Any]:
        """
        Predict potential side effects for specified medications.

        Args:
            patient_id: UUID of the patient
            patient_data: Patient data including genetic markers
            medications: List of medications to predict side effects for

        Returns:
            Dictionary containing side effect predictions
        """
        pass

    @abstractmethod
    async def recommend_treatment_plan(
        self,
        patient_id: UUID,
        patient_data: Dict[str, Any],
        diagnosis: str,
        current_medications: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Recommend a personalized treatment plan based on genetic markers and diagnosis.

        Args:
            patient_id: UUID of the patient
            patient_data: Patient data including genetic markers
            diagnosis: Patient diagnosis
            current_medications: Optional list of current medications

        Returns:
            Dictionary containing treatment recommendations
        """
        pass


class DigitalTwinServiceInterface(ABC):
    """Interface for Digital Twin integration services."""

    @abstractmethod
    async def generate_comprehensive_patient_insights(
        self, patient_id: UUID, patient_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive insights for a patient using all ML services.

        Args:
            patient_id: UUID of the patient
            patient_data: Comprehensive patient data

        Returns:
            Dictionary containing comprehensive insights
        """
        pass

    @abstractmethod
    async def update_digital_twin(
        self, patient_id: UUID, patient_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update the Digital Twin with new patient data.

        Args:
            patient_id: UUID of the patient
            patient_data: New patient data

        Returns:
            Dictionary containing update results
        """
        pass

    @abstractmethod
    async def get_digital_twin_status(self, patient_id: UUID) -> Dict[str, Any]:
        """
        Get the status of a patient's Digital Twin.

        Args:
            patient_id: UUID of the patient

        Returns:
            Dictionary containing Digital Twin status
        """
        pass
