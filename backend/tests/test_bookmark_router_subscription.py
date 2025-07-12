import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app
from app.services.subscription_service import TIER_LIMITS
import json

client = TestClient(app)

class TestBookmarkRouterSubscription:
    """Integration tests for bookmark router with subscription middleware"""
    
    @pytest.fixture
    def mock_auth_middleware(self):
        """Mock the auth middleware to set user_id in request state"""
        def mock_middleware(request, call_next):
            request.state.user_id = "test_user_123"
            return call_next(request)
        return mock_middleware
    
    @pytest.fixture
    def sample_link_data(self):
        """Sample link data for testing"""
        return {
            "title": "Test Article",
            "note": "This is test content for the article.",
            "link": "https://example.com/test-article"
        }
    
    @pytest.fixture
    def free_user_subscription(self):
        """Mock subscription data for free user at memory limit"""
        return {
            "user_id": "test_user_123",
            "subscription_tier": "free",
            "subscription_status": "active",
            "subscription_start_date": "2024-01-01T00:00:00Z",
            "subscription_end_date": None,
            "total_memories_saved": 100,  # At limit
            "monthly_summary_pages_used": 0,
            "monthly_summary_reset_date": "2024-01-01T00:00:00Z"
        }
    
    @pytest.fixture
    def free_user_under_limit(self):
        """Mock subscription data for free user under memory limit"""
        return {
            "user_id": "test_user_123",
            "subscription_tier": "free",
            "subscription_status": "active",
            "subscription_start_date": "2024-01-01T00:00:00Z",
            "subscription_end_date": None,
            "total_memories_saved": 50,  # Under limit
            "monthly_summary_pages_used": 0,
            "monthly_summary_reset_date": "2024-01-01T00:00:00Z"
        }
    
    @pytest.fixture
    def pro_user_subscription(self):
        """Mock subscription data for pro user"""
        return {
            "user_id": "test_user_123",
            "subscription_tier": "pro",
            "subscription_status": "active",
            "subscription_start_date": "2024-01-01T00:00:00Z",
            "subscription_end_date": "2025-01-01T00:00:00Z",
            "total_memories_saved": 500,  # High number but pro has unlimited
            "monthly_summary_pages_used": 20,
            "monthly_summary_reset_date": "2024-01-01T00:00:00Z"
        }
    
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.services.subscription_service.get_user_subscription')
    @patch('app.routers.bookmarkRouters.save_to_vector_db')
    @patch('app.routers.bookmarkRouters.increment_memory_count')
    def test_free_user_blocked_at_101st_memory_save(
        self, 
        mock_increment, 
        mock_save_to_vector, 
        mock_get_subscription,
        mock_jwt_decode,
        mock_create_user,
        free_user_subscription,
        sample_link_data
    ):
        """Integration test: Free user blocked on 101st memory save"""
        
        # Setup mocks - decodeJWT returns payload (main.py calls this)
        mock_jwt_decode.return_value = {"sub": "test_user_123", "user_metadata": {"full_name": "Test User"}}
        # mock_create_user is AsyncMock and will handle await automatically
        mock_get_subscription.return_value = free_user_subscription
        
        # Make request to save endpoint (using properly formatted JWT)
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {"access_token": fake_jwt}
        response = client.post("/links/save", json=sample_link_data, headers=headers)
        
        # Assertions
        assert response.status_code == 402
        response_data = response.json()
        
        # Check 402 response structure
        assert "detail" in response_data
        detail = response_data["detail"]
        assert detail["error"] == "Subscription limit exceeded"
        assert detail["action_required"] == "upgrade"
        assert "memory save limit" in detail["message"]
        assert detail["upgrade_url"] == "/subscription/upgrade"
        assert "subscription_info" in detail
        
        # Verify save function was never called
        mock_save_to_vector.assert_not_called()
        mock_increment.assert_not_called()
    
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.services.subscription_service.get_user_subscription')
    @patch('app.routers.bookmarkRouters.save_to_vector_db')
    @patch('app.routers.bookmarkRouters.increment_memory_count')
    def test_pro_user_can_save_unlimited_memories(
        self,
        mock_increment,
        mock_save_to_vector,
        mock_get_subscription,
        mock_jwt_decode,
        mock_create_user,
        pro_user_subscription,
        sample_link_data
    ):
        """Integration test: Pro user can save unlimited memories"""
        
        # Setup mocks - decodeJWT returns payload (main.py calls this)
        mock_jwt_decode.return_value = {"sub": "test_user_123", "user_metadata": {"full_name": "Test User"}}
        # mock_create_user is AsyncMock and will handle await automatically
        mock_get_subscription.return_value = pro_user_subscription
        mock_save_to_vector.return_value = {"status": "saved", "doc_id": "doc_123"}
        mock_increment.return_value = {**pro_user_subscription, "total_memories_saved": 501}
        
        # Make request to save endpoint (using properly formatted JWT)
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {"access_token": fake_jwt}
        response = client.post("/links/save", json=sample_link_data, headers=headers)
        
        # Assertions
        assert response.status_code == 200
        
        # Verify save function was called
        mock_save_to_vector.assert_called_once()
        call_args = mock_save_to_vector.call_args
        assert call_args[1]["namespace"] == "test_user_123"
        
        # Verify increment was called
        mock_increment.assert_called_once_with("test_user_123")
    
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.services.subscription_service.get_user_subscription')
    @patch('app.routers.bookmarkRouters.save_to_vector_db')
    @patch('app.routers.bookmarkRouters.increment_memory_count')
    def test_memory_count_increments_correctly_after_save(
        self,
        mock_increment,
        mock_save_to_vector,
        mock_get_subscription,
        mock_jwt_decode,
        mock_create_user,
        free_user_under_limit,
        sample_link_data
    ):
        """Integration test: Memory count increments correctly after save"""
        
        # Setup mocks - decodeJWT returns payload (main.py calls this)
        mock_jwt_decode.return_value = {"sub": "test_user_123", "user_metadata": {"full_name": "Test User"}}
        # mock_create_user is AsyncMock and will handle await automatically
        mock_get_subscription.return_value = free_user_under_limit
        mock_save_to_vector.return_value = {"status": "saved", "doc_id": "doc_123"}
        
        # Mock increment to return updated count
        updated_subscription = {**free_user_under_limit, "total_memories_saved": 51}
        mock_increment.return_value = updated_subscription
        
        # Make request to save endpoint (using properly formatted JWT)
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {"access_token": fake_jwt}
        response = client.post("/links/save", json=sample_link_data, headers=headers)
        
        # Assertions
        assert response.status_code == 200
        
        # Verify save function was called first
        mock_save_to_vector.assert_called_once()
        
        # Verify increment was called after save
        mock_increment.assert_called_once_with("test_user_123")
        
        # Verify the increment was called with correct user
        args, kwargs = mock_increment.call_args
        assert args[0] == "test_user_123"
    
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.services.subscription_service.get_user_subscription')
    @patch('app.routers.bookmarkRouters.save_to_vector_db')
    @patch('app.routers.bookmarkRouters.increment_memory_count')
    def test_failed_saves_dont_increment_counter(
        self,
        mock_increment,
        mock_save_to_vector,
        mock_get_subscription,
        mock_jwt_decode,
        mock_create_user,
        free_user_under_limit,
        sample_link_data
    ):
        """Integration test: Failed saves don't increment counter"""
        
        # Setup mocks - decodeJWT returns payload (main.py calls this)
        mock_jwt_decode.return_value = {"sub": "test_user_123", "user_metadata": {"full_name": "Test User"}}
        # mock_create_user is AsyncMock and will handle await automatically
        mock_get_subscription.return_value = free_user_under_limit
        
        # Mock save to raise an exception
        from app.exceptions.httpExceptionsSave import DocumentSaveError
        mock_save_to_vector.side_effect = DocumentSaveError("test_user_123", "Save failed")
        
        # Make request to save endpoint (using properly formatted JWT)
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {"access_token": fake_jwt}
        response = client.post("/links/save", json=sample_link_data, headers=headers)
        
        # Assertions
        assert response.status_code in [400, 503]  # DocumentSaveError maps to these codes
        
        # Verify save function was called but failed
        mock_save_to_vector.assert_called_once()
        
        # Verify increment was NOT called since save failed
        mock_increment.assert_not_called()
    
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.services.subscription_service.get_user_subscription')
    @patch('app.routers.bookmarkRouters.save_to_vector_db')
    @patch('app.routers.bookmarkRouters.increment_memory_count')
    def test_increment_failure_doesnt_break_save(
        self,
        mock_increment,
        mock_save_to_vector,
        mock_get_subscription,
        mock_jwt_decode,
        mock_create_user,
        free_user_under_limit,
        sample_link_data
    ):
        """Integration test: Increment failure doesn't break successful save"""
        
        # Setup mocks - decodeJWT returns payload (main.py calls this)
        mock_jwt_decode.return_value = {"sub": "test_user_123", "user_metadata": {"full_name": "Test User"}}
        # mock_create_user is AsyncMock and will handle await automatically
        mock_get_subscription.return_value = free_user_under_limit
        mock_save_to_vector.return_value = {"status": "saved", "doc_id": "doc_123"}
        
        # Mock increment to raise an exception
        mock_increment.side_effect = Exception("Database connection failed")
        
        # Make request to save endpoint (using properly formatted JWT)
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {"access_token": fake_jwt}
        response = client.post("/links/save", json=sample_link_data, headers=headers)
        
        # Assertions - save should still succeed even if increment fails
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "saved"
        
        # Verify both functions were called
        mock_save_to_vector.assert_called_once()
        mock_increment.assert_called_once_with("test_user_123")
    
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.services.subscription_service.get_user_subscription')
    def test_extension_receives_402_error_properly(
        self,
        mock_get_subscription,
        mock_jwt_decode,
        mock_create_user,
        free_user_subscription,
        sample_link_data
    ):
        """End-to-end test: Extension receives 402 error properly"""
        
        # Setup mocks for user at limit - decodeJWT returns payload (main.py calls this)
        mock_jwt_decode.return_value = {"sub": "test_user_123", "user_metadata": {"full_name": "Test User"}}
        # mock_create_user is AsyncMock and will handle await automatically
        mock_get_subscription.return_value = free_user_subscription
        
        # Make request with proper headers that extension would use
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {
            "access_token": fake_jwt,
            "Content-Type": "application/json",
            "User-Agent": "HippoCampus Extension/1.0"
        }
        
        response = client.post("/links/save", json=sample_link_data, headers=headers)
        
        # Verify 402 response
        assert response.status_code == 402
        response_data = response.json()
        
        # Check response structure that extension expects
        assert "detail" in response_data
        detail = response_data["detail"]
        
        # Extension should be able to parse these fields
        assert detail["error"] == "Subscription limit exceeded"
        assert detail["action_required"] == "upgrade"
        assert detail["upgrade_url"] == "/subscription/upgrade"
        
        # Check upgrade benefits for frontend display
        assert "subscription_info" in detail
        subscription_info = detail["subscription_info"]
        assert subscription_info["current_tier"] == "free"
        assert "upgrade_benefits" in subscription_info
        assert len(subscription_info["upgrade_benefits"]) > 0
        
        # Check message contains useful information
        assert "memory save limit" in detail["message"].lower()
        assert "100" in detail["message"]  # Free tier limit
        assert "pro" in detail["message"].lower()  # Upgrade suggestion
    
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    def test_unauthenticated_request_fails(self, mock_jwt_decode, mock_create_user, sample_link_data):
        """Test that unauthenticated requests fail properly"""
        
        # Mock JWT decode to raise error (simulating invalid token)
        from jose import JWTError
        mock_jwt_decode.side_effect = JWTError("Invalid token")
        
        # Make request without valid auth (invalid JWT format)
        headers = {"access_token": "invalid_token"}
        response = client.post("/links/save", json=sample_link_data, headers=headers)
        
        # Should fail with 401
        assert response.status_code == 401
    
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.services.subscription_service.get_user_subscription')
    def test_subscription_service_error_handling(
        self,
        mock_get_subscription,
        mock_jwt_decode,
        mock_create_user,
        sample_link_data
    ):
        """Test handling of subscription service errors"""
        
        # Setup mocks - decodeJWT returns payload (main.py calls this)
        mock_jwt_decode.return_value = {"sub": "test_user_123", "user_metadata": {"full_name": "Test User"}}
        # mock_create_user is AsyncMock and will handle await automatically
        
        # Mock subscription service to raise an exception
        mock_get_subscription.side_effect = Exception("Database connection failed")
        
        # Make request (using properly formatted JWT)
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {"access_token": fake_jwt}
        response = client.post("/links/save", json=sample_link_data, headers=headers)
        
        # Should fail with 402 due to subscription check error (system defaults to blocking user)
        assert response.status_code == 402 