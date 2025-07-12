"""
Tests for Phase 3.3: Subscription Lifecycle Management

Tests for:
- Grace periods for expired subscriptions
- Reactivation logic for returning users  
- Edge cases (timezone changes, leap years)
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import mongomock

from app.services.subscription_service import (
    get_subscription_status_with_grace,
    check_grace_period_limits,
    reactivate_subscription,
    handle_timezone_safe_operations,
    handle_leap_year_edge_cases,
    get_users_requiring_grace_period_processing,
    check_memory_limit,
    check_summary_limit,
    GRACE_PERIOD_DAYS,
    GRACE_PERIOD_LIMITS
)
from app.services.background_jobs import BackgroundJobsService


# Test fixtures and setup
@pytest.fixture
def mock_collection():
    """Mock MongoDB collection for testing."""
    return mongomock.MongoClient().test_db.test_collection


@pytest.fixture  
def sample_pro_user():
    """Sample pro user data for testing."""
    now = datetime.now(timezone.utc)
    return {
        "id": "pro-user-123",
        "email": "pro@example.com",
        "subscription_tier": "pro",
        "subscription_status": "active",
        "subscription_start_date": now - timedelta(days=25),
        "subscription_end_date": now - timedelta(days=2),  # Expired 2 days ago
        "total_memories_saved": 50,
        "monthly_summary_pages_used": 15,
        "monthly_summary_reset_date": datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    }


@pytest.fixture
def sample_free_user():
    """Sample free user data for testing."""
    now = datetime.now(timezone.utc)
    return {
        "id": "free-user-456", 
        "email": "free@example.com",
        "subscription_tier": "free",
        "subscription_status": "active",
        "subscription_start_date": now - timedelta(days=30),
        "subscription_end_date": None,
        "total_memories_saved": 80,
        "monthly_summary_pages_used": 3,
        "monthly_summary_reset_date": datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    }


# ===== GRACE PERIOD FUNCTIONALITY TESTS =====

class TestGracePeriodLogic:
    """Test grace period functionality."""

    @patch('app.services.subscription_service.collection')
    def test_get_subscription_status_with_grace_active_pro(self, mock_collection, sample_pro_user):
        """Test grace period status for active pro user."""
        # Setup: Pro user with active subscription
        sample_pro_user["subscription_end_date"] = datetime.now(timezone.utc) + timedelta(days=5)
        sample_pro_user["subscription_status"] = "active"
        mock_collection.find_one.return_value = sample_pro_user
        
        # Test
        status = get_subscription_status_with_grace("pro-user-123")
        
        # Assert
        assert status is not None
        assert status["is_active"] is True
        assert status["is_expired"] is False
        assert status["is_in_grace_period"] is False
        assert status["effective_tier"] == "pro"
        assert status["days_remaining"] >= 4  # Allow for timing differences
        assert status["days_remaining"] <= 5

    @patch('app.services.subscription_service.collection')
    def test_get_subscription_status_with_grace_in_grace_period(self, mock_collection, sample_pro_user):
        """Test grace period status for user in grace period."""
        # Setup: Pro user expired 3 days ago (within grace period)
        now = datetime.now(timezone.utc)
        sample_pro_user["subscription_end_date"] = now - timedelta(days=3)
        sample_pro_user["subscription_status"] = "expired"
        mock_collection.find_one.return_value = sample_pro_user
        
        # Test
        status = get_subscription_status_with_grace("pro-user-123")
        
        # Assert
        assert status is not None
        assert status["is_active"] is False
        assert status["is_expired"] is True
        assert status["is_in_grace_period"] is True
        assert status["effective_tier"] == "grace"
        assert status["grace_days_remaining"] == GRACE_PERIOD_DAYS - 3
        assert status["grace_period_end"] == sample_pro_user["subscription_end_date"] + timedelta(days=GRACE_PERIOD_DAYS)

    @patch('app.services.subscription_service.collection')
    def test_get_subscription_status_with_grace_fully_expired(self, mock_collection, sample_pro_user):
        """Test grace period status for fully expired user."""
        # Setup: Pro user expired beyond grace period
        now = datetime.now(timezone.utc)
        sample_pro_user["subscription_end_date"] = now - timedelta(days=GRACE_PERIOD_DAYS + 2)
        sample_pro_user["subscription_status"] = "expired"
        mock_collection.find_one.return_value = sample_pro_user
        
        # Test
        status = get_subscription_status_with_grace("pro-user-123")
        
        # Assert
        assert status is not None
        assert status["is_active"] is False
        assert status["is_expired"] is True
        assert status["is_in_grace_period"] is False
        assert status["effective_tier"] == "free"
        assert status["grace_days_remaining"] is None

    @patch('app.services.subscription_service.collection')
    def test_get_subscription_status_with_grace_free_user(self, mock_collection, sample_free_user):
        """Test grace period status for free user."""
        mock_collection.find_one.return_value = sample_free_user
        
        # Test
        status = get_subscription_status_with_grace("free-user-456")
        
        # Assert
        assert status is not None
        assert status["is_active"] is True
        assert status["is_expired"] is False
        assert status["is_in_grace_period"] is False
        assert status["effective_tier"] == "free"

    @patch('app.services.subscription_service.get_subscription_status_with_grace')
    def test_check_grace_period_limits_memory_allowed(self, mock_status):
        """Test grace period memory limits - allowed operation."""
        # Setup: User in grace period with no grace usage
        mock_status.return_value = {
            "is_in_grace_period": True,
            "grace_period_usage": {"memories_used": 2, "summary_pages_used": 0}
        }
        
        # Test
        result = check_grace_period_limits("user-123", "memory")
        
        # Assert
        assert result is True  # 2 < 5 (grace limit)

    @patch('app.services.subscription_service.get_subscription_status_with_grace')
    def test_check_grace_period_limits_memory_blocked(self, mock_status):
        """Test grace period memory limits - blocked operation."""
        # Setup: User in grace period at memory limit
        mock_status.return_value = {
            "is_in_grace_period": True,
            "grace_period_usage": {"memories_used": 5, "summary_pages_used": 0}
        }
        
        # Test
        result = check_grace_period_limits("user-123", "memory")
        
        # Assert
        assert result is False  # 5 >= 5 (grace limit)

    @patch('app.services.subscription_service.get_subscription_status_with_grace')
    def test_check_grace_period_limits_summary_allowed(self, mock_status):
        """Test grace period summary limits - allowed operation."""
        # Setup: User in grace period with no summary usage
        mock_status.return_value = {
            "is_in_grace_period": True,
            "grace_period_usage": {"memories_used": 0, "summary_pages_used": 0}
        }
        
        # Test
        result = check_grace_period_limits("user-123", "summary", 1)
        
        # Assert
        assert result is True  # 0 + 1 <= 1 (grace limit)

    @patch('app.services.subscription_service.get_subscription_status_with_grace')
    def test_check_grace_period_limits_summary_blocked(self, mock_status):
        """Test grace period summary limits - blocked operation."""
        # Setup: User in grace period at summary limit
        mock_status.return_value = {
            "is_in_grace_period": True,
            "grace_period_usage": {"memories_used": 0, "summary_pages_used": 1}
        }
        
        # Test
        result = check_grace_period_limits("user-123", "summary", 1)
        
        # Assert
        assert result is False  # 1 + 1 > 1 (grace limit)


# ===== REACTIVATION LOGIC TESTS =====

class TestReactivationLogic:
    """Test subscription reactivation functionality."""

    @patch('app.services.subscription_service.collection')
    @patch('app.services.subscription_service.get_subscription_status_with_grace')
    def test_reactivate_subscription_from_grace_period(self, mock_status, mock_collection):
        """Test reactivating subscription from grace period."""
        # Setup: User in grace period
        now = datetime.now(timezone.utc)
        mock_status.return_value = {
            "subscription_tier": "pro",
            "subscription_status": "expired",
            "is_in_grace_period": True,
            "monthly_summary_reset_date": datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        
        # Test
        result = reactivate_subscription("user-123", "credit_card")
        
        # Assert
        assert result["user_id"] == "user-123"
        assert result["previous_status"] == "expired"
        assert result["new_status"] == "active"
        assert result["subscription_tier"] == "pro"
        assert result["payment_method"] == "credit_card"
        assert result["was_in_grace_period"] is True
        assert isinstance(result["new_end_date"], datetime)
        
        # Verify database update
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args
        assert call_args[0][0] == {"id": "user-123"}
        assert "subscription_status" in call_args[0][1]["$set"]
        assert call_args[0][1]["$set"]["subscription_status"] == "active"

    @patch('app.services.subscription_service.collection')
    @patch('app.services.subscription_service.get_subscription_status_with_grace')
    def test_reactivate_subscription_from_cancelled(self, mock_status, mock_collection):
        """Test reactivating cancelled subscription."""
        # Setup: Cancelled pro user
        now = datetime.now(timezone.utc)
        mock_status.return_value = {
            "subscription_tier": "pro",
            "subscription_status": "cancelled",
            "is_in_grace_period": False,
            "monthly_summary_reset_date": datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        
        # Test
        result = reactivate_subscription("user-123")
        
        # Assert
        assert result["previous_status"] == "cancelled"
        assert result["new_status"] == "active"
        assert result["was_in_grace_period"] is False

    @patch('app.services.subscription_service.get_subscription_status_with_grace')
    def test_reactivate_subscription_invalid_user(self, mock_status):
        """Test reactivating subscription for invalid user."""
        # Setup: User not found
        mock_status.return_value = None
        
        # Test
        with pytest.raises(ValueError, match="User not found"):
            reactivate_subscription("invalid-user")

    @patch('app.services.subscription_service.get_subscription_status_with_grace')
    def test_reactivate_subscription_free_user_blocked(self, mock_status):
        """Test reactivating subscription for free user (should be blocked)."""
        # Setup: Free user trying to reactivate
        mock_status.return_value = {
            "subscription_tier": "free",
            "subscription_status": "active",
            "is_in_grace_period": False
        }
        
        # Test
        with pytest.raises(ValueError, match="User subscription cannot be reactivated"):
            reactivate_subscription("free-user")

    @patch('app.services.subscription_service.collection')
    @patch('app.services.subscription_service.get_subscription_status_with_grace')
    def test_reactivate_subscription_with_monthly_reset(self, mock_status, mock_collection):
        """Test reactivating subscription with monthly usage reset."""
        # Setup: User in grace period with old monthly reset date
        now = datetime.now(timezone.utc)
        old_reset_date = datetime(now.year, now.month - 1 if now.month > 1 else 12, 1, tzinfo=timezone.utc)
        
        mock_status.return_value = {
            "subscription_tier": "pro",
            "subscription_status": "expired", 
            "is_in_grace_period": True,
            "monthly_summary_reset_date": old_reset_date
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        
        # Test
        result = reactivate_subscription("user-123")
        
        # Assert - should reset monthly usage
        call_args = mock_collection.update_one.call_args[0][1]["$set"]
        assert "monthly_summary_pages_used" in call_args
        assert call_args["monthly_summary_pages_used"] == 0
        assert "monthly_summary_reset_date" in call_args


# ===== EDGE CASE HANDLING TESTS =====

class TestEdgeCaseHandling:
    """Test edge case handling for timezones and leap years."""

    def test_handle_timezone_safe_operations_naive_datetime(self):
        """Test timezone handling for naive datetime."""
        # Setup: Naive datetime
        naive_dt = datetime(2024, 3, 15, 10, 30, 0)
        
        # Test
        result = handle_timezone_safe_operations(naive_dt)
        
        # Assert
        assert result.tzinfo == timezone.utc
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15

    def test_handle_timezone_safe_operations_with_timezone(self):
        """Test timezone handling for timezone-aware datetime."""
        # Setup: Datetime with timezone
        est_tz = timezone(timedelta(hours=-5))
        est_dt = datetime(2024, 3, 15, 10, 30, 0, tzinfo=est_tz)
        
        # Test
        result = handle_timezone_safe_operations(est_dt)
        
        # Assert
        assert result.tzinfo == timezone.utc
        assert result.hour == 15  # Converted from EST to UTC

    def test_handle_timezone_safe_operations_already_utc(self):
        """Test timezone handling for UTC datetime."""
        # Setup: UTC datetime
        utc_dt = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        
        # Test
        result = handle_timezone_safe_operations(utc_dt)
        
        # Assert
        assert result == utc_dt  # Should be unchanged
        assert result.tzinfo == timezone.utc

    def test_handle_leap_year_edge_cases_leap_year(self):
        """Test leap year handling for Feb 29 in leap year."""
        # Test: Feb 29, 2024 (leap year)
        result = handle_leap_year_edge_cases(2024, 2, 29)
        
        # Assert
        assert result.year == 2024
        assert result.month == 2
        assert result.day == 29

    def test_handle_leap_year_edge_cases_non_leap_year(self):
        """Test leap year handling for Feb 29 in non-leap year."""
        # Test: Feb 29, 2023 (non-leap year)
        result = handle_leap_year_edge_cases(2023, 2, 29)
        
        # Assert - should adjust to Feb 28
        assert result.year == 2023
        assert result.month == 2
        assert result.day == 28

    def test_handle_leap_year_edge_cases_month_overflow(self):
        """Test leap year handling for invalid day in month."""
        # Test: April 31 (April only has 30 days)
        result = handle_leap_year_edge_cases(2024, 4, 31)
        
        # Assert - should adjust to April 30
        assert result.year == 2024
        assert result.month == 4
        assert result.day == 30

    def test_handle_leap_year_edge_cases_normal_date(self):
        """Test leap year handling for normal date."""
        # Test: Normal date
        result = handle_leap_year_edge_cases(2024, 6, 15)
        
        # Assert
        assert result.year == 2024
        assert result.month == 6
        assert result.day == 15


# ===== INTEGRATION TESTS =====

class TestSubscriptionLifecycleIntegration:
    """Integration tests for subscription lifecycle management."""

    @patch('app.services.subscription_service.collection')
    def test_enhanced_memory_limit_check_with_grace(self, mock_collection):
        """Integration test: Memory limit checking with grace period."""
        # Setup: User in grace period
        now = datetime.now(timezone.utc)
        user_data = {
            "id": "user-123",
            "subscription_tier": "pro",
            "subscription_status": "expired",
            "subscription_end_date": now - timedelta(days=3),  # In grace period
            "total_memories_saved": 200
        }
        mock_collection.find_one.return_value = user_data
        
        # Test
        with patch('app.services.subscription_service.check_grace_period_limits', return_value=True):
            result = check_memory_limit("user-123")
        
        # Assert
        assert result is True  # Should allow in grace period

    @patch('app.services.subscription_service.collection')
    def test_enhanced_summary_limit_check_with_grace(self, mock_collection):
        """Integration test: Summary limit checking with grace period."""
        # Setup: User in grace period
        now = datetime.now(timezone.utc)
        user_data = {
            "id": "user-123",
            "subscription_tier": "pro",
            "subscription_status": "expired",
            "subscription_end_date": now - timedelta(days=3),  # In grace period
            "monthly_summary_pages_used": 50
        }
        mock_collection.find_one.return_value = user_data
        
        # Test
        with patch('app.services.subscription_service.check_grace_period_limits', return_value=False):
            result = check_summary_limit("user-123", 2)
        
        # Assert
        assert result is False  # Should block in grace period when at limit

    @patch('app.services.subscription_service.collection')
    def test_get_users_requiring_grace_period_processing(self, mock_collection):
        """Integration test: Finding users in grace period."""
        # Setup: Mock users in grace period
        now = datetime.now(timezone.utc)
        grace_cutoff = now - timedelta(days=GRACE_PERIOD_DAYS)
        
        mock_users = [
            {
                "id": "user-1",
                "subscription_tier": "pro",
                "subscription_status": "expired",
                "subscription_end_date": now - timedelta(days=2)
            },
            {
                "id": "user-2", 
                "subscription_tier": "pro",
                "subscription_status": "active",
                "subscription_end_date": now - timedelta(days=1)
            }
        ]
        mock_collection.find.return_value = mock_users
        
        # Test
        result = get_users_requiring_grace_period_processing()
        
        # Assert
        assert len(result) == 2
        assert result[0]["id"] == "user-1"
        assert result[1]["id"] == "user-2"


# ===== BACKGROUND JOBS GRACE PERIOD TESTS =====

class TestBackgroundJobsGracePeriod:
    """Test background jobs with grace period support."""

    @patch('app.services.background_jobs.collection')
    def test_check_subscription_expiry_with_grace_period(self, mock_collection):
        """Integration test: Background job handling grace periods."""
        # Setup: Mock users for grace period transitions
        now = datetime.now(timezone.utc)
        grace_cutoff = now - timedelta(days=GRACE_PERIOD_DAYS)
        
        # Recently expired user (move to grace)
        recently_expired = {
            "id": "user-1",
            "email": "user1@example.com",
            "subscription_tier": "pro",
            "subscription_status": "active",
            "subscription_end_date": now - timedelta(hours=1)
        }
        
        # Grace period expired user (move to free)
        grace_expired = {
            "id": "user-2",
            "email": "user2@example.com", 
            "subscription_tier": "pro",
            "subscription_status": "expired",
            "subscription_end_date": grace_cutoff - timedelta(days=1)
        }
        
        # Mock database calls
        def mock_find(query):
            if "subscription_status" in query and query["subscription_status"] == "active":
                return [recently_expired]
            elif "subscription_status" in query and query["subscription_status"] == "expired":
                return [grace_expired]
            return []
        
        mock_collection.find.side_effect = mock_find
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        
        # Test
        jobs_service = BackgroundJobsService()
        result = jobs_service.check_subscription_expiry()
        
        # Assert
        assert result["status"] == "success"
        assert result["total_users_processed"] == 2
        assert result["total_transitions"] == 2
        assert result["expired_to_grace"]["count"] == 1
        assert result["grace_to_free"]["count"] == 1
        assert result["grace_period_days"] == GRACE_PERIOD_DAYS
        
        # Verify specific user transitions
        expired_to_grace_user = result["expired_to_grace"]["users"][0]
        assert expired_to_grace_user["user_id"] == "user-1"
        assert expired_to_grace_user["previous_status"] == "active"
        assert expired_to_grace_user["new_status"] == "expired"
        
        grace_to_free_user = result["grace_to_free"]["users"][0]
        assert grace_to_free_user["user_id"] == "user-2"
        assert grace_to_free_user["previous_tier"] == "pro"
        assert grace_to_free_user["new_tier"] == "free"

    @patch('app.services.background_jobs.collection')
    def test_check_subscription_expiry_no_users(self, mock_collection):
        """Test background job with no users to process."""
        # Setup: No users found
        mock_collection.find.return_value = []
        
        # Test
        jobs_service = BackgroundJobsService()
        result = jobs_service.check_subscription_expiry()
        
        # Assert
        assert result["status"] == "success"
        assert result["total_users_processed"] == 0
        assert result["total_transitions"] == 0
        assert result["expired_to_grace"]["count"] == 0
        assert result["grace_to_free"]["count"] == 0


# ===== TIMEZONE HANDLING CONSISTENCY TESTS =====

class TestTimezoneHandling:
    """Test timezone handling consistency across the system."""

    def test_timezone_consistency_across_functions(self):
        """Test that all functions handle timezones consistently."""
        # Setup: Various timezone representations
        now_naive = datetime(2024, 3, 15, 12, 0, 0)
        now_utc = datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        now_est = datetime(2024, 3, 15, 7, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
        
        # Test: All should convert to UTC consistently
        result_naive = handle_timezone_safe_operations(now_naive)
        result_utc = handle_timezone_safe_operations(now_utc)
        result_est = handle_timezone_safe_operations(now_est)
        
        # Assert: All results should be in UTC and equivalent
        assert result_naive.tzinfo == timezone.utc
        assert result_utc.tzinfo == timezone.utc
        assert result_est.tzinfo == timezone.utc
        assert result_utc == result_est  # EST 7am = UTC 12pm

    @patch('app.services.subscription_service.collection')
    def test_grace_period_calculation_timezone_safe(self, mock_collection):
        """Test grace period calculation is timezone-safe."""
        # Setup: User with subscription end date in different timezone
        est_tz = timezone(timedelta(hours=-5))
        end_date_est = datetime(2024, 3, 15, 23, 59, 59, tzinfo=est_tz)
        
        user_data = {
            "id": "user-123",
            "subscription_tier": "pro",
            "subscription_status": "expired", 
            "subscription_end_date": end_date_est
        }
        mock_collection.find_one.return_value = user_data
        
        # Test
        status = get_subscription_status_with_grace("user-123")
        
        # Assert: Grace period end should be calculated correctly in UTC
        expected_grace_end = end_date_est.astimezone(timezone.utc) + timedelta(days=GRACE_PERIOD_DAYS)
        assert status["grace_period_end"] == expected_grace_end


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 