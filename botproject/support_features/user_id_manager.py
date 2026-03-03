# user_id_manager.py - Sequential User ID Management with Deletion Support

import logging
from typing import Optional, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class SequentialUserIDManager:
    """Manages sequential user IDs starting from 1000 with deletion/reactivation support"""
    
    def __init__(self, mongodb_manager=None):
        self.mongodb_manager = mongodb_manager
        self.starting_id = 1000
        
    def get_next_user_id(self) -> int:
        """Get the next available sequential user ID"""
        if not self.mongodb_manager:
            logger.warning("MongoDB not available, using timestamp-based ID")
            return int(datetime.now().timestamp()) % 1000000 + 1000
        
        try:
            # Get the highest user_id from the database
            highest_user = self.mongodb_manager.users_collection.find_one(
                {"deleted": {"$ne": True}},
                sort=[("user_id", -1)]
            )
            
            if highest_user and highest_user.get('user_id'):
                return highest_user['user_id'] + 1
            else:
                return self.starting_id
                
        except Exception as e:
            logger.error(f"Error getting next user ID: {e}")
            return self.starting_id
    
    def check_existing_user(self, identifier: str) -> Tuple[bool, Optional[int], Optional[Dict]]:
        """
        Check if user exists (including deleted users)

        Args:
            identifier: Phone number or email address

        Returns: (exists, user_id, user_data)
        """
        if not self.mongodb_manager:
            return False, None, None

        try:
            # Determine if identifier is email or phone
            is_email = '@' in identifier if identifier else False

            # Build query based on identifier type
            if is_email:
                # For OAuth users, search by email field first
                # Also check phone field (legacy: some OAuth users have email stored in phone)
                query_active = {
                    "$or": [
                        {"preferences.email": identifier},
                        {"preferences.phone": identifier}  # Legacy: email was stored in phone
                    ],
                    "deleted": {"$ne": True}
                }
                query_deleted = {
                    "$or": [
                        {"preferences.email": identifier},
                        {"preferences.phone": identifier}
                    ],
                    "deleted": True
                }
            else:
                # For phone users, search by phone
                query_active = {
                    "preferences.phone": identifier,
                    "deleted": {"$ne": True}
                }
                query_deleted = {
                    "preferences.phone": identifier,
                    "deleted": True
                }

            # First check active users
            active_user = self.mongodb_manager.users_collection.find_one(query_active)

            if active_user:
                preferences = active_user.get('preferences', {})
                return True, active_user['user_id'], {
                    'status': 'active',
                    'user_name': preferences.get('user_name', 'User'),
                    'full_name': preferences.get('full_name', ''),
                    'email': preferences.get('email', ''),
                    'phone': preferences.get('phone', ''),
                    'created_at': active_user.get('created_at')
                }

            # Check deleted users
            deleted_user = self.mongodb_manager.users_collection.find_one(query_deleted)

            if deleted_user:
                preferences = deleted_user.get('preferences', {})
                return True, deleted_user['user_id'], {
                    'status': 'deleted',
                    'user_name': preferences.get('user_name', 'User'),
                    'full_name': preferences.get('full_name', ''),
                    'email': preferences.get('email', ''),
                    'phone': preferences.get('phone', ''),
                    'deleted_at': deleted_user.get('deleted_at')
                }

            return False, None, None

        except Exception as e:
            logger.error(f"Error checking existing user: {e}")
            return False, None, None
    
    def reactivate_user(self, user_id: int, identifier: str) -> bool:
        """Reactivate a deleted user account

        Args:
            user_id: User ID
            identifier: Phone number or email address
        """
        if not self.mongodb_manager:
            return False

        try:
            # Determine if identifier is email or phone
            is_email = '@' in identifier if identifier else False

            # Build query based on identifier type
            if is_email:
                query = {
                    "user_id": user_id,
                    "preferences.email": identifier,
                    "deleted": True
                }
            else:
                query = {
                    "user_id": user_id,
                    "preferences.phone": identifier,
                    "deleted": True
                }

            result = self.mongodb_manager.users_collection.update_one(
                query,
                {
                    "$set": {
                        "deleted": False,
                        "reactivated_at": datetime.utcnow(),
                        "preferences.last_login": datetime.now().isoformat(),
                        "updated_at": datetime.utcnow()
                    },
                    "$inc": {
                        "reactivation_count": 1
                    }
                }
            )

            if result.modified_count > 0:
                logger.info(f"Reactivated user account: {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error reactivating user: {e}")
            return False
    
    def delete_user_account(self, user_id: int) -> Dict:
        """Soft delete a user account"""
        if not self.mongodb_manager:
            return {"success": False, "error": "MongoDB not available"}
        
        try:
            # Mark user as deleted (soft delete)
            result = self.mongodb_manager.users_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "deleted": True,
                        "deleted_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Mark all sessions as deleted
                self.mongodb_manager.sessions_collection.update_many(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "deleted": True,
                            "deleted_at": datetime.utcnow()
                        }
                    }
                )
                
                logger.info(f"Soft deleted user account: {user_id}")
                return {"success": True, "message": "Account deleted successfully"}
            else:
                return {"success": False, "error": "User not found"}
                
        except Exception as e:
            logger.error(f"Error deleting user account: {e}")
            return {"success": False, "error": str(e)}

# Initialize the manager
user_id_manager = None

def initialize_user_id_manager(mongodb_manager):
    """Initialize the user ID manager with MongoDB connection"""
    global user_id_manager
    user_id_manager = SequentialUserIDManager(mongodb_manager)
    logger.info("User ID Manager initialized")
    return user_id_manager