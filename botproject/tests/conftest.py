"""
Pytest Configuration and Shared Fixtures
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "user_id": 12345,
        "name": "Test User",
        "phone": "+919876543210",
        "email": "test@example.com",
        "dob": "1990-01-15",
        "gender": "male",
        "address": "123 Test Street"
    }

@pytest.fixture
def sample_chat_data():
    """Sample chat data for testing"""
    return {
        "session_id": "test_session_123",
        "user_id": 12345,
        "title": "Test Chat",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    }

@pytest.fixture
def sample_policy_data():
    """Sample policy data for testing"""
    return {
        "policy_number": "POL123456",
        "policy_type": "health",
        "premium": 5000,
        "coverage": 500000,
        "start_date": "2024-01-01",
        "end_date": "2025-01-01"
    }

@pytest.fixture
def valid_phone_numbers():
    """Valid phone numbers for testing"""
    return [
        "+919876543210",
        "9876543210",
        "+918888888888"
    ]

@pytest.fixture
def invalid_phone_numbers():
    """Invalid phone numbers for testing"""
    return [
        "123",
        "abc",
        "98765432",  # Too short
        "98765432109",  # Too long
        "+1234567890",  # Wrong country code
    ]

@pytest.fixture
def valid_emails():
    """Valid email addresses for testing"""
    return [
        "test@example.com",
        "user.name@company.co.in",
        "admin123@test.org"
    ]

@pytest.fixture
def invalid_emails():
    """Invalid email addresses for testing"""
    return [
        "notanemail",
        "@example.com",
        "user@",
        "user @example.com",
        "user@exam ple.com"
    ]


# Service-specific fixtures for Phase 5 testing

@pytest.fixture
def mock_mongodb_manager():
    """Mock MongoDB manager for service testing"""
    from unittest.mock import Mock
    manager = Mock()
    manager.users_collection = Mock()
    manager.sessions_collection = Mock()
    manager.messages_collection = Mock()
    manager.chat_sessions_collection = Mock()
    manager.policy_applications_collection = Mock()
    manager.policy_analyses_collection = Mock()
    manager.activities_collection = Mock()
    manager.claim_guidance_collection = Mock()
    return manager


@pytest.fixture
def mock_redis_session():
    """Mock Redis session for testing"""
    return {
        "session_id": "test_session_123",
        "user_id": 12345,
        "phone": "+919876543210",
        "user_name": "Test User",
        "access_token": "test_token_abc123",
        "active": True,
        "created_at": "2024-01-01T00:00:00",
        "last_activity": "2024-01-15T00:00:00"
    }


@pytest.fixture
def sample_user_profile():
    """Complete user profile for testing"""
    return {
        "user_id": 12345,
        "eazr_user_id": "12345",
        "preferences": {
            "phone": "+919876543210",
            "user_name": "Test User",
            "full_name": "Test Full Name",
            "profile_pic": "https://example.com/pic.jpg",
            "gender": "male",
            "dob": "1990-01-15",
            "age": 34,
            "app_platform": "android",
            "android_version": "1.0.0",
            "registration_date": "2024-01-01T00:00:00",
            "last_login": "2024-01-15T00:00:00",
            "login_count": 5,
            "profile_completion_score": 100
        },
        "language_preference": "en",
        "interests": ["finance", "insurance"],
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-15T00:00:00",
        "deleted": False,
        "status": "active"
    }


@pytest.fixture
def sample_chat_session():
    """Sample chat session for testing"""
    from datetime import datetime
    return {
        "session_id": "chat_12345_123456_abcd",
        "user_id": 12345,
        "session_type": "chat_session",
        "title": "Insurance Inquiry",
        "created_at": datetime.utcnow(),
        "last_activity": datetime.utcnow(),
        "message_count": 10,
        "active": True,
        "deleted": False,
        "is_archived": False
    }


@pytest.fixture
def sample_chat_messages():
    """Sample chat messages for testing"""
    from datetime import datetime
    return [
        {
            "message_id": "msg_1",
            "session_id": "chat_12345_123456_abcd",
            "user_id": 12345,
            "role": "user",
            "content": "What is health insurance?",
            "timestamp": datetime.utcnow()
        },
        {
            "message_id": "msg_2",
            "session_id": "chat_12345_123456_abcd",
            "user_id": 12345,
            "role": "assistant",
            "content": "Health insurance is a type of insurance that covers medical expenses.",
            "timestamp": datetime.utcnow()
        }
    ]


@pytest.fixture
def sample_policy_analysis():
    """Sample policy analysis result for testing"""
    return {
        "_id": "policy_analysis_123",
        "user_id": "12345",
        "session_id": "session_123",
        "filename": "health_policy.pdf",
        "insurance_type": "health",
        "analysis_result": {
            "success": True,
            "policy_type": "health",
            "insurer": "ABC Insurance",
            "policy_number": "POL123456",
            "coverage_amount": 500000,
            "premium": 5000,
            "key_benefits": ["Hospitalization", "Pre-post hospitalization", "Daycare procedures"],
            "exclusions": ["Pre-existing diseases for 2 years", "Dental treatment"]
        },
        "s3_url": "https://s3.com/policy.pdf",
        "created_at": "2024-01-15T00:00:00"
    }


@pytest.fixture
def sample_otp_response():
    """Sample OTP verification response from eazr.in"""
    return {
        "message": "Login Successfully",
        "data": {
            "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "id": "12345",
            "name": "Test User",
            "contactNumber": "9876543210"
        }
    }


@pytest.fixture
def sample_admin_credentials():
    """Sample admin credentials for testing"""
    return {
        "username": "testadmin",
        "password": "testpass123"
    }


@pytest.fixture
def mock_storage_health():
    """Mock storage health check response"""
    return {
        "redis_connected": True,
        "latency": "2ms",
        "memory_used": "10MB",
        "total_keys": 150
    }


@pytest.fixture
def mock_claim_guidance():
    """Mock claim guidance data"""
    return {
        "insurance_type": "health",
        "query": "How do I file a claim?",
        "response": "To file a health insurance claim, follow these steps: 1. Collect all medical documents...",
        "suggestions": [
            "Upload medical bills",
            "Submit claim form",
            "Track claim status online"
        ]
    }
