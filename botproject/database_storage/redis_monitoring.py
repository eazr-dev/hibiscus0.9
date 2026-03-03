# redis_monitoring.py - Advanced Redis monitoring and analytics

import redis
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import asyncio
from database_storage.simple_redis_config import redis_manager

logger = logging.getLogger(__name__)

@dataclass
class SessionMetrics:
    """Session analytics data structure"""
    total_sessions: int
    active_sessions: int
    expired_sessions: int
    average_session_duration: float
    sessions_by_hour: Dict[int, int]
    sessions_by_language: Dict[str, int]

@dataclass
class ChatbotMetrics:
    """Chatbot analytics data structure"""
    total_conversations: int
    completed_conversations: int
    abandoned_conversations: int
    completion_rate: float
    average_steps: float
    conversations_by_type: Dict[str, int]
    common_drop_off_points: Dict[str, List[int]]

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    most_cached_queries: Dict[str, int]
    cache_size_by_type: Dict[str, int]

class RedisAnalytics:
    """Advanced Redis analytics and monitoring"""
    
    def __init__(self):
        self.redis_client = redis_manager.redis_client
        
    def get_session_analytics(self, hours_back: int = 24) -> SessionMetrics:
        """Get comprehensive session analytics"""
        try:
            # Get all session keys
            session_keys = self.redis_client.keys("session:*")
            
            total_sessions = len(session_keys)
            active_sessions = 0
            sessions_by_hour = defaultdict(int)
            sessions_by_language = defaultdict(int)
            session_durations = []
            
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=hours_back)
            
            for key in session_keys:
                try:
                    session_data = self.redis_client.get(key)
                    if session_data:
                        data = json.loads(session_data)
                        
                        # Check if session is active
                        last_activity = datetime.fromisoformat(data.get('last_activity', ''))
                        if last_activity > cutoff_time:
                            active_sessions += 1
                        
                        # Session duration
                        created_at = datetime.fromisoformat(data.get('created_at', ''))
                        if created_at > cutoff_time:
                            duration = (last_activity - created_at).total_seconds() / 3600
                            session_durations.append(duration)
                            
                            # Sessions by hour
                            hour = created_at.hour
                            sessions_by_hour[hour] += 1
                        
                        # Get language preference
                        session_id = key.replace('session:', '')
                        user_lang = self.redis_client.get(f"user_lang:{session_id}")
                        if user_lang:
                            sessions_by_language[user_lang] += 1
                            
                except Exception as e:
                    logger.error(f"Error processing session {key}: {e}")
                    continue
            
            avg_duration = sum(session_durations) / len(session_durations) if session_durations else 0
            expired_sessions = total_sessions - active_sessions
            
            return SessionMetrics(
                total_sessions=total_sessions,
                active_sessions=active_sessions,
                expired_sessions=expired_sessions,
                average_session_duration=avg_duration,
                sessions_by_hour=dict(sessions_by_hour),
                sessions_by_language=dict(sessions_by_language)
            )
            
        except Exception as e:
            logger.error(f"Error getting session analytics: {e}")
            return SessionMetrics(0, 0, 0, 0, {}, {})
    
    def get_chatbot_analytics(self) -> ChatbotMetrics:
        """Get chatbot performance analytics"""
        try:
            chatbot_keys = self.redis_client.keys("chatbot:*")
            
            total_conversations = len(chatbot_keys)
            completed_conversations = 0
            conversations_by_type = defaultdict(int)
            step_counts = []
            drop_off_points = defaultdict(list)
            
            for key in chatbot_keys:
                try:
                    chatbot_data = self.redis_client.get(key)
                    if chatbot_data:
                        data = json.loads(chatbot_data)
                        
                        chatbot_type = data.get('chatbot_type', 'unknown')
                        conversations_by_type[chatbot_type] += 1
                        
                        current_step = data.get('current_step', 0)
                        completed = data.get('completed', False)
                        
                        if completed:
                            completed_conversations += 1
                        else:
                            # Track drop-off points
                            drop_off_points[chatbot_type].append(current_step)
                        
                        step_counts.append(current_step)
                        
                except Exception as e:
                    logger.error(f"Error processing chatbot {key}: {e}")
                    continue
            
            abandoned_conversations = total_conversations - completed_conversations
            completion_rate = (completed_conversations / total_conversations * 100) if total_conversations > 0 else 0
            average_steps = sum(step_counts) / len(step_counts) if step_counts else 0
            
            return ChatbotMetrics(
                total_conversations=total_conversations,
                completed_conversations=completed_conversations,
                abandoned_conversations=abandoned_conversations,
                completion_rate=completion_rate,
                average_steps=average_steps,
                conversations_by_type=dict(conversations_by_type),
                common_drop_off_points=dict(drop_off_points)
            )
            
        except Exception as e:
            logger.error(f"Error getting chatbot analytics: {e}")
            return ChatbotMetrics(0, 0, 0, 0, 0, {}, {})
    
    def get_cache_analytics(self) -> CacheMetrics:
        """Get cache performance analytics"""
        try:
            # Get cache keys by type
            rag_keys = self.redis_client.keys("rag:*")
            task_keys = self.redis_client.keys("task:*")
            casual_keys = self.redis_client.keys("casual:*")
            
            cache_size_by_type = {
                "rag": len(rag_keys),
                "task": len(task_keys),
                "casual": len(casual_keys)
            }
            
            # Get cache statistics (this would need to be tracked separately)
            # For now, we'll provide structure for cache hit/miss tracking
            total_requests = cache_size_by_type["rag"] + cache_size_by_type["task"] + cache_size_by_type["casual"]
            
            # These would be tracked in separate counters in a real implementation
            cache_hits = int(total_requests * 0.7)  # Placeholder
            cache_misses = total_requests - cache_hits
            hit_rate = (cache_hits / (cache_hits + cache_misses) * 100) if (cache_hits + cache_misses) > 0 else 0
            
            return CacheMetrics(
                total_requests=total_requests,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                hit_rate=hit_rate,
                most_cached_queries={},  # Would need additional tracking
                cache_size_by_type=cache_size_by_type
            )
            
        except Exception as e:
            logger.error(f"Error getting cache analytics: {e}")
            return CacheMetrics(0, 0, 0, 0, {}, {})
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time Redis statistics"""
        try:
            info = self.redis_client.info()
            
            return {
                "server": {
                    "redis_version": info.get("redis_version", "unknown"),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                    "uptime_in_days": info.get("uptime_in_days", 0)
                },
                "clients": {
                    "connected_clients": info.get("connected_clients", 0),
                    "blocked_clients": info.get("blocked_clients", 0)
                },
                "memory": {
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "used_memory_peak": info.get("used_memory_peak", 0),
                    "used_memory_peak_human": info.get("used_memory_peak_human", "0B")
                },
                "stats": {
                    "total_connections_received": info.get("total_connections_received", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0)
                },
                "keyspace": info.get("db0", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time stats: {e}")
            return {}
    
    def get_user_activity_patterns(self) -> Dict[str, Any]:
        """Analyze user activity patterns"""
        try:
            session_keys = self.redis_client.keys("session:*")
            
            activity_by_hour = defaultdict(int)
            activity_by_day = defaultdict(int)
            user_journey_lengths = []
            
            for key in session_keys:
                try:
                    session_data = self.redis_client.get(key)
                    if session_data:
                        data = json.loads(session_data)
                        
                        # Activity by hour
                        last_activity = datetime.fromisoformat(data.get('last_activity', ''))
                        activity_by_hour[last_activity.hour] += 1
                        activity_by_day[last_activity.strftime('%A')] += 1
                        
                        # Calculate user journey length
                        created_at = datetime.fromisoformat(data.get('created_at', ''))
                        journey_length = (last_activity - created_at).total_seconds() / 60  # minutes
                        user_journey_lengths.append(journey_length)
                        
                except Exception as e:
                    continue
            
            return {
                "peak_hours": dict(sorted(activity_by_hour.items(), key=lambda x: x[1], reverse=True)[:5]),
                "activity_by_day": dict(activity_by_day),
                "average_journey_length": sum(user_journey_lengths) / len(user_journey_lengths) if user_journey_lengths else 0,
                "total_active_users": len(session_keys)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user activity patterns: {e}")
            return {}
    
    def cleanup_old_data(self, days_old: int = 7) -> Dict[str, int]:
        """Clean up old Redis data"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days_old)
            cleaned_counts = defaultdict(int)
            
            # Clean old sessions
            session_keys = self.redis_client.keys("session:*")
            for key in session_keys:
                try:
                    session_data = self.redis_client.get(key)
                    if session_data:
                        data = json.loads(session_data)
                        last_activity = datetime.fromisoformat(data.get('last_activity', ''))
                        if last_activity < cutoff_time:
                            self.redis_client.delete(key)
                            cleaned_counts['sessions'] += 1
                except Exception:
                    continue
            
            # Clean old chatbot states
            chatbot_keys = self.redis_client.keys("chatbot:*")
            for key in chatbot_keys:
                try:
                    chatbot_data = self.redis_client.get(key)
                    if chatbot_data:
                        data = json.loads(chatbot_data)
                        # Check if chatbot was started long ago and not completed
                        if not data.get('completed', False):
                            # This would need timestamp tracking
                            pass
                except Exception:
                    continue
            
            return dict(cleaned_counts)
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return {}

