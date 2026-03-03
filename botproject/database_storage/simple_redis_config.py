# simple_redis_config.py - Simplified Redis configuration with fallback

import os
import json
import logging
from typing import Dict, Any, Optional,List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Try to import Redis, fallback to in-memory if not available
try:
    import redis
    from redis import ConnectionPool
    REDIS_AVAILABLE = True

    # Connection pool for better performance
    redis_pool = ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=0,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        max_connections=50,  # Pool size
        socket_keepalive=True
    )

    # Initialize Redis client with connection pool
    redis_client = redis.Redis(connection_pool=redis_pool)
    
    # Test connection
    try:
        redis_client.ping()
        logger.info(" Redis connection established successfully")
    except redis.ConnectionError:
        logger.warning("  Redis server not available, using in-memory storage")
        REDIS_AVAILABLE = False
        redis_client = None
        
except ImportError:
    REDIS_AVAILABLE = False
    redis_client = None
    logger.info("  Redis not installed, using in-memory storage")

# Async Redis client for WebSocket module (connection_manager, presence_manager)
async_redis_client = None
if REDIS_AVAILABLE:
    try:
        from redis.asyncio import Redis as AsyncRedis
        async_redis_client = AsyncRedis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            max_connections=50,
        )
        logger.info("Async Redis client created for WebSocket module")
    except Exception as e:
        logger.warning(f"Async Redis client not available: {e}")
        async_redis_client = None

# Fallback in-memory storage
_memory_sessions = {}
_memory_chatbot_states = {}
_memory_cache = {}

