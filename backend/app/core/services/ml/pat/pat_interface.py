# -*- coding: utf-8 -*-
"""
Patient Assessment Tool (PAT) Interface.

This module defines the interface for the PAT service used in patient assessment
and clinical evaluation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class PATInterface(ABC):
    """Interface for Patient Assessment Tool services."""
    
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
    
    @abstractmethod
    def create_assessment(
        self,
        patient_id: str,
        assessment_type: str,
        clinician_id: Optional[str] = None,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new patient assessment.
        
        Args:
            patient_id: Patient identifier
            assessment_type: Type of assessment (e.g., "depression", "anxiety")
            clinician_id: Clinician identifier (optional)
            initial_data: Initial assessment data (optional)
            
        Returns:
            Dict containing assessment information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If patient_id or assessment_type is invalid
        """
        pass
    
    @abstractmethod
    def get_assessment(self, assessment_id: str) -> Dict[str, Any]:
        """
        Get information about an assessment.
        
        Args:
            assessment_id: Assessment identifier
            
        Returns:
            Dict containing assessment information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If assessment_id is invalid
            ModelNotFoundError: If assessment not found
        """
        pass
    
    @abstractmethod
    def update_assessment(
        self,
        assessment_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an assessment with new data.
        
        Args:
            assessment_id: Assessment identifier
            data: Updated assessment data
            
        Returns:
            Dict containing update status
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If assessment_id is invalid or assessment is completed
            ModelNotFoundError: If assessment not found
        """
        pass
    
    @abstractmethod
    def complete_assessment(
        self,
        assessment_id: str,
        completion_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete an assessment.
        
        Args:
            assessment_id: Assessment identifier
            completion_data: Final data to add before completion (optional)
            
        Returns:
            Dict containing completion status and results
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If assessment_id is invalid or already completed
            ModelNotFoundError: If assessment not found
        """
        pass
    
    @abstractmethod
    def analyze_assessment(
        self,
        assessment_id: str,
        analysis_type: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze an assessment.
        
        Args:
            assessment_id: Assessment identifier
            analysis_type: Type of analysis to perform (optional)
            options: Additional analysis options (optional)
            
        Returns:
            Dict containing analysis results
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If assessment_id or analysis_type is invalid
            ModelNotFoundError: If assessment not found
        """
        pass
    
    @abstractmethod
    def get_assessment_history(
        self,
        patient_id: str,
        assessment_type: Optional[str] = None,
        limit: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get assessment history for a patient.
        
        Args:
            patient_id: Patient identifier
            assessment_type: Type of assessments to retrieve (optional)
            limit: Maximum number of assessments to retrieve (optional)
            options: Additional retrieval options (optional)
            
        Returns:
            Dict containing assessment history
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If patient_id is invalid
        """
        pass
    
    @abstractmethod
    def create_form_template(
        self,
        name: str,
        form_type: str,
        fields: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new assessment form template.
        
        Args:
            name: Template name
            form_type: Type of form (e.g., "depression", "anxiety")
            fields: List of field definitions
            metadata: Additional template metadata (optional)
            
        Returns:
            Dict containing template information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If name, form_type, or fields are invalid
        """
        pass
    
    @abstractmethod
    def get_form_template(
        self,
        template_id: str
    ) -> Dict[str, Any]:
        """
        Get a form template.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Dict containing template information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If template_id is invalid
            ModelNotFoundError: If template not found
        """
        pass
    
    @abstractmethod
    def list_form_templates(
        self,
        form_type: Optional[str] = None,
        limit: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        List available form templates.
        
        Args:
            form_type: Type of templates to list (optional)
            limit: Maximum number of templates to retrieve (optional)
            options: Additional retrieval options (optional)
            
        Returns:
            Dict containing list of templates
            
        Raises:
            ServiceUnavailableError: If service is not initialized
        """
        pass
    
    @abstractmethod
    def calculate_score(
        self,
        assessment_id: str,
        scoring_method: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate score for an assessment.
        
        Args:
            assessment_id: Assessment identifier
            scoring_method: Method to use for scoring (optional)
            options: Additional scoring options (optional)
            
        Returns:
            Dict containing calculated scores
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If assessment_id or scoring_method is invalid
            ModelNotFoundError: If assessment not found
        """
        pass
    
    @abstractmethod
    def generate_report(
        self,
        assessment_id: str,
        report_type: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a report for an assessment.
        
        Args:
            assessment_id: Assessment identifier
            report_type: Type of report to generate (optional)
            options: Additional report options (optional)
            
        Returns:
            Dict containing generated report
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If assessment_id or report_type is invalid
            ModelNotFoundError: If assessment not found
        """
        pass