"""
Service responsible for user authentication logic.
"""

import logging
from typing import Optional
import uuid

from app.domain.entities.user import User
# Import password service and user repository interface (adjust path as needed)
from app.infrastructure.security.password.hashing import verify_password
# from app.domain.repositories.user_repository import UserRepository # Example
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.security.password.password_handler import PasswordHandler
from app.infrastructure.security.jwt.jwt_service import JWTService
# CORRECTED Import: Use UserModel from infrastructure, and Role from domain
from app.infrastructure.models.user_model import UserModel 
from app.domain.enums.role import Role 
# CORRECTED import: Use EntityNotFoundError
from app.domain.exceptions import AuthenticationError, EntityNotFoundError 

logger = logging.getLogger(__name__)

class AuthenticationService:
    """
    Handles user authentication by verifying credentials.
    """
    
    # def __init__(self, user_repository: UserRepository): # Example with DI
    #     self.user_repository = user_repository
    def __init__(
        self,
        user_repository: UserRepository,
        password_handler: PasswordHandler,
        jwt_service: JWTService,
    ):
        """Initialize the AuthenticationService.

        Args:
            user_repository: Repository for user data access.
            password_handler: Handler for password hashing and verification.
            jwt_service: Service for JWT token creation and validation.
        """
        self.user_repository = user_repository
        self.password_handler = password_handler
        self.jwt_service = jwt_service
        logger.info("AuthenticationService initialized with dependencies.")

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
        Retrieve a user by their unique ID.

        Args:
            user_id: The unique identifier of the user (string UUID).

        Returns:
            User DOMAIN model object if found, None otherwise.
        """
        logger.debug(f"Retrieving user by ID: {user_id}")
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.warning(f"Invalid UUID format provided for user_id: {user_id}")
            return None
        
        user_model: Optional[UserModel] = await self.user_repository.get_by_id(user_uuid)

        if not user_model:
            logger.warning(f"User not found by ID via repository: {user_id}")
            # Raise EntityNotFoundError instead of returning None
            # This aligns better with signaling failure to find a resource
            raise EntityNotFoundError(f"User with ID {user_id} not found.") 
            
        # Map ORM UserModel to domain User model (if they are different)
        # If User domain model is different from UserModel ORM model, mapping is needed.
        # If they are intended to be the same, then this mapping is redundant,
        # but the type hints should reflect UserModel is being handled internally.
        # Let's assume for now a mapping is intended based on previous structure.
        try:
            # Import User domain model HERE if it's different and lives elsewhere
            # e.g., from app.domain.entities.user import User as DomainUser
            # For now, assume User == UserModel is intended, or mapping needs adjustment
            # Based on previous context, let's assume User is defined in domain.models.user_model
            from app.domain.models.user_model import User # Re-import domain model for clarity
            
            # Perform mapping
            user_domain = User(
                id=user_model.id,
                email=user_model.email,
                first_name=user_model.first_name,
                last_name=user_model.last_name,
                roles=[Role(role_str) for role_str in user_model.roles], 
                is_active=user_model.is_active,
                hashed_password=user_model.hashed_password, 
                # date_joined=user_model.created_at, # Map audit fields if needed
            )
            logger.debug(f"User found and mapped to domain model: {user_id}")
            return user_domain
        except ImportError:
             logger.error("Failed to import User domain model for mapping. Check path.")
             raise # Re-raise import error
        except Exception as e:
            logger.error(f"Failed to map UserModel to User domain model for ID {user_id}: {e}", exc_info=True)
            # Instead of returning None, maybe raise a specific MappingError?
            raise RuntimeError(f"Failed to process user data for {user_id}") from e
