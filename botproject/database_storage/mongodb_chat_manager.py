# mongodb_chat_manager.py - FIXED VERSION with all missing methods

import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
import json
from bson import ObjectId
import hashlib
import time
import secrets
import os
from session_security.security_utils import sanitize_regex_input, validate_user_id, validate_limit

logger = logging.getLogger(__name__)

# IST Timezone helper function
def get_ist_now():
    """Get current time in IST (Indian Standard Time - UTC+5:30)"""
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_timezone).replace(tzinfo=None)

# MongoDB Configuration - Environment-based with connection pooling
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

# Get MongoDB URI based on environment
if ENVIRONMENT == "production":
    MONGODB_URI = os.getenv("MONGODB_URI_PRODUCTION")
    DATABASE_NAME = os.getenv("MONGODB_DB_PRODUCTION", "insurance_analysis_db")
    logger.info("🚀 Using PRODUCTION MongoDB (Atlas)")
else:
    MONGODB_URI = os.getenv("MONGODB_URI_LOCAL", "mongodb://localhost:27017/")
    DATABASE_NAME = os.getenv("MONGODB_DB_LOCAL", "insurance_analysis_db")
    logger.info("🔧 Using LOCAL MongoDB")

if not MONGODB_URI:
    raise ValueError(f"MongoDB URI not configured for environment: {ENVIRONMENT}")

# Validate MongoDB URI format
if not MONGODB_URI.startswith(('mongodb://', 'mongodb+srv://')):
    raise ValueError("Invalid MongoDB URI format. Must start with mongodb:// or mongodb+srv://")

COLLECTION_NAME = "policy_analyses"

# Get connection pool settings from environment
# Increased timeouts for MongoDB Atlas to handle network latency
MAX_POOL_SIZE = int(os.getenv("MONGO_MAX_POOL_SIZE", "50"))
MIN_POOL_SIZE = int(os.getenv("MONGO_MIN_POOL_SIZE", "10"))
CONNECT_TIMEOUT = int(os.getenv("MONGO_CONNECT_TIMEOUT", "30000"))  # 30s for Atlas connections
SOCKET_TIMEOUT = int(os.getenv("MONGO_SOCKET_TIMEOUT", "45000"))  # 45s for operations
SERVER_SELECTION_TIMEOUT = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT", "30000"))  # 30s

logger.info(f"📊 MongoDB Database: {DATABASE_NAME}")
logger.info(f"🔗 MongoDB URI: {MONGODB_URI[:30]}...")

# SSL Configuration — only for Atlas (mongodb+srv://) connections
import ssl
import certifi

_mongo_kwargs = dict(
    maxPoolSize=MAX_POOL_SIZE,
    minPoolSize=MIN_POOL_SIZE,
    maxIdleTimeMS=60000,
    serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT,
    connectTimeoutMS=CONNECT_TIMEOUT,
    socketTimeoutMS=SOCKET_TIMEOUT,
    retryWrites=True,
    retryReads=True,
    w='majority',
    readPreference='primaryPreferred',
    heartbeatFrequencyMS=30000,
    appname='EazrFinancialAssistant',
)

# Only enable TLS for Atlas/remote connections (mongodb+srv:// or explicit tls in URI)
if MONGODB_URI.startswith('mongodb+srv://') or 'tls=true' in MONGODB_URI or 'ssl=true' in MONGODB_URI:
    _mongo_kwargs['tlsCAFile'] = certifi.where()
    logger.info("TLS enabled for MongoDB connection")

# Initialize MongoDB client with connection pooling and optimizations
mongo_client = MongoClient(MONGODB_URI, **_mongo_kwargs)
insurance_db = mongo_client[DATABASE_NAME]
policy_collection = insurance_db[COLLECTION_NAME]

logger.info(f"✅ MongoDB connection initialized for {ENVIRONMENT} environment")


@dataclass
class AppVersion:
    """App version information structure"""
    version_id: str
    platform: str  # 'ios' or 'android'
    version_number: str
    version_name: Optional[str] = None
    build_number: Optional[str] = None
    release_date: datetime = None
    minimum_supported: bool = True
    force_update: bool = False
    release_notes: Optional[str] = None
    download_url: Optional[str] = None
    features: Optional[List[str]] = None
    bug_fixes: Optional[List[str]] = None
    status: str = "active"  # active, deprecated, discontinued
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = get_ist_now()
        if self.updated_at is None:
            self.updated_at = get_ist_now()
        if self.release_date is None:
            self.release_date = get_ist_now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'version_id': self.version_id,
            'platform': self.platform,
            'version_number': self.version_number,
            'version_name': self.version_name,
            'build_number': self.build_number,
            'release_date': self.release_date,
            'minimum_supported': self.minimum_supported,
            'force_update': self.force_update,
            'release_notes': self.release_notes,
            'download_url': self.download_url,
            'features': self.features or [],
            'bug_fixes': self.bug_fixes or [],
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

def store_policy_analysis_in_mongodb(
    userId: str,
    sessionId: str,
    filename: str,
    analysis_result: Dict[Any, Any],
    s3_url: str = None
) -> str:
    """Store policy analysis result in MongoDB with original document and report URLs"""
    try:
        # Extract URLs from analysis_result if present
        original_document_url = analysis_result.get("original_document_url", s3_url)
        analysis_report_url = analysis_result.get("analysis_report_url")

        document = {
            "userId": userId,
            "sessionId": sessionId,
            "uploaded_filename": filename,

            # Store all S3 URLs at root level for easy querying
            "original_document_url": original_document_url,  # User's uploaded document
            "analysis_report_url": analysis_report_url,      # Generated analysis PDF
            "s3_report_url": s3_url,  # Backward compatibility

            # File metadata
            "file_type": analysis_result.get("file_type", "pdf"),
            "file_size": analysis_result.get("file_size"),

            # Timestamps
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "upload_timestamp": analysis_result.get("upload_timestamp"),

            # Analysis summary data at root level
            "insurance_type": analysis_result.get("insurance_type"),
            "total_score": analysis_result.get("total_score"),
            "protection_level": analysis_result.get("protection_level"),
            "company_name": analysis_result.get("company_name"),
            "policy_number": analysis_result.get("policy_number"),

            # Full analysis data
            "analysis_data": {
                "insurance_type": analysis_result.get("insurance_type"),
                "total_score": analysis_result.get("total_score"),
                "protection_level": analysis_result.get("protection_level"),
                "general_recommendation": analysis_result.get("general_recommendation"),
                "personalized_recommendations": analysis_result.get("personalized_recommendations", []),
                "extraction_confidence": analysis_result.get("extraction_confidence"),
                "category_scores": analysis_result.get("category_scores", {}),
                "policy_info": analysis_result.get("policy_info", {}),
                "user_info": analysis_result.get("user_info", {}),
                "extraction_info": analysis_result.get("extraction_info", {}),

                # Include all other fields from analysis_result
                **{k: v for k, v in analysis_result.items() if k not in [
                    "insurance_type", "total_score", "protection_level",
                    "general_recommendation", "personalized_recommendations",
                    "extraction_confidence", "category_scores", "policy_info",
                    "user_info", "extraction_info", "original_document_url",
                    "analysis_report_url", "file_type", "file_size", "upload_timestamp"
                ]}
            }
        }

        result = policy_collection.insert_one(document)
        logger.info(f" Stored policy analysis in MongoDB with ID: {result.inserted_id} for user: {userId}")
        logger.info(f" Original document URL: {original_document_url}")
        logger.info(f" Analysis report URL: {analysis_report_url}")
        return str(result.inserted_id)

    except Exception as e:
        logger.error(f" Error storing policy analysis in MongoDB for user {userId}: {str(e)}")
        raise Exception(f"Failed to store analysis in database: {str(e)}")

def get_policy_analysis_by_id(analysis_id: str) -> Dict:
    """Get specific policy analysis by MongoDB _id"""
    try:
        analysis = policy_collection.find_one({"_id": ObjectId(analysis_id)})
        
        if analysis:
            analysis["_id"] = str(analysis["_id"])
            analysis["created_at"] = analysis["created_at"].isoformat()
            analysis["updated_at"] = analysis["updated_at"].isoformat()
        
        return analysis
        
    except Exception as e:
        logger.error(f" Error retrieving policy analysis by ID: {str(e)}")
        return None

