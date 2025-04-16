# -*- coding: utf-8 -*-
"""
Domain entities related to Pharmacogenomics (PGx).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime

@dataclass
class PGXResult:
    """Represents a single PGx result (e.g., for a specific gene/variant)."""
    gene: str
    variant: str
    result: str  # e.g., "Normal Metabolizer", "*1/*2", etc.
    # Add more relevant fields as needed

@dataclass
class PGXReport:
    """Represents a full PGx report for a patient."""
    # Non-default fields first
    patient_id: UUID
    report_date: datetime
    
    # Fields with defaults
    id: UUID = field(default_factory=uuid4)
    results: List[PGXResult] = field(default_factory=list)
    provider_notes: Optional[str] = None
    # Add other report metadata

    # Removed custom __init__; dataclass default should work with correct field order. 