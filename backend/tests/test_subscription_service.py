import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from bson import ObjectId

# Import the functions to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))
from services.subscription_service import (
    TIER_LIMITS,
    get_user_subscription,
    check_memory_limit,
    check_summary_limit,
    increment_memory_count,
    increment_summary_pages,
    reset_monthly_summaries,
    estimate_content_pages
)


class TestTierLimitsConstants:
    """Test that tier limits are properly defined"""
    
    def test_tier_limits_structure(self):
        """Test that TIER_LIMITS has correct structure"""
        assert "free" in TIER_LIMITS
        assert "pro" in TIER_LIMITS
        
        # Free tier limits
        assert TIER_LIMITS["free"]["memories"] == 100
        assert TIER_LIMITS["free"]["monthly_summary_pages"] == 5
        
        # Pro tier limits  
        assert TIER_LIMITS["pro"]["memories"] == -1  # unlimited
        assert TIER_LIMITS["pro"]["monthly_summary_pages"] == 100


class TestGetUserSubscription:
    """Test get_user_subscription function"""
    
    @patch('services.subscription_service.collection')
    def test_get_user_subscription_existing_user(self, mock_collection):
        """Test getting subscription for existing user"""
        # Mock database response
        mock_user_data = {
            '_id': ObjectId('507f1f77bcf86cd799439011'),
            'id': 'user123',
            'email': 'test@example.com',
            'subscription_tier': 'pro',
            'subscription_status': 'active',
            'subscription_start_date': datetime(2023, 1, 1),
            'subscription_end_date': datetime(2024, 1, 1),
            'total_memories_saved': 50,
            'monthly_summary_pages_used': 10,
            'monthly_summary_reset_date': datetime(2023, 12, 1)
        }
        mock_collection.find_one.return_value = mock_user_data
        
        result = get_user_subscription('user123')
        
        # Verify database query
        mock_collection.find_one.assert_called_once_with({"id": "user123"})
        
        # Verify returned data
        assert result is not None
        assert result['user_id'] == 'user123'
        assert result['subscription_tier'] == 'pro'
        assert result['subscription_status'] == 'active'
        assert result['total_memories_saved'] == 50
        assert result['monthly_summary_pages_used'] == 10
    
    @patch('services.subscription_service.collection')
    def test_get_user_subscription_user_not_found(self, mock_collection):
        """Test getting subscription for non-existent user"""
        mock_collection.find_one.return_value = None
        
        result = get_user_subscription('nonexistent')
        
        mock_collection.find_one.assert_called_once_with({"id": "nonexistent"})
        assert result is None
    
    @patch('services.subscription_service.collection')
    def test_get_user_subscription_with_defaults(self, mock_collection):
        """Test getting subscription with missing fields uses defaults"""
        # Mock user with minimal data
        mock_user_data = {
            '_id': ObjectId('507f1f77bcf86cd799439011'),
            'id': 'user123',
            'email': 'test@example.com'
            # Missing subscription fields
        }
        mock_collection.find_one.return_value = mock_user_data
        
        result = get_user_subscription('user123')
        
        # Verify defaults are applied
        assert result['subscription_tier'] == 'free'
        assert result['subscription_status'] == 'active'
        assert result['total_memories_saved'] == 0
        assert result['monthly_summary_pages_used'] == 0


class TestCheckMemoryLimit:
    """Test check_memory_limit function"""
    
    @patch('services.subscription_service.get_subscription_status_with_grace')
    def test_check_memory_limit_free_user_under_limit(self, mock_get_status):
        """Unit test: check_memory_limit returns True when user at 50/100 (free)"""
        mock_get_status.return_value = {
            'user_id': 'user123',
            'subscription_tier': 'free',
            'subscription_status': 'active',
            'effective_tier': 'free',
            'total_memories_saved': 50,
            'is_in_grace_period': False
        }
        
        result = check_memory_limit('user123')
        
        assert result is True
        mock_get_status.assert_called_once_with('user123')
    
    @patch('services.subscription_service.get_user_subscription')
    def test_check_memory_limit_free_user_at_limit(self, mock_get_subscription):
        """Unit test: check_memory_limit returns False when user at 100/100 (free)"""
        mock_get_subscription.return_value = {
            'user_id': 'user123',
            'subscription_tier': 'free',
            'total_memories_saved': 100
        }
        
        result = check_memory_limit('user123')
        
        assert result is False
        mock_get_subscription.assert_called_once_with('user123')
    
    @patch('services.subscription_service.get_subscription_status_with_grace')
    def test_check_memory_limit_pro_user_unlimited(self, mock_get_status):
        """Unit test: check_memory_limit returns True when user at 500 memories (pro)"""
        mock_get_status.return_value = {
            'user_id': 'user123',
            'subscription_tier': 'pro',
            'subscription_status': 'active',
            'effective_tier': 'pro',
            'total_memories_saved': 500,
            'is_in_grace_period': False
        }
        
        result = check_memory_limit('user123')
        
        assert result is True
        mock_get_status.assert_called_once_with('user123')
    
    @patch('services.subscription_service.get_user_subscription')
    def test_check_memory_limit_user_not_found(self, mock_get_subscription):
        """Test check_memory_limit returns False when user not found"""
        mock_get_subscription.return_value = None
        
        result = check_memory_limit('nonexistent')
        
        assert result is False


