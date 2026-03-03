"""
User Service
Business logic for user profile management, account operations, and preferences
"""
import logging
import httpx
from datetime import datetime, timezone, date, timedelta
from typing import Optional, Dict, Any
from core.dependencies import MONGODB_AVAILABLE

logger = logging.getLogger(__name__)


class UserService:
    """Service for handling user profile operations"""

    def __init__(self):
        """Initialize user service"""
        if MONGODB_AVAILABLE:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            self.mongodb_manager = mongodb_chat_manager
        else:
            self.mongodb_manager = None
            logger.warning("MongoDB not available for UserService")

    @staticmethod
    def calculate_age(dob: str) -> Optional[int]:
        """
        Calculate age from date of birth (YYYY-MM-DD format)

        Args:
            dob: Date of birth string in YYYY-MM-DD format

        Returns:
            Age in years or None if invalid
        """
        try:
            birth_date = datetime.strptime(dob, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        except Exception as e:
            logger.warning(f"Error calculating age from DOB {dob}: {e}")
            return None

    def calculate_profile_completion(self, profile: Dict[str, Any]) -> int:
        """
        Calculate profile completion score (0-100%)

        Args:
            profile: User profile dictionary with preferences

        Returns:
            Profile completion score as integer percentage
        """
        try:
            preferences = profile.get('preferences', {})
            completion_fields = {
                'phone': preferences.get('phone'),
                'user_name': preferences.get('user_name'),
                'full_name': preferences.get('full_name'),
                'profile_pic': preferences.get('profile_pic'),
                'gender': preferences.get('gender'),
                'dob': preferences.get('dob'),
                'age': preferences.get('age')
            }

            completed_fields = sum(1 for value in completion_fields.values() if value)
            profile_completion_score = (completed_fields / len(completion_fields)) * 100

            return round(profile_completion_score, 1)
        except Exception as e:
            logger.error(f"Error calculating profile completion: {e}")
            return 0

    async def get_user_profile(
        self,
        user_id: int,
        session_id: str,
        access_token: Optional[str] = None,
        eazr_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user profile with MongoDB and eazr.in API data

        Args:
            user_id: User ID
            session_id: Current session ID
            access_token: Optional eazr.in access token
            eazr_user_id: Optional eazr.in user ID

        Returns:
            Dictionary with user profile data

        Raises:
            ValueError: If user not found or MongoDB unavailable
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        # Get user profile from MongoDB
        profile_data = self.mongodb_manager.users_collection.find_one({"user_id": user_id})

        if not profile_data:
            raise ValueError(f"User profile not found for user_id {user_id}")

        # Get eazr_user_id from profile if not provided
        # In eazr.in API, the user_id IS the eazr_user_id (they use same ID)
        if not eazr_user_id:
            eazr_user_id = profile_data.get('eazr_user_id')

        # If still not found, use user_id as eazr_user_id (they're the same in eazr system)
        if not eazr_user_id:
            eazr_user_id = str(user_id)
            logger.info(f"Using user_id ({user_id}) as eazr_user_id")

        # Calculate profile completion score
        preferences = profile_data.get('preferences', {})
        profile_completion_score = self.calculate_profile_completion(profile_data)

        # Calculate age from DOB if available and age not stored
        calculated_age = None
        dob = preferences.get('dob')
        stored_age = preferences.get('age')

        if dob and not stored_age:
            calculated_age = self.calculate_age(dob)

        # Build profile info
        profile_info = {
            'user_id': str(user_id),
            'phone': preferences.get('phone'),
            'user_name': preferences.get('user_name'),
            'full_name': preferences.get('full_name'),
            'profile_pic': preferences.get('profile_pic'),
            'gender': preferences.get('gender'),
            'dob': preferences.get('dob'),
            'age': stored_age or calculated_age,
            'app_platform': preferences.get('app_platform'),
            'android_version': preferences.get('android_version'),
            'ios_version': preferences.get('ios_version'),
            'registration_date': preferences.get('registration_date'),
            'last_login': preferences.get('last_login'),
            'login_count': preferences.get('login_count', 0),
            'profile_completion_score': profile_completion_score,
            'language_preference': profile_data.get('language_preference', 'en'),
            'interests': profile_data.get('interests', []),
            'current_session': session_id,
            'session_history_count': len(profile_data.get('session_history', []))
        }

        # Prepare response
        response_data = {
            "profile": profile_info,
            "eazr_profile": None,
            "eazr_error": None
        }

        # Fetch eazr.in API data if available
        logger.info(f"Checking eazr.in API conditions - eazr_user_id: {eazr_user_id}, access_token: {'present' if access_token else 'missing'}")

        # Try to fetch from eazr.in API
        # According to original code, access_token may not be required for eazr.in API
        # It can work without Authorization header
        if eazr_user_id:
            try:
                logger.info(f"Attempting to fetch eazr profile for eazr_user_id: {eazr_user_id}")
                eazr_data = await self._fetch_eazr_profile(eazr_user_id, access_token)
                response_data["eazr_profile"] = eazr_data
                logger.info(f"✓ Successfully fetched eazr profile data")
            except Exception as e:
                logger.error(f"✗ Error fetching eazr profile for {eazr_user_id}: {type(e).__name__} - {str(e)}")
                response_data["eazr_error"] = f"{type(e).__name__}: {str(e)}"
                # Don't fail the whole request, just set eazr_profile to null
                response_data["eazr_profile"] = None
        else:
            logger.warning(f"Cannot fetch eazr profile: No eazr_user_id available for user_id {user_id}")
            response_data["eazr_error"] = "No eazr user ID available"

        return response_data

    async def _fetch_eazr_profile(self, eazr_user_id: str, access_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch user profile from eazr.in API using async httpx

        Args:
            eazr_user_id: Eazr.in user ID (can be same as our user_id)
            access_token: Optional API access token

        Returns:
            Eazr.in profile data

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"https://api.prod.eazr.in/users/{eazr_user_id}"

        # Build headers - Authorization is optional
        headers = {
            "Content-Type": "application/json"
        }

        # Add Authorization header only if access_token is provided
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
            logger.debug(f"Using Authorization header with token")
        else:
            logger.debug(f"No access_token provided, calling API without Authorization header")

        logger.info(f"Making async request to: {url}")

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, verify=False) as client:
                response = await client.get(url, headers=headers)

                logger.info(f"Eazr API response status: {response.status_code}")

                # Check if successful
                if response.status_code == 200:
                    eazr_data = response.json()
                    logger.info(f"Successfully fetched eazr profile for user {eazr_user_id} - Data keys: {list(eazr_data.keys()) if isinstance(eazr_data, dict) else 'non-dict response'}")
                    return eazr_data
                elif response.status_code == 404:
                    logger.warning(f"User {eazr_user_id} not found in eazr.in system (404)")
                    raise ValueError(f"User not found in eazr.in system")
                elif response.status_code == 401:
                    logger.warning(f"Unauthorized access to eazr.in API (401) - may need valid access_token")
                    raise ValueError(f"Unauthorized - access token may be invalid or required")
                else:
                    logger.error(f"Unexpected status code from eazr API: {response.status_code} - {response.text[:200]}")
                    response.raise_for_status()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from eazr API: {e.response.status_code} - {e.response.text[:200]}")
            raise
        except httpx.ConnectError as e:
            logger.error(f"Connection error to eazr API: {str(e)}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to eazr API (10s): {str(e)}")
            raise
        except ValueError:
            # Re-raise ValueError for 404/401
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling eazr API: {type(e).__name__} - {str(e)}")
            raise

    async def update_user_profile(
        self,
        user_id: int,
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user profile information

        Args:
            user_id: User ID
            profile_data: Dictionary with profile updates

        Returns:
            Success result dictionary

        Raises:
            ValueError: If MongoDB unavailable or update fails
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        from database_storage.mongodb_chat_manager import update_user_profile_in_mongodb

        result = update_user_profile_in_mongodb(user_id, profile_data)

        if not result.get('success'):
            raise ValueError(result.get('error', 'Profile update failed'))

        return result

    async def update_profile_with_picture(
        self,
        user_id: int,
        update_data: Dict[str, Any],
        profile_picture = None
    ) -> Dict[str, Any]:
        """
        Update user profile with optional picture upload

        Args:
            user_id: User ID
            update_data: Dictionary with profile field updates
            profile_picture: Optional UploadFile for profile picture

        Returns:
            Success result with updated fields

        Raises:
            ValueError: If MongoDB unavailable or no data provided
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        # Handle profile picture upload
        if profile_picture and profile_picture.filename:
            try:
                from database_storage.s3_bucket import upload_image_to_s3
                picture_url = upload_image_to_s3(profile_picture, user_id)
                update_data['preferences.profile_pic'] = picture_url
                logger.info(f"Profile picture uploaded for user {user_id}: {picture_url}")
            except Exception as upload_error:
                logger.error(f"Failed to upload profile picture: {upload_error}")
                # Continue with other updates even if picture upload fails

        # Update timestamp
        update_data['updated_at'] = datetime.now(timezone.utc)

        if not update_data:
            raise ValueError("No update data provided")

        # Update in MongoDB
        result = self.mongodb_manager.users_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )

        return {
            "success": result.modified_count > 0,
            "modified_count": result.modified_count,
            "updated_fields": list(update_data.keys())
        }

    async def update_profile_with_picture_enhanced(
        self,
        user_id: int,
        session_id: str,
        full_name: Optional[str] = None,
        gender: Optional[str] = None,
        dob: Optional[str] = None,
        age: Optional[str] = None,
        language_preference: Optional[str] = None,
        interests: Optional[str] = None,
        profile_picture = None,
        current_timestamp: str = None
    ) -> Dict[str, Any]:
        """
        Enhanced profile update with S3 upload, validations, and auto-calculations

        Args:
            user_id: User ID
            session_id: Current session ID
            full_name: Optional full name
            gender: Optional gender (will be normalized)
            dob: Optional DOB (supports multiple formats)
            age: Optional age string (will be converted to int)
            language_preference: Optional language
            interests: Optional comma-separated interests
            profile_picture: Optional UploadFile
            current_timestamp: ISO timestamp

        Returns:
            Dictionary with success, message, updated_fields, and profile

        Raises:
            ValueError: If validation fails or MongoDB unavailable
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        # Check if profile exists, create if not
        current_profile = self.mongodb_manager.users_collection.find_one({"user_id": user_id})

        if not current_profile:
            logger.info(f"Creating new profile for user {user_id}")
            current_profile = {
                "user_id": user_id,
                "last_session_id": session_id,
                "session_history": [session_id],
                "preferences": {
                    "registration_date": current_timestamp,
                    "last_login": current_timestamp,
                    "profile_completion_score": 0
                },
                "interests": [],
                "language_preference": "en",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            self.mongodb_manager.users_collection.insert_one(current_profile)

        # Prepare update operations
        set_operations = {}
        updated_fields = []

        # Process full_name
        if full_name is not None:
            set_operations["preferences.full_name"] = full_name
            updated_fields.append("full_name")

        # Process and validate gender
        if gender is not None:
            try:
                normalized_gender = self.validate_gender(gender)
                set_operations["preferences.gender"] = normalized_gender
                updated_fields.append("gender")
            except ValueError as e:
                raise ValueError(f"Gender validation error: {str(e)}")

        # Process age (convert string to int)
        if age is not None:
            try:
                age_int = int(age)
                if 0 <= age_int <= 120:
                    set_operations["preferences.age"] = age_int
                    updated_fields.append("age")
                else:
                    raise ValueError("Age must be between 0 and 120")
            except ValueError as e:
                if "Age must be" in str(e):
                    raise
                raise ValueError("Age must be a valid number")

        # Process DOB with multiple format support
        if dob is not None:
            try:
                validated_dob = self._parse_and_validate_dob(dob)
                set_operations["preferences.dob"] = validated_dob
                updated_fields.append("dob")

                # Auto-calculate age from DOB
                calculated_age = self.calculate_age(validated_dob)
                if calculated_age is not None:
                    set_operations["preferences.age"] = calculated_age
                    if "age" not in updated_fields:
                        updated_fields.append("age (auto-calculated)")

            except ValueError as e:
                raise ValueError(f"DOB validation error: {str(e)}")

        # Process language preference
        if language_preference is not None:
            set_operations["language_preference"] = language_preference
            updated_fields.append("language_preference")

        # Process interests (comma-separated string to list)
        if interests is not None:
            interests_list = [i.strip() for i in interests.split(',') if i.strip()]
            set_operations["interests"] = interests_list
            updated_fields.append("interests")

        # Process profile picture with S3 upload
        if profile_picture is not None and profile_picture.filename:
            try:
                # Validate file type
                if not profile_picture.content_type or not profile_picture.content_type.startswith('image/'):
                    raise ValueError("Profile picture must be an image file")

                # Check file size (5MB max)
                file_content = await profile_picture.read()
                max_size = 5 * 1024 * 1024  # 5MB

                if len(file_content) > max_size:
                    raise ValueError("Profile picture must be less than 5MB")

                # Reset file position for upload
                await profile_picture.seek(0)

                # Upload to S3
                s3_result = await self._upload_profile_picture_to_s3(profile_picture, user_id)

                if s3_result["success"]:
                    set_operations["preferences.profile_pic"] = s3_result["s3_url"]
                    set_operations["preferences.profile_pic_s3_key"] = f"eaza_images/{s3_result['filename']}"
                    updated_fields.append("profile_pic")
                    logger.info(f"Profile picture uploaded to S3: {s3_result['s3_url']}")
                else:
                    raise ValueError(f"Failed to upload profile picture: {s3_result.get('error')}")

            except ValueError:
                raise
            except Exception as e:
                logger.error(f"Error processing profile picture: {e}")
                raise ValueError(f"Profile picture upload error: {str(e)}")

        # If no fields to update
        if not set_operations:
            preferences = current_profile.get('preferences', {})
            profile_info = self._build_profile_info(user_id, preferences, current_profile)
            return {
                "success": True,
                "message": "No fields provided to update",
                "updated_fields": [],
                "profile": profile_info
            }

        # Calculate profile completion score
        current_preferences = current_profile.get('preferences', {}).copy()

        # Apply updates to calculate new score
        for key, value in set_operations.items():
            if key.startswith("preferences."):
                field_name = key.replace("preferences.", "")
                current_preferences[field_name] = value
            elif key in ["language_preference", "interests"]:
                # These are top-level fields, not in preferences
                pass

        completion_fields = ['phone', 'user_name', 'full_name', 'profile_pic', 'gender', 'dob', 'age']
        completed_count = sum(
            1 for field in completion_fields
            if current_preferences.get(field) is not None and current_preferences.get(field) != ""
        )
        new_completion_score = (completed_count / len(completion_fields)) * 100

        # Add metadata
        set_operations["preferences.profile_completion_score"] = round(new_completion_score, 1)
        set_operations["preferences.profile_updated_at"] = current_timestamp
        set_operations["updated_at"] = datetime.now(timezone.utc)
        set_operations["last_session_id"] = session_id

        # Perform the update
        result = self.mongodb_manager.users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": set_operations,
                "$addToSet": {"session_history": session_id}
            }
        )

        if result.matched_count == 0:
            raise ValueError("User profile not found")

        # Get updated profile
        updated_profile = self.mongodb_manager.users_collection.find_one({"user_id": user_id})
        preferences = updated_profile.get('preferences', {})

        # Build profile info
        profile_info = self._build_profile_info(user_id, preferences, updated_profile)

        return {
            "success": True,
            "message": f"Successfully updated {len(updated_fields)} field(s)",
            "updated_fields": updated_fields,
            "profile": profile_info
        }

    def _parse_and_validate_dob(self, dob_str: str) -> str:
        """
        Parse DOB from multiple formats and validate

        Supports: YYYY-MM-DD, DD-Mon-YYYY, DD/MM/YYYY, MM/DD/YYYY, etc.

        Args:
            dob_str: DOB string in various formats

        Returns:
            DOB in YYYY-MM-DD format

        Raises:
            ValueError: If format invalid or date invalid
        """
        date_formats = [
            "%Y-%m-%d",      # 2024-10-24
            "%d-%b-%Y",      # 24-Oct-2024
            "%d-%B-%Y",      # 24-October-2024
            "%d/%m/%Y",      # 24/10/2024
            "%m/%d/%Y",      # 10/24/2024
            "%Y/%m/%d",      # 2024/10/24
            "%d-%m-%Y",      # 24-10-2024
        ]

        dob_date = None
        for fmt in date_formats:
            try:
                dob_date = datetime.strptime(dob_str, fmt).date()
                break
            except ValueError:
                continue

        # Try with case normalization for month abbreviations
        if dob_date is None:
            dob_formatted = dob_str.replace('oct', 'Oct').replace('OCT', 'Oct')
            dob_formatted = dob_formatted.replace('jan', 'Jan').replace('JAN', 'Jan')
            dob_formatted = dob_formatted.replace('feb', 'Feb').replace('FEB', 'Feb')
            # Add more months as needed
            try:
                dob_date = datetime.strptime(dob_formatted, "%d-%b-%Y").date()
            except ValueError:
                pass

        if dob_date is None:
            raise ValueError("Invalid date format. Use formats like: YYYY-MM-DD, DD-Mon-YYYY, DD/MM/YYYY")

        # Validate date
        today = date.today()
        if dob_date > today:
            raise ValueError("Date of birth cannot be in the future")

        min_date = today.replace(year=today.year - 120)
        if dob_date < min_date:
            raise ValueError("Date of birth is too old")

        # Return in standard format
        return dob_date.strftime("%Y-%m-%d")

    async def _upload_profile_picture_to_s3(self, file, user_id: int) -> Dict[str, Any]:
        """
        Upload profile picture to S3

        Args:
            file: UploadFile object
            user_id: User ID

        Returns:
            Dictionary with success status and S3 URL

        Raises:
            Exception: If upload fails
        """
        try:
            from io import BytesIO
            from database_storage.s3_bucket import upload_image_to_s3
            import asyncio
            from functools import partial

            # Read file content
            file_content = await file.read()

            # Create filename with user_id
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"profile_pic_user_{user_id}_{timestamp}.{file_extension}"

            # Create BytesIO buffer
            image_buffer = BytesIO(file_content)

            # Upload to S3 in thread executor (since upload_image_to_s3 is synchronous)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                partial(upload_image_to_s3, image_buffer, filename)
            )

            return result

        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to upload image: {str(e)}"
            }

    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user preferences

        Args:
            user_id: User ID

        Returns:
            User preferences dictionary

        Raises:
            ValueError: If MongoDB unavailable or user not found
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        user = self.mongodb_manager.users_collection.find_one(
            {"user_id": user_id},
            {"preferences": 1, "language_preference": 1, "interests": 1}
        )

        if not user:
            raise ValueError(f"User {user_id} not found")

        return {
            "preferences": user.get("preferences", {}),
            "language_preference": user.get("language_preference", "en"),
            "interests": user.get("interests", [])
        }

    async def delete_user_account(
        self,
        user_id: int,
        session_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete user account and ALL associated data with backup

        Args:
            user_id: User ID to delete
            session_id: Current session ID
            reason: Optional deletion reason

        Returns:
            Success result with deletion summary and backup ID

        Raises:
            ValueError: If MongoDB unavailable or user not found
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        db = self.mongodb_manager.db
        deletion_summary = {
            "user_id": user_id,
            "deleted_data": {},
            "backed_up_data": {}
        }

        # Generate backup ID for this deletion
        backup_id = f"backup_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"
        backup_timestamp = datetime.now(timezone.utc)

        # Ensure deleted_user_backups collection exists
        backup_collection = db['deleted_user_backups']

        # ============= BACKUP ALL DATA FIRST =============
        logger.info(f"Starting backup for user {user_id} with backup_id: {backup_id}")

        backup_document = {
            "backup_id": backup_id,
            "user_id": user_id,
            "deletion_reason": reason,
            "deleted_at": backup_timestamp,
            "retention_until": backup_timestamp + timedelta(days=90),  # 90 days retention
            "data": {}
        }

        # 1. Backup user profile
        try:
            user_profile = self.mongodb_manager.users_collection.find_one({"user_id": user_id})
            if not user_profile:
                user_profile = self.mongodb_manager.users_collection.find_one({"user_id": str(user_id)})
            if user_profile:
                user_profile.pop('_id', None)  # Remove MongoDB internal ID
                backup_document["data"]["user_profile"] = user_profile
                deletion_summary["backed_up_data"]["user_profile"] = 1
        except Exception as e:
            logger.error(f"Error backing up user profile for user {user_id}: {e}")

        # 2. Backup policy analysis
        try:
            policy_analysis = list(db['policy_analysis'].find({"$or": [{"user_id": user_id}, {"user_id": str(user_id)}]}))
            for doc in policy_analysis:
                doc.pop('_id', None)
            if policy_analysis:
                backup_document["data"]["policy_analysis"] = policy_analysis
                deletion_summary["backed_up_data"]["policy_analysis"] = len(policy_analysis)
        except Exception as e:
            logger.error(f"Error backing up policy_analysis for user {user_id}: {e}")

        # 3. Backup policy uploads
        try:
            policy_uploads = list(db['policy_uploads'].find({"$or": [{"user_id": user_id}, {"user_id": str(user_id)}]}))
            for doc in policy_uploads:
                doc.pop('_id', None)
            if policy_uploads:
                backup_document["data"]["policy_uploads"] = policy_uploads
                deletion_summary["backed_up_data"]["policy_uploads"] = len(policy_uploads)
        except Exception as e:
            logger.error(f"Error backing up policy_uploads for user {user_id}: {e}")

        # 4. Backup insurance reports
        try:
            insurance_reports = list(db['insurance_reports'].find({"$or": [{"user_id": user_id}, {"user_id": str(user_id)}]}))
            for doc in insurance_reports:
                doc.pop('_id', None)
            if insurance_reports:
                backup_document["data"]["insurance_reports"] = insurance_reports
                deletion_summary["backed_up_data"]["insurance_reports"] = len(insurance_reports)
        except Exception as e:
            logger.error(f"Error backing up insurance_reports for user {user_id}: {e}")

        # 5. Backup chat messages
        try:
            chat_messages = list(self.mongodb_manager.messages_collection.find({"$or": [{"user_id": user_id}, {"user_id": str(user_id)}]}))
            for doc in chat_messages:
                doc.pop('_id', None)
            if chat_messages:
                backup_document["data"]["chat_messages"] = chat_messages
                deletion_summary["backed_up_data"]["chat_messages"] = len(chat_messages)
        except Exception as e:
            logger.error(f"Error backing up chat messages for user {user_id}: {e}")

        # 6. Backup conversation summaries
        try:
            summaries = list(self.mongodb_manager.summaries_collection.find({"$or": [{"user_id": user_id}, {"user_id": str(user_id)}]}))
            for doc in summaries:
                doc.pop('_id', None)
            if summaries:
                backup_document["data"]["conversation_summaries"] = summaries
                deletion_summary["backed_up_data"]["conversation_summaries"] = len(summaries)
        except Exception as e:
            logger.error(f"Error backing up conversation summaries for user {user_id}: {e}")

        # 7. Backup sessions
        try:
            sessions = list(self.mongodb_manager.sessions_collection.find({"$or": [{"user_id": user_id}, {"user_id": str(user_id)}]}))
            for doc in sessions:
                doc.pop('_id', None)
            if sessions:
                backup_document["data"]["sessions"] = sessions
                deletion_summary["backed_up_data"]["sessions"] = len(sessions)
        except Exception as e:
            logger.error(f"Error backing up sessions for user {user_id}: {e}")

        # 8. Backup user activities
        try:
            activities = list(self.mongodb_manager.activities_collection.find({"$or": [{"user_id": user_id}, {"user_id": str(user_id)}]}))
            for doc in activities:
                doc.pop('_id', None)
            if activities:
                backup_document["data"]["user_activities"] = activities
                deletion_summary["backed_up_data"]["user_activities"] = len(activities)
        except Exception as e:
            logger.error(f"Error backing up user activities for user {user_id}: {e}")

        # Save the backup document
        try:
            backup_collection.insert_one(backup_document)
            logger.info(f"Backup saved successfully with ID: {backup_id}")
        except Exception as e:
            logger.error(f"Error saving backup document for user {user_id}: {e}")
            raise ValueError(f"Failed to create backup: {str(e)}")

        # ============= NOW DELETE ALL DATA =============
        logger.info(f"Starting deletion for user {user_id}")

        # 1. Delete policy analysis data
        try:
            policy_analysis_result = db['policy_analysis'].delete_many({"user_id": user_id})
            policy_analysis_result_str = db['policy_analysis'].delete_many({"user_id": str(user_id)})
            total_policy_deleted = policy_analysis_result.deleted_count + policy_analysis_result_str.deleted_count
            deletion_summary["deleted_data"]["policy_analysis"] = total_policy_deleted
            logger.info(f"Deleted {total_policy_deleted} policy analysis records for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting policy_analysis for user {user_id}: {e}")

        # 2. Delete policy uploads
        try:
            policy_uploads_result = db['policy_uploads'].delete_many({"user_id": user_id})
            policy_uploads_result_str = db['policy_uploads'].delete_many({"user_id": str(user_id)})
            total_uploads_deleted = policy_uploads_result.deleted_count + policy_uploads_result_str.deleted_count
            deletion_summary["deleted_data"]["policy_uploads"] = total_uploads_deleted
            logger.info(f"Deleted {total_uploads_deleted} policy uploads for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting policy_uploads for user {user_id}: {e}")

        # 3. Delete insurance reports
        try:
            insurance_reports_result = db['insurance_reports'].delete_many({"user_id": user_id})
            insurance_reports_result_str = db['insurance_reports'].delete_many({"user_id": str(user_id)})
            total_reports_deleted = insurance_reports_result.deleted_count + insurance_reports_result_str.deleted_count
            deletion_summary["deleted_data"]["insurance_reports"] = total_reports_deleted
            logger.info(f"Deleted {total_reports_deleted} insurance reports for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting insurance_reports for user {user_id}: {e}")

        # 4. Delete chat messages
        try:
            messages_result = self.mongodb_manager.messages_collection.delete_many({"user_id": user_id})
            messages_result_str = self.mongodb_manager.messages_collection.delete_many({"user_id": str(user_id)})
            total_messages_deleted = messages_result.deleted_count + messages_result_str.deleted_count
            deletion_summary["deleted_data"]["chat_messages"] = total_messages_deleted
            logger.info(f"Deleted {total_messages_deleted} chat messages for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting chat messages for user {user_id}: {e}")

        # 5. Delete conversation summaries
        try:
            summaries_result = self.mongodb_manager.summaries_collection.delete_many({"user_id": user_id})
            summaries_result_str = self.mongodb_manager.summaries_collection.delete_many({"user_id": str(user_id)})
            total_summaries_deleted = summaries_result.deleted_count + summaries_result_str.deleted_count
            deletion_summary["deleted_data"]["conversation_summaries"] = total_summaries_deleted
            logger.info(f"Deleted {total_summaries_deleted} conversation summaries for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting conversation summaries for user {user_id}: {e}")

        # 6. Delete claim guidance messages
        try:
            claim_result = self.mongodb_manager.claim_guidance_collection.delete_many({"user_id": user_id})
            claim_result_str = self.mongodb_manager.claim_guidance_collection.delete_many({"user_id": str(user_id)})
            total_claims_deleted = claim_result.deleted_count + claim_result_str.deleted_count
            deletion_summary["deleted_data"]["claim_guidance"] = total_claims_deleted
            logger.info(f"Deleted {total_claims_deleted} claim guidance records for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting claim guidance for user {user_id}: {e}")

        # 7. Delete policy applications
        try:
            applications_result = self.mongodb_manager.policy_applications_collection.delete_many({"user_id": user_id})
            applications_result_str = self.mongodb_manager.policy_applications_collection.delete_many({"user_id": str(user_id)})
            total_apps_deleted = applications_result.deleted_count + applications_result_str.deleted_count
            deletion_summary["deleted_data"]["policy_applications"] = total_apps_deleted
            logger.info(f"Deleted {total_apps_deleted} policy applications for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting policy applications for user {user_id}: {e}")

        # 8. Delete user activities
        try:
            activities_result = self.mongodb_manager.activities_collection.delete_many({"user_id": user_id})
            activities_result_str = self.mongodb_manager.activities_collection.delete_many({"user_id": str(user_id)})
            total_activities_deleted = activities_result.deleted_count + activities_result_str.deleted_count
            deletion_summary["deleted_data"]["user_activities"] = total_activities_deleted
            logger.info(f"Deleted {total_activities_deleted} user activities for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting user activities for user {user_id}: {e}")

        # 9. Delete all sessions (both user and chat sessions)
        try:
            sessions_result = self.mongodb_manager.sessions_collection.delete_many({"user_id": user_id})
            sessions_result_str = self.mongodb_manager.sessions_collection.delete_many({"user_id": str(user_id)})
            total_sessions_deleted = sessions_result.deleted_count + sessions_result_str.deleted_count
            deletion_summary["deleted_data"]["sessions"] = total_sessions_deleted
            logger.info(f"Deleted {total_sessions_deleted} sessions for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting sessions for user {user_id}: {e}")

        # 10. Finally, delete the user profile
        deletion_result = self.mongodb_manager.users_collection.delete_one({"user_id": user_id})
        if deletion_result.deleted_count == 0:
            deletion_result = self.mongodb_manager.users_collection.delete_one({"user_id": str(user_id)})

        if deletion_result.deleted_count == 0:
            raise ValueError("User not found or already deleted")

        deletion_summary["deleted_data"]["user_profile"] = 1

        logger.info(f"User account completely deleted: {user_id}, reason: {reason}, backup_id: {backup_id}")

        return {
            "user_id": user_id,
            "status": "permanently_deleted",
            "backup_id": backup_id,
            "backup_retention": "90 days",
            "deleted_data": deletion_summary["deleted_data"],
            "backed_up_data": deletion_summary["backed_up_data"],
            "note": "All user data has been deleted. Backup available for 90 days for recovery."
        }

    @staticmethod
    def validate_gender(gender: str) -> str:
        """
        Validate and normalize gender value

        Args:
            gender: Gender string (case-insensitive)

        Returns:
            Normalized gender value

        Raises:
            ValueError: If gender is invalid
        """
        valid_genders = ['Male', 'Female', 'Other', 'Prefer not to say']
        gender_mapping = {
            'male': 'Male',
            'female': 'Female',
            'm': 'Male',
            'f': 'Female',
            'other': 'Other',
            'prefer not to say': 'Prefer not to say'
        }

        gender_lower = gender.lower()

        if gender_lower in gender_mapping:
            return gender_mapping[gender_lower]
        elif gender in valid_genders:
            return gender
        else:
            raise ValueError(f"Invalid gender. Must be one of: {', '.join(valid_genders)}")

    @staticmethod
    def validate_dob(dob_str: str) -> str:
        """
        Validate date of birth

        Args:
            dob_str: DOB string in YYYY-MM-DD format

        Returns:
            Validated DOB in YYYY-MM-DD format

        Raises:
            ValueError: If DOB is invalid or in future
        """
        from datetime import date

        try:
            dob_date = datetime.strptime(dob_str, "%Y-%m-%d").date()

            # Check not in future
            if dob_date > date.today():
                raise ValueError("Date of birth cannot be in the future")

            # Check not too old (120 years)
            min_date = date.today().replace(year=date.today().year - 120)
            if dob_date < min_date:
                raise ValueError("Date of birth is too old")

            return dob_str

        except ValueError as e:
            if "Date of birth" in str(e):
                raise
            raise ValueError("Invalid date format for DOB. Use YYYY-MM-DD format")

    @staticmethod
    def validate_profile_pic(profile_pic: str) -> bool:
        """
        Validate profile picture URL or base64 data

        Args:
            profile_pic: URL or base64 encoded image

        Returns:
            True if valid

        Raises:
            ValueError: If invalid format
        """
        if not profile_pic or not profile_pic.strip():
            return True  # Empty is valid (clears the field)

        is_url = profile_pic.startswith(('http://', 'https://'))
        is_base64 = profile_pic.startswith('data:image/')

        if not (is_url or is_base64):
            raise ValueError("Profile picture must be a valid URL or base64 encoded image")

        return True

    async def update_user_profile_patch(
        self,
        user_id: int,
        update_request,
        session_id: str,
        current_timestamp: str
    ) -> Dict[str, Any]:
        """
        Update user profile using PATCH method (allows null values and partial updates)

        Args:
            user_id: User ID
            update_request: UserProfileUpdateRequest object
            session_id: Current session ID
            current_timestamp: ISO timestamp

        Returns:
            Dictionary with update result

        Raises:
            ValueError: If validation fails or MongoDB unavailable
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        # Check if profile exists
        current_profile = self.mongodb_manager.users_collection.find_one({"user_id": user_id})

        # Create profile if doesn't exist
        if not current_profile:
            logger.info(f"Profile not found for user {user_id}, creating new profile")

            initial_profile = {
                "user_id": user_id,
                "last_session_id": session_id,
                "session_history": [session_id],
                "preferences": {
                    "registration_date": current_timestamp,
                    "last_login": current_timestamp,
                    "profile_completion_score": 0
                },
                "interests": [],
                "language_preference": "en",
                "interaction_patterns": {},
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            self.mongodb_manager.users_collection.insert_one(initial_profile)
            current_profile = initial_profile

        # Get request data (exclude_unset = only include fields that were explicitly set)
        request_data = update_request.dict(exclude_unset=True)

        # If no fields provided, return current profile
        if not request_data:
            preferences = current_profile.get('preferences', {})
            profile_info = self._build_profile_info(user_id, preferences, current_profile)

            return {
                "success": True,
                "message": "No updates provided - returning current profile",
                "updated_fields": [],
                "profile": profile_info
            }

        # Validate and process fields
        updated_fields = []

        # Validate gender if provided
        if 'gender' in request_data and request_data['gender'] is not None:
            try:
                request_data['gender'] = self.validate_gender(request_data['gender'])
            except ValueError as e:
                raise ValueError(str(e))

        # Validate profile_pic if provided
        if 'profile_pic' in request_data and request_data['profile_pic'] is not None:
            try:
                self.validate_profile_pic(request_data['profile_pic'])
            except ValueError as e:
                raise ValueError(str(e))

        # Validate DOB if provided
        if 'dob' in request_data and request_data['dob'] is not None and request_data['dob']:
            try:
                request_data['dob'] = self.validate_dob(request_data['dob'])
            except ValueError as e:
                raise ValueError(str(e))

        # Validate age if provided
        if 'age' in request_data and request_data['age'] is not None:
            age = request_data['age']
            if not isinstance(age, int) or age < 0 or age > 120:
                raise ValueError("Age must be a valid integer between 0 and 120")

        # Auto-calculate age from DOB if DOB is provided
        if 'dob' in request_data and request_data['dob'] is not None and request_data['dob']:
            calculated_age = self.calculate_age(request_data['dob'])
            if calculated_age is not None:
                request_data['age'] = calculated_age
                if 'age' not in updated_fields:
                    updated_fields.append('age')

        # Build update operations
        set_operations = {}
        for field, value in request_data.items():
            set_operations[f"preferences.{field}"] = value
            if field not in updated_fields:
                updated_fields.append(field)

        # Calculate new profile completion score
        current_preferences = current_profile.get('preferences', {}).copy()
        for field, value in request_data.items():
            if field in ['phone', 'user_name', 'full_name', 'profile_pic', 'gender', 'dob', 'age']:
                current_preferences[field] = value

        completion_fields = ['phone', 'user_name', 'full_name', 'profile_pic', 'gender', 'dob', 'age']
        completed_count = sum(
            1 for field in completion_fields
            if current_preferences.get(field) is not None and current_preferences.get(field) != ""
        )
        new_completion_score = (completed_count / len(completion_fields)) * 100

        # Add metadata
        set_operations["preferences.profile_completion_score"] = round(new_completion_score, 1)
        set_operations["updated_at"] = datetime.now(timezone.utc)
        set_operations["last_session_id"] = session_id
        set_operations["preferences.profile_updated_at"] = current_timestamp

        # Perform update
        result = self.mongodb_manager.users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": set_operations,
                "$addToSet": {"session_history": session_id}
            }
        )

        logger.info(f"Updated profile for user {user_id}: matched={result.matched_count}, modified={result.modified_count}")

        # Get updated profile
        updated_profile = self.mongodb_manager.users_collection.find_one({"user_id": user_id})

        if not updated_profile:
            raise ValueError("Failed to retrieve updated profile")

        # Format response
        preferences = updated_profile.get('preferences', {})
        profile_info = self._build_profile_info(user_id, preferences, updated_profile)

        return {
            "success": True,
            "message": f"Successfully updated {len(updated_fields)} profile field(s)" if updated_fields else "Profile returned without updates",
            "updated_fields": updated_fields,
            "profile": profile_info
        }

    def _build_profile_info(self, user_id: int, preferences: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build profile info dictionary from preferences and profile data

        Args:
            user_id: User ID
            preferences: Preferences dictionary
            profile: Full profile dictionary

        Returns:
            Formatted profile info dictionary
        """
        return {
            'user_id': str(user_id),
            'phone': preferences.get('phone'),
            'user_name': preferences.get('user_name'),
            'full_name': preferences.get('full_name'),
            'profile_pic': preferences.get('profile_pic'),
            'gender': preferences.get('gender'),
            'dob': preferences.get('dob'),
            'age': preferences.get('age'),
            'app_platform': preferences.get('app_platform'),
            'android_version': preferences.get('android_version'),
            'ios_version': preferences.get('ios_version'),
            'registration_date': preferences.get('registration_date'),
            'last_login': preferences.get('last_login'),
            'login_count': preferences.get('login_count', 0),
            'profile_completion_score': preferences.get('profile_completion_score', 0),
            'language_preference': profile.get('language_preference', 'en'),
            'interests': profile.get('interests', []),
            'profile_updated_at': preferences.get('profile_updated_at')
        }

    async def get_profile_completion_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get detailed profile completion status

        Args:
            user_id: User ID

        Returns:
            Dictionary with completion score, missing fields, and suggestions

        Raises:
            ValueError: If MongoDB unavailable or user not found
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        profile_data = self.mongodb_manager.users_collection.find_one({"user_id": user_id})

        if not profile_data:
            raise ValueError(f"User profile not found for user_id {user_id}")

        preferences = profile_data.get('preferences', {})

        # Define completion fields with weights
        fields_status = {
            'phone': {
                'completed': bool(preferences.get('phone')),
                'value': preferences.get('phone'),
                'weight': 15
            },
            'user_name': {
                'completed': bool(preferences.get('user_name')),
                'value': preferences.get('user_name'),
                'weight': 15
            },
            'full_name': {
                'completed': bool(preferences.get('full_name')),
                'value': preferences.get('full_name'),
                'weight': 15
            },
            'profile_pic': {
                'completed': bool(preferences.get('profile_pic')),
                'value': preferences.get('profile_pic'),
                'weight': 15
            },
            'gender': {
                'completed': bool(preferences.get('gender')),
                'value': preferences.get('gender'),
                'weight': 10
            },
            'dob': {
                'completed': bool(preferences.get('dob')),
                'value': preferences.get('dob'),
                'weight': 15
            },
            'age': {
                'completed': bool(preferences.get('age')),
                'value': preferences.get('age'),
                'weight': 15
            }
        }

        # Calculate weighted completion score
        total_weight = sum(field['weight'] for field in fields_status.values())
        completed_weight = sum(field['weight'] for field in fields_status.values() if field['completed'])
        completion_score = (completed_weight / total_weight) * 100

        # Get missing fields
        missing_fields = [
            field_name for field_name, field_data in fields_status.items()
            if not field_data['completed']
        ]

        return {
            "completion_score": round(completion_score, 1),
            "fields_status": fields_status,
            "missing_fields": missing_fields,
            "suggestions": [
                f"Add {field.replace('_', ' ')}" for field in missing_fields
            ]
        }


# Create singleton instance
user_service = UserService()