# Initialize analytics
redis_analytics = RedisAnalytics()

# Background monitoring task
async def monitor_redis_health():
    """Background task to monitor Redis health"""
    while True:
        try:
            stats = redis_analytics.get_real_time_stats()
            
            # Log warnings for high memory usage
            memory_usage = stats.get('memory', {}).get('used_memory', 0)
            if memory_usage > 100 * 1024 * 1024:  # 100MB threshold
                logger.warning(f"Redis memory usage high: {stats.get('memory', {}).get('used_memory_human', '0B')}")
            
            # Log info about active connections
            active_clients = stats.get('clients', {}).get('connected_clients', 0)
            if active_clients > 50:  # Threshold for high connection count
                logger.info(f"High Redis connection count: {active_clients}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            logger.error(f"Redis monitoring error: {e}")
            await asyncio.sleep(60)  # Retry in 1 minute

# Utility functions for easy integration
def get_dashboard_data() -> Dict[str, Any]:
    """Get comprehensive dashboard data"""
    try:
        return {
            "session_metrics": redis_analytics.get_session_analytics(),
            "chatbot_metrics": redis_analytics.get_chatbot_analytics(),
            "cache_metrics": redis_analytics.get_cache_analytics(),
            "real_time_stats": redis_analytics.get_real_time_stats(),
            "user_patterns": redis_analytics.get_user_activity_patterns(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return {"error": str(e)}

def export_analytics_report(format_type: str = "json") -> str:
    """Export analytics report in specified format"""
    try:
        data = get_dashboard_data()
        
        if format_type == "json":
            return json.dumps(data, indent=2, default=str)
        elif format_type == "csv":
            # Convert to CSV format (simplified)
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write session data
            writer.writerow(["Metric", "Value"])
            session_data = data.get("session_metrics", {})
            for key, value in session_data.__dict__.items() if hasattr(session_data, '__dict__') else {}:
                writer.writerow([key, value])
            
            return output.getvalue()
        else:
            return json.dumps(data, indent=2, default=str)
            
    except Exception as e:
        logger.error(f"Error exporting analytics report: {e}")
        return f"Error: {str(e)}"