def get_user_latest_policy_analysis(userId: str) -> list:
    """Get all policy analyses for a specific user"""
    try:
        analyses = list(policy_collection.find(
            {"userId": userId}
        ).sort("created_at", -1))
        
        if analyses:
            for analysis in analyses:
                analysis["_id"] = str(analysis["_id"])
                analysis["created_at"] = analysis["created_at"].isoformat()
                analysis["updated_at"] = analysis["updated_at"].isoformat()
            
            logger.info(f" Retrieved {len(analyses)} policy analyses for user: {userId}")
            return analyses
        else:
            logger.info(f" No policy analyses found for user: {userId}")
            return []
            
    except Exception as e:
        logger.error(f" Error retrieving policy analyses for user {userId}: {str(e)}")
        return []

@dataclass
class ChatMessage:
    """Individual chat message structure"""
    message_id: str
    session_id: str
    user_id: int
    role: str  # 'user' or 'assistant'
    content: str
    intent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    language: str = 'en'
    response_data: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = get_ist_now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        doc = {
            'message_id': self.message_id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'intent': self.intent,
            'context': self.context or {},
            'metadata': self.metadata or {},
            'timestamp': self.timestamp,
            'language': self.language
        }
        if self.response_data:
            doc['response_data'] = self.response_data
        return doc

@dataclass
class UserProfile:
    """User profile and preferences"""
    user_id: int
    session_id: str
    preferences: Dict[str, Any]
    interests: List[str]
    language_preference: str
    interaction_patterns: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'preferences': self.preferences,
            'interests': self.interests,
            'language_preference': self.language_preference,
            'interaction_patterns': self.interaction_patterns,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

@dataclass
class ConversationSummary:
    """Conversation summary for context"""
    session_id: str
    user_id: int
    summary_text: str
    key_topics: List[str]
    user_intents: List[str]
    important_entities: Dict[str, Any]
    conversation_length: int
    start_time: datetime
    end_time: datetime
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'summary_text': self.summary_text,
            'key_topics': self.key_topics,
            'user_intents': self.user_intents,
            'important_entities': self.important_entities,
            'conversation_length': self.conversation_length,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'created_at': self.created_at
        }

@dataclass
class UserActivity:
    """User activity tracking"""
    user_id: int
    session_id: str
    activity_type: str  # 'login', 'logout', 'chat', 'api_call'
    phone: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = get_ist_now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'activity_type': self.activity_type,
            'phone': self.phone,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'metadata': self.metadata or {},
            'timestamp': self.timestamp
        }

