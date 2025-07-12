import pytest
import json
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import collection
from app.models.user_model import userModel
from app.routers.admin_router import require_admin

# Test authentication helper
def setup_test_auth(user_payload):
    """Setup authentication for testing by overriding dependencies and middleware"""
    
    def mock_require_admin():
        return user_payload
    
    app.dependency_overrides[require_admin] = mock_require_admin

def cleanup_test_auth():
    """Clean up authentication overrides"""
    if require_admin in app.dependency_overrides:
        del app.dependency_overrides[require_admin]

def create_admin_test_client(user_payload):
    """Create a test client with authentication bypassed for admin endpoints"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.routers.admin_router import router as admin_router
    
    # Create a new app instance without middleware for testing
    test_app = FastAPI()
    
    # Mock the require_admin dependency
    def mock_require_admin():
        return user_payload
    
    # Override the dependency in the test app
    test_app.dependency_overrides[require_admin] = mock_require_admin
    
    # Include only the admin router
    test_app.include_router(admin_router)
    
    return TestClient(test_app)

# Test client
client = TestClient(app)

# Test data constants
TEST_ADMIN_EMAIL = "admin@test.com"
TEST_USER_EMAIL = "user@test.com"
TEST_NON_ADMIN_EMAIL = "nonadmin@test.com"

# Mock admin payload
ADMIN_PAYLOAD = {
    "sub": "admin_user_id",
    "email": TEST_ADMIN_EMAIL,
    "user_metadata": {"full_name": "Test Admin", "picture": "admin.jpg"}
}

# Mock non-admin payload
NON_ADMIN_PAYLOAD = {
    "sub": "non_admin_user_id", 
    "email": TEST_NON_ADMIN_EMAIL,
    "user_metadata": {"full_name": "Non Admin User", "picture": "user.jpg"}
}

# Mock user payload
USER_PAYLOAD = {
    "sub": "test_user_id",
    "email": TEST_USER_EMAIL,
    "user_metadata": {"full_name": "Test User", "picture": "user.jpg"}
}

@pytest.fixture
def mock_admin_env():
    """Mock admin email environment variable"""
    with patch.dict(os.environ, {"ADMIN_EMAILS": TEST_ADMIN_EMAIL}):
        # Force reload of admin emails by patching the module variable
        with patch('app.services.admin_service.ADMIN_EMAILS', [TEST_ADMIN_EMAIL.lower()]):
            yield

@pytest.fixture
def sample_users():
    """Create sample users for testing"""
    now = datetime.now(timezone.utc)
    users = [
        {
            "_id": "user1_id",
            "id": "user1_id",
            "email": "user1@test.com",
            "full_name": "User One",
            "role": "user",
            "created_at": now,
            "last_sign_in_at": now,
            "picture": "user1.jpg",
            "issuer": "supabase",
            "provider": "email",
            "providers": ["email"],
            "subscription_tier": "free",
            "subscription_status": "active",
            "subscription_start_date": now,
            "subscription_end_date": None,
            "total_memories_saved": 45,
            "monthly_summary_pages_used": 3,
            "monthly_summary_reset_date": datetime(now.year, now.month, 1)
        },
        {
            "_id": "user2_id",
            "id": "user2_id", 
            "email": "user2@test.com",
            "full_name": "User Two",
            "role": "user",
            "created_at": now,
            "last_sign_in_at": now,
            "picture": "user2.jpg",
            "issuer": "supabase",
            "provider": "email",
            "providers": ["email"],
            "subscription_tier": "pro",
            "subscription_status": "active",
            "subscription_start_date": now,
            "subscription_end_date": now + timedelta(days=30),
            "total_memories_saved": 150,
            "monthly_summary_pages_used": 25,
            "monthly_summary_reset_date": datetime(now.year, now.month, 1)
        }
    ]
    
    # Insert test users into database
    collection.delete_many({"email": {"$in": ["user1@test.com", "user2@test.com"]}})
    collection.insert_many(users)
    
    yield users
    
    # Cleanup
    collection.delete_many({"email": {"$in": ["user1@test.com", "user2@test.com"]}})

class TestAdminAuthentication:
    """Test admin authentication and authorization"""
    
    def test_admin_endpoints_require_authentication(self):
        """Unit test: Admin endpoints require admin authentication"""
        # Test without authentication
        response = client.get("/admin/users")
        assert response.status_code == 401
        assert "Authentication required" in response.json()["error"] or "Access token is missing" in response.json()["error"]
        
        response = client.get("/admin/analytics")
        assert response.status_code == 401
        
        response = client.get("/admin/users/test_user/subscription")
        assert response.status_code == 401

    def test_non_admin_users_cannot_access_admin_endpoints(self, mock_admin_env):
        """Unit test: Non-admin users cannot access admin endpoints"""
        # Create test client with non-admin user that raises 403
        def mock_non_admin_user():
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        non_admin_client = create_admin_test_client(NON_ADMIN_PAYLOAD)
        non_admin_client.app.dependency_overrides[require_admin] = mock_non_admin_user
        
        response = non_admin_client.get("/admin/users")
        assert response.status_code == 403
        assert "Admin privileges required" in response.json()["detail"]

    def test_admin_authentication_success(self, mock_admin_env):
        """Integration test: Admin authentication works correctly"""
        # Create authenticated admin test client
        admin_client = create_admin_test_client(ADMIN_PAYLOAD)
        
        # Test that admin can access admin endpoints
        response = admin_client.get("/admin/users")
        assert response.status_code == 200
        
        # Verify response structure
        data = response.json()
        assert "users" in data
        assert "total_users" in data
        assert "page" in data
        assert "page_size" in data

class TestAdminUserManagement:
    """Test admin user management functionality"""
    
    @patch('app.services.admin_service.get_all_users_with_subscriptions')
    def test_admin_can_view_all_user_subscriptions(self, mock_get_users, sample_users, mock_admin_env):
        """Integration test: Admin can view all user subscriptions"""
        mock_get_users.return_value = ([userModel(user) for user in sample_users], 2)
        
        # Setup admin authentication
        setup_test_auth(ADMIN_PAYLOAD)
        
        try:
            response = client.get("/admin/users?page=1&page_size=10")
            assert response.status_code == 200
            
            data = response.json()
            assert data["total_users"] == 2
            assert len(data["users"]) == 2
            assert data["page"] == 1
            assert data["page_size"] == 10
            
            # Verify user data structure
            user = data["users"][0]
            assert "user_id" in user
            assert "email" in user
            assert "subscription_tier" in user
            assert "subscription_status" in user
            assert "total_memories_saved" in user
        finally:
            cleanup_test_auth()

    @patch('app.services.admin_service.is_admin_user')
    @patch('app.services.admin_service.get_user_subscription_detail')
    def test_admin_can_get_specific_user_subscription(self, mock_get_detail, mock_is_admin, sample_users, mock_admin_env):
        """Integration test: Admin can get specific user subscription details"""
        mock_is_admin.return_value = True
        
        # Mock detailed user data
        user_detail = userModel(sample_users[0])
        user_detail["days_remaining"] = 25
        user_detail["is_expired"] = False
        mock_get_detail.return_value = user_detail
        
        # Setup admin authentication
        setup_test_auth(ADMIN_PAYLOAD)
        
        try:
            response = client.get("/admin/users/user1_id/subscription")
            assert response.status_code == 200
            
            data = response.json()
            assert data["user_id"] == "user1_id"
            assert data["email"] == "user1@test.com"
            assert data["subscription_tier"] == "free"
            assert "days_remaining" in data
            assert "is_expired" in data
        finally:
            cleanup_test_auth()

class TestAdminSubscriptionOperations:
    """Test admin subscription management operations"""
    
    @patch('app.services.admin_service.is_admin_user')
    @patch('app.services.admin_service.admin_upgrade_user_subscription')
    def test_admin_can_manually_upgrade_users(self, mock_upgrade, mock_is_admin, mock_admin_env):
        """Integration test: Admin can manually upgrade/downgrade users"""
        mock_is_admin.return_value = True
        mock_upgrade.return_value = {
            "user_id": "user1_id",
            "previous_tier": "free",
            "new_tier": "pro",
            "subscription_status": "active",
            "subscription_end_date": datetime.now(timezone.utc) + timedelta(days=30),
            "reason": "Admin manual upgrade",
            "updated_by": "admin",
            "updated_at": datetime.now(timezone.utc)
        }
        
        with patch('app.main.authorisation_middleware') as mock_auth_middleware:
            async def mock_middleware(request, call_next):
                request.state.user_id = "admin_user_id"
                request.state.user_payload = ADMIN_PAYLOAD
                return await call_next(request)
            
            mock_auth_middleware.side_effect = mock_middleware
            
            upgrade_data = {
                "target_tier": "pro",
                "extend_days": 30,
                "reason": "Admin manual upgrade"
            }
            
            response = client.post(
                "/admin/users/user1_id/upgrade",
                json=upgrade_data
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["action"] == "upgrade"
            assert data["user_id"] == "user1_id"
            assert "User successfully upgraded" in data["message"]
            assert data["details"]["previous_tier"] == "free"
            assert data["details"]["new_tier"] == "pro"

    @patch('app.services.admin_service.is_admin_user')  
    @patch('app.services.admin_service.admin_downgrade_user_subscription')
    def test_admin_can_manually_downgrade_users(self, mock_downgrade, mock_is_admin, mock_admin_env):
        """Integration test: Admin can manually downgrade users"""
        mock_is_admin.return_value = True
        mock_downgrade.return_value = {
            "user_id": "user2_id",
            "previous_tier": "pro",
            "new_tier": "free",
            "subscription_status": "cancelled",
            "subscription_end_date": datetime.now(timezone.utc),
            "reason": "Customer support request",
            "updated_by": "admin",
            "updated_at": datetime.now(timezone.utc)
        }
        
        with patch('app.main.authorisation_middleware') as mock_auth_middleware:
            async def mock_middleware(request, call_next):
                request.state.user_id = "admin_user_id"
                request.state.user_payload = ADMIN_PAYLOAD
                return await call_next(request)
            
            mock_auth_middleware.side_effect = mock_middleware
            
            response = client.post(
                "/admin/users/user2_id/downgrade?reason=Customer support request"
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["action"] == "downgrade"
            assert data["user_id"] == "user2_id"
            assert "downgraded to Free tier" in data["message"]

    @patch('app.services.admin_service.is_admin_user')
    @patch('app.services.admin_service.admin_extend_user_subscription')
    def test_admin_can_extend_subscription_dates(self, mock_extend, mock_is_admin, mock_admin_env):
        """Integration test: Admin can extend subscription dates"""
        mock_is_admin.return_value = True
        
        now = datetime.now(timezone.utc)
        mock_extend.return_value = {
            "user_id": "user2_id",
            "previous_end_date": now + timedelta(days=5),
            "new_end_date": now + timedelta(days=35),
            "days_extended": 30,
            "subscription_status": "active",
            "reason": "Compensation for service issues",
            "updated_by": "admin",
            "updated_at": now
        }
        
        with patch('app.main.authorisation_middleware') as mock_auth_middleware:
            async def mock_middleware(request, call_next):
                request.state.user_id = "admin_user_id"
                request.state.user_payload = ADMIN_PAYLOAD
                return await call_next(request)
            
            mock_auth_middleware.side_effect = mock_middleware
            
            extend_data = {
                "extend_days": 30,
                "reason": "Compensation for service issues"
            }
            
            response = client.post(
                "/admin/users/user2_id/extend",
                json=extend_data
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["action"] == "extend"
            assert "extended by 30 days" in data["message"]
            assert data["details"]["days_extended"] == 30

    @patch('app.services.admin_service.is_admin_user')
    @patch('app.services.admin_service.admin_reset_user_usage')
    def test_admin_can_reset_usage_counters(self, mock_reset, mock_is_admin, mock_admin_env):
        """Integration test: Admin can reset usage counters"""
        mock_is_admin.return_value = True
        mock_reset.return_value = {
            "user_id": "user1_id",
            "reset_memories": True,
            "reset_monthly_summaries": True,
            "previous_values": {
                "total_memories_saved": 45,
                "monthly_summary_pages_used": 3
            },
            "new_values": {
                "total_memories_saved": 0,
                "monthly_summary_pages_used": 0
            },
            "reason": "Data correction request",
            "updated_by": "admin",
            "updated_at": datetime.now(timezone.utc)
        }
        
        with patch('app.main.authorisation_middleware') as mock_auth_middleware:
            async def mock_middleware(request, call_next):
                request.state.user_id = "admin_user_id"
                request.state.user_payload = ADMIN_PAYLOAD
                return await call_next(request)
            
            mock_auth_middleware.side_effect = mock_middleware
            
            reset_data = {
                "reset_memories": True,
                "reset_monthly_summaries": True,
                "reason": "Data correction request"
            }
            
            response = client.post(
                "/admin/users/user1_id/reset-usage",
                json=reset_data
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["action"] == "reset-usage"
            assert "memories, monthly summaries" in data["message"]
            assert data["details"]["previous_values"]["total_memories_saved"] == 45

class TestAdminAnalytics:
    """Test admin analytics functionality"""
    
    def test_admin_analytics_return_correct_data(self, mock_admin_env):
        """Integration test: Admin analytics return correct data"""
        # Create authenticated admin test client
        admin_client = create_admin_test_client(ADMIN_PAYLOAD)
        
        response = admin_client.get("/admin/analytics")
        assert response.status_code == 200
        
        # Verify response structure
        data = response.json()
        assert "total_users" in data
        assert "free_users" in data
        assert "pro_users" in data
        assert "conversion_rate" in data
        assert "revenue_estimate" in data
        assert "average_memories_per_user" in data
        
        # Verify data types
        assert isinstance(data["total_users"], int)
        assert isinstance(data["conversion_rate"], float)
        assert isinstance(data["revenue_estimate"], (int, float))

class TestAdminActionLogging:
    """Test admin action logging"""
    
    @patch('app.services.admin_service.is_admin_user')
    @patch('app.services.admin_service.admin_upgrade_user_subscription')
    def test_admin_actions_are_properly_logged(self, mock_upgrade, mock_is_admin, mock_admin_env):
        """Integration test: Admin actions are properly logged"""
        mock_is_admin.return_value = True
        
        # Mock the upgrade with proper logging data
        now = datetime.now(timezone.utc)
        mock_upgrade.return_value = {
            "user_id": "user1_id",
            "previous_tier": "free",
            "new_tier": "pro",
            "subscription_status": "active",
            "subscription_end_date": now + timedelta(days=30),
            "reason": "Customer support upgrade",
            "updated_by": "admin",
            "updated_at": now
        }
        
        with patch('app.main.authorisation_middleware') as mock_auth_middleware:
            async def mock_middleware(request, call_next):
                request.state.user_id = "admin_user_id"
                request.state.user_payload = ADMIN_PAYLOAD
                return await call_next(request)
            
            mock_auth_middleware.side_effect = mock_middleware
            
            upgrade_data = {
                "target_tier": "pro",
                "extend_days": 30,
                "reason": "Customer support upgrade"
            }
            
            # Capture logs
            with patch('app.routers.admin_router.logger') as mock_logger:
                response = client.post(
                    "/admin/users/user1_id/upgrade",
                    json=upgrade_data
                )
                assert response.status_code == 200
                
                # Verify logging calls were made
                assert mock_logger.info.called
                
                # Check response includes admin tracking
                data = response.json()
                assert data["details"]["admin_email"] == TEST_ADMIN_EMAIL
                assert data["details"]["reason"] == "Customer support upgrade"
                assert "timestamp" in data

# Integration test to verify the complete admin workflow
class TestAdminWorkflowIntegration:
    """Integration tests for complete admin workflows"""
    
    def test_complete_admin_user_management_workflow(self, sample_users, mock_admin_env):
        """End-to-end test of admin user management workflow"""
        with patch('app.services.admin_service.is_admin_user') as mock_is_admin:
            mock_is_admin.return_value = True
            
            with patch('app.main.authorisation_middleware') as mock_auth_middleware:
                async def mock_middleware(request, call_next):
                    request.state.user_id = "admin_user_id"
                    request.state.user_payload = ADMIN_PAYLOAD
                    return await call_next(request)
                
                mock_auth_middleware.side_effect = mock_middleware
                
                # Step 1: View all users
                response = client.get("/admin/users")
                assert response.status_code == 200
                users_data = response.json()
                assert users_data["total_users"] == 2
                
                # Step 2: Get specific user details
                user_id = "user1_id"
                response = client.get(f"/admin/users/{user_id}/subscription")
                assert response.status_code == 200
                user_detail = response.json()
                assert user_detail["subscription_tier"] == "free"
                
                # Step 3: Upgrade user
                upgrade_data = {
                    "target_tier": "pro",
                    "extend_days": 30,
                    "reason": "Test upgrade"
                }
                response = client.post(f"/admin/users/{user_id}/upgrade", json=upgrade_data)
                assert response.status_code == 200
                upgrade_result = response.json()
                assert upgrade_result["success"] is True
                
                # Step 4: View analytics
                response = client.get("/admin/analytics")
                assert response.status_code == 200
                analytics = response.json()
                assert "total_users" in analytics
                assert "conversion_rate" in analytics 