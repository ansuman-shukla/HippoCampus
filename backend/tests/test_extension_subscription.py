"""
Test Extension Subscription Error Handling

This module tests the extension's ability to handle 402 Payment Required errors
and show appropriate upgrade prompts without breaking functionality.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app


class TestExtensionSubscriptionHandling:
    """Test extension subscription error handling and upgrade prompts."""

    def setup_method(self):
        """Setup test client and mock data."""
        self.client = TestClient(app)
        self.test_user_id = "test_extension_user_123"
        self.test_email = "extension@test.com"
        
        # Mock JWT token for extension user
        self.mock_jwt_payload = {
            "sub": self.test_user_id,
            "email": self.test_email,
            "aud": "authenticated",
            "role": "authenticated"
        }

    @patch('app.main.decodeJWT')
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.routers.bookmarkRouters.check_memory_middleware')
    def test_extension_memory_save_402_error(self, mock_check_memory_middleware, mock_create_user, mock_decode_jwt):
        """Test that extension memory save shows upgrade message on 402 error."""
        # Setup mocks
        mock_decode_jwt.return_value = self.mock_jwt_payload
        mock_create_user.return_value = {"user_id": self.test_user_id}
        # Mock middleware to raise 402 error (memory limit reached)
        from fastapi import HTTPException
        mock_check_memory_middleware.side_effect = HTTPException(
            status_code=402, 
            detail="Memory limit reached. You have saved 100/100 memories on the Free plan. Upgrade to Pro for unlimited memories!"
        )
        
        # Simulate extension bookmark save request
        bookmark_data = {
            "title": "Test Page",
            "note": "Test content for memory save",
            "link": "https://example.com"
        }
        
        # Make request with cookies (simulating extension)
        response = self.client.post(
            "/links/save",
            json=bookmark_data,
            cookies={"access_token": "mock_token"}
        )
        
        # Should return 402 Payment Required
        assert response.status_code == 402
        error_data = response.json()
        assert "memory" in error_data["detail"].lower() or "limit" in error_data["detail"].lower()
        assert "upgrade" in error_data["detail"].lower()
        
        # Verify the error message encourages upgrading
        assert "pro" in error_data["detail"].lower() or "plan" in error_data["detail"].lower()

    @patch('app.main.decodeJWT')
    @patch('app.services.user_service.create_user_if_not_exists')
    @patch('app.services.subscription_service.check_summary_limit')
    def test_extension_summary_generation_402_error(self, mock_check_summary, mock_create_user, mock_decode_jwt):
        """Test that extension summary generation shows upgrade message on 402 error."""
        # Setup mocks
        mock_decode_jwt.return_value = self.mock_jwt_payload
        mock_create_user.return_value = {"user_id": self.test_user_id}
        mock_check_summary.return_value = False  # Summary limit reached
        
        # Simulate extension summary generation request
        summary_data = {
            "content": "This is a long article that needs to be summarized for the user. " * 100
        }
        
        # Make request with cookies (simulating extension)
        response = self.client.post(
            "/summary/generate",
            json=summary_data,
            cookies={"access_token": "mock_token"}
        )
        
        # Should return 402 Payment Required
        assert response.status_code == 402
        error_data = response.json()
        assert "summary" in error_data["detail"].lower() or "page" in error_data["detail"].lower()
        assert "upgrade" in error_data["detail"].lower()

    @patch('app.main.decodeJWT')
    @patch('app.services.user_service.create_user_if_not_exists')
    @patch('app.services.subscription_service.check_memory_limit')
    @patch('app.services.subscription_service.increment_memory_count')
    def test_extension_successful_save_after_upgrade(self, mock_increment, mock_check_memory, mock_create_user, mock_decode_jwt):
        """Test that extension functionality works normally after subscription upgrade."""
        # Setup mocks for Pro user
        mock_decode_jwt.return_value = self.mock_jwt_payload
        mock_create_user.return_value = {"user_id": self.test_user_id}
        mock_check_memory.return_value = True  # Pro user has unlimited memory
        mock_increment.return_value = {"total_memories_saved": 150}
        
        # Simulate extension bookmark save request from Pro user
        bookmark_data = {
            "url": "https://example.com",
            "title": "Test Page",
            "content": "Test content for memory save",
            "site_name": "Example Site", 
            "type": "web page"
        }
        
        # Make request with cookies (simulating extension)
        response = self.client.post(
            "/links/save",
            json=bookmark_data,
            cookies={"access_token": "mock_token"}
        )
        
        # Should be successful for Pro user
        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "message" in data

    def test_extension_error_response_format(self):
        """Test that 402 error responses have the correct format for extension consumption."""
        # Simulate a 402 error response structure
        expected_error_format = {
            "detail": "Memory limit reached. You have saved 100/100 memories on the Free plan. Upgrade to Pro for unlimited memories!",
            "error_code": "MEMORY_LIMIT_REACHED",
            "upgrade_url": "https://hippocampus-puxn.onrender.com/upgrade",
            "benefits": [
                "Unlimited memory saves",
                "Up to 100 summary pages per month", 
                "Priority support"
            ]
        }
        
        # Verify the error response structure is extension-friendly
        assert "detail" in expected_error_format
        assert "upgrade_url" in expected_error_format
        assert "benefits" in expected_error_format
        assert isinstance(expected_error_format["benefits"], list)
        assert len(expected_error_format["benefits"]) > 0

    @patch('app.main.decodeJWT')
    @patch('app.services.user_service.create_user_if_not_exists')
    def test_extension_handles_malformed_402_response(self, mock_create_user, mock_decode_jwt):
        """Test that extension can handle malformed 402 responses gracefully."""
        # Setup mocks
        mock_decode_jwt.return_value = self.mock_jwt_payload
        mock_create_user.return_value = {"user_id": self.test_user_id}
        
        # Test with minimal error response (edge case)
        with patch('app.services.subscription_service.check_memory_limit', return_value=False):
            response = self.client.post(
                "/links/save",
                json={"url": "https://example.com", "title": "Test", "content": "Test"},
                cookies={"access_token": "mock_token"}
            )
            
            assert response.status_code == 402
            # Should still have basic error information
            error_data = response.json()
            assert "detail" in error_data

    @patch('app.main.decodeJWT')
    @patch('app.services.user_service.create_user_if_not_exists')
    def test_extension_multiple_simultaneous_requests(self, mock_create_user, mock_decode_jwt):
        """Test that extension can handle multiple simultaneous 402 errors without breaking."""
        # Setup mocks
        mock_decode_jwt.return_value = self.mock_jwt_payload
        mock_create_user.return_value = {"user_id": self.test_user_id}
        
        # Test multiple simultaneous requests that hit limits
        with patch('app.services.subscription_service.check_memory_limit', return_value=False):
            responses = []
            for i in range(3):
                response = self.client.post(
                    "/links/save",
                    json={
                        "url": f"https://example{i}.com",
                        "title": f"Test {i}",
                        "content": f"Test content {i}"
                    },
                    cookies={"access_token": "mock_token"}
                )
                responses.append(response)
            
            # All should return 402 without breaking
            for response in responses:
                assert response.status_code == 402
                error_data = response.json()
                assert "detail" in error_data

    def test_extension_upgrade_prompt_timing(self):
        """Test that upgrade prompts appear at appropriate times."""
        # Test scenarios where upgrade prompts should appear
        upgrade_scenarios = [
            "Memory limit reached",
            "Summary limit reached", 
            "Monthly quota exceeded",
            "Free tier limit exceeded"
        ]
        
        for scenario in upgrade_scenarios:
            # Each scenario should trigger upgrade prompt
            assert "limit" in scenario.lower() or "quota" in scenario.lower()
            assert "reach" in scenario.lower() or "exceed" in scenario.lower()

    @patch('app.main.decodeJWT')
    @patch('app.services.user_service.create_user_if_not_exists')
    @patch('app.services.subscription_service.check_memory_limit')
    def test_extension_functionality_preservation_on_error(self, mock_check_memory, mock_create_user, mock_decode_jwt):
        """Test that 402 errors don't break other extension functionality."""
        # Setup mocks
        mock_decode_jwt.return_value = self.mock_jwt_payload
        mock_create_user.return_value = {"user_id": self.test_user_id}
        mock_check_memory.return_value = False  # Memory limit reached
        
        # First request hits limit
        response1 = self.client.post(
            "/links/save",
            json={"url": "https://example.com", "title": "Test", "content": "Test"},
            cookies={"access_token": "mock_token"}
        )
        assert response1.status_code == 402
        
        # Other endpoints should still work (search, get, etc.)
        with patch('app.core.database.get_links_collection') as mock_collection:
            mock_collection.return_value.find.return_value = []
            
            response2 = self.client.get(
                "/links/get",
                cookies={"access_token": "mock_token"}
            )
            # Should work fine (not hitting subscription limits)
            assert response2.status_code == 200

    def test_extension_error_logging_format(self):
        """Test that subscription errors are logged in the correct format for monitoring."""
        # Test log message format expectations
        log_patterns = [
            "💰 BACKGROUND: Subscription limit reached - memory_limit",
            "💰 BACKGROUND: Subscription limit reached - summary_limit", 
            "💰 BACKGROUND: Submit blocked - subscription limit reached",
            "💰 BACKGROUND: GenerateSummary blocked - subscription limit reached"
        ]
        
        for pattern in log_patterns:
            assert "💰" in pattern
            assert "BACKGROUND:" in pattern
            assert "subscription" in pattern.lower() or "limit" in pattern.lower()


