"""
Service responsible for user authentication logic.
"""

import logging
from typing import Optional

from app.domain.entities.user import User
# Import password service and user repository interface (adjust path as needed)
from app.infrastructure.security.password.hashing import verify_password
# from app.domain.repositories.user_repository import UserRepository # Example

logger = logging.getLogger(__name__)

class AuthenticationService:
    """
    Handles user authentication by verifying credentials.
    """
    
    # def __init__(self, user_repository: UserRepository): # Example with DI
    #     self.user_repository = user_repository
    def __init__(self):
        # Placeholder for dependency injection (e.g., user repository)
        pass

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticates a user based on username and password.

        Args:
            username: The user's username.
            password: The user's plaintext password.

        Returns:
            The authenticated User object if credentials are valid, otherwise None.
        """
        logger.debug(f"Attempting authentication for user: {username}")
        
        # --- Replace with actual database lookup --- 
        # user = await self.user_repository.get_by_username(username)
        # Mock implementation for now:
        if username == "test_admin":
            from app.infrastructure.security.rbac.roles import Role # Temp import
            # Mock admin user - replace with DB fetch
            mock_hashed_pw = "$2b$12$EixZAe3R3Tjp9.Kq/qL4jeY.RL.xUjS0xJGAUMAPF1z5MdGtJqB9S" # Hash for 'password'
            user = User(id="uuid-admin-123", username="test_admin", roles=[Role.ADMIN], is_active=True, hashed_password=mock_hashed_pw)
        elif username == "test_clinician":
            from app.infrastructure.security.rbac.roles import Role # Temp import
             # Mock clinician user - replace with DB fetch
            mock_hashed_pw = "$2b$12$EixZAe3R3Tjp9.Kq/qL4jeY.RL.xUjS0xJGAUMAPF1z5MdGtJqB9S" # Hash for 'password'
            user = User(id="uuid-clinician-456", username="test_clinician", roles=[Role.CLINICIAN], is_active=True, hashed_password=mock_hashed_pw)
        else:
            user = None
        # --- End replace --- 
            
        if user is None:
            logger.warning(f"Authentication failed: User '{username}' not found.")
            return None

        if not user.hashed_password:
             logger.error(f"Authentication failed: User '{username}' has no stored password hash.")
             return None # Cannot authenticate user without a stored hash

        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password for user '{username}'.")
            return None
            
        if not user.is_active:
            logger.warning(f"Authentication failed: User '{username}' is inactive.")
            # Consider raising a specific exception for inactive users if needed
            return None

        logger.info(f"Authentication successful for user: {username}")
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieves a user by their ID.

        Args:
            user_id: The ID of the user to retrieve.

        Returns:
            The User object if found and active, otherwise None.
        """
        logger.debug(f"Fetching user by ID: {user_id}")
        # --- Replace with actual database lookup --- 
        # user = await self.user_repository.get_by_id(user_id)
        # Mock implementation
        from app.infrastructure.security.rbac.roles import Role # Temp import
        MOCK_USERS = {
            "uuid-admin-123": User(id="uuid-admin-123", username="test_admin", roles=[Role.ADMIN], is_active=True),
            "uuid-clinician-456": User(id="uuid-clinician-456", username="test_clinician", roles=[Role.CLINICIAN], is_active=True),
        }
        user = MOCK_USERS.get(user_id)
        # --- End replace --- 

        if user and user.is_active:
            logger.debug(f"User found and active: {user_id}")
            return user
        elif user:
             logger.warning(f"User found but inactive: {user_id}")
             return None # Or raise specific exception
        else:
            logger.warning(f"User not found: {user_id}")
            return None
