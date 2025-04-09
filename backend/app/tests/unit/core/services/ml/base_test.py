"""
Base test class for ML-related tests in Novamind Digital Twin Platform.

This class provides specialized fixtures and utilities for testing
machine learning services and components.
"""

from typing import Dict, Any, List, Optional
from unittest import mock

from app.tests.base_test import BaseTest


class BaseMLTest(BaseTest):
    """Base class for all ML-related tests."""
    
    def setUp(self) -> None:
        """Set up ML test fixtures."""
        super().setUp()
        
        # Initialize mocks for ML services
        self.setup_ml_mocks()
        
    def setup_ml_mocks(self) -> None:
        """Set up mocks for ML services."""
        # These can be overridden by specific test classes
        pass
        
    def tearDown(self) -> None:
        """Tear down ML test fixtures."""
        super().tearDown()
        
    def assert_valid_sentiment_result(self, result: Dict[str, Any]) -> None:
        """Assert that a sentiment analysis result is valid.
        
        Args:
            result: Sentiment analysis result
        """
        self.assertIn("sentiment", result)
        self.assertIn("score", result)
        self.assertIn(result["sentiment"], ["positive", "negative", "neutral"])
        self.assertGreaterEqual(result["score"], -1.0)
        self.assertLessEqual(result["score"], 1.0)
        
    def assert_valid_risk_assessment(self, result: Dict[str, Any]) -> None:
        """Assert that a risk assessment result is valid.
        
        Args:
            result: Risk assessment result
        """
        self.assertIn("risk_level", result)
        self.assertIn("risk_factors", result)
        self.assertIn(result["risk_level"], ["low", "moderate", "high", "severe"])
        self.assertIsInstance(result["risk_factors"], list)