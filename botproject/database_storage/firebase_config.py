"""
Firebase Admin SDK Configuration
Singleton pattern for Firebase Admin initialization
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)


class FirebaseAdmin:
    """Singleton class for Firebase Admin SDK initialization"""

    _instance: Optional[firebase_admin.App] = None
    _initialized: bool = False

    @classmethod
    def get_instance(cls) -> Optional[firebase_admin.App]:
        """Get or create Firebase Admin instance"""
        if cls._initialized:
            return cls._instance

        try:
            # Get service account path from environment
            service_account_path = os.getenv(
                "FIREBASE_SERVICE_ACCOUNT_PATH",
                "eazrapp-firebase-adminsdk.json"
            )

            # Build absolute path
            base_dir = Path(__file__).parent.parent
            full_path = base_dir / service_account_path

            if not full_path.exists():
                logger.error(f"Firebase service account file not found: {full_path}")
                cls._initialized = True
                return None

            # Load credentials
            cred = credentials.Certificate(str(full_path))

            # Initialize Firebase Admin
            cls._instance = firebase_admin.initialize_app(cred)
            cls._initialized = True

            logger.info("Firebase Admin SDK initialized successfully")
            return cls._instance

        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin: {e}")
            cls._initialized = True
            return None

    @classmethod
    def is_available(cls) -> bool:
        """Check if Firebase is available"""
        if not cls._initialized:
            cls.get_instance()
        return cls._instance is not None


# Initialize on module load
firebase_app = FirebaseAdmin.get_instance()


def get_firebase_app() -> Optional[firebase_admin.App]:
    """Get Firebase app instance"""
    return FirebaseAdmin.get_instance()


def is_firebase_available() -> bool:
    """Check if Firebase is available"""
    return FirebaseAdmin.is_available()
