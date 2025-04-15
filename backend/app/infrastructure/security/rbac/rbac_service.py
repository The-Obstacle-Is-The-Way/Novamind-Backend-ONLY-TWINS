"""
Unified Role-Based Access Control (RBAC) Service.

This service provides a centralized way to manage and check roles and permissions,
drawing definitions from the `roles` module.
"""

import logging
from typing import List, Optional, Set

# Use relative import within the same package
from .roles import Role, ROLE_PERMISSIONS, has_permission as check_role_has_permission

# Assuming User entity might be needed for context later
# from app.domain.entities.user import User 

logger = logging.getLogger(__name__)

class RBACService:
    """
    Provides methods to check user permissions based on their roles.
    
    Uses the definitive roles and permissions defined in `roles.py`.
    """

    def __init__(self):
        """Initialize the RBAC service."""
        # Roles and permissions are loaded directly from the imported roles module
        pass 

    def check_permission(self, user_roles: List[Role], required_permission: str) -> bool:
        """
        Check if a user with the given roles has a specific permission.

        Args:
            user_roles: List of Role enums the user possesses.
            required_permission: The permission string to check for.

        Returns:
            True if any of the user's roles grant the permission, False otherwise.
        """
        if not user_roles:
            return False
            
        # Delegate to the check function from roles.py for consistency
        has_perm = check_role_has_permission(user_roles, required_permission)
        
        # Future: Implement context-aware checks here if needed 
        # (e.g., checking resource ownership for 'own_' permissions)
        # Example:
        # if not has_perm and required_permission.startswith("read:"):
        #     own_perm = f"read:own_{required_permission.split(':', 1)[1]}"
        #     if check_role_has_permission(user_roles, own_perm):
        #          # Need resource_owner_id and user_id context here
        #          pass # Logic to compare owner_id and user_id

        logger.debug(f"Permission check: Roles={user_roles}, Required='{required_permission}', Result={has_perm}")
        return has_perm

    def get_permissions_for_roles(self, roles: List[Role]) -> List[str]:
        """
        Get the combined set of unique permissions for the given roles.

        Args:
            roles: List of Role enums.

        Returns:
            A list of unique permission strings.
        """
        all_permissions: Set[str] = set()
        for role in roles:
            # Use the imported dictionary directly
            all_permissions.update(ROLE_PERMISSIONS.get(role, []))
        return list(all_permissions)

# Optional: Singleton pattern if desired, similar to role_manager.py
# from functools import lru_cache
# @lru_cache(maxsize=1)
# def get_rbac_service() -> RBACService:
#     return RBACService()

