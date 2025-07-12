import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta

from app.main import app
from app.core.database import collection
from app.services.subscription_service import TIER_LIMITS

# Test client
client = TestClient(app)

# Test data
MOCK_USER_ID = "test_user_123"
MOCK_USER_EMAIL = "test@example.com"
MOCK_USER_NAME = "Test User"

# Mock JWT payload
MOCK_JWT_PAYLOAD = {
    "sub": MOCK_USER_ID,
    "email": MOCK_USER_EMAIL,
    "user_metadata": {
        "full_name": MOCK_USER_NAME,
        "picture": "https://example.com/avatar.jpg"
    },
    "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    "iat": int(datetime.now(timezone.utc).timestamp())
}

@pytest.fixture
def authenticated_headers():
    """Fixture to provide authentication headers for testing"""
    # Use properly formatted fake JWT token like in existing tests
    fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
    return {"access_token": fake_jwt}

@pytest.fixture
def mock_user_subscription():
    """Fixture with mock user subscription data"""
    now = datetime.now(timezone.utc)
    return {
        "id": MOCK_USER_ID,
        "email": MOCK_USER_EMAIL,
        "subscription_tier": "free",
        "subscription_status": "active",
        "subscription_start_date": now - timedelta(days=30),
        "subscription_end_date": None,
        "total_memories_saved": 50,
        "monthly_summary_pages_used": 3,
        "monthly_summary_reset_date": datetime(now.year, now.month, 1)
    }

@pytest.fixture
def mock_pro_user_subscription():
    """Fixture with mock pro user subscription data"""
    now = datetime.now(timezone.utc)
    return {
        "id": MOCK_USER_ID,
        "email": MOCK_USER_EMAIL,
        "subscription_tier": "pro",
        "subscription_status": "active",
        "subscription_start_date": now - timedelta(days=15),
        "subscription_end_date": now + timedelta(days=15),
        "total_memories_saved": 250,
        "monthly_summary_pages_used": 45,
        "monthly_summary_reset_date": datetime(now.year, now.month, 1)
    }