class TestCheckSummaryLimit:
    """Test check_summary_limit function"""
    
    @patch('services.subscription_service.get_subscription_status_with_grace')
    def test_check_summary_limit_free_user_within_limit(self, mock_get_status):
        """Unit test: check_summary_limit allows free user at 3 pages requesting 1 more"""
        mock_get_status.return_value = {
            'user_id': 'user123',
            'subscription_tier': 'free',
            'subscription_status': 'active',
            'effective_tier': 'free',
            'monthly_summary_pages_used': 3,
            'is_in_grace_period': False
        }
        
        result = check_summary_limit('user123', 1)
        
        assert result is True
        mock_get_status.assert_called_once_with('user123')
    
    @patch('services.subscription_service.get_user_subscription')
    def test_check_summary_limit_free_user_exceeds_limit(self, mock_get_subscription):
        """Unit test: check_summary_limit blocks free user at 6 pages in month"""
        mock_get_subscription.return_value = {
            'user_id': 'user123',
            'subscription_tier': 'free',
            'monthly_summary_pages_used': 5
        }
        
        result = check_summary_limit('user123', 2)  # Would make total 7, exceeds limit of 5
        
        assert result is False
        mock_get_subscription.assert_called_once_with('user123')
    
    @patch('services.subscription_service.get_subscription_status_with_grace')
    def test_check_summary_limit_pro_user_within_limit(self, mock_get_status):
        """Unit test: check_summary_limit allows pro user at 50 pages in month"""
        mock_get_status.return_value = {
            'user_id': 'user123',
            'subscription_tier': 'pro',
            'subscription_status': 'active',
            'effective_tier': 'pro',
            'monthly_summary_pages_used': 50,
            'is_in_grace_period': False
        }
        
        result = check_summary_limit('user123', 10)  # Total 60, within pro limit of 100
        
        assert result is True
        mock_get_status.assert_called_once_with('user123')
    
    @patch('services.subscription_service.get_user_subscription')
    def test_check_summary_limit_user_not_found(self, mock_get_subscription):
        """Test check_summary_limit returns False when user not found"""
        mock_get_subscription.return_value = None
        
        result = check_summary_limit('nonexistent', 1)
        
        assert result is False


class TestIncrementMemoryCount:
    """Test increment_memory_count function"""
    
    @patch('services.subscription_service.collection')
    @patch('services.subscription_service.get_user_subscription')
    def test_increment_memory_count_successful(self, mock_get_subscription, mock_collection):
        """Unit test: increment_memory_count updates total_memories_saved"""
        # Mock subscription data
        mock_subscription = {
            'user_id': 'user123',
            'subscription_tier': 'free',
            'total_memories_saved': 25
        }
        mock_get_subscription.return_value = mock_subscription
        
        # Mock database update
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_collection.update_one.return_value = mock_result
        
        result = increment_memory_count('user123')
        
        # Verify database update call
        mock_collection.update_one.assert_called_once_with(
            {"id": "user123"},
            {"$set": {"total_memories_saved": 26}}
        )
        
        # Verify returned data
        assert result['total_memories_saved'] == 26
        assert result['user_id'] == 'user123'
    
    @patch('services.subscription_service.get_user_subscription')
    def test_increment_memory_count_user_not_found(self, mock_get_subscription):
        """Test increment_memory_count raises error when user not found"""
        mock_get_subscription.return_value = None
        
        with pytest.raises(ValueError, match="User not found"):
            increment_memory_count('nonexistent')


