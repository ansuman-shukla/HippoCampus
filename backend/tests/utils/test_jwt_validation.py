
import pytest
from unittest.mock import patch
from jose import jwt, JWTError
from app.utils.jwt import decodeJWT, TokenExpiredError
from app.core.config import Settings
import time

# A dummy secret for testing
TEST_SECRET = "your-test-secret"
TEST_URL = "https://test.supabase.co"

def create_test_token(payload, secret=TEST_SECRET, algorithm="HS256"):
    """Creates a JWT token for testing."""
    return jwt.encode(payload, secret, algorithm=algorithm)

@pytest.fixture
def mock_settings():
    """Fixture to mock the application settings."""
    return Settings(
        SUPABASE_URL=TEST_URL,
        SUPABASE_JWT_SECRET=TEST_SECRET,
        SUPABASE_API_KEY="test",
        SUPABASE_ANON_KEY="test",
        MONGODB_DB="test",
        MONGODB_URI="test",
        PINECONE_API_KEY="test",
        PINECONE_INDEX="test",
        GEMINI_API_KEY="test",
        MONGODB_COLLECTION_USER="test",
        MONGODB_COLLECTION_NOTES="test",
        MONGODB_COLLECTION_MEMORIES="test"
    )

@pytest.mark.asyncio
async def test_decode_valid_jwt(mock_settings):
    """Tests decoding of a valid JWT token."""
    with patch('app.utils.jwt.settings', mock_settings):
        payload = {
            "sub": "1234567890",
            "iss": TEST_URL,
            "aud": "authenticated",
            "exp": int(time.time()) + 3600  # Expires in 1 hour
        }
        token = create_test_token(payload)
        decoded_payload = await decodeJWT(token)
        assert decoded_payload["sub"] == "1234567890"

@pytest.mark.asyncio
async def test_decode_invalid_signature(mock_settings):
    """Tests decoding of a JWT with an invalid signature."""
    with patch('app.utils.jwt.settings', mock_settings):
        payload = {"sub": "1234567890"}
        token = create_test_token(payload, secret="wrong-secret")
        with pytest.raises(JWTError):
            await decodeJWT(token)

@pytest.mark.asyncio
async def test_decode_expired_token(mock_settings):
    """Tests decoding of an expired JWT token."""
    with patch('app.utils.jwt.settings', mock_settings):
        payload = {
            "sub": "1234567890",
            "iss": TEST_URL,
            "aud": "authenticated",
            "exp": int(time.time()) - 3600  # Expired 1 hour ago
        }
        token = create_test_token(payload)
        with pytest.raises(TokenExpiredError):
            await decodeJWT(token)
