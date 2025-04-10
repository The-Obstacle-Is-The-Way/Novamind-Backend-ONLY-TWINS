"""
SQLAlchemy model for Patient entity in the Novamind Digital Twin platform.

This module defines the database model for patients, mapping the domain
entity to a database table.
"""
from sqlalchemy import Column, String, DateTime, JSON, Table, MetaData
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import json

# Define metadata
metadata = MetaData()

# Define Patient table
PatientModel = Table(
    "patients",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("date_of_birth", String, nullable=False),
    Column("gender", String, nullable=False),
    Column("email", String, nullable=True),
    Column("phone", String, nullable=True),
    Column("address", String, nullable=True),
    Column("insurance_number", String, nullable=True),
    Column("medical_history", JSON, nullable=True),
    Column("medications", JSON, nullable=True),
    Column("allergies", JSON, nullable=True),
    Column("treatment_notes", JSON, nullable=True),
    Column("created_at", String, nullable=False, server_default=func.now()),
    Column("updated_at", String, nullable=False, server_default=func.now(), onupdate=func.now()),
)
