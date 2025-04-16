from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

# Commenting out missing entity import
# from app.domain.entities.biometric_alert import BiometricAlert
from app.domain.entities.digital_twin_enums import AlertPriority
from app.domain.exceptions import EntityNotFoundError, RepositoryError

# ... existing code ...
