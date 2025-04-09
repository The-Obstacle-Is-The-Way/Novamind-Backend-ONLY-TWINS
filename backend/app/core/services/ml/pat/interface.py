"""
Interface definition for PAT service.

This module defines the interface that all PAT implementations must follow.
For backward compatibility with existing code, we maintain this interface
alongside the newer PATBase class.
"""

from app.core.services.ml.pat.base import PATBase

# For compatibility with existing code, we alias PATBase as PATInterface
PATInterface = PATBase
