"""
Base test class for all unit tests in the Novamind Digital Twin Platform.

This class provides common functionality and setup/teardown methods
for unit tests across all layers of the architecture.
"""
from unittest import TestCase
import pytest


class BaseUnitTest(TestCase):
    """Base class for all unit tests in the Novamind platform.
    
    This class provides common setup and teardown logic for unit tests,
    as well as helpful assertion methods and utilities.
    
    All unit tests should inherit from this class to ensure consistent
    test structure and behavior.
    """
    
    def setUp(self):
        """Set up test fixtures before each test method execution.
        
        This method is called before each test method to set up any objects
        or values that are needed for the test.
        """
        self.test_started = True
        
    def tearDown(self):
        """Tear down test fixtures after each test method execution.
        
        This method is called after each test method to clean up any objects
        or values that were created during the test.
        """
        self.test_started = False
        
    def assert_phi_sanitized(self, sanitized_text, original_phi_values):
        """Assert that PHI values have been properly sanitized from text.
        
        Args:
            sanitized_text (str): The text that should have PHI sanitized
            original_phi_values (list): A list of PHI values that should not appear in the sanitized text
            
        Raises:
            AssertionError: If any of the PHI values are found in the sanitized text
        """
        for phi_value in original_phi_values:
            self.assertNotIn(phi_value, sanitized_text, 
                           f"PHI value '{phi_value}' was found in sanitized text")
            
    def assert_audit_logged(self, mock_logger, expected_event_type, expected_data=None):
        """Assert that an audit log event was properly recorded.
        
        Args:
            mock_logger: The mock logger object that should have received the log call
            expected_event_type (str): The expected event type (e.g., 'phi_access')
            expected_data (dict, optional): Expected data fields in the audit log
            
        Raises:
            AssertionError: If the expected audit log event was not recorded
        """
        mock_logger.log.assert_called()
        
        # Check if any call matches our expected event type and data
        found_matching_call = False
        for call in mock_logger.log.call_args_list:
            args, kwargs = call
            
            # Check that the event type matches
            if args and args[0] == expected_event_type:
                found_matching_call = True
                
                # If expected_data is provided, check that it's included in the logged data
                if expected_data:
                    logged_data = kwargs.get('data', {})
                    for key, value in expected_data.items():
                        self.assertIn(key, logged_data)
                        self.assertEqual(logged_data[key], value)
                        
                break
        
        self.assertTrue(found_matching_call, 
                      f"No audit log event of type '{expected_event_type}' was recorded")