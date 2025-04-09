# -*- coding: utf-8 -*-
"""
Mock ML Service Implementation.

This module provides mock implementations of ML services for testing purposes.
These mock implementations follow the interfaces defined in interface.py
and provide realistic responses for testing without requiring actual ML models.
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from app.core.exceptions import (
    InvalidConfigurationError,
    InvalidRequestError,
    ModelNotFoundError,
    ServiceUnavailableError,
)
from app.core.services.ml.interface import PHIDetectionInterface
from app.core.services.ml.mentalllama import BaseMentaLLaMA
from app.core.utils.logging import get_logger


# Create logger (no PHI logging)
logger = get_logger(__name__)


class MockMentaLLaMA(BaseMentaLLaMA):
    """
    Mock MentaLLaMA implementation.
    
    This class provides a mock implementation of MentaLLaMA services for testing.
    It simulates responses from various mental health analysis models and 
    implements Digital Twin functionality for patient simulation.
    """
    
    def __init__(self) -> None:
        """Initialize MockMentaLLaMA instance."""
        # Call parent class initializer
        super().__init__()
        
        # Add additional mock-specific fields
        self._model_types = [
            "general", "depression_detection", "risk_assessment",
            "sentiment_analysis", "wellness_dimensions", "digital_twin"
        ]
        self._mock_responses = {}
        self._sessions = {}
        self._digital_twins = {}
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the service with configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        try:
            # Validate that config is a non-empty dictionary
            if config is None:
                raise InvalidConfigurationError("Configuration cannot be None")
                
            if not isinstance(config, dict):
                raise InvalidConfigurationError("Configuration must be a dictionary")
                
            self._config = config
            
            # Validate mock_responses if provided
            custom_responses = self._config.get("mock_responses")
            if custom_responses is not None:
                if not isinstance(custom_responses, dict):
                    raise InvalidConfigurationError("mock_responses must be a dictionary")
                self._mock_responses = custom_responses
            else:
                self._load_default_mock_responses()
            
            self._initialized = True
            logger.info("Mock MentaLLaMA service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize mock MentaLLaMA service: {str(e)}")
            self._initialized = False
            self._config = None
            raise InvalidConfigurationError(f"Failed to initialize mock MentaLLaMA service: {str(e)}")
    
    def _load_default_mock_responses(self) -> None:
        """Load default mock responses for various model types."""
        self._mock_responses = {
            "general": self._create_general_response(),
            "depression_detection": self._create_depression_detection_response(),
            "risk_assessment": self._create_risk_assessment_response(),
            "sentiment_analysis": self._create_sentiment_analysis_response(),
            "wellness_dimensions": self._create_wellness_dimensions_response(),
            "digital_twin": self._create_digital_twin_response(),
        }
    
    def _create_general_response(self) -> Dict[str, Any]:
        """Create a default mock response for general model type."""
        return {
            "content": """Based on the provided text, I've identified several patterns that may be clinically relevant:

1. **Emotional Presentation**: The text shows a mix of anxiety and low mood, with significant worry about the future.

2. **Cognitive Patterns**: There appears to be some catastrophic thinking and overgeneralization, particularly around work performance.

3. **Behavioral Indicators**: Mentions of sleep disruption and reduced engagement in previously enjoyed activities.

4. **Relational Context**: References to strained interpersonal connections, particularly with family members.

These patterns would warrant further professional assessment to determine clinical significance. This analysis is meant to support, not replace, clinical judgment.

