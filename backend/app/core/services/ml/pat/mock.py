# -*- coding: utf-8 -*-
"""
Mock PAT (Patient Assessment Tool) Service Implementation.

This module implements a mock version of the PAT interface for testing.
"""

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

from app.core.services.ml.pat.exceptions import InitializationError, ValidationError, ResourceNotFoundError
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
            raise InitializationError("Mock PAT service not initialized")
    
    def _validate_device_info(self, device_info: Dict[str, Any]) -> None:
        """Validate actigraphy device info."""
        if not device_info or not isinstance(device_info, dict):
            raise ValidationError("Device info must be a non-empty dictionary")
            
        required_fields = ["device_type", "manufacturer"]
        for field in required_fields:
            if field not in device_info:
                raise ValidationError(f"Device info missing required field: {field}")
    
    def _validate_analysis_types(self, analysis_types: List[str]) -> None:
        """Validate analysis types."""
        if not analysis_types or not isinstance(analysis_types, list):
            raise ValidationError("Analysis types must be a non-empty list")
            
        valid_types = ["sleep", "activity", "stress", "movement"]
        for analysis_type in analysis_types:
            if analysis_type not in valid_types:
                raise ValidationError(f"Invalid analysis type: {analysis_type}")
                
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
            "status": "draft",
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "updated_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "data": initial_data or {},
            "score": None,
            "summary": None
        }
        
        # Store in memory
        if not hasattr(self, "_assessment_db"):
            self._assessment_db = {}
        
        self._assessment_db[assessment_id] = assessment
        
        # Also store in patient index
        patient_key = f"patient:{patient_id}"
        if patient_key not in self._assessment_db:
            self._assessment_db[patient_key] = []
        
        self._assessment_db[patient_key].append(assessment_id)
        
        # Return assessment data to caller
        return assessment
    
    def get_assessment(self, assessment_id: str) -> Dict[str, Any]:
        """Get assessment by ID."""
        self._check_initialized()
        
        if not hasattr(self, "_assessment_db"):
            self._assessment_db = {}
        
        if assessment_id not in self._assessment_db:
            from app.core.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(f"Assessment not found: {assessment_id}")
        
        return self._assessment_db[assessment_id]
    
    def update_assessment(
        self,
        assessment_id: str,
        data: Dict[str, Any],
        complete: bool = False
    ) -> Dict[str, Any]:
        """Update an existing assessment."""
        self._check_initialized()
        
        # Get current assessment (raises if not found)
        assessment = self.get_assessment(assessment_id)
        
        # Update data fields
        assessment["data"].update(data)
        assessment["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()
        
        # Complete assessment if requested
        if complete:
            assessment["status"] = "completed"
            
            # Generate mock score and summary when completed
            template = self._form_templates.get(assessment["template_id"], {})
            score_range = template.get("score_range", (0, 100))
            
            import random
            assessment["score"] = random.randint(score_range[0], score_range[1])
            assessment["summary"] = f"Mock assessment summary for {assessment['assessment_type']}"
        
        # Save changes
        self._assessment_db[assessment_id] = assessment
        
        return assessment
    
    def get_patient_assessments(
        self,
        patient_id: str,
        assessment_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get assessments for a patient."""
        self._check_initialized()
        
        if not hasattr(self, "_assessment_db"):
            self._assessment_db = {}
        
        patient_key = f"patient:{patient_id}"
        assessment_ids = self._assessment_db.get(patient_key, [])
        
        # Fetch full assessment data
        assessments = []
        for assessment_id in assessment_ids:
            try:
                assessment = self.get_assessment(assessment_id)
                
                # Apply filters
                if assessment_type and assessment["assessment_type"] != assessment_type:
                    continue
                
                if status and assessment["status"] != status:
                    continue
                
                assessments.append(assessment)
            except Exception:
                # Skip invalid assessments
                continue
        
        # Apply pagination
        total = len(assessments)
        paginated = assessments[offset:offset+limit]
        
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "assessments": paginated
        }
    
    def get_assessment_form_template(self, template_id: str) -> Dict[str, Any]:
        """Get an assessment form template."""
        self._check_initialized()
        
        if template_id not in self._form_templates:
            from app.core.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(f"Template not found: {template_id}")
        
        return self._form_templates[template_id]
    
    def list_assessment_templates(
        self,
        form_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List available assessment templates."""
        self._check_initialized()
        
        # Filter by form type if specified
        templates = []
        for template_id, template in self._form_templates.items():
            if form_type and template["form_type"] != form_type:
                continue
            
            template_copy = template.copy()
            template_copy["id"] = template_id
            templates.append(template_copy)
        
        # Apply pagination
        total = len(templates)
        paginated = templates[offset:offset+limit]
        
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "templates": paginated
        }
    
    def _setup_mock_templates(self) -> None:
        """Setup default assessment form templates for testing."""
        self._form_templates = {
            "template:phq-9": {
                "name": "PHQ-9 Depression Screening",
                "form_type": "depression_screening",
                "version": "1.0",
                "fields": [
                    {
                        "id": "q1",
                        "type": "scale",
                        "label": "Little interest or pleasure in doing things",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    # Additional questions would be here in a real template
                ],
                "scoring": {
                    "ranges": [
                        {"min": 0, "max": 4, "label": "Minimal depression"},
                        {"min": 5, "max": 9, "label": "Mild depression"},
                        {"min": 10, "max": 14, "label": "Moderate depression"},
                        {"min": 15, "max": 19, "label": "Moderately severe depression"},
                        {"min": 20, "max": 27, "label": "Severe depression"}
                    ]
                },
                "score_range": (0, 27)
            },
            "template:gad-7": {
                "name": "GAD-7 Anxiety Screening",
                "form_type": "anxiety_screening",
                "version": "1.0",
                "fields": [
                    {
                        "id": "q1",
                        "type": "scale",
                        "label": "Feeling nervous, anxious, or on edge",
                        "options": [
                            {"value": 0, "label": "Not at all"},
                            {"value": 1, "label": "Several days"},
                            {"value": 2, "label": "More than half the days"},
                            {"value": 3, "label": "Nearly every day"}
                        ]
                    },
                    # Additional questions would be here in a real template
                ],
                "scoring": {
                    "ranges": [
                        {"min": 0, "max": 4, "label": "Minimal anxiety"},
                        {"min": 5, "max": 9, "label": "Mild anxiety"},
                        {"min": 10, "max": 14, "label": "Moderate anxiety"},
                        {"min": 15, "max": 21, "label": "Severe anxiety"}
                    ]
                },
                "score_range": (0, 21)
            }
        }
    
    def _create_mock_template(self, form_type: str) -> str:
        """Create a mock template for the specified form type."""
        template_id = f"template:{form_type.lower()}"
        
        self._form_templates[template_id] = {
            "name": f"{form_type} Assessment",
            "form_type": form_type,
            "version": "1.0",
            "fields": [
                {
                    "id": "q1",
                    "type": "scale",
                    "label": "Sample question 1",
                    "options": [
                        {"value": 0, "label": "Not at all"},
                        {"value": 1, "label": "Somewhat"},
                        {"value": 2, "label": "Very much"}
                    ]
                },
                {
                    "id": "q2",
                    "type": "text",
                    "label": "Sample open-ended question"
                }
            ],
            "scoring": {
                "ranges": [
                    {"min": 0, "max": 3, "label": "Low"},
                    {"min": 4, "max": 7, "label": "Medium"},
                    {"min": 8, "max": 10, "label": "High"}
                ]
            },
            "score_range": (0, 10)
        }
        
        return template_id
    
    def generate_report(
        self,
        patient_id: str,
        report_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        assessments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate a patient report."""
        self._check_initialized()
        
        # Get assessments to include in report
        included_assessments = []
        
        if assessments:
            # Specific assessments requested
            for assessment_id in assessments:
                try:
                    assessment = self.get_assessment(assessment_id)
                    if assessment["patient_id"] == patient_id:
                        included_assessments.append(assessment)
                except Exception:
                    # Skip invalid assessments
                    continue
        else:
            # Get all assessments in date range
            patient_assessments = self.get_patient_assessments(
                patient_id=patient_id,
                limit=100,
                offset=0
            )["assessments"]
            
            # Filter by date if needed
            if start_date or end_date:
                from datetime import datetime
                
                start = None
                if start_date:
                    start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                
                end = None
                if end_date:
                    end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                
                for assessment in patient_assessments:
                    created = datetime.fromisoformat(assessment["created_at"].replace("Z", "+00:00"))
                    
                    if start and created < start:
                        continue
                    
                    if end and created > end:
                        continue
                    
                    included_assessments.append(assessment)
            else:
                included_assessments = patient_assessments
        
        # Generate report ID
        report_id = str(uuid.uuid4())
        
        # Create mock report
        report = {
            "id": report_id,
            "patient_id": patient_id,
            "report_type": report_type,
            "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "start_date": start_date,
            "end_date": end_date,
            "assessments": [a["id"] for a in included_assessments],
            "summary": f"Mock {report_type} report for patient {patient_id}",
            "sections": [
                {
                    "title": "Assessment Overview",
                    "content": f"Patient completed {len(included_assessments)} assessments."
                },
                {
                    "title": "Recommendations",
                    "content": "Mock recommendations based on assessment results."
                }
            ]
        }
        
        # Store report
        if not hasattr(self, "_reports"):
            self._reports = {}
        
        self._reports[report_id] = report
        
        # Also store in patient index
        patient_key = f"patient_reports:{patient_id}"
        if patient_key not in self._reports:
            self._reports[patient_key] = []
        
        self._reports[patient_key].append(report_id)
        
        return report
    
    def get_report(self, report_id: str) -> Dict[str, Any]:
        """Get a report by ID."""
        self._check_initialized()
        
        if not hasattr(self, "_reports"):
            self._reports = {}
        
        if report_id not in self._reports:
            from app.core.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(f"Report not found: {report_id}")
        
        return self._reports[report_id]
    
    def get_patient_reports(
        self,
        patient_id: str,
        report_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get reports for a patient."""
        self._check_initialized()
        
        if not hasattr(self, "_reports"):
            self._reports = {}
        
        patient_key = f"patient_reports:{patient_id}"
        report_ids = self._reports.get(patient_key, [])
        
        # Fetch full report data
        reports = []
        for report_id in report_ids:
            try:
                report = self.get_report(report_id)
                
                # Apply filters
                if report_type and report["report_type"] != report_type:
                    continue
                
                reports.append(report)
            except Exception:
                # Skip invalid reports
                continue
        
        # Apply pagination
        total = len(reports)
        paginated = reports[offset:offset+limit]
        
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "reports": paginated
        }
    
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
        if not patient_id:
            raise ValueError("Patient ID is required")
        
        if not readings or not isinstance(readings, list):
            raise ValidationError("Readings must be a non-empty list")
        
        if sampling_rate_hz <= 0:
            raise ValidationError("Sampling rate must be positive")
        
        # Basic shape validation
        for reading in readings:
            if not all(k in reading for k in ['x', 'y', 'z']):
                raise ValidationError("Each reading must contain x, y, z values")
                
        # Validate device info and analysis types
        self._validate_device_info(device_info)
        self._validate_analysis_types(analysis_types)
        
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
            "device_info": device_info,
            "analysis_types": analysis_types,
            "data_summary": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_minutes": 120,  # Mock duration
                "samples_count": len(readings),
                "sampling_rate_hz": sampling_rate_hz
            },
            "results": {}
        }
        
        # Generate mock results for each analysis type
        for analysis_type in analysis_types:
            if analysis_type == "sleep":
                result["results"]["sleep"] = {
                    "total_sleep_time": 360,  # minutes
                    "sleep_efficiency": 85,  # percentage
                    "sleep_onset_latency": 15,  # minutes
                    "wake_after_sleep_onset": 45,  # minutes
                    "sleep_stages": {
                        "awake": 60,  # minutes
                        "light": 180,
                        "deep": 120,
                        "rem": 60
                    }
                }
            elif analysis_type == "activity":
                result["results"]["activity"] = {
                    "steps_count": 8500,
                    "active_minutes": 75,
                    "sedentary_minutes": 480,
                    "calories_burned": 1800,
                    "activity_score": 75  # percentage
                }
            elif analysis_type == "stress":
                result["results"]["stress"] = {
                    "average_stress_level": 45,  # scale 0-100
                    "stress_events": [
                        {"start_time": "2025-03-27T14:30:00Z", "end_time": "2025-03-27T15:00:00Z", "level": 75},
                        {"start_time": "2025-03-27T18:15:00Z", "end_time": "2025-03-27T18:45:00Z", "level": 80}
                    ],
                    "recovery_periods": [
                        {"start_time": "2025-03-27T17:00:00Z", "end_time": "2025-03-27T17:30:00Z", "quality": "good"}
                    ]
                }
            elif analysis_type == "movement":
                result["results"]["movement"] = {
                    "movement_patterns": [
                        {"type": "walking", "duration_minutes": 45, "intensity": "moderate"},
                        {"type": "running", "duration_minutes": 20, "intensity": "high"},
                        {"type": "stationary", "duration_minutes": 480, "intensity": "none"}
                    ],
                    "movement_quality": {
                        "gait_stability": 85,  # percentage
                        "stride_regularity": 80,
                        "symmetry": 90
                    }
                }
        
        # Store analysis
        if not hasattr(self, "_analyses"):
            self._analyses = {}
        
        self._analyses[analysis_id] = result
        
        # Also store in patient index
        if not hasattr(self, "_patient_analyses"):
            self._patient_analyses = {}
        
        if patient_id not in self._patient_analyses:
            self._patient_analyses[patient_id] = {}
        
        self._patient_analyses[patient_id][analysis_id] = result
        
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
        raise ResourceNotFoundError(f"Analysis not found: {analysis_id}")
    
    def get_actigraphy_embeddings(
        self,
        patient_id: str,
        readings: List[Dict[str, Any]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float
    ) -> Dict[str, Any]:
        """Generate embeddings from actigraphy data.
        
        Args:
            patient_id: Unique identifier for the patient
            readings: List of accelerometer readings
            start_time: ISO-8601 formatted start time
            end_time: ISO-8601 formatted end time
            sampling_rate_hz: Sampling rate in Hz
        
        Returns:
            Dictionary containing embedding vector and metadata
        """
        self._check_initialized()
        
        # Validate inputs
        if not patient_id:
            raise ValidationError("Patient ID is required")
        
        if not readings or not isinstance(readings, list):
            raise ValidationError("Readings must be a non-empty list")
        
        if sampling_rate_hz <= 0:
            raise ValidationError("Sampling rate must be positive")
        
        # Generate mock embedding
        embedding_id = str(uuid.uuid4())
        embedding_dim = 384  # Default dimension
        
        # Create random embedding vector
        import random
        embedding = [random.uniform(-0.9, 0.9) for _ in range(embedding_dim)]
        
        # Create result
        result = {
            "embedding_id": embedding_id,
            "patient_id": patient_id,
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "embedding_type": "actigraphy",
            "embedding_dim": embedding_dim,
            "embedding": embedding,
            "metadata": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_minutes": 1440,  # 24 hours
                "sampling_rate_hz": sampling_rate_hz,
                "readings_count": len(readings)
            }
        }
        
        # Store embedding
        if not hasattr(self, "_embeddings"):
            self._embeddings = {}
        
        self._embeddings[embedding_id] = result
        
        return result
    
    def get_patient_analyses(
        self,
        patient_id: str,
        analysis_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get actigraphy analyses for a patient."""
        self._check_initialized()
        
        if not hasattr(self, "_patient_analyses"):
            self._patient_analyses = {}
        
        if patient_id not in self._patient_analyses:
            return {
                "analyses": [],
                "pagination": {
                    "total": 0,
                    "offset": offset,
                    "limit": limit,
                    "has_more": False
                }
            }
        
        # Get all analyses for the patient
        all_analyses = list(self._patient_analyses[patient_id].values())
        
        # Filter by analysis types if specified
        if analysis_types:
            filtered_analyses = []
            for analysis in all_analyses:
                # Check if any of the requested types are in this analysis
                if any(t in analysis["analysis_types"] for t in analysis_types):
                    filtered_analyses.append(analysis)
            
            all_analyses = filtered_analyses
        
        # Filter by date range if specified
        if start_date or end_date:
            from datetime import datetime
            
            start = None
            if start_date:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            
            end = None
            if end_date:
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            
            filtered_analyses = []
            for analysis in all_analyses:
                created = datetime.fromisoformat(analysis["created_at"].replace("Z", "+00:00"))
                
                if start and created < start:
                    continue
                
                if end and created > end:
                    continue
                
                filtered_analyses.append(analysis)
            
            all_analyses = filtered_analyses
        
        # Sort analyses by created_at (newest first)
        all_analyses.sort(key=lambda a: a["created_at"], reverse=True)
        
        # Apply pagination
        total = len(all_analyses)
        paginated = all_analyses[offset:offset+limit]
        
        # Calculate if there are more results
        has_more = (offset + limit) < total
        
        return {
            "analyses": paginated,
            "pagination": {
                "total": total,
                "offset": offset,
                "limit": limit,
                "has_more": has_more
            }
        }
    
    def get_actigraphy_embeddings(
        self,
        patient_id: str,
        readings: List[Dict[str, float]],
        start_time: str,
        end_time: str,
        sampling_rate_hz: float
    ) -> Dict[str, Any]:
        """Generate embeddings from actigraphy data.
        
        Args:
            patient_id: Unique identifier for the patient
            readings: List of accelerometer readings
            start_time: ISO-8601 formatted start time
            end_time: ISO-8601 formatted end time
            sampling_rate_hz: Sampling rate in Hz
        
        Returns:
            Dictionary containing embedding vector and metadata
        """
        self._check_initialized()
        
        # Validate inputs
        if not patient_id:
            raise ValidationError("Patient ID is required")
        
        if not readings or not isinstance(readings, list):
            raise ValidationError("Readings must be a non-empty list")
        
        if sampling_rate_hz <= 0:
            raise ValidationError("Sampling rate must be positive")
        
        # Generate mock embedding with fixed dimension for tests
        embedding_id = str(uuid.uuid4())
        embedding_dim = 384  # Fixed dimension for test compatibility
        
        # Generate mock embedding
        import random
        embedding = []
        for i in range(embedding_dim):
            value = random.uniform(-0.9, 0.9)
            embedding.append(value)
        
        # Create result
        result = {
            "embedding_id": embedding_id,
            "patient_id": patient_id,
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "embedding_type": "actigraphy",
            "embedding_dim": embedding_dim,
            "embedding": embedding,
            "metadata": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_minutes": 1440,  # 24 hours
                "sampling_rate_hz": sampling_rate_hz,
                "readings_count": len(readings)
            }
        }
        
        # Store embeddings for retrieval
        if not hasattr(self, "_embeddings"):
            self._embeddings = {}
        
        self._embeddings[embedding_id] = result
        
        return result
    
    def compare_embeddings(
        self,
        embedding_a: List[float],
        embedding_b: List[float]
    ) -> Dict[str, Any]:
        """Compare two embeddings and return similarity metrics."""
        self._check_initialized()
        
        # Validate inputs
        if not embedding_a or not embedding_b:
            raise ValueError("Both embeddings must be non-empty")
        
        if len(embedding_a) != len(embedding_b):
            raise ValueError("Embeddings must have the same dimension")
        
        # Generate mock similarity metrics
        import random
        
        # Cosine similarity (0-1 where 1 is identical)
        cosine_similarity = round(random.uniform(0.6, 0.95), 4)
        
        # Euclidean distance (0 is identical, higher is more different)
        euclidean_distance = round(random.uniform(0.1, 2.0), 4)
        
        # Create result
        result = {
            "metrics": {
                "cosine_similarity": cosine_similarity,
                "euclidean_distance": euclidean_distance
            },
            "dimension": len(embedding_a),
            "created_at": datetime.datetime.now(datetime.UTC).isoformat()
        }
        
        return result
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the PAT model being used."""
        self._check_initialized()
        
        # For the mock service, just return static info that matches test expectations
        return {
            "name": "PAT-Mock-Model",
            "version": "1.0.0",
            "description": "Mock Patient Assessment Tool for testing",
            "supported_analysis_types": [
                "sleep",
                "activity",
                "stress",
                "circadian",
                "anomaly"
            ],
            "supported_devices": [
                "Actigraph wGT3X-BT",
                "Apple Watch",
                "Fitbit Sense",
                "Oura Ring"
            ],
            "created_at": "2025-01-01T00:00:00Z",
            "last_updated": "2025-01-01T00:00:00Z",
            "capabilities": [
                "actigraphy_analysis",
                "sleep_detection",
                "activity_classification",
                "stress_monitoring"
            ],
            "embedding_dimensions": [10, 32, 64, 128],
            "sampling_rate_range": {
                "min": 1.0,
                "max": 100.0,
                "recommended": 30.0
            },
            "provider": "NovaMind Mock Services"
        }
    
    def integrate_with_digital_twin(
        self,
        patient_id: str,
        profile_id: str,
        analysis_id: str
    ) -> Dict[str, Any]:
        """Integrate analysis results with a patient's digital twin."""
        self._check_initialized()
        
        # Verify analysis exists and belongs to the patient
        analysis = self.get_analysis_by_id(analysis_id)
        
        if analysis["patient_id"] != patient_id:
            from app.core.services.ml.pat.exceptions import AuthorizationError
            raise AuthorizationError("Analysis does not belong to the specified patient")
        
        # Create mock integration result
        integration_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.UTC).isoformat()
        
        # Create mock insights based on analysis types
        insights = []
        
        for analysis_type in analysis.get("analysis_types", []):
            if analysis_type == "sleep":
                insights.append({
                    "id": str(uuid.uuid4()),
                    "type": "sleep_pattern",
                    "description": "Sleep efficiency has improved by 15% in the last week",
                    "created_at": now,
                    "severity": "positive"
                })
            elif analysis_type == "activity":
                insights.append({
                    "id": str(uuid.uuid4()),
                    "type": "activity_level",
                    "description": "Activity level is below recommended targets",
                    "created_at": now,
                    "severity": "warning"
                })
        
        result = {
            "integration_id": integration_id,
            "patient_id": patient_id,
            "profile_id": profile_id,
            "analysis_id": analysis_id,
            "status": "completed",
            "created_at": now,
            "updated_profile": {
                "profile_id": profile_id,
                "patient_id": patient_id,
                "last_updated": now,
                "insights": insights
            }
        }
        
        # Store integration record
        if not hasattr(self, "_integrations"):
            self._integrations = {}
        
        self._integrations[integration_id] = result
        
        # Also store in patient index
        if not hasattr(self, "_patient_integrations"):
            self._patient_integrations = {}
        
        if patient_id not in self._patient_integrations:
            self._patient_integrations[patient_id] = {}
        
        self._patient_integrations[patient_id][integration_id] = result
        
        return result
        
    # Implementing the required abstract methods from PATInterface
    
    def analyze_assessment(
        self,
        assessment_id: str,
        analysis_type: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze an assessment."""
        self._check_initialized()
        
        # Get assessment (raises if not found)
        assessment = self.get_assessment(assessment_id)
        
        # Generate mock analysis result
        result = {
            "assessment_id": assessment_id,
            "analysis_type": analysis_type or "standard",
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "results": {
                "risk_level": "moderate",
                "suggested_interventions": [
                    "Cognitive Behavioral Therapy",
                    "Medication review"
                ],
                "notes": "Mock analysis results for testing purposes"
            }
        }
        
        return result
    
    def calculate_score(
        self,
        assessment_id: str,
        scoring_method: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate score for an assessment."""
        self._check_initialized()
        
        # Get assessment (raises if not found)
        assessment = self.get_assessment(assessment_id)
        
        # Generate mock scoring result
        import random
        score = random.randint(0, 100)
        
        result = {
            "assessment_id": assessment_id,
            "scoring_method": scoring_method or "standard",
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "scores": {
                "total_score": score,
                "subscores": {
                    "cognitive": random.randint(0, 100),
                    "affective": random.randint(0, 100),
                    "somatic": random.randint(0, 100)
                }
            },
            "interpretation": f"Mock score interpretation: {score}/100"
        }
        
        return result
    
    def complete_assessment(
        self,
        assessment_id: str,
        completion_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Complete an assessment."""
        self._check_initialized()
        
        # Update assessment with completion data if provided
        if completion_data:
            assessment = self.update_assessment(assessment_id, completion_data, complete=True)
        else:
            assessment = self.update_assessment(assessment_id, {}, complete=True)
        
        return assessment
    
    def get_assessment_history(
        self,
        patient_id: str,
        assessment_type: Optional[str] = None,
        limit: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get assessment history for a patient."""
        self._check_initialized()
        
        # Use existing method to get patient assessments
        limit_val = limit or 10
        result = self.get_patient_assessments(
            patient_id=patient_id,
            assessment_type=assessment_type,
            limit=limit_val,
            offset=0
        )
        
        return result
    
    def create_form_template(
        self,
        name: str,
        form_type: str,
        fields: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new assessment form template."""
        self._check_initialized()
        
        if not name or not form_type or not fields:
            raise ValueError("Name, form type, and fields are required")
        
        # Create template ID
        template_id = f"template:{str(uuid.uuid4())}"
        
        # Create template
        template = {
            "id": template_id,
            "name": name,
            "form_type": form_type,
            "fields": fields,
            "metadata": metadata or {},
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "version": "1.0"
        }
        
        # Store template
        self._form_templates[template_id] = template
        
        return template
    
    def get_form_template(
        self,
        template_id: str
    ) -> Dict[str, Any]:
        """Get a form template."""
        self._check_initialized()
        
        # Just use existing method
        return self.get_assessment_form_template(template_id)
    
    def list_form_templates(
        self,
        form_type: Optional[str] = None,
        limit: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List available form templates."""
        self._check_initialized()
        
        # Just use existing method
        limit_val = limit or 10
        return self.list_assessment_templates(
            form_type=form_type,
            limit=limit_val,
            offset=0
        )