# Correct import for PyJWT (change this in your app.py)
import jwt  # This is correct - PyJWT package is imported as 'jwt'
from datetime import datetime, timedelta
import hashlib
import time
import requests
import os
import logging
print('d')

logger = logging.getLogger(__name__)

# Configuration constants - Load from environment variables
MSG91_AUTH_KEY = os.getenv("MSG91_AUTH_KEY")
if not MSG91_AUTH_KEY:
    raise ValueError("MSG91_AUTH_KEY environment variable must be set")

MSG91_TEMPLATE_ID = os.getenv("MSG91_TEMPLATE_ID")
if not MSG91_TEMPLATE_ID:
    raise ValueError("MSG91_TEMPLATE_ID environment variable must be set")

MSG91_SEND_OTP_URL = "https://api.msg91.com/api/v5/otp"
MSG91_VERIFY_OTP_URL = "https://api.msg91.com/api/v5/otp/verify"

# JWT Configuration
# Support both JWT_SECRET (your format) and JWT_SECRET_KEY (old format)
JWT_SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    # Fallback to default for development (should be set in production)
    JWT_SECRET_KEY = "eazr-jwt"
    logger.warning("Using default JWT_SECRET. Set JWT_SECRET environment variable in production!")

# JWT Expiration - support JWT_EXPIRATION or default to 1 week
JWT_EXPIRATION = os.getenv("JWT_EXPIRATION", "1w")  # 1w = 1 week

# Convert JWT_EXPIRATION to hours
def parse_jwt_expiration(expiration_str: str) -> int:
    """Parse JWT expiration string to hours (e.g., '1w' = 168 hours, '7d' = 168 hours, '24h' = 24 hours)"""
    expiration_str = expiration_str.lower().strip()

    if expiration_str.endswith('w'):  # weeks
        weeks = int(expiration_str[:-1])
        return weeks * 7 * 24
    elif expiration_str.endswith('d'):  # days
        days = int(expiration_str[:-1])
        return days * 24
    elif expiration_str.endswith('h'):  # hours
        return int(expiration_str[:-1])
    else:
        # Default to hours if no unit specified
        return int(expiration_str)

JWT_EXPIRATION_HOURS = parse_jwt_expiration(JWT_EXPIRATION)

JWT_ALGORITHM = "HS256"

logger.info(f"JWT Configuration: Secret={'***' + JWT_SECRET_KEY[-4:] if len(JWT_SECRET_KEY) > 4 else '***'}, Expiration={JWT_EXPIRATION} ({JWT_EXPIRATION_HOURS} hours), Algorithm={JWT_ALGORITHM}")

def generate_user_id(phone: str) -> int:
    """Generate a consistent user_id based on phone number"""
    phone_hash = hashlib.md5(phone.encode()).hexdigest()
    user_id = int(phone_hash[:8], 16) % 1000000
    return user_id

def create_jwt_token(user_id: int, phone: str, name: str, ip_address: str = None, user_agent: str = None, expiry_hours: int = None) -> str:
    """
    Create JWT token with configurable expiry

    Args:
        user_id: User ID
        phone: Phone number
        name: User name
        ip_address: Client IP address
        user_agent: Client user agent
        expiry_hours: Token expiry in hours (default: uses JWT_EXPIRATION_HOURS from config)
    """
    current_time = int(time.time())

    # Use configured JWT_EXPIRATION_HOURS if not specified
    if expiry_hours is None:
        expiry_hours = JWT_EXPIRATION_HOURS

    payload = {
        "id": user_id,
        "contactNumber": phone,
        "name": name,
        "ip": ip_address or "unknown",
        "userAgent": user_agent or "unknown",
        "role": "user",
        "timestamp": str(current_time * 1000),
        "iat": current_time,
        "exp": current_time + (expiry_hours * 60 * 60)  # Configurable expiry
    }
    
    try:
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        # Handle both PyJWT 1.x (returns bytes) and 2.x (returns string)
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        return token
    except Exception as e:
        logger.error(f"Error creating JWT token: {e}")
        raise

def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return {"valid": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "Invalid token"}
    except Exception as e:
        return {"valid": False, "error": str(e)}