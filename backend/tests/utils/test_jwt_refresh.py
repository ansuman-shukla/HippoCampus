
import pytest
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException
from app.utils.jwt import refresh_access_token
from app.core.config import settings
import os

# Override settings for testing
os.environ["SUPABASE_URL"] = "http://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test_anon_key"

@pytest.mark.asyncio
async def test_refresh_access_token_success():
    """Test successful token refresh."""
    mock_response = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 3600
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        
        result = await refresh_access_token("valid_refresh_token")
        
        assert result["access_token"] == "new_access_token"
        assert result["refresh_token"] == "new_refresh_token"

@pytest.mark.asyncio
async def test_refresh_access_token_failure():
    """Test failed token refresh."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 401
        mock_post.return_value.json.return_value = {"error": "invalid_grant", "error_description": "Invalid refresh token"}
        
        with pytest.raises(HTTPException) as exc_info:
            await refresh_access_token("invalid_refresh_token")
            
        assert exc_info.value.status_code == 401
        assert "Token refresh failed" in exc_info.value.detail

@pytest.mark.asyncio
async def test_refresh_access_token_no_token():
    """Test refresh with no token provided."""
    with pytest.raises(HTTPException) as exc_info:
        await refresh_access_token(None)
    assert exc_info.value.status_code == 401
    assert "Invalid refresh token" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        await refresh_access_token("   ")
    assert exc_info.value.status_code == 401
    assert "Invalid refresh token" in exc_info.value.detail
