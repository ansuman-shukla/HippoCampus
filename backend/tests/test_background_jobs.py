import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from app.services.background_jobs import (
    BackgroundJobsService, 
    background_jobs_service,
    reset_monthly_summaries, 
    check_subscription_expiry
)
from app.core.database import collection
import logging

# Test fixture for background jobs service
@pytest.fixture
def jobs_service():
    return BackgroundJobsService()

# Test fixture for test users data
@pytest.fixture
def test_users_data():
    """Create test users with various subscription states for background job testing"""
    now = datetime.now(timezone.utc)
    
    return [
        {
            "id": "user_1",
            "email": "user1@test.com",
            "subscription_tier": "free",
            "subscription_status": "active",
            "subscription_start_date": now,
            "subscription_end_date": None,
            "total_memories_saved": 10,
            "monthly_summary_pages_used": 3,
            "monthly_summary_reset_date": datetime(now.year, now.month, 1)
        },
        {
            "id": "user_2", 
            "email": "user2@test.com",
            "subscription_tier": "pro",
            "subscription_status": "active",
            "subscription_start_date": now - timedelta(days=60),
            "subscription_end_date": now - timedelta(days=5),  # Expired 5 days ago
            "total_memories_saved": 150,
            "monthly_summary_pages_used": 25,
            "monthly_summary_reset_date": datetime(now.year, now.month, 1)
        },
        {
            "id": "user_3",
            "email": "user3@test.com", 
            "subscription_tier": "pro",
            "subscription_status": "active",
            "subscription_start_date": now - timedelta(days=15),
            "subscription_end_date": now + timedelta(days=15),  # Active for 15 more days
            "total_memories_saved": 75,
            "monthly_summary_pages_used": 12,
            "monthly_summary_reset_date": datetime(now.year, now.month, 1)
        },
        {
            "id": "user_4",
            "email": "user4@test.com",
            "subscription_tier": "pro", 
            "subscription_status": "active",
            "subscription_start_date": now - timedelta(days=25),
            "subscription_end_date": now - timedelta(hours=2),  # Expired 2 hours ago
            "total_memories_saved": 200,
            "monthly_summary_pages_used": 45,
            "monthly_summary_reset_date": datetime(now.year, now.month, 1)
        },
        {
            "id": "user_5",
            "email": "user5@test.com",
            "subscription_tier": "free",
            "subscription_status": "active", 
            "subscription_start_date": now,
            "subscription_end_date": None,
            "total_memories_saved": 0,
            "monthly_summary_pages_used": 0,
            "monthly_summary_reset_date": datetime(now.year, now.month, 1)
        }
    ]