def store_session(session_id: str, data: Dict[str, Any], expire_seconds: int = 1800) -> bool:
    """Store session data with optional expiration"""
    try:
        if REDIS_AVAILABLE and redis_client:
            # Use Redis
            key = f"session:{session_id}"
            serialized_data = json.dumps(data, default=str)
            redis_client.setex(key, expire_seconds, serialized_data)
            return True
        else:
            # Use in-memory storage
            expiry_time = datetime.now() + timedelta(seconds=expire_seconds)
            _memory_sessions[session_id] = {
                'data': data,
                'expires_at': expiry_time
            }
            return True
            
    except Exception as e:
        logger.error(f"Error storing session: {e}")
        return False

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve session data"""
    try:
        if REDIS_AVAILABLE and redis_client:
            # Use Redis
            key = f"session:{session_id}"
            data = redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        else:
            # Use in-memory storage
            if session_id in _memory_sessions:
                session_data = _memory_sessions[session_id]
                
                # Check if expired
                if datetime.now() > session_data['expires_at']:
                    del _memory_sessions[session_id]
                    return None
                
                return session_data['data']
            return None
            
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return None

def delete_session(session_id: str) -> bool:
    """Delete session data"""
    try:
        if REDIS_AVAILABLE and redis_client:
            # Use Redis
            key = f"session:{session_id}"
            return bool(redis_client.delete(key))
        else:
            # Use in-memory storage
            if session_id in _memory_sessions:
                del _memory_sessions[session_id]
                return True
            return False
            
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return False

def store_chatbot_state(session_id: str, chatbot_type: str, state: Dict[str, Any]) -> bool:
    """Store chatbot state"""
    try:
        if REDIS_AVAILABLE and redis_client:
            # Use Redis
            key = f"chatbot:{session_id}:{chatbot_type}"
            serialized_state = json.dumps(state, default=str)
            redis_client.setex(key, 3600, serialized_state)  # 1 hour expiry
            return True
        else:
            # Use in-memory storage
            key = f"{session_id}_{chatbot_type}"
            expiry_time = datetime.now() + timedelta(hours=1)
            _memory_chatbot_states[key] = {
                'data': state,
                'expires_at': expiry_time
            }
            return True
            
    except Exception as e:
        logger.error(f"Error storing chatbot state: {e}")
        return False

def get_chatbot_state(session_id: str, chatbot_type: str) -> Optional[Dict[str, Any]]:
    """Retrieve chatbot state"""
    try:
        if REDIS_AVAILABLE and redis_client:
            # Use Redis
            key = f"chatbot:{session_id}:{chatbot_type}"
            state = redis_client.get(key)
            if state:
                return json.loads(state)
            return None
        else:
            # Use in-memory storage
            key = f"{session_id}_{chatbot_type}"
            if key in _memory_chatbot_states:
                state_data = _memory_chatbot_states[key]
                
                # Check if expired
                if datetime.now() > state_data['expires_at']:
                    del _memory_chatbot_states[key]
                    return None
                
                return state_data['data']
            return None
            
    except Exception as e:
        logger.error(f"Error getting chatbot state: {e}")
        return None

def cache_api_call(cache_key: str, data: Any, expire_seconds: int = 300) -> bool:
    """Cache API call result"""
    try:
        if REDIS_AVAILABLE and redis_client:
            # Use Redis
            serialized_data = json.dumps(data, default=str)
            redis_client.setex(cache_key, expire_seconds, serialized_data)
            return True
        else:
            # Use in-memory storage
            expiry_time = datetime.now() + timedelta(seconds=expire_seconds)
            _memory_cache[cache_key] = {
                'data': data,
                'expires_at': expiry_time
            }
            return True
            
    except Exception as e:
        logger.error(f"Error caching API call: {e}")
        return False

def get_cached_api_call(cache_key: str) -> Optional[Any]:
    """Get cached API call result"""
    try:
        if REDIS_AVAILABLE and redis_client:
            # Use Redis
            data = redis_client.get(cache_key)
            if data:
                return json.loads(data)
            return None
        else:
            # Use in-memory storage
            if cache_key in _memory_cache:
                cache_data = _memory_cache[cache_key]
                
                # Check if expired
                if datetime.now() > cache_data['expires_at']:
                    del _memory_cache[cache_key]
                    return None
                
                return cache_data['data']
            return None
            
    except Exception as e:
        logger.error(f"Error getting cached API call: {e}")
        return None

# ============= CHAT CONVERSATION CACHE =============
CHAT_CACHE_TTL = 86400  # 24 hours

def cache_conversation_history(session_id: str, messages_data: list, ttl: int = CHAT_CACHE_TTL) -> bool:
    """Cache conversation history in Redis for fast WebSocket context access"""
    try:
        if REDIS_AVAILABLE and redis_client:
            key = f"chat_history:{session_id}"
            serialized = json.dumps(messages_data, default=str)
            redis_client.setex(key, ttl, serialized)
            return True
        else:
            expiry_time = datetime.now() + timedelta(seconds=ttl)
            _memory_cache[f"chat_history:{session_id}"] = {
                'data': messages_data,
                'expires_at': expiry_time
            }
            return True
    except Exception as e:
        logger.error(f"Error caching conversation history: {e}")
        return False

def get_cached_conversation_history(session_id: str) -> Optional[list]:
    """Get cached conversation history from Redis"""
    try:
        if REDIS_AVAILABLE and redis_client:
            key = f"chat_history:{session_id}"
            data = redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        else:
            cache_key = f"chat_history:{session_id}"
            if cache_key in _memory_cache:
                cache_data = _memory_cache[cache_key]
                if datetime.now() > cache_data['expires_at']:
                    del _memory_cache[cache_key]
                    return None
                return cache_data['data']
            return None
    except Exception as e:
        logger.error(f"Error getting cached conversation history: {e}")
        return None

def invalidate_conversation_cache(session_id: str) -> bool:
    """Invalidate cached conversation history"""
    try:
        if REDIS_AVAILABLE and redis_client:
            key = f"chat_history:{session_id}"
            redis_client.delete(key)
            return True
        else:
            cache_key = f"chat_history:{session_id}"
            if cache_key in _memory_cache:
                del _memory_cache[cache_key]
            return True
    except Exception as e:
        logger.error(f"Error invalidating conversation cache: {e}")
        return False

def batch_store_sessions(sessions: Dict[str, Dict[str, Any]], expire_seconds: int = 1800) -> bool:
    """Store multiple sessions in a single pipeline operation"""
    try:
        if REDIS_AVAILABLE and redis_client:
            pipe = redis_client.pipeline()
            for session_id, data in sessions.items():
                key = f"session:{session_id}"
                serialized_data = json.dumps(data, default=str)
                pipe.setex(key, expire_seconds, serialized_data)
            pipe.execute()
            return True
        else:
            # Fallback to individual stores
            for session_id, data in sessions.items():
                store_session(session_id, data, expire_seconds)
            return True
    except Exception as e:
        logger.error(f"Error batch storing sessions: {e}")
        return False

def batch_get_sessions(session_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
    """Get multiple sessions in a single pipeline operation"""
    try:
        if REDIS_AVAILABLE and redis_client:
            pipe = redis_client.pipeline()
            for session_id in session_ids:
                key = f"session:{session_id}"
                pipe.get(key)
            results = pipe.execute()

            output = {}
            for session_id, data in zip(session_ids, results):
                output[session_id] = json.loads(data) if data else None
            return output
        else:
            # Fallback to individual gets
            return {sid: get_session(sid) for sid in session_ids}
    except Exception as e:
        logger.error(f"Error batch getting sessions: {e}")
        return {sid: None for sid in session_ids}

def cleanup_expired_data():
    """Clean up expired data from in-memory storage"""
    if REDIS_AVAILABLE:
        return  # Redis handles expiration automatically
    
    try:
        current_time = datetime.now()
        
        # Clean expired sessions
        expired_sessions = [
            session_id for session_id, session_data in _memory_sessions.items()
            if current_time > session_data['expires_at']
        ]
        for session_id in expired_sessions:
            del _memory_sessions[session_id]
        
        # Clean expired chatbot states
        expired_states = [
            key for key, state_data in _memory_chatbot_states.items()
            if current_time > state_data['expires_at']
        ]
        for key in expired_states:
            del _memory_chatbot_states[key]
        
        # Clean expired cache
        expired_cache = [
            key for key, cache_data in _memory_cache.items()
            if current_time > cache_data['expires_at']
        ]
        for key in expired_cache:
            del _memory_cache[key]
        
        if expired_sessions or expired_states or expired_cache:
            logger.info(f" Cleaned up {len(expired_sessions)} sessions, {len(expired_states)} states, {len(expired_cache)} cache entries")
            
    except Exception as e:
        logger.error(f"Error cleaning up expired data: {e}")

def get_storage_stats() -> Dict[str, Any]:
    """Get storage statistics"""
    try:
        if REDIS_AVAILABLE and redis_client:
            # Redis stats
            info = redis_client.info()
            return {
                "storage_type": "redis",
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        else:
            # In-memory stats
            return {
                "storage_type": "in_memory",
                "total_sessions": len(_memory_sessions),
                "total_chatbot_states": len(_memory_chatbot_states),
                "total_cache_entries": len(_memory_cache),
                "memory_usage": "Not available for in-memory storage"
            }
            
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        return {"error": str(e)}

# Health check function
def check_storage_health() -> Dict[str, Any]:
    """Check storage system health"""
    try:
        if REDIS_AVAILABLE and redis_client:
            # Test Redis connection
            redis_client.ping()
            return {
                "status": "healthy",
                "storage_type": "redis",
                "connection": "active"
            }
        else:
            return {
                "status": "healthy",
                "storage_type": "in_memory",
                "connection": "local"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "storage_type": "redis" if REDIS_AVAILABLE else "in_memory",
            "error": str(e)
        }

# Initialize cleanup scheduler for in-memory storage
if not REDIS_AVAILABLE:
    import threading
    import time
    
    def cleanup_scheduler():
        """Background thread to clean up expired data"""
        while True:
            time.sleep(300)  # Run every 5 minutes
            cleanup_expired_data()
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_scheduler, daemon=True)
    cleanup_thread.start()
    logger.info(" Started in-memory cleanup scheduler")

# Export information
storage_info = {
    "redis_available": REDIS_AVAILABLE,
    "storage_type": "redis" if REDIS_AVAILABLE else "in_memory",
    "fallback_active": not REDIS_AVAILABLE
}

print(f" Simple Redis Configuration Loaded")
print(f" Storage Type: {'Redis' if REDIS_AVAILABLE else 'In-Memory (Fallback)'}")
if not REDIS_AVAILABLE:
    print(" To use Redis: pip install redis")
print("=" * 50)