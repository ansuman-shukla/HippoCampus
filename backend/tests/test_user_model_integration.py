import pytest
from datetime import datetime
import os
import sys

# Add the app directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from models.user_model import userModel
from services.user_service import create_user, user_exists
from core.database import collection


class TestUserModelIntegration:
    """Integration tests for user model with database operations"""
    
    @pytest.fixture(scope="function")
    def clean_test_db(self):
        """Clean up test data before and after each test"""
        # Clean up before test
        collection.delete_many({"email": {"$regex": "test.*@example\\.com"}})
        yield
        # Clean up after test
        collection.delete_many({"email": {"$regex": "test.*@example\\.com"}})
    
    def test_new_user_document_contains_all_subscription_fields(self, clean_test_db):
        """Test that new user documents contain all subscription fields with defaults"""
        
        # Create test user data (similar to JWT payload structure)
        test_user_data = {
            "id": "test_user_12345",
            "email": "test_integration@example.com",
            "role": "user",
            "created_at": "2023-12-15T10:30:00Z",
            "last_sign_in_at": "2023-12-15T10:30:00Z",
            "issuer": "https://auth.example.com",
            "full_name": "Integration Test User",
            "picture": "https://example.com/pic.jpg",
            "provider": "google",
            "providers": ["google"]
        }
        
        # Create user in database
        create_user(test_user_data)
        
        # Retrieve user from database
        stored_user = collection.find_one({"id": "test_user_12345"})
        
        # Verify user was created
        assert stored_user is not None
        assert stored_user["email"] == "test_integration@example.com"
        
        # Transform using userModel to check subscription fields
        result = userModel(stored_user)
        
        # Verify all subscription fields are present with correct types
        assert "subscription_tier" in result
        assert "subscription_status" in result
        assert "subscription_start_date" in result
        assert "subscription_end_date" in result
        assert "total_memories_saved" in result
        assert "monthly_summary_pages_used" in result
        assert "monthly_summary_reset_date" in result
        
        # Verify default values
        assert result["subscription_tier"] == "free"
        assert result["subscription_status"] == "active"
        assert isinstance(result["subscription_start_date"], datetime)
        assert result["subscription_end_date"] is None
        assert result["total_memories_saved"] == 0
        assert result["monthly_summary_pages_used"] == 0
        assert isinstance(result["monthly_summary_reset_date"], datetime)
    
    def test_user_model_with_existing_database_user_missing_subscription_fields(self, clean_test_db):
        """Test userModel with existing user that doesn't have subscription fields"""
        
        # Insert user directly to database without subscription fields (simulating existing users)
        legacy_user_data = {
            "id": "legacy_user_12345",
            "email": "test_legacy@example.com",
            "role": "user",
            "created_at": "2023-01-01T00:00:00Z",
            "last_sign_in_at": "2023-12-01T10:00:00Z",
            "issuer": "https://auth.example.com",
            "full_name": "Legacy User",
            "picture": "https://example.com/legacy.jpg",
            "provider": "google",
            "providers": ["google"]
            # Note: No subscription fields
        }
        
        # Insert directly to simulate legacy user
        result = collection.insert_one(legacy_user_data)
        assert result.acknowledged
        
        # Retrieve and process with userModel
        stored_user = collection.find_one({"id": "legacy_user_12345"})
        processed_user = userModel(stored_user)
        
        # Verify that userModel adds defaults for missing subscription fields
        assert processed_user["subscription_tier"] == "free"
        assert processed_user["subscription_status"] == "active"
        assert isinstance(processed_user["subscription_start_date"], datetime)
        assert processed_user["subscription_end_date"] is None
        assert processed_user["total_memories_saved"] == 0
        assert processed_user["monthly_summary_pages_used"] == 0
        assert isinstance(processed_user["monthly_summary_reset_date"], datetime)
        
        # Verify original fields are preserved
        assert processed_user["email"] == "test_legacy@example.com"
        assert processed_user["full_name"] == "Legacy User"
    
    def test_user_model_with_partial_subscription_data(self, clean_test_db):
        """Test userModel with user that has some subscription fields"""
        
        # Insert user with partial subscription data
        partial_subscription_user = {
            "id": "partial_user_12345",
            "email": "test_partial@example.com",
            "role": "user",
            "created_at": "2023-01-01T00:00:00Z",
            "last_sign_in_at": "2023-12-01T10:00:00Z",
            "issuer": "https://auth.example.com",
            "full_name": "Partial User",
            "picture": "https://example.com/partial.jpg",
            "provider": "google",
            "providers": ["google"],
            # Partial subscription data
            "subscription_tier": "pro",
            "total_memories_saved": 150,
            # Missing other subscription fields
        }
        
        result = collection.insert_one(partial_subscription_user)
        assert result.acknowledged
        
        # Retrieve and process
        stored_user = collection.find_one({"id": "partial_user_12345"})
        processed_user = userModel(stored_user)
        
        # Verify existing fields are preserved
        assert processed_user["subscription_tier"] == "pro"
        assert processed_user["total_memories_saved"] == 150
        
        # Verify missing fields get defaults
        assert processed_user["subscription_status"] == "active"
        assert isinstance(processed_user["subscription_start_date"], datetime)
        assert processed_user["subscription_end_date"] is None
        assert processed_user["monthly_summary_pages_used"] == 0
        assert isinstance(processed_user["monthly_summary_reset_date"], datetime)


class TestUserServiceIntegration:
    """Integration tests for user service with subscription fields"""
    
    @pytest.fixture(scope="function")
    def clean_test_db(self):
        """Clean up test data before and after each test"""
        collection.delete_many({"email": {"$regex": "service.*@example\\.com"}})
        yield
        collection.delete_many({"email": {"$regex": "service.*@example\\.com"}})
    
    def test_create_user_if_not_exists_with_subscription_fields(self, clean_test_db):
        """Test that create_user_if_not_exists creates users with subscription defaults"""
        
        # Mock JWT payload data
        jwt_payload = {
            "sub": "service_test_user_123",
            "email": "service_test@example.com",
            "role": "user",
            "created_at": "2023-12-15T10:30:00Z",
            "updated_at": "2023-12-15T10:30:00Z",
            "iss": "https://auth.example.com",
            "user_metadata": {
                "full_name": "Service Test User",
                "picture": "https://example.com/service.jpg"
            },
            "app_metadata": {
                "provider": "google",
                "providers": ["google"]
            }
        }
        
        # This import is here to avoid circular import issues
        from services.user_service import create_user_if_not_exists
        
        # Call the service function
        result = create_user_if_not_exists(jwt_payload)
        
        # Verify user was created in database
        stored_user = collection.find_one({"id": "service_test_user_123"})
        assert stored_user is not None
        
        # Process with userModel to check subscription fields
        processed_user = userModel(stored_user)
        
        # Verify subscription fields are present with defaults
        assert processed_user["subscription_tier"] == "free"
        assert processed_user["subscription_status"] == "active"
        assert processed_user["total_memories_saved"] == 0
        assert processed_user["monthly_summary_pages_used"] == 0
        assert processed_user["subscription_end_date"] is None
        assert isinstance(processed_user["subscription_start_date"], datetime)
        assert isinstance(processed_user["monthly_summary_reset_date"], datetime)
        
        # Verify original user data is correct
        assert processed_user["email"] == "service_test@example.com"
        assert processed_user["full_name"] == "Service Test User"

 