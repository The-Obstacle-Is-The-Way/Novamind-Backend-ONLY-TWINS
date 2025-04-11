# -*- coding: utf-8 -*-
"""
SQLAlchemy models for BiometricTwin and BiometricDataPoint entities.

This module defines the database models for storing biometric twin data,
including the core twin entity and its associated data points.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, String, DateTime, Boolean, Float, ForeignKey, JSON, ARRAY
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.sqlalchemy.config.database import Base


class BiometricTwinModel(Base):
    """
    SQLAlchemy model for BiometricTwin entities.
    
    This model represents the core biometric twin entity in the database,
    storing metadata about the twin and its relationship to a patient.
    """
    
    __tablename__ = "biometric_twins"
    
    twin_id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    baseline_established = Column(Boolean, nullable=False, default=False)
    connected_devices = Column(ARRAY(String), nullable=True)
    
    # Relationships
    data_points = relationship(
        "BiometricDataPointModel", 
        back_populates="twin",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<BiometricTwin(twin_id={self.twin_id}, patient_id={self.patient_id})>"


class BiometricDataPointModel(Base):
    """
    SQLAlchemy model for BiometricDataPoint entities.
    
    This model represents individual biometric measurements associated with
    a biometric twin, storing the measurement value, metadata, and context.
    """
    
    __tablename__ = "biometric_data_points"
    
    data_id = Column(String, primary_key=True, index=True)
    twin_id = Column(String, ForeignKey("biometric_twins.twin_id"), index=True, nullable=False)
    data_type = Column(String, index=True, nullable=False)
    value = Column(String, nullable=False)
    value_type = Column(String, nullable=False)  # "number", "string", "json"
    timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String, nullable=False, index=True)
    metadata = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)
    
    # Relationships
    twin = relationship("BiometricTwinModel", back_populates="data_points")
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return (
            f"<BiometricDataPoint(data_id={self.data_id}, "
            f"twin_id={self.twin_id}, data_type={self.data_type})>"
        )