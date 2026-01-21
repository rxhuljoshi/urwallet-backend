# Supabase JWT verification - supports both HS256 (legacy) and RS256 (new)
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
        
        jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        try:
            _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
            logger.info(f"JWKS client initialized for {settings.supabase_url}")
        except Exception as e:
            logger.warning(f"Could not initialize JWKS client: {e}")
            return None
    
    return _jwks_client


def verify_supabase_token(access_token: str) -> Optional[dict]:
    """Verify Supabase JWT - tries RS256 (JWKS) first, falls back to HS256."""
    settings = get_settings()
    
    # First, decode without verification to check the algorithm
    try:
        unverified = jwt.decode(access_token, options={"verify_signature": False})
        header = jwt.get_unverified_header(access_token)
        alg = header.get("alg", "HS256")
    except Exception as e:
        logger.warning(f"Could not decode token header: {e}")
        return None
    
    # Try RS256 with JWKS if that's the algorithm
    if alg == "RS256":
        jwks_client = get_jwks_client()
        if jwks_client:
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(access_token)
                decoded = jwt.decode(
                    access_token,
                    signing_key.key,
                    algorithms=["RS256"],
                    audience="authenticated",
                )
                return decoded
            except Exception as e:
                logger.warning(f"RS256 verification failed: {e}")
                return None
    
    # Fall back to HS256 with JWT secret
    if alg == "HS256":
        if not settings.supabase_jwt_secret:
            logger.error("Supabase JWT secret not configured for HS256 token")
            return None
        
        try:
            decoded = jwt.decode(
                access_token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            return decoded
        except jwt.ExpiredSignatureError:
            logger.warning("Supabase token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid Supabase token: {e}")
            return None
    
    logger.warning(f"Unsupported algorithm: {alg}")
    return None


def get_user_id_from_token(decoded: dict) -> Optional[str]:
    """Extract user ID from decoded Supabase token."""
    return decoded.get("sub")


def get_email_from_token(decoded: dict) -> Optional[str]:
    """Extract email from decoded Supabase token."""
    return decoded.get("email")
