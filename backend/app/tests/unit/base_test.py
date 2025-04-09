"""
Base Unit Test Class

This module provides a base class for all unit tests in the application,
ensuring consistent test setup, teardown, and utilities.
"""

import unittest
from typing import Dict, Any, List, Optional
import json
import logging
from unittest.mock import patch, MagicMock

# Configure logging to prevent PHI leakage
logging.basicConfig(level=logging.ERROR)


class BaseUnitTest(unittest.TestCase):
    """
    Base class for all unit tests.
    
    This class extends unittest.TestCase and provides common setup,
    teardown, and utility methods for unit testing. It implements
    proper mocking strategies and validation helpers.
    """
    
    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        super().setUp()
        # Create patch context managers
        self.patches = []
        self.mocks = {}
        
        # Suppress logs during tests
        logging.disable(logging.CRITICAL)
    
    def tearDown(self) -> None:
        """Clean up after each test method."""
        # Stop all patches
        for patcher in self.patches:
            patcher.stop()
        
        # Clear mocks
        self.mocks.clear()
        
        # Re-enable logging
        logging.disable(logging.NOTSET)
        
        super().tearDown()
    
    def create_mock(self, target: str, **kwargs) -> MagicMock:
        """Create a mock for the specified target.
        
        Args:
            target: Target to mock, in the form 'package.module.Class'
            **kwargs: Additional arguments to pass to patch
            
        Returns:
            The created mock object
        """
        patcher = patch(target, **kwargs)
        mock = patcher.start()
        self.patches.append(patcher)
        self.mocks[target] = mock
        return mock
    
    def load_test_data(self, file_path: str) -> Dict[str, Any]:
        """Load test data from a JSON file.
        
        Args:
            file_path: Path to the JSON file, relative to the tests/data directory
            
        Returns:
            The loaded test data
        """
        with open(f"app/tests/data/{file_path}", "r") as f:
            return json.load(f)
    
    def assert_dict_subset(self, subset: Dict[str, Any], superset: Dict[str, Any], 
                          path: str = "") -> None:
        """Assert that all key-value pairs in subset exist in superset.
        
        Args:
            subset: The dictionary with keys to check
            superset: The dictionary to check against
            path: Current path for nested dictionaries, used for error messages
        """
        for key, value in subset.items():
            current_path = f"{path}.{key}" if path else key
            
            self.assertIn(key, superset, f"Key '{current_path}' not found in response")
            
            if isinstance(value, dict) and isinstance(superset[key], dict):
                # Recursively check nested dictionaries
                self.assert_dict_subset(value, superset[key], current_path)
            else:
                # Check values directly
                self.assertEqual(value, superset[key], 
                               f"Value mismatch for key '{current_path}'")
    
    def assertNoLogging(self, logger_name: str, level: int = logging.INFO) -> None:
        """Assert that no logging occurred during the test.
        
        Args:
            logger_name: Name of the logger to check
            level: Minimum logging level to check for
        """
        with self.assertLogs(logger_name, level=level) as cm:
            # Trigger a log message to avoid assertLogs raising an error
            logging.getLogger(logger_name).log(level, "dummy")
            
        # Check that only our dummy message was logged
        self.assertEqual(len(cm.records), 1)
        self.assertEqual(cm.records[0].message, "dummy")