Remember that this is a preliminary analysis based solely on the language patterns in the text provided. A comprehensive evaluation would include a structured clinical interview, standardized assessments, and consideration of medical, developmental, and psychosocial history.""",
            "model": "mock-gpt-4",
            "model_type": "general",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _create_depression_detection_response(self) -> Dict[str, Any]:
        """Create a default mock response for depression detection model type."""
        return {
            "depression_signals": {
                "severity": "moderate",
                "confidence": 0.78,
                "key_indicators": [
                    {
                        "type": "linguistic",
                        "description": "Negative self-referential language",
                        "evidence": "I'm not good enough to handle this"
                    },
                    {
                        "type": "behavioral",
                        "description": "Sleep disruption",
                        "evidence": "I've been having trouble sleeping most nights"
                    },
                    {
                        "type": "cognitive",
                        "description": "Hopelessness",
                        "evidence": "I don't see how things will get better"
                    }
                ]
            },
            "analysis": {
                "summary": "Multiple moderate depression indicators present, including negative self-evaluation, sleep disruption, and hopelessness about the future",
                "warning_signs": ["Explicit statements of worthlessness", "Disrupted sleep pattern", "Expressions of hopelessness"],
                "protective_factors": ["Seeking help/awareness of difficulties", "References to previously enjoyed activities"],
                "limitations": ["Analysis based only on text without clinical interview", "Cannot assess duration of symptoms"]
            },
            "recommendations": {
                "suggested_assessments": ["PHQ-9", "Beck Depression Inventory-II", "Clinical interview focusing on mood and neurovegetative symptoms"],
                "discussion_points": ["Timeline of symptom development", "Impact on daily functioning", "Exploration of cognitive distortions"]
            },
            "model": "mock-gpt-4",
            "model_type": "depression_detection",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _create_risk_assessment_response(self) -> Dict[str, Any]:
        """Create a default mock response for risk assessment model type."""
        return {
            "risk_assessment": {
                "overall_risk_level": "low",
                "confidence": 0.82,
                "identified_risks": [
                    {
                        "risk_type": "self-harm",
                        "severity": "low",
                        "evidence": "I don't care what happens to me anymore",
                        "temporality": "current"
                    }
                ]
            },
            "analysis": {
                "summary": "Mild risk indicators present but no explicit statements of intent or plan for self-harm or suicide",
                "critical_factors": ["Expressions of hopelessness", "Passive indifference to wellbeing"],
                "protective_factors": ["Help-seeking behavior", "No explicit expressions of intent to harm self"],
                "context_considerations": ["Current stressors may be temporary", "Social support not clearly evaluated"],
                "limitations": ["Risk assessment requires direct clinical evaluation", "Text analysis cannot determine intent or access to means"]
            },
            "recommendations": {
                "immediate_actions": [],
                "clinical_follow_up": ["Direct assessment of self-harm/suicidal ideation", "Safety planning if risk increases", "Evaluation of support system"],
                "screening_tools": ["Columbia-Suicide Severity Rating Scale", "Safety Planning Intervention"]
            },
            "model": "mock-gpt-4",
            "model_type": "risk_assessment",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _create_sentiment_analysis_response(self) -> Dict[str, Any]:
        """Create a default mock response for sentiment analysis model type."""
        return {
            "sentiment": {
                "overall_score": -0.65,
                "intensity": 0.72,
                "dominant_valence": "negative"
            },
            "emotions": {
                "primary_emotions": [
                    {
                        "emotion": "sadness",
                        "intensity": 0.76,
                        "evidence": "I feel so down all the time"
                    },
                    {
                        "emotion": "anxiety",
                        "intensity": 0.68,
                        "evidence": "I'm constantly worried about everything"
                    },
                    {
                        "emotion": "hopelessness",
                        "intensity": 0.72,
                        "evidence": "I don't see how things will improve"
                    }
                ],
                "emotional_range": "narrow",
                "emotional_stability": "relatively stable"
            },
            "analysis": {
                "summary": "Predominantly negative emotional tone with consistent expressions of sadness, anxiety, and hopelessness",
                "notable_patterns": ["Persistent negative valence throughout", "Limited positive emotional expression", "Significant intensity of negative emotions"],
                "emotional_themes": ["Sadness related to self-perception", "Anxiety about the future", "General sense of defeat"],
                "clinical_relevance": "Emotional pattern consistent with depressive presentation, with significant anxiety component",
                "limitations": ["Point-in-time assessment only", "Cannot determine baseline emotional state"]
            },
            "model": "mock-gpt-4",
            "model_type": "sentiment_analysis",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _create_wellness_dimensions_response(self) -> Dict[str, Any]:
        """Create a default mock response for wellness dimensions model type."""
        return {
            "wellness_dimensions": [
                {
                    "dimension": "emotional",
                    "score": 0.35,
                    "summary": "Significant emotional distress indicated",
                    "strengths": ["Emotional awareness", "Ability to articulate feelings"],
                    "challenges": ["Persistent negative emotions", "Difficulty regulating emotional state"],
                    "evidence": ["I feel overwhelmed by sadness", "I can't seem to shake these feelings"]
                },
                {
                    "dimension": "social",
                    "score": 0.42,
                    "summary": "Moderate challenges in social connections",
                    "strengths": ["References to existing relationships"],
                    "challenges": ["Withdrawal from social interaction", "Feeling disconnected from others"],
                    "evidence": ["I've been avoiding my friends", "Nobody really understands what I'm going through"]
                },
                {
                    "dimension": "physical",
                    "score": 0.40,
                    "summary": "Physical wellness concerns present",
                    "strengths": ["Awareness of physical health impact"],
                    "challenges": ["Sleep disruption", "Low energy", "Changes in appetite"],
                    "evidence": ["I'm exhausted all the time", "I've been having trouble sleeping"]
                }
            ],
            "analysis": {
                "overall_wellness_pattern": "Multiple dimensions showing significant challenges, with emotional and physical dimensions most affected",
                "areas_of_strength": ["Self-awareness", "Insight into current challenges"],
                "areas_for_growth": ["Emotional wellness", "Physical wellness related to sleep and energy"],
                "balance_assessment": "Imbalance across dimensions with emotional challenges appearing to influence other areas",
                "limitations": ["Assessment based only on limited text sample", "Unable to assess all wellness dimensions equally"]
            },
            "recommendations": {
                "clinical_focus_areas": ["Emotional regulation strategies", "Sleep hygiene intervention", "Social reconnection plan"],
                "suggested_resources": ["Sleep hygiene education", "Behavioral activation for depression", "Mindfulness practices for emotional regulation"],
                "assessment_tools": ["Quality of Life Inventory", "Pittsburgh Sleep Quality Index"]
            },
            "model": "mock-gpt-4",
            "model_type": "wellness_dimensions",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _create_digital_twin_response(self) -> Dict[str, Any]:
        """Create a default mock response for digital twin model type."""
        return {
            "digital_twin_model": {
                "model_id": "dt-mock-123",
                "model_type": "personalized-mental-health",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "status": "active",
                "metrics": {
                    "training_samples": 1250,
                    "accuracy": 0.92,
                    "f1_score": 0.89,
                    "confidence": 0.85
                }
            },
            "analysis": {
                "summary": "Digital twin model captures personalized mental health patterns with high confidence",
                "key_findings": [
                    "Strong indicators of situational anxiety",
                    "Moderate depression symptoms primarily related to work stress",
                    "Sleep disruption as a significant contributing factor"
                ],
                "personalized_insights": [
                    "Responds well to structured behavioral activation",
                    "Benefits from mindfulness techniques for sleep improvement",
                    "Shows positive response to cognitive restructuring for work anxieties"
                ],
                "limitations": [
                    "Limited data on long-term symptom patterns",
                    "Insufficient information on medication response"
                ]
            },
            "model": "mock-gpt-4",
            "model_type": "digital_twin",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def is_healthy(self) -> bool:
        """
        Check if the service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        # Use parent implementation
        return super().is_healthy()
    
    def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        # Clear mock-specific resources
        self._mock_responses.clear()
        self._sessions.clear()
        self._digital_twins.clear()
        
        # Call parent implementation
        super().shutdown()
        logger.info("Mock MentaLLaMA service shut down")
    
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
        self._validate_service_and_input(text)
        
        # Get model type (default to general)
        model_type = model_type or "general"
        
        # Check if model type is valid
        if model_type not in self._model_types:
            raise ModelNotFoundError(f"Model type not found: {model_type}")
        
        # Get mock response for model type
        mock_response = self._mock_responses.get(model_type)
        if not mock_response:
            raise ModelNotFoundError(f"Mock response not found for model type: {model_type}")
        
        # Create a copy of the mock response
        result = mock_response.copy()
        
        # Update timestamp
        result["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        return result
    
    def _validate_service_and_input(self, text: str) -> None:
        """
        Validate service state and input text.
        
        Args:
            text: Input text to validate
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If text is empty or invalid
        """
        # Use parent's method to check initialization
        self._ensure_initialized()
        
        # Validate text input
        if not text or not isinstance(text, str):
            raise InvalidRequestError("Text must be a non-empty string")
    
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
        self._validate_service_and_input(text)
        
        # Process with depression detection model
        return self.process(text, "depression_detection", options)
    
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
        self._validate_service_and_input(text)
        
        # Get mock response
        response = self.process(text, "risk_assessment", options)
        
        # Customize response based on risk type if provided
        if risk_type and isinstance(response, dict) and "risk_assessment" in response:
            filtered_risks = []
            for risk in response["risk_assessment"].get("identified_risks", []):
                if risk.get("risk_type") == risk_type:
                    filtered_risks.append(risk)
            
            # If we found matching risks, replace the identified risks
            if filtered_risks:
                response["risk_assessment"]["identified_risks"] = filtered_risks
        
        return response
    
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
        self._validate_service_and_input(text)
        
        # Process with sentiment analysis model
        return self.process(text, "sentiment_analysis", options)
    
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
        self._validate_service_and_input(text)
        
        # Get mock response
        response = self.process(text, "wellness_dimensions", options)
        
        # Filter dimensions if provided
        if dimensions and isinstance(response, dict) and "wellness_dimensions" in response:
            filtered_dimensions = []
            for dim in response["wellness_dimensions"]:
                if dim.get("dimension") in dimensions:
                    filtered_dimensions.append(dim)
            
            # If we found matching dimensions, replace the wellness dimensions
            if filtered_dimensions:
                response["wellness_dimensions"] = filtered_dimensions
        
        return response
    
    ##### Digital Twin Methods #####
    
    def generate_digital_twin(
        self,
        text_data: List[str],
        demographic_data: Dict[str, Any],
        medical_history: Dict[str, Any],
        treatment_history: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a digital twin model for a patient.
        
        Args:
            text_data: List of text data (clinical notes, patient reports, etc.)
            demographic_data: Patient demographic information
            medical_history: Patient medical history
            treatment_history: Patient treatment history
            options: Additional generation options
            
        Returns:
            Digital twin model and analysis
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If required data is missing or invalid
        """
        self._ensure_initialized()
        
        # Validate inputs
        if not isinstance(text_data, list) or not all(isinstance(text, str) for text in text_data):
            raise InvalidRequestError("Text data must be a list of strings")
            
        if not isinstance(demographic_data, dict):
            raise InvalidRequestError("Demographic data must be a dictionary")
            
        if not isinstance(medical_history, dict):
            raise InvalidRequestError("Medical history must be a dictionary")
            
        if not isinstance(treatment_history, dict):
            raise InvalidRequestError("Treatment history must be a dictionary")
        
        # Generate twin ID
        digital_twin_id = f"dt-{uuid.uuid4().hex[:8]}"
        
        # Create a mock digital twin
        digital_twin = {
            "digital_twin_id": digital_twin_id,
            "creation_timestamp": datetime.utcnow().isoformat() + "Z",
            "patient_info": {
                # Store minimal, de-identified patient info
                "age": demographic_data.get("age", 35),
                "gender": demographic_data.get("gender", "undisclosed"),
                "clinical_history_summary": "History of anxiety and depressive episodes"
            },
            "model_parameters": {
                "version": "1.0",
                "training_samples": 1250,
                "accuracy": 0.92,
                "confidence": 0.85
            },
            "text_analysis": {
                "analyzed_texts": len(text_data),
                "key_themes": ["anxiety", "depression", "sleep disturbance"],
                "sentiment": "predominantly negative",
                "linguistic_markers": ["negative self-reference", "catastrophizing", "emotional reasoning"]
            },
            "clinical_profile": {
                "primary_conditions": medical_history.get("conditions", ["Generalized anxiety disorder", "Major depressive disorder"]),
                "symptom_patterns": ["Stress-induced anxiety", "Sleep disruption", "Negative rumination"],
                "treatment_responses": [
                    {
                        "intervention": medication,
                        "response_rate": 0.75,
                        "durability": "medium"
                    } for medication in treatment_history.get("medications", ["escitalopram"])
                ],
                "environmental_factors": [
                    {
                        "factor": "Work stress",
                        "impact": "high",
                        "temporal_pattern": "weekday peaks"
                    },
                    {
                        "factor": "Sleep quality",
                        "impact": "high",
                        "temporal_pattern": "variable"
                    }
                ],
                "risk_factors": {
                    "suicidality": "low",
                    "self_harm": "low",
                    "substance_use": "low"
                }
            },
            "prediction_models": {
                "mood_trajectory": {
                    "baseline": "moderate anxiety/depression",
                    "trend": "gradual improvement",
                    "variability": "moderate",
                    "confidence": 0.80
                },
                "crisis_prediction": {
                    "short_term_risk": "low",
                    "triggers": ["work deadline", "interpersonal conflict"],
                    "warning_signs": ["sleep disruption > 3 days", "withdrawal from social contact"],
                    "confidence": 0.78
                },
                "intervention_response": {
                    "optimal_modalities": ["Cognitive behavioral therapy", "Mindfulness practice"],
                    "predicted_response_time": "2-4 weeks",
                    "confidence": 0.75
                }
            },
            "digital_phenotype": {
                "linguistic_patterns": {
                    "negative_self_reference": "moderate",
                    "absolutist_thinking": "moderate",
                    "future_orientation": "low"
                },
                "behavioral_patterns": {
                    "sleep_cycle": "disrupted",
                    "physical_activity": "below average",
                    "social_engagement": "declining"
                },
                "cognitive_patterns": {
                    "catastrophizing": "frequent",
                    "rumination": "high",
                    "problem_solving": "impaired under stress"
                }
            }
        }
        
        # Store in memory for retrieval
        self._digital_twins[digital_twin_id] = digital_twin
        
        # Create result for API
        result = {
            "digital_twin_id": digital_twin_id,
            "creation_timestamp": digital_twin["creation_timestamp"],
            "analyzed_text_count": len(text_data),
            "summary": {
                "key_characteristics": [
                    "Moderate anxiety/depression with gradual improvement trend",
                    "Strong response to CBT and mindfulness interventions",
                    "Work stress as primary environmental trigger"
                ],
                "clinical_insights": [
                    "Exhibits classic stress-anxiety-depression cycle",
                    "Responds well to structured cognitive interventions",
                    "Sleep quality is a key modifiable factor"
                ],
                "limitations": [
                    "Digital twin is a simulation based on limited data",
                    "Real-world behavior may differ from modeled predictions",
                    "Regular recalibration recommended"
                ]
            },
            "model": "mock-gpt-4",
            "model_type": "digital_twin"
        }
        
        return result
    
    def create_digital_twin_session(
        self, 
        twin_id: Optional[str] = None,
        session_type: str = "therapeutic",
        initial_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new digital twin session.
        
        Args:
            twin_id: ID of the digital twin to use (creates generic twin if None)
            session_type: Type of session (therapeutic, assessment, etc.)
            initial_prompt: Initial prompt for the session
            options: Additional session options
            
        Returns:
            Session details and information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If required parameters are invalid
            ModelNotFoundError: If the specified twin ID does not exist
        """
        self._ensure_initialized()
        
        # Validate session type
        valid_session_types = ["therapeutic", "therapy", "assessment", "crisis", "monitoring"]
        
        # Map session types for backward compatibility
        session_type_mapping = {
            "therapy": "therapeutic"
        }
        
        # Use mapped session type if available
        internal_session_type = session_type_mapping.get(session_type, session_type)
        
        if session_type not in valid_session_types:
            raise InvalidRequestError(
                f"Invalid session type: {session_type}. "
                f"Must be one of {valid_session_types}"
            )
        
        # Create session ID
        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        
        # Check if twin exists if ID is provided
        digital_twin = None
        if twin_id:
            digital_twin = self._digital_twins.get(twin_id)
            if not digital_twin:
                raise ModelNotFoundError(f"Digital twin not found: {twin_id}")
        
        # Use a generic twin ID if none provided
        if not twin_id:
            twin_id = f"dt-generic-{uuid.uuid4().hex[:4]}"
        
        # Create session
        session = {
            "session_id": session_id,
            "twin_id": twin_id,
            "session_type": internal_session_type,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "status": "active",
            "messages": []
        }
        
        # Add initial prompt if provided
        if initial_prompt:
            response = self._generate_dt_response(initial_prompt, session_type)
            
            # Add messages to session
            message_id = f"msg-{random.randint(10000, 99999)}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            session["messages"].append({
                "id": message_id,
                "role": "user",
                "content": initial_prompt,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })
            
            dt_message_id = f"msg-{random.randint(10000, 99999)}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            session["messages"].append({
                "id": dt_message_id,
                "role": "assistant",
                "content": response,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })
            
            # Update session timestamp
            session["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Store session
        self._sessions[session_id] = session
        
        # Create API response
        result = {
            "session_id": session_id,
            "twin_id": twin_id,
            "session_type": session_type,
            "created_at": session["created_at"],
            "status": "active",
            "messages": session["messages"],
            "message_count": len(session["messages"])
        }
        
        return result
    
    def get_digital_twin_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get details of a digital twin session.
        
        Args:
            session_id: ID of the session to retrieve
            
        Returns:
            Session details and information
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If session ID is empty or invalid
            ModelNotFoundError: If the specified session ID does not exist
        """
        self._ensure_initialized()
        
        # Validate session ID
        if not session_id or not isinstance(session_id, str):
            raise InvalidRequestError("Session ID must be a non-empty string")
        
        # Get session
        session = self._sessions.get(session_id)
        if not session:
            raise ModelNotFoundError(f"Session not found: {session_id}")
        
        # Return a copy of the session
        result = session.copy()
        
        return result
    
    def send_message_to_session(
        self, 
        session_id: str,
        message: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a digital twin session.
        
        Args:
            session_id: ID of the session to send message to
            message: Message content
            options: Additional message options
            
        Returns:
            Updated session details and response
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If required parameters are invalid
            ModelNotFoundError: If the specified session ID does not exist
        """
        self._ensure_initialized()
        
        # Validate parameters
        if not session_id or not isinstance(session_id, str):
            raise InvalidRequestError("Session ID must be a non-empty string")
            
        if not message or not isinstance(message, str):
            raise InvalidRequestError("Message must be a non-empty string")
        
        # Get session
        session = self._sessions.get(session_id)
        if not session:
            raise ModelNotFoundError(f"Session not found: {session_id}")
            
        # Check if session is active
        if session.get("status") != "active":
            raise InvalidRequestError(f"Session is not active: {session_id}")
        
        # Add user message to session
        message_id = f"msg-{random.randint(10000, 99999)}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        session["messages"].append({
            "id": message_id,
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
        
        # Update session timestamp
        session["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Generate response
        response = self._generate_dt_response(message, session.get("session_type", "therapeutic"))
        
        # Add digital twin response to session
        dt_message_id = f"msg-{random.randint(10000, 99999)}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        session["messages"].append({
            "id": dt_message_id,
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
        
        # Update session timestamp
        session["updated_at"] = datetime.utcnow().isoformat() + "Z"
        # Create result
        result = {
            "session_id": session_id,
            "message_id": dt_message_id,
            "response": response,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_status": session["status"],
            "message_count": len(session["messages"]),
            "messages": session["messages"]
        }
        
        return result
        return result
    
    def _generate_dt_response(self, message: str, session_type: str) -> str:
        """
        Generate a response from the digital twin.
        
        Args:
            message: User message
            session_type: Type of session
            
        Returns:
            Digital twin response
        """
        if session_type == "therapeutic":
            return """I appreciate you sharing that with me. It sounds like you've been experiencing a mix of anxiety and low mood, particularly related to work pressures. Many people find themselves struggling with similar feelings, especially when multiple stressors coincide.

When you mention feeling "overwhelmed" and "stuck in a cycle," I'm noticing patterns consistent with anxiety and potential depression. These experiences can feel isolating, but they're actually quite common responses to persistent stress.

Have you noticed any particular situations or times of day when these feelings are stronger? Understanding these patterns can help us identify practical coping strategies that might work for you.

It might also be helpful to explore some brief relaxation techniques that can interrupt the stress cycle when it begins to escalate. Would you be interested in learning about a simple breathing exercise that many find helpful during moments of acute stress?"""
        elif session_type == "assessment":
            return """Based on what you've shared, I'm noticing several patterns that would be important to explore further in a clinical assessment:

1. Sleep difficulties (trouble falling asleep, early morning awakening)
2. Persistent worry, especially about work performance
3. Negative self-perception and self-criticism
4. Reduced interest in previously enjoyed activities
5. Physical symptoms including tension and fatigue

These symptoms suggest elements of both anxiety and depression, which often co-occur. The duration and persistence of these experiences would be important to establish in a clinical context.

On standardized measures, these descriptions might align with moderate anxiety and mild-to-moderate depressive symptoms, though formal assessment would be needed to confirm this.

What other aspects of your daily functioning have you noticed being affected by these experiences?"""
        elif session_type == "crisis":
            return """I'm very concerned about what you're sharing, and I want to make sure you have immediate support. These feelings of hopelessness and thoughts about not wanting to continue are serious warning signs that require prompt professional attention.

Your safety is the absolute priority right now. While I can provide information and support, you need to connect with a crisis professional who can help ensure your immediate safety.

Please consider one of these immediate resources:
- Call the National Suicide Prevention Lifeline: 988 or 1-800-273-8255
- Text HOME to the Crisis Text Line: 741741
- Go to your nearest emergency room
- Call 911

Would it be possible for you to reach out to one of these resources right now? Or is there someone nearby who could stay with you while you make this contact?"""
        else:  # monitoring
            return """Thank you for your check-in. I notice that your sleep has improved this week, which is a positive development. Your anxiety levels seem to fluctuate, with work meetings still triggering significant symptoms.

Compared to your previous patterns, this represents moderate improvement in your sleep pattern, while anxiety symptoms remain fairly consistent with your baseline. The connection between work stressors and symptom increase remains a clear pattern.

The mindfulness practice you've been implementing seems to be showing some initial positive effects, particularly for sleep onset. Continuing this practice, especially before challenging work situations, might help extend these benefits.

Would you like to discuss some additional strategies specifically for managing anxiety during work meetings?"""
    
    def end_digital_twin_session(
        self, 
        session_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        End a digital twin session.
        
        Args:
            session_id: ID of the session to end
            options: Additional options
            
        Returns:
            Session summary and insights
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If session ID is empty or invalid
            ModelNotFoundError: If the specified session ID does not exist
        """
        self._ensure_initialized()
        
        # Validate session ID
        if not session_id or not isinstance(session_id, str):
            raise InvalidRequestError("Session ID must be a non-empty string")
        
        # Get session
        session = self._sessions.get(session_id)
        if not session:
            raise ModelNotFoundError(f"Session not found: {session_id}")
            
        # Check if session is already ended
        if session.get("status") != "active":
            raise InvalidRequestError(f"Session is already ended: {session_id}")
        
        # End session
        session["status"] = "completed"
        session["updated_at"] = datetime.utcnow().isoformat() + "Z"
        session["ended_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Generate session summary
        summary = self._generate_session_summary(session)
        
        # Add summary to session
        session["summary"] = summary
        
        # Create result
        result = {
            "session_id": session_id,
            "status": "completed",
            "ended_at": session["ended_at"],
            "duration": self._calculate_session_duration(session),
            "message_count": len(session["messages"]),
            "summary": summary
        }
        
        return result
    
    def _calculate_session_duration(self, session: Dict[str, Any]) -> str:
        """
        Calculate the duration of a session.
        
        Args:
            session: Session data
            
        Returns:
            Duration as a string (e.g., "45 minutes")
        """
        try:
            created_at = datetime.fromisoformat(session["created_at"].rstrip("Z"))
            ended_at = datetime.fromisoformat(session["ended_at"].rstrip("Z"))
            duration = ended_at - created_at
            minutes = duration.total_seconds() / 60
            
            if minutes < 1:
                return "less than 1 minute"
            elif minutes < 60:
                return f"{int(minutes)} minutes"
            else:
                hours = int(minutes / 60)
                remaining_minutes = int(minutes % 60)
                if remaining_minutes == 0:
                    return f"{hours} hours"
                else:
                    return f"{hours} hours {remaining_minutes} minutes"
        except Exception:
            return "unknown duration"
    
    def _generate_session_summary(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of a digital twin session.
        
        Args:
            session: Session data
            
        Returns:
            Session summary
        """
        session_type = session.get("session_type", "therapeutic")
        
        if session_type == "therapeutic":
            return {
                "key_themes": [
                    "Work-related anxiety",
                    "Sleep disruption",
                    "Negative self-perception",
                    "Social withdrawal"
                ],
                "session_progression": {
                    "engagement_level": "high",
                    "emotional_trajectory": "initial distress with gradual stabilization",
                    "insight_development": "moderate increase in self-awareness"
                },
                "therapeutic_elements": [
                    {
                        "element": "Validation",
                        "response": "positive",
                        "notes": "Client responded well to normalization of experience"
                    },
                    {
                        "element": "Cognitive reframing",
                        "response": "mixed",
                        "notes": "Initial resistance followed by tentative consideration"
                    },
                    {
                        "element": "Relaxation techniques",
                        "response": "positive",
                        "notes": "Expressed willingness to try breathing exercises"
                    }
                ],
                "recommendations": [
                    "Continue exploration of work-related anxiety triggers",
                    "Develop personalized stress reduction routine",
                    "Monitor sleep patterns and nighttime rumination",
                    "Consider workload management strategies"
                ]
            }
        elif session_type == "assessment":
            return {
                "clinical_impressions": {
                    "primary_concerns": [
                        "Generalized anxiety with prominent work-related worries",
                        "Depressive symptoms including anhedonia and sleep disturbance",
                        "Possible perfectionistic traits contributing to anxiety"
                    ],
                    "severity_estimate": "moderate",
                    "functional_impact": "significant in occupational and social domains",
                    "risk_assessment": "low acute risk; chronic moderate distress"
                },
                "symptom_pattern": {
                    "onset": "gradual over approximately 6 months",
                    "course": "persistent with recent intensification",
                    "exacerbating_factors": ["work deadlines", "performance evaluations", "interpersonal conflicts"],
                    "alleviating_factors": ["exercise", "time in nature", "structured activities"]
                },
                "diagnostic_considerations": [
                    "Generalized Anxiety Disorder",
                    "Persistent Depressive Disorder",
                    "Adjustment Disorder with Mixed Anxiety and Depression"
                ],
                "recommended_assessments": [
                    "GAD-7 and PHQ-9 for symptom quantification",
                    "Sleep diary to evaluate insomnia pattern",
                    "Screening for comorbid conditions including substance use"
                ],
                "treatment_considerations": [
                    "CBT with focus on cognitive restructuring",
                    "Stress management and relaxation training",
                    "Regular physical activity",
                    "Evaluate need for psychiatric consultation"
                ]
            }
        elif session_type == "crisis":
            return {
                "crisis_nature": {
                    "type": "suicidal ideation with moderate risk",
                    "precipitating_factors": ["job loss", "financial stress", "relationship conflict"],
                    "protective_factors": ["awareness of distress", "help-seeking behavior", "social supports"],
                    "immediate_concerns": "active thoughts of suicide without specific plan"
                },
                "interventions_provided": [
                    "Risk assessment",
                    "Safety planning",
                    "Referral to crisis services",
                    "Support and validation"
                ],
                "client_response": {
                    "engagement": "cooperative and forthcoming",
                    "emotional_state": "fluctuating distress with periods of calm",
                    "insight": "acknowledges need for immediate support",
                    "safety_plan_adherence": "agreed to contact crisis line and inform family"
                },
                "risk_status": {
                    "assessment": "moderate acute risk requiring prompt intervention",
                    "recommendations": "immediate crisis services contact; consider emergency evaluation",
                    "follow_up": "confirmed connection with crisis services and family support"
                },
                "continuity_of_care": [
                    "Crisis services actively engaged",
                    "Outpatient provider notified with client permission",
                    "Family member informed and providing support",
                    "Follow-up appointment scheduled within 24 hours"
                ]
            }
        else:  # monitoring
            return {
                "monitoring_period": {
                    "duration": "2 weeks",
                    "check_in_adherence": "85% compliance with scheduled check-ins",
                    "data_quality": "consistent and detailed reporting"
                },
                "symptom_tracking": {
                    "anxiety": {
                        "trend": "gradually decreasing",
                        "pattern": "highest mid-week, lowest weekends",
                        "triggers": "consistently related to work meetings",
                        "intervention_response": "moderate improvement with mindfulness practice"
                    },
                    "mood": {
                        "trend": "stable with mild improvement",
                        "pattern": "morning lows, evening improvement",
                        "triggers": "social isolation associated with lower mood",
                        "intervention_response": "positive response to scheduled activity"
                    },
                    "sleep": {
                        "trend": "significant improvement",
                        "pattern": "initial insomnia resolved, early waking persists",
                        "triggers": "screen time before bed associated with poorer sleep",
                        "intervention_response": "strong positive response to sleep hygiene protocol"
                    }
                },
                "intervention_engagement": [
                    {
                        "intervention": "Daily mindfulness practice",
                        "adherence": "70%",
                        "reported_benefit": "moderate",
                        "barriers": "time constraints, difficulty focusing"
                    },
                    {
                        "intervention": "Sleep hygiene protocol",
                        "adherence": "90%",
                        "reported_benefit": "significant",
                        "barriers": "occasional work requirements"
                    },
                    {
                        "intervention": "Cognitive reframing exercises",
                        "adherence": "60%",
                        "reported_benefit": "mild to moderate",
                        "barriers": "difficulty applying during high stress periods"
                    }
                ],
                "recommendations": [
                    "Continue sleep hygiene protocol with current parameters",
                    "Adjust mindfulness practice to shorter, more frequent sessions",
                    "Develop specific cognitive strategies for work meetings",
                    "Increase scheduled positive social interactions"
                ]
            }
    
    def get_session_insights(
        self, 
        session_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get clinical insights from a digital twin session.
        
        Args:
            session_id: ID of the session to analyze
            options: Additional options
            
        Returns:
            Clinical insights and analysis
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If session ID is empty or invalid
            ModelNotFoundError: If the specified session ID does not exist
        """
        self._ensure_initialized()
        
        # Validate session ID
        if not session_id or not isinstance(session_id, str):
            raise InvalidRequestError("Session ID must be a non-empty string")
        
        # Get session
        session = self._sessions.get(session_id)
        if not session:
            raise ModelNotFoundError(f"Session not found: {session_id}")
        
        # Check if session has messages
        if not session.get("messages"):
            raise InvalidRequestError(f"Session has no messages: {session_id}")
        # Create insights dictionary with the expected structure
        insights = {
            "session_id": session_id,
            "twin_id": session.get("twin_id"),
            "session_type": session.get("session_type"),
            "message_count": len(session["messages"]),
            "session_status": session.get("status"),
            "insights": {
                "themes": [
                    "Work-related anxiety and stress",
                    "Sleep disruption and fatigue",
                    "Negative self-perception and rumination",
                    "Social withdrawal and isolation"
                ],
                "patterns": {
                    "emotional_tone": {
                        "primary_valence": "negative",
                        "intensity": "moderate to high",
                        "stability": "fluctuating",
                        "dominant_emotions": ["anxiety", "sadness", "frustration"]
                    },
                    "cognitive_patterns": {
                        "all_or_nothing_thinking": "frequent",
                        "catastrophizing": "moderate",
                        "personalization": "frequent",
                        "mental_filtering": "present"
                    }
                },
                "clinical_indicators": {
                    "symptom_patterns": [
                        {
                            "domain": "mood",
                            "description": "Persistent low mood with diurnal variation",
                            "severity": "moderate",
                            "evidence": "Consistent negative self-description and expressed hopelessness"
                        },
                        {
                            "domain": "anxiety",
                            "description": "Worry about performance and social evaluation",
                            "severity": "moderate to severe",
                            "evidence": "Recurring expressions of fear regarding negative judgment"
                        }
                    ],
                    "risk_assessment": {
                        "overall_risk_level": "low to moderate",
                        "concerning_elements": ["expressions of hopelessness", "social withdrawal"],
                        "protective_factors": ["help-seeking behavior", "future planning", "social connections"]
                    }
                },
                "recommendations": [
                    "Implement structured CBT protocol focusing on cognitive restructuring",
                    "Develop personalized stress reduction routine with daily mindfulness practice",
                    "Establish sleep hygiene protocol with regular monitoring",
                    "Consider workload management strategies and workplace accommodations",
                    "Regular monitoring of mood symptoms using standardized measures"
                ]
            }
        }
        
        # Add generated_at timestamp
        insights["generated_at"] = datetime.utcnow().isoformat() + "Z"
        
        return insights


class MockPHIDetection(PHIDetectionInterface):
    """
    Mock PHI detection implementation.
    
    This class provides a mock implementation of PHI detection services for testing.
    It simulates PHI detection and redaction capabilities.
    """
    
    def __init__(self) -> None:
        """Initialize MockPHIDetection instance."""
        self._initialized = False
        self._config = None
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the service with configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        try:
            # Configuration is optional for mock service
            if config is not None and not isinstance(config, dict):
                raise InvalidConfigurationError("Configuration must be a dictionary")
                
            self._config = config or {}
            self._initialized = True
            logger.info("Mock PHI detection service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize mock PHI detection service: {str(e)}")
            self._initialized = False
            self._config = None
            raise
    
    def is_healthy(self) -> bool:
        """
        Check if the service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        return self._initialized
    
    def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        self._initialized = False
        logger.info("Mock PHI detection service shut down")
    
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
        if not self._initialized:
            raise ServiceUnavailableError("Mock PHI detection service is not initialized")
        if not text or not isinstance(text, str):
            raise InvalidRequestError("Text must be a non-empty string")
        
        # Use a more strict detection level by default
        original_level = detection_level or "strict"
        detection_level = original_level
        
        # Validate detection level
        valid_levels = ["minimal", "moderate", "aggressive", "strict", "relaxed"]
        if detection_level not in valid_levels:
            raise InvalidRequestError(f"Invalid detection level: {detection_level}. Must be one of {valid_levels}")
            
        # Map detection levels for backwards compatibility (internal processing only)
        level_mapping = {
            "minimal": "relaxed",
            "aggressive": "strict"
        }
        internal_level = level_mapping.get(detection_level, detection_level)
        
        # Create mock PHI instances based on mapped detection level
        phi_instances = self._create_mock_phi_instances(internal_level)
        
        # Create a mock detection result (using original level name for the API response)
        result = {
            "has_phi": True,
            "confidence": 0.95,
            "detection_level": original_level,
            "phi_instances": phi_instances,
            "model": "mock-phi-detection",
            "analysis_time_ms": 42,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return result
    
    def _create_mock_phi_instances(self, detection_level: str) -> List[Dict[str, Any]]:
        """
        Create mock PHI instances based on detection level.
        
        Args:
            detection_level: Detection level (strict, moderate, relaxed)
            
        Returns:
            List of mock PHI instances
        """
        # Default PHI instances (comprehensive set)
        phi_instances = [
            {
                "type": "NAME",
                "subtype": "PATIENT",
                "text": "John Smith",
                "start_pos": 10,
                "end_pos": 20,
                "position": {"start": 10, "end": 20},
                "confidence": 0.99
            },
            {
                "type": "DATE",
                "subtype": "BIRTH_DATE",
                "text": "01/15/1980",
                "start_pos": 45,
                "end_pos": 55,
                "position": {"start": 45, "end": 55},
                "confidence": 0.98
            },
            {
                "type": "ID",
                "subtype": "SSN",
                "text": "123-45-6789",
                "start_pos": 80,
                "end_pos": 91,
                "position": {"start": 80, "end": 91},
                "confidence": 0.99
            },
            {
                "type": "LOCATION",
                "subtype": "ADDRESS",
                "text": "123 Main St, Anytown, NY 12345",
                "start_pos": 110,
                "end_pos": 141,
                "position": {"start": 110, "end": 141},
                "confidence": 0.97
            },
            {
                "type": "CONTACT",
                "subtype": "PHONE",
                "text": "(555) 123-4567",
                "start_pos": 160,
                "end_pos": 174,
                "position": {"start": 160, "end": 174},
                "confidence": 0.98
            }
        ]
        
        # Adjust instances based on detection level
        if detection_level == "relaxed":
            # For relaxed detection, only include high-confidence or sensitive types
            return [instance for instance in phi_instances 
                   if instance["confidence"] > 0.98 or 
                   instance["type"] in ["NAME", "ID"]]
        
        elif detection_level == "moderate":
            # For moderate detection, include all but reduce confidence threshold
            return phi_instances
        
        # For strict detection, include all and potentially add more thorough detection
        return phi_instances
    
    def redact_phi(
        self,
        text: str,
        replacement: str = "[REDACTED]",
        detection_level: Optional[str] = None,
        redaction_marker: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Redact PHI from text.
        
        Args:
            text: Text to redact
            replacement: Replacement text for redacted PHI (deprecated)
            detection_level: Detection level (strict, moderate, relaxed)
            redaction_marker: Custom marker to replace PHI with
            
        Returns:
            Dict containing redacted text and metadata
            
        Raises:
            ServiceUnavailableError: If service is not initialized
            InvalidRequestError: If text is empty or invalid
        """
        if not self._initialized:
            raise ServiceUnavailableError("Mock PHI detection service is not initialized")
        if not text or not isinstance(text, str):
            raise InvalidRequestError("Text must be a non-empty string")
        
        # Use redaction_marker if provided, otherwise use replacement
        marker = redaction_marker if redaction_marker is not None else replacement
        
        # Detect PHI first
        detection_result = self.detect_phi(text, detection_level)
        
        # Create a mock redacted text
        # In real implementation, we would use the detection result to redact the text
        redacted_text = f"""Patient: {marker} was seen on {marker} for follow-up.
        
Medical Record #: {marker}
Address: {marker}
Phone: {marker}
        
Assessment:
The patient continues to show improvement in mood and anxiety symptoms. They report better sleep quality and reduced rumination. No suicidal ideation or intent. Blood pressure is within normal range at {marker}.
        
Plan:
1. Continue current medication regimen
2. Follow-up in 4 weeks
3. Refer to weekly therapy sessions with Dr. {marker}"""
        
        # Create result
        result = {
            "original_length": len(text),
            "redacted_length": len(redacted_text),
            "redacted_text": redacted_text,
            "redaction_count": len(detection_result["phi_instances"]),
            "redacted_types": list({instance["type"] for instance in detection_result["phi_instances"]}),
            "detection_level": detection_result["detection_level"],
            "replacement_used": marker,
            "phi_instances": detection_result["phi_instances"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return result