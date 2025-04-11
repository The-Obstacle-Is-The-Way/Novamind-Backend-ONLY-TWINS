# -*- coding: utf-8 -*-
"""
Mock PAT (Patient Assessment Tool) Service Implementation.

This module implements a mock version of the PAT interface for testing.
"""

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

from app.core.services.ml.pat.pat_interface import PATInterface

logger = logging.getLogger(__name__)


class MockPATService(PATInterface):
    """
    Mock implementation of the Patient Assessment Tool service for testing.
    
    This implementation stores data in memory and provides simplified
    functionality to facilitate testing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the mock PAT service."""
        self._initialized = False
        self._config = config or {}
        self._mock_delay_ms = 0  # Default mock delay
        self._assessments = {}
        self._form_templates = {}
        
        # Setup default templates for testing
        self._setup_mock_templates()
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the service with configuration."""
        self._config.update(config)
        self._mock_delay_ms = config.get("mock_delay_ms", 0)  # Get mock delay from config
        self._initialized = True
        logger.info("Mock PAT service initialized")
    
    def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        return self._initialized
    
    def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        self._initialized = False
        self._assessments.clear()
        self._form_templates.clear()
        logger.info("Mock PAT service shutdown")
    
    def create_assessment(
        self,
        patient_id: str,
        assessment_type: str,
        clinician_id: Optional[str] = None,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new patient assessment."""
        if not self._initialized:
            raise Exception("Service not initialized")
        
        if not patient_id or not assessment_type:
            raise ValueError("Patient ID and assessment type are required")
        
        assessment_id = str(uuid.uuid4())
        template_id = None
        
        # Find template for the assessment type
        for tid, template in self._form_templates.items():
            if template["form_type"] == assessment_type:
                template_id = tid
                break
        
        if not template_id:
            template_id = self._create_mock_template(assessment_type)
        
        # Create assessment record
        assessment = {
            "id": assessment_id,
            "patient_id": patient_id,
            "clinician_id": clinician_id,
            "assessment_type": assessment_type,
            "template_id": template_id,
            "status": "created",
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "updated_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "completed_at": None,
            "data": initial_data or {},
            "scores": {},
            "flags": []
        }
        
        self._assessments[assessment_id] = assessment
        
        return {
            "assessment_id": assessment_id,
            "patient_id": patient_id,
            "status": "created",
            "template_id": template_id
        }
    
    def get_assessment(self, assessment_id: str) -> Dict[str, Any]:
        """Get information about an assessment."""
        if not self._initialized:
            raise Exception("Service not initialized")
            
        if not assessment_id:
            raise ValueError("Assessment ID is required")
        
        assessment = self._assessments.get(assessment_id)
        if not assessment:
            raise KeyError(f"Assessment not found: {assessment_id}")
        
        return {
            "assessment_id": assessment["id"],
            "patient_id": assessment["patient_id"],
            "clinician_id": assessment["clinician_id"],
            "assessment_type": assessment["assessment_type"],
            "status": assessment["status"],
            "created_at": assessment["created_at"],
            "updated_at": assessment["updated_at"],
            "completed_at": assessment["completed_at"],
            "data": assessment["data"],
            "scores": assessment["scores"],
            "flags": assessment["flags"]
        }
    
    def update_assessment(
        self,
        assessment_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an assessment with new data."""
        if not self._initialized:
            raise Exception("Service not initialized")
            
        if not assessment_id:
            raise ValueError("Assessment ID is required")
        
        assessment = self._assessments.get(assessment_id)
        if not assessment:
            raise KeyError(f"Assessment not found: {assessment_id}")
        
        if assessment["status"] == "completed":
            raise ValueError("Cannot update completed assessment")
        
        # Update data
        assessment["data"].update(data)
        assessment["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()
        
        # Check for simple completion
        if len(assessment["data"]) >= 3 and assessment["status"] == "created":
            assessment["status"] = "in_progress"
        
        return {
            "assessment_id": assessment["id"],
            "patient_id": assessment["patient_id"],
            "status": assessment["status"],
            "updated_at": assessment["updated_at"]
        }
    
    def complete_assessment(
        self,
        assessment_id: str,
        completion_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Complete an assessment."""
        if not self._initialized:
            raise Exception("Service not initialized")
            
        if not assessment_id:
            raise ValueError("Assessment ID is required")
        
        assessment = self._assessments.get(assessment_id)
        if not assessment:
            raise KeyError(f"Assessment not found: {assessment_id}")
        
        if assessment["status"] == "completed":
            raise ValueError("Assessment already completed")
        
        # Update with completion data
        if completion_data:
            assessment["data"].update(completion_data)
        
        # Mark as completed
        assessment["status"] = "completed"
        assessment["completed_at"] = datetime.datetime.now(datetime.UTC).isoformat()
        assessment["updated_at"] = assessment["completed_at"]
        
        # Generate mock scores
        assessment["scores"] = self._generate_mock_scores(assessment)
        
        return {
            "assessment_id": assessment["id"],
            "patient_id": assessment["patient_id"],
            "status": "completed",
            "completed_at": assessment["completed_at"],
            "scores": assessment["scores"]
        }
    
    def analyze_assessment(
        self,
        assessment_id: str,
        analysis_type: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze an assessment."""
        if not self._initialized:
            raise Exception("Service not initialized")
            
        if not assessment_id:
            raise ValueError("Assessment ID is required")
        
        assessment = self._assessments.get(assessment_id)
        if not assessment:
            raise KeyError(f"Assessment not found: {assessment_id}")
        
        analysis_type = analysis_type or "general"
        
        # Generate mock analysis result
        result = {
            "analysis_type": analysis_type,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "summary": f"Mock analysis of {analysis_type} type for assessment {assessment_id}",
            "details": {},
            "recommendations": []
        }
        
        if analysis_type == "clinical":
            result["details"]["clinical_significance"] = "moderate"
            result["recommendations"].append("Consider follow-up assessment")
        
        if assessment["assessment_type"] == "depression":
            result["details"]["depression_indicators"] = ["mood", "sleep", "appetite"]
            if "phq9_9" in assessment["data"] and assessment["data"]["phq9_9"] > 1:
                result["details"]["risk_level"] = "moderate"
                result["recommendations"].append("Evaluate suicide risk")
        
        return {
            "assessment_id": assessment["id"],
            "patient_id": assessment["patient_id"],
            "result": result
        }
    
    def get_assessment_history(
        self,
        patient_id: str,
        assessment_type: Optional[str] = None,
        limit: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get assessment history for a patient."""
        if not self._initialized:
            raise Exception("Service not initialized")
            
        if not patient_id:
            raise ValueError("Patient ID is required")
        
        # Filter by patient ID and assessment type
        history = []
        for assessment in self._assessments.values():
            if assessment["patient_id"] == patient_id:
                if assessment_type and assessment["assessment_type"] != assessment_type:
                    continue
                
                history.append({
                    "assessment_id": assessment["id"],
                    "assessment_type": assessment["assessment_type"],
                    "status": assessment["status"],
                    "created_at": assessment["created_at"],
                    "completed_at": assessment["completed_at"]
                })
        
        # Sort by created_at in descending order
        history.sort(key=lambda a: a["created_at"], reverse=True)
        
        # Apply limit
        if limit and limit > 0:
            history = history[:limit]
        
        return {
            "patient_id": patient_id,
            "assessment_type": assessment_type,
            "count": len(history),
            "history": history
        }
    
    def create_form_template(
        self,
        name: str,
        form_type: str,
        fields: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new assessment form template."""
        if not self._initialized:
            raise Exception("Service not initialized")
            
        if not name or not form_type or not fields:
            raise ValueError("Name, form type, and fields are required")
        
        template_id = str(uuid.uuid4())
        
        template = {
            "id": template_id,
            "name": name,
            "form_type": form_type,
            "fields": fields,
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "metadata": metadata or {}
        }
        
        self._form_templates[template_id] = template
        
        return {
            "template_id": template_id,
            "name": name,
            "form_type": form_type,
            "field_count": len(fields)
        }
    
    def get_form_template(
        self,
        template_id: str
    ) -> Dict[str, Any]:
        """Get a form template."""
        if not self._initialized:
            raise Exception("Service not initialized")
            
        if not template_id:
            raise ValueError("Template ID is required")
        
        template = self._form_templates.get(template_id)
        if not template:
            raise KeyError(f"Template not found: {template_id}")
        
        return template
    
    def list_form_templates(
        self,
        form_type: Optional[str] = None,
        limit: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List available form templates."""
        if not self._initialized:
            raise Exception("Service not initialized")
        
        # Filter by form type
        templates = []
        for template in self._form_templates.values():
            if form_type and template["form_type"] != form_type:
                continue
            
            templates.append({
                "id": template["id"],
                "name": template["name"],
                "form_type": template["form_type"],
                "field_count": len(template["fields"])
            })
        
        # Sort by name
        templates.sort(key=lambda t: t["name"])
        
        # Apply limit
        if limit and limit > 0:
            templates = templates[:limit]
        
        return {
            "count": len(templates),
            "templates": templates
        }
    
    def calculate_score(
        self,
        assessment_id: str,
        scoring_method: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate score for an assessment."""
        if not self._initialized:
            raise Exception("Service not initialized")
            
        if not assessment_id:
            raise ValueError("Assessment ID is required")
        
        assessment = self._assessments.get(assessment_id)
        if not assessment:
            raise KeyError(f"Assessment not found: {assessment_id}")
        
        scoring_method = scoring_method or "standard"
        
        # Generate mock scores
        scores = self._generate_mock_scores(assessment)
        
        # Update assessment scores
        assessment["scores"] = scores
        
        return {
            "assessment_id": assessment["id"],
            "patient_id": assessment["patient_id"],
            "scoring_method": scoring_method,
            "scores": scores
        }
    
    def generate_report(
        self,
        assessment_id: str,
        report_type: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a report for an assessment."""
        if not self._initialized:
            raise Exception("Service not initialized")
            
        if not assessment_id:
            raise ValueError("Assessment ID is required")
        
        assessment = self._assessments.get(assessment_id)
        if not assessment:
            raise KeyError(f"Assessment not found: {assessment_id}")
        
        report_type = report_type or "summary"
        
        # Check if assessment is completed for certain report types
        if report_type in ["detailed", "clinical"] and assessment["status"] != "completed":
            raise ValueError(f"Assessment not completed for report type: {report_type}")
        
        # Generate mock report
        report = {
            "title": f"{report_type.capitalize()} Report",
            "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "assessment_id": assessment["id"],
            "patient_id": assessment["patient_id"],
            "assessment_type": assessment["assessment_type"],
            "status": assessment["status"],
            "content": f"Mock {report_type} report content for assessment {assessment_id}"
        }
        
        if assessment["scores"]:
            report["scores"] = assessment["scores"]
        
        return {
            "assessment_id": assessment["id"],
            "report_type": report_type,
            "report": report
        }
    
    def _setup_mock_templates(self) -> None:
        """Setup mock templates for testing."""
        # PHQ-9 template
        phq9_fields = [
            {
                "id": "phq9_1",
                "type": "choice",
                "question": "Little interest or pleasure in doing things",
                "choices": [
                    {"value": 0, "label": "Not at all"},
                    {"value": 1, "label": "Several days"},
                    {"value": 2, "label": "More than half the days"},
                    {"value": 3, "label": "Nearly every day"}
                ],
                "required": True
            },
            {
                "id": "phq9_9",
                "type": "choice",
                "question": "Thoughts that you would be better off dead, or of hurting yourself",
                "choices": [
                    {"value": 0, "label": "Not at all"},
                    {"value": 1, "label": "Several days"},
                    {"value": 2, "label": "More than half the days"},
                    {"value": 3, "label": "Nearly every day"}
                ],
                "required": True,
                "flag": True
            }
        ]
        
        phq9_template = {
            "id": str(uuid.uuid4()),
            "name": "PHQ-9 Depression Scale",
            "form_type": "depression",
            "fields": phq9_fields,
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "metadata": {
                "description": "Patient Health Questionnaire-9 for depression screening"
            }
        }
        
        # GAD-7 template
        gad7_fields = [
            {
                "id": "gad7_1",
                "type": "choice",
                "question": "Feeling nervous, anxious, or on edge",
                "choices": [
                    {"value": 0, "label": "Not at all"},
                    {"value": 1, "label": "Several days"},
                    {"value": 2, "label": "More than half the days"},
                    {"value": 3, "label": "Nearly every day"}
                ],
                "required": True
            }
        ]
        
        gad7_template = {
            "id": str(uuid.uuid4()),
            "name": "GAD-7 Anxiety Scale",
            "form_type": "anxiety",
            "fields": gad7_fields,
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "metadata": {
                "description": "Generalized Anxiety Disorder 7-item scale"
            }
        }
        
        # Store templates
        self._form_templates[phq9_template["id"]] = phq9_template
        self._form_templates[gad7_template["id"]] = gad7_template
    
    def _create_mock_template(self, form_type: str) -> str:
        """Create a mock template for a form type."""
        template_id = str(uuid.uuid4())
        
        template = {
            "id": template_id,
            "name": f"{form_type.capitalize()} Assessment",
            "form_type": form_type,
            "fields": [
                {
                    "id": f"{form_type}_1",
                    "type": "text",
                    "question": "Mock question 1",
                    "required": True
                },
                {
                    "id": f"{form_type}_2",
                    "type": "choice",
                    "question": "Mock question 2",
                    "choices": [
                        {"value": 0, "label": "None"},
                        {"value": 1, "label": "Mild"},
                        {"value": 2, "label": "Moderate"},
                        {"value": 3, "label": "Severe"}
                    ],
                    "required": True
                }
            ],
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "metadata": {
                "description": f"Mock template for {form_type} assessment"
            }
        }
        
        self._form_templates[template_id] = template
        
        return template_id
    
    def _generate_mock_scores(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock scores for an assessment."""
        scores = {}
        
        if assessment["assessment_type"] == "depression":
            # Generate PHQ-9 scores
            phq9_total = 0
            for i in range(1, 10):
                field_id = f"phq9_{i}"
                if field_id in assessment["data"]:
                    value = assessment["data"][field_id]
                    if isinstance(value, (int, float)):
                        phq9_total += value
            
            # If no data, generate random score
            if phq9_total == 0:
                phq9_total = int(uuid.uuid4().int % 27)  # Random score between 0-27
            
            scores["phq9_total"] = phq9_total
            
            # Determine severity
            if phq9_total >= 20:
                scores["phq9_severity"] = "severe"
            elif phq9_total >= 15:
                scores["phq9_severity"] = "moderately_severe"
            elif phq9_total >= 10:
                scores["phq9_severity"] = "moderate"
            elif phq9_total >= 5:
                scores["phq9_severity"] = "mild"
            else:
                scores["phq9_severity"] = "minimal"
        
        elif assessment["assessment_type"] == "anxiety":
            # Generate GAD-7 scores
            gad7_total = 0
            for i in range(1, 8):
                field_id = f"gad7_{i}"
                if field_id in assessment["data"]:
                    value = assessment["data"][field_id]
                    if isinstance(value, (int, float)):
                        gad7_total += value
            
            # If no data, generate random score
            if gad7_total == 0:
                gad7_total = int(uuid.uuid4().int % 21)  # Random score between 0-21
            
            scores["gad7_total"] = gad7_total
            
            # Determine severity
            if gad7_total >= 15:
                scores["gad7_severity"] = "severe"
            elif gad7_total >= 10:
                scores["gad7_severity"] = "moderate"
            elif gad7_total >= 5:
                scores["gad7_severity"] = "mild"
            else:
                scores["gad7_severity"] = "minimal"
        
        else:
            # Generate generic score
            total = int(uuid.uuid4().int % 100)  # Random score between 0-99
            scores[f"{assessment['assessment_type']}_score"] = total
        
        return scores