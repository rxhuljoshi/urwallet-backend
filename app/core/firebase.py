# Firebase Admin SDK setup
import firebase_admin
from firebase_admin import auth, credentials
from pathlib import Path
from typing import Optional
import logging

from .config import get_settings

logger = logging.getLogger(__name__)

_firebase_app: Optional[firebase_admin.App] = None


def init_firebase() -> None:
    global _firebase_app
    if _firebase_app is not None:
        return
    
    settings = get_settings()
    cred_path = Path(settings.firebase_credentials_path)
    
    if not cred_path.exists():
        logger.warning(f"Firebase creds not found at {cred_path}")
        return
    
    try:
        cred = credentials.Certificate(str(cred_path))
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized")
    except Exception as e:
        logger.error(f"Failed to init Firebase: {e}")


def verify_firebase_token(id_token: str) -> Optional[dict]:
    """Returns decoded token dict or None if invalid/expired."""
    if _firebase_app is None:
        logger.error("Firebase not initialized")
        return None
    
    try:
        return auth.verify_id_token(id_token)
    except auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase token")
        return None
    except auth.ExpiredIdTokenError:
        logger.warning("Expired Firebase token")
        return None
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None


def get_firebase_user(uid: str) -> Optional[auth.UserRecord]:
    if _firebase_app is None:
        return None
    
    try:
        return auth.get_user(uid)
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        logger.error(f"Error fetching Firebase user: {e}")
        return None
