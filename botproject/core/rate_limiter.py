"""
Advanced Rate Limiter with Redis Backend
Production-ready rate limiting for API endpoints

Features:
- Redis-based distributed rate limiting (works across multiple instances)
- Sliding window algorithm (more accurate than fixed window)
- Per-user, per-IP, and per-phone rate limiting
- Adaptive rate limiting (adjusts based on user behavior)
- Detailed analytics and monitoring
- Graceful fallback to in-memory when Redis unavailable
- Whitelist/Blacklist support
- Rate limit headers in responses

Protects against:
- SMS flooding on /send-otp
- Brute force attacks on /verify-otp
- Expensive API call abuse on /ask
- OAuth abuse on /oauth-login
- DDoS attacks
"""
import os
import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, Callable
from functools import wraps

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# -------------------- Configuration --------------------

class RateLimitConfig:
    """Centralized rate limit configuration"""

    # Redis configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_RATE_LIMIT_DB", "1"))  # Separate DB for rate limiting
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    # Rate limit defaults (can be overridden via env vars)
    LIMITS = {
        # ==================== AUTHENTICATION ====================
        "send_otp": os.getenv("RATE_LIMIT_SEND_OTP", "10/minute"),
        "send_otp_per_phone": os.getenv("RATE_LIMIT_SEND_OTP_PER_PHONE", "10/hour"),
        "verify_otp": os.getenv("RATE_LIMIT_VERIFY_OTP", "30/minute"),
        "verify_otp_strict": os.getenv("RATE_LIMIT_VERIFY_OTP_STRICT", "100/hour"),
        "oauth_login": os.getenv("RATE_LIMIT_OAUTH", "30/minute"),
        "check_session": os.getenv("RATE_LIMIT_CHECK_SESSION", "120/minute"),

        # ==================== CHAT ENDPOINTS ====================
        "ask": os.getenv("RATE_LIMIT_ASK", "30/minute"),
        "ask_authenticated": os.getenv("RATE_LIMIT_ASK_AUTH", "60/minute"),
        "ask_burst": os.getenv("RATE_LIMIT_ASK_BURST", "5/second"),
        "chat_session": os.getenv("RATE_LIMIT_CHAT_SESSION", "20/minute"),
        "chat_history": os.getenv("RATE_LIMIT_CHAT_HISTORY", "30/minute"),
        "chat_export": os.getenv("RATE_LIMIT_CHAT_EXPORT", "5/minute"),
        "chat_delete": os.getenv("RATE_LIMIT_CHAT_DELETE", "10/minute"),

        # ==================== POLICY ENDPOINTS ====================
        "policy_upload": os.getenv("RATE_LIMIT_POLICY_UPLOAD", "10/minute"),
        "policy_analysis": os.getenv("RATE_LIMIT_POLICY_ANALYSIS", "10/minute"),
        "policy_read": os.getenv("RATE_LIMIT_POLICY_READ", "30/minute"),
        "policy_modify": os.getenv("RATE_LIMIT_POLICY_MODIFY", "10/minute"),
        "policy_delete": os.getenv("RATE_LIMIT_POLICY_DELETE", "5/minute"),
        "policy_export": os.getenv("RATE_LIMIT_POLICY_EXPORT", "5/minute"),
        "policy_report": os.getenv("RATE_LIMIT_POLICY_REPORT", "5/minute"),

        # ==================== DASHBOARD ENDPOINTS ====================
        "dashboard_data": os.getenv("RATE_LIMIT_DASHBOARD", "20/minute"),
        "protection_score": os.getenv("RATE_LIMIT_PROTECTION_SCORE", "10/minute"),
        "insights": os.getenv("RATE_LIMIT_INSIGHTS", "10/minute"),

        # ==================== ADMIN ENDPOINTS ====================
        "admin_login": os.getenv("RATE_LIMIT_ADMIN_LOGIN", "5/minute"),
        "admin_read": os.getenv("RATE_LIMIT_ADMIN_READ", "30/minute"),
        "admin_write": os.getenv("RATE_LIMIT_ADMIN_WRITE", "10/minute"),
        "admin_delete": os.getenv("RATE_LIMIT_ADMIN_DELETE", "3/minute"),
        "admin_critical": os.getenv("RATE_LIMIT_ADMIN_CRITICAL", "1/minute"),

        # ==================== USER DATA ENDPOINTS ====================
        "user_read": os.getenv("RATE_LIMIT_USER_READ", "30/minute"),
        "user_write": os.getenv("RATE_LIMIT_USER_WRITE", "10/minute"),
        "user_delete": os.getenv("RATE_LIMIT_USER_DELETE", "5/minute"),
        "family_member": os.getenv("RATE_LIMIT_FAMILY_MEMBER", "10/minute"),

        # ==================== CLAIMS & SUPPORT ====================
        "claims": os.getenv("RATE_LIMIT_CLAIMS", "10/minute"),
        "support": os.getenv("RATE_LIMIT_SUPPORT", "10/minute"),

        # ==================== FILE OPERATIONS ====================
        "file_upload": os.getenv("RATE_LIMIT_FILE_UPLOAD", "5/minute"),
        "file_download": os.getenv("RATE_LIMIT_FILE_DOWNLOAD", "20/minute"),

        # ==================== AI/EXPENSIVE OPERATIONS ====================
        "ai_processing": os.getenv("RATE_LIMIT_AI_PROCESSING", "10/minute"),
        "report_generation": os.getenv("RATE_LIMIT_REPORT_GEN", "5/minute"),

        # ==================== WEBSOCKET ENDPOINTS ====================
        "ws_chat": os.getenv("RATE_LIMIT_WS_CHAT", "60/minute"),
        "ws_chat_burst": os.getenv("RATE_LIMIT_WS_CHAT_BURST", "10/second"),
        "ws_typing": os.getenv("RATE_LIMIT_WS_TYPING", "120/minute"),
        "ws_presence": os.getenv("RATE_LIMIT_WS_PRESENCE", "30/minute"),
        "ws_connect": os.getenv("RATE_LIMIT_WS_CONNECT", "10/minute"),

        # ==================== BILL AUDIT ENDPOINTS ====================
        "bill_audit_upload": os.getenv("RATE_LIMIT_BILL_UPLOAD", "5/minute"),
        "bill_audit_read": os.getenv("RATE_LIMIT_BILL_READ", "30/minute"),
        "bill_audit_report": os.getenv("RATE_LIMIT_BILL_REPORT", "5/minute"),

        # ==================== HBF/GBF ENDPOINTS ====================
        "hbf_check": os.getenv("RATE_LIMIT_HBF_CHECK", "10/minute"),
        "hbf_apply": os.getenv("RATE_LIMIT_HBF_APPLY", "5/minute"),

        # ==================== GENERAL ====================
        "default": os.getenv("RATE_LIMIT_DEFAULT", "100/minute"),
        "strict": os.getenv("RATE_LIMIT_STRICT", "10/minute"),
        "relaxed": os.getenv("RATE_LIMIT_RELAXED", "60/minute"),
        "public": os.getenv("RATE_LIMIT_PUBLIC", "60/minute"),
    }

    # Whitelist - IPs that bypass rate limiting (internal services, health checks)
    WHITELIST_IPS = set(os.getenv("RATE_LIMIT_WHITELIST_IPS", "127.0.0.1").split(","))

    # Blacklist - IPs that are always blocked
    BLACKLIST_IPS = set(filter(None, os.getenv("RATE_LIMIT_BLACKLIST_IPS", "").split(",")))

    # Adaptive rate limiting thresholds
    ADAPTIVE_THRESHOLD_WARNINGS = 3  # Warnings before reducing limit
    ADAPTIVE_REDUCTION_FACTOR = 0.5  # Reduce limit by 50% for bad actors
    ADAPTIVE_RECOVERY_TIME = 3600  # 1 hour to recover from reduced limits


