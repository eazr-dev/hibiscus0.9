"""
Admin Service
Business logic for admin operations (user management, statistics, system operations)
"""
import logging
import os
import jwt
import qrcode
import base64
from io import BytesIO
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

# Admin configuration
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "your-admin-secret-key-change-this")


class AdminService:
    """Service for handling admin operations"""

    def __init__(self):
        """Initialize admin service"""
        from core.dependencies import MONGODB_AVAILABLE
        if MONGODB_AVAILABLE:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            self.mongodb_manager = mongodb_chat_manager
        else:
            self.mongodb_manager = None
            logger.warning("MongoDB not available for AdminService")

    def create_admin_token(self, username: str) -> str:
        """Create admin JWT token"""
        payload = {
            "username": username,
            "role": "admin",
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        token = jwt.encode(payload, ADMIN_SECRET_KEY, algorithm="HS256")
        return token

    def verify_admin_credentials(self, username: str, password: str) -> Optional[str]:
        """
        Verify admin credentials and return token

        Args:
            username: Admin username
            password: Admin password

        Returns:
            JWT token if valid, None otherwise
        """
        ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
        ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return self.create_admin_token(username)
        return None

    def generate_qr_login(self) -> Dict[str, Any]:
        """
        Generate QR code for admin login

        Returns:
            Dictionary with QR code data and session info
        """
        import uuid

        session_id = str(uuid.uuid4())
        server_url = os.getenv("SERVER_URL", "https://eazr.ai.eazr.in")
        scan_url = f"{server_url}/qr-scan.html?session={session_id}"

        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(scan_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        logger.info(f"Generated QR code for session: {session_id}")

        return {
            "session_id": session_id,
            "qr_code": f"data:image/png;base64,{img_str}",
            "expires_in": 300
        }

    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all users with pagination and filtering

        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            status: Filter by status (active/inactive)

        Returns:
            Dictionary with users and pagination info

        Raises:
            ValueError: If MongoDB unavailable
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB not available")

        # Get users from MongoDB
        all_users = list(self.mongodb_manager.users_collection.find(
            {},
            {"_id": 0}
        ).sort("created_at", -1))

        # Filter by status
        filtered_users = []
        if status:
            current_time = datetime.utcnow()
            inactive_threshold = timedelta(days=30)

            for user in all_users:
                prefs = user.get("preferences", {})
                last_login = prefs.get("last_login")

                is_active = True
                if last_login:
                    try:
                        if isinstance(last_login, str):
                            last_login_dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                        else:
                            last_login_dt = last_login
                        is_active = (current_time - last_login_dt) < inactive_threshold
                    except:
                        is_active = True

                if (status == "active" and is_active) or (status == "inactive" and not is_active):
                    filtered_users.append(user)
        else:
            filtered_users = all_users

        # Apply pagination
        total_count = len(filtered_users)
        users = filtered_users[skip:skip + limit]

        # Format user data
        formatted_users = []
        for user in users:
            prefs = user.get("preferences", {})
            formatted_users.append({
                "user_id": user.get("user_id"),
                "user_name": prefs.get("user_name", "Unknown"),
                "phone": prefs.get("phone", "N/A"),
                "registration_date": prefs.get("registration_date", user.get("created_at", "N/A")),
                "last_login": prefs.get("last_login", "N/A"),
                "login_count": prefs.get("login_count", 0),
                "language_preference": user.get("language_preference", "en")
            })

        return {
            "users": formatted_users,
            "total_count": total_count,
            "page": skip // limit + 1,
            "total_pages": (total_count + limit - 1) // limit
        }

    async def get_user_details(self, user_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific user

        Args:
            user_id: User ID

        Returns:
            Dictionary with user details

        Raises:
            ValueError: If user not found
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB not available")

        user = self.mongodb_manager.users_collection.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )

        if not user:
            raise ValueError("User not found")

        # Get user's login statistics
        from database_storage.mongodb_chat_manager import get_user_login_statistics
        login_stats = get_user_login_statistics(user_id)

        # Get user's recent sessions
        recent_sessions = list(self.mongodb_manager.sessions_collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(10))

        # Get user's policy applications
        policy_apps = list(self.mongodb_manager.policy_applications_collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(10))

        return {
            "user": user,
            "login_statistics": login_stats,
            "recent_sessions": recent_sessions,
            "policy_applications": policy_apps
        }

    async def delete_user(self, user_id: int) -> Dict[str, Any]:
        """
        Delete a user and all associated data

        Args:
            user_id: User ID to delete

        Returns:
            Dictionary with deletion statistics

        Raises:
            ValueError: If user not found
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB not available")

        # Check if user exists
        user = self.mongodb_manager.users_collection.find_one({"user_id": user_id})
        if not user:
            raise ValueError("User not found")

        # Delete user data from all collections
        sessions_result = self.mongodb_manager.sessions_collection.delete_many({"user_id": user_id})
        messages_result = self.mongodb_manager.messages_collection.delete_many({"user_id": user_id})
        policy_result = self.mongodb_manager.policy_applications_collection.delete_many({"user_id": user_id})
        activities_result = self.mongodb_manager.activities_collection.delete_many({"user_id": user_id})
        user_result = self.mongodb_manager.users_collection.delete_one({"user_id": user_id})

        logger.info(f"Deleted user {user_id}: {sessions_result.deleted_count} sessions, "
                   f"{messages_result.deleted_count} messages, {policy_result.deleted_count} policies, "
                   f"{activities_result.deleted_count} activities")

        return {
            "sessions": sessions_result.deleted_count,
            "messages": messages_result.deleted_count,
            "policy_applications": policy_result.deleted_count,
            "activities": activities_result.deleted_count
        }

    async def get_system_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive system statistics

        Returns:
            Dictionary with system stats

        Raises:
            ValueError: If MongoDB unavailable
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB not available")

        # Get statistics
        total_users = self.mongodb_manager.users_collection.count_documents({})
        active_users = self.mongodb_manager.users_collection.count_documents(
            {"preferences.status": "active"}
        )

        total_sessions = self.mongodb_manager.sessions_collection.count_documents({})
        active_sessions = self.mongodb_manager.sessions_collection.count_documents(
            {"active": True}
        )

        total_messages = self.mongodb_manager.messages_collection.count_documents({})

        total_policies = self.mongodb_manager.policy_applications_collection.count_documents({})
        pending_policies = self.mongodb_manager.policy_applications_collection.count_documents(
            {"status": "pending"}
        )
        completed_policies = self.mongodb_manager.policy_applications_collection.count_documents(
            {"status": "completed"}
        )

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_logins = self.mongodb_manager.activities_collection.count_documents({
            "activity_type": "login",
            "timestamp": {"$gte": today_start}
        })

        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": total_users - active_users
            },
            "sessions": {
                "total": total_sessions,
                "active": active_sessions,
                "completed": total_sessions - active_sessions
            },
            "messages": {
                "total": total_messages
            },
            "policies": {
                "total": total_policies,
                "pending": pending_policies,
                "completed": completed_policies
            },
            "activities": {
                "today_logins": today_logins
            },
            "timestamp": datetime.now().isoformat()
        }

    async def get_analytics(self) -> Dict[str, Any]:
        """
        Get analytics data for charts and insights

        Returns:
            Dictionary with analytics data
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB not available")

        from datetime import timezone

        ist_timezone = timezone(timedelta(hours=5, minutes=30))
        current_ist = datetime.now(ist_timezone).replace(tzinfo=None)
        seven_days_ago_utc = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
        thirty_days_ago_utc = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)

        # Daily Active Users
        daily_users = defaultdict(set)
        messages_for_users = list(self.mongodb_manager.messages_collection.find({
            "timestamp": {"$gte": seven_days_ago_utc},
            "role": "user"
        }))

        for message in messages_for_users:
            timestamp = message.get("timestamp")
            user_id = message.get("user_id")
            if timestamp and user_id:
                timestamp_ist = timestamp + timedelta(hours=5, minutes=30)
                day = timestamp_ist.strftime("%Y-%m-%d")
                daily_users[day].add(user_id)

        daily_users_count = {day: len(users) for day, users in daily_users.items()}

        daily_active_users = []
        for i in range(7):
            date = (current_ist - timedelta(days=6-i)).strftime("%Y-%m-%d")
            daily_active_users.append({
                "date": date,
                "users": daily_users_count.get(date, 0)
            })

        # Message Volume
        daily_messages = defaultdict(int)
        messages_list = list(self.mongodb_manager.messages_collection.find({
            "timestamp": {"$gte": seven_days_ago_utc}
        }))

        for message in messages_list:
            timestamp = message.get("timestamp")
            if timestamp:
                timestamp_ist = timestamp + timedelta(hours=5, minutes=30)
                day = timestamp_ist.strftime("%Y-%m-%d")
                daily_messages[day] += 1

        message_volume = []
        for i in range(7):
            date = (current_ist - timedelta(days=6-i)).strftime("%Y-%m-%d")
            message_volume.append({
                "date": date,
                "messages": daily_messages.get(date, 0)
            })

        # Registration Trend
        daily_registrations = defaultdict(int)
        users_list = list(self.mongodb_manager.users_collection.find({
            "created_at": {"$gte": thirty_days_ago_utc}
        }))

        for user in users_list:
            created_at = user.get("created_at")
            if created_at:
                timestamp_ist = created_at + timedelta(hours=5, minutes=30)
                day = timestamp_ist.strftime("%Y-%m-%d")
                daily_registrations[day] += 1

        registration_trend = []
        for i in range(30):
            date = (current_ist - timedelta(days=29-i)).strftime("%Y-%m-%d")
            registration_trend.append({
                "date": date,
                "registrations": daily_registrations.get(date, 0)
            })

        return {
            "daily_active_users": daily_active_users,
            "message_volume": message_volume,
            "registration_trend": registration_trend,
            "timestamp": datetime.now().isoformat()
        }


# Create singleton instance
admin_service = AdminService()
