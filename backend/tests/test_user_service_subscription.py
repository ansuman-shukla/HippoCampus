import pytest
from datetime import datetime
import os
import sys
from unittest.mock import patch, MagicMock

# Add the app directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.user_service import create_user_if_not_exists, create_user, user_exists
from models.user_model import userModel
from core.database import collection


class TestUserServiceSubscriptionDefaults:
    """Test cases for Phase 1.4: User Service Subscription Defaults"""
    
    @pytest.fixture(scope="function") 
    def clean_test_db(self):
        """Clean up test data before and after each test"""
        # Clean up before test
        collection.delete_many({"id": {"$regex": "^test_"}})
        yield
        # Clean up after test
        collection.delete_many({"id": {"$regex": "^test_"}})

    def setup_method(self):
        """Set up test data for each test method"""
        self.sample_jwt_payload = {
            "sub": "test_user_phase14_new",
            "email": "test_phase14_new@example.com", 
            "role": "authenticated",
            "created_at": "2023-12-15T10:30:00Z",
            "updated_at": "2023-12-15T11:00:00Z",
            "iss": "https://auth.example.com",
            "user_metadata": {
                "full_name": "Phase 1.4 Test User",
                "picture": "https://example.com/avatar.jpg"
            },
            "app_metadata": {
                "provider": "google",
                "providers": ["google"]
            }
        }

    # Unit Test: create_user_if_not_exists sets correct free tier defaults
    @patch('services.user_service.user_exists')
    @patch('services.user_service.create_user')
    def test_create_user_if_not_exists_sets_correct_free_tier_defaults(self, mock_create_user, mock_user_exists):
        """Unit test: create_user_if_not_exists sets correct free tier defaults"""
        
        # Mock user doesn't exist, so create_user should be called
        mock_user_exists.return_value = False
        mock_create_user.return_value = {
            "id": "test_user_phase14_new",
            "subscription_tier": "free"
        }
        
        # Call the function
        result = create_user_if_not_exists(self.sample_jwt_payload)
        
        # Verify user_exists was called with correct user_id
        mock_user_exists.assert_called_once_with("test_user_phase14_new")
        
        # Verify create_user was called
        mock_create_user.assert_called_once()
        
        # Get the user_data that was passed to create_user
        call_args = mock_create_user.call_args[0][0]
        
        # Verify extracted user data is correct
        assert call_args["id"] == "test_user_phase14_new"
        assert call_args["email"] == "test_phase14_new@example.com"
        assert call_args["role"] == "authenticated"
        assert call_args["full_name"] == "Phase 1.4 Test User"
        assert call_args["picture"] == "https://example.com/avatar.jpg"
        assert call_args["provider"] == "google"
        assert call_args["providers"] == ["google"]
        
        # Verify function returns user data
        assert result["id"] == "test_user_phase14_new"

    @patch('services.user_service.user_exists')
    @patch('services.user_service.create_user')
    def test_create_user_if_not_exists_skips_creation_for_existing_user(self, mock_create_user, mock_user_exists):
        """Unit test: create_user_if_not_exists doesn't call create_user for existing users"""
        
        # Mock user exists, so create_user should NOT be called
        mock_user_exists.return_value = True
        
        # Call the function
        result = create_user_if_not_exists(self.sample_jwt_payload)
        
        # Verify user_exists was called
        mock_user_exists.assert_called_once_with("test_user_phase14_new")
        
        # Verify create_user was NOT called
        mock_create_user.assert_not_called()
        
        # Verify function still returns user data
        assert result["id"] == "test_user_phase14_new"

    # Integration Test: New user registration creates subscription defaults
    def test_new_user_registration_creates_subscription_defaults(self, clean_test_db):
        """Integration test: New user registration creates subscription defaults"""
        
        # Verify user doesn't exist initially
        assert not user_exists("test_user_phase14_new")
        
        # Call create_user_if_not_exists (this will create the user)
        result = create_user_if_not_exists(self.sample_jwt_payload)
        
        # Verify user was created
        assert user_exists("test_user_phase14_new")
        
        # Retrieve user from database
        stored_user = collection.find_one({"id": "test_user_phase14_new"})
        assert stored_user is not None
        
        # Process with userModel
        processed_user = userModel(stored_user)
        
        # Verify subscription defaults are set correctly
        assert processed_user["subscription_tier"] == "free"
        assert processed_user["subscription_status"] == "active"
        assert processed_user["total_memories_saved"] == 0
        assert processed_user["monthly_summary_pages_used"] == 0
        assert processed_user["subscription_end_date"] is None
        
        # Verify dates are datetime objects and reasonable
        assert isinstance(processed_user["subscription_start_date"], datetime)
        assert isinstance(processed_user["monthly_summary_reset_date"], datetime)
        
        # Verify subscription_start_date is recent (within last minute)
        now = datetime.utcnow()
        time_diff = abs((now - processed_user["subscription_start_date"]).total_seconds())
        assert time_diff < 60, "subscription_start_date should be very recent"
        
        # Verify monthly_reset_date is first day of current month
        expected_reset_date = datetime(now.year, now.month, 1)
        assert processed_user["monthly_summary_reset_date"] == expected_reset_date
        
        # Verify original user data is preserved
        assert processed_user["email"] == "test_phase14_new@example.com"
        assert processed_user["full_name"] == "Phase 1.4 Test User"
        assert processed_user["role"] == "authenticated"

    # Integration Test: Existing user login doesn't overwrite subscription data
    def test_existing_user_login_doesnt_overwrite_subscription_data(self, clean_test_db):
        """Integration test: Existing user login doesn't overwrite subscription data"""
        
        # First, create a user with custom subscription data
        existing_user_data = {
            "id": "test_user_phase14_existing",
            "email": "test_phase14_existing@example.com",
            "role": "authenticated", 
            "created_at": "2023-01-01T00:00:00Z",
            "last_sign_in_at": "2023-01-01T00:00:00Z",
            "issuer": "https://auth.example.com",
            "full_name": "Existing User",
            "picture": "https://example.com/existing.jpg", 
            "provider": "google",
            "providers": ["google"],
            # Custom subscription data (simulating a pro user)
            "subscription_tier": "pro",
            "subscription_status": "active",
            "subscription_start_date": datetime(2023, 6, 1),
            "subscription_end_date": datetime(2024, 6, 1),
            "total_memories_saved": 75,
            "monthly_summary_pages_used": 12,
            "monthly_summary_reset_date": datetime(2023, 12, 1)
        }
        
        # Insert user directly to database
        result = collection.insert_one(existing_user_data)
        assert result.acknowledged
        
        # Verify user exists
        assert user_exists("test_user_phase14_existing")
        
        # Create JWT payload for existing user (simulating login)
        existing_user_jwt = {
            "sub": "test_user_phase14_existing",
            "email": "test_phase14_existing@example.com",
            "role": "authenticated",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-12-15T11:00:00Z",  # Updated last sign in
            "iss": "https://auth.example.com",
            "user_metadata": {
                "full_name": "Existing User Updated Name",  # Changed name
                "picture": "https://example.com/existing_new.jpg"  # Changed picture
            },
            "app_metadata": {
                "provider": "google",
                "providers": ["google"]
            }
        }
        
        # Call create_user_if_not_exists (should NOT create, just return data)
        result = create_user_if_not_exists(existing_user_jwt)
        
        # Retrieve user from database
        stored_user = collection.find_one({"id": "test_user_phase14_existing"})
        processed_user = userModel(stored_user)
        
        # Verify subscription data was NOT overwritten
        assert processed_user["subscription_tier"] == "pro"
        assert processed_user["subscription_status"] == "active"
        assert processed_user["subscription_start_date"] == datetime(2023, 6, 1)
        assert processed_user["subscription_end_date"] == datetime(2024, 6, 1)
        assert processed_user["total_memories_saved"] == 75
        assert processed_user["monthly_summary_pages_used"] == 12
        assert processed_user["monthly_summary_reset_date"] == datetime(2023, 12, 1)
        
        # Verify other user data remains as originally stored (NOT updated from JWT)
        assert processed_user["email"] == "test_phase14_existing@example.com"
        assert processed_user["full_name"] == "Existing User"  # Original name, not updated
        assert processed_user["picture"] == "https://example.com/existing.jpg"  # Original picture

    def test_create_user_function_adds_subscription_defaults_directly(self, clean_test_db):
        """Integration test: create_user function adds subscription defaults correctly"""
        
        # Create basic user data without subscription fields
        basic_user_data = {
            "id": "test_user_phase14_direct",
            "email": "test_phase14_direct@example.com",
            "role": "authenticated",
            "created_at": "2023-12-15T10:30:00Z",
            "last_sign_in_at": "2023-12-15T10:30:00Z",
            "issuer": "https://auth.example.com",
            "full_name": "Direct Test User",
            "picture": "https://example.com/direct.jpg",
            "provider": "google", 
            "providers": ["google"]
        }
        
        # Call create_user directly
        result = create_user(basic_user_data)
        
        # Verify user was created in database
        stored_user = collection.find_one({"id": "test_user_phase14_direct"})
        assert stored_user is not None
        
        # Process with userModel
        processed_user = userModel(stored_user)
        
        # Verify subscription defaults were added by create_user
        assert processed_user["subscription_tier"] == "free"
        assert processed_user["subscription_status"] == "active"
        assert processed_user["total_memories_saved"] == 0
        assert processed_user["monthly_summary_pages_used"] == 0
        assert processed_user["subscription_end_date"] is None
        assert isinstance(processed_user["subscription_start_date"], datetime)
        assert isinstance(processed_user["monthly_summary_reset_date"], datetime)
        
        # Verify original data is preserved
        assert processed_user["email"] == "test_phase14_direct@example.com"
        assert processed_user["full_name"] == "Direct Test User"

    def test_subscription_defaults_datetime_consistency(self, clean_test_db):
        """Integration test: Verify datetime consistency in subscription defaults"""
        
        # Create user and capture creation time
        before_creation = datetime.utcnow()
        
        result = create_user_if_not_exists(self.sample_jwt_payload)
        
        after_creation = datetime.utcnow()
        
        # Retrieve user from database
        stored_user = collection.find_one({"id": "test_user_phase14_new"})
        processed_user = userModel(stored_user)
        
        # Verify subscription_start_date is between before and after creation
        start_date = processed_user["subscription_start_date"]
        assert before_creation <= start_date <= after_creation
        
        # Verify monthly_reset_date is correct for current month
        expected_reset_date = datetime(before_creation.year, before_creation.month, 1)
        assert processed_user["monthly_summary_reset_date"] == expected_reset_date


