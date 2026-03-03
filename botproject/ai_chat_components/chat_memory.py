# chat_memory.py - Advanced Chat Memory System for Eazr Financial Assistant
# Updated to work with MongoDB persistent storage and 14-day session timeout

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque
import hashlib

logger = logging.getLogger(__name__)

# Session timeout constant - 14 days
SESSION_TIMEOUT_SECONDS = 1209600  # 14 days = 14 * 24 * 60 * 60 = 1,209,600 seconds

@dataclass
class ChatMessage:
    """Individual chat message structure"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    message_id: str
    intent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'message_id': self.message_id,
            'intent': self.intent,
            'context': self.context or {},
            'metadata': self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create from dictionary"""
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            message_id=data['message_id'],
            intent=data.get('intent'),
            context=data.get('context'),
            metadata=data.get('metadata')
        )

@dataclass
class ConversationSummary:
    """Summary of conversation context"""
    main_topics: List[str]
    user_preferences: Dict[str, Any]
    completed_actions: List[str]
    pending_actions: List[str]
    user_profile: Dict[str, Any]
    last_updated: datetime

class ChatMemoryManager:
    """Advanced chat memory management system with MongoDB integration support"""
    
    def __init__(self, max_messages_per_session: int = 50, max_context_window: int = 10):
        self.max_messages_per_session = max_messages_per_session
        self.max_context_window = max_context_window
        
        # In-memory storage (fallback when MongoDB is not available)
        self.conversations: Dict[str, deque] = {}
        self.summaries: Dict[str, ConversationSummary] = {}
        self.user_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Check for MongoDB availability first (higher priority than Redis)
        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            self.mongodb_available = bool(mongodb_chat_manager)
            if self.mongodb_available:
                self.mongodb_manager = mongodb_chat_manager
                logger.info("MongoDB chat manager available for persistent storage")
        except ImportError:
            self.mongodb_available = False
            logger.info("MongoDB chat manager not available")
        
        # Try to use Redis as secondary storage option
        try:
            from database_storage.simple_redis_config import (
                store_session, get_session,
                cache_api_call, get_cached_api_call,
                cache_conversation_history,
                get_cached_conversation_history,
                invalidate_conversation_cache
            )
            self.redis_available = True
            self.store_session = store_session
            self.get_session = get_session
            self.cache_api_call = cache_api_call
            self.get_cached_api_call = get_cached_api_call
            self.cache_conversation_history = cache_conversation_history
            self.get_cached_conversation_history = get_cached_conversation_history
            self.invalidate_conversation_cache = invalidate_conversation_cache
            logger.info("Redis integration enabled for chat memory (with conversation cache)")
        except ImportError:
            self.redis_available = False
            logger.info("Redis not available, using in-memory storage")

    def generate_message_id(self, session_id: str, content: str) -> str:
        """Generate unique message ID"""
        timestamp = datetime.now().isoformat()
        raw_id = f"{session_id}_{content[:50]}_{timestamp}"
        return hashlib.md5(raw_id.encode()).hexdigest()[:12]

    def add_message(self, session_id: str, role: str, content: str, 
                   intent: str = None, context: Dict[str, Any] = None,
                   metadata: Dict[str, Any] = None, user_id: int = None) -> str:
        """Add a new message to the conversation history"""
        try:
            message_id = self.generate_message_id(session_id, content)
            
            # If MongoDB is available and we have user_id, use MongoDB for persistent storage
            if self.mongodb_available and user_id:
                # Use MongoDB for persistent storage
                if role == 'user':
                    from database_storage.mongodb_chat_manager import add_user_message_to_mongodb
                    mongodb_message_id = add_user_message_to_mongodb(
                        session_id, user_id, content, intent, context
                    )
                    if mongodb_message_id:
                        message_id = mongodb_message_id
                else:  # assistant
                    from database_storage.mongodb_chat_manager import add_assistant_message_to_mongodb
                    mongodb_message_id = add_assistant_message_to_mongodb(
                        session_id, user_id, content, intent, context
                    )
                    if mongodb_message_id:
                        message_id = mongodb_message_id
            
            # Also maintain in-memory for immediate access
            message = ChatMessage(
                role=role,
                content=content,
                timestamp=datetime.now(),
                message_id=message_id,
                intent=intent,
                context=context or {},
                metadata=metadata or {}
            )
            
            # Initialize conversation if not exists
            if session_id not in self.conversations:
                self.conversations[session_id] = deque(maxlen=self.max_messages_per_session)
            
            # Add message to conversation
            self.conversations[session_id].append(message)
            
            # Update conversation summary
            self._update_conversation_summary(session_id, message)
            
            # Always cache recent messages to Redis for fast WebSocket context
            self._cache_recent_messages_to_redis(session_id)
            
            logger.info(f"Added {role} message to session {session_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error adding message to memory: {e}")
            return ""

    def get_conversation_history(self, session_id: str,
                               limit: Optional[int] = None) -> List[ChatMessage]:
        """Get conversation history for a session.

        Lookup order: in-memory (fastest) → Redis cache → MongoDB (slowest).
        On cache miss, populates the faster layers for subsequent calls.
        """
        try:
            # 1. In-memory first (fastest, always up-to-date for active sessions)
            if session_id in self.conversations and self.conversations[session_id]:
                messages = list(self.conversations[session_id])
                if limit:
                    messages = messages[-limit:]
                return messages

            # 2. Redis cache (fast, survives process restart)
            if self.redis_available:
                try:
                    cached = self.get_cached_conversation_history(session_id)
                    if cached:
                        messages = [ChatMessage.from_dict(m) for m in cached]
                        # Populate in-memory for subsequent calls
                        self.conversations[session_id] = deque(messages, maxlen=self.max_messages_per_session)
                        if limit:
                            messages = messages[-limit:]
                        return messages
                except Exception as e:
                    logger.warning(f"Redis cache read failed, trying MongoDB: {e}")

            # 3. MongoDB (slowest, but authoritative)
            if self.mongodb_available:
                try:
                    mongodb_messages = self.mongodb_manager.get_conversation_history(session_id, limit)
                    if mongodb_messages:
                        # Populate in-memory and Redis for next time
                        self.conversations[session_id] = deque(mongodb_messages, maxlen=self.max_messages_per_session)
                        self._cache_recent_messages_to_redis(session_id)
                        return mongodb_messages
                except Exception as e:
                    logger.warning(f"MongoDB read failed: {e}")

            # 4. Last resort: legacy Redis persist format
            self._load_conversation(session_id)
            if session_id in self.conversations:
                messages = list(self.conversations[session_id])
                if limit:
                    messages = messages[-limit:]
                return messages

            return []

        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    def get_context_for_response(self, session_id: str) -> Dict[str, Any]:
        """Get relevant context for generating response"""
        try:
            # Try to get context from MongoDB first if available
            if self.mongodb_available:
                try:
                    mongodb_context = self.mongodb_manager.get_context_window(session_id)
                    if mongodb_context:
                        return mongodb_context
                except Exception as e:
                    logger.warning(f"Could not get MongoDB context, using fallback: {e}")
            
            # Fallback to in-memory context
            recent_messages = self.get_conversation_history(session_id, self.max_context_window)
            summary = self.summaries.get(session_id)
            user_context = self.user_contexts.get(session_id, {})
            
            # Extract recent intents and topics
            recent_intents = []
            recent_topics = []
            conversation_flow = []
            
            for msg in recent_messages[-5:]:  # Last 5 messages
                if msg.intent:
                    recent_intents.append(msg.intent)
                if msg.context:
                    recent_topics.extend(msg.context.get('topics', []))
                
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
                'user_context': user_context,
                'conversation_length': len(recent_messages),
                'last_user_message': recent_messages[-1].content if recent_messages and recent_messages[-1].role == 'user' else None,
                'last_assistant_message': None,
                'summary': asdict(summary) if summary else None
            }
            
            # Find last assistant message
            for msg in reversed(recent_messages):
                if msg.role == 'assistant':
                    context['last_assistant_message'] = msg.content
                    break
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting context for response: {e}")
            return {}

    def update_user_context(self, session_id: str, updates: Dict[str, Any]):
        """Update user context information"""
        try:
            # Try MongoDB first if available
            if self.mongodb_available:
                try:
                    session_info = self.mongodb_manager.sessions_collection.find_one({"session_id": session_id})
                    if session_info and session_info.get("user_id"):
                        user_id = session_info["user_id"]
                        from database_storage.mongodb_chat_manager import update_user_profile_in_mongodb
                        update_user_profile_in_mongodb(session_id, user_id, updates)
                        logger.info(f"Updated user context in MongoDB for session {session_id}")
                        return
                except Exception as e:
                    logger.warning(f"Could not update MongoDB context, using fallback: {e}")
            
            # Fallback to in-memory
            if session_id not in self.user_contexts:
                self.user_contexts[session_id] = {}
            
            self.user_contexts[session_id].update(updates)
            
            # Persist user context to Redis
            if self.redis_available:
                cache_key = f"user_context:{session_id}"
                self.cache_api_call(cache_key, self.user_contexts[session_id], expire_seconds=SESSION_TIMEOUT_SECONDS)
            
            logger.info(f"Updated user context for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error updating user context: {e}")

    def search_conversation_history(self, session_id: str, query: str, 
                                  limit: int = 5) -> List[ChatMessage]:
        """Search through conversation history"""
        try:
            # Try MongoDB search first if available
            if self.mongodb_available:
                try:
                    results = self.mongodb_manager.search_conversation_history(session_id, query, limit)
                    if results:
                        return results
                except Exception as e:
                    logger.warning(f"Could not search MongoDB, using fallback: {e}")
            
            # Fallback to in-memory search
            messages = self.get_conversation_history(session_id)
            query_lower = query.lower()
            
            matching_messages = []
            for msg in messages:
                if (query_lower in msg.content.lower() or 
                    (msg.intent and query_lower in msg.intent.lower())):
                    matching_messages.append(msg)
            
            return matching_messages[-limit:]
            
        except Exception as e:
            logger.error(f"Error searching conversation history: {e}")
            return []

    def get_conversation_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics about the conversation"""
        try:
            # Try MongoDB analytics first if available
            if self.mongodb_available:
                try:
                    analytics = self.mongodb_manager.get_conversation_analytics(session_id)
                    if analytics:
                        return analytics
                except Exception as e:
                    logger.warning(f"Could not get MongoDB analytics, using fallback: {e}")
            
            # Fallback to in-memory analytics
            messages = self.get_conversation_history(session_id)
            
            if not messages:
                return {}
            
            user_messages = [msg for msg in messages if msg.role == 'user']
            assistant_messages = [msg for msg in messages if msg.role == 'assistant']
            
            # Calculate analytics
            total_messages = len(messages)
            conversation_duration = (messages[-1].timestamp - messages[0].timestamp).total_seconds() / 60  # minutes
            
            intents = [msg.intent for msg in messages if msg.intent]
            intent_counts = {}
            for intent in intents:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            analytics = {
                'total_messages': total_messages,
                'user_messages': len(user_messages),
                'assistant_messages': len(assistant_messages),
                'conversation_duration_minutes': conversation_duration,
                'most_common_intents': sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:3],
                'average_message_length': sum(len(msg.content) for msg in messages) / total_messages,
                'session_start': messages[0].timestamp.isoformat(),
                'last_activity': messages[-1].timestamp.isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting conversation analytics: {e}")
            return {}

    def clear_conversation(self, session_id: str) -> bool:
        """Clear conversation history for a session"""
        try:
            # Clear from MongoDB if available
            if self.mongodb_available:
                try:
                    success = self.mongodb_manager.clear_conversation(session_id)
                    if success:
                        logger.info(f"Cleared MongoDB conversation for session {session_id}")
                except Exception as e:
                    logger.warning(f"Could not clear MongoDB conversation: {e}")
            
            # Clear from in-memory storage
            if session_id in self.conversations:
                del self.conversations[session_id]
            
            if session_id in self.summaries:
                del self.summaries[session_id]
            
            if session_id in self.user_contexts:
                del self.user_contexts[session_id]
            
            # Clear from Redis cache
            if self.redis_available:
                try:
                    self.invalidate_conversation_cache(session_id)
                except Exception:
                    pass
            
            logger.info(f"Cleared conversation for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False

    def get_contextual_prompt(self, session_id: str, current_query: str) -> str:
        """Generate contextual prompt including conversation history"""
        try:
            # Try MongoDB contextual prompt first if available
            if self.mongodb_available:
                try:
                    from database_storage.mongodb_chat_manager import get_contextual_prompt_from_mongodb
                    contextual_prompt = get_contextual_prompt_from_mongodb(session_id, current_query)
                    if contextual_prompt and contextual_prompt != current_query:
                        return contextual_prompt
                except Exception as e:
                    logger.warning(f"Could not get MongoDB contextual prompt, using fallback: {e}")
            
            # Fallback to in-memory contextual prompt generation
            context = self.get_context_for_response(session_id)
            
            # Build contextual prompt
            prompt_parts = []
            
            # Add conversation context
            if context.get('recent_messages'):
                prompt_parts.append("Previous conversation context:")
                for msg in context['recent_messages'][-3:]:  # Last 3 messages
                    role = "User" if msg['role'] == 'user' else "Assistant"
                    prompt_parts.append(f"{role}: {msg['content']}")
                prompt_parts.append("")
            
            # Add user context
            if context.get('user_context'):
                user_info = []
                for key, value in context['user_context'].items():
                    user_info.append(f"{key}: {value}")
                if user_info:
                    prompt_parts.append(f"User Information: {', '.join(user_info)}")
                    prompt_parts.append("")
            
            # Add recent topics/intents
            if context.get('recent_intents'):
                prompt_parts.append(f"Recent topics discussed: {', '.join(context['recent_intents'])}")
                prompt_parts.append("")
            
            # Add current query
            prompt_parts.append(f"Current User Query: {current_query}")
            prompt_parts.append("")
            prompt_parts.append("Please provide a contextual response considering the conversation history above.")
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Error generating contextual prompt: {e}")
            return current_query

    def _update_conversation_summary(self, session_id: str, message: ChatMessage):
        """Update conversation summary with new message"""
        try:
            if session_id not in self.summaries:
                self.summaries[session_id] = ConversationSummary(
                    main_topics=[],
                    user_preferences={},
                    completed_actions=[],
                    pending_actions=[],
                    user_profile={},
                    last_updated=datetime.now()
                )
            
            summary = self.summaries[session_id]
            
            # Extract topics from message
            if message.context and 'topics' in message.context:
                for topic in message.context['topics']:
                    if topic not in summary.main_topics:
                        summary.main_topics.append(topic)
            
            # Track completed actions
            if message.role == 'assistant' and message.intent:
                if 'completed' in message.content.lower():
                    if message.intent not in summary.completed_actions:
                        summary.completed_actions.append(message.intent)
            
            # Update user profile from user messages
            if message.role == 'user':
                # Extract potential user information
                content_lower = message.content.lower()
                if 'my name is' in content_lower:
                    name = message.content.split('my name is')[1].strip().split()[0]
                    summary.user_profile['name'] = name
            
            summary.last_updated = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating conversation summary: {e}")

    def _cache_recent_messages_to_redis(self, session_id: str):
        """Cache recent in-memory messages to Redis for fast WebSocket context access"""
        try:
            if not self.redis_available or session_id not in self.conversations:
                return
            # Cache last 20 messages (enough for LLM context window of 6-10)
            recent = list(self.conversations[session_id])[-20:]
            messages_data = [msg.to_dict() for msg in recent]
            self.cache_conversation_history(session_id, messages_data)
        except Exception as e:
            logger.error(f"Error caching messages to Redis: {e}")

    def _persist_conversation(self, session_id: str):
        """Persist conversation to storage"""
        try:
            if not self.redis_available:
                return
            
            if session_id in self.conversations:
                # Convert messages to serializable format
                messages_data = [msg.to_dict() for msg in self.conversations[session_id]]
                
                cache_key = f"conversation:{session_id}"
                self.cache_api_call(cache_key, {
                    'messages': messages_data,
                    'summary': asdict(self.summaries.get(session_id)) if session_id in self.summaries else None,
                    'user_context': self.user_contexts.get(session_id, {})
                }, expire_seconds=SESSION_TIMEOUT_SECONDS)  # 14 days
                
        except Exception as e:
            logger.error(f"Error persisting conversation: {e}")

    def _load_conversation(self, session_id: str):
        """Load conversation from storage"""
        try:
            if not self.redis_available or session_id in self.conversations:
                return
            
            cache_key = f"conversation:{session_id}"
            data = self.get_cached_api_call(cache_key)
            
            if data and 'messages' in data:
                # Reconstruct messages
                messages = deque(maxlen=self.max_messages_per_session)
                for msg_data in data['messages']:
                    message = ChatMessage.from_dict(msg_data)
                    messages.append(message)
                
                self.conversations[session_id] = messages
                
                # Load summary
                if data.get('summary'):
                    summary_data = data['summary']
                    summary = ConversationSummary(
                        main_topics=summary_data.get('main_topics', []),
                        user_preferences=summary_data.get('user_preferences', {}),
                        completed_actions=summary_data.get('completed_actions', []),
                        pending_actions=summary_data.get('pending_actions', []),
                        user_profile=summary_data.get('user_profile', {}),
                        last_updated=datetime.fromisoformat(summary_data.get('last_updated', datetime.now().isoformat()))
                    )
                    self.summaries[session_id] = summary
                
                # Load user context
                if data.get('user_context'):
                    self.user_contexts[session_id] = data['user_context']
                
                logger.info(f"Loaded conversation for session {session_id}")
                
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")

# Initialize global memory manager
chat_memory = ChatMemoryManager()

# Helper functions for easy integration (updated to support MongoDB)

def add_user_message(session_id: str, content: str, intent: str = None, 
                    context: Dict[str, Any] = None, user_id: int = None) -> str:
    """Add user message to memory"""
    return chat_memory.add_message(session_id, 'user', content, intent, context, user_id=user_id)

def add_assistant_message(session_id: str, content: str, intent: str = None,
                         context: Dict[str, Any] = None, user_id: int = None) -> str:
    """Add assistant message to memory"""
    return chat_memory.add_message(session_id, 'assistant', content, intent, context, user_id=user_id)

def get_conversation_context(session_id: str) -> Dict[str, Any]:
    """Get conversation context for response generation"""
    return chat_memory.get_context_for_response(session_id)

def get_contextual_prompt_for_query(session_id: str, query: str) -> str:
    """Get contextual prompt including conversation history"""
    return chat_memory.get_contextual_prompt(session_id, query)

def update_user_profile(session_id: str, profile_data: Dict[str, Any]):
    """Update user profile information"""
    chat_memory.update_user_context(session_id, profile_data)

def search_chat_history(session_id: str, search_query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search through chat history"""
    messages = chat_memory.search_conversation_history(session_id, search_query, limit)
    return [msg.to_dict() for msg in messages]

def get_chat_analytics(session_id: str) -> Dict[str, Any]:
    """Get chat analytics"""
    return chat_memory.get_conversation_analytics(session_id)

def clear_chat_history(session_id: str) -> bool:
    """Clear chat history"""
    return chat_memory.clear_conversation(session_id)

print("Advanced Chat Memory System with MongoDB Integration Loaded Successfully!")
print("=" * 60)
print("Features:")
print("   MongoDB persistent storage integration")
print("   14-day session timeout support")
print("   Cross-session conversation context")
print("   Fallback to Redis/in-memory storage")
print("   User activity tracking compatibility")
print("   Conversation analytics")
print("   Search functionality")
print("=" * 60)