class TestIncrementSummaryPages:
    """Test increment_summary_pages function"""
    
    @patch('services.subscription_service.collection')
    @patch('services.subscription_service.get_user_subscription')
    def test_increment_summary_pages_successful(self, mock_get_subscription, mock_collection):
        """Unit test: increment_summary_pages updates monthly_summary_pages_used"""
        # Mock subscription data
        mock_subscription = {
            'user_id': 'user123',
            'subscription_tier': 'free',
            'monthly_summary_pages_used': 2
        }
        mock_get_subscription.return_value = mock_subscription
        
        # Mock database update
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_collection.update_one.return_value = mock_result
        
        result = increment_summary_pages('user123', 3)
        
        # Verify database update call
        mock_collection.update_one.assert_called_once_with(
            {"id": "user123"},
            {"$set": {"monthly_summary_pages_used": 5}}
        )
        
        # Verify returned data
        assert result['monthly_summary_pages_used'] == 5
        assert result['user_id'] == 'user123'
    
    @patch('services.subscription_service.get_user_subscription')
    def test_increment_summary_pages_user_not_found(self, mock_get_subscription):
        """Test increment_summary_pages raises error when user not found"""
        mock_get_subscription.return_value = None
        
        with pytest.raises(ValueError, match="User not found"):
            increment_summary_pages('nonexistent', 1)


class TestResetMonthlySummaries:
    """Test reset_monthly_summaries function"""
    
    @patch('services.subscription_service.collection')
    @patch('services.subscription_service.datetime')
    def test_reset_monthly_summaries_successful(self, mock_datetime, mock_collection):
        """Test reset_monthly_summaries resets all users correctly"""
        # Mock datetime
        fixed_datetime = datetime(2023, 12, 15, 10, 30, 0)
        mock_datetime.utcnow.return_value = fixed_datetime
        mock_datetime.return_value = datetime(2023, 12, 1)  # First day of month
        
        # Mock database update
        mock_result = MagicMock()
        mock_result.modified_count = 25
        mock_collection.update_many.return_value = mock_result
        
        result = reset_monthly_summaries()
        
        # Verify database update call
        expected_reset_date = datetime(2023, 12, 1)
        mock_collection.update_many.assert_called_once_with(
            {},  # Empty filter for all users
            {
                "$set": {
                    "monthly_summary_pages_used": 0,
                    "monthly_summary_reset_date": expected_reset_date
                }
            }
        )
        
        # Verify returned data
        assert result['users_updated'] == 25
        assert result['reset_date'] == expected_reset_date
        assert result['operation_time'] == fixed_datetime


class TestEstimateContentPages:
    """Test estimate_content_pages function"""
    
    def test_estimate_content_pages_empty_content(self):
        """Test estimate_content_pages returns 1 for empty content"""
        assert estimate_content_pages("") == 1
        assert estimate_content_pages("   ") == 1
        assert estimate_content_pages(None) == 1
    
    def test_estimate_content_pages_short_content(self):
        """Test estimate_content_pages returns 1 for short content"""
        short_content = "This is a short piece of content."
        result = estimate_content_pages(short_content)
        assert result == 1
    
    def test_estimate_content_pages_medium_content(self):
        """Test estimate_content_pages calculates correctly for medium content"""
        # Create content that's approximately 1.5 pages (4500 characters)
        medium_content = "A" * 4500
        result = estimate_content_pages(medium_content)
        assert result == 2  # Should round up to 2 pages
    
    def test_estimate_content_pages_large_content(self):
        """Unit test: estimate_content_pages calculates reasonable page estimates"""
        # Create content that's approximately 3 pages (9000 characters)
        large_content = "A" * 9000
        result = estimate_content_pages(large_content)
        assert result == 3
    
    def test_estimate_content_pages_very_large_content(self):
        """Test estimate_content_pages handles very large content"""
        # Create content that's approximately 10 pages (30000 characters)
        very_large_content = "A" * 30000
        result = estimate_content_pages(very_large_content)
        assert result == 10
    
    def test_estimate_content_pages_with_whitespace(self):
        """Test estimate_content_pages handles content with whitespace correctly"""
        content_with_whitespace = "   " + "A" * 3000 + "   "
        result = estimate_content_pages(content_with_whitespace)
        assert result == 1  # 3000 chars after stripping = 1 page 