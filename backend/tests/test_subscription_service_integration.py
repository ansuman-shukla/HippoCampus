import pytest
import mongomock
from datetime import datetime
from unittest.mock import patch
from bson import ObjectId

# Import the functions to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))
from services.subscription_service import (
    get_user_subscription,
    check_memory_limit,
    check_summary_limit,
    increment_memory_count,
    increment_summary_pages,
    reset_monthly_summaries
)


class TestSubscriptionServiceIntegration:
    """Integration tests for subscription service with real database operations"""
    
    def setup_method(self):
        """Set up test data and mock database before each test"""
        # Create a mock MongoDB collection
        self.mock_client = mongomock.MongoClient()
        self.mock_db = self.mock_client.test_db
        self.mock_collection = self.mock_db.test_collection
        
        # Sample user data
        self.test_user_1 = {
            '_id': ObjectId('507f1f77bcf86cd799439011'),
            'id': 'user_free_123',
            'email': 'free@example.com',
            'subscription_tier': 'free',
            'subscription_status': 'active',
            'subscription_start_date': datetime(2023, 1, 1),
            'subscription_end_date': None,
            'total_memories_saved': 50,
            'monthly_summary_pages_used': 3,
            'monthly_summary_reset_date': datetime(2023, 12, 1)
        }
        
        self.test_user_2 = {
            '_id': ObjectId('507f1f77bcf86cd799439012'),
            'id': 'user_pro_456',
            'email': 'pro@example.com',
            'subscription_tier': 'pro',
            'subscription_status': 'active',
            'subscription_start_date': datetime(2023, 6, 1),
            'subscription_end_date': datetime(2024, 6, 1),
            'total_memories_saved': 250,
            'monthly_summary_pages_used': 25,
            'monthly_summary_reset_date': datetime(2023, 12, 1)
        }
        
        self.test_user_3 = {
            '_id': ObjectId('507f1f77bcf86cd799439013'),
            'id': 'user_at_limit_789',
            'email': 'limit@example.com',
            'subscription_tier': 'free',
            'subscription_status': 'active',
            'subscription_start_date': datetime(2023, 1, 1),
            'subscription_end_date': None,
            'total_memories_saved': 100,  # At the free tier limit
            'monthly_summary_pages_used': 5,  # At the free tier limit
            'monthly_summary_reset_date': datetime(2023, 12, 1)
        }
        
        # Insert test users into mock database
        self.mock_collection.insert_many([
            self.test_user_1,
            self.test_user_2,
            self.test_user_3
        ])
    
    @patch('services.subscription_service.collection')
    def test_get_user_subscription_integration(self, mock_collection):
        """Integration test: get_user_subscription retrieves correct data from database"""
        mock_collection.find_one = self.mock_collection.find_one
        
        # Test getting free user subscription
        result = get_user_subscription('user_free_123')
        
        assert result is not None
        assert result['user_id'] == 'user_free_123'
        assert result['subscription_tier'] == 'free'
        assert result['total_memories_saved'] == 50
        assert result['monthly_summary_pages_used'] == 3
        
        # Test getting pro user subscription
        result = get_user_subscription('user_pro_456')
        
        assert result is not None
        assert result['user_id'] == 'user_pro_456'
        assert result['subscription_tier'] == 'pro'
        assert result['total_memories_saved'] == 250
        assert result['monthly_summary_pages_used'] == 25
    
    @patch('services.subscription_service.collection')
    def test_increment_memory_count_database_integration(self, mock_collection):
        """Integration test: increment_memory_count updates database correctly"""
        mock_collection.find_one = self.mock_collection.find_one
        mock_collection.update_one = self.mock_collection.update_one
        
        # Increment memory count for free user
        result = increment_memory_count('user_free_123')
        
        # Verify returned data
        assert result['total_memories_saved'] == 51
        assert result['user_id'] == 'user_free_123'
        
        # Verify database was actually updated
        updated_user = self.mock_collection.find_one({'id': 'user_free_123'})
        assert updated_user['total_memories_saved'] == 51
    
    @patch('services.subscription_service.collection')
    def test_increment_summary_pages_database_integration(self, mock_collection):
        """Integration test: increment_summary_pages updates database correctly"""
        mock_collection.find_one = self.mock_collection.find_one
        mock_collection.update_one = self.mock_collection.update_one
        
        # Increment summary pages for pro user
        result = increment_summary_pages('user_pro_456', 5)
        
        # Verify returned data
        assert result['monthly_summary_pages_used'] == 30
        assert result['user_id'] == 'user_pro_456'
        
        # Verify database was actually updated
        updated_user = self.mock_collection.find_one({'id': 'user_pro_456'})
        assert updated_user['monthly_summary_pages_used'] == 30
    
    @patch('services.subscription_service.collection')
    def test_reset_monthly_summaries_database_integration(self, mock_collection):
        """Integration test: reset_monthly_summaries updates all users in database"""
        mock_collection.find_one = self.mock_collection.find_one
        mock_collection.update_many = self.mock_collection.update_many
        mock_collection.find = self.mock_collection.find
        
        # Reset monthly summaries
        result = reset_monthly_summaries()
        
        # Verify operation result
        assert result['users_updated'] == 3  # Should update all 3 test users
        assert isinstance(result['reset_date'], datetime)
        assert isinstance(result['operation_time'], datetime)
        
        # Verify all users were reset in database
        all_users = list(self.mock_collection.find({}))
        for user in all_users:
            assert user['monthly_summary_pages_used'] == 0
            assert isinstance(user['monthly_summary_reset_date'], datetime)
    
    @patch('services.subscription_service.collection')
    def test_memory_limit_scenarios_integration(self, mock_collection):
        """Integration test: check_memory_limit works correctly with real data"""
        mock_collection.find_one = self.mock_collection.find_one
        
        # Free user under limit (50/100)
        assert check_memory_limit('user_free_123') is True
        
        # Free user at limit (100/100)
        assert check_memory_limit('user_at_limit_789') is False
        
        # Pro user with high count (unlimited)
        assert check_memory_limit('user_pro_456') is True
    
    @patch('services.subscription_service.collection')
    def test_summary_limit_scenarios_integration(self, mock_collection):
        """Integration test: check_summary_limit works correctly with real data"""
        mock_collection.find_one = self.mock_collection.find_one
        
        # Free user under limit (3/5, requesting 1 more = 4/5)
        assert check_summary_limit('user_free_123', 1) is True
        
        # Free user would exceed limit (3/5, requesting 3 more = 6/5)
        assert check_summary_limit('user_free_123', 3) is False
        
        # Free user at limit (5/5, requesting 1 more = 6/5)
        assert check_summary_limit('user_at_limit_789', 1) is False
        
        # Pro user within limit (25/100, requesting 20 more = 45/100)
        assert check_summary_limit('user_pro_456', 20) is True
        
        # Pro user would exceed limit (25/100, requesting 80 more = 105/100)
        assert check_summary_limit('user_pro_456', 80) is False
    
    @patch('services.subscription_service.collection')
    def test_error_handling_integration(self, mock_collection):
        """Integration test: Error handling works correctly with database"""
        mock_collection.find_one = self.mock_collection.find_one
        mock_collection.update_one = self.mock_collection.update_one
        
        # Test operations with non-existent user
        assert get_user_subscription('nonexistent_user') is None
        assert check_memory_limit('nonexistent_user') is False
        assert check_summary_limit('nonexistent_user', 1) is False
        
        # Test increment operations raise errors for non-existent users
        with pytest.raises(ValueError, match="User not found"):
            increment_memory_count('nonexistent_user')
        
        with pytest.raises(ValueError, match="User not found"):
            increment_summary_pages('nonexistent_user', 1)
    
    @patch('services.subscription_service.collection')
    def test_concurrent_operations_integration(self, mock_collection):
        """Integration test: Multiple operations on same user work correctly"""
        mock_collection.find_one = self.mock_collection.find_one
        mock_collection.update_one = self.mock_collection.update_one
        
        # Start with known state
        initial_data = get_user_subscription('user_free_123')
        assert initial_data['total_memories_saved'] == 50
        assert initial_data['monthly_summary_pages_used'] == 3
        
        # Perform multiple operations
        increment_memory_count('user_free_123')  # 50 -> 51
        increment_summary_pages('user_free_123', 2)  # 3 -> 5
        increment_memory_count('user_free_123')  # 51 -> 52
        
        # Verify final state
        final_data = get_user_subscription('user_free_123')
        assert final_data['total_memories_saved'] == 52
        assert final_data['monthly_summary_pages_used'] == 5
        
        # Verify limits are enforced correctly
        assert check_memory_limit('user_free_123') is True  # 52/100 still under limit
        assert check_summary_limit('user_free_123', 1) is False  # 5/5 at limit
    
    @patch('services.subscription_service.collection')
    def test_edge_case_values_integration(self, mock_collection):
        """Integration test: Edge case values are handled correctly"""
        mock_collection.find_one = self.mock_collection.find_one
        mock_collection.update_one = self.mock_collection.update_one
        
        # Add a user with edge case values
        edge_case_user = {
            '_id': ObjectId('507f1f77bcf86cd799439014'),
            'id': 'edge_case_user',
            'email': 'edge@example.com',
            'subscription_tier': 'free',
            'subscription_status': 'active',
            'total_memories_saved': 99,  # One away from limit
            'monthly_summary_pages_used': 4,  # One away from limit
            'monthly_summary_reset_date': datetime(2023, 12, 1)
        }
        self.mock_collection.insert_one(edge_case_user)
        
        # Test edge cases
        assert check_memory_limit('edge_case_user') is True  # 99/100 under limit
        assert check_summary_limit('edge_case_user', 1) is True  # 4+1=5/5 at limit
        assert check_summary_limit('edge_case_user', 2) is False  # 4+2=6/5 over limit
        
        # Push to exact limit
        increment_memory_count('edge_case_user')  # 99 -> 100
        increment_summary_pages('edge_case_user', 1)  # 4 -> 5
        
        # Now at exact limits
        assert check_memory_limit('edge_case_user') is False  # 100/100 at limit
        assert check_summary_limit('edge_case_user', 1) is False  # 5+1=6/5 over limit 