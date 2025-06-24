import pytest
from jose import jwt, JWTError
from fastapi import HTTPException
from app.utils.jwt import decodeJWT
from app.core.config import settings
import os

# A known valid JWT secret for testing
VALID_SECRET = "your-256-bit-secret"
# A different secret to test invalid signature
INVALID_SECRET = "another-256-bit-secret"

# Override the settings for testing
os.environ["SUPABASE_JWT_SECRET"] = VALID_SECRET
os.environ["SUPABASE_URL"] = "http://test.supabase.co"


def create_test_token(payload, secret, algorithm="HS256"):
    """Helper to create a token for testing."""
    return jwt.encode(payload, secret, algorithm=algorithm)

@pytest.mark.asyncio
async def test_decode_jwt_valid_token():
    """Test decoding a valid JWT with the correct secret."""
    payload = {
        "sub": "1234567890",
        "name": "John Doe",
        "iat": 1516239022,
        "exp": 9999999999,  # Non-expiring for test
        "aud": "authenticated",
        "iss": "http://test.supabase.co"
    }
    token = create_test_token(payload, VALID_SECRET)
    
    # Temporarily set the correct secret in settings
    original_secret = settings.SUPABASE_JWT_SECRET
    settings.SUPABASE_JWT_SECRET = VALID_SECRET
    
    decoded_payload = await decodeJWT(f"Bearer {token}")
    assert decoded_payload["sub"] == payload["sub"]
    
    # Restore original secret
    settings.SUPABASE_JWT_SECRET = original_secret

@pytest.mark.asyncio
async def test_decode_jwt_invalid_signature():
    """Test decoding a JWT with an invalid signature (wrong secret)."""
    payload = {
        "sub": "1234567890",
        "name": "John Doe",
        "iat": 1516239022,
        "exp": 9999999999,
        "aud": "authenticated",
        "iss": "http://test.supabase.co"
    }
    # Token created with a different secret
    token = create_test_token(payload, INVALID_SECRET)
    
    # Temporarily set the correct secret in settings for decoding attempt
    original_secret = settings.SUPABASE_JWT_SECRET
    settings.SUPABASE_JWT_SECRET = VALID_SECRET

    with pytest.raises(HTTPException) as exc_info:
        await decodeJWT(f"Bearer {token}")
    
    assert exc_info.value.status_code == 401
    assert "Signature verification failed" in exc_info.value.detail

    # Restore original secret
    settings.SUPABASE_JWT_SECRET = original_secret