class TestBackgroundJobsService:
    
    def setup_method(self):
        """Setup before each test"""
        # Clear any existing test data
        collection.delete_many({"email": {"$regex": "@test.com"}})
    
    def teardown_method(self):
        """Cleanup after each test"""
        # Clear test data
        collection.delete_many({"email": {"$regex": "@test.com"}})

    # ===== MONTHLY RESET TESTS =====

    def test_monthly_reset_zeroes_summary_counts(self, jobs_service, test_users_data):
        """Integration test: Monthly reset zeroes summary counts"""
        # Insert test users with non-zero summary pages
        collection.insert_many(test_users_data)
        
        # Verify users have non-zero summary pages before reset
        users_before = list(collection.find({"email": {"$regex": "@test.com"}}))
        non_zero_count_before = sum(1 for user in users_before if user.get("monthly_summary_pages_used", 0) > 0)
        assert non_zero_count_before > 0, "Test setup should have users with non-zero summary pages"
        
        # Execute monthly reset
        result = jobs_service.reset_monthly_summaries()
        
        # Verify the reset was successful
        assert result["status"] == "success"
        assert result["job_name"] == "reset_monthly_summaries"
        assert result["users_updated"] > 0
        assert len(result["errors"]) == 0
        
        # Verify all users now have zero monthly summary pages
        users_after = list(collection.find({"email": {"$regex": "@test.com"}}))
        for user in users_after:
            assert user.get("monthly_summary_pages_used") == 0, f"User {user['id']} should have 0 summary pages after reset"
            
        # Verify other fields are unchanged
        for i, user_after in enumerate(users_after):
            user_before = next(u for u in users_before if u["id"] == user_after["id"])
            assert user_after["total_memories_saved"] == user_before["total_memories_saved"]
            assert user_after["subscription_tier"] == user_before["subscription_tier"]
            assert user_after["subscription_status"] == user_before["subscription_status"]

    def test_monthly_reset_updates_reset_dates(self, jobs_service, test_users_data):
        """Integration test: Monthly reset updates reset dates"""
        # Insert test users
        collection.insert_many(test_users_data)
        
        # Get current month start for comparison
        now = datetime.now(timezone.utc)
        expected_reset_date = datetime(now.year, now.month, 1)
        
        # Execute monthly reset
        result = jobs_service.reset_monthly_summaries()
        
        # Verify the reset was successful
        assert result["status"] == "success"
        assert result["reset_date"] is not None
        
        # Verify all users have updated reset dates
        users_after = list(collection.find({"email": {"$regex": "@test.com"}}))
        for user in users_after:
            reset_date = user.get("monthly_summary_reset_date")
            assert reset_date is not None, f"User {user['id']} should have a reset date"
            
            # Convert to datetime if it's a string
            if isinstance(reset_date, str):
                reset_date = datetime.fromisoformat(reset_date.replace('Z', '+00:00'))
            
            # Allow some tolerance for time differences during test execution
            time_diff = abs((reset_date - expected_reset_date).total_seconds())
            assert time_diff < 60, f"Reset date should be close to expected date for user {user['id']}"

    def test_monthly_reset_handles_empty_database(self, jobs_service):
        """Integration test: Monthly reset handles empty database gracefully"""
        # Ensure database is empty for this test
        collection.delete_many({"email": {"$regex": "@test.com"}})
        
        # Execute monthly reset on empty database
        result = jobs_service.reset_monthly_summaries()
        
        # Should complete successfully even with no users
        assert result["status"] == "success"
        assert result["users_updated"] == 0
        assert len(result["errors"]) == 0

    # ===== SUBSCRIPTION EXPIRY TESTS =====

    def test_expiry_check_downgrades_expired_users(self, jobs_service, test_users_data):
        """Integration test: Expiry check downgrades expired users"""
        # Insert test users (includes expired pro users)
        collection.insert_many(test_users_data)
        
        # Count expired pro users before the job
        now = datetime.now(timezone.utc)
        expired_users_before = list(collection.find({
            "subscription_tier": "pro",
            "subscription_status": "active", 
            "subscription_end_date": {"$lte": now}
        }))
        
        assert len(expired_users_before) > 0, "Test setup should have expired pro users"
        
        # Execute expiry check job
        result = jobs_service.check_subscription_expiry()
        
        # Verify the job completed successfully
        assert result["status"] in ["success", "partial_success"]
        assert result["job_name"] == "check_subscription_expiry_with_grace"
        assert result["total_users_processed"] == len(expired_users_before)
        assert result["expired_to_grace"]["count"] == len(expired_users_before)
        
        # Verify expired users were moved to grace period (not downgraded to free yet)
        for expired_user in expired_users_before:
            user_after = collection.find_one({"id": expired_user["id"]})
            assert user_after["subscription_tier"] == "pro", f"User {expired_user['id']} should remain pro in grace period"
            assert user_after["subscription_status"] == "expired", f"User {expired_user['id']} should have expired status"
            # End date should be preserved for audit trail
            assert user_after["subscription_end_date"] == expired_user["subscription_end_date"]
        
        # Verify users moved to grace period are recorded in result
        grace_period_user_ids = [u["user_id"] for u in result["expired_to_grace"]["users"]]
        expected_user_ids = [u["id"] for u in expired_users_before]
        assert set(grace_period_user_ids) == set(expected_user_ids)

    def test_expiry_check_non_expired_users_remain_unchanged(self, jobs_service, test_users_data):
        """Integration test: Non-expired users remain unchanged"""
        # Insert test users
        collection.insert_many(test_users_data)
        
        # Find non-expired pro users
        now = datetime.now(timezone.utc)
        non_expired_users_before = list(collection.find({
            "subscription_tier": "pro",
            "subscription_status": "active",
            "subscription_end_date": {"$gt": now}
        }))
        
        assert len(non_expired_users_before) > 0, "Test setup should have non-expired pro users"
        
        # Execute expiry check job
        result = jobs_service.check_subscription_expiry()
        
        # Verify non-expired users are unchanged
        for user_before in non_expired_users_before:
            user_after = collection.find_one({"id": user_before["id"]})
            assert user_after["subscription_tier"] == "pro", f"Non-expired user {user_before['id']} should remain pro"
            assert user_after["subscription_status"] == "active", f"Non-expired user {user_before['id']} should remain active"
            assert user_after["subscription_end_date"] == user_before["subscription_end_date"]
            assert user_after["total_memories_saved"] == user_before["total_memories_saved"]
            assert user_after["monthly_summary_pages_used"] == user_before["monthly_summary_pages_used"]

    def test_expiry_check_free_users_remain_unchanged(self, jobs_service, test_users_data):
        """Integration test: Free users are not affected by expiry checks"""
        # Insert test users
        collection.insert_many(test_users_data)
        
        # Find free users
        free_users_before = list(collection.find({"subscription_tier": "free"}))
        assert len(free_users_before) > 0, "Test setup should have free users"
        
        # Execute expiry check job
        result = jobs_service.check_subscription_expiry()
        
        # Verify free users are completely unchanged
        for user_before in free_users_before:
            user_after = collection.find_one({"id": user_before["id"]})
            assert user_after == user_before, f"Free user {user_before['id']} should be completely unchanged"

    def test_expiry_check_handles_no_expired_users(self, jobs_service):
        """Integration test: Expiry check handles case with no expired users"""
        # Create only non-expired users
        now = datetime.now(timezone.utc)
        non_expired_users = [
            {
                "id": "user_active_1",
                "email": "active1@test.com",
                "subscription_tier": "pro",
                "subscription_status": "active",
                "subscription_end_date": now + timedelta(days=30),
                "monthly_summary_pages_used": 5
            },
            {
                "id": "user_free_1", 
                "email": "free1@test.com",
                "subscription_tier": "free",
                "subscription_status": "active",
                "subscription_end_date": None,
                "monthly_summary_pages_used": 2
            }
        ]
        
        collection.insert_many(non_expired_users)
        
        # Execute expiry check job
        result = jobs_service.check_subscription_expiry()
        
        # Should complete successfully with no transitions
        assert result["status"] == "success"
        assert result["total_users_processed"] == 0
        assert result["total_transitions"] == 0
        assert result["expired_to_grace"]["count"] == 0
        assert result["grace_to_free"]["count"] == 0
        assert len(result["errors"]) == 0

    # ===== ERROR HANDLING TESTS =====

    def test_monthly_reset_handles_database_errors_gracefully(self, jobs_service):
        """Unit test: Background jobs handle database errors gracefully"""
        # Mock the subscription service function to raise an exception
        with patch('app.services.background_jobs.subscription_reset_monthly_summaries') as mock_reset:
            mock_reset.side_effect = Exception("Database connection failed")
            
            # Execute monthly reset job
            result = jobs_service.reset_monthly_summaries()
            
            # Should handle error gracefully
            assert result["status"] == "error"
            assert result["users_updated"] == 0
            assert result["reset_date"] is None
            assert len(result["errors"]) == 1
            assert "Database connection failed" in result["errors"][0]
            assert "duration_seconds" in result
            assert result["job_start_time"] is not None
            assert result["job_end_time"] is not None

    def test_expiry_check_handles_database_errors_gracefully(self, jobs_service):
        """Unit test: Expiry check handles database errors gracefully"""
        # Mock the collection.find method to raise an exception
        with patch('app.services.background_jobs.collection.find') as mock_find:
            mock_find.side_effect = Exception("Database query failed")
            
            # Execute expiry check job
            result = jobs_service.check_subscription_expiry()
            
            # Should handle error gracefully
            assert result["status"] == "error"
            assert result["total_users_processed"] == 0
            assert result["total_transitions"] == 0
            assert result["expired_to_grace"]["count"] == 0
            assert result["grace_to_free"]["count"] == 0
            assert len(result["errors"]) == 1
            assert "Database query failed" in result["errors"][0]
            assert "duration_seconds" in result
            assert result["job_start_time"] is not None
            assert result["job_end_time"] is not None

    def test_expiry_check_handles_partial_failures(self, jobs_service, test_users_data):
        """Integration test: Expiry check handles partial failures during user processing"""
        # Insert test users with expired pro users
        collection.insert_many(test_users_data)
        
        # Mock collection.update_one to fail for specific user
        original_update_one = collection.update_one
        def mock_update_one(filter_dict, update_dict, **kwargs):
            if filter_dict.get("id") == "user_2":  # Fail for user_2
                raise Exception("Update failed for user_2")
            return original_update_one(filter_dict, update_dict, **kwargs)
        
        with patch.object(collection, 'update_one', side_effect=mock_update_one):
            result = jobs_service.check_subscription_expiry()
            
            # Should complete with partial success
            assert result["status"] in ["partial_success", "error"]
            assert len(result["errors"]) > 0
            assert any("user_2" in error for error in result["errors"])
            
            # Other expired users should still be processed
            if result["total_transitions"] > 0:
                # At least one user should have been successfully moved to grace period
                assert result["expired_to_grace"]["count"] > 0

    # ===== HELPER FUNCTION TESTS =====

    def test_get_users_needing_monthly_reset(self, jobs_service, test_users_data):
        """Test helper function to get users needing monthly reset"""
        # Insert test users
        collection.insert_many(test_users_data)
        
        # Get users needing reset
        users_needing_reset = jobs_service.get_users_needing_monthly_reset()
        
        # Should find users with non-zero summary pages
        assert len(users_needing_reset) > 0
        for user in users_needing_reset:
            assert user["monthly_summary_pages_used"] > 0
            assert "id" in user
            assert "email" in user
            assert "subscription_tier" in user

    def test_get_users_with_expiring_subscriptions(self, jobs_service):
        """Test helper function to get users with expiring subscriptions"""
        # Create users with subscriptions expiring in different timeframes
        now = datetime.now(timezone.utc)
        test_users = [
            {
                "id": "user_expiring_soon",
                "email": "expiring@test.com", 
                "subscription_tier": "pro",
                "subscription_status": "active",
                "subscription_end_date": now + timedelta(days=3)  # Expires in 3 days
            },
            {
                "id": "user_expiring_later",
                "email": "later@test.com",
                "subscription_tier": "pro", 
                "subscription_status": "active",
                "subscription_end_date": now + timedelta(days=15)  # Expires in 15 days
            }
        ]
        
        collection.insert_many(test_users)
        
        # Get users expiring within 7 days
        expiring_users = jobs_service.get_users_with_expiring_subscriptions(days_ahead=7)
        
        # Should find only the user expiring in 3 days
        assert len(expiring_users) == 1
        assert expiring_users[0]["id"] == "user_expiring_soon"
        
        # Get users expiring within 20 days
        expiring_users_20 = jobs_service.get_users_with_expiring_subscriptions(days_ahead=20)
        
        # Should find both users
        assert len(expiring_users_20) == 2
        user_ids = [u["id"] for u in expiring_users_20]
        assert "user_expiring_soon" in user_ids
        assert "user_expiring_later" in user_ids

    # ===== CONVENIENCE FUNCTION TESTS =====

    def test_convenience_functions_work_correctly(self, test_users_data):
        """Test that convenience functions work correctly"""
        # Insert test users
        collection.insert_many(test_users_data)
        
        # Test reset convenience function
        reset_result = reset_monthly_summaries()
        assert reset_result["status"] == "success"
        assert reset_result["job_name"] == "reset_monthly_summaries"
        
        # Test expiry check convenience function
        expiry_result = check_subscription_expiry()
        assert expiry_result["job_name"] == "check_subscription_expiry_with_grace"
        assert expiry_result["status"] in ["success", "partial_success"]

    # ===== LOGGING TESTS =====

    def test_jobs_produce_proper_logging(self, jobs_service, test_users_data, caplog):
        """Test that background jobs produce proper logging output"""
        # Insert test users
        collection.insert_many(test_users_data)
        
        with caplog.at_level(logging.INFO):
            # Execute both jobs
            reset_result = jobs_service.reset_monthly_summaries()
            expiry_result = jobs_service.check_subscription_expiry()
            
            # Check that proper log messages were generated
            log_messages = [record.message for record in caplog.records]
            
            # Should contain job start/completion messages
            assert any("Starting monthly summary reset job" in msg for msg in log_messages)
            assert any("Monthly summary reset job completed" in msg for msg in log_messages)
            assert any("Starting subscription expiry check job with grace period support" in msg for msg in log_messages) 
            assert any("Subscription expiry check with grace period completed" in msg for msg in log_messages)
            
            # Should contain operational details
            assert any("Users updated:" in msg for msg in log_messages)
            assert any("Duration:" in msg for msg in log_messages) 