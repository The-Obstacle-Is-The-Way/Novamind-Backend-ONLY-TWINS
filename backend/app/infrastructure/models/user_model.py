"""
SQLAlchemy user model for database operations.

This module defines the SQLAlchemy ORM model for users, which maps to a
database table and provides the data access layer for user operations.
"""
import uuid
from datetime import datetime, timedelta
from app.domain.utils.datetime_utils import UTC
from typing import List

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.core.db import Base


class UserModel(Base):
    """
    SQLAlchemy ORM model for users.
    
    This model maps to the database 'users' table and contains
    columns for all user fields needed for authentication,
    authorization, and user identity.
    """
    __tablename__ = "users"
    
    # Primary key and identity
    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = sa.Column(sa.String, unique=True, index=True, nullable=False)
    first_name = sa.Column(sa.String, nullable=False)
    last_name = sa.Column(sa.String, nullable=False)
    
    # Authentication
    hashed_password = sa.Column(sa.String, nullable=False)
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
    
    # Authorization
    roles = sa.Column(ARRAY(sa.String), default=[], nullable=False)
    
    # Audit fields
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = sa.Column(
        sa.DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Add SQLite compatibility for array type
    __table_args__ = {
        'sqlite_autoincrement': True,
    }
    
    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User {self.email}>"