"""
Unit Tests for the MentaLLaMA Service.

This module contains unit tests for the MentaLLaMA psychiatric analysis service.
It mocks external dependencies and verifies the core logic, error handling,
and specific analysis features like depression detection and risk assessment.
"""

import pytest
from unittest.mock import patch, MagicMock
# Updated import path
# from app.core.config.settings import get_settings
from app.config.settings import get_settings

from app.core.exceptions import (
    MLServiceError,
) 