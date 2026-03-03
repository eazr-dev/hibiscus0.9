# session_manager.py - Enhanced with better user data recovery

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
import random
import hashlib

logger = logging.getLogger(__name__)

class AutoRegeneratingSessionManager:
    """Enhanced session manager with user data recovery - Optimized"""

    def __init__(self):
        # Track session mappings and user data
        self.session_mapping = {}  # old_session_id -> new_session_id
        self.user_data_cache = {}  # session_id -> user_data
        self.regeneration_count = {}
        self.cache_timestamps = {}  # Track cache freshness
        self.CACHE_TTL = 300  # 5 minutes cache TTL
        
    def generate_new_session_id(self, user_phone: str = None, user_id: int = None) -> str:
        """Generate a new session ID"""
        timestamp = int(time.time())
        random_part = random.randint(1000, 9999)
        
        if user_phone:
            phone_suffix = user_phone[-4:] if len(user_phone) >= 4 else "0000"
            return f"user_{timestamp}_{phone_suffix}_{random_part}"
        elif user_id:
            return f"user_{timestamp}_{user_id}_{random_part}"
        else:
            return f"session_{timestamp}_{random_part}"
    
    def extract_user_data_from_session_id(self, session_id: str) -> Dict:
        """Try to extract user data from session ID format"""
        user_data = {}
        
        # Try to extract from session ID pattern
        if session_id.startswith("user_"):
            parts = session_id.split("_")
            if len(parts) >= 3:
                # Try to extract phone suffix (might be last 4 digits)
                possible_phone = parts[2]
                if possible_phone.isdigit() and len(possible_phone) == 4:
                    # Store as potential phone suffix
                    user_data['phone_suffix'] = possible_phone
        
        return user_data
    
    def recover_user_data_from_mongodb(self, session_id: str, old_session_data: Dict = None) -> Dict:
        """Try to recover user data from MongoDB"""
        recovered_data = {}
        
        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            
            if not mongodb_chat_manager:
                return recovered_data
            
            # Try different recovery methods
            
            # Method 1: Find by session_id in sessions collection
            session_doc = mongodb_chat_manager.sessions_collection.find_one({"session_id": session_id})
            if session_doc:
                recovered_data['user_id'] = session_doc.get('user_id')
                recovered_data['phone'] = session_doc.get('phone')
                recovered_data['user_name'] = session_doc.get('user_name')
                if recovered_data['user_id']:
                    logger.info(f"Recovered user data from MongoDB sessions: user_id={recovered_data['user_id']}")
                    return recovered_data
            
            # Method 2: If we have phone from old session, find user by phone
            if old_session_data and old_session_data.get('phone'):
                phone = old_session_data['phone']
                user_doc = mongodb_chat_manager.users_collection.find_one(
                    {"preferences.phone": phone}
                )
                if user_doc:
                    recovered_data['user_id'] = user_doc.get('user_id')
                    recovered_data['phone'] = phone
                    recovered_data['user_name'] = user_doc.get('preferences', {}).get('user_name', 'User')
                    logger.info(f"Recovered user data from MongoDB by phone: user_id={recovered_data['user_id']}")
                    return recovered_data
            
            # Method 3: Find by last_session_id in users collection
            user_doc = mongodb_chat_manager.users_collection.find_one(
                {"last_session_id": session_id}
            )
            if user_doc:
                recovered_data['user_id'] = user_doc.get('user_id')
                prefs = user_doc.get('preferences', {})
                recovered_data['phone'] = prefs.get('phone')
                recovered_data['user_name'] = prefs.get('user_name', 'User')
                logger.info(f"Recovered user data from MongoDB users: user_id={recovered_data['user_id']}")
                return recovered_data
            
            # Method 4: Check session history
            user_doc = mongodb_chat_manager.users_collection.find_one(
                {"session_history": session_id}
            )
            if user_doc:
                recovered_data['user_id'] = user_doc.get('user_id')
                prefs = user_doc.get('preferences', {})
                recovered_data['phone'] = prefs.get('phone')
                recovered_data['user_name'] = prefs.get('user_name', 'User')
                logger.info(f"Recovered user data from session history: user_id={recovered_data['user_id']}")
                return recovered_data
                
        except Exception as e:
            logger.error(f"Error recovering user data from MongoDB: {e}")
        
        return recovered_data
    
    def validate_and_regenerate_session(
        self,
        session_id: str,
        get_session_func,
        store_session_func,
        user_data: Dict = None
    ) -> Tuple[str, Dict, bool]:
        """
        Enhanced validation and regeneration with MongoDB sync - Optimized
        """
        try:
            # Check cached user data first with TTL validation
            if session_id in self.user_data_cache:
                cache_time = self.cache_timestamps.get(session_id, 0)
                if time.time() - cache_time < self.CACHE_TTL:
                    cached_data = self.user_data_cache[session_id]
                    logger.info(f" Cache hit for {session_id}: user_id={cached_data.get('user_id')}")
                    if user_data:
                        user_data.update(cached_data)
                    else:
                        user_data = cached_data
                else:
                    # Invalidate expired cache
                    del self.user_data_cache[session_id]
                    del self.cache_timestamps[session_id]
            
            # Check if this session was already regenerated
            if session_id in self.session_mapping:
                mapped_session_id = self.session_mapping[session_id]
                mapped_session_data = get_session_func(mapped_session_id)
                if mapped_session_data and mapped_session_data.get('active'):
                    # Ensure user data is present
                    if not mapped_session_data.get('user_id') and user_data:
                        mapped_session_data.update(user_data)
                        store_session_func(mapped_session_id, mapped_session_data, expire_seconds=1209600)
                    return mapped_session_id, mapped_session_data, False
            
            # Try to get existing session
            session_data = get_session_func(session_id)
            
            # Cache any user data we find with timestamp
            if session_data and session_data.get('user_id'):
                self.user_data_cache[session_id] = {
                    'user_id': session_data.get('user_id'),
                    'phone': session_data.get('phone'),
                    'user_name': session_data.get('user_name', 'User'),
                    'access_token': session_data.get('access_token')
                }
                self.cache_timestamps[session_id] = time.time()
            
            if session_data and session_data.get('active'):
                # Check if session is actually expired
                try:
                    last_activity = datetime.fromisoformat(session_data.get('last_activity', ''))
                    if datetime.now() - last_activity < timedelta(days=14):
                        # Session is still valid
                        return session_id, session_data, False
                except:
                    pass
            
            # Session expired - need to regenerate
            logger.info(f"Session {session_id} expired/invalid, regenerating with MongoDB sync...")
            
            # Comprehensive data recovery
            recovered_user_data = {}
            
            # 1. From provided user_data
            if user_data:
                recovered_user_data.update(user_data)
            
            # 2. From old session data
            if session_data:
                if session_data.get('user_id'):
                    recovered_user_data['user_id'] = session_data['user_id']
                if session_data.get('phone'):
                    recovered_user_data['phone'] = session_data['phone']
                if session_data.get('user_name'):
                    recovered_user_data['user_name'] = session_data['user_name']
                if session_data.get('access_token'):
                    recovered_user_data['access_token'] = session_data['access_token']
            
            # 3. From MongoDB if still missing user_id
            if not recovered_user_data.get('user_id'):
                mongodb_data = self.recover_user_data_from_mongodb(session_id, session_data)
                if mongodb_data:
                    recovered_user_data.update(mongodb_data)
            
            # 4. From cached data
            if session_id in self.user_data_cache:
                cached = self.user_data_cache[session_id]
                for key, value in cached.items():
                    if not recovered_user_data.get(key):
                        recovered_user_data[key] = value
            
            # Generate new session ID
            new_session_id = self.generate_new_session_id(
                recovered_user_data.get('phone'),
                recovered_user_data.get('user_id')
            )
            
            # Track regeneration
            self.session_mapping[session_id] = new_session_id
            self.regeneration_count[new_session_id] = self.regeneration_count.get(session_id, 0) + 1
            
            # Create comprehensive new session data
            new_session_data = {
                'phone': recovered_user_data.get('phone'),
                'user_name': recovered_user_data.get('user_name', 'User'),
                'user_id': recovered_user_data.get('user_id'),
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'active': True,
                'regenerated_from': session_id,
                'regeneration_count': self.regeneration_count[new_session_id],
                'access_token': recovered_user_data.get('access_token')
            }
            
            # Cache the user data for the new session with timestamp
            if new_session_data.get('user_id'):
                self.user_data_cache[new_session_id] = {
                    'user_id': new_session_data['user_id'],
                    'phone': new_session_data.get('phone'),
                    'user_name': new_session_data.get('user_name'),
                    'access_token': new_session_data.get('access_token')
                }
                self.cache_timestamps[new_session_id] = time.time()
            
            # Store new session
            success = store_session_func(new_session_id, new_session_data, expire_seconds=1209600)
            
            if success:
                logger.info(f"Successfully regenerated session: {session_id} -> {new_session_id} with user_id={new_session_data.get('user_id')}")
                
                # CRITICAL: Sync MongoDB with new session (this is the key fix)
                self._sync_mongodb_with_new_session(session_id, new_session_id, new_session_data)
                
                # Migrate chatbot sessions
                self._migrate_chatbot_sessions(session_id, new_session_id)
                
                return new_session_id, new_session_data, True
            else:
                logger.error("Failed to store regenerated session")
                if session_data:
                    session_data.update(recovered_user_data)
                else:
                    session_data = recovered_user_data
                session_data['active'] = True
                return session_id, session_data, False
                
        except Exception as e:
            logger.error(f"Error in session validation/regeneration: {e}")
            
            # Emergency session with any available data
            emergency_user_id = None
            if user_data and user_data.get('user_id'):
                emergency_user_id = user_data['user_id']
            elif session_id in self.user_data_cache:
                emergency_user_id = self.user_data_cache[session_id].get('user_id')
            
            emergency_session_id = f"emergency_{int(time.time())}_{emergency_user_id or random.randint(1000, 9999)}"
            emergency_session_data = {
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'active': True,
                'emergency': True,
                'user_id': emergency_user_id,
                'access_token': user_data.get('access_token') if user_data else None
            }
            return emergency_session_id, emergency_session_data, True
    
    def _migrate_chatbot_sessions(self, old_session_id: str, new_session_id: str):
        """Migrate chatbot sessions from old to new session ID"""
        try:
            from ai_chat_components.enhanced_chatbot_handlers import chatbot_sessions
            
            keys_to_migrate = []
            for key in list(chatbot_sessions.keys()):
                if old_session_id in key:
                    keys_to_migrate.append(key)
            
            for old_key in keys_to_migrate:
                new_key = old_key.replace(old_session_id, new_session_id)
                chatbot_sessions[new_key] = chatbot_sessions[old_key]
                # Update session data in the chatbot session
                if hasattr(chatbot_sessions[new_key], 'session_id'):
                    chatbot_sessions[new_key].session_id = new_session_id
                del chatbot_sessions[old_key]
                logger.info(f"Migrated chatbot session: {old_key} -> {new_key}")
                
        except Exception as e:
            logger.error(f"Error migrating chatbot sessions: {e}")

    def _sync_mongodb_with_new_session(self, old_session_id: str, new_session_id: str, new_session_data: Dict):
        """CRITICAL: Sync MongoDB collections with the new session ID - this is the main fix"""
        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            
            if not mongodb_chat_manager:
                logger.warning("MongoDB not available for session sync")
                return
                
            user_id = new_session_data.get('user_id')
            if not user_id:
                logger.warning("No user_id in new session data for MongoDB sync")
                return
            
            current_time = datetime.utcnow()
            
            # 1. Update user profile with new session ID (MOST IMPORTANT)
            result = mongodb_chat_manager.users_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "last_session_id": new_session_id,
                        "updated_at": current_time,
                        "preferences.last_login": current_time.isoformat(),
                        "session_regenerated_at": current_time.isoformat(),
                        "session_regenerated_from": old_session_id
                    },
                    "$addToSet": {
                        "session_history": new_session_id
                    }
                }
            )
            
            if result.matched_count > 0:
                logger.info(f"Updated MongoDB user profile for user {user_id} with new session {new_session_id}")
            else:
                logger.warning(f"No user profile found in MongoDB for user_id {user_id}")
                
                # Create basic profile if it doesn't exist
                try:
                    basic_profile = {
                        "user_id": user_id,
                        "last_session_id": new_session_id,
                        "session_history": [old_session_id, new_session_id],
                        "preferences": {
                            "phone": new_session_data.get('phone'),
                            "user_name": new_session_data.get('user_name', 'User'),
                            "registration_date": current_time.isoformat(),
                            "last_login": current_time.isoformat(),
                            "login_count": 1,
                            "profile_completion_score": 30
                        },
                        "interests": [],
                        "language_preference": "en",
                        "interaction_patterns": {},
                        "created_at": current_time,
                        "updated_at": current_time
                    }
                    
                    mongodb_chat_manager.users_collection.insert_one(basic_profile)
                    logger.info(f"Created basic MongoDB profile for user {user_id}")
                    
                except Exception as profile_error:
                    logger.error(f"Error creating basic profile: {profile_error}")
            
            # 2. Update sessions collection
            mongodb_chat_manager.sessions_collection.update_one(
                {"session_id": new_session_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "phone": new_session_data.get('phone'),
                        "user_name": new_session_data.get('user_name'),
                        "last_activity": current_time,
                        "regenerated_from": old_session_id,
                        "active": True
                    },
                    "$setOnInsert": {
                        "created_at": current_time
                    }
                },
                upsert=True
            )
            
            # 3. Mark old session as expired
            mongodb_chat_manager.sessions_collection.update_one(
                {"session_id": old_session_id},
                {
                    "$set": {
                        "expired_at": current_time,
                        "regenerated_to": new_session_id,
                        "active": False,
                        "status": "expired_regenerated"
                    }
                }
            )
            
            logger.info(f"MongoDB fully synced: {old_session_id} -> {new_session_id} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error syncing MongoDB with new session: {e}")

# Create global instance
session_manager = AutoRegeneratingSessionManager()