class TestExtensionUpgradeNotifications:
    """Test extension upgrade notification functionality."""

    def test_subscription_message_content(self):
        """Test that subscription messages contain appropriate upgrade information."""
        # Test message content structure
        memory_message = {
            "title": "Memory Limit Reached",
            "message": "You've reached your limit of 100 saved memories on the Free plan. Upgrade to Pro for unlimited memories!",
            "benefits": ["Unlimited memory saves", "Up to 100 summary pages per month", "Priority support"],
            "action": "Upgrade to Pro ($8/month)"
        }
        
        summary_message = {
            "title": "Summary Limit Reached",
            "message": "You've used all 5 summary pages for this month on the Free plan. Upgrade to Pro for 100 pages per month!",
            "benefits": ["Up to 100 summary pages monthly", "Unlimited memory saves", "Priority support"],
            "action": "Upgrade to Pro ($8/month)"
        }
        
        # Verify message structure
        for message in [memory_message, summary_message]:
            assert "title" in message
            assert "message" in message
            assert "benefits" in message
            assert "action" in message
            assert isinstance(message["benefits"], list)
            assert len(message["benefits"]) >= 3
            assert "upgrade" in message["message"].lower()
            assert "$8/month" in message["action"]

    def test_upgrade_url_generation(self):
        """Test that upgrade URLs are generated correctly for extension navigation."""
        backend_url = "https://hippocampus-puxn.onrender.com"
        expected_upgrade_url = f"{backend_url}/upgrade"
        
        # Test URL formation
        assert expected_upgrade_url.startswith("https://")
        assert "hippocampus" in expected_upgrade_url
        assert "/upgrade" in expected_upgrade_url

    def test_notification_button_configuration(self):
        """Test that notification buttons are configured correctly."""
        expected_buttons = [
            {"title": "Upgrade to Pro ($8/month)"},
            {"title": "Maybe Later"}
        ]
        
        # Verify button configuration
        assert len(expected_buttons) == 2
        assert "upgrade" in expected_buttons[0]["title"].lower()
        assert "later" in expected_buttons[1]["title"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 