import pytest
from unittest.mock import MagicMock, patch

# Import the correct class name
from app.infrastructure.security.phi.log_sanitizer import LogSanitizer, LogSanitizerConfig
# Import the core service for comparison or context if needed
from app.infrastructure.security.phi.phi_service import PHIService


# Test cases for the LogSanitizer wrapper class 