class MongoDBChatManager:
    """MongoDB-based chat memory management system with user activity tracking - Optimized"""

    def __init__(self, mongodb_uri: str = MONGODB_URI, database_name: str = "eazr_chatbot"):
        _chat_kwargs = dict(
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            retryWrites=True,
            retryReads=True,
            w='majority',
            readPreference='primaryPreferred',
        )
        if mongodb_uri.startswith('mongodb+srv://') or 'tls=true' in mongodb_uri or 'ssl=true' in mongodb_uri:
            _chat_kwargs['tlsCAFile'] = certifi.where()
        self.client = MongoClient(mongodb_uri, **_chat_kwargs)
        self.db = self.client[database_name]
        
        # Initialize collections
        self.messages_collection = self.db['chat_messages']
        self.users_collection = self.db['user_profiles']
        self.summaries_collection = self.db['conversation_summaries']
        self.sessions_collection = self.db['chat_sessions']
        self.activities_collection = self.db['user_activities']
        self.claim_guidance_collection = self.db['claim_guidance_messages']
        self.policy_applications_collection = self.db['policy_applications']
        self.policy_analysis_collection = self.db['policy_analysis']  # Added for gap analysis
        self.insurance_reports_collection = self.db['insurance_reports']  # For RAG queries
        self.backup_messages_collection = self.db['backup_chat_messages']
        self.backup_summaries_collection = self.db['backup_conversation_summaries']
        self.backup_claim_guidance_collection = self.db['backup_claim_guidance_messages']
        self.chat_backup_logs_collection = self.db['chat_backup_logs']
        self.app_versions_collection = self.db['app_versions']
        self.contact_support_collection = self.db['contact_support']
        self.contact_support_history_collection = self.db['contact_support_history']

        # Create indexes for better performance
        self._create_indexes()
        self._create_backup_indexes()
        
        # Configuration
        self.max_context_window = 20
        self.max_messages_per_session = 1000
        
        logger.info(" MongoDB Chat Manager initialized successfully")
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Messages collection indexes
            self.messages_collection.create_index([("session_id", 1), ("timestamp", -1)])
            self.messages_collection.create_index([("user_id", 1), ("timestamp", -1)])

            # Try to create unique indexes, skip if already exists with different spec
            try:
                self.messages_collection.create_index([("message_id", 1)], unique=True)
            except Exception as idx_err:
                if "IndexKeySpecsConflict" in str(idx_err) or "86" in str(idx_err):
                    logger.warning(f"Index message_id already exists, skipping...")
                else:
                    raise

            # User profiles indexes
            try:
                self.users_collection.create_index([("user_id", 1)], unique=True)
            except Exception as idx_err:
                if "IndexKeySpecsConflict" in str(idx_err) or "86" in str(idx_err):
                    logger.warning(f"Index user_id already exists, skipping...")
                else:
                    raise
            
            # Summaries collection indexes
            self.summaries_collection.create_index([("session_id", 1)])
            self.summaries_collection.create_index([("user_id", 1), ("created_at", -1)])
            
            # Sessions collection indexes
            try:
                self.sessions_collection.create_index([("session_id", 1)], unique=True)
            except Exception as idx_err:
                if "IndexKeySpecsConflict" in str(idx_err) or "86" in str(idx_err):
                    logger.warning(f"Index session_id already exists, skipping...")
                else:
                    raise
            self.sessions_collection.create_index([("user_id", 1), ("created_at", -1)])
            
            # Activities collection indexes
            self.activities_collection.create_index([("user_id", 1), ("timestamp", -1)])
            self.activities_collection.create_index([("session_id", 1), ("timestamp", -1)])
            self.activities_collection.create_index([("activity_type", 1), ("timestamp", -1)])

            # Claim guidance indexes
            self.claim_guidance_collection.create_index([("user_id", 1), ("timestamp", -1)])
            self.claim_guidance_collection.create_index([("session_id", 1)])
            self.claim_guidance_collection.create_index([("guidance_type", 1)])

            # Policy applications indexes
            self.policy_applications_collection.create_index([("user_id", 1), ("policy_id", 1)])
            self.policy_applications_collection.create_index([("session_id", 1)])
            try:
                self.policy_applications_collection.create_index([("application_id", 1)], unique=True)
            except Exception as idx_err:
                if "IndexKeySpecsConflict" in str(idx_err) or "86" in str(idx_err):
                    logger.warning(f"Index application_id already exists, skipping...")
                else:
                    raise
            self.policy_applications_collection.create_index([("created_at", -1)])
            self.policy_applications_collection.create_index([("status", 1)])

            # App versions indexes
            self.app_versions_collection.create_index([("platform", 1), ("version_number", -1)])
            try:
                self.app_versions_collection.create_index([("version_id", 1)], unique=True)
            except Exception as idx_err:
                if "IndexKeySpecsConflict" in str(idx_err) or "86" in str(idx_err):
                    logger.warning(f"Index version_id already exists, skipping...")
                else:
                    raise
            self.app_versions_collection.create_index([("status", 1), ("release_date", -1)])
            self.app_versions_collection.create_index([("minimum_supported", 1), ("platform", 1)])

            # Insurance reports indexes (for RAG queries)
            self.insurance_reports_collection.create_index([("user_id", 1), ("created_at", -1)])
            self.insurance_reports_collection.create_index([("session_id", 1)])
            try:
                self.insurance_reports_collection.create_index([("report_id", 1)], unique=True)
            except Exception as idx_err:
                if "IndexKeySpecsConflict" in str(idx_err) or "86" in str(idx_err):
                    logger.warning(f"Index report_id already exists, skipping...")
                else:
                    raise

            logger.info(" MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    def _create_backup_indexes(self):
        """Create indexes for backup collections"""
        try:
            # Backup messages indexes
            self.backup_messages_collection.create_index([("user_id", 1), ("backup_timestamp", -1)])
            self.backup_messages_collection.create_index([("original_session_id", 1)])
            self.backup_messages_collection.create_index([("backup_id", 1)])
            
            # Backup summaries indexes
            self.backup_summaries_collection.create_index([("user_id", 1), ("backup_timestamp", -1)])
            self.backup_summaries_collection.create_index([("backup_id", 1)])
            
            # Backup claim guidance indexes
            self.backup_claim_guidance_collection.create_index([("user_id", 1), ("backup_timestamp", -1)])
            self.backup_claim_guidance_collection.create_index([("backup_id", 1)])
            
            # Backup logs indexes
            self.chat_backup_logs_collection.create_index([("user_id", 1), ("backup_timestamp", -1)])
            self.chat_backup_logs_collection.create_index([("backup_id", 1)], unique=True)
            
        except Exception as e:
            logger.error(f"Error creating backup indexes: {e}")
    
    def log_user_activity(self, user_id: int, session_id: str, activity_type: str,
                          phone: str = None, ip_address: str = None, 
                          user_agent: str = None, metadata: Dict[str, Any] = None):
        """Log user activity (login/logout/chat)"""
        try:
            activity = UserActivity(
                user_id=user_id,
                session_id=session_id,
                activity_type=activity_type,
                phone=phone,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            self.activities_collection.insert_one(activity.to_dict())
            logger.info(f"Logged {activity_type} activity for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error logging user activity: {e}")
    
    def get_user_login_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user login statistics"""
        try:
            # Count login activities
            login_count = self.activities_collection.count_documents({
                "user_id": user_id,
                "activity_type": "login"
            })
            
            # Get last login
            last_login = self.activities_collection.find_one(
                {"user_id": user_id, "activity_type": "login"},
                sort=[("timestamp", -1)]
            )
            
            # Get first login
            first_login = self.activities_collection.find_one(
                {"user_id": user_id, "activity_type": "login"},
                sort=[("timestamp", 1)]
            )
            
            # Count unique days active
            pipeline = [
                {"$match": {"user_id": user_id, "activity_type": {"$in": ["login", "chat"]}}},
                {"$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "count": {"$sum": 1}
                }},
                {"$count": "unique_days"}
            ]
            
            unique_days_result = list(self.activities_collection.aggregate(pipeline))
            unique_days = unique_days_result[0]['unique_days'] if unique_days_result else 0
            
            return {
                "user_id": user_id,
                "total_logins": login_count,
                "last_login": last_login['timestamp'].isoformat() if last_login else None,
                "first_login": first_login['timestamp'].isoformat() if first_login else None,
                "unique_active_days": unique_days,
                "last_login_phone": last_login.get('phone') if last_login else None
            }
            
        except Exception as e:
            logger.error(f"Error getting user login stats: {e}")
            return {"user_id": user_id, "error": str(e)}
    
    def get_user_chat_history_across_sessions(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for user across all sessions (persistent history)"""
        try:
            cursor = self.messages_collection.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit)
            
            messages = list(cursor)
            
            # Convert ObjectId and datetime to strings
            for msg in messages:
                msg['_id'] = str(msg['_id'])
                msg['timestamp'] = msg['timestamp'].isoformat()
            
            # Reverse to get chronological order
            messages.reverse()
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting user chat history: {e}")
            return []
    
    def get_user_activity_timeline(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get user activity timeline for the last N days"""
        try:
            start_date = get_ist_now() - timedelta(days=days)
            
            cursor = self.activities_collection.find(
                {
                    "user_id": user_id,
                    "timestamp": {"$gte": start_date}
                }
            ).sort("timestamp", -1)
            
            activities = list(cursor)
            
            # Convert ObjectId and datetime to strings
            for activity in activities:
                activity['_id'] = str(activity['_id'])
                activity['timestamp'] = activity['timestamp'].isoformat()
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting user activity timeline: {e}")
            return []

    def generate_message_id(self, session_id: str, content: str) -> str:
        """Generate unique message ID"""
        timestamp = get_ist_now().isoformat()
        raw_id = f"{session_id}_{content[:50]}_{timestamp}"
        return hashlib.md5(raw_id.encode()).hexdigest()[:16]
    
    def add_message(self, session_id: str, user_id: int, role: str, content: str,
               intent: str = None, context: Dict[str, Any] = None,
               metadata: Dict[str, Any] = None, language: str = 'en',
               response_data: Dict[str, Any] = None) -> str:
        """Add a new message to the conversation"""
        try:
            # Validate content is not empty
            if not content or not str(content).strip():
                logger.warning(f"Skipping empty message for session {session_id}, user {user_id}")
                return ""

            # Clean the content
            clean_content = str(content).strip()

            message_id = self.generate_message_id(session_id, clean_content)

            message = ChatMessage(
                message_id=message_id,
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=clean_content,  # Use cleaned content
                intent=intent,
                context=context or {},
                metadata=metadata or {},
                language=language,
                response_data=response_data
            )
            
            # Insert message into MongoDB
            result = self.messages_collection.insert_one(message.to_dict())
            
            # Log chat activity for users
            if role == 'user':
                self.log_user_activity(user_id, session_id, 'chat', 
                                    metadata={'message_content_preview': clean_content[:50]})
            
            # Update session info
            self._update_session_info(session_id, user_id)
            
            # Check if we need to create a summary (every 50 messages)
            message_count = self.messages_collection.count_documents({"session_id": session_id})
            if message_count % 50 == 0:
                self._generate_conversation_summary(session_id, user_id)
            
            logger.info(f"Added {role} message to session {session_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return ""
    
    def get_conversation_history(self, session_id: str, limit: int = None) -> List[ChatMessage]:
        """Get conversation history for a session"""
        try:
            query = {"session_id": session_id}
            
            if limit:
                cursor = self.messages_collection.find(query).sort("timestamp", -1).limit(limit)
                messages = list(cursor)
                messages.reverse()  # Return in chronological order
            else:
                cursor = self.messages_collection.find(query).sort("timestamp", 1)
                messages = list(cursor)
            
            return [self._dict_to_message(msg) for msg in messages]
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def get_context_window(self, session_id: str) -> Dict[str, Any]:
        """Get contextual information for generating responses"""
        try:
            # Get recent messages
            recent_messages = self.get_conversation_history(session_id, self.max_context_window)
            
            # Get user profile
            user_profile = self.get_user_profile(session_id)
            
            # Get conversation summary if available
            summary = self.get_latest_conversation_summary(session_id)
            
            # Extract context information
            recent_intents = []
            recent_topics = []
            conversation_flow = []
            
            for msg in recent_messages[-10:]:  # Last 10 messages
                if msg.intent:
                    recent_intents.append(msg.intent)
                if msg.context and msg.context.get('topics'):
                    recent_topics.extend(msg.context['topics'])
                
                conversation_flow.append({
                    'role': msg.role,
                    'content': msg.content[:100],  # Truncate for context
                    'intent': msg.intent,
                    'timestamp': msg.timestamp.isoformat()
                })
            
            context = {
                'recent_messages': [msg.to_dict() for msg in recent_messages],
                'conversation_flow': conversation_flow,
                'recent_intents': list(set(recent_intents)),
                'recent_topics': list(set(recent_topics)),
                'user_context': user_profile.to_dict() if user_profile else {},
                'conversation_length': len(recent_messages),
                'summary': summary.to_dict() if summary else None,
                'last_user_message': recent_messages[-1].content if recent_messages and recent_messages[-1].role == 'user' else None,
                'last_assistant_message': None
            }
            
            # Find last assistant message
            for msg in reversed(recent_messages):
                if msg.role == 'assistant':
                    context['last_assistant_message'] = msg.content
                    break
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting context window: {e}")
            return {}
    
    def get_contextual_prompt(self, session_id: str, current_query: str) -> str:
        """Generate contextual prompt including conversation history"""
        try:
            context = self.get_context_window(session_id)
            
            # Build contextual prompt
            prompt_parts = []
            
            # Add conversation context
            if context.get('recent_messages'):
                prompt_parts.append("Previous conversation context:")
                for msg in context['recent_messages'][-5:]:  # Last 5 messages
                    role = "User" if msg['role'] == 'user' else "Assistant"
                    prompt_parts.append(f"{role}: {msg['content']}")
                prompt_parts.append("")
            
            # Add user context
            if context.get('user_context') and context['user_context'].get('preferences'):
                user_info = []
                preferences = context['user_context']['preferences']
                for key, value in preferences.items():
                    user_info.append(f"{key}: {value}")
                if user_info:
                    prompt_parts.append(f"User Information: {', '.join(user_info)}")
                    prompt_parts.append("")
            
            # Add recent topics/intents
            if context.get('recent_intents'):
                prompt_parts.append(f"Recent discussion topics: {', '.join(context['recent_intents'])}")
                prompt_parts.append("")
            
            # Add conversation summary if available
            if context.get('summary'):
                prompt_parts.append(f"Conversation summary: {context['summary']['summary_text']}")
                prompt_parts.append("")
            
            # Add current query
            prompt_parts.append(f"Current User Query: {current_query}")
            prompt_parts.append("")
            prompt_parts.append("Please provide a contextual response considering the conversation history above.")
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Error generating contextual prompt: {e}")
            return current_query
    
    def update_user_profile(self, session_id: str, user_id: int, profile_updates: Dict[str, Any]):
        """Update or create user profile - now user-centric"""
        try:
            # Find profile by user_id only (not session_id)
            existing_profile = self.users_collection.find_one({"user_id": user_id})
            
            current_time = get_ist_now()
            
            if existing_profile:
                # Update existing profile
                update_data = {
                    "$set": {
                        "updated_at": current_time,
                        "last_session_id": session_id,  # Track last session
                        **{f"preferences.{k}": v for k, v in profile_updates.items()}
                    }
                }
                
                if "interested_in" in profile_updates:
                    update_data["$addToSet"] = {"interests": profile_updates["interested_in"]}
                
                self.users_collection.update_one(
                    {"user_id": user_id},  # Only match by user_id
                    update_data
                )
            else:
                # Create new profile
                profile = {
                    "user_id": user_id,
                    "last_session_id": session_id,  # Track sessions
                    "session_history": [session_id],  # Keep history
                    "preferences": profile_updates,
                    "interests": [profile_updates.get("interested_in")] if profile_updates.get("interested_in") else [],
                    "language_preference": 'en',
                    "interaction_patterns": {},
                    "created_at": current_time,
                    "updated_at": current_time
                }
                
                self.users_collection.insert_one(profile)
            
            # Add session to history if not already there
            self.users_collection.update_one(
                {"user_id": user_id},
                {"$addToSet": {"session_history": session_id}}
            )
            
            logger.info(f"Updated user profile for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
    
    def get_user_profile(self, session_id: str = None, user_id: int = None) -> Optional[UserProfile]:
        """Get user profile by user_id (session_id optional for backwards compatibility)"""
        try:
            # If user_id provided directly, use it
            if user_id:
                profile_data = self.users_collection.find_one({"user_id": user_id})
            # Otherwise try to get user_id from session
            elif session_id:
                try:
                    from database_storage.simple_redis_config import get_session
                    session_data = get_session(session_id)
                    if session_data and session_data.get('user_id'):
                        user_id = session_data.get('user_id')
                        profile_data = self.users_collection.find_one({"user_id": user_id})
                    else:
                        return None
                except ImportError:
                    # Fallback if redis not available
                    return None
            else:
                return None
            
            if profile_data:
                # Convert to UserProfile, mapping correctly
                return UserProfile(
                    user_id=profile_data['user_id'],
                    session_id=profile_data.get('last_session_id', session_id),
                    preferences=profile_data.get('preferences', {}),
                    interests=profile_data.get('interests', []),
                    language_preference=profile_data.get('language_preference', 'en'),
                    interaction_patterns=profile_data.get('interaction_patterns', {}),
                    created_at=profile_data.get('created_at', get_ist_now()),
                    updated_at=profile_data.get('updated_at', get_ist_now())
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def search_conversation_history(self, session_id: str, search_query: str, limit: int = 5) -> List[ChatMessage]:
        """Search through conversation history with input sanitization"""
        try:
            # Sanitize search query to prevent ReDoS attacks
            sanitized_query = sanitize_regex_input(search_query, max_length=200)

            # Validate limit
            validated_limit = validate_limit(limit, max_limit=100, default=5)

            query = {
                "session_id": session_id,
                "$or": [
                    {"content": {"$regex": sanitized_query, "$options": "i"}},
                    {"intent": {"$regex": sanitized_query, "$options": "i"}}
                ]
            }

            cursor = self.messages_collection.find(query).sort("timestamp", -1).limit(validated_limit)
            messages = list(cursor)

            return [self._dict_to_message(msg) for msg in messages]

        except Exception as e:
            logger.error(f"Error searching conversation history: {e}")
            return []
    
    def get_conversation_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics about the conversation"""
        try:
            # Get all messages for the session
            messages = list(self.messages_collection.find({"session_id": session_id}))
            
            if not messages:
                return {}
            
            user_messages = [msg for msg in messages if msg['role'] == 'user']
            assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
            
            # Calculate analytics
            total_messages = len(messages)
            start_time = min(msg['timestamp'] for msg in messages)
            end_time = max(msg['timestamp'] for msg in messages)
            conversation_duration = (end_time - start_time).total_seconds() / 60  # minutes
            
            # Intent analysis
            intents = [msg['intent'] for msg in messages if msg.get('intent')]
            intent_counts = {}
            for intent in intents:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            # Language analysis
            languages = [msg.get('language', 'en') for msg in messages]
            language_counts = {}
            for lang in languages:
                language_counts[lang] = language_counts.get(lang, 0) + 1
            
            analytics = {
                'session_id': session_id,
                'total_messages': total_messages,
                'user_messages': len(user_messages),
                'assistant_messages': len(assistant_messages),
                'conversation_duration_minutes': conversation_duration,
                'most_common_intents': sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                'language_distribution': language_counts,
                'average_message_length': sum(len(msg['content']) for msg in messages) / total_messages,
                'session_start': start_time.isoformat(),
                'last_activity': end_time.isoformat(),
                'unique_days_active': len(set(msg['timestamp'].date() for msg in messages))
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting conversation analytics: {e}")
            return {}
    
    def clear_conversation(self, session_id: str) -> bool:
        """Clear conversation history for a session"""
        try:
            # Delete messages
            self.messages_collection.delete_many({"session_id": session_id})
            
            # Delete summaries
            self.summaries_collection.delete_many({"session_id": session_id})
            
            # Update session info
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"cleared_at": get_ist_now()}}
            )
            
            logger.info(f"Cleared conversation for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False
    
    def _update_session_info(self, session_id: str, user_id: int):
        """Update or create session information"""
        try:
            current_time = get_ist_now()
            
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "last_activity": current_time
                    },
                    "$setOnInsert": {
                        "created_at": current_time
                    }
                },
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error updating session info: {e}")
    
    def _generate_conversation_summary(self, session_id: str, user_id: int):
        """Generate a summary of the conversation"""
        try:
            # Get recent messages for summarization
            recent_messages = self.get_conversation_history(session_id, 50)
            
            if len(recent_messages) < 10:  # Not enough messages to summarize
                return
            
            # Extract key information
            key_topics = set()
            user_intents = set()
            important_entities = {}
            
            for msg in recent_messages:
                if msg.intent:
                    user_intents.add(msg.intent)
                if msg.context and msg.context.get('topics'):
                    key_topics.update(msg.context['topics'])
            
            # Create summary text (this could be enhanced with AI summarization)
            summary_text = f"Conversation with {len(recent_messages)} messages discussing "
            summary_text += f"{', '.join(list(key_topics)[:5])} " if key_topics else "general topics "
            summary_text += f"with focus on {', '.join(list(user_intents)[:3])}" if user_intents else ""
            
            # Create summary object
            summary = ConversationSummary(
                session_id=session_id,
                user_id=user_id,
                summary_text=summary_text,
                key_topics=list(key_topics),
                user_intents=list(user_intents),
                important_entities=important_entities,
                conversation_length=len(recent_messages),
                start_time=recent_messages[0].timestamp,
                end_time=recent_messages[-1].timestamp,
                created_at=get_ist_now()
            )
            
            # Store summary
            self.summaries_collection.insert_one(summary.to_dict())
            logger.info(f"Generated summary for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
    
    def get_latest_conversation_summary(self, session_id: str) -> Optional[ConversationSummary]:
        """Get the latest conversation summary"""
        try:
            summary_data = self.summaries_collection.find_one(
                {"session_id": session_id},
                sort=[("created_at", -1)]
            )
            
            if summary_data:
                return ConversationSummary(**{k: v for k, v in summary_data.items() if k != '_id'})
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return None
    
    def _dict_to_message(self, msg_dict: Dict[str, Any]) -> ChatMessage:
        """Convert dictionary to ChatMessage object"""
        return ChatMessage(
            message_id=msg_dict['message_id'],
            session_id=msg_dict['session_id'],
            user_id=msg_dict['user_id'],
            role=msg_dict['role'],
            content=msg_dict['content'],
            intent=msg_dict.get('intent'),
            context=msg_dict.get('context', {}),
            metadata=msg_dict.get('metadata', {}),
            timestamp=msg_dict['timestamp'],
            language=msg_dict.get('language', 'en'),
            response_data=msg_dict.get('response_data')
        )
    
    def get_user_conversation_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive stats for a user across all sessions"""
        try:
            # Get all messages for the user
            user_messages = list(self.messages_collection.find({"user_id": user_id}))
            
            if not user_messages:
                return {"user_id": user_id, "total_messages": 0}
            
            # Get unique sessions
            unique_sessions = set(msg['session_id'] for msg in user_messages)
            
            # Calculate stats
            total_messages = len(user_messages)
            first_interaction = min(msg['timestamp'] for msg in user_messages)
            last_interaction = max(msg['timestamp'] for msg in user_messages)
            
            # Intent analysis
            intents = [msg['intent'] for msg in user_messages if msg.get('intent')]
            intent_counts = {}
            for intent in intents:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            # Language preference
            languages = [msg.get('language', 'en') for msg in user_messages]
            most_common_language = max(set(languages), key=languages.count)
            
            return {
                "user_id": user_id,
                "total_messages": total_messages,
                "total_sessions": len(unique_sessions),
                "first_interaction": first_interaction.isoformat(),
                "last_interaction": last_interaction.isoformat(),
                "most_common_intents": sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                "preferred_language": most_common_language,
                "average_messages_per_session": total_messages / len(unique_sessions),
                "active_days": len(set(msg['timestamp'].date() for msg in user_messages))
            }
            
        except Exception as e:
            logger.error(f"Error getting user conversation stats: {e}")
            return {"user_id": user_id, "error": str(e)}

    # ========== POLICY APPLICATION METHODS (FIXED) ==========
    
    def store_policy_application_answer(self, session_id: str, user_id: int, policy_id: str, 
                                       question_number: int, question_data: Dict, answer: str) -> bool:
        """Store individual answer for policy application"""
        try:
            application_id = f"APP_{policy_id}_{user_id}_{int(time.time())}"
            
            # Update or create application document
            self.policy_applications_collection.update_one(
                {
                    "user_id": user_id,
                    "policy_id": policy_id,
                    "session_id": session_id
                },
                {
                    "$set": {
                        f"answers.q_{question_number}": {
                            "question": question_data.get("question"),
                            "key": question_data.get("key"),
                            "type": question_data.get("type"),
                            "answer": answer,
                            "answered_at": get_ist_now(),
                            "question_number": question_number
                        },
                        "last_updated": get_ist_now(),
                        "status": "in_progress"
                    },
                    "$setOnInsert": {
                        "created_at": get_ist_now(),
                        "application_id": application_id
                    }
                },
                upsert=True
            )
            
            logger.info(f"Stored answer for question {question_number} in application for policy {policy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing policy application answer: {e}")
            return False

    def get_policy_application_data(self, user_id: int, policy_id: str, session_id: str = None) -> Dict:
        """Get all answers for a policy application"""
        try:
            query = {
                "user_id": user_id,
                "policy_id": policy_id
            }
            
            if session_id:
                query["session_id"] = session_id
            
            # Get the most recent application
            application = self.policy_applications_collection.find_one(
                query,
                sort=[("created_at", -1)]
            )
            
            if application:
                # Convert ObjectId and datetime to strings
                application["_id"] = str(application["_id"])
                application["created_at"] = application["created_at"].isoformat()
                application["last_updated"] = application["last_updated"].isoformat()
                
                # Format answers for display
                formatted_answers = {}
                if "answers" in application:
                    for key, value in application["answers"].items():
                        if isinstance(value, dict):
                            value["answered_at"] = value["answered_at"].isoformat() if "answered_at" in value else None
                            formatted_answers[key] = value
                    application["answers"] = formatted_answers

                # print('2233333333',application)
                
                return application
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting policy application data: {e}")
            return {}

    def update_policy_application_answer(self, application_id: str, question_number: int, 
                                        new_answer: str) -> bool:
        """Update a specific answer in the application"""
        try:
            result = self.policy_applications_collection.update_one(
                {"application_id": application_id},
                {
                    "$set": {
                        f"answers.q_{question_number}.answer": new_answer,
                        f"answers.q_{question_number}.updated_at": get_ist_now(),
                        f"answers.q_{question_number}.is_edited": True,
                        "last_updated": get_ist_now()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated answer for question {question_number} in application {application_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating policy application answer: {e}")
            return False

    def complete_policy_application(self, application_id: str, submission_data: Dict = None) -> bool:
        """Mark application as completed and store submission details"""
        try:
            update_data = {
                "status": "completed",
                "completed_at": get_ist_now(),
                "last_updated": get_ist_now()
            }
            
            if submission_data:
                update_data["submission_details"] = submission_data
            
            result = self.policy_applications_collection.update_one(
                {"application_id": application_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Completed application {application_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error completing policy application: {e}")
            return False

    def get_all_user_policy_applications(self, user_id: int) -> List[Dict]:
        """Get all policy applications for a user"""
        try:
            applications = list(self.policy_applications_collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1))
            
            for app in applications:
                app["_id"] = str(app["_id"])
                app["created_at"] = app["created_at"].isoformat()
                app["last_updated"] = app["last_updated"].isoformat()
                if "completed_at" in app:
                    app["completed_at"] = app["completed_at"].isoformat()
            
            return applications
            
        except Exception as e:
            logger.error(f"Error getting user policy applications: {e}")
            return []
        
    # App Version Management Methods
    def create_app_version(self, version_data: Dict[str, Any]) -> str:
        """Create a new app version entry"""
        try:
            # Generate version_id if not provided
            if 'version_id' not in version_data:
                platform = version_data.get('platform', 'unknown')
                version_number = version_data.get('version_number', '1.0.0')
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                version_data['version_id'] = f"{platform}_{version_number}_{timestamp}"
            
            app_version = AppVersion(**version_data)
            result = self.app_versions_collection.insert_one(app_version.to_dict())
            
            logger.info(f" Created app version: {app_version.version_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f" Error creating app version: {e}")
            raise Exception(f"Failed to create app version: {str(e)}")

    def get_latest_app_versions(self) -> Dict[str, Any]:
        """Get latest versions for both iOS and Android"""
        try:
            latest_versions = {}
            
            for platform in ['ios', 'android']:
                latest = self.app_versions_collection.find_one(
                    {"platform": platform, "status": "active"},
                    sort=[("release_date", -1)]
                )
                
                if latest:
                    latest["_id"] = str(latest["_id"])
                    latest["release_date"] = latest["release_date"].isoformat()
                    latest["created_at"] = latest["created_at"].isoformat()
                    latest["updated_at"] = latest["updated_at"].isoformat()
                    latest_versions[platform] = latest
            
            return latest_versions
            
        except Exception as e:
            logger.error(f" Error getting latest app versions: {e}")
            return {}

    def get_app_version_by_platform(self, platform: str, include_deprecated: bool = False) -> List[Dict]:
        """Get all versions for a specific platform"""
        try:
            query = {"platform": platform}
            if not include_deprecated:
                query["status"] = "active"
            
            versions = list(self.app_versions_collection.find(query).sort("release_date", -1))
            
            for version in versions:
                version["_id"] = str(version["_id"])
                version["release_date"] = version["release_date"].isoformat()
                version["created_at"] = version["created_at"].isoformat()
                version["updated_at"] = version["updated_at"].isoformat()
            
            return versions
            
        except Exception as e:
            logger.error(f" Error getting versions for {platform}: {e}")
            return []

    def check_version_compatibility(self, platform: str, version_number: str) -> Dict[str, Any]:
        """Check if a specific version is supported"""
        try:
            # Get the specific version
            user_version = self.app_versions_collection.find_one({
                "platform": platform,
                "version_number": version_number
            })
            
            # Get latest version
            latest_version = self.app_versions_collection.find_one(
                {"platform": platform, "status": "active"},
                sort=[("release_date", -1)]
            )
            
            if not latest_version:
                return {
                    "supported": False,
                    "message": f"No active versions found for {platform}",
                    "latest_version": None
                }
            
            result = {
                "platform": platform,
                "user_version": version_number,
                "latest_version": latest_version["version_number"],
                "is_latest": user_version and user_version["version_number"] == latest_version["version_number"],
                "supported": True,
                "force_update": False,
                "message": "Version is supported"
            }
            
            if user_version:
                result["supported"] = user_version.get("minimum_supported", True)
                result["force_update"] = user_version.get("force_update", False)
                
                if not result["supported"]:
                    result["message"] = "This version is no longer supported. Please update to continue."
                elif result["force_update"]:
                    result["message"] = "A critical update is required. Please update immediately."
                elif not result["is_latest"]:
                    result["message"] = "A newer version is available with improvements and bug fixes."
            else:
                result["supported"] = False
                result["message"] = "Unknown version. Please update to the latest version."
            
            return result
            
        except Exception as e:
            logger.error(f" Error checking version compatibility: {e}")
            return {
                "supported": False,
                "message": "Error checking version compatibility",
                "error": str(e)
            }

    def update_app_version(self, version_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing app version"""
        try:
            update_data["updated_at"] = get_ist_now()
            
            result = self.app_versions_collection.update_one(
                {"version_id": version_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f" Updated app version: {version_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f" Error updating app version: {e}")
            return False

    def deprecate_app_version(self, version_id: str, reason: str = None) -> bool:
        """Mark an app version as deprecated"""
        try:
            update_data = {
                "status": "deprecated",
                "minimum_supported": False,
                "updated_at": get_ist_now()
            }
            
            if reason:
                update_data["deprecation_reason"] = reason
                update_data["deprecated_at"] = get_ist_now()
            
            result = self.app_versions_collection.update_one(
                {"version_id": version_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f" Deprecated app version: {version_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f" Error deprecating app version: {e}")
            return False

    # Insurance Report Storage Methods (for RAG queries)

    def store_insurance_report(self, user_id: int, session_id: str, report_data: Dict[str, Any]) -> str:
        """
        Store insurance gap analysis report for RAG queries

        Args:
            user_id: User's ID
            session_id: Chat session ID where report was generated
            report_data: Complete report data from insurance analysis

        Returns:
            str: Report ID (MongoDB ObjectId as string)
        """
        try:
            import secrets

            current_time = get_ist_now()
            report_id = f"report_{user_id}_{int(time.time())}_{secrets.token_hex(4)}"

            # Structure report for efficient RAG queries
            report_document = {
                "report_id": report_id,
                "user_id": user_id,
                "session_id": session_id,
                "created_at": current_time,
                "updated_at": current_time,

                # Report URL and metadata
                "report_url": report_data.get("report_url"),
                "report_type": report_data.get("report_type", "gap_analysis"),

                # Core data for RAG (extracted at root level for easy querying)
                "protection_score": report_data.get("protection_score"),
                "current_coverage": report_data.get("current_coverage") or report_data.get("coverage_details", {}).get("current_coverage"),
                "recommended_coverage": report_data.get("recommended_coverage") or report_data.get("coverage_details", {}).get("recommended_coverage"),
                "coverage_gaps": report_data.get("coverage_gaps", []),
                "recommendations": report_data.get("recommendations", []),

                # Additional structured data
                "premium_estimates": report_data.get("premium_estimates", {}),
                "category_scores": report_data.get("category_scores", {}),
                "policy_details": report_data.get("policy_details", {}),
                "policy_info": report_data.get("policy_info", {}),
                "analysis_results": report_data.get("analysis_results", ""),

                # Full data backup (everything)
                "data": report_data
            }

            result = self.insurance_reports_collection.insert_one(report_document)

            logger.info(f"✓ Stored insurance report {report_id} for user {user_id}")
            logger.info(f"  Protection Score: {report_document.get('protection_score')}")
            logger.info(f"  Report URL: {report_document.get('report_url')}")

            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"✗ Error storing insurance report for user {user_id}: {e}")
            raise Exception(f"Failed to store insurance report: {str(e)}")

    def get_latest_insurance_report(self, user_id: int, hours: int = 24) -> Optional[Dict[str, Any]]:
        """
        Get user's most recent insurance report within specified time window

        Args:
            user_id: User's ID
            hours: Time window in hours (default 24)

        Returns:
            Dict with report data or None if not found
        """
        try:
            cutoff_time = get_ist_now() - timedelta(hours=hours)

            report = self.insurance_reports_collection.find_one(
                {
                    "user_id": user_id,
                    "created_at": {"$gte": cutoff_time}
                },
                sort=[("created_at", -1)]
            )

            if report:
                # Remove MongoDB _id from return
                report.pop('_id', None)
                logger.info(f"✓ Found insurance report for user {user_id} (created {report.get('created_at')})")
                return report

            logger.info(f"✗ No insurance report found for user {user_id} in last {hours} hours")
            return None

        except Exception as e:
            logger.error(f"✗ Error retrieving insurance report for user {user_id}: {e}")
            return None

    # Add these methods to the MongoDBChatManager class in mongodb_chat_manager.py

    def create_new_chat_session(self, user_id: int, session_id: str = None, title: str = "New Chat") -> Dict[str, Any]:
        """Create a new chat session for user"""
        try:
            if not session_id:
                session_id = f"chat_{user_id}_{int(time.time())}_{secrets.token_hex(4)}"
            
            current_time = get_ist_now()
            
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "title": title,
                "created_at": current_time,
                "last_activity": current_time,
                "message_count": 0,
                "active": True,
                "deleted": False,
                "is_archived": False,
                "tags": [],
                "first_message_preview": None
            }
            
            # Insert into sessions collection
            self.sessions_collection.insert_one(session_data)
            
            logger.info(f" Created new chat session {session_id} for user {user_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "title": title,
                "created_at": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating new chat session: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_user_chat_sessions(self, user_id: int, limit: int = 50, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user with summaries"""
        try:
            query = {
                "user_id": user_id,
                "deleted": False
            }
            
            if not include_archived:
                query["is_archived"] = False
            
            # Get sessions sorted by last activity
            sessions = list(self.sessions_collection.find(query).sort("last_activity", -1).limit(limit))
            
            result = []
            for session in sessions:
                session_id = session.get("session_id")
                
                # Get message count
                message_count = self.messages_collection.count_documents({"session_id": session_id})
                
                # Get first user message for preview
                first_message = self.messages_collection.find_one(
                    {"session_id": session_id, "role": "user"},
                    sort=[("timestamp", 1)]
                )
                
                # Get last message
                last_message = self.messages_collection.find_one(
                    {"session_id": session_id},
                    sort=[("timestamp", -1)]
                )
                
                # Generate title if not set or still a default placeholder
                title = session.get("title", "New Chat")
                default_titles = {"New Chat", "WebSocket Chat", "Chat Session", "Auto Chat"}
                if title in default_titles and first_message:
                    # Use first message as title (truncated)
                    title = first_message.get("content", "")[:50]
                    if len(first_message.get("content", "")) > 50:
                        title += "..."
                
                session_summary = {
                    "session_id": session_id,
                    "title": title,
                    "created_at": session.get("created_at").isoformat(),
                    "last_activity": session.get("last_activity").isoformat(),
                    "message_count": message_count,
                    "first_message_preview": first_message.get("content", "")[:100] if first_message else None,
                    "last_message_preview": last_message.get("content", "")[:100] if last_message else None,
                    "is_archived": session.get("is_archived", False),
                    "tags": session.get("tags", [])
                }
                
                result.append(session_summary)
            
            logger.info(f"Retrieved {len(result)} chat sessions for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting user chat sessions: {e}")
            return []

    def load_chat_session(self, session_id: str, message_limit: int = 100) -> Dict[str, Any]:
        """Load a specific chat session with messages"""
        try:
            # Get session info
            session = self.sessions_collection.find_one({"session_id": session_id})
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            # Get messages
            messages = list(self.messages_collection.find(
                {"session_id": session_id}
            ).sort("timestamp", 1).limit(message_limit))
            
            # Convert ObjectId and datetime to strings
            for msg in messages:
                msg['_id'] = str(msg['_id'])
                msg['timestamp'] = msg['timestamp'].isoformat()
            
            # Update last activity
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"last_activity": get_ist_now()}}
            )
            
            session['_id'] = str(session['_id'])
            session['created_at'] = session['created_at'].isoformat()
            session['last_activity'] = session['last_activity'].isoformat()
            
            return {
                "success": True,
                "session": session,
                "messages": messages,
                "total_messages": len(messages)
            }
            
        except Exception as e:
            logger.error(f"Error loading chat session: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_chat_title(self, session_id: str, new_title: str) -> bool:
        """Update chat session title"""
        try:
            result = self.sessions_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "title": new_title,
                        "updated_at": get_ist_now()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating chat title: {e}")
            return False

    def delete_chat_session(self, session_id: str, hard_delete: bool = False) -> bool:
        """Delete or archive a chat session"""
        try:
            if hard_delete:
                # Permanently delete
                self.messages_collection.delete_many({"session_id": session_id})
                self.summaries_collection.delete_many({"session_id": session_id})
                self.sessions_collection.delete_one({"session_id": session_id})
            else:
                # Soft delete (mark as deleted)
                self.sessions_collection.update_one(
                    {"session_id": session_id},
                    {
                        "$set": {
                            "deleted": True,
                            "deleted_at": get_ist_now()
                        }
                    }
                )
            
            logger.info(f"Deleted chat session {session_id} (hard_delete={hard_delete})")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chat session: {e}")
            return False

    def archive_chat_session(self, session_id: str) -> bool:
        """Archive a chat session"""
        try:
            result = self.sessions_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "is_archived": True,
                        "archived_at": get_ist_now()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error archiving chat session: {e}")
            return False

    def search_chat_sessions(self, user_id: int, search_query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search through user's chat sessions with input sanitization"""
        try:
            # Validate and sanitize inputs
            validated_user_id = validate_user_id(user_id)
            sanitized_query = sanitize_regex_input(search_query, max_length=200)
            validated_limit = validate_limit(limit, max_limit=100, default=20)

            # Search in session titles and message content
            session_ids = set()

            # Search in messages
            messages = self.messages_collection.find({
                "user_id": validated_user_id,
                "content": {"$regex": sanitized_query, "$options": "i"}
            }).limit(validated_limit * 2)

            for msg in messages:
                session_ids.add(msg.get("session_id"))

            # Search in session titles
            sessions = self.sessions_collection.find({
                "user_id": validated_user_id,
                "title": {"$regex": sanitized_query, "$options": "i"},
                "deleted": False
            }).limit(validated_limit)
            
            for session in sessions:
                session_ids.add(session.get("session_id"))
            
            # Get full session data for matched sessions
            results = []
            for session_id in list(session_ids)[:limit]:
                session_data = self.load_chat_session(session_id, message_limit=5)
                if session_data.get("success"):
                    results.append({
                        "session_id": session_id,
                        "session_info": session_data.get("session"),
                        "matched_messages": session_data.get("messages", [])
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching chat sessions: {e}")
            return []
                



# Initialize MongoDB Chat Manager
try:
    mongodb_chat_manager = MongoDBChatManager()
    print("[OK] MongoDB Chat Manager initialized successfully")
except Exception as e:
    print(f"[ERROR] Error initializing MongoDB Chat Manager: {e}")
    mongodb_chat_manager = None

# Helper functions for easy integration
def add_user_message_to_mongodb(session_id: str, user_id: int, content: str, intent: str = None, 
                               context: Dict[str, Any] = None, language: str = 'en') -> str:
    """Add user message to MongoDB"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.add_message(session_id, user_id, 'user', content, intent, context, language=language)
    return ""

def add_assistant_message_to_mongodb(session_id: str, user_id: int, content: str, intent: str = None,
                                   context: Dict[str, Any] = None, language: str = 'en') -> str:
    """Add assistant message to MongoDB"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.add_message(session_id, user_id, 'assistant', content, intent, context, language=language)
    return ""

def get_conversation_context_from_mongodb(session_id: str) -> Dict[str, Any]:
    """Get conversation context from MongoDB"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.get_context_window(session_id)
    return {}

def get_contextual_prompt_from_mongodb(session_id: str, query: str) -> str:
    """Get contextual prompt from MongoDB"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.get_contextual_prompt(session_id, query)
    return query

def update_user_profile_in_mongodb(session_id: str, user_id: int, profile_data: Dict[str, Any]):
    """Update user profile in MongoDB"""
    if mongodb_chat_manager:
        mongodb_chat_manager.update_user_profile(session_id, user_id, profile_data)

def search_chat_history_in_mongodb(session_id: str, search_query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search chat history in MongoDB"""
    if mongodb_chat_manager:
        messages = mongodb_chat_manager.search_conversation_history(session_id, search_query, limit)
        return [msg.to_dict() for msg in messages]
    return []

def get_chat_analytics_from_mongodb(session_id: str) -> Dict[str, Any]:
    """Get chat analytics from MongoDB"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.get_conversation_analytics(session_id)
    return {}

def clear_chat_history_in_mongodb(session_id: str) -> bool:
    """Clear chat history in MongoDB"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.clear_conversation(session_id)
    return False

# New helper functions for user activity tracking
def log_user_login_activity(user_id: int, session_id: str, phone: str = None, 
                           ip_address: str = None, user_agent: str = None):
    """Log user login activity"""
    if mongodb_chat_manager:
        mongodb_chat_manager.log_user_activity(
            user_id, session_id, 'login', phone, ip_address, user_agent
        )

def log_user_logout_activity(user_id: int, session_id: str, 
                            ip_address: str = None, user_agent: str = None):
    """Log user logout activity"""
    if mongodb_chat_manager:
        mongodb_chat_manager.log_user_activity(
            user_id, session_id, 'logout', ip_address=ip_address, user_agent=user_agent
        )

def get_user_login_statistics(user_id: int) -> Dict[str, Any]:
    """Get user login statistics"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.get_user_login_stats(user_id)
    return {}

def get_user_persistent_chat_history(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get persistent chat history across sessions"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.get_user_chat_history_across_sessions(user_id, limit)
    return []

def get_user_activity_history(user_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """Get user activity timeline"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.get_user_activity_timeline(user_id, days)
    return []

# FIXED: Policy application helper functions
def store_policy_answer(session_id: str, user_id: int, policy_id: str, 
                        question_number: int, question_data: Dict, answer: str) -> bool:
    """Helper function to store policy application answer"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.store_policy_application_answer(
            session_id, user_id, policy_id, question_number, question_data, answer
        )
    return False

def get_policy_application(user_id: int, policy_id: str, session_id: str = None) -> Dict:
    """Helper function to get policy application data"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.get_policy_application_data(user_id, policy_id, session_id)
    return {}

def update_policy_answer(application_id: str, question_number: int, new_answer: str) -> bool:
    """Helper function to update policy answer"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.update_policy_application_answer(
            application_id, question_number, new_answer
        )
    return False

def complete_application(application_id: str, submission_data: Dict = None) -> bool:
    """Helper function to complete application"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.complete_policy_application(application_id, submission_data)
    return False

def backup_and_clear_user_chat_history(user_id: int, backup_reason: str = "user_requested") -> dict:
    """Backup user's chat history to backup collections and then clear active data"""
    if not mongodb_chat_manager:
        logger.warning("MongoDB not available for backup and clear")
        return {"success": False, "error": "MongoDB not available"}
    
    try:
        backup_timestamp = get_ist_now()
        backup_id = f"backup_{user_id}_{int(backup_timestamp.timestamp())}"
        
        # Step 1: Get all data to backup
        messages = list(mongodb_chat_manager.messages_collection.find({"user_id": user_id}))
        summaries = list(mongodb_chat_manager.summaries_collection.find({"user_id": user_id}))
        claim_messages = list(mongodb_chat_manager.claim_guidance_collection.find({"user_id": user_id}))
        
        backup_stats = {
            "messages_count": len(messages),
            "summaries_count": len(summaries),
            "claim_messages_count": len(claim_messages)
        }
        
        if backup_stats["messages_count"] == 0:
            return {
                "success": True,
                "message": "No chat history found to backup",
                "backup_stats": backup_stats,
                "backup_id": None
            }
        
        # Step 2: Backup messages
        if messages:
            backup_messages = []
            for msg in messages:
                backup_msg = msg.copy()
                backup_msg["backup_id"] = backup_id
                backup_msg["backup_timestamp"] = backup_timestamp
                backup_msg["backup_reason"] = backup_reason
                backup_msg["original_session_id"] = msg.get("session_id")
                backup_msg["original_message_id"] = msg.get("_id")
                # Remove original _id to avoid conflicts
                if "_id" in backup_msg:
                    del backup_msg["_id"]
                backup_messages.append(backup_msg)
            
            mongodb_chat_manager.backup_messages_collection.insert_many(backup_messages)
            logger.info(f"Backed up {len(backup_messages)} messages for user {user_id}")
        
        # Step 3: Backup summaries
        if summaries:
            backup_summaries = []
            for summary in summaries:
                backup_summary = summary.copy()
                backup_summary["backup_id"] = backup_id
                backup_summary["backup_timestamp"] = backup_timestamp
                backup_summary["backup_reason"] = backup_reason
                backup_summary["original_summary_id"] = summary.get("_id")
                if "_id" in backup_summary:
                    del backup_summary["_id"]
                backup_summaries.append(backup_summary)
            
            mongodb_chat_manager.backup_summaries_collection.insert_many(backup_summaries)
            logger.info(f"Backed up {len(backup_summaries)} summaries for user {user_id}")
        
        # Step 4: Backup claim guidance messages
        if claim_messages:
            backup_claims = []
            for claim in claim_messages:
                backup_claim = claim.copy()
                backup_claim["backup_id"] = backup_id
                backup_claim["backup_timestamp"] = backup_timestamp
                backup_claim["backup_reason"] = backup_reason
                backup_claim["original_claim_id"] = claim.get("_id")
                if "_id" in backup_claim:
                    del backup_claim["_id"]
                backup_claims.append(backup_claim)
            
            mongodb_chat_manager.backup_claim_guidance_collection.insert_many(backup_claims)
            logger.info(f"Backed up {len(backup_claims)} claim messages for user {user_id}")
        
        # Step 5: Create backup log entry
        backup_log = {
            "backup_id": backup_id,
            "user_id": user_id,
            "backup_timestamp": backup_timestamp,
            "backup_reason": backup_reason,
            "backup_stats": backup_stats,
            "backup_status": "completed",
            "unique_sessions_backed_up": len(set(msg.get("session_id") for msg in messages if msg.get("session_id"))),
            "date_range": {
                "first_message": min((msg.get("timestamp") for msg in messages if msg.get("timestamp")), default=None),
                "last_message": max((msg.get("timestamp") for msg in messages if msg.get("timestamp")), default=None)
            }
        }
        
        mongodb_chat_manager.chat_backup_logs_collection.insert_one(backup_log)
        
        # Step 6: Now clear the active data
        # Clear all messages for this user
        messages_result = mongodb_chat_manager.messages_collection.delete_many({"user_id": user_id})
        
        # Clear all conversation summaries for this user
        summaries_result = mongodb_chat_manager.summaries_collection.delete_many({"user_id": user_id})
        
        # Clear claim guidance messages for this user
        claim_result = mongodb_chat_manager.claim_guidance_collection.delete_many({"user_id": user_id})
        
        # Update all sessions for this user to mark as cleared
        sessions_result = mongodb_chat_manager.sessions_collection.update_many(
            {"user_id": user_id},
            {
                "$set": {
                    "chat_cleared_at": backup_timestamp,
                    "chat_history_status": "backed_up_and_cleared",
                    "backup_id": backup_id
                }
            }
        )
        
        # Update user profile to mark chat history as cleared
        profile_result = mongodb_chat_manager.users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "chat_history_cleared_at": backup_timestamp,
                    "last_chat_clear": backup_timestamp.isoformat(),
                    "last_backup_id": backup_id,
                    "chat_backup_count": 1,
                    "updated_at": backup_timestamp
                },
                "$push": {
                    "chat_backup_history": {
                        "backup_id": backup_id,
                        "backup_timestamp": backup_timestamp.isoformat(),
                        "backup_reason": backup_reason,
                        "backup_stats": backup_stats
                    }
                }
            }
        )
        
        logger.info(f"Backup and clear completed for user {user_id}")
        
        return {
            "success": True,
            "message": "Chat history backed up and cleared successfully",
            "backup_id": backup_id,
            "backup_stats": backup_stats,
            "cleared_stats": {
                "messages_cleared": messages_result.deleted_count,
                "summaries_cleared": summaries_result.deleted_count,
                "claims_cleared": claim_result.deleted_count,
                "sessions_updated": sessions_result.modified_count
            },
            "backup_timestamp": backup_timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error backing up and clearing user chat history for user {user_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to backup and clear chat history"
        }
    

# Add these helper functions at the bottom of mongodb_chat_manager.py

def create_new_chat_for_user(user_id: int, session_id: str = None, title: str = "New Chat") -> Dict:
    """Helper to create new chat session"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.create_new_chat_session(user_id, session_id, title)
    return {"success": False, "error": "MongoDB not available"}

def get_all_user_chats(user_id: int, limit: int = 50, include_archived: bool = False) -> List[Dict]:
    """Helper to get all user chats"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.get_user_chat_sessions(user_id, limit, include_archived)
    return []

def load_specific_chat(session_id: str, message_limit: int = 100) -> Dict:
    """Helper to load specific chat"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.load_chat_session(session_id, message_limit)
    return {"success": False, "error": "MongoDB not available"}

def update_chat_session_title(session_id: str, new_title: str) -> bool:
    """Helper to update chat title"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.update_chat_title(session_id, new_title)
    return False

def delete_chat_session_by_id(session_id: str, hard_delete: bool = False) -> bool:
    """Helper to delete chat session"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.delete_chat_session(session_id, hard_delete)
    return False

def search_user_chats(user_id: int, search_query: str, limit: int = 20) -> List[Dict]:
    """Helper to search user chats"""
    if mongodb_chat_manager:
        return mongodb_chat_manager.search_chat_sessions(user_id, search_query, limit)
    return []

print("[OK] FIXED MongoDB Chat Manager with all missing methods!")
print("[OK] Policy application methods now implemented correctly")
print("[OK] All missing methods added to the MongoDBChatManager class")