class TestUserServiceEdgeCases:
    """Edge case tests for user service subscription functionality"""
    
    @pytest.fixture(scope="function")
    def clean_test_db(self):
        """Clean up test data before and after each test"""
        collection.delete_many({"id": {"$regex": "^edge_"}})
        yield
        collection.delete_many({"id": {"$regex": "^edge_"}})

    def test_create_user_if_not_exists_handles_minimal_jwt_payload(self, clean_test_db):
        """Test that create_user_if_not_exists handles minimal JWT payload gracefully"""
        
        # Minimal JWT payload (some fields missing)
        minimal_jwt = {
            "sub": "edge_minimal_user",
            "email": "edge_minimal@example.com",
            "role": "authenticated", 
            # Missing user_metadata and app_metadata
        }
        
        # Should not raise an exception
        result = create_user_if_not_exists(minimal_jwt)
        
        # Verify user was created
        stored_user = collection.find_one({"id": "edge_minimal_user"})
        assert stored_user is not None
        
        # Process with userModel
        processed_user = userModel(stored_user)
        
        # Verify subscription defaults are still set
        assert processed_user["subscription_tier"] == "free"
        assert processed_user["subscription_status"] == "active"
        assert processed_user["total_memories_saved"] == 0
        
        # Verify missing fields are handled gracefully (likely None)
        assert processed_user["email"] == "edge_minimal@example.com"

    def test_create_user_handles_database_error_gracefully(self, clean_test_db):
        """Test that create_user handles database errors and raises appropriately"""
        
        basic_user_data = {
            "id": "edge_db_error_user",
            "email": "edge_db_error@example.com",
            "role": "authenticated"
        }
        
        # Mock database to raise an exception
        with patch('services.user_service.collection') as mock_collection:
            mock_collection.insert_one.side_effect = Exception("Database connection failed")
            
            # Should raise the exception
            with pytest.raises(Exception, match="Database connection failed"):
                create_user(basic_user_data) 