"""
Comprehensive tests for refresh token functionality
"""
import pytest
import asyncio
import httpx
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.main import app
from app.routers.auth_router import refresh_access_token
from app.utils.jwt import decode_token

class TestRefreshToken:
    """Test cases for refresh token functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.client = TestClient(app)
        self.valid_refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNjk0MTM0ODAwLCJpYXQiOjE2OTQxMzEyMDAsInN1YiI6IjEyMzQ1Njc4LTEyMzQtMTIzNC0xMjM0LTEyMzQ1Njc4OTAxMiJ9.test_signature"
        self.invalid_short_token = "c4h7lbg5m7bm"
        self.malformed_token = "invalid.token.here"
        
    def test_refresh_token_invalid_short_token(self):
        """Test the specific failing case with short token"""
        response = self.client.post(
            "/auth/refresh",
            json={"refresh_token": self.invalid_short_token}
        )
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
        
    def test_refresh_token_malformed_token(self):
        """Test with malformed token"""
        response = self.client.post(
            "/auth/refresh",
            json={"refresh_token": self.malformed_token}
        )
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
        
    def test_refresh_token_empty_token(self):
        """Test with empty token"""
        response = self.client.post(
            "/auth/refresh",
            json={"refresh_token": ""}
        )
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
        
    def test_refresh_token_missing_field(self):
        """Test with missing refresh_token field"""
        response = self.client.post(
            "/auth/refresh",
            json={}
        )
        
        assert response.status_code == 422  # Pydantic validation error
        
    @patch('app.routers.auth_router.supabase')
    def test_refresh_token_supabase_success(self, mock_supabase):
        """Test successful refresh token with mocked Supabase"""
        # Mock successful Supabase response
        mock_response = MagicMock()
        mock_response.user = MagicMock()
        mock_response.user.id = "test-user-id"
        mock_response.session = MagicMock()
        mock_response.session.access_token = "new-access-token"
        mock_response.session.refresh_token = "new-refresh-token"
        
        mock_supabase.auth.refresh_session.return_value = mock_response
        
        response = self.client.post(
            "/auth/refresh",
            json={"refresh_token": self.valid_refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] == "new-access-token"
        assert data["refresh_token"] == "new-refresh-token"
        
    @patch('app.routers.auth_router.supabase')
    def test_refresh_token_supabase_error(self, mock_supabase):
        """Test Supabase error response"""
        # Mock Supabase error
        mock_supabase.auth.refresh_session.side_effect = Exception("Invalid refresh token")
        
        response = self.client.post(
            "/auth/refresh",
            json={"refresh_token": self.valid_refresh_token}
        )
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
        
    @patch('app.routers.auth_router.supabase')
    def test_refresh_token_supabase_null_response(self, mock_supabase):
        """Test Supabase null response"""
        # Mock Supabase returning None/null
        mock_supabase.auth.refresh_session.return_value = None
        
        response = self.client.post(
            "/auth/refresh",
            json={"refresh_token": self.valid_refresh_token}
        )
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

class TestRefreshTokenValidation:
    """Test token validation logic"""
    
    def test_token_length_validation(self):
        """Test various token lengths"""
        short_tokens = ["abc", "c4h7lbg5m7bm", "123456789"]
        
        for token in short_tokens:
            assert len(token) < 50, f"Token {token} should be considered short"
            
    def test_token_format_validation(self):
        """Test token format validation"""
        # JWT-like tokens typically start with 'eyJ'
        jwt_like_tokens = [
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature",
            "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"
        ]
        
        for token in jwt_like_tokens:
            assert token.startswith("eyJ"), f"Token {token} should start with 'eyJ'"
            parts = token.split(".")
            assert len(parts) == 3, f"JWT token should have 3 parts, got {len(parts)}"

class TestTokenDebugHelpers:
    """Helper functions for debugging tokens"""
    
    def test_analyze_token_format(self):
        """Analyze the problematic token format"""
        problematic_token = "c4h7lbg5m7bm"
        
        analysis = {
            "length": len(problematic_token),
            "is_alphanumeric": problematic_token.isalnum(),
            "is_hex": all(c in "0123456789abcdef" for c in problematic_token.lower()),
            "unique_chars": len(set(problematic_token)),
            "starts_with_eyj": problematic_token.startswith("eyJ"),
            "has_dots": "." in problematic_token
        }
        
        # Assertions about the problematic token
        assert analysis["length"] == 12
        assert analysis["is_alphanumeric"] == True
        assert analysis["is_hex"] == True  # It's all hex characters
        assert analysis["starts_with_eyj"] == False
        assert analysis["has_dots"] == False
        
        print(f"Token analysis: {json.dumps(analysis, indent=2)}")
        
    def test_generate_mock_tokens(self):
        """Generate mock tokens for testing"""
        # Mock JWT refresh token (typical format)
        mock_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNjk0MTM0ODAwfQ.mock_signature"
        
        # Mock UUID-like token
        mock_uuid = "550e8400-e29b-41d4-a716-446655440000"
        
        # Mock random string token
        mock_random = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
        
        tokens = {
            "jwt_like": mock_jwt,
            "uuid_like": mock_uuid,
            "random_string": mock_random,
            "problematic": "c4h7lbg5m7bm"
        }
        
        for name, token in tokens.items():
            print(f"{name}: {len(token)} chars - {token[:50]}...")

@pytest.mark.asyncio
class TestAsyncRefreshToken:
    """Async tests for refresh token functionality"""
    
    async def test_concurrent_refresh_requests(self):
        """Test multiple concurrent refresh requests"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            tasks = []
            for i in range(5):
                task = client.post(
                    "/auth/refresh",
                    json={"refresh_token": "c4h7lbg5m7bm"}
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All should fail with same error
            for response in responses:
                assert response.status_code == 401
                assert "Invalid refresh token" in response.json()["detail"]

def test_integration_refresh_token_flow():
    """Integration test for the complete refresh flow"""
    client = TestClient(app)
    
    # Test the specific failing case
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "c4h7lbg5m7bm"}
    )
    
    # Verify the exact error format matches what you're seeing
    assert response.status_code == 401
    
    expected_response = {
        "detail": "Invalid refresh token"
    }
    
    actual_response = response.json()
    assert actual_response == expected_response
    
    # Verify response headers
    assert response.headers["content-type"] == "application/json"

if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v"])
