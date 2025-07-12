import pytest
from datetime import datetime
from unittest.mock import patch
from bson import ObjectId

# Import the functions to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))
from models.user_model import userModel, userModels


class TestUserModel:
    """Test cases for userModel function with subscription fields"""
    
    def setup_method(self):
        """Set up test data"""
        self.base_user_data = {
            '_id': ObjectId('507f1f77bcf86cd799439011'),
            'email': 'test@example.com',
            'role': 'user',
            'created_at': datetime(2023, 1, 1),
            'last_sign_in_at': datetime(2023, 12, 1),
            'full_name': 'Test User',
            'picture': 'https://example.com/pic.jpg',
            'issuer': 'auth0',
            'provider': 'google',
            'providers': ['google']
        }
    
    @patch('models.user_model.datetime')
    def test_usermodel_returns_all_subscription_fields_with_defaults(self, mock_datetime):
        """Test that userModel returns all subscription fields with correct defaults"""
        # Mock the current datetime
        fixed_datetime = datetime(2023, 12, 15, 10, 30, 0)
        mock_datetime.utcnow.return_value = fixed_datetime
        mock_datetime.return_value = datetime(2023, 12, 1)  # For monthly reset date calculation
        
        # Test with user data that has no subscription fields
        result = userModel(self.base_user_data)
        
        # Verify all original fields are present
        assert result['id'] == '507f1f77bcf86cd799439011'
        assert result['email'] == 'test@example.com'
        assert result['role'] == 'user'
        assert result['full_name'] == 'Test User'
        
        # Verify subscription fields have correct defaults
        assert result['subscription_tier'] == 'free'
        assert result['subscription_status'] == 'active'
        assert result['subscription_start_date'] == fixed_datetime
        assert result['subscription_end_date'] is None
        assert result['total_memories_saved'] == 0
        assert result['monthly_summary_pages_used'] == 0
        assert result['monthly_summary_reset_date'] == datetime(2023, 12, 1)
    
    def test_usermodel_handles_missing_subscription_fields_gracefully(self):
        """Test that userModel handles partial subscription data gracefully"""
        # Add only some subscription fields
        user_data_partial = self.base_user_data.copy()
        user_data_partial.update({
            'subscription_tier': 'pro',
            'total_memories_saved': 50,
            # Missing other subscription fields
        })
        
        result = userModel(user_data_partial)
        
        # Verify existing subscription fields are preserved
        assert result['subscription_tier'] == 'pro'
        assert result['total_memories_saved'] == 50
        
        # Verify missing fields get defaults
        assert result['subscription_status'] == 'active'
        assert result['subscription_end_date'] is None
        assert result['monthly_summary_pages_used'] == 0
        assert isinstance(result['subscription_start_date'], datetime)
        assert isinstance(result['monthly_summary_reset_date'], datetime)
    
    def test_usermodel_preserves_existing_subscription_fields(self):
        """Test that userModel preserves existing subscription field values"""
        # Create user data with all subscription fields
        subscription_start = datetime(2023, 10, 1)
        subscription_end = datetime(2024, 10, 1)
        monthly_reset = datetime(2023, 12, 1)
        
        user_data_complete = self.base_user_data.copy()
        user_data_complete.update({
            'subscription_tier': 'pro',
            'subscription_status': 'expired',
            'subscription_start_date': subscription_start,
            'subscription_end_date': subscription_end,
            'total_memories_saved': 250,
            'monthly_summary_pages_used': 15,
            'monthly_summary_reset_date': monthly_reset
        })
        
        result = userModel(user_data_complete)
        
        # Verify all subscription fields are preserved exactly
        assert result['subscription_tier'] == 'pro'
        assert result['subscription_status'] == 'expired'
        assert result['subscription_start_date'] == subscription_start
        assert result['subscription_end_date'] == subscription_end
        assert result['total_memories_saved'] == 250
        assert result['monthly_summary_pages_used'] == 15
        assert result['monthly_summary_reset_date'] == monthly_reset
    
    def test_usermodel_handles_edge_case_values(self):
        """Test that userModel handles edge case values correctly"""
        user_data_edge = self.base_user_data.copy()
        user_data_edge.update({
            'subscription_tier': 'pro',
            'subscription_status': 'cancelled',
            'total_memories_saved': 0,  # Zero values
            'monthly_summary_pages_used': 0,
            'subscription_end_date': None  # Explicit None
        })
        
        result = userModel(user_data_edge)
        
        # Verify edge cases are handled properly
        assert result['subscription_tier'] == 'pro'
        assert result['subscription_status'] == 'cancelled'
        assert result['total_memories_saved'] == 0
        assert result['monthly_summary_pages_used'] == 0
        assert result['subscription_end_date'] is None
    
    def test_usermodels_function_with_multiple_users(self):
        """Test that userModels function works with multiple users"""
        user1 = self.base_user_data.copy()
        user2 = self.base_user_data.copy()
        user2['_id'] = ObjectId('507f1f77bcf86cd799439012')
        user2['email'] = 'test2@example.com'
        user2['subscription_tier'] = 'pro'
        
        users_list = [user1, user2]
        result = userModels(users_list)
        
        # Verify we get a list of processed users
        assert len(result) == 2
        assert result[0]['subscription_tier'] == 'free'  # Default for user1
        assert result[1]['subscription_tier'] == 'pro'   # Explicit for user2
        assert all('subscription_status' in user for user in result)


class TestUserModelValidation:
    """Additional validation tests for user model subscription fields"""
    
    def test_subscription_tier_enum_values(self):
        """Test that subscription tier accepts expected values"""
        base_data = {
            '_id': ObjectId('507f1f77bcf86cd799439011'),
            'email': 'test@example.com',
            'role': 'user',
            'created_at': datetime.now(),
            'last_sign_in_at': datetime.now(),
            'full_name': 'Test User',
            'picture': 'pic.jpg',
            'issuer': 'auth0',
            'provider': 'google',
            'providers': ['google']
        }
        
        # Test valid tier values
        for tier in ['free', 'pro']:
            user_data = base_data.copy()
            user_data['subscription_tier'] = tier
            result = userModel(user_data)
            assert result['subscription_tier'] == tier
    
    def test_subscription_status_enum_values(self):
        """Test that subscription status accepts expected values"""
        base_data = {
            '_id': ObjectId('507f1f77bcf86cd799439011'),
            'email': 'test@example.com',
            'role': 'user',
            'created_at': datetime.now(),
            'last_sign_in_at': datetime.now(),
            'full_name': 'Test User',
            'picture': 'pic.jpg',
            'issuer': 'auth0',
            'provider': 'google',
            'providers': ['google']
        }
        
        # Test valid status values
        for status in ['active', 'expired', 'cancelled']:
            user_data = base_data.copy()
            user_data['subscription_status'] = status
            result = userModel(user_data)
            assert result['subscription_status'] == status 