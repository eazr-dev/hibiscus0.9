"""
Eazr Credit Waitlist Service - Business Logic Layer
Handles all waitlist operations with MongoDB storage
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
from bson import ObjectId

logger = logging.getLogger(__name__)

# IST Timezone helper
def get_ist_now() -> datetime:
    """Get current time in IST (Indian Standard Time - UTC+5:30)"""
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_timezone)


def get_utc_now() -> datetime:
    """Get current UTC time"""
    return datetime.now(timezone.utc)


class EazrCreditWaitlistService:
    """
    Service class for Eazr Credit Waitlist operations

    Handles:
    - Adding users to waitlist
    - Checking waitlist status
    - Generating unique waitlist IDs
    - Position calculation
    """

    COLLECTION_NAME = "eazr_credit_waitlist"

    def __init__(self):
        self.logger = logger
        self._collection = None
        self._db = None

    def _get_collection(self):
        """Lazy load MongoDB collection"""
        if self._collection is None:
            try:
                from database_storage.mongodb_chat_manager import mongodb_chat_manager
                if mongodb_chat_manager is not None and mongodb_chat_manager.db is not None:
                    self._db = mongodb_chat_manager.db
                    self._collection = self._db[self.COLLECTION_NAME]

                    # Create indexes for efficient queries
                    self._ensure_indexes()

                    self.logger.info(f"✓ Eazr Credit Waitlist collection initialized")
                else:
                    self.logger.error("MongoDB not available for waitlist service")
                    raise ConnectionError("Database not available")
            except ImportError as e:
                self.logger.error(f"Could not import MongoDB manager: {e}")
                raise ConnectionError("Database module not available")
        return self._collection

    def _ensure_indexes(self):
        """Create necessary indexes for the waitlist collection"""
        try:
            if self._collection is not None:
                # Unique index on user_id to prevent duplicates
                self._collection.create_index("user_id", unique=True)
                # Index on waitlist_id for quick lookups
                self._collection.create_index("waitlist_id")
                # Index on position for ordering
                self._collection.create_index("position")
                # Index on status for filtering
                self._collection.create_index("status")
                self.logger.info("✓ Waitlist indexes created/verified")
        except Exception as e:
            self.logger.warning(f"Could not create indexes: {e}")

    def _generate_waitlist_id(self, position: int) -> str:
        """
        Generate unique waitlist ID in format: WL-YYYY-NNNNNN

        Args:
            position: User's position in waitlist

        Returns:
            Unique waitlist ID string
        """
        year = datetime.now().year
        return f"WL-{year}-{position:06d}"

    def _get_next_position(self) -> int:
        """
        Get next available position in waitlist

        Returns:
            Next position number (1-indexed)
        """
        try:
            collection = self._get_collection()
            # Find the highest position
            result = collection.find_one(
                {"status": {"$in": ["active", "notified", "converted"]}},
                sort=[("position", -1)]
            )
            if result and result.get("position"):
                return result["position"] + 1
            return 1
        except Exception as e:
            self.logger.error(f"Error getting next position: {e}")
            return 1

    def join_waitlist(self, user_id: int) -> Tuple[bool, Dict[str, Any], int]:
        """
        Add user to the Eazr Credit waitlist

        Args:
            user_id: User's unique ID

        Returns:
            Tuple of (success, data_dict, http_status_code)
            - On success: (True, waitlist_data, 200)
            - If already exists: (False, existing_data, 409)
            - On error: (False, error_data, 500)
        """
        try:
            collection = self._get_collection()

            # Check if user already exists in waitlist
            existing = collection.find_one({"user_id": user_id})

            if existing:
                # User already on waitlist - return 409 Conflict
                self.logger.info(f"User {user_id} already on waitlist")
                return False, {
                    "is_waitlisted": True,
                    "user_id": user_id,
                    "waitlist_id": existing.get("waitlist_id"),
                    "position": existing.get("position"),
                    "joined_at": existing.get("joined_at").isoformat() + "Z" if existing.get("joined_at") else None
                }, 409

            # Get next position
            position = self._get_next_position()
            waitlist_id = self._generate_waitlist_id(position)
            joined_at = get_utc_now()

            # Create waitlist entry
            waitlist_entry = {
                "waitlist_id": waitlist_id,
                "user_id": user_id,
                "position": position,
                "joined_at": joined_at,
                "status": "active",  # active, notified, converted
                "created_at": joined_at,
                "updated_at": joined_at
            }

            # Insert into database
            result = collection.insert_one(waitlist_entry)

            if result.inserted_id:
                self.logger.info(f"✓ User {user_id} joined waitlist at position {position}")
                return True, {
                    "waitlist_id": waitlist_id,
                    "user_id": user_id,
                    "is_waitlisted": True,
                    "position": position,
                    "joined_at": joined_at.isoformat() + "Z"
                }, 200
            else:
                self.logger.error(f"Failed to insert waitlist entry for user {user_id}")
                return False, {
                    "is_waitlisted": False,
                    "user_id": user_id,
                    "waitlist_id": None,
                    "position": None,
                    "joined_at": None
                }, 500

        except Exception as e:
            self.logger.error(f"Error adding user {user_id} to waitlist: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False, {
                "is_waitlisted": False,
                "user_id": user_id,
                "waitlist_id": None,
                "position": None,
                "joined_at": None
            }, 500

    def get_waitlist_status(self, user_id: int) -> Dict[str, Any]:
        """
        Check if user is on the waitlist

        Args:
            user_id: User's unique ID

        Returns:
            Dictionary with waitlist status data
        """
        try:
            collection = self._get_collection()

            # Find user in waitlist
            entry = collection.find_one({"user_id": user_id})

            if entry:
                self.logger.info(f"User {user_id} found in waitlist at position {entry.get('position')}")
                return {
                    "user_id": user_id,
                    "is_waitlisted": True,
                    "waitlist_id": entry.get("waitlist_id"),
                    "position": entry.get("position"),
                    "joined_at": entry.get("joined_at").isoformat() + "Z" if entry.get("joined_at") else None
                }
            else:
                self.logger.info(f"User {user_id} not found in waitlist")
                return {
                    "user_id": user_id,
                    "is_waitlisted": False,
                    "waitlist_id": None,
                    "position": None,
                    "joined_at": None
                }

        except Exception as e:
            self.logger.error(f"Error checking waitlist status for user {user_id}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Return safe default on error
            return {
                "user_id": user_id,
                "is_waitlisted": False,
                "waitlist_id": None,
                "position": None,
                "joined_at": None
            }

    def get_waitlist_stats(self) -> Dict[str, Any]:
        """
        Get overall waitlist statistics (for admin use)

        Returns:
            Dictionary with waitlist statistics
        """
        try:
            collection = self._get_collection()

            total_count = collection.count_documents({})
            active_count = collection.count_documents({"status": "active"})
            notified_count = collection.count_documents({"status": "notified"})
            converted_count = collection.count_documents({"status": "converted"})

            return {
                "total_signups": total_count,
                "active": active_count,
                "notified": notified_count,
                "converted": converted_count
            }
        except Exception as e:
            self.logger.error(f"Error getting waitlist stats: {e}")
            return {
                "total_signups": 0,
                "active": 0,
                "notified": 0,
                "converted": 0
            }


# Create singleton instance
eazr_credit_waitlist_service = EazrCreditWaitlistService()
