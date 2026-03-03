"""
Contact Support Service
Handles business logic for contact support operations
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
import math

logger = logging.getLogger(__name__)


class ContactSupportService:
    """Service for managing contact support information"""

    def __init__(self, mongodb_manager=None):
        self.mongodb_manager = mongodb_manager
        logger.info("ContactSupportService initialized")

    def _generate_id(self, prefix: str = "cs") -> str:
        """Generate a unique ID with prefix"""
        return f"{prefix}_{ObjectId()}"

    def _serialize_document(self, doc: Dict) -> Dict:
        """Serialize MongoDB document for JSON response"""
        if doc is None:
            return None

        serialized = {}
        for key, value in doc.items():
            if key == '_id':
                continue  # Skip MongoDB internal ID
            elif isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = self._serialize_document(value)
            elif isinstance(value, list):
                serialized[key] = [
                    self._serialize_document(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                serialized[key] = value
        return serialized

    def get_contact_support(self) -> Optional[Dict[str, Any]]:
        """
        Get contact support details

        Returns:
            Contact support data or None if not found
        """
        try:
            if not self.mongodb_manager:
                logger.error("MongoDB manager not available")
                return None

            # Get the latest contact support document
            doc = self.mongodb_manager.contact_support_collection.find_one(
                {},
                sort=[("updated_at", -1)]
            )

            if not doc:
                logger.info("No contact support details found")
                return None

            return self._serialize_document(doc)

        except Exception as e:
            logger.error(f"Error getting contact support: {e}")
            return None

    def create_or_update_contact_support(
        self,
        data: Dict[str, Any],
        admin_id: str,
        admin_email: Optional[str] = None,
        admin_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create or update contact support details

        Args:
            data: Contact support data
            admin_id: Admin user ID for audit
            admin_email: Admin email for audit
            admin_name: Admin name for audit

        Returns:
            Created/updated contact support data
        """
        try:
            if not self.mongodb_manager:
                raise ValueError("MongoDB service unavailable")

            current_time = datetime.now(timezone.utc)

            # Check if contact support already exists
            existing = self.mongodb_manager.contact_support_collection.find_one({})

            if existing:
                # Update existing
                old_data = self._serialize_document(existing)
                contact_id = existing.get('id')

                # Find changed fields
                changed_fields = self._get_changed_fields(old_data, data)

                # Update document
                update_data = {
                    **data,
                    "updated_at": current_time,
                    "updated_by": admin_email or admin_id
                }

                self.mongodb_manager.contact_support_collection.update_one(
                    {"id": contact_id},
                    {"$set": update_data}
                )

                # Log history
                if changed_fields:
                    self._log_history(
                        contact_id=contact_id,
                        action="UPDATE",
                        changed_fields=changed_fields,
                        old_values=self._extract_values(old_data, changed_fields),
                        new_values=self._extract_values(data, changed_fields),
                        admin_id=admin_id,
                        admin_email=admin_email,
                        admin_name=admin_name
                    )

                # Get updated document
                updated = self.mongodb_manager.contact_support_collection.find_one({"id": contact_id})
                logger.info(f"Updated contact support: {contact_id}")
                return self._serialize_document(updated)

            else:
                # Create new
                contact_id = self._generate_id("cs")

                new_doc = {
                    "id": contact_id,
                    **data,
                    "created_at": current_time,
                    "updated_at": current_time,
                    "updated_by": admin_email or admin_id
                }

                self.mongodb_manager.contact_support_collection.insert_one(new_doc)

                # Log history
                self._log_history(
                    contact_id=contact_id,
                    action="CREATE",
                    changed_fields=["all"],
                    old_values=None,
                    new_values=data,
                    admin_id=admin_id,
                    admin_email=admin_email,
                    admin_name=admin_name
                )

                logger.info(f"Created contact support: {contact_id}")
                return self._serialize_document(new_doc)

        except Exception as e:
            logger.error(f"Error creating/updating contact support: {e}")
            raise

    def _get_changed_fields(self, old_data: Dict, new_data: Dict, prefix: str = "") -> List[str]:
        """Get list of changed field paths"""
        changed = []

        for key, new_value in new_data.items():
            field_path = f"{prefix}{key}" if prefix else key
            old_value = old_data.get(key)

            if isinstance(new_value, dict) and isinstance(old_value, dict):
                # Recursively check nested dicts
                nested_changes = self._get_changed_fields(old_value, new_value, f"{field_path}.")
                changed.extend(nested_changes)
            elif new_value != old_value:
                changed.append(field_path)

        return changed

    def _extract_values(self, data: Dict, fields: List[str]) -> Dict[str, Any]:
        """Extract values for specific fields from data"""
        values = {}
        for field in fields:
            parts = field.split('.')
            current = data
            try:
                for part in parts:
                    if current is None:
                        break
                    current = current.get(part) if isinstance(current, dict) else None
                values[field] = current
            except (KeyError, TypeError):
                values[field] = None
        return values

    def _log_history(
        self,
        contact_id: str,
        action: str,
        changed_fields: List[str],
        old_values: Optional[Dict],
        new_values: Optional[Dict],
        admin_id: str,
        admin_email: Optional[str] = None,
        admin_name: Optional[str] = None
    ):
        """Log contact support change to history"""
        try:
            history_doc = {
                "id": self._generate_id("hist"),
                "contact_support_id": contact_id,
                "action": action,
                "changed_fields": changed_fields,
                "old_values": old_values,
                "new_values": new_values,
                "updated_by": {
                    "id": admin_id,
                    "email": admin_email,
                    "name": admin_name
                },
                "updated_at": datetime.now(timezone.utc)
            }

            self.mongodb_manager.contact_support_history_collection.insert_one(history_doc)
            logger.info(f"Logged history for contact support: {contact_id}, action: {action}")

        except Exception as e:
            logger.error(f"Error logging contact support history: {e}")

    def get_contact_support_history(
        self,
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get contact support change history with pagination

        Args:
            page: Page number (1-indexed)
            limit: Records per page

        Returns:
            History data with pagination info
        """
        try:
            if not self.mongodb_manager:
                raise ValueError("MongoDB service unavailable")

            skip = (page - 1) * limit

            # Get total count
            total_records = self.mongodb_manager.contact_support_history_collection.count_documents({})
            total_pages = math.ceil(total_records / limit) if total_records > 0 else 1

            # Get history records
            cursor = self.mongodb_manager.contact_support_history_collection.find(
                {},
                sort=[("updated_at", -1)]
            ).skip(skip).limit(limit)

            history = [self._serialize_document(doc) for doc in cursor]

            return {
                "history": history,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_records": total_records,
                    "per_page": limit
                }
            }

        except Exception as e:
            logger.error(f"Error getting contact support history: {e}")
            raise


# Global service instance
contact_support_service = None


def initialize_contact_support_service(mongodb_manager):
    """Initialize the contact support service with MongoDB connection"""
    global contact_support_service
    contact_support_service = ContactSupportService(mongodb_manager)
    logger.info("Contact Support Service initialized")
    return contact_support_service


def get_contact_support_service() -> ContactSupportService:
    """Get the contact support service instance"""
    global contact_support_service
    if contact_support_service is None:
        logger.warning("Contact Support Service not initialized, creating without MongoDB")
        contact_support_service = ContactSupportService()
    return contact_support_service
