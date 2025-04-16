# -*- coding: utf-8 -*-
"""
Authentication related dependencies.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status

# Domain/Infrastructure Services & Repositories
from app.infrastructure.security.auth.authentication_service import AuthenticationService
from app.infrastructure.security.jwt.jwt_service import JWTService, get_jwt_service
from app.infrastructure.security.password.password_handler import PasswordHandler
from app.domain.repositories.user_repository import UserRepository
# REMOVED: from app.presentation.dependencies.repository import get_user_repository 

logger = logging.getLogger(__name__)

# Dependency provider for PasswordHandler (assuming simple instantiation)
def get_password_handler() -> PasswordHandler:
    """Provides a PasswordHandler instance."""
    return PasswordHandler()

# Placeholder provider for UserRepository
# This should be replaced with a real provider that yields an actual implementation
# possibly depending on a database session (e.g., Depends(get_db_session))
async def get_user_repository() -> UserRepository:
    """Placeholder dependency provider for UserRepository."""
    # In a real application, this would return an instance of UserRepositoryImpl
    # For now, raise error or return a mock if needed outside tests.
    # Tests should override this provider.
    logger.warning("Using placeholder get_user_repository provider.")
    # Option 1: Raise error if called outside test override
    raise NotImplementedError("UserRepository implementation/provider not fully configured.")
    # Option 2: Return a basic mock (less safe, might hide issues)
    # from unittest.mock import AsyncMock
    # return AsyncMock(spec=UserRepository)

# Dependency provider for AuthenticationService
def get_authentication_service(
    # Declare dependencies using Depends
    user_repo: UserRepository = Depends(get_user_repository), 
    password_handler: PasswordHandler = Depends(get_password_handler),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> AuthenticationService:
    """Provides an instance of AuthenticationService with its dependencies resolved."""
    logger.debug("Resolving AuthenticationService dependency.")
    return AuthenticationService(
        user_repository=user_repo,
        password_handler=password_handler,
        jwt_service=jwt_service
    )

# Note: get_jwt_service is likely already defined in jwt_service.py
# Note: get_user_repository needs to be defined, potentially in a repositories dependency file.
# For now, assume get_user_repository exists or will be mocked/overridden in tests. 