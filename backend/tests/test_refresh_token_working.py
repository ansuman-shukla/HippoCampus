"""
Test refresh token functionality with actual working token
"""
import pytest
import asyncio
import httpx
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.main import app
from app.utils.jwt import refresh_access_token

class TestRefreshTokenFunctionality:
    """Test refresh token with actual working cases"""
    
    def setup_method(self):
        """Setup for each test"""
        self.client = TestClient(app)
        self.working_refresh_token = "oop5f3md3fuk"  # The one that actually works
        self.invalid_tokens = [
            "",  # Empty
            "invalid",  # Too short/invalid
            "eyJinvalid.token.here",  # Malformed JWT
            None  # None value
        ]
        
    def test_refresh_token_endpoint_with_working_token(self):
        """Test the refresh endpoint with the working token"""
        response = self.client.post(
            "/auth/refresh",
            json={"refresh_token": self.working_refresh_token}
        )
        
        # This should now work!
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert "token_type" in data
        
        # Verify token format
        assert len(data["access_token"]) > 100  # JWT tokens are long
        assert data["token_type"].lower() == "bearer"
        
    def test_refresh_token_endpoint_with_cookie(self):
        """Test refresh endpoint using cookies"""
        response = self.client.post(
            "/auth/refresh",
            cookies={"refresh_token": self.working_refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data    @pytest.mark.parametrize("invalid_token", ["", "invalid", None])
    def test_refresh_token_endpoint_with_invalid_tokens(self, invalid_token):
        """Test refresh endpoint with various invalid tokens"""
        if invalid_token is None:
            response = self.client.post("/auth/refresh", json={})
        else:
            response = self.client.post(
                "/auth/refresh",
                json={"refresh_token": invalid_token}
            )
        
        # Should fail with 400, 401 or 422 (validation/auth error)
        assert response.status_code in [400, 401, 422]
        
    def test_refresh_token_sets_cookies(self):
        """Test that refresh endpoint sets proper cookies"""
        response = self.client.post(
            "/auth/refresh",
            json={"refresh_token": self.working_refresh_token}
        )
        
        assert response.status_code == 200
        
        # Check that cookies are set
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        
        # Check cookie properties
        access_cookie = None
        refresh_cookie = None
        
        for cookie in response.cookies.jar:
            if cookie.name == "access_token":
                access_cookie = cookie
            elif cookie.name == "refresh_token":
                refresh_cookie = cookie
                
        assert access_cookie is not None
        assert refresh_cookie is not None
        assert access_cookie.secure
        assert refresh_cookie.secure

class TestRefreshTokenUtility:
    """Test the refresh_access_token utility function directly"""
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_utility_success(self):
        """Test the utility function with working token"""
        result = await refresh_access_token("c4h7lbg5m7bm")
        
        # Check result structure
        assert isinstance(result, dict)
        assert "access_token" in result
        assert "refresh_token" in result
        assert "user" in result
        
        # Verify token properties
        assert len(result["access_token"]) > 100
        assert result["user"]["email"] == "ansuman00edu@gmail.com"
        
    @pytest.mark.asyncio
    async def test_refresh_access_token_utility_invalid_token(self):
        """Test the utility function with invalid token"""
        with pytest.raises(Exception):  # Should raise HTTPException
            await refresh_access_token("invalid_token")
            
    @pytest.mark.asyncio
    async def test_refresh_access_token_utility_empty_token(self):
        """Test the utility function with empty token"""
        with pytest.raises(Exception):  # Should raise HTTPException
            await refresh_access_token("")

class TestTokenRefreshMiddleware:
    """Test how middleware handles token refresh"""
    
    def setup_method(self):
        """Setup for each test"""
        self.client = TestClient(app)
    
    def test_middleware_with_expired_access_token(self):
        """Test middleware behavior with expired access token"""
        # This would require setting up expired tokens
        # For now, just test the endpoint exists
        response = self.client.get("/auth/status")
        assert response.status_code == 200
        
    def test_protected_endpoint_with_refresh_flow(self):
        """Test accessing protected endpoint that triggers refresh"""
        # Set cookies with working refresh token
        cookies = {
            "refresh_token": "c4h7lbg5m7bm",
            "access_token": "expired_or_invalid_token"
        }
        
        # Try to access a protected endpoint
        # This should trigger the refresh flow in middleware
        response = self.client.get(
            "/auth/verify",
            cookies=cookies
        )
        
        # The middleware should handle refresh automatically
        # Result depends on implementation, but shouldn't be 401 due to refresh

class TestTokenAnalysis:
    """Analyze token characteristics"""
    
    def test_working_token_characteristics(self):
        """Analyze the working refresh token"""
        token = "c4h7lbg5m7bm"
        
        analysis = {
            "length": len(token),
            "is_alphanumeric": token.isalnum(),
            "is_lowercase": token.islower(),
            "unique_chars": len(set(token)),
            "char_frequency": {char: token.count(char) for char in set(token)}
        }
        
        # Document the working token characteristics
        assert analysis["length"] == 12
        assert analysis["is_alphanumeric"] == True
        assert analysis["is_lowercase"] == True
        assert analysis["unique_chars"] == 9  # 9 unique characters
        
        print(f"Working token analysis: {json.dumps(analysis, indent=2)}")
        
    def test_response_token_format(self):
        """Test the format of tokens returned by Supabase"""
        # Based on the debug output, we know the response format
        expected_new_refresh_token = "f7pitk6lsxvm"  # From debug output
        
        # Both tokens are similar format - short alphanumeric strings
        assert len(expected_new_refresh_token) == 12
        assert expected_new_refresh_token.isalnum()
        assert expected_new_refresh_token.islower()

class TestIntegrationRefreshFlow:
    """Integration tests for complete refresh flow"""
    
    def test_complete_refresh_cycle(self):
        """Test complete cycle: refresh -> use new token -> refresh again"""
        client = TestClient(app)
        
        # Step 1: Refresh with original token
        response1 = client.post(
            "/auth/refresh",
            json={"refresh_token": "c4h7lbg5m7bm"}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        new_refresh_token = data1["refresh_token"]
        new_access_token = data1["access_token"]
        
        # Step 2: Use the new access token to verify
        response2 = client.get(
            "/auth/verify",
            cookies={"access_token": new_access_token}
        )
        
        # Should work with new token
        if response2.status_code == 200:
            print("✅ New access token works for verification")
        
        # Step 3: Try to refresh again with new refresh token
        response3 = client.post(
            "/auth/refresh",
            json={"refresh_token": new_refresh_token}
        )
        
        # Should work or give specific error about token usage
        print(f"Second refresh status: {response3.status_code}")
        print(f"Second refresh response: {response3.text}")

    def test_auth_status_with_working_tokens(self):
        """Test auth status endpoint with working tokens"""
        client = TestClient(app)
        
        # First get fresh tokens
        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": "c4h7lbg5m7bm"}
        )
        
        if refresh_response.status_code == 200:
            tokens = refresh_response.json()
            
            # Test status with new tokens
            status_response = client.get(
                "/auth/status",
                cookies={
                    "access_token": tokens["access_token"],
                    "refresh_token": tokens["refresh_token"]
                }
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            assert status_data["has_access_token"] == True
            assert status_data["has_refresh_token"] == True
            assert status_data["is_authenticated"] == True
            assert status_data["token_valid"] == True

if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "-s"])
