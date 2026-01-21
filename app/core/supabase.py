# Supabase JWT verification using JWKS (modern approach)
import jwt
from jwt import PyJWKClient
from typing import Optional
import logging

from .config import get_settings

logger = logging.getLogger(__name__)

# Cache for JWKS client
_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> Optional[PyJWKClient]:
    """Get or create JWKS client for Supabase."""
    global _jwks_client
    if _jwks_client is None:
        settings = get_settings()
        if not settings.supabase_url:
            logger.error("Supabase URL not configured")
            return None
        
        # JWKS endpoint for Supabase
        jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
        logger.info(f"JWKS client initialized for {settings.supabase_url}")
    
    return _jwks_client


def verify_supabase_token(access_token: str) -> Optional[dict]:
    """Verify Supabase JWT using JWKS and return decoded payload or None if invalid."""
    jwks_client = get_jwks_client()
    
    if jwks_client is None:
        logger.error("JWKS client not available")
        return None
    
    try:
        # Get the signing key from JWKS based on token's kid
        signing_key = jwks_client.get_signing_key_from_jwt(access_token)
        
        # Verify and decode the token
        decoded = jwt.decode(
            access_token,
            signing_key.key,
            algorithms=["RS256"],
            audience="authenticated",
        )
        return decoded
    except jwt.ExpiredSignatureError:
        logger.warning("Supabase token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid Supabase token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None


def get_user_id_from_token(decoded: dict) -> Optional[str]:
    """Extract user ID from decoded Supabase token."""
    return decoded.get("sub")


def get_email_from_token(decoded: dict) -> Optional[str]:
    """Extract email from decoded Supabase token."""
    return decoded.get("email")
