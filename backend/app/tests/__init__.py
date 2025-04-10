"""
Test package initialization.

This module sets up the testing environment variables and configuration
before any tests are loaded.
"""
import os

# Ensure testing mode is enabled
os.environ["TESTING"] = "1"