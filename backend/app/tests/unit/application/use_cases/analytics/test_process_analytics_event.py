# -*- coding: utf-8 -*-
"""
Tests for the ProcessAnalyticsEventUseCase.

This module contains unit tests for the analytics event processing use case,
ensuring proper handling of events, validation, and error conditions.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.domain.entities.analytics import AnalyticsEvent
from app.application.use_cases.analytics.process_analytics_event import ProcessAnalyticsEventUseCase


@pytest.fixture
def mock_analytics_repository():
    """Create a mock analytics repository for testing."""
    repo = AsyncMock()
    
    # Set up the save_event method to return a modified event with an ID
    async def save_event_mock(event):
        return AnalyticsEvent()
            event_type=event.event_type,
            event_data=event.event_data,
            user_id=event.user_id,
            session_id=event.session_id,
            timestamp=event.timestamp,
            event_id="test-event-id-123"
        (        )
    
        repo.save_event = save_event_mock
        return repo


        @pytest.fixture
        def mock_cache_service():
    """Create a mock cache service for testing."""
    cache = AsyncMock()
    
    # Set up increment method to return a count
    async def increment_mock(key, increment=1):
        return 10  # Mock counter value after increment
    
        cache.increment = increment_mock
        return cache


        @pytest.fixture
        def use_case(mock_analytics_repository, mock_cache_service):
    """Create the use case with mocked dependencies."""
    with patch('app.core.utils.logging.get_logger') as mock_logger:
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        use_case = ProcessAnalyticsEventUseCase()
            analytics_repository=mock_analytics_repository,
            cache_service=mock_cache_service
        (        )
        
        # Attach the mock logger for assert ions
        use_case._logger = mock_logger_instance
        return use_case


        @pytest.mark.db_required()
        class TestProcessAnalyticsEventUseCase:
    """Test suite for the ProcessAnalyticsEventUseCase."""
    
    @pytest.mark.asyncio()
    async def test_execute_with_all_parameters(self, use_case, mock_analytics_repository):
        """
        Test processing an event with all parameters provided.
        """
        # Arrange
        event_type = "page_view"
        event_data = {"page": "/dashboard", "time_on_page": 45}
        user_id = "user-123"
        session_id = "session-456"
        timestamp = datetime(2025, 3, 30, 0, 0, 0)
        
        # Act
        result = await use_case.execute()
        event_type=event_type,
        event_data=event_data,
        user_id=user_id,
        session_id=session_id,
        timestamp=timestamp
        (    )
        
        # Assert
        assert result.event_type  ==  event_type
        assert result.event_data  ==  event_data
        assert result.user_id  ==  user_id
        assert result.session_id  ==  session_id
        assert result.timestamp  ==  timestamp
        assert result.event_id  ==  "test-event-id-123"
        
        # Verify repository was called correctly
        mock_analytics_repository.save_event.assert_called_once()
        
        # Verify appropriate logging (without PHI)
        use_case._logger.info.assert_called_with()
        f"Processing analytics event of type: {event_type}",
        {"session_id": session_id}
        (    )
    
        @pytest.mark.asyncio()
        async def test_execute_with_minimal_parameters(self, use_case):
        """
        Test processing an event with only required parameters.
        """
        # Arrange
        event_type = "feature_usage"
        event_data = {"feature": "digital_twin", "action": "zoom"}
        
        # Act
        result = await use_case.execute()
        event_type=event_type,
        event_data=event_data
        (    )
        
        # Assert
        assert result.event_type  ==  event_type
        assert result.event_data  ==  event_data
        assert result.user_id is None
        assert result.session_id is None
        assert isinstance(result.timestamp, datetime)
        assert result.event_id  ==  "test-event-id-123"
        
        # Verify appropriate logging (without PHI)
        use_case._logger.info.assert_called_with()
        f"Processing analytics event of type: {event_type}",
        {"session_id": None}
        (    )
    
        @pytest.mark.asyncio()
        async def test_real_time_counter_updates(self, use_case, mock_cache_service):
        """
        Test that real-time counters are updated in cache.
        """
        # Arrange
        event_type = "patient_search"
        event_data = {"query_type": "name"}
        user_id = "provider-789"
        
        # Act
        await use_case.execute()
        event_type=event_type,
        event_data=event_data,
        user_id=user_id
        (    )
        
        # Assert - verify cache service was called to update counters
        mock_cache_service.increment.assert _any_call(f"analytics:counter:{event_type}")
        mock_cache_service.increment.assert _any_call(f"analytics:user:{user_id}:{event_type}")
    
        @pytest.mark.asyncio()
        async def test_phi_not_logged(self, use_case):
        """
        Test that PHI is not included in logs even if present in event data.
        """
        # Arrange - include data that could be PHI
        event_type = "patient_record_view"
        event_data = {"patient_name": "John Smith", "mrn": "12345678"}
        user_id = "doctor-456"
        session_id = "session-xyz"
        
        # Act
        await use_case.execute()
        event_type=event_type,
        event_data=event_data,
        user_id=user_id,
        session_id=session_id
        (    )
        
        # Assert - only non-PHI should be logged
        use_case._logger.info.assert_called_with()
        f"Processing analytics event of type: {event_type}",
        {"session_id": session_id}
        (    )
        
        # The event_data containing PHI should not be in any log parameters
        log_calls = use_case._logger.info.call_args_list
        for call in log_calls:
        args, kwargs = call
        assert "patient_name" not in str(args)
        assert "mrn" not in str(args)
        assert "John Smith" not in str(args)
        assert "12345678" not in str(args)
    
        @pytest.mark.asyncio()
        async def test_repository_error_handling(self, use_case, mock_analytics_repository):
        """
        Test proper error handling when repository operations fail.
        """
        # Arrange
        mock_analytics_repository.save_event.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(Exception) as excinfo:
        await use_case.execute()
        event_type="error_test",
        event_data={"test": True}
        (    )
        
        assert "Database connection error" in str(excinfo.value)