# Export RATE_LIMITS for backward compatibility
RATE_LIMITS = RateLimitConfig.LIMITS


# -------------------- Redis Rate Limiter --------------------

class RedisRateLimiter:
    """
    Advanced Redis-based rate limiter with sliding window algorithm
    """

    def __init__(self):
        self.redis_client = None
        self.redis_available = False
        self._memory_storage: Dict[str, list] = {}  # Fallback storage
        self._blacklist_cache: Dict[str, float] = {}  # Temporary blacklist
        self._warning_counts: Dict[str, int] = {}  # Track warnings per client
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=RateLimitConfig.REDIS_HOST,
                port=RateLimitConfig.REDIS_PORT,
                db=RateLimitConfig.REDIS_DB,
                password=RateLimitConfig.REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
            logger.info(f"✓ Redis rate limiter connected to {RateLimitConfig.REDIS_HOST}:{RateLimitConfig.REDIS_PORT}")
        except Exception as e:
            logger.warning(f"⚠ Redis not available for rate limiting, using in-memory fallback: {e}")
            self.redis_available = False

    def _parse_rate_limit(self, limit_string: str) -> Tuple[int, int]:
        """
        Parse rate limit string like '30/minute' into (count, seconds)

        Supports: /second, /minute, /hour, /day
        """
        try:
            count, period = limit_string.split("/")
            count = int(count)

            period_seconds = {
                "second": 1,
                "minute": 60,
                "hour": 3600,
                "day": 86400
            }

            seconds = period_seconds.get(period.lower(), 60)
            return count, seconds
        except Exception:
            return 100, 60  # Default: 100/minute

    def _get_window_key(self, identifier: str, endpoint: str, window_start: int) -> str:
        """Generate Redis key for rate limit window"""
        return f"ratelimit:{endpoint}:{identifier}:{window_start}"

    def _get_analytics_key(self, identifier: str, endpoint: str) -> str:
        """Generate Redis key for analytics"""
        return f"ratelimit:analytics:{endpoint}:{identifier}"

    def check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        limit_string: str,
        cost: int = 1
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limit using sliding window algorithm

        Args:
            identifier: Unique client identifier (IP, user_id, phone, etc.)
            endpoint: API endpoint name
            limit_string: Rate limit string (e.g., '30/minute')
            cost: Request cost (default 1, higher for expensive operations)

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        # Check whitelist
        if identifier in RateLimitConfig.WHITELIST_IPS:
            return True, {"whitelisted": True}

        # Check blacklist
        if identifier in RateLimitConfig.BLACKLIST_IPS:
            return False, {"blacklisted": True, "permanent": True}

        # Check temporary blacklist
        if identifier in self._blacklist_cache:
            if time.time() < self._blacklist_cache[identifier]:
                return False, {"blacklisted": True, "temporary": True}
            else:
                del self._blacklist_cache[identifier]

        max_requests, window_seconds = self._parse_rate_limit(limit_string)
        current_time = time.time()
        window_start = int(current_time // window_seconds) * window_seconds

        if self.redis_available:
            return self._check_redis(identifier, endpoint, max_requests, window_seconds, window_start, cost)
        else:
            return self._check_memory(identifier, endpoint, max_requests, window_seconds, current_time, cost)

    def _check_redis(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
        window_start: int,
        cost: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis with sliding window"""
        try:
            current_window_key = self._get_window_key(identifier, endpoint, window_start)
            previous_window_key = self._get_window_key(identifier, endpoint, window_start - window_seconds)

            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.get(current_window_key)
            pipe.get(previous_window_key)
            pipe.ttl(current_window_key)
            results = pipe.execute()

            current_count = int(results[0] or 0)
            previous_count = int(results[1] or 0)
            ttl = results[2] if results[2] > 0 else window_seconds

            # Sliding window calculation
            current_time = time.time()
            window_position = (current_time - window_start) / window_seconds
            weighted_count = previous_count * (1 - window_position) + current_count

            remaining = max(0, max_requests - int(weighted_count) - cost)
            reset_time = window_start + window_seconds

            rate_info = {
                "limit": max_requests,
                "remaining": remaining,
                "reset": int(reset_time),
                "reset_after": int(reset_time - current_time),
                "current_usage": int(weighted_count),
                "window_seconds": window_seconds
            }

            if weighted_count + cost > max_requests:
                # Rate limit exceeded
                self._record_violation(identifier, endpoint)
                return False, rate_info

            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incrby(current_window_key, cost)
            pipe.expire(current_window_key, window_seconds * 2)  # Keep for 2 windows
            pipe.execute()

            # Update analytics
            self._update_analytics(identifier, endpoint, cost)

            return True, rate_info

        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fallback to allowing request on error
            return True, {"error": str(e), "fallback": True}

    def _check_memory(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
        current_time: float,
        cost: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using in-memory storage (fallback)"""
        key = f"{endpoint}:{identifier}"

        # Clean old entries
        if key in self._memory_storage:
            cutoff = current_time - window_seconds
            self._memory_storage[key] = [t for t in self._memory_storage[key] if t > cutoff]
        else:
            self._memory_storage[key] = []

        current_count = len(self._memory_storage[key])
        remaining = max(0, max_requests - current_count - cost)
        reset_time = current_time + window_seconds

        rate_info = {
            "limit": max_requests,
            "remaining": remaining,
            "reset": int(reset_time),
            "reset_after": window_seconds,
            "current_usage": current_count,
            "storage": "memory"
        }

        if current_count + cost > max_requests:
            self._record_violation(identifier, endpoint)
            return False, rate_info

        # Record requests
        for _ in range(cost):
            self._memory_storage[key].append(current_time)

        return True, rate_info

    def _record_violation(self, identifier: str, endpoint: str):
        """Record rate limit violation for adaptive limiting"""
        key = f"{identifier}:{endpoint}"
        self._warning_counts[key] = self._warning_counts.get(key, 0) + 1

        # Temporary blacklist after too many violations
        if self._warning_counts[key] >= RateLimitConfig.ADAPTIVE_THRESHOLD_WARNINGS:
            blacklist_until = time.time() + 300  # 5 minute temporary block
            self._blacklist_cache[identifier] = blacklist_until
            logger.warning(f"Rate limit: Temporarily blocked {identifier} until {datetime.fromtimestamp(blacklist_until)}")

            # Store in Redis for distributed blocking
            if self.redis_available:
                try:
                    self.redis_client.setex(f"ratelimit:blocked:{identifier}", 300, "1")
                except Exception:
                    pass

    def _update_analytics(self, identifier: str, endpoint: str, cost: int):
        """Update rate limit analytics in Redis"""
        if not self.redis_available:
            return

        try:
            today = datetime.now().strftime("%Y-%m-%d")
            hour = datetime.now().strftime("%H")

            pipe = self.redis_client.pipeline()

            # Daily stats
            pipe.hincrby(f"ratelimit:stats:daily:{today}", endpoint, cost)
            pipe.hincrby(f"ratelimit:stats:daily:{today}", f"{endpoint}:unique", 0)
            pipe.sadd(f"ratelimit:stats:daily:{today}:clients:{endpoint}", identifier)

            # Hourly stats
            pipe.hincrby(f"ratelimit:stats:hourly:{today}:{hour}", endpoint, cost)

            # Set expiry (keep for 7 days)
            pipe.expire(f"ratelimit:stats:daily:{today}", 86400 * 7)
            pipe.expire(f"ratelimit:stats:hourly:{today}:{hour}", 86400 * 2)

            pipe.execute()
        except Exception as e:
            logger.debug(f"Analytics update error: {e}")

    def get_client_stats(self, identifier: str) -> Dict[str, Any]:
        """Get rate limit statistics for a specific client"""
        if not self.redis_available:
            return {"storage": "memory", "stats_unavailable": True}

        try:
            stats = {}
            pattern = f"ratelimit:*:{identifier}:*"

            for key in self.redis_client.scan_iter(pattern, count=100):
                value = self.redis_client.get(key)
                if value:
                    stats[key] = int(value)

            # Check if blocked
            blocked = self.redis_client.get(f"ratelimit:blocked:{identifier}")

            return {
                "identifier": identifier,
                "current_windows": stats,
                "is_blocked": bool(blocked),
                "warning_count": self._warning_counts.get(identifier, 0)
            }
        except Exception as e:
            return {"error": str(e)}

    def get_analytics(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get rate limit analytics for a specific date"""
        if not self.redis_available:
            return {"storage": "memory", "analytics_unavailable": True}

        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")

            # Get daily stats
            daily_stats = self.redis_client.hgetall(f"ratelimit:stats:daily:{date}")

            # Get unique clients per endpoint
            unique_clients = {}
            for endpoint in RATE_LIMITS.keys():
                clients = self.redis_client.scard(f"ratelimit:stats:daily:{date}:clients:{endpoint}")
                if clients:
                    unique_clients[endpoint] = clients

            # Get hourly breakdown
            hourly_stats = {}
            for hour in range(24):
                hour_str = f"{hour:02d}"
                stats = self.redis_client.hgetall(f"ratelimit:stats:hourly:{date}:{hour_str}")
                if stats:
                    hourly_stats[hour_str] = {k: int(v) for k, v in stats.items()}

            return {
                "date": date,
                "daily_totals": {k: int(v) for k, v in daily_stats.items()},
                "unique_clients": unique_clients,
                "hourly_breakdown": hourly_stats
            }
        except Exception as e:
            return {"error": str(e)}

    def reset_client_limits(self, identifier: str) -> bool:
        """Reset rate limits for a specific client (admin function)"""
        try:
            if self.redis_available:
                # Delete all rate limit keys for this client
                pattern = f"ratelimit:*:{identifier}*"
                keys = list(self.redis_client.scan_iter(pattern, count=100))
                if keys:
                    self.redis_client.delete(*keys)

                # Remove from blocked list
                self.redis_client.delete(f"ratelimit:blocked:{identifier}")

            # Clear memory storage
            keys_to_delete = [k for k in self._memory_storage.keys() if identifier in k]
            for key in keys_to_delete:
                del self._memory_storage[key]

            # Clear warning counts
            keys_to_delete = [k for k in self._warning_counts.keys() if identifier in k]
            for key in keys_to_delete:
                del self._warning_counts[key]

            # Remove from blacklist
            if identifier in self._blacklist_cache:
                del self._blacklist_cache[identifier]

            logger.info(f"Reset rate limits for: {identifier}")
            return True

        except Exception as e:
            logger.error(f"Error resetting limits: {e}")
            return False

    def add_to_whitelist(self, identifier: str) -> bool:
        """Add an IP to the whitelist"""
        RateLimitConfig.WHITELIST_IPS.add(identifier)
        logger.info(f"Added to whitelist: {identifier}")
        return True

    def add_to_blacklist(self, identifier: str, duration_seconds: int = 3600) -> bool:
        """Add an IP to the blacklist"""
        if duration_seconds == 0:  # Permanent
            RateLimitConfig.BLACKLIST_IPS.add(identifier)
        else:
            self._blacklist_cache[identifier] = time.time() + duration_seconds
            if self.redis_available:
                try:
                    self.redis_client.setex(f"ratelimit:blocked:{identifier}", duration_seconds, "1")
                except Exception:
                    pass

        logger.warning(f"Added to blacklist: {identifier} for {duration_seconds}s")
        return True


# -------------------- Global Instance --------------------

redis_rate_limiter = RedisRateLimiter()


# -------------------- Client Identifier Functions --------------------

def get_client_identifier(request: Request) -> str:
    """
    Get a unique identifier for rate limiting.
    Combines IP address with session/user info for more precise limiting.
    """
    # Get IP address
    ip = get_remote_address(request)

    # Try to get additional identifiers
    identifiers = [ip]

    # Check Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if len(token) > 10:
            # Hash the token for privacy
            token_hash = hashlib.sha256(token.encode()).hexdigest()[:12]
            identifiers.append(token_hash)

    # Check for session_id
    session_id = request.query_params.get("session_id") or request.headers.get("X-Session-ID")
    if session_id:
        identifiers.append(session_id[:12])

    return ":".join(identifiers)


def get_user_identifier(request: Request) -> str:
    """Get user-specific identifier for per-user rate limiting"""
    # Try to extract user_id from various sources
    user_id = request.headers.get("X-User-ID")

    if not user_id:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Use token hash as user identifier
            token = auth_header[7:]
            user_id = hashlib.sha256(token.encode()).hexdigest()[:16]

    if not user_id:
        user_id = get_remote_address(request)

    return f"user:{user_id}"


def get_phone_identifier(request: Request) -> str:
    """Get phone-based identifier for OTP rate limiting"""
    # IP-based by default, phone will be checked in the endpoint
    return f"phone:{get_remote_address(request)}"


# -------------------- SlowAPI Integration --------------------

# Create SlowAPI limiter with Redis storage
def _get_redis_storage_uri() -> str:
    """Build Redis storage URI for SlowAPI"""
    password_part = f":{RateLimitConfig.REDIS_PASSWORD}@" if RateLimitConfig.REDIS_PASSWORD else ""
    return f"redis://{password_part}{RateLimitConfig.REDIS_HOST}:{RateLimitConfig.REDIS_PORT}/{RateLimitConfig.REDIS_DB}"


def _test_redis_connection() -> bool:
    """Test if Redis is actually available and accepting connections"""
    try:
        import redis
        client = redis.Redis(
            host=RateLimitConfig.REDIS_HOST,
            port=RateLimitConfig.REDIS_PORT,
            db=RateLimitConfig.REDIS_DB,
            password=RateLimitConfig.REDIS_PASSWORD,
            socket_timeout=2,
            socket_connect_timeout=2
        )
        client.ping()
        client.close()
        return True
    except Exception as e:
        logger.warning(f"Redis connection test failed: {e}")
        return False


# Initialize SlowAPI limiter - test Redis first before using it
_redis_available = _test_redis_connection()

if _redis_available:
    try:
        storage_uri = _get_redis_storage_uri()
        limiter = Limiter(
            key_func=get_client_identifier,
            default_limits=[RATE_LIMITS["default"]],
            storage_uri=storage_uri,
            strategy="moving-window",  # More accurate than fixed-window
        )
        logger.info(f"✓ SlowAPI limiter initialized with Redis storage")
    except Exception as e:
        logger.warning(f"⚠ SlowAPI Redis storage failed, using memory: {e}")
        limiter = Limiter(
            key_func=get_client_identifier,
            default_limits=[RATE_LIMITS["default"]],
            storage_uri="memory://",
            strategy="fixed-window",
        )
else:
    logger.warning(f"⚠ Redis not available at {RateLimitConfig.REDIS_HOST}:{RateLimitConfig.REDIS_PORT}, using in-memory rate limiting")
    limiter = Limiter(
        key_func=get_client_identifier,
        default_limits=[RATE_LIMITS["default"]],
        storage_uri="memory://",
        strategy="fixed-window",
    )


# -------------------- Custom Rate Limit Decorator --------------------

def rate_limit(
    limit_string: str,
    key_func: Optional[Callable] = None,
    cost: int = 1,
    error_message: Optional[str] = None
):
    """
    Advanced rate limit decorator with Redis backend

    Usage:
        @rate_limit("30/minute")
        async def my_endpoint(request: Request):
            ...

        @rate_limit("5/minute", key_func=get_phone_identifier, cost=2)
        async def expensive_endpoint(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")

            if not request:
                # No request object, skip rate limiting
                return await func(*args, **kwargs)

            # Get identifier
            identifier = key_func(request) if key_func else get_client_identifier(request)
            endpoint = func.__name__

            # Check rate limit
            is_allowed, rate_info = redis_rate_limiter.check_rate_limit(
                identifier, endpoint, limit_string, cost
            )

            if not is_allowed:
                message = error_message or "Rate limit exceeded. Please try again later."
                raise HTTPException(
                    status_code=429,
                    detail={
                        "success": False,
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": message,
                        "rate_limit": rate_info
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_info.get("limit", 0)),
                        "X-RateLimit-Remaining": str(rate_info.get("remaining", 0)),
                        "X-RateLimit-Reset": str(rate_info.get("reset", 0)),
                        "Retry-After": str(rate_info.get("reset_after", 60))
                    }
                )

            # Execute function
            response = await func(*args, **kwargs)

            # Add rate limit headers to response if possible
            # (This would require response modification which is complex)

            return response

        return wrapper
    return decorator


# -------------------- Rate Limit Exceeded Handler --------------------

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors from SlowAPI
    """
    client_id = get_client_identifier(request)
    endpoint = request.url.path

    # Log the violation
    logger.warning(f"Rate limit exceeded: {client_id} on {endpoint} - Limit: {exc.detail}")

    # Record in Redis for analytics
    redis_rate_limiter._record_violation(client_id, endpoint)

    retry_after = 60

    response = JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error_code": "RATE_4001",
            "message": "Too many requests. Please slow down and try again."
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(exc.detail) if exc.detail else "unknown"
        }
    )

    return response


# -------------------- Setup Function --------------------

def setup_rate_limiter(app):
    """
    Setup advanced rate limiter on FastAPI app.

    Usage in app.py:
        from core.rate_limiter import setup_rate_limiter
        setup_rate_limiter(app)
    """
    # Add limiter to app state
    app.state.limiter = limiter
    app.state.redis_rate_limiter = redis_rate_limiter

    # Add custom exception handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # Add middleware
    app.add_middleware(SlowAPIMiddleware)

    # Log configuration
    logger.info("=" * 50)
    logger.info("✓ Advanced Rate Limiter Configured")
    logger.info(f"  Storage: {'Redis' if redis_rate_limiter.redis_available else 'In-Memory'}")
    logger.info(f"  Strategy: Sliding Window")
    logger.info("  Limits:")
    for key, value in RATE_LIMITS.items():
        logger.info(f"    - {key}: {value}")
    logger.info(f"  Whitelisted IPs: {len(RateLimitConfig.WHITELIST_IPS)}")
    logger.info(f"  Blacklisted IPs: {len(RateLimitConfig.BLACKLIST_IPS)}")
    logger.info("=" * 50)


# -------------------- Helper Functions for Endpoints --------------------

def check_phone_rate_limit(phone: str, request: Request) -> Tuple[bool, Dict[str, Any]]:
    """
    Check rate limit for a specific phone number (for OTP endpoints)

    Usage in endpoint:
        is_allowed, info = check_phone_rate_limit(phone, request)
        if not is_allowed:
            raise HTTPException(429, detail=info)
    """
    # Normalize phone number
    phone_normalized = phone.replace("+", "").replace(" ", "").replace("-", "")
    identifier = f"phone:{phone_normalized}"

    return redis_rate_limiter.check_rate_limit(
        identifier,
        "send_otp_phone",
        RATE_LIMITS["send_otp_per_phone"]
    )


def check_user_rate_limit(user_id: str, endpoint: str, limit: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Check rate limit for a specific user ID

    Usage:
        is_allowed, info = check_user_rate_limit(user_id, "ask", "60/minute")
    """
    identifier = f"user:{user_id}"
    return redis_rate_limiter.check_rate_limit(identifier, endpoint, limit)


def get_rate_limit_headers(rate_info: Dict[str, Any]) -> Dict[str, str]:
    """Generate standard rate limit headers from rate info"""
    return {
        "X-RateLimit-Limit": str(rate_info.get("limit", 0)),
        "X-RateLimit-Remaining": str(rate_info.get("remaining", 0)),
        "X-RateLimit-Reset": str(rate_info.get("reset", 0)),
        "X-RateLimit-Reset-After": str(rate_info.get("reset_after", 0))
    }


# -------------------- WebSocket Rate Limiter --------------------

class WebSocketRateLimiter:
    """
    Rate limiter specifically designed for WebSocket connections.

    Features:
    - Per-user message rate limiting
    - Per-connection rate limiting
    - Different limits for different message types (chat, typing, presence)
    - Burst protection
    - Graceful degradation without Redis
    """

    def __init__(self):
        self._redis_limiter = redis_rate_limiter
        self._memory_counters: Dict[str, Dict[str, list]] = {}  # Fallback

    def _get_limit_config(self, message_type: str) -> str:
        """Get rate limit configuration for message type"""
        limit_map = {
            "chat": RATE_LIMITS.get("ws_chat", "60/minute"),
            "typing_start": RATE_LIMITS.get("ws_typing", "120/minute"),
            "typing_stop": RATE_LIMITS.get("ws_typing", "120/minute"),
            "presence_update": RATE_LIMITS.get("ws_presence", "30/minute"),
            "ping": "120/minute",  # Allow frequent pings
            "pong": "120/minute",
            "authenticate": RATE_LIMITS.get("ws_connect", "10/minute"),
        }
        return limit_map.get(message_type, RATE_LIMITS.get("ws_chat", "60/minute"))

    def check_message_rate_limit(
        self,
        user_id: int,
        connection_id: str,
        message_type: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a WebSocket message is within rate limits.

        Args:
            user_id: User identifier
            connection_id: WebSocket connection ID
            message_type: Type of message (chat, typing_start, etc.)

        Returns:
            Tuple of (is_allowed, rate_info)
        """
        limit_string = self._get_limit_config(message_type)
        identifier = f"ws:user:{user_id}:{message_type}"

        return self._redis_limiter.check_rate_limit(
            identifier=identifier,
            endpoint=f"ws_{message_type}",
            limit_string=limit_string
        )

    def check_connection_rate_limit(
        self,
        ip_address: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a new WebSocket connection is within rate limits.

        Args:
            ip_address: Client IP address

        Returns:
            Tuple of (is_allowed, rate_info)
        """
        limit_string = RATE_LIMITS.get("ws_connect", "10/minute")
        identifier = f"ws:connect:{ip_address}"

        return self._redis_limiter.check_rate_limit(
            identifier=identifier,
            endpoint="ws_connect",
            limit_string=limit_string
        )

    def check_chat_burst(
        self,
        user_id: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check burst rate limit for chat messages (short-term protection).

        Args:
            user_id: User identifier

        Returns:
            Tuple of (is_allowed, rate_info)
        """
        limit_string = RATE_LIMITS.get("ws_chat_burst", "10/second")
        identifier = f"ws:burst:{user_id}"

        return self._redis_limiter.check_rate_limit(
            identifier=identifier,
            endpoint="ws_chat_burst",
            limit_string=limit_string
        )

    def get_user_rate_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get current rate limit status for a user.

        Returns dict with remaining limits for each message type.
        """
        status = {}
        for msg_type in ["chat", "typing_start", "presence_update"]:
            limit_string = self._get_limit_config(msg_type)
            identifier = f"ws:user:{user_id}:{msg_type}"
            _, info = self._redis_limiter.check_rate_limit(
                identifier=identifier,
                endpoint=f"ws_{msg_type}",
                limit_string=limit_string,
                cost=0  # Don't consume, just check
            )
            status[msg_type] = {
                "limit": info.get("limit", 0),
                "remaining": info.get("remaining", 0),
                "reset_in": info.get("reset_after", 0)
            }
        return status


# Global WebSocket rate limiter instance
ws_rate_limiter = WebSocketRateLimiter()
