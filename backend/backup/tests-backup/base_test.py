"""
Base test class for all tests in Novamind Digital Twin Platform.

This class provides common functionality and setup required for all tests,
regardless of category.
"""

import os
import unittest
from typing import Dict, Any, List, Optional
from unittest import mock


class BaseTest(unittest.TestCase):
    """Base class for all tests in the system."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()
        # Initialize common test fixtures
        self.audit_events: List[Dict[str, Any]] = []
    
    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Clean up any fixtures or mocks
        super().tearDown()
    
    def mock_audit_log(self, user_id: str, action: str, 
                      resource_type: str, resource_id: str, 
                      details: Optional[Dict[str, Any]] = None) -> None:
        """Mock function to log audit events."""
        self.audit_events.append({
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {}
        })
    
    @staticmethod
    def load_test_data(filename: str) -> Any:
        """Load test data from a file in the tests/data directory.
        
        Args:
            filename: Name of the file to load
            
        Returns:
            The loaded test data
        """
        import json
        import yaml
        from pathlib import Path
        
        # Get base test directory
        test_dir = Path(__file__).parent
        data_dir = test_dir / "data"
        file_path = data_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Test data file not found: {filename}")
        
        # Load data based on file extension
        if filename.endswith(".json"):
            with open(file_path, "r") as f:
                return json.load(f)
        elif filename.endswith((".yaml", ".yml")):
            with open(file_path, "r") as f:
                return yaml.safe_load(f)
        else:
            # For other file types, just return the text content
            with open(file_path, "r") as f:
                return f.read()