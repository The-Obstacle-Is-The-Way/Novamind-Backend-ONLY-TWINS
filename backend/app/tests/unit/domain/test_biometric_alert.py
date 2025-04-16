from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

import pytest

# Corrected import path for AlertPriority
from app.domain.services.biometric_event_processor import AlertPriority
# from app.domain.entities.digital_twin.biometric_alert import BiometricAlert # Removed - Module/Entity does not exist
from app.domain.exceptions import EntityNotFoundError, RepositoryError
# from app.domain.value_objects import AlertStatus, AlertPriority, AlertThreshold # Removed - Not defined here
# Attempting import from schemas, assuming Priority/Threshold are also enums/types there
from app.presentation.api.schemas.biometric_alert import (
    AlertStatusEnum as AlertStatus, # Alias to match test usage
    AlertPriorityEnum as AlertPriority, # Correct name and alias
    # AlertThreshold # Removed - Not found in schema file
)

# ... existing code ...
