# -*- coding: utf-8 -*-
"""
ML Service Interfaces.

This module defines the interfaces for ML services used in the application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class BaseMLInterface(ABC):
    """Base interface for all ML services."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the service with configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if the service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        pass


class MentaLLaMAInterface(BaseMLInterface):
    """Interface for MentaLLaMA ML services."""
    
    @abstractmethod
    def process(
        self, 
        text: str,
        model_type: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process text using the MentaLLaMA model.
        
        Args:
            text: Text to process
            model_type: Type of model to use
            options: Additional processing options
            
        Returns:
            Processing results
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If text is empty or invalid
            ModelNotFoundError: If model type is not found
        """
        pass
    
    @abstractmethod
    def detect_depression(
        self, 
        text: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect depression signals in text.
        
        Args:
            text: Text to analyze
            options: Additional processing options
            
        Returns:
            Depression detection results
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If text is empty or invalid
        """
        pass
    
    @abstractmethod
    def assess_risk(
        self, 
        text: str,
        risk_type: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assess risk in text.
        
        Args:
            text: Text to analyze
            risk_type: Type of risk to assess (suicide, self-harm, violence, etc.)
            options: Additional processing options
            
        Returns:
            Risk assessment results
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If text is empty or invalid
        """
        pass
    
    @abstractmethod
    def analyze_sentiment(
        self, 
        text: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment in text.
        
        Args:
            text: Text to analyze
            options: Additional processing options
            
        Returns:
            Sentiment analysis results
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If text is empty or invalid
        """
        pass
    
    @abstractmethod
    def analyze_wellness_dimensions(
        self, 
        text: str,
        dimensions: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze wellness dimensions in text.
        
        Args:
            text: Text to analyze
            dimensions: List of dimensions to analyze
            options: Additional processing options
            
        Returns:
            Wellness dimensions analysis results
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If text is empty or invalid
        """
        pass
    
    @abstractmethod
    def generate_digital_twin(
        self,
        patient_id: str,
        patient_data: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate or update a digital twin model for a patient.
        
        Args:
            patient_id: ID of the patient
            patient_data: Additional patient data
            options: Additional generation options
            
        Returns:
            Digital twin model data and metrics
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If patient ID is invalid
        """
        pass
    
    @abstractmethod
    def create_digital_twin_session(
        self,
        therapist_id: str,
        patient_id: Optional[str] = None,
        session_type: Optional[str] = None,
        session_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Digital Twin session.
        
        Args:
            therapist_id: ID of the therapist
            patient_id: ID of the patient (optional for anonymous sessions)
            session_type: Type of session (therapy, assessment, coaching)
            session_params: Additional session parameters
            
        Returns:
            Dict containing session information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If request is invalid
        """
        pass
    
    @abstractmethod
    def get_digital_twin_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about a Digital Twin session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dict containing session information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If session ID is invalid
            ModelNotFoundError: If session not found
        """
        pass
    
    @abstractmethod
    def send_message_to_session(
        self,
        session_id: str,
        message: str,
        sender_type: Optional[str] = None,
        sender_id: Optional[str] = None,
        message_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a Digital Twin session.
        
        Args:
            session_id: ID of the session
            message: Message content
            sender_type: Type of sender (user, therapist, system)
            sender_id: ID of the sender
            message_params: Additional message parameters
            
        Returns:
            Dict containing message information and Digital Twin's response
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If request is invalid
            ModelNotFoundError: If session not found
        """
        pass
    
    @abstractmethod
    def end_digital_twin_session(
        self,
        session_id: str,
        end_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End a Digital Twin session.
        
        Args:
            session_id: ID of the session
            end_reason: Reason for ending the session
            
        Returns:
            Dict containing session summary
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If session ID is invalid
            ModelNotFoundError: If session not found
        """
        pass
    
    @abstractmethod
    def get_session_insights(
        self,
        session_id: str,
        insight_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get insights from a Digital Twin session.
        
        Args:
            session_id: ID of the session
            insight_type: Type of insights to retrieve
            
        Returns:
            Dict containing session insights
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If session ID is invalid
            ModelNotFoundError: If session not found
        """
        pass


class PHIDetectionInterface(BaseMLInterface):
    """Interface for PHI detection services."""
    
    @abstractmethod
    def detect_phi(
        self,
        text: str,
        detection_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect PHI in text.
        
        Args:
            text: Text to analyze
            detection_level: Detection level (strict, moderate, relaxed)
            
        Returns:
            Dict containing detection results with PHI locations and types
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If text is empty or invalid
        """
        pass
    
    @abstractmethod
    def redact_phi(
        self,
        text: str,
        replacement: str = "[REDACTED]",
        detection_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Redact PHI from text.
        
        Args:
            text: Text to redact
            replacement: Replacement text for redacted PHI
            detection_level: Detection level (strict, moderate, relaxed)
            
        Returns:
            Dict containing redacted text and metadata
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If text is empty or invalid
        """
        pass


class DigitalTwinInterface(BaseMLInterface):
    """Interface for Digital Twin services."""
    
    @abstractmethod
    def create_session(
        self,
        therapist_id: str,
        patient_id: Optional[str] = None,
        session_type: str = "therapy",
        session_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Digital Twin session.
        
        Args:
            therapist_id: ID of the therapist
            patient_id: ID of the patient (optional for anonymous sessions)
            session_type: Type of session (therapy, assessment, etc.)
            session_params: Additional session parameters
            
        Returns:
            Dict containing session information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If request is invalid
        """
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about a Digital Twin session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dict containing session information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If session ID is invalid or not found
        """
        pass
    
    @abstractmethod
    def send_message(
        self,
        session_id: str,
        message: str,
        sender_type: str = "user",
        sender_id: Optional[str] = None,
        message_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a Digital Twin session.
        
        Args:
            session_id: ID of the session
            message: Message content
            sender_type: Type of sender (user, therapist, system)
            sender_id: ID of the sender (optional)
            message_params: Additional message parameters
            
        Returns:
            Dict containing message information and Digital Twin's response
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If request is invalid or session not found
        """
        pass
    
    @abstractmethod
    def end_session(
        self,
        session_id: str,
        end_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End a Digital Twin session.
        
        Args:
            session_id: ID of the session
            end_reason: Reason for ending the session
            
        Returns:
            Dict containing session summary
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If session ID is invalid or not found
        """
        pass
    
    @abstractmethod
    def get_insights(
        self,
        session_id: str,
        insight_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get insights from a Digital Twin session.
        
        Args:
            session_id: ID of the session
            insight_type: Type of insights to retrieve
            
        Returns:
            Dict containing insights
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If session ID is invalid or not found
        """
        pass