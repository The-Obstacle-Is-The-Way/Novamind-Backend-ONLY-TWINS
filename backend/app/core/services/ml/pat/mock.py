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
        
    def _check_initialized(self) -> None:
        """Check if the service is initialized and raise exception if not."""
        if not self._initialized:
            from app.core.exceptions import InitializationError
            raise InitializationError("Mock PAT service not initialized")
    
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
    
    def analyze_actigraphy(
        self,
        patient_id: str,
        readings: List[Dict[str, float]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float,
        device_info: Dict[str, str],
        analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Analyze actigraphy readings."""
        self._check_initialized()
        # Validate inputs
        from app.core.exceptions import ValidationError
        if not patient_id:
            raise ValidationError("Patient ID is required")
        if not readings or not isinstance(readings, list):
            raise ValidationError("Readings must be a non-empty list")
        if sampling_rate_hz is None or not isinstance(sampling_rate_hz, (int, float)) or sampling_rate_hz <= 0:
            raise ValidationError("Sampling rate must be positive")
        if not device_info or not isinstance(device_info, dict):
            raise ValidationError("device_info must be a non-empty dict")
        # Device info validation relaxed: accept any provided fields
        if not analysis_types or not isinstance(analysis_types, list):
            raise ValidationError("analysis_types must be a non-empty list")
        # Validate allowed analysis types
        valid_types = ['sleep_quality', 'activity_levels', 'gait_analysis', 'tremor_analysis']
        for t in analysis_types:
            if not isinstance(t, str) or t not in valid_types:
                raise ValidationError(f"Invalid analysis type: {t}")
        # Basic shape validation for readings
        for reading in readings:
            if not all(k in reading for k in ('x', 'y', 'z')):
                raise ValidationError("Each reading must contain x, y, z values")

        # Create analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Generate mock analysis result
        result = {
            "analysis_id": analysis_id,  # Changed from 'id' to 'analysis_id' to match test expectations
            "patient_id": patient_id,
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),  # Changed from 'timestamp' to 'created_at'
            "start_time": start_time,
            "end_time": end_time,
            "status": "completed",
            "analysis_types": analysis_types,
            "device_info": device_info,
            "reading_stats": {
                "count": len(readings),
                "sampling_rate_hz": sampling_rate_hz
            },
            "results": {},  # Added to match test expectations
            "metrics": self._generate_mock_actigraphy_metrics(readings, analysis_types),
            "interpretation": self._generate_mock_interpretation(analysis_types)
        }
        
        # Add results for each analysis type - expected by tests
        for analysis_type in analysis_types:
            result["results"][analysis_type] = self._generate_mock_actigraphy_metrics(readings, [analysis_type])
        
        # Store analysis under patient's analyses AND in a flat structure
        # Initialize data structures if needed
        if not hasattr(self, "_analyses"):
            # Flat structure for direct ID lookup (for test compatibility)
            self._analyses = {}
        
        # Store analysis directly in _analyses (flat structure)
        self._analyses[analysis_id] = result
        
        # Store in hierarchical patient structure
        if not hasattr(self, "_patients_analyses"):  # Renamed to match test expectations
            self._patients_analyses = {}
            self._patient_analyses = self._patients_analyses  # Alias for backward compatibility
        
        if patient_id not in self._patients_analyses:
            self._patients_analyses[patient_id] = {}
        
        self._patients_analyses[patient_id][analysis_id] = result
        
        # Also store in actigraphy_analyses for backwards compatibility
        if not hasattr(self, "_actigraphy_analyses"):
            self._actigraphy_analyses = {}
        
        if patient_id not in self._actigraphy_analyses:
            self._actigraphy_analyses[patient_id] = {}
        
        self._actigraphy_analyses[patient_id][analysis_id] = result
        
        return result
    
    def get_actigraphy_embeddings(
        self,
        patient_id: str,
        readings: List[Dict[str, float]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float
    ) -> Dict[str, Any]:
        """Generate embeddings from actigraphy readings."""
        self._check_initialized()
        
        from app.core.exceptions import ValidationError
        # Validate inputs
        if not patient_id:
            raise ValidationError("Patient ID is required")
        if not readings or not isinstance(readings, list):
            raise ValidationError("Readings must be a non-empty list")
        if sampling_rate_hz is None or not isinstance(sampling_rate_hz, (int, float)) or sampling_rate_hz <= 0:
            raise ValidationError("Sampling rate must be positive")
        # Basic shape validation for readings
        for reading in readings:
            if not all(k in reading for k in ('x', 'y', 'z')):
                raise ValidationError("Each reading must contain x, y, z values")
        
        # Generate mock embeddings with 384 dimensions
        embedding_id = str(uuid.uuid4())
        embeddings = [0.1] * 384  # Create a 384-dimensional embedding vector
        
        # Create result
        result = {
            "embedding_id": embedding_id,
            "patient_id": patient_id,
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "embedding_type": "actigraphy",
            "embedding": embeddings,
            "embedding_dim": len(embeddings),
            "metadata": {
                "reading_count": len(readings),
                "start_time": start_time,
                "end_time": end_time,
                "sampling_rate_hz": sampling_rate_hz
            }
        }
        
        # Store embedding in the service
        if not hasattr(self, "_embeddings"):
            self._embeddings = {}
        
        self._embeddings[embedding_id] = result
        
        # Also store per patient for convenience
        if not hasattr(self, "_patient_embeddings"):
            self._patient_embeddings = {}
        
        if patient_id not in self._patient_embeddings:
            self._patient_embeddings[patient_id] = {}
        
        self._patient_embeddings[patient_id][embedding_id] = result
        
        return result
    
    def get_analysis_by_id(self, analysis_id: str) -> Dict[str, Any]:
        """Get an actigraphy analysis by ID."""
        self._check_initialized()
        
        if not hasattr(self, "_analyses"):
            self._analyses = {}
        
        # First check in the flat structure (direct lookup)
        if analysis_id in self._analyses:
            return self._analyses[analysis_id]
            
        # If not found, check in patient_analyses (hierarchical structure)
        if hasattr(self, "_patient_analyses"):
            for patient_id, analyses in self._patient_analyses.items():
                if analysis_id in analyses:
                    return analyses[analysis_id]
        
        # If still not found, check in actigraphy_analyses for backward compatibility
        if hasattr(self, "_actigraphy_analyses"):
            for patient_id, analyses in self._actigraphy_analyses.items():
                if analysis_id in analyses:
                    return analyses[analysis_id]
        
        # Analysis not found
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError(f"Analysis not found: {analysis_id}")
    
    def get_patient_analyses(
        self,
        patient_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get actigraphy analyses for a patient."""
        self._check_initialized()
        
        # Initialize structures if needed
        if not hasattr(self, "_patients_analyses"):  # Renamed to match test expectations
            self._patients_analyses = {}
            self._patient_analyses = self._patients_analyses  # Alias for backward compatibility
            
        if not hasattr(self, "_analyses"):
            self._analyses = {}
            
        # First try to get analyses from patient_analyses (hierarchical structure)
        patient_analyses = self._patients_analyses.get(patient_id, {})
        
        # If empty, try actigraphy_analyses for backward compatibility
        if not patient_analyses and hasattr(self, "_actigraphy_analyses"):
            patient_analyses = self._actigraphy_analyses.get(patient_id, {})
        
        # If still empty but we have flat structure, filter by patient_id
        if not patient_analyses and self._analyses:
            patient_analyses_list = {
                analysis_id: analysis
                for analysis_id, analysis in self._analyses.items()
                if analysis.get("patient_id") == patient_id
            }
            analyses_list = list(patient_analyses_list.values())
        else:
            analyses_list = list(patient_analyses.values())
        
        # Sort by created_at in descending order
        analyses_list.sort(key=lambda a: a["created_at"], reverse=True)
        
        # Apply pagination
        if offset is not None and offset > 0:
            analyses_list = analyses_list[offset:]
        
        if limit is not None and limit > 0:
            analyses_list = analyses_list[:limit]
        return {
            "patient_id": patient_id,
            "analyses": analyses_list,
            "pagination": {  # Added pagination info expected by tests
                "total": len(patient_analyses),
                "limit": limit or 10,
                "offset": offset or 0,
                "has_more": (offset or 0) + (limit or 10) < len(patient_analyses)
            }
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the PAT model."""
        self._check_initialized()
        
        return {
            "name": "Mock PAT Model",
            "version": "1.0.0",
            "type": "actigraphy_analysis",
            "created_at": "2025-01-01T00:00:00Z",
            "description": "Mock model for Patient Assessment Tool",
            "capabilities": [
                "actigraphy_analysis",
                "sleep_detection",
                "activity_classification",
                "digital_twin_integration"
            ],
            "supported_analysis_types": ["sleep", "activity", "stress", "circadian", "anomaly"],  # Added to match test expectations
            "supported_devices": [
                "Actigraph wGT3X-BT",
                "Apple Watch",
                "Fitbit Sense",
                "Oura Ring",
                "Generic Accelerometer"
            ],
            "metrics": {
                "accuracy": 0.95,
                "recall": 0.92,
                "precision": 0.94,
                "f1_score": 0.93
            }
        }
    
    def integrate_with_digital_twin(
        self,
        patient_id: str,
        profile_id: str,
        analysis_id: str = None,
        actigraphy_analysis: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Integrate an actigraphy analysis with a digital twin."""
        self._check_initialized()
        from app.core.exceptions import ValidationError, ResourceNotFoundError
        # Determine actigraphy_analysis from inputs
        if analysis_id:
            # fetch analysis or raise ResourceNotFoundError
            actigraphy_analysis = self.get_analysis_by_id(analysis_id)
        if actigraphy_analysis is None:
            raise ValidationError("Missing actigraphy_analysis or analysis_id")

        # Extract analysis_id
        analysis_id = actigraphy_analysis.get("analysis_id")
        if not analysis_id:
            raise ValidationError("Missing 'analysis_id' in actigraphy_analysis data")

        if actigraphy_analysis.get("patient_id") != patient_id:
            from app.core.exceptions import AuthorizationError
            raise AuthorizationError(f"Analysis {analysis_id} does not belong to patient {patient_id}")

        logger.info(f"Mock integrating analysis {analysis_id} for patient {patient_id} with profile {profile_id}")

        # Initialize integrations storage if needed
        if not hasattr(self, "_integrations"):
            self._integrations = {}

        # Check if analysis exists (using the passed data, but could also re-fetch)
        # analysis = self.get_analysis_by_id(analysis_id) # Optional: re-fetch to ensure consistency

        # Generate mock integration result
        integration_id = str(uuid.uuid4())
        integration_timestamp = datetime.datetime.now(datetime.UTC).isoformat()

        # Mock updated profile data based on analysis
        sleep_results = actigraphy_analysis.get("results", {}).get("sleep", {})
        activity_results = actigraphy_analysis.get("results", {}).get("activity", {})
        analysis_metrics = actigraphy_analysis.get("metrics", {}) # Use passed metrics

        result = {
            "integration_id": integration_id,
            "patient_id": patient_id,
            "profile_id": profile_id,
            "analysis_id": analysis_id,
            "created_at": integration_timestamp,
            "timestamp": integration_timestamp, # Align timestamp
            "status": "completed",
            "metrics_integrated": len(analysis_metrics), # Use passed metrics count
            "digital_twin_updated": True,
            "updated_profile": {
                "id": profile_id,
                "profile_id": profile_id,
                "patient_id": patient_id,
                "metrics_count": len(analysis_metrics), # Use passed metrics count
                "last_update": integration_timestamp,
                "last_updated": integration_timestamp,
                "insights": [
                     {
                         "type": "sleep",
                         "summary": f"Sleep quality appears {sleep_results.get('quality', 'average')}", # Use actual results
                         "confidence": sleep_results.get('confidence', 0.85)
                     },
                     {
                         "type": "activity",
                         "summary": f"Activity level is {activity_results.get('level', 'moderate')}", # Use actual results
                         "confidence": activity_results.get('confidence', 0.78)
                     }
                 ]
            }
        }

        # Store integration result
        self._integrations[integration_id] = {
            "integration_id": integration_id,
            "patient_id": patient_id,
            "profile_id": profile_id,
            "analysis_id": analysis_id,
            "created_at": integration_timestamp,
            "status": "completed"
        }

        return result
    
    def _generate_mock_actigraphy_metrics(
        self,
        readings: List[Dict[str, float]],
        analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Generate mock metrics for actigraphy analysis."""
        metrics = {}
        
        # Calculate some basic statistics from the readings
        x_values = [r['x'] for r in readings]
        y_values = [r['y'] for r in readings]
        z_values = [r['z'] for r in readings]
        
        metrics["x_mean"] = sum(x_values) / len(x_values) if x_values else 0
        metrics["y_mean"] = sum(y_values) / len(y_values) if y_values else 0
        metrics["z_mean"] = sum(z_values) / len(z_values) if z_values else 0
        
        # Add analysis type-specific metrics
        if "sleep" in analysis_types:
            metrics["sleep"] = {
                "total_sleep_hours": 6.5 + (uuid.uuid4().int % 30) / 10,  # Random between 6.5-9.5
                "sleep_efficiency": 0.75 + (uuid.uuid4().int % 20) / 100,  # Random between 0.75-0.95
                "deep_sleep_percentage": 0.2 + (uuid.uuid4().int % 15) / 100,  # Random between 0.2-0.35
                "rem_sleep_percentage": 0.15 + (uuid.uuid4().int % 15) / 100,  # Random between 0.15-0.3
                "awakenings": int(uuid.uuid4().int % 6)  # Random between 0-5
            }
        
        if "activity" in analysis_types:
            metrics["activity"] = {
                "steps": 7500 + (uuid.uuid4().int % 5000),  # Random between 7500-12500
                "active_minutes": 120 + (uuid.uuid4().int % 120),  # Random between 120-240
                "calories_burned": 1500 + (uuid.uuid4().int % 1000),  # Random between 1500-2500
                "distance_km": 5.0 + (uuid.uuid4().int % 50) / 10  # Random between 5.0-10.0
            }
        
        return metrics
    
    def _generate_mock_interpretation(self, analysis_types: List[str]) -> Dict[str, Any]:
        """Generate mock interpretation for actigraphy analysis."""
        interpretation = {
            "summary": "Mock interpretation of actigraphy data"
        }
        
        # Add analysis type-specific interpretations
        if "sleep" in analysis_types:
            sleep_quality = ["poor", "fair", "good", "excellent"][uuid.uuid4().int % 4]
            interpretation["sleep"] = {
                "quality": sleep_quality,
                "issues": ["difficulty falling asleep"] if sleep_quality in ["poor", "fair"] else []
            }
        
        if "activity" in analysis_types:
            activity_level = ["sedentary", "low", "moderate", "high"][uuid.uuid4().int % 4]
            interpretation["activity"] = {
                "level": activity_level,
                "meets_guidelines": activity_level in ["moderate", "high"]
            }
        
        return interpretation

    # --- Added missing abstract method implementations ---

    def detect_anomalies(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        baseline_period: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock implementation for detecting anomalies."""
        self._check_initialized()
        logger.info(f"Mock detecting anomalies for patient {patient_id}")
        # Return a simple mock response
        return {
            "patient_id": patient_id,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "anomalies_detected": [
                {
                    "type": "sleep_pattern_shift",
                    "severity": "low",
                    "timestamp": readings[-1]['timestamp'] if readings else datetime.datetime.now(datetime.UTC).isoformat(),
                    "details": "Mock anomaly: Slight shift detected."
                }
            ] if len(readings) > 50 else [], # Example condition
            "baseline_period": baseline_period
        }

    def get_activity_metrics(
        self,
        patient_id: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock implementation for getting activity metrics."""
        self._check_initialized()
        logger.info(f"Mock getting activity metrics for patient {patient_id} from {start_date} to {end_date}")
        # Return simple mock metrics
        return {
            "patient_id": patient_id,
            "start_date": start_date,
            "end_date": end_date,
            "metrics": {
                "total_steps": 15000,
                "average_steps_per_day": 5000,
                "active_minutes": 120,
                "sedentary_minutes": 600,
                "intensity_distribution": {
                    "light": 0.6,
                    "moderate": 0.3,
                    "vigorous": 0.1
                }
            }
        }

    def get_sleep_metrics(
        self,
        patient_id: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock implementation for getting sleep metrics."""
        self._check_initialized()
        logger.info(f"Mock getting sleep metrics for patient {patient_id} from {start_date} to {end_date}")
        return {
            "patient_id": patient_id,
            "start_date": start_date,
            "end_date": end_date,
            "metrics": {
                "average_duration_hours": 7.5,
                "average_efficiency": 0.85,
                "average_deep_sleep_percentage": 0.20,
                "average_rem_sleep_percentage": 0.25,
                "average_light_sleep_percentage": 0.55,
                "consistency_score": 0.7
            }
        }

    def predict_mood_state(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        historical_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock implementation for predicting mood state."""
        self._check_initialized()
        logger.info(f"Mock predicting mood state for patient {patient_id}")
        return {
            "patient_id": patient_id,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "predicted_mood": "neutral",
            "confidence": 0.65,
            "contributing_factors": ["activity_level", "sleep_regularity"]
        }