class TestSubscriptionRouterCore:
    """Core tests for subscription router endpoints"""

    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    def test_get_subscription_status_success_free_user(self, mock_decode_jwt, mock_create_user, 
                                                       authenticated_headers, mock_user_subscription):
        """Integration test: /subscription/status returns correct user data for free user"""
        # Setup mocks
        mock_decode_jwt.return_value = MOCK_JWT_PAYLOAD
        mock_create_user.return_value = None
        
        # Mock database response
        with patch.object(collection, 'find_one', return_value=mock_user_subscription):
            response = client.get("/subscription/status", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify subscription status response structure
        assert data["user_id"] == MOCK_USER_ID
        assert data["subscription_tier"] == "free"
        assert data["subscription_status"] == "active"
        assert data["total_memories_saved"] == 50
        assert data["monthly_summary_pages_used"] == 3
        assert "subscription_start_date" in data
        assert "monthly_summary_reset_date" in data

    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    def test_get_subscription_status_success_pro_user(self, mock_decode_jwt, mock_create_user, 
                                                      authenticated_headers, mock_pro_user_subscription):
        """Integration test: /subscription/status returns correct user data for pro user"""
        # Setup mocks
        mock_decode_jwt.return_value = MOCK_JWT_PAYLOAD
        mock_create_user.return_value = None
        
        # Mock database response
        with patch.object(collection, 'find_one', return_value=mock_pro_user_subscription):
            response = client.get("/subscription/status", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify pro subscription details
        assert data["user_id"] == MOCK_USER_ID
        assert data["subscription_tier"] == "pro"
        assert data["subscription_status"] == "active"
        assert data["total_memories_saved"] == 250
        assert data["monthly_summary_pages_used"] == 45
        assert data["subscription_end_date"] is not None

    def test_get_subscription_status_requires_authentication(self):
        """Unit test: Endpoints require authentication"""
        response = client.get("/subscription/status")
        assert response.status_code == 401
        assert "Access token is missing" in response.json()["error"]

    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    def test_upgrade_subscription_success(self, mock_decode_jwt, mock_create_user, 
                                          authenticated_headers, mock_user_subscription):
        """Integration test: /subscription/upgrade simulates payment flow"""
        # Setup mocks
        mock_decode_jwt.return_value = MOCK_JWT_PAYLOAD
        mock_create_user.return_value = None
        
        # Mock database operations
        with patch.object(collection, 'find_one', return_value=mock_user_subscription), \
             patch.object(collection, 'update_one') as mock_update:
            
            mock_update.return_value = MagicMock(modified_count=1)
            
            upgrade_data = {
                "user_id": MOCK_USER_ID,
                "target_tier": "pro",
                "payment_method_id": "pm_test_123",
                "billing_email": "billing@example.com"
            }
            
            response = client.post("/subscription/upgrade", 
                                 json=upgrade_data, 
                                 headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify upgrade response structure
        assert data["success"] is True
        assert "upgraded to Pro successfully" in data["message"]
        assert data["subscription"]["tier"] == "pro"
        assert data["subscription"]["status"] == "active"
        assert data["subscription"]["billing_email"] == "billing@example.com"
        assert "benefits" in data
        assert data["benefits"]["unlimited_memories"] is True
        assert data["benefits"]["ai_dashboard_access"] is True
        
        # Verify database update was called
        mock_update.assert_called_once()
        update_call = mock_update.call_args
        assert update_call[0][0] == {"id": MOCK_USER_ID}  # Filter
        update_data = update_call[0][1]["$set"]
        assert update_data["subscription_tier"] == "pro"
        assert update_data["subscription_status"] == "active"

    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    def test_upgrade_subscription_sets_correct_dates(self, mock_decode_jwt, mock_create_user, 
                                                     authenticated_headers, mock_user_subscription):
        """Integration test: Pro upgrade sets correct dates and status"""
        # Setup mocks
        mock_decode_jwt.return_value = MOCK_JWT_PAYLOAD
        mock_create_user.return_value = None
        
        # Mock database operations
        with patch.object(collection, 'find_one', return_value=mock_user_subscription), \
             patch.object(collection, 'update_one') as mock_update:
            
            mock_update.return_value = MagicMock(modified_count=1)
            
            upgrade_data = {
                "user_id": MOCK_USER_ID,
                "target_tier": "pro",
                "payment_method_id": "pm_test_123"
            }
            
            response = client.post("/subscription/upgrade", 
                                 json=upgrade_data, 
                                 headers=authenticated_headers)
        
        assert response.status_code == 200
        
        # Verify dates are set correctly
        update_call = mock_update.call_args
        update_data = update_call[0][1]["$set"]
        
        # Check that start and end dates are set and end date is after start date
        start_date = update_data["subscription_start_date"]
        end_date = update_data["subscription_end_date"]
        
        assert start_date is not None
        assert end_date is not None
        assert end_date > start_date
        
        # Verify subscription is set for 30 days
        date_diff = end_date - start_date
        assert date_diff.days == 30

    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    def test_get_usage_statistics_success_free_user(self, mock_decode_jwt, mock_create_user, 
                                                    authenticated_headers, mock_user_subscription):
        """Integration test: /subscription/usage returns accurate counts for free user"""
        # Setup mocks
        mock_decode_jwt.return_value = MOCK_JWT_PAYLOAD
        mock_create_user.return_value = None
        
        # Mock database response
        with patch.object(collection, 'find_one', return_value=mock_user_subscription):
            response = client.get("/subscription/usage", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify usage statistics structure and values
        assert data["user_id"] == MOCK_USER_ID
        assert data["subscription_tier"] == "free"
        assert data["memories_used"] == 50
        assert data["memories_limit"] == TIER_LIMITS["free"]["memories"]  # 100
        assert data["summary_pages_used"] == 3
        assert data["summary_pages_limit"] == TIER_LIMITS["free"]["monthly_summary_pages"]  # 5
        
        # Verify calculated fields
        assert data["can_save_memory"] is True  # 50 < 100
        assert data["can_generate_summary"] is True  # 3 < 5
        
        # Verify computed percentage fields
        assert data["memories_percentage"] == 50.0  # 50/100 * 100
        assert data["summary_pages_percentage"] == 60.0  # 3/5 * 100

    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    def test_get_usage_statistics_success_pro_user(self, mock_decode_jwt, mock_create_user, 
                                                   authenticated_headers, mock_pro_user_subscription):
        """Integration test: /subscription/usage returns accurate counts for pro user"""
        # Setup mocks
        mock_decode_jwt.return_value = MOCK_JWT_PAYLOAD
        mock_create_user.return_value = None
        
        # Mock database response
        with patch.object(collection, 'find_one', return_value=mock_pro_user_subscription):
            response = client.get("/subscription/usage", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify pro user usage statistics
        assert data["user_id"] == MOCK_USER_ID
        assert data["subscription_tier"] == "pro"
        assert data["memories_used"] == 250
        assert data["memories_limit"] == -1  # Unlimited
        assert data["summary_pages_used"] == 45
        assert data["summary_pages_limit"] == TIER_LIMITS["pro"]["monthly_summary_pages"]  # 100
        
        # Verify capabilities for pro user
        assert data["can_save_memory"] is True  # Unlimited
        assert data["can_generate_summary"] is True  # 45 < 100
        
        # Verify computed percentage fields for pro user
        assert data["memories_percentage"] is None  # Unlimited memories
        assert data["summary_pages_percentage"] == 45.0  # 45/100 * 100

    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    def test_downgrade_subscription_success(self, mock_decode_jwt, mock_create_user, 
                                           authenticated_headers, mock_pro_user_subscription):
        """Integration test: /subscription/downgrade successfully cancels pro subscription"""
        # Setup mocks
        mock_decode_jwt.return_value = MOCK_JWT_PAYLOAD
        mock_create_user.return_value = None
        
        # Mock database operations
        with patch.object(collection, 'find_one', return_value=mock_pro_user_subscription), \
             patch.object(collection, 'update_one') as mock_update:
            
            mock_update.return_value = MagicMock(modified_count=1)
            
            response = client.post("/subscription/downgrade", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify downgrade response structure
        assert data["success"] is True
        assert "downgraded to Free successfully" in data["message"]
        assert data["subscription"]["tier"] == "free"
        assert data["subscription"]["status"] == "cancelled"
        assert "end_date" in data["subscription"]
        assert "new_limits" in data
        assert data["new_limits"]["memories"] == TIER_LIMITS["free"]["memories"]
        assert data["new_limits"]["ai_dashboard_access"] is False
        
        # Verify database update was called
        mock_update.assert_called_once()
        update_call = mock_update.call_args
        assert update_call[0][0] == {"id": MOCK_USER_ID}  # Filter
        update_data = update_call[0][1]["$set"]
        assert update_data["subscription_tier"] == "free"
        assert update_data["subscription_status"] == "cancelled"

    def test_authentication_required_for_all_endpoints(self):
        """Unit test: All subscription endpoints require authentication"""
        endpoints_to_test = [
            ("GET", "/subscription/status"),
            ("GET", "/subscription/usage"),
            ("POST", "/subscription/downgrade"),
        ]
        
        for method, endpoint in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            assert response.status_code == 401, f"Endpoint {method} {endpoint} should require auth"
            assert "Access token is missing" in response.json()["error"]

    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    def test_user_not_found_error_handling(self, mock_decode_jwt, mock_create_user, authenticated_headers):
        """Integration test: Handle user not found scenario"""
        # Setup mocks
        mock_decode_jwt.return_value = MOCK_JWT_PAYLOAD
        mock_create_user.return_value = None
        
        # Mock database response - no user found
        with patch.object(collection, 'find_one', return_value=None):
            response = client.get("/subscription/status", headers=authenticated_headers)
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    def test_upgrade_already_pro_user(self, mock_decode_jwt, mock_create_user, 
                                      authenticated_headers, mock_pro_user_subscription):
        """Integration test: Handle already pro user scenario"""
        # Setup mocks
        mock_decode_jwt.return_value = MOCK_JWT_PAYLOAD
        mock_create_user.return_value = None
        
        # Mock database response - user already pro
        with patch.object(collection, 'find_one', return_value=mock_pro_user_subscription):
            upgrade_data = {
                "user_id": MOCK_USER_ID,
                "target_tier": "pro",
                "payment_method_id": "pm_test_123"
            }
            
            response = client.post("/subscription/upgrade", 
                                 json=upgrade_data, 
                                 headers=authenticated_headers)
        
        assert response.status_code == 400
        assert "already has Pro subscription" in response.json()["detail"]

    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    def test_downgrade_already_free_user(self, mock_decode_jwt, mock_create_user, 
                                         authenticated_headers, mock_user_subscription):
        """Integration test: Handle already free user scenario"""
        # Setup mocks
        mock_decode_jwt.return_value = MOCK_JWT_PAYLOAD
        mock_create_user.return_value = None
        
        # Mock database response - user already free
        with patch.object(collection, 'find_one', return_value=mock_user_subscription):
            response = client.post("/subscription/downgrade", headers=authenticated_headers)
        
        assert response.status_code == 400
        assert "already has Free subscription" in response.json()["detail"] 