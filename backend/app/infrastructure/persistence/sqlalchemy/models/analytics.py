# -*- coding: utf-8 -*-
"""
SQLAlchemy models for analytics.

This module defines the ORM models for analytics data,
mapping domain entities to database tables.
"""

import uuid
from datetime import datetime, UTC, UTC
from typing import Dict, Any, Optional

from sqlalchemy import Column, String, DateTime, Integer, JSON, func, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableDict

from app.infrastructure.persistence.sqlalchemy.config.base import Base


class AnalyticsEventModel(Base):
    """
    SQLAlchemy model for analytics events.
    
    This model stores individual analytics events like page views,
    feature usage, and other trackable user interactions.
    """
    
    __tablename__ = "analytics_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(MutableDict.as_mutable(JSONB), nullable=False, default=dict)
    user_id = Column(String(100), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Useful indexes for analytics queries
    __table_args__ = (
        # Index for filtering by event type and time range
        Index('ix_analytics_events_type_timestamp', 'event_type', 'timestamp'),
        
        # Index for user analytics
        Index('ix_analytics_events_user_timestamp', 'user_id', 'timestamp'),
        
        # Index for session analytics
        Index('ix_analytics_events_session_timestamp', 'session_id', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<AnalyticsEvent(id={self.id}, type={self.event_type}, timestamp={self.timestamp})>"


class AnalyticsAggregateModel(Base):
    """
    SQLAlchemy model for pre-computed analytics aggregates.
    
    This model stores aggregated analytics data like counts, averages,
    and other metrics grouped by dimensions for faster dashboard retrieval.
    """
    
    __tablename__ = "analytics_aggregates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type = Column(String(50), nullable=False, index=True)
    dimensions = Column(MutableDict.as_mutable(JSONB), nullable=False, default=dict)
    metrics = Column(MutableDict.as_mutable(JSONB), nullable=False, default=dict)
    time_period = Column(MutableDict.as_mutable(JSONB), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    ttl = Column(Integer, nullable=True)  # Time-to-live in seconds
    
    __table_args__ = (
        # Index for efficient lookups by dimensions
        Index('ix_analytics_aggregates_dimensions', 'dimensions', postgresql_using='gin'),
        
        # Index for finding aggregates by type
        Index('ix_analytics_aggregates_type_created', 'aggregate_type', 'created_at'),
    )
    
    def __repr__(self) -> str:
        """Return string representation of the model."""
        dim_str = ", ".join(f"{k}={v}" for k, v in self.dimensions.items())
        return f"<AnalyticsAggregate(id={self.id}, dimensions={dim_str})>"


class AnalyticsJobModel(Base):
    """
    SQLAlchemy model for analytics processing jobs.
    
    This model tracks background analytics processing jobs,
    such as batch processing, aggregation, and reporting tasks.
    """
    
    __tablename__ = "analytics_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    parameters = Column(MutableDict.as_mutable(JSONB), nullable=False, default=dict)
    result = Column(MutableDict.as_mutable(JSONB), nullable=True)
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<AnalyticsJob(id={self.id}, type={self.job_type}, status={self.status})>"