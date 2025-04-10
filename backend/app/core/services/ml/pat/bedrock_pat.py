# -*- coding: utf-8 -*-
"""
PAT (Patient Assessment Tool) Bedrock Implementation.

This module implements the PAT interface using AWS Bedrock for advanced
natural language processing and assessment capabilities.
"""

import datetime
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
    
    This service provides patient assessment capabilities using
    AWS Bedrock's natural language processing and machine learning features.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Bedrock PAT service.
        
        Args:
            config: Configuration dictionary
        """
        self._initialized = False
        self._config = config or {}
        self._assessments = {}
        self._templates = {}
        self._healthy = True
        self._bedrock_client = None
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the service with configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        self._config.update(config)
        
        # Initialize AWS Bedrock client and resources
        logger.info("Initializing Bedrock PAT service with config: %s", json.dumps({k: "***" if "key" in k.lower() or "secret" in k.lower() else v for k, v in self._config.items()}))
        
        # In a real implementation, this would initialize the AWS Bedrock client
        # and prepare necessary resources
        
        # Load standard assessment templates
        self._initialize_templates()
        
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
        
        # Close AWS Bedrock client
        self._bedrock_client = None
        
        # Clear cached data
        self._assessments.clear()
        self._templates.clear()
        
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
    
    def _initialize_templates(self) -> None:
        """Initialize standard assessment templates."""
        # Create standard templates
        phq9_template = {
            "id": str(uuid.uuid4()),
            "name": "PHQ-9 Depression Assessment",
            "form_type": "questionnaire",
            "version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "fields": [
                {
                    "id": "phq9_1",
                    "text": "Little interest or pleasure in doing things",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "phq9_2",
                    "text": "Feeling down, depressed, or hopeless",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "phq9_3",
                    "text": "Trouble falling or staying asleep, or sleeping too much",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "phq9_4",
                    "text": "Feeling tired or having little energy",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "phq9_5",
                    "text": "Poor appetite or overeating",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "phq9_6",
                    "text": "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "phq9_7",
                    "text": "Trouble concentrating on things, such as reading the newspaper or watching television",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "phq9_8",
                    "text": "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "phq9_9",
                    "text": "Thoughts that you would be better off dead or of hurting yourself in some way",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "phq9_difficulty",
                    "text": "If you checked off any problems, how difficult have these problems made it for you to do your work, take care of things at home, or get along with other people?",
                    "type": "single_choice",
                    "options": [
                        {"value": 0, "text": "Not difficult at all"},
                        {"value": 1, "text": "Somewhat difficult"},
                        {"value": 2, "text": "Very difficult"},
                        {"value": 3, "text": "Extremely difficult"}
                    ]
                }
            ],
            "metadata": {
                "description": "The Patient Health Questionnaire-9 (PHQ-9) is a 9-question instrument given to patients in a primary care setting to screen for the presence and severity of depression.",
                "scoring": {
                    "ranges": [
                        {"min": 0, "max": 4, "label": "Minimal depression"},
                        {"min": 5, "max": 9, "label": "Mild depression"},
                        {"min": 10, "max": 14, "label": "Moderate depression"},
                        {"min": 15, "max": 19, "label": "Moderately severe depression"},
                        {"min": 20, "max": 27, "label": "Severe depression"}
                    ]
                }
            }
        }
        
        gad7_template = {
            "id": str(uuid.uuid4()),
            "name": "GAD-7 Anxiety Assessment",
            "form_type": "questionnaire",
            "version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "fields": [
                {
                    "id": "gad7_1",
                    "text": "Feeling nervous, anxious, or on edge",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "gad7_2",
                    "text": "Not being able to stop or control worrying",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "gad7_3",
                    "text": "Worrying too much about different things",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "gad7_4",
                    "text": "Trouble relaxing",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "gad7_5",
                    "text": "Being so restless that it's hard to sit still",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "gad7_6",
                    "text": "Becoming easily annoyed or irritable",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "gad7_7",
                    "text": "Feeling afraid, as if something awful might happen",
                    "type": "likert",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"}
                    ]
                },
                {
                    "id": "gad7_difficulty",
                    "text": "If you checked off any problems, how difficult have these problems made it for you to do your work, take care of things at home, or get along with other people?",
                    "type": "single_choice",
                    "options": [
                        {"value": 0, "text": "Not difficult at all"},
                        {"value": 1, "text": "Somewhat difficult"},
                        {"value": 2, "text": "Very difficult"},
                        {"value": 3, "text": "Extremely difficult"}
                    ]
                }
            ],
            "metadata": {
                "description": "The Generalized Anxiety Disorder-7 (GAD-7) is a 7-item instrument that is used to measure or assess the severity of generalized anxiety disorder.",
                "scoring": {
                    "ranges": [
                        {"min": 0, "max": 4, "label": "Minimal anxiety"},
                        {"min": 5, "max": 9, "label": "Mild anxiety"},
                        {"min": 10, "max": 14, "label": "Moderate anxiety"},
                        {"min": 15, "max": 21, "label": "Severe anxiety"}
                    ]
                }
            }
        }
        
        # Add templates to collection
        self._templates[phq9_template["id"]] = phq9_template
        self._templates[gad7_template["id"]] = gad7_template
    
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
        
        logger.info(
            "Creating %s assessment for patient %s, clinician %s", 
            assessment_type, 
            patient_id, 
            clinician_id
        )
        
        # Create a new assessment
        assessment_id = str(uuid.uuid4())
        
        # Determine which template to use based on assessment type
        template_id = None
        if assessment_type == "depression":
            # Find PHQ-9 template ID
            template_id = next((tid for tid, t in self._templates.items() if "PHQ-9" in t["name"]), None)
        elif assessment_type == "anxiety":
            # Find GAD-7 template ID
            template_id = next((tid for tid, t in self._templates.items() if "GAD-7" in t["name"]), None)
        
        assessment = {
            "id": assessment_id,
            "patient_id": patient_id,
            "clinician_id": clinician_id,
            "type": assessment_type,
            "template_id": template_id,
            "status": "in_progress",
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "updated_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "data": initial_data,
            "responses": {},
            "notes": [],
            "results": None
        }
        
        # Store the assessment
        self._assessments[assessment_id] = assessment
        
        # Return assessment info
        assessment_info = {
            "assessment_id": assessment_id,
            "patient_id": patient_id,
            "type": assessment_type,
            "status": "in_progress",
            "created_at": assessment["created_at"]
        }
        
        # Include template information if a template was used
        if template_id and template_id in self._templates:
            assessment_info["template"] = {
                "id": template_id,
                "name": self._templates[template_id]["name"],
                "form_type": self._templates[template_id]["form_type"],
                "field_count": len(self._templates[template_id]["fields"])
            }
        
        return assessment_info
    
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
        
        # Get template if available
        template = None
        if assessment.get("template_id") and assessment["template_id"] in self._templates:
            template = self._templates[assessment["template_id"]]
        
        # Return assessment info with response counts
        assessment_info = {
            "assessment_id": assessment["id"],
            "patient_id": assessment["patient_id"],
            "clinician_id": assessment["clinician_id"],
            "type": assessment["type"],
            "status": assessment["status"],
            "created_at": assessment["created_at"],
            "updated_at": assessment["updated_at"],
            "response_count": len(assessment["responses"]),
            "notes_count": len(assessment["notes"]),
            "data": assessment["data"]
        }
        
        # Add template information if available
        if template:
            assessment_info["template"] = {
                "id": template["id"],
                "name": template["name"],
                "form_type": template["form_type"],
                "version": template["version"],
                "field_count": len(template["fields"])
            }
        
        # Add results if assessment is complete
        if assessment["status"] == "completed" and assessment["results"]:
            assessment_info["results"] = assessment["results"]
        
        return assessment_info
    
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
        
        # Check if assessment can be updated
        if assessment["status"] == "completed":
            logger.error("Cannot update completed assessment: %s", assessment_id)
            raise InvalidRequestError(f"Cannot update completed assessment: {assessment_id}")
        
        logger.info("Updating assessment %s", assessment_id)
        
        # Update assessment with new data
        if "responses" in data:
            assessment["responses"].update(data["responses"])
        
        if "notes" in data and isinstance(data["notes"], list):
            for note in data["notes"]:
                if isinstance(note, dict) and "text" in note:
                    note_with_timestamp = {
                        "id": str(uuid.uuid4()),
                        "text": note["text"],
                        "author_id": note.get("author_id"),
                        "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
                    }
                    assessment["notes"].append(note_with_timestamp)
        
        if "data" in data and isinstance(data["data"], dict):
            assessment["data"].update(data["data"])
        
        # Update timestamp
        assessment["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()
        
        # Return updated assessment info
        return self.get_assessment(assessment_id)
    
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
        
        # Check if assessment is already completed
        if assessment["status"] == "completed":
            logger.warning("Assessment already completed: %s", assessment_id)
            if assessment["results"]:
                return {"assessment_id": assessment_id, "results": assessment["results"]}
            
        logger.info("Completing assessment %s", assessment_id)
        
        # Update assessment with completion data if provided
        if completion_data:
            if "responses" in completion_data:
                assessment["responses"].update(completion_data["responses"])
            
            if "notes" in completion_data and isinstance(completion_data["notes"], list):
                for note in completion_data["notes"]:
                    if isinstance(note, dict) and "text" in note:
                        note_with_timestamp = {
                            "id": str(uuid.uuid4()),
                            "text": note["text"],
                            "author_id": note.get("author_id"),
                            "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
                        }
                        assessment["notes"].append(note_with_timestamp)
            
            if "data" in completion_data and isinstance(completion_data["data"], dict):
                assessment["data"].update(completion_data["data"])
        
        # Generate results based on assessment type and responses
        results = self._calculate_assessment_results(assessment)
        
        # Update assessment with results and mark as completed
        assessment["status"] = "completed"
        assessment["results"] = results
        assessment["completed_at"] = datetime.datetime.now(datetime.UTC).isoformat()
        assessment["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()
        
        # Return assessment results
        return {
            "assessment_id": assessment_id,
            "patient_id": assessment["patient_id"],
            "type": assessment["type"],
            "status": "completed",
            "completed_at": assessment["completed_at"],
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
        
        logger.info("Analyzing assessment %s, type: %s", assessment_id, analysis_type)
        
        # Get template if available
        template = None
        if assessment.get("template_id") and assessment["template_id"] in self._templates:
            template = self._templates[assessment["template_id"]]
        
        # Perform analysis based on type
        analysis_results = {}
        
        if analysis_type == "standard":
            # Generate standard analysis results
            analysis_results = self._generate_standard_analysis(assessment, template, options)
        elif analysis_type == "detailed":
            # Generate detailed analysis results
            analysis_results = self._generate_detailed_analysis(assessment, template, options)
        elif analysis_type == "nlp":
            # Generate NLP-based analysis using AWS Bedrock
            analysis_results = self._generate_nlp_analysis(assessment, template, options)
        else:
            logger.warning("Unknown analysis type: %s, using standard analysis", analysis_type)
            analysis_results = self._generate_standard_analysis(assessment, template, options)
        
        return {
            "assessment_id": assessment_id,
            "patient_id": assessment["patient_id"],
            "type": assessment["type"],
            "analysis_type": analysis_type,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
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
        
                    "type": "scale",
                    "question": "Feeling nervous, anxious, or on edge",
                    "options": [
                        {"value": 0, "label": "Not at all"},
                        {"value": 1, "label": "Several days"},
                        {"value": 2, "label": "More than half the days"},
                        {"value": 3, "label": "Nearly every day"}
                    ],
                    "required": True
                },
                {
                    "id": "gad7_2",
                    "type": "scale",
                    "question": "Not being able to stop or control worrying",
                    "options": [
                        {"value": 0, "label": "Not at all"},
                        {"value": 1, "label": "Several days"},
                        {"value": 2, "label": "More than half the days"},
                        {"value": 3, "label": "Nearly every day"}
                    ],
                    "required": True
                },
                {
                    "id": "gad7_3",
                    "type": "scale",
                    "question": "Worrying too much about different things",
                    "options": [
                        {"value": 0, "label": "Not at all"},
                        {"value": 1, "label": "Several days"},
                        {"value": 2, "label": "More than half the days"},
                        {"value": 3, "label": "Nearly every day"}
                    ],
                    "required": True
                },
                {
                    "id": "gad7_4",
                    "type": "scale",
                    "question": "Trouble relaxing",
                    "options": [
                        {"value": 0, "label": "Not at all"},
                        {"value": 1, "label": "Several days"},
                        {"value": 2, "label": "More than half the days"},
                        {"value": 3, "label": "Nearly every day"}
                    ],
                    "required": True
                },
                {
                    "id": "gad7_5",
                    "type": "scale",
                    "question": "Being so restless that it's hard to sit still",
                    "options": [
                        {"value": 0, "label": "Not at all"},
                        {"value": 1, "label": "Several days"},
                        {"value": 2, "label": "More than half the days"},
                        {"value": 3, "label": "Nearly every day"}
                    ],
                    "required": True
                },
                {
                    "id": "gad7_6",
                    "type": "scale",
                    "question": "Becoming easily annoyed or irritable",
                    "options": [
                        {"value": 0, "label": "Not at all"},
                        {"value": 1, "label": "Several days"},
                        {"value": 2, "label": "More than half the days"},
                        {"value": 3, "label": "Nearly every day"}
                    ],
                    "required": True
                },
                {
                    "id": "gad7_7",
                    "type": "scale",
                    "question": "Feeling afraid as if something awful might happen",
                    "options": [
                        {"value": 0, "label": "Not at all"},
                        {"value": 1, "label": "Several days"},
                        {"value": 2, "label": "More than half the days"},
                        {"value": 3, "label": "Nearly every day"}
                    ],
                    "required": True
                },
                {
                    "id": "gad7_difficulty",
                    "type": "scale",
                    "question": "If you checked off any problems, how difficult have these problems made it for you to do your work, take care of things at home, or get along with other people?",
                    "options": [
                        {"value": 0, "label": "Not difficult at all"},
                        {"value": 1, "label": "Somewhat difficult"},
                        {"value": 2, "label": "Very difficult"},
                        {"value": 3, "label": "Extremely difficult"}
                    ],
                    "required": True
                }
            ],
            "metadata": {
                "description": "The Generalized Anxiety Disorder-7 (GAD-7) is a 7-item anxiety scale used for screening, diagnosing, monitoring, and measuring the severity of anxiety.",
                "scoring": {
                    "ranges": [
                        {"min": 0, "max": 4, "label": "Minimal anxiety"},
                        {"min": 5, "max": 9, "label": "Mild anxiety"},
                        {"min": 10, "max": 14, "label": "Moderate anxiety"},
                        {"min": 15, "max": 21, "label": "Severe anxiety"}
                    ]
                }
            }
        }
        
        # Initial Psychiatric Assessment
        initial_assessment_template = {
            "id": "template-initial-assessment",
            "name": "Initial Psychiatric Assessment",
            "form_type": "initial_assessment",
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "updated_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "fields": [
                {
                    "id": "presenting_problem",
                    "type": "text",
                    "question": "Presenting Problem",
                    "required": True
                },
                {
                    "id": "history_of_present_illness",
                    "type": "textarea",
                    "question": "History of Present Illness",
                    "required": True
                },
                {
                    "id": "psychiatric_history",
                    "type": "textarea",
                    "question": "Psychiatric History",
                    "required": True
                },
                {
                    "id": "medical_history",
                    "type": "textarea",
                    "question": "Medical History",
                    "required": True
                },
                {
                    "id": "medications",
                    "type": "textarea",
                    "question": "Current Medications",
                    "required": True
                },
                {
                    "id": "allergies",
                    "type": "text",
                    "question": "Allergies",
                    "required": True
                },
                {
                    "id": "substance_use",
                    "type": "textarea",
                    "question": "Substance Use History",
                    "required": True
                },
                {
                    "id": "family_history",
                    "type": "textarea",
                    "question": "Family History",
                    "required": True
                },
                {
                    "id": "social_history",
                    "type": "textarea",
                    "question": "Social History",
                    "required": True
                },
                {
                    "id": "mental_status",
                    "type": "checklist",
                    "question": "Mental Status Examination",
                    "options": [
                        {"value": "alert", "label": "Alert"},
                        {"value": "oriented", "label": "Oriented x3"},
                        {"value": "cooperative", "label": "Cooperative"},
                        {"value": "agitated", "label": "Agitated"},
                        {"value": "disheveled", "label": "Disheveled"},
                        {"value": "poor_eye_contact", "label": "Poor eye contact"},
                        {"value": "normal_speech", "label": "Normal speech"},
                        {"value": "pressured_speech", "label": "Pressured speech"},
                        {"value": "tangential", "label": "Tangential"},
                        {"value": "linear_thought", "label": "Linear thought process"},
                        {"value": "si", "label": "Suicidal ideation"},
                        {"value": "hi", "label": "Homicidal ideation"},
                        {"value": "hallucinations", "label": "Hallucinations"},
                        {"value": "delusions", "label": "Delusions"},
                        {"value": "insight_good", "label": "Good insight"},
                        {"value": "insight_fair", "label": "Fair insight"},
                        {"value": "insight_poor", "label": "Poor insight"},
                        {"value": "judgment_good", "label": "Good judgment"},
                        {"value": "judgment_fair", "label": "Fair judgment"},
                        {"value": "judgment_poor", "label": "Poor judgment"}
                    ],
                    "required": True
                },
                {
                    "id": "diagnosis",
                    "type": "text",
                    "question": "Provisional Diagnosis",
                    "required": True
                },
                {
                    "id": "treatment_plan",
                    "type": "textarea",
                    "question": "Treatment Plan",
                    "required": True
                }
            ],
            "metadata": {
                "description": "Comprehensive initial psychiatric assessment for new patients.",
                "clinical_use": "Initial evaluation and treatment planning"
            }
        }
        
        # Store templates
        self._templates = {
            "template-phq9": phq9_template,
            "template-gad7": gad7_template,
            "template-initial-assessment": initial_assessment_template
        }
    
    def _calculate_completion_percentage(self, assessment: Dict[str, Any], template: Dict[str, Any]) -> float:
        """
        Calculate the completion percentage of an assessment.
        
        Args:
            assessment: The assessment to check
            template: The assessment template
            
        Returns:
            Completion percentage (0-100)
        """
        if not template:
            return 0.0
        
        # Count required fields
        required_fields = [f for f in template["fields"] if f.get("required", False)]
        required_count = len(required_fields)
        
        if required_count == 0:
            return 100.0
        
        # Count completed required fields
        completed_count = 0
        for field in required_fields:
            field_id = field["id"]
            if field_id in assessment["data"] and assessment["data"][field_id] is not None:
                completed_count += 1
        
        return (completed_count / required_count) * 100
    
    def _calculate_assessment_scores(self, assessment: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate scores for an assessment.
        
        Args:
            assessment: The assessment to score
            template: The assessment template
            
        Returns:
            Score results
        """
        if not template:
            return {"total_score": 0}
        
        form_type = template["form_type"]
        
        if form_type == "depression_assessment":
            return self._calculate_phq9_scores(assessment, template)
        elif form_type == "anxiety_assessment":
            return self._calculate_gad7_scores(assessment, template)
        else:
            # Generic scoring for other assessment types
            return self._calculate_generic_scores(assessment, template)
    
    def _calculate_phq9_scores(self, assessment: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate PHQ-9 depression scores.
        
        Args:
            assessment: The assessment to score
            template: The assessment template
            
        Returns:
            Score results
        """
        data = assessment["data"]
        
        # Calculate total score (sum of first 9 items)
        total_score = 0
        for i in range(1, 10):
            field_id = f"phq9_{i}"
            if field_id in data and isinstance(data[field_id], (int, float)):
                total_score += int(data[field_id])
        
        # Determine severity
        severity = "minimal"
        if total_score >= 20:
            severity = "severe"
        elif total_score >= 15:
            severity = "moderately_severe"
        elif total_score >= 10:
            severity = "moderate"
        elif total_score >= 5:
            severity = "mild"
        
        # Check suicide risk (item 9)
        suicide_risk = "none"
        if "phq9_9" in data:
