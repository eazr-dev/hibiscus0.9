"""
Auth Service - Authentication Business Logic
Extracted from routers/auth.py for better separation of concerns
"""
import logging
import time
import secrets
import requests
from datetime import datetime
from typing import Dict, Tuple, Optional, Any

# Core dependencies
from core.dependencies import (
    get_session,
    store_session,
    MONGODB_AVAILABLE,
    uid_manager
)
from session_security.session_manager import session_manager

logger = logging.getLogger(__name__)


class AuthService:
    """
    Business logic for authentication operations

    Handles:
    - OTP sending via eazr.in API
    - OTP verification
    - Session creation (user + chat sessions)
    - Session validation and regeneration
    - User profile management in MongoDB
    """

    def __init__(self):
        self.logger = logger
        self.eazr_api_base = "https://api.prod.eazr.in"

    async def send_otp_to_phone(self, phone: str) -> Dict[str, Any]:
        """
        Send OTP to phone number via eazr.in API

        Args:
            phone: Phone number (with or without +91 prefix)

        Returns:
            dict: {"success": bool, "message": str}

        Raises:
            ValueError: If phone number is invalid
            TimeoutError: If API times out
            ConnectionError: If API is unavailable
            Exception: For other errors
        """
        self.logger.info(f"Sending OTP to: {phone}")

        if not phone:
            raise ValueError("Phone number is required")

        # Extract number without country code
        number = self._normalize_phone_number(phone)

        # eazr.in API configuration
        url = f"{self.eazr_api_base}/users/send-otp"
        headers = {"Content-Type": "application/json"}
        json_body = {"contactNumber": number}

        try:
            # Send POST request to eazr.in
            response = requests.post(url, headers=headers, json=json_body, timeout=30)

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    # Check for success patterns in response
                    if (response_data.get('success') == True or
                        response_data.get('status') == 'success' or
                        'success' in str(response_data).lower()):
                        self.logger.info(f"OTP sent successfully to {phone}")
                        return {"success": True, "message": "OTP sent successfully"}
                    else:
                        self.logger.error(f"eazr.in response: {response_data}")
                        raise ValueError("Failed to send OTP")
                except ValueError as json_error:
                    # Response is not JSON, check if it's a success string
                    if 'success' in response.text.lower():
                        return {"success": True, "message": "OTP sent successfully"}
                    else:
                        raise ValueError("Invalid response from SMS service")
            else:
                self.logger.error(f"eazr.in API error: {response.status_code} - {response.text}")
                error_detail = "Failed to send OTP"
                try:
                    # Try to extract error message from response
                    error_data = response.json()
                    if 'message' in error_data:
                        error_detail = error_data['message']
                    elif 'error' in error_data:
                        error_detail = error_data['error']
                except:
                    error_detail = f"Failed to send OTP: {response.text[:100]}"

                raise ValueError(error_detail)

        except requests.Timeout:
            self.logger.error(f"Request timeout while sending OTP to {phone}")
            raise TimeoutError("SMS service timeout")
        except requests.RequestException as e:
            self.logger.error(f"Request error while sending OTP: {str(e)}")
            raise ConnectionError("SMS service unavailable")

    async def verify_otp_and_create_sessions(
        self,
        phone: str,
        otp: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        app_version: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Verify OTP and create both user and chat sessions

        Args:
            phone: Phone number
            otp: OTP code
            ip_address: User's IP address (optional)
            user_agent: User's browser/app info (optional)
            app_version: App version info (optional)

        Returns:
            dict: {
                "success": bool,
                "message": str,
                "session_id": str,  # user session
                "chat_session_id": str,
                "user_phone": str,
                "user_name": str,
                "access_token": str,
                "user_id": int,
                "profile_created": bool
            }

        Raises:
            ValueError: If OTP is invalid
            Exception: For other errors
        """
        current_timestamp = datetime.now().isoformat()
        self.logger.info(f"Verifying OTP for phone: {phone}")

        # Verify OTP with eazr.in
        number = self._normalize_phone_number(phone)
        url = f"{self.eazr_api_base}/users/verify-otp"
        headers = {"Content-Type": "application/json"}
        json_body = {"contactNumber": number, "otp": otp}

        try:
            response = requests.post(url, headers=headers, json=json_body, timeout=30)
        except requests.Timeout:
            self.logger.error(f"Request timeout while verifying OTP for {phone}")
            raise TimeoutError("SMS service timeout")
        except requests.RequestException as e:
            self.logger.error(f"Request error while verifying OTP: {str(e)}")
            raise ConnectionError("SMS service unavailable")

        if response.status_code != 200:
            self.logger.error(f"OTP verification failed: {response.status_code}")
            raise ValueError("Invalid OTP")

        response_data = response.json()
        if response_data.get('message') != 'Login Successfully':
            self.logger.error(f"OTP verification failed: {response_data}")
            raise ValueError("Invalid OTP")

        # Extract user data from eazr.in response
        eazr_user_data = response_data.get('data', {})
        access_token = eazr_user_data.get('accessToken')
        eazr_user_id = eazr_user_data.get('id')

        # Get full name from API - try 'fullName' first, then 'name'
        full_name = eazr_user_data.get('fullName') or eazr_user_data.get('name') or ''
        if full_name == 'User':
            full_name = ''  # Reset default 'User' to empty

        if not access_token:
            self.logger.error("No access token in eazr.in response")
            raise Exception("Authentication failed")

        # IMPORTANT: Convert to int and ensure consistency
        try:
            user_id = int(eazr_user_id)
        except (ValueError, TypeError) as e:
            self.logger.error(f"Invalid eazr_user_id format: {eazr_user_id}")
            raise Exception(f"Invalid user ID from authentication service: {str(e)}")

        profile_created = False
        account_reactivated = False
        user_name = None  # Will be generated based on full_name + user_id

        # Check existing user in MongoDB
        if uid_manager and MONGODB_AVAILABLE:
            exists, existing_user_id, user_data = uid_manager.check_existing_user(phone)

            if exists:
                # Use existing user_id (ensure it's int)
                try:
                    user_id = int(existing_user_id)
                except (ValueError, TypeError):
                    self.logger.warning(f"Existing user_id is not int: {existing_user_id}, using eazr_user_id")
                    user_id = int(eazr_user_id)

                if user_data.get('status') == 'deleted':
                    # Reactivate deleted account
                    reactivated = uid_manager.reactivate_user(user_id, phone)
                    if reactivated:
                        account_reactivated = True
                        self.logger.info(f"Reactivated account for user {user_id}")

                # Get stored username and full_name from MongoDB
                stored_user_name = user_data.get('user_name', '')
                stored_full_name = user_data.get('full_name', '')

                # Check if stored_user_name looks like a full name (legacy data issue)
                # A proper username should be lowercase firstname + digits (e.g., hrushikesh282)
                import re
                is_legacy_full_name = (
                    stored_user_name and
                    (' ' in stored_user_name or  # Has space = likely full name
                     not re.search(r'\d+$', stored_user_name) or  # Doesn't end with digits
                     stored_user_name[0].isupper())  # Starts with capital = likely full name
                )

                if is_legacy_full_name:
                    # The stored user_name is actually a full name (legacy data)
                    if not full_name:
                        full_name = stored_user_name
                        self.logger.info(f"Using stored user_name as full_name (legacy fix): {full_name}")
                elif stored_user_name and stored_user_name != 'User' and not stored_user_name.startswith('User_'):
                    # Stored username is in correct format
                    user_name = stored_user_name
                    self.logger.info(f"Using stored username from MongoDB: {user_name}")

                # Use stored full_name if API didn't return one
                if not full_name and stored_full_name:
                    full_name = stored_full_name
            else:
                # New user
                user_id = int(eazr_user_id)
                profile_created = True
                self.logger.info(f"New user detected: {user_id}")

        else:
            # MongoDB not available, use eazr_user_id
            user_id = int(eazr_user_id)

        # Generate username if not already set: firstname + user_id (e.g., hrushikesh282)
        if not user_name:
            user_name = self._generate_username(full_name, user_id, number)
            self.logger.info(f"Generated username: {user_name}")

        # CREATE USER SESSION (authentication) - Store user_id as int
        user_session_id = self._create_user_session_id(user_id, phone)

        user_session_data = {
            'phone': phone,
            'user_name': user_name,
            'full_name': full_name,  # Store full name separately
            'created_at': current_timestamp,
            'last_activity': current_timestamp,
            'access_token': access_token,
            'user_id': user_id,  # Stored as int
            'eazr_user_id': str(eazr_user_id),  # Keep original as string for reference
            'active': True,
            'session_type': 'user_session'
        }

        # Store user session (15 days = 1,296,000 seconds)
        store_session(user_session_id, user_session_data, expire_seconds=1296000)
        self.logger.info(f"Created user session: {user_session_id}")

        # CREATE CHAT SESSION (first conversation) - Store user_id as int
        chat_session_id = self._create_chat_session_id(user_id)

        chat_session_data = {
            'user_id': user_id,  # Stored as int
            'session_type': 'chat_session',
            'created_at': current_timestamp,
            'last_activity': current_timestamp,
            'title': 'New Chat',
            'active': True,
            'message_count': 0,
            'user_session_id': user_session_id  # Link to user session
        }

        # Store chat session (24 hours = 86,400 seconds)
        store_session(chat_session_id, chat_session_data, expire_seconds=86400)
        self.logger.info(f"Created chat session: {chat_session_id}")

        # MongoDB operations
        if MONGODB_AVAILABLE:
            await self._handle_mongodb_operations(
                user_id=user_id,
                user_session_id=user_session_id,
                chat_session_id=chat_session_id,
                phone=phone,
                user_name=user_name,
                full_name=full_name,  # Pass full_name to MongoDB operations
                access_token=access_token,
                eazr_user_id=eazr_user_id,
                profile_created=profile_created,
                account_reactivated=account_reactivated,
                current_timestamp=current_timestamp,
                ip_address=ip_address,
                user_agent=user_agent,
                app_version=app_version
            )

        # Prepare response message
        response_message = "Login successful"
        if account_reactivated:
            response_message = "Welcome back! Your account has been reactivated."
        elif profile_created:
            response_message = "Welcome! Your account has been created successfully."

        self.logger.info(f"Login completed for {phone} - user: {user_id}, user_session: {user_session_id}, chat_session: {chat_session_id}")

        # Return response with consistent int user_id
        return {
            "success": True,
            "message": response_message,
            "session_id": user_session_id,  # USER session (auth)
            "chat_session_id": chat_session_id,  # CHAT session (first conversation)
            "user_phone": number,
            "user_name": user_name,  # e.g., hrushikesh282
            "full_name": full_name,  # e.g., Hrushikesh Tembe
            "access_token": access_token,
            "user_id": user_id,  # Return as int
            "profile_created": profile_created
        }

    async def verify_oauth_and_create_sessions(
        self,
        provider: str,
        id_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        app_version: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Verify OAuth idToken and create sessions

        Args:
            provider: OAuth provider ('google' or 'apple')
            id_token: ID token from OAuth provider
            ip_address: User's IP address (optional)
            user_agent: User's browser/app info (optional)
            app_version: App version info (optional)

        Returns:
            dict: {
                "success": bool,
                "message": str,
                "session_id": str,  # user session
                "chat_session_id": str,
                "user_phone": str,
                "user_name": str,
                "access_token": str,
                "user_id": int,
                "profile_created": bool,
                "email": str,
                "provider": str
            }

        Raises:
            ValueError: If token is invalid or provider not supported
            Exception: For other errors
        """
        current_timestamp = datetime.now().isoformat()
        self.logger.info(f"Verifying OAuth token for provider: {provider}")

        # Validate provider
        if provider.lower() not in ['google', 'apple']:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        # Call eazr.in API to verify idToken
        url = f"{self.eazr_api_base}/users/verify-idtoken"
        headers = {"Content-Type": "application/json"}
        json_body = {
            "provider": provider,
            "idToken": id_token
        }

        try:
            response = requests.post(url, headers=headers, json=json_body, timeout=30)
        except requests.Timeout:
            self.logger.error(f"Request timeout while verifying OAuth token")
            raise TimeoutError("OAuth service timeout")
        except requests.RequestException as e:
            self.logger.error(f"Request error while verifying OAuth token: {str(e)}")
            raise ConnectionError("OAuth service unavailable")

        if response.status_code != 200:
            self.logger.error(f"OAuth verification failed: {response.status_code} - {response.text}")
            try:
                error_data = response.json()
                error_message = error_data.get('message', 'Invalid OAuth token')
            except:
                error_message = "Invalid OAuth token"
            raise ValueError(error_message)

        response_data = response.json()

        # Check if response is wrapped or direct user object
        # If response has 'data' key, extract it; otherwise use response directly
        if 'data' in response_data:
            # Wrapped response format
            if not response_data.get('success') and response_data.get('message') != 'Login Successfully':
                self.logger.error(f"OAuth verification failed: {response_data}")
                raise ValueError(response_data.get('message', 'OAuth authentication failed'))
            eazr_user_data = response_data.get('data', {})
        else:
            # Direct user object format (current backend response)
            eazr_user_data = response_data

        # Extract user data from eazr.in response
        access_token = eazr_user_data.get('accessToken')
        eazr_user_id = eazr_user_data.get('id')
        # Get full_name from API - try 'fullName' first, then 'name'
        full_name = eazr_user_data.get('fullName') or eazr_user_data.get('name') or ''
        if full_name == 'User':
            full_name = ''  # Reset default 'User' to empty
        email = eazr_user_data.get('email', '')
        phone = eazr_user_data.get('contactNumber', '')

        if not access_token:
            self.logger.error("No access token in OAuth response")
            raise Exception("OAuth authentication failed")

        # Convert to int and ensure consistency
        try:
            user_id = int(eazr_user_id)
        except (ValueError, TypeError) as e:
            self.logger.error(f"Invalid user ID format: {eazr_user_id}")
            raise Exception(f"Invalid user ID from OAuth service: {str(e)}")

        profile_created = False
        account_reactivated = False
        user_name = None  # Will be generated based on full_name + user_id

        # IMPORTANT: Keep phone and email as separate fields
        # Do NOT use email as phone fallback - they are different identifiers
        # phone will be None/empty for OAuth users who haven't added their phone number

        # Check existing user in MongoDB
        if uid_manager and MONGODB_AVAILABLE:
            exists, existing_user_id, user_data = uid_manager.check_existing_user(email or phone)

            if exists:
                try:
                    user_id = int(existing_user_id)
                except (ValueError, TypeError):
                    self.logger.warning(f"Existing user_id not int: {existing_user_id}")
                    user_id = int(eazr_user_id)

                if user_data.get('status') == 'deleted':
                    reactivated = uid_manager.reactivate_user(user_id, email or phone)
                    if reactivated:
                        account_reactivated = True
                        self.logger.info(f"Account reactivated for {email}")

                # Get stored username and full_name from MongoDB
                stored_user_name = user_data.get('user_name', '')
                stored_full_name = user_data.get('full_name', '')

                # Check if stored_user_name looks like a full name (legacy data issue)
                # A proper username should be lowercase firstname + digits (e.g., hrushikesh282)
                # A full name typically has spaces or is capitalized without digits at end
                import re
                is_legacy_full_name = (
                    stored_user_name and
                    (' ' in stored_user_name or  # Has space = likely full name
                     not re.search(r'\d+$', stored_user_name) or  # Doesn't end with digits
                     stored_user_name[0].isupper())  # Starts with capital = likely full name
                )

                if is_legacy_full_name:
                    # The stored user_name is actually a full name (legacy data)
                    # Use it as full_name if we don't have one from API
                    if not full_name:
                        full_name = stored_user_name
                        self.logger.info(f"Using stored user_name as full_name (legacy fix): {full_name}")
                    # Don't use stored_user_name as username - will generate new one
                elif stored_user_name and stored_user_name != 'User' and not stored_user_name.startswith('User_'):
                    # Stored username is in correct format
                    user_name = stored_user_name
                    self.logger.info(f"Using stored username from MongoDB: {user_name}")

                # Use stored full_name if API didn't return one
                if not full_name and stored_full_name:
                    full_name = stored_full_name
            else:
                # Create new user
                new_user_id = user_id
                if new_user_id:
                    user_id = new_user_id
                    profile_created = True
                    self.logger.info(f"New OAuth user created: {user_id}")

        # Generate username if not already set: firstname + user_id (e.g., hrushikesh282)
        if not user_name:
            # For OAuth users, use email prefix as fallback instead of phone
            email_prefix = email.split('@')[0] if email and '@' in email else None
            user_name = self._generate_username(full_name, user_id, email_prefix)
            self.logger.info(f"Generated username for OAuth user: {user_name}")

        # Create sessions - use email for OAuth users (phone may be empty)
        user_session_id = self._create_user_session_id(user_id, email if email else phone)
        chat_session_id = self._create_chat_session_id(user_id)

        # Create user session data - keep phone and email as separate fields
        user_session_data = {
            "session_id": user_session_id,
            "user_id": user_id,
            "phone": phone if phone else None,  # Actual phone number (may be None for OAuth)
            "email": email,  # Email from OAuth provider
            "user_name": user_name,  # e.g., hrushikesh282
            "full_name": full_name,  # e.g., Hrushikesh Tembe
            "access_token": access_token,
            "oauth_provider": provider,
            "created_at": current_timestamp,
            "last_activity": current_timestamp,
            "active": True,
            "session_type": "oauth_login"
        }

        # Store in Redis/memory
        store_session(user_session_id, user_session_data, expire_seconds=1296000)  # 15 days
        self.logger.info(f"OAuth user session created: {user_session_id}")

        # Create chat session data
        chat_session_data = {
            "session_id": chat_session_id,
            "user_id": user_id,
            "created_at": current_timestamp,
            "last_activity": current_timestamp,
            "active": True,
            "session_type": "chat"
        }

        store_session(chat_session_id, chat_session_data, expire_seconds=1296000)
        self.logger.info(f"Chat session created: {chat_session_id}")

        # Store in MongoDB if available
        if MONGODB_AVAILABLE:
            await self._handle_mongodb_operations_oauth(
                user_id=user_id,
                user_session_id=user_session_id,
                chat_session_id=chat_session_id,
                phone=phone if phone else None,  # Actual phone (may be None)
                email=email,  # Email from OAuth
                user_name=user_name,
                full_name=full_name,  # Pass full_name to MongoDB operations
                access_token=access_token,
                eazr_user_id=eazr_user_id,
                profile_created=profile_created,
                account_reactivated=account_reactivated,
                current_timestamp=current_timestamp,
                ip_address=ip_address,
                user_agent=user_agent,
                app_version=app_version,
                oauth_provider=provider
            )

        # Prepare response message
        response_message = f"OAuth login successful via {provider}"
        if account_reactivated:
            response_message = f"Welcome back! Your account has been reactivated via {provider}."
        elif profile_created:
            response_message = f"Welcome! Your account has been created via {provider}."

        self.logger.info(f"OAuth login completed for {email} - user: {user_id}, provider: {provider}")

        return {
            "success": True,
            "message": response_message,
            "session_id": user_session_id,
            "chat_session_id": chat_session_id,
            "user_phone": None,  # OAuth users don't have phone numbers
            "user_name": user_name,  # e.g., hrushikesh282
            "full_name": full_name,  # e.g., Hrushikesh Tembe
            "access_token": access_token,
            "user_id": user_id,
            "profile_created": profile_created,
            "email": email,
            "provider": provider
        }

    def validate_and_regenerate_session(
        self,
        session_id: str
    ) -> Tuple[str, Dict, bool]:
        """
        Validate session and regenerate if expired

        Args:
            session_id: Session ID to validate

        Returns:
            tuple: (valid_session_id, session_data, was_regenerated)
        """
        self.logger.info(f"Checking session: {session_id}")

        # Auto-validate and regenerate if needed
        valid_session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
            session_id,
            get_session,
            store_session
        )

        if was_regenerated:
            self.logger.info(f"Session regenerated: {session_id} -> {valid_session_id}")
        else:
            self.logger.info(f"Session valid: {valid_session_id}")

        return valid_session_id, session_data, was_regenerated

    # Helper methods

    def _normalize_phone_number(self, phone: str) -> str:
        """Extract number without country code"""
        return phone[3:] if phone.startswith("+91") else phone

    def _create_user_session_id(self, user_id: int, phone: str) -> str:
        """Generate user session ID"""
        return f"user_{int(time.time())}_{user_id}_{phone[-4:]}"

    def _create_chat_session_id(self, user_id: int) -> str:
        """Generate chat session ID"""
        return f"chat_{user_id}_{int(time.time())}_{secrets.token_hex(4)}"

    def _generate_username(self, full_name: str, user_id: int, phone: str = None) -> str:
        """
        Generate username in format: firstname + user_id

        Examples:
            - "Hrushikesh Tembe" + 282 -> "hrushikesh282"
            - "John Doe" + 123 -> "john123"
            - "" (no name) + 282 + phone "7021948806" -> "user8806282"

        Args:
            full_name: User's full name from API
            user_id: User's unique ID
            phone: Phone number (fallback if no name)

        Returns:
            Generated username string
        """
        import re

        if full_name and full_name.strip():
            # Extract first name (first word before space)
            first_name = full_name.strip().split()[0]
            # Remove any special characters, keep only alphanumeric
            first_name = re.sub(r'[^a-zA-Z0-9]', '', first_name)
            # Convert to lowercase
            first_name = first_name.lower()

            if first_name:
                return f"{first_name}{user_id}"

        # Fallback: use phone suffix if available
        if phone and len(phone) >= 4:
            phone_suffix = phone[-4:]
            return f"user{phone_suffix}{user_id}"

        # Final fallback
        return f"user{user_id}"

    async def _handle_mongodb_operations(
        self,
        user_id: int,
        user_session_id: str,
        chat_session_id: str,
        phone: str,
        user_name: str,
        full_name: str,
        access_token: str,
        eazr_user_id: Any,
        profile_created: bool,
        account_reactivated: bool,
        current_timestamp: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        app_version: Optional[Dict]
    ) -> None:
        """
        Handle all MongoDB operations for user authentication

        Args:
            user_id: User ID
            user_session_id: User session ID
            chat_session_id: Chat session ID
            phone: Phone number
            user_name: Username (e.g., hrushikesh282)
            full_name: Full name (e.g., Hrushikesh Tembe)
            access_token: Access token
            eazr_user_id: Eazr user ID
            profile_created: Whether profile was created
            account_reactivated: Whether account was reactivated
            current_timestamp: Current timestamp
            ip_address: IP address (optional)
            user_agent: User agent (optional)
            app_version: App version info (optional)
        """
        from database_storage.mongodb_chat_manager import (
            mongodb_chat_manager,
            log_user_login_activity
        )

        try:
            # Log login activity
            log_user_login_activity(
                user_id=user_id,
                session_id=user_session_id,
                phone=phone,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Store user session in MongoDB
            mongodb_chat_manager.sessions_collection.update_one(
                {"session_id": user_session_id},
                {
                    "$set": {
                        "user_id": user_id,  # Store as int
                        "session_type": "user_session",
                        "last_activity": datetime.utcnow(),
                        "phone": phone,
                        "user_name": user_name,
                        "access_token": access_token,
                        "eazr_user_id": str(eazr_user_id),
                        "active": True
                    },
                    "$setOnInsert": {"created_at": datetime.utcnow()}
                },
                upsert=True
            )

            # Create chat session in MongoDB
            chat_result = mongodb_chat_manager.create_new_chat_session(
                user_id=user_id,
                session_id=chat_session_id,
                title="New Chat"
            )

            if not chat_result.get("success"):
                self.logger.warning(f"Failed to create chat session in MongoDB for user {user_id}")

            # Handle user profile
            if profile_created:
                await self._create_user_profile(
                    user_id=user_id,
                    eazr_user_id=eazr_user_id,
                    user_session_id=user_session_id,
                    chat_session_id=chat_session_id,
                    phone=phone,
                    user_name=user_name,
                    full_name=full_name,
                    current_timestamp=current_timestamp,
                    app_version=app_version
                )
            elif account_reactivated:
                await self._reactivate_user_profile(
                    user_id=user_id,
                    eazr_user_id=eazr_user_id,
                    user_session_id=user_session_id,
                    chat_session_id=chat_session_id,
                    user_name=user_name,
                    full_name=full_name,
                    current_timestamp=current_timestamp
                )
            else:
                await self._update_user_profile(
                    user_id=user_id,
                    eazr_user_id=eazr_user_id,
                    user_session_id=user_session_id,
                    chat_session_id=chat_session_id,
                    user_name=user_name,
                    full_name=full_name,
                    current_timestamp=current_timestamp
                )

        except Exception as mongo_error:
            self.logger.error(f"MongoDB operation failed: {mongo_error}")
            # Continue even if MongoDB fails

    async def _create_user_profile(
        self,
        user_id: int,
        eazr_user_id: Any,
        user_session_id: str,
        chat_session_id: str,
        phone: str,
        user_name: str,
        full_name: str,
        current_timestamp: str,
        app_version: Optional[Dict]
    ) -> None:
        """Create new user profile in MongoDB

        Args:
            user_name: Generated username (e.g., hrushikesh282)
            full_name: Full name from API (e.g., Hrushikesh Tembe)
        """
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        new_profile = {
            "user_id": user_id,  # Store as int
            "eazr_user_id": str(eazr_user_id),
            "last_user_session_id": user_session_id,
            "last_chat_session_id": chat_session_id,
            "user_session_history": [user_session_id],
            "chat_session_history": [chat_session_id],
            "preferences": {
                "phone": phone,
                "user_name": user_name,  # e.g., hrushikesh282
                "full_name": full_name,  # e.g., Hrushikesh Tembe
                "registration_date": current_timestamp,
                "last_login": current_timestamp,
                "login_count": 1,
                "profile_completion_score": 40 if full_name else 30
            },
            "interests": [],
            "language_preference": "en",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "deleted": False,
            "status": "active"
        }

        # Add app version info if provided
        if app_version:
            new_profile["preferences"].update({
                "app_platform": app_version.get("platform"),
                "android_version": app_version.get("android_version") or "1.0.0",
                "ios_version": app_version.get("ios_version") or "1.0.0"
            })

        mongodb_chat_manager.users_collection.insert_one(new_profile)
        self.logger.info(f"Created profile for new user {user_id} with username: {user_name}, full_name: {full_name}")

    async def _reactivate_user_profile(
        self,
        user_id: int,
        eazr_user_id: Any,
        user_session_id: str,
        chat_session_id: str,
        user_name: str,
        full_name: str,
        current_timestamp: str
    ) -> None:
        """Reactivate existing user profile in MongoDB

        Args:
            user_name: Generated username (e.g., hrushikesh282)
            full_name: Full name from API (e.g., Hrushikesh Tembe)
        """
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        # Build update data
        update_set = {
            "preferences.last_login": current_timestamp,
            "last_user_session_id": user_session_id,
            "last_chat_session_id": chat_session_id,
            "updated_at": datetime.utcnow(),
            "deleted": False,
            "status": "active",
            "reactivated_at": datetime.utcnow(),
            "eazr_user_id": str(eazr_user_id),
            "user_id": user_id  # Ensure int type
        }

        # Always update username (e.g., hrushikesh282) and full_name
        if user_name:
            update_set["preferences.user_name"] = user_name
        if full_name:
            update_set["preferences.full_name"] = full_name

        mongodb_chat_manager.users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": update_set,
                "$addToSet": {
                    "user_session_history": user_session_id,
                    "chat_session_history": chat_session_id
                },
                "$inc": {"preferences.login_count": 1}
            }
        )
        self.logger.info(f"Reactivated profile for user {user_id} with username: {user_name}")

    async def _update_user_profile(
        self,
        user_id: int,
        eazr_user_id: Any,
        user_session_id: str,
        chat_session_id: str,
        user_name: str,
        full_name: str,
        current_timestamp: str
    ) -> None:
        """Update existing active user profile in MongoDB

        Args:
            user_name: Generated username (e.g., hrushikesh282)
            full_name: Full name from API (e.g., Hrushikesh Tembe)
        """
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        # Build update data
        update_set = {
            "preferences.last_login": current_timestamp,
            "last_user_session_id": user_session_id,
            "last_chat_session_id": chat_session_id,
            "updated_at": datetime.utcnow(),
            "eazr_user_id": str(eazr_user_id),
            "user_id": user_id  # Ensure int type
        }

        # Always update username (e.g., hrushikesh282) and full_name
        if user_name:
            update_set["preferences.user_name"] = user_name
            self.logger.info(f"Updating user_name to: {user_name}")
        if full_name:
            update_set["preferences.full_name"] = full_name
            self.logger.info(f"Updating full_name to: {full_name}")

        mongodb_chat_manager.users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": update_set,
                "$addToSet": {
                    "user_session_history": user_session_id,
                    "chat_session_history": chat_session_id
                },
                "$inc": {"preferences.login_count": 1}
            }
        )
        self.logger.info(f"Updated profile for existing user {user_id}")

    async def _handle_mongodb_operations_oauth(
        self,
        user_id: int,
        user_session_id: str,
        chat_session_id: str,
        phone: Optional[str],
        email: str,
        user_name: str,
        full_name: str,
        access_token: str,
        eazr_user_id: Any,
        profile_created: bool,
        account_reactivated: bool,
        current_timestamp: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        app_version: Optional[Dict],
        oauth_provider: str
    ) -> None:
        """
        Handle MongoDB operations for OAuth authentication

        This is separate from phone OTP to properly handle email and phone as separate fields

        Args:
            user_name: Generated username (e.g., hrushikesh282)
            full_name: Full name from API (e.g., Hrushikesh Tembe)
        """
        from database_storage.mongodb_chat_manager import (
            mongodb_chat_manager,
            log_user_login_activity
        )

        try:
            # Log login activity - use email for OAuth users
            log_user_login_activity(
                user_id=user_id,
                session_id=user_session_id,
                phone=email,  # Log email for OAuth login activity
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Store user session in MongoDB with proper email/phone separation
            mongodb_chat_manager.sessions_collection.update_one(
                {"session_id": user_session_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "session_type": "oauth_session",
                        "last_activity": datetime.utcnow(),
                        "phone": phone,  # Actual phone (may be None)
                        "email": email,  # Email from OAuth
                        "user_name": user_name,
                        "access_token": access_token,
                        "eazr_user_id": str(eazr_user_id),
                        "oauth_provider": oauth_provider,
                        "active": True
                    },
                    "$setOnInsert": {"created_at": datetime.utcnow()}
                },
                upsert=True
            )

            # Create chat session in MongoDB
            chat_result = mongodb_chat_manager.create_new_chat_session(
                user_id=user_id,
                session_id=chat_session_id,
                title="New Chat"
            )

            if not chat_result.get("success"):
                self.logger.warning(f"Failed to create chat session for OAuth user {user_id}")

            # Handle user profile
            if profile_created:
                await self._create_oauth_user_profile(
                    user_id=user_id,
                    eazr_user_id=eazr_user_id,
                    user_session_id=user_session_id,
                    chat_session_id=chat_session_id,
                    phone=phone,
                    email=email,
                    user_name=user_name,
                    full_name=full_name,
                    oauth_provider=oauth_provider,
                    current_timestamp=current_timestamp,
                    app_version=app_version
                )
            elif account_reactivated:
                await self._reactivate_oauth_user_profile(
                    user_id=user_id,
                    eazr_user_id=eazr_user_id,
                    user_session_id=user_session_id,
                    chat_session_id=chat_session_id,
                    email=email,
                    user_name=user_name,
                    full_name=full_name,
                    oauth_provider=oauth_provider,
                    current_timestamp=current_timestamp
                )
            else:
                await self._update_oauth_user_profile(
                    user_id=user_id,
                    eazr_user_id=eazr_user_id,
                    user_session_id=user_session_id,
                    chat_session_id=chat_session_id,
                    email=email,
                    user_name=user_name,
                    full_name=full_name,
                    oauth_provider=oauth_provider,
                    current_timestamp=current_timestamp
                )

        except Exception as mongo_error:
            self.logger.error(f"MongoDB OAuth operation failed: {mongo_error}")

    async def _create_oauth_user_profile(
        self,
        user_id: int,
        eazr_user_id: Any,
        user_session_id: str,
        chat_session_id: str,
        phone: Optional[str],
        email: str,
        user_name: str,
        full_name: str,
        oauth_provider: str,
        current_timestamp: str,
        app_version: Optional[Dict]
    ) -> None:
        """Create new user profile for OAuth users with proper email/phone separation

        Args:
            user_name: Generated username (e.g., hrushikesh282)
            full_name: Full name from API (e.g., Hrushikesh Tembe)
        """
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        new_profile = {
            "user_id": user_id,
            "eazr_user_id": str(eazr_user_id),
            "last_user_session_id": user_session_id,
            "last_chat_session_id": chat_session_id,
            "user_session_history": [user_session_id],
            "chat_session_history": [chat_session_id],
            "preferences": {
                "phone": phone,  # Actual phone (may be None for OAuth users)
                "email": email,  # Email from OAuth provider
                "user_name": user_name,  # e.g., hrushikesh282
                "full_name": full_name,  # e.g., Hrushikesh Tembe
                "registration_date": current_timestamp,
                "last_login": current_timestamp,
                "login_count": 1,
                "profile_completion_score": 40 if full_name else 30,
                "auth_method": oauth_provider
            },
            "interests": [],
            "language_preference": "en",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "deleted": False,
            "status": "active",
            "oauth_provider": oauth_provider
        }

        if app_version:
            new_profile["preferences"].update({
                "app_platform": app_version.get("platform"),
                "android_version": app_version.get("android_version") or "1.0.0",
                "ios_version": app_version.get("ios_version") or "1.0.0"
            })

        mongodb_chat_manager.users_collection.insert_one(new_profile)
        self.logger.info(f"Created OAuth profile for user {user_id} via {oauth_provider}")

    async def _reactivate_oauth_user_profile(
        self,
        user_id: int,
        eazr_user_id: Any,
        user_session_id: str,
        chat_session_id: str,
        email: str,
        user_name: str,
        full_name: str,
        oauth_provider: str,
        current_timestamp: str
    ) -> None:
        """Reactivate OAuth user profile

        Args:
            user_name: Generated username (e.g., hrushikesh282)
            full_name: Full name from API (e.g., Hrushikesh Tembe)
        """
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        update_set = {
            "preferences.last_login": current_timestamp,
            "preferences.email": email,
            "last_user_session_id": user_session_id,
            "last_chat_session_id": chat_session_id,
            "updated_at": datetime.utcnow(),
            "deleted": False,
            "status": "active",
            "reactivated_at": datetime.utcnow(),
            "eazr_user_id": str(eazr_user_id),
            "user_id": user_id,
            "oauth_provider": oauth_provider
        }

        # Always update username and full_name
        if user_name:
            update_set["preferences.user_name"] = user_name
        if full_name:
            update_set["preferences.full_name"] = full_name

        mongodb_chat_manager.users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": update_set,
                "$addToSet": {
                    "user_session_history": user_session_id,
                    "chat_session_history": chat_session_id
                },
                "$inc": {"preferences.login_count": 1}
            }
        )
        self.logger.info(f"Reactivated OAuth profile for user {user_id} with username: {user_name}")

    async def _update_oauth_user_profile(
        self,
        user_id: int,
        eazr_user_id: Any,
        user_session_id: str,
        chat_session_id: str,
        email: str,
        user_name: str,
        full_name: str,
        oauth_provider: str,
        current_timestamp: str
    ) -> None:
        """Update existing OAuth user profile

        This also fixes legacy data where:
        - Email was stored in phone field
        - Full name was stored in user_name field

        Args:
            user_name: Generated username (e.g., hrushikesh282)
            full_name: Full name from API (e.g., Hrushikesh Tembe)
        """
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        update_set = {
            "preferences.last_login": current_timestamp,
            "preferences.email": email,  # Ensure email is in correct field
            "preferences.phone": None,   # Clear phone for OAuth users (was storing email incorrectly)
            "last_user_session_id": user_session_id,
            "last_chat_session_id": chat_session_id,
            "updated_at": datetime.utcnow(),
            "eazr_user_id": str(eazr_user_id),
            "user_id": user_id,
            "oauth_provider": oauth_provider
        }

        # Always update username and full_name to fix legacy data
        if user_name:
            update_set["preferences.user_name"] = user_name
            self.logger.info(f"Updating OAuth user_name to: {user_name}")
        if full_name:
            update_set["preferences.full_name"] = full_name
            self.logger.info(f"Updating OAuth full_name to: {full_name}")

        mongodb_chat_manager.users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": update_set,
                "$addToSet": {
                    "user_session_history": user_session_id,
                    "chat_session_history": chat_session_id
                },
                "$inc": {"preferences.login_count": 1}
            }
        )
        self.logger.info(f"Updated OAuth profile for user {user_id}")
