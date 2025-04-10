"""
venv_only Tests Package for Novamind Digital Twin Platform.

This package contains tests that require Python packages but no external services:
- Can use third-party packages (pandas, numpy, etc.)
- Cannot connect to databases
- Cannot make network requests
- Can access the filesystem

These tests are run after standalone tests but before integration tests.
"""