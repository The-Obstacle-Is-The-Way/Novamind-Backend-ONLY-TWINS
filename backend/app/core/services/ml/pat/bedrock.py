# -*- coding: utf-8 -*-
"""
Bedrock PAT Service Implementation.

This module implements the PAT interface using AWS Bedrock
for the mental health platform.
"""

import datetime
from datetime import timezone
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

from app.core.services.ml.pat.pat_interface import PATInterface
from app.core.exceptions import (
    InvalidRequestError,
    ModelNotFoundError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class BedrockPAT(PATInterface):
    """
    Implementation of the PAT service using AWS Bedrock.
    
    This service provides assessment capabilities powered by
    AWS Bedrock foundation models.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Bedrock PAT service.
        
        Args:
            config: Configuration dictionary
        """
        self._initialized = False
        self._config = config or {}
        self._assessments = {}  # In-memory assessment storage (would be a DB in production)
        self._templates = {}  # In-memory template storage
        self._healthy = True
        
        # Initialize default templates
        self._default_templates = {
            "phq9": {
                "id": "phq9",
                "name": "Patient Health Questionnaire-9",
                "form_type": "questionnaire",
                "description": "Depression screening tool",
                "fields": [
                    {
                        "id": "q1",
                        "question": "Little interest or pleasure in doing things",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q2",
                        "question": "Feeling down, depressed, or hopeless",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q3",
                        "question": "Trouble falling or staying asleep, or sleeping too much",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q4",
                        "question": "Feeling tired or having little energy",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q5",
                        "question": "Poor appetite or overeating",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q6",
                        "question": "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q7",
                        "question": "Trouble concentrating on things, such as reading the newspaper or watching television",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q8",
                        "question": "Moving or speaking so slowly that other people could have noticed — or so fidgety or restless that you have been moving a lot more than usual",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q9",
                        "question": "Thoughts that you would be better off dead, or thoughts of hurting yourself in some way",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    }
                ],
                "scoring": {
                    "method": "sum",
                    "ranges": [
                        {"min": 0, "max": 4, "severity": "minimal"},
                        {"min": 5, "max": 9, "severity": "mild"},
                        {"min": 10, "max": 14, "severity": "moderate"},
                        {"min": 15, "max": 19, "severity": "moderately severe"},
                        {"min": 20, "max": 27, "severity": "severe"}
                    ]
                }
            },
            "gad7": {
                "id": "gad7",
                "name": "Generalized Anxiety Disorder-7",
                "form_type": "questionnaire",
                "description": "Anxiety screening tool",
                "fields": [
                    {
                        "id": "q1",
                        "question": "Feeling nervous, anxious, or on edge",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q2",
                        "question": "Not being able to stop or control worrying",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q3",
                        "question": "Worrying too much about different things",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q4",
                        "question": "Trouble relaxing",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q5",
                        "question": "Being so restless that it's hard to sit still",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q6",
                        "question": "Becoming easily annoyed or irritable",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    {
                        "id": "q7",
                        "question": "Feeling afraid as if something awful might happen",
                        "type": "scale",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    }
                ],
                "scoring": {
                    "method": "sum",
                    "ranges": [
                        {"min": 0, "max": 4, "severity": "minimal"},
                        {"min": 5, "max": 9, "severity": "mild"},
                        {"min": 10, "max": 14, "severity": "moderate"},
                        {"min": 15, "max": 21, "severity": "severe"}
                    ]
                }
            }
        }
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the service with configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        self._config.update(config)
        
        # Initialize components and connections
        logger.info("Initializing Bedrock PAT service with config: %s", json.dumps({k: "***" if "key" in k.lower() or "secret" in k.lower() else v for k, v in self._config.items()}))
        
        # In a real implementation, this would initialize connections to AWS Bedrock
        # and configure the models and parameters
        
        # Initialize default templates
        self._templates = {**self._default_templates}
        
        self._initialized = True
        logger.info("Bedrock PAT service initialized successfully")
    
    def is_healthy(self) -> bool:
        """
        Check if the service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        return self._initialized and self._healthy
    
    def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        logger.info("Shutting down Bedrock PAT service")
        self._initialized = False
        self._assessments.clear()
        self._templates.clear()
        # Additional cleanup would happen here
        logger.info("Bedrock PAT service shutdown complete")
    
    def _ensure_initialized(self) -> None:
        """
        Ensure the service is initialized.
        
        Raises:
            ServiceUnavailableError: If service is not initialized
        """
        if not self._initialized:
            logger.error("Bedrock PAT service not initialized")
            raise ServiceUnavailableError("Bedrock PAT service not initialized")
    
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
            patient_id: ID of the patient
            assessment_type: Type of assessment (initial, followup, specialized)
            clinician_id: ID of the clinician (optional)
            initial_data: Initial assessment data
            
        Returns:
            Dict containing assessment information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If request is invalid
        """
        self._ensure_initialized()
        
        if not patient_id:
            logger.error("Invalid request: patient_id is required")
            raise InvalidRequestError("Invalid request: patient_id is required")
        
        if not assessment_type:
            logger.error("Invalid request: assessment_type is required")
            raise InvalidRequestError("Invalid request: assessment_type is required")
        
        initial_data = initial_data or {}
        
        # Get template for assessment type
        template_id = initial_data.get("template_id")
        template = None
        
        if template_id:
            template = self._templates.get(template_id)
            if not template:
                logger.error("Invalid request: template_id %s not found", template_id)
                raise InvalidRequestError(f"Invalid request: template_id {template_id} not found")
        
        # Create assessment ID
        assessment_id = str(uuid.uuid4())
        
        # Initialize assessment object
        assessment = {
            "id": assessment_id,
            "patient_id": patient_id,
            "clinician_id": clinician_id,
            "assessment_type": assessment_type,
            "status": "created",
            "created_at": datetime.datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.datetime.now(timezone.utc).isoformat(),
            "template": template,
            "data": initial_data.get("data", {}),
            "responses": initial_data.get("responses", {}),
            "metrics": {
                "completion_percentage": 0,
                "time_spent": 0,
                "response_count": 0
            }
        }
        
        # Store assessment
        self._assessments[assessment_id] = assessment
        
        logger.info(
            "Created assessment: %s, type: %s, patient: %s", 
            assessment_id, 
            assessment_type, 
            patient_id
        )
        
        return {
            "assessment_id": assessment_id,
            "patient_id": patient_id,
            "clinician_id": clinician_id,
            "assessment_type": assessment_type,
            "status": "created",
            "created_at": assessment["created_at"],
            "template": template
        }
    
    def get_assessment(self, assessment_id: str) -> Dict[str, Any]:
        """
        Get information about an assessment.
        
        Args:
            assessment_id: ID of the assessment
            
        Returns:
            Dict containing assessment information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If assessment ID is invalid
            ModelNotFoundError: If assessment not found
        """
        self._ensure_initialized()
        
        if not assessment_id:
            logger.error("Invalid request: assessment_id is required")
            raise InvalidRequestError("Invalid request: assessment_id is required")
        
        assessment = self._assessments.get(assessment_id)
        if not assessment:
            logger.error("Assessment not found: %s", assessment_id)
            raise ModelNotFoundError(f"Assessment not found: {assessment_id}")
        
        # Return a copy to prevent modification of internal state
        return {
            "assessment_id": assessment["id"],
            "patient_id": assessment["patient_id"],
            "clinician_id": assessment["clinician_id"],
            "assessment_type": assessment["assessment_type"],
            "status": assessment["status"],
            "created_at": assessment["created_at"],
            "updated_at": assessment["updated_at"],
            "template": assessment["template"],
            "data": assessment["data"],
            "responses": assessment["responses"],
            "metrics": assessment["metrics"]
        }
    
    def update_assessment(
        self,
        assessment_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an assessment with new data.
        
        Args:
            assessment_id: ID of the assessment
            data: Updated assessment data
            
        Returns:
            Dict containing updated assessment information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If request is invalid
            ModelNotFoundError: If assessment not found
        """
        self._ensure_initialized()
        
        if not assessment_id:
            logger.error("Invalid request: assessment_id is required")
            raise InvalidRequestError("Invalid request: assessment_id is required")
        
        if not data:
            logger.error("Invalid request: data is required")
            raise InvalidRequestError("Invalid request: data is required")
        
        assessment = self._assessments.get(assessment_id)
        if not assessment:
            logger.error("Assessment not found: %s", assessment_id)
            raise ModelNotFoundError(f"Assessment not found: {assessment_id}")
        
        # Ensure assessment is not completed
        if assessment["status"] == "completed":
            logger.error("Cannot update completed assessment: %s", assessment_id)
            raise InvalidRequestError(f"Cannot update completed assessment: {assessment_id}")
        
        # Update assessment data
        if "responses" in data:
            # Merge responses
            assessment["responses"].update(data["responses"])
            
            # Update completion percentage
            if assessment["template"]:
                field_count = len(assessment["template"]["fields"])
                response_count = len(assessment["responses"])
                completion_percentage = (response_count / field_count * 100) if field_count > 0 else 0
                assessment["metrics"]["completion_percentage"] = min(100, completion_percentage)
                assessment["metrics"]["response_count"] = response_count
        
        # Update other data
        for key, value in data.items():
            if key != "responses" and key in assessment["data"]:
                assessment["data"][key] = value
        
        # Update timestamp
        assessment["updated_at"] = datetime.datetime.now(timezone.utc).isoformat()
        
        logger.info("Updated assessment: %s", assessment_id)
        
        return {
            "assessment_id": assessment["id"],
            "patient_id": assessment["patient_id"],
            "status": assessment["status"],
            "updated_at": assessment["updated_at"],
            "metrics": assessment["metrics"]
        }
    
    def complete_assessment(
        self,
        assessment_id: str,
        completion_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete an assessment.
        
        Args:
            assessment_id: ID of the assessment
            completion_data: Additional completion data
            
        Returns:
            Dict containing assessment results
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If assessment ID is invalid
            ModelNotFoundError: If assessment not found
        """
        self._ensure_initialized()
        
        if not assessment_id:
            logger.error("Invalid request: assessment_id is required")
            raise InvalidRequestError("Invalid request: assessment_id is required")
        
        assessment = self._assessments.get(assessment_id)
        if not assessment:
            logger.error("Assessment not found: %s", assessment_id)
            raise ModelNotFoundError(f"Assessment not found: {assessment_id}")
        
        # Ensure assessment is not already completed
        if assessment["status"] == "completed":
            logger.error("Assessment already completed: %s", assessment_id)
            raise InvalidRequestError(f"Assessment already completed: {assessment_id}")
        
        completion_data = completion_data or {}
        
        # Update assessment with completion data
        if "responses" in completion_data:
            assessment["responses"].update(completion_data["responses"])
        
        # Update other data
        for key, value in completion_data.items():
            if key != "responses" and key in assessment["data"]:
                assessment["data"][key] = value
        
        # Mark as completed
        assessment["status"] = "completed"
        assessment["completed_at"] = datetime.datetime.now(timezone.utc).isoformat()
        assessment["updated_at"] = assessment["completed_at"]
        
        # Calculate final metrics
        template = assessment["template"]
        if template:
            field_count = len(template["fields"])
            response_count = len(assessment["responses"])
            completion_percentage = (response_count / field_count * 100) if field_count > 0 else 0
            assessment["metrics"]["completion_percentage"] = min(100, completion_percentage)
            assessment["metrics"]["response_count"] = response_count
        
        # Generate results
        results = self._generate_assessment_results(assessment)
        assessment["results"] = results
        
        logger.info("Completed assessment: %s", assessment_id)
        
        return {
            "assessment_id": assessment["id"],
            "patient_id": assessment["patient_id"],
            "status": "completed",
            "completed_at": assessment["completed_at"],
            "metrics": assessment["metrics"],
            "results": results
        }
    
    def analyze_assessment(
        self,
        assessment_id: str,
        analysis_type: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze an assessment.
        
        Args:
            assessment_id: ID of the assessment
            analysis_type: Type of analysis to perform
            options: Additional analysis options
            
        Returns:
            Dict containing analysis results
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If assessment ID is invalid
            ModelNotFoundError: If assessment not found
        """
        self._ensure_initialized()
        
        if not assessment_id:
            logger.error("Invalid request: assessment_id is required")
            raise InvalidRequestError("Invalid request: assessment_id is required")
        
        assessment = self._assessments.get(assessment_id)
        if not assessment:
            logger.error("Assessment not found: %s", assessment_id)
            raise ModelNotFoundError(f"Assessment not found: {assessment_id}")
        
        analysis_type = analysis_type or "standard"
        options = options or {}
        
        logger.info(
            "Analyzing assessment: %s, type: %s", 
            assessment_id,
            analysis_type
        )
        
        # In a real implementation, this would use AWS Bedrock to perform advanced analysis
        
        # For demonstration, use a basic analysis method
        if analysis_type == "sentiment":
            analysis_results = self._analyze_sentiment(assessment)
        elif analysis_type == "risk":
            analysis_results = self._analyze_risk(assessment)
        elif analysis_type == "trends":
            analysis_results = self._analyze_trends(assessment, options.get("previous_assessments", []))
        else:  # standard
            analysis_results = self._standard_analysis(assessment)
        
        return {
            "assessment_id": assessment["id"],
            "patient_id": assessment["patient_id"],
            "analysis_type": analysis_type,
            "analyzed_at": datetime.datetime.now(timezone.utc).isoformat(),
            "results": analysis_results
        }
    
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
            patient_id: ID of the patient
            assessment_type: Type of assessment to filter by
            limit: Maximum number of assessments to return
            options: Additional options
            
        Returns:
            Dict containing assessment history
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If patient ID is invalid
        """
        self._ensure_initialized()
        
        if not patient_id:
            logger.error("Invalid request: patient_id is required")
            raise InvalidRequestError("Invalid request: patient_id is required")
        
        options = options or {}
        
        # Filter assessments by patient ID
        patient_assessments = [a for a in self._assessments.values() if a["patient_id"] == patient_id]
        
        # Filter by assessment type if specified
        if assessment_type:
            patient_assessments = [a for a in patient_assessments if a["assessment_type"] == assessment_type]
        
        # Sort by creation date (newest first)
        patient_assessments.sort(key=lambda a: a["created_at"], reverse=True)
        
        # Apply limit if specified
        if limit:
            patient_assessments = patient_assessments[:limit]
        
        # Extract basic information for each assessment
        assessment_history = []
        for assessment in patient_assessments:
            history_item = {
                "assessment_id": assessment["id"],
                "assessment_type": assessment["assessment_type"],
                "status": assessment["status"],
                "created_at": assessment["created_at"],
                "updated_at": assessment["updated_at"],
                "metrics": assessment["metrics"]
            }
            
            if "completed_at" in assessment:
                history_item["completed_at"] = assessment["completed_at"]
            
            if "results" in assessment and options.get("include_results", False):
                history_item["results"] = assessment["results"]
            
            assessment_history.append(history_item)
        
        return {
            "patient_id": patient_id,
            "assessment_count": len(assessment_history),
            "assessment_history": assessment_history
        }
    
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
            name: Name of the template
            form_type: Type of form (questionnaire, scale, etc.)
            fields: Form fields
            metadata: Additional template metadata
            
        Returns:
            Dict containing template information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If request is invalid
        """
        self._ensure_initialized()
        
        if not name:
            logger.error("Invalid request: name is required")
            raise InvalidRequestError("Invalid request: name is required")
        
        if not form_type:
            logger.error("Invalid request: form_type is required")
            raise InvalidRequestError("Invalid request: form_type is required")
        
        if not fields:
            logger.error("Invalid request: fields is required")
            raise InvalidRequestError("Invalid request: fields is required")
        
        metadata = metadata or {}
        
        # Create template ID
        template_id = name.lower().replace(" ", "_")
        
        # Check if template already exists
        if template_id in self._templates:
            logger.error("Template already exists: %s", template_id)
            raise InvalidRequestError(f"Template already exists: {template_id}")
        
        # Create template
        template = {
            "id": template_id,
            "name": name,
            "form_type": form_type,
            "fields": fields,
            "created_at": datetime.datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.datetime.now(timezone.utc).isoformat(),
            "scoring": metadata.get("scoring", {}),
            "description": metadata.get("description", ""),
            "instructions": metadata.get("instructions", ""),
            "language": metadata.get("language", "en"),
            "version": metadata.get("version", "1.0.0")
        }
        
        # Store template
        self._templates[template_id] = template
        
        logger.info("Created form template: %s", template_id)
        
        return {
            "template_id": template_id,
            "name": name,
            "form_type": form_type,
            "field_count": len(fields),
            "created_at": template["created_at"]
        }
    
    def get_form_template(
        self,
        template_id: str
    ) -> Dict[str, Any]:
        """
        Get a form template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            Dict containing template information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If template ID is invalid
            ModelNotFoundError: If template not found
        """
        self._ensure_initialized()
        
        if not template_id:
            logger.error("Invalid request: template_id is required")
            raise InvalidRequestError("Invalid request: template_id is required")
        
        template = self._templates.get(template_id)
        if not template:
            logger.error("Template not found: %s", template_id)
            raise ModelNotFoundError(f"Template not found: {template_id}")
        
        # Return a copy to prevent modification of internal state
        return dict(template)
    
    def list_form_templates(
        self,
        form_type: Optional[str] = None,
        limit: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        List available form templates.
        
        Args:
            form_type: Type of form to filter by
            limit: Maximum number of templates to return
            options: Additional options
            
        Returns:
            Dict containing template list
            
        Raises:
            ServiceUnavailableError: If service is not initialized
        """
        self._ensure_initialized()
        
        options = options or {}
        
        # Get all templates
        templates = list(self._templates.values())
        
        # Filter by form type if specified
        if form_type:
            templates = [t for t in templates if t["form_type"] == form_type]
        
        # Sort by name
        templates.sort(key=lambda t: t["name"])
        
        # Apply limit if specified
        if limit:
            templates = templates[:limit]
        
        # Extract basic information for each template
        template_list = []
        for template in templates:
            template_info = {
                "id": template["id"],
                "name": template["name"],
                "form_type": template["form_type"],
                "field_count": len(template["fields"]),
                "description": template.get("description", "")
            }
            
            if options.get("include_fields", False):
                template_info["fields"] = template["fields"]
            
            template_list.append(template_info)
        
        return {
            "template_count": len(template_list),
            "templates": template_list
        }
    
    def calculate_score(
        self,
        assessment_id: str,
        scoring_method: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate score for an assessment.
        
        Args:
            assessment_id: ID of the assessment
            scoring_method: Scoring method to use
            options: Additional scoring options
            
        Returns:
            Dict containing score results
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If assessment ID is invalid
            ModelNotFoundError: If assessment not found
        """
        self._ensure_initialized()
        
        if not assessment_id:
            logger.error("Invalid request: assessment_id is required")
            raise InvalidRequestError("Invalid request: assessment_id is required")
        
        assessment = self._assessments.get(assessment_id)
        if not assessment:
            logger.error("Assessment not found: %s", assessment_id)

        # ... rest of your code remains the same ...
