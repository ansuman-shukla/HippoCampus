import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys
import os

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))

from migrate_subscriptions import SubscriptionMigrator
from app.core.database import collection, collection_memories


class TestSubscriptionMigration:
    """Integration tests for subscription migration script."""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Setup and cleanup test data for each test."""
        import time
        # Track test users created during test - use timestamp for uniqueness
        self.test_timestamp = str(int(time.time() * 1000))  # milliseconds
        self.test_user_ids = []
        
        # Clean up any existing test data more aggressively
        collection.delete_many({"email": {"$regex": "test_migrate_.*"}})
        collection.delete_many({"id": {"$regex": "test_user_.*"}})
        collection_memories.delete_many({"user_id": {"$regex": "test_user_.*"}})
        
        yield
        
        # Cleanup after test - delete test data we created
        if self.test_user_ids:
            collection.delete_many({"id": {"$in": self.test_user_ids}})
            collection_memories.delete_many({"user_id": {"$in": self.test_user_ids}})
    
    def create_test_user(self, user_id: str, email: str, include_subscription: bool = False):
        """Helper to create test users."""
        user_data = {
            "id": user_id,
            "email": email,
            "role": "user",
            "created_at": datetime.utcnow(),
            "last_sign_in_at": datetime.utcnow(),
            "full_name": f"Test User {user_id}",
            "picture": "",
            "issuer": "test",
            "provider": "test",
            "providers": ["test"]
        }
        
        if include_subscription:
            # Add all subscription fields
            now = datetime.utcnow()
            monthly_reset_date = datetime(now.year, now.month, 1)
            
            user_data.update({
                "subscription_tier": "free",
                "subscription_status": "active",
                "subscription_start_date": now,
                "subscription_end_date": None,
                "total_memories_saved": 0,
                "monthly_summary_pages_used": 0,
                "monthly_summary_reset_date": monthly_reset_date
            })
        
        result = collection.insert_one(user_data)
        self.test_user_ids.append(user_id)  # Track for cleanup
        return str(result.inserted_id)
    
    def create_test_memory(self, user_id: str, memory_id: str, title: str):
        """Helper to create test memories."""
        memory_data = {
            "user_id": user_id,
            "doc_id": memory_id,
            "title": title,
            "content": f"Test content for {title}",
            "url": f"https://example.com/{memory_id}",
            "created_at": datetime.utcnow()
        }
        
        result = collection_memories.insert_one(memory_data)
        return str(result.inserted_id)
    
    async def run_migration_with_test_users_only(self, dry_run: bool = False):
        """Helper to run migration with only test users."""
        # Simpler approach - just run the migration without mocking
        # Since we've cleaned up other users, the migration should only process our test users
        migrator = SubscriptionMigrator(dry_run=dry_run)
        return await migrator.migrate_all_users()
    
    @pytest.mark.asyncio
    async def test_migration_handles_users_with_no_memories(self):
        """Integration test: Migration script handles users with no memories."""
        # Create test user without subscription fields and no memories
        user_id = f"test_user_no_memories_{self.test_timestamp}"
        self.create_test_user(user_id, f"test_migrate_no_memories_{self.test_timestamp}@example.com")
        
# Clean up debug output for production
        # print(f"Test user IDs: {self.test_user_ids}")
        
        # Run migration in dry-run mode first
        stats = await self.run_migration_with_test_users_only(dry_run=True)
        
        # Verify dry run stats - focus on our test user being included in the count
        assert stats["users_updated"] >= 1  # Our test user should be updated
        assert stats["errors"] == 0
        
        # Verify our specific test user doesn't have subscription fields yet (dry run didn't change anything)
        test_user_before = collection.find_one({"id": user_id})
        assert "subscription_tier" not in test_user_before
        
        # Run actual migration
        stats = await self.run_migration_with_test_users_only(dry_run=False)
        
        # Verify migration stats - our test user should be included
        assert stats["users_updated"] >= 1  # Our test user should be updated
        assert stats["errors"] == 0
        
        # Verify user was updated correctly
        updated_user = collection.find_one({"id": user_id})
        assert updated_user is not None
        assert updated_user["subscription_tier"] == "free"
        assert updated_user["subscription_status"] == "active"
        assert updated_user["total_memories_saved"] == 0
        assert updated_user["monthly_summary_pages_used"] == 0
        assert "subscription_start_date" in updated_user
        assert "monthly_summary_reset_date" in updated_user
    
    @pytest.mark.asyncio
    async def test_migration_correctly_counts_existing_memories(self):
        """Integration test: Migration script correctly counts existing memories."""
        # Create test user without subscription fields
        user_id = f"test_user_with_memories_{self.test_timestamp}"
        self.create_test_user(user_id, f"test_migrate_with_memories_{self.test_timestamp}@example.com")
        
        # Create multiple memories for this user
        memory_count = 5
        for i in range(memory_count):
            self.create_test_memory(user_id, f"memory_{i}_{self.test_timestamp}", f"Test Memory {i}")
        
        # Also create memories for a different user to ensure counting is correct
        other_user_id = f"other_test_user_{self.test_timestamp}"
        self.create_test_user(other_user_id, f"test_migrate_other_{self.test_timestamp}@example.com")
        for i in range(3):
            self.create_test_memory(other_user_id, f"other_memory_{i}_{self.test_timestamp}", f"Other Memory {i}")
        
        # Run migration
        stats = await self.run_migration_with_test_users_only(dry_run=False)
        
        # Verify migration stats - our test users should be included
        assert stats["users_updated"] >= 2  # Our test users should be updated
        assert stats["errors"] == 0
        
        # Verify first user's memory count is correct
        updated_user = collection.find_one({"id": user_id})
        assert updated_user is not None
        assert updated_user["total_memories_saved"] == memory_count
        assert updated_user["subscription_tier"] == "free"
        assert updated_user["subscription_status"] == "active"
        
        # Verify other user's memory count is correct
        other_updated_user = collection.find_one({"id": other_user_id})
        assert other_updated_user is not None
        assert other_updated_user["total_memories_saved"] == 3
        assert other_updated_user["subscription_tier"] == "free"
        assert other_updated_user["subscription_status"] == "active"
    
    @pytest.mark.asyncio
    async def test_migration_doesnt_duplicate_subscription_fields(self):
        """Integration test: Migration script doesn't duplicate subscription fields."""
        # Create test user WITH existing subscription fields
        user_id = f"test_user_with_subscription_{self.test_timestamp}"
        self.create_test_user(user_id, f"test_migrate_has_sub_{self.test_timestamp}@example.com", include_subscription=True)
        
        # Create some memories for this user
        memory_count = 3
        for i in range(memory_count):
            self.create_test_memory(user_id, f"existing_memory_{i}_{self.test_timestamp}", f"Existing Memory {i}")
        
        # Get original subscription data
        original_user = collection.find_one({"id": user_id})
        original_tier = original_user["subscription_tier"]
        original_start_date = original_user["subscription_start_date"]
        original_total_memories = original_user["total_memories_saved"]
        
        # Run migration
        stats = await self.run_migration_with_test_users_only(dry_run=False)
        
        # Verify migration stats - user should be among those skipped (since it has subscription fields)
        # We can't guarantee exact counts due to existing users, but we can verify our specific user
        assert stats["errors"] == 0
        
        # Verify user data unchanged
        updated_user = collection.find_one({"id": user_id})
        assert updated_user is not None
        assert updated_user["subscription_tier"] == original_tier
        assert updated_user["subscription_start_date"] == original_start_date
        assert updated_user["total_memories_saved"] == original_total_memories  # Should not be recalculated
    
    @pytest.mark.asyncio
    async def test_migration_is_idempotent(self):
        """Integration test: Migration script is idempotent (safe to run multiple times)."""
        # Create test user without subscription fields
        user_id = f"test_user_idempotent_{self.test_timestamp}"
        self.create_test_user(user_id, f"test_migrate_idempotent_{self.test_timestamp}@example.com")
        
        # Create memories for this user
        memory_count = 4
        for i in range(memory_count):
            self.create_test_memory(user_id, f"idempotent_memory_{i}_{self.test_timestamp}", f"Idempotent Memory {i}")
        
        # Run migration first time
        stats1 = await self.run_migration_with_test_users_only(dry_run=False)
        
        # Verify first migration - our test user should be included
        assert stats1["users_updated"] >= 1  # Our test user should be updated
        assert stats1["errors"] == 0
        
        # Get user data after first migration
        user_after_first = collection.find_one({"id": user_id})
        first_subscription_data = {
            "subscription_tier": user_after_first["subscription_tier"],
            "subscription_status": user_after_first["subscription_status"],
            "subscription_start_date": user_after_first["subscription_start_date"],
            "total_memories_saved": user_after_first["total_memories_saved"],
            "monthly_summary_pages_used": user_after_first["monthly_summary_pages_used"],
            "monthly_summary_reset_date": user_after_first["monthly_summary_reset_date"]
        }
        
        # Run migration second time (should be idempotent)
        stats2 = await self.run_migration_with_test_users_only(dry_run=False)
        
        # Verify second migration - our user should now be skipped (already has subscription fields)
        # Since existing users might also be processed, we can't guarantee exact counts
        assert stats2["errors"] == 0
        
        # Verify user data is unchanged after second migration
        user_after_second = collection.find_one({"id": user_id})
        second_subscription_data = {
            "subscription_tier": user_after_second["subscription_tier"],
            "subscription_status": user_after_second["subscription_status"],
            "subscription_start_date": user_after_second["subscription_start_date"],
            "total_memories_saved": user_after_second["total_memories_saved"],
            "monthly_summary_pages_used": user_after_second["monthly_summary_pages_used"],
            "monthly_summary_reset_date": user_after_second["monthly_summary_reset_date"]
        }
        
        assert first_subscription_data == second_subscription_data
        
        # Run migration third time to be absolutely sure
        stats3 = await self.run_migration_with_test_users_only(dry_run=False)
        
        # Verify third migration - still should produce same results
        assert stats3["errors"] == 0
        
        # Verify user data is still unchanged
        user_after_third = collection.find_one({"id": user_id})
        assert user_after_third["subscription_tier"] == first_subscription_data["subscription_tier"]
        assert user_after_third["total_memories_saved"] == first_subscription_data["total_memories_saved"]
    
    @pytest.mark.asyncio
    async def test_migration_handles_mixed_user_scenarios(self):
        """Integration test: Migration handles mixed scenarios correctly."""
        # Create multiple users with different states
        
        # User 1: No subscription fields, no memories
        user1_id = f"test_user_mixed_1_{self.test_timestamp}"
        self.create_test_user(user1_id, f"test_migrate_mixed_1_{self.test_timestamp}@example.com")
        
        # User 2: No subscription fields, has memories
        user2_id = f"test_user_mixed_2_{self.test_timestamp}"
        self.create_test_user(user2_id, f"test_migrate_mixed_2_{self.test_timestamp}@example.com")
        for i in range(7):
            self.create_test_memory(user2_id, f"mixed_memory_2_{i}_{self.test_timestamp}", f"Mixed Memory 2-{i}")
        
        # User 3: Has subscription fields (should be skipped)
        user3_id = f"test_user_mixed_3_{self.test_timestamp}"
        self.create_test_user(user3_id, f"test_migrate_mixed_3_{self.test_timestamp}@example.com", include_subscription=True)
        for i in range(2):
            self.create_test_memory(user3_id, f"mixed_memory_3_{i}_{self.test_timestamp}", f"Mixed Memory 3-{i}")
        
        # User 4: Partial subscription fields (missing some)
        user4_id = f"test_user_mixed_4_{self.test_timestamp}"
        user4_doc_id = self.create_test_user(user4_id, f"test_migrate_mixed_4_{self.test_timestamp}@example.com")
        
        # Add only some subscription fields to user 4
        collection.update_one(
            {"id": user4_id},
            {"$set": {
                "subscription_tier": "pro",  # Different from default
                "subscription_status": "active",
                # Missing other fields
            }}
        )
        
        for i in range(1):
            self.create_test_memory(user4_id, f"mixed_memory_4_{i}_{self.test_timestamp}", f"Mixed Memory 4-{i}")
        
        # Run migration
        stats = await self.run_migration_with_test_users_only(dry_run=False)
        
        # Verify overall stats - focus on our test users working correctly
        # Can't guarantee exact counts due to existing users, but ensure no errors
        assert stats["errors"] == 0
        
        # Verify each user individually
        
        # User 1: Should have subscription with 0 memories
        user1_updated = collection.find_one({"id": user1_id})
        assert user1_updated["subscription_tier"] == "free"
        assert user1_updated["total_memories_saved"] == 0
        
        # User 2: Should have subscription with 7 memories
        user2_updated = collection.find_one({"id": user2_id})
        assert user2_updated["subscription_tier"] == "free"
        assert user2_updated["total_memories_saved"] == 7
        
        # User 3: Should be unchanged (skipped)
        user3_updated = collection.find_one({"id": user3_id})
        assert user3_updated["subscription_tier"] == "free"  # Original value
        assert user3_updated["total_memories_saved"] == 0   # Original value, not recalculated
        
        # User 4: Should have missing fields added, existing fields preserved
        user4_updated = collection.find_one({"id": user4_id})
        assert user4_updated["subscription_tier"] == "pro"  # Should preserve existing value
        assert user4_updated["subscription_status"] == "active"  # Should preserve existing value
        assert user4_updated["total_memories_saved"] == 1  # Should calculate from memories
        assert "subscription_start_date" in user4_updated  # Should add missing field
        assert "monthly_summary_reset_date" in user4_updated  # Should add missing field
    
    @pytest.mark.asyncio
    async def test_migration_with_database_errors(self):
        """Integration test: Migration handles database errors gracefully."""
        # Create test user
        user_id = f"test_user_db_error_{self.test_timestamp}"
        self.create_test_user(user_id, f"test_migrate_db_error_{self.test_timestamp}@example.com")
        
        # Mock a database error during memory counting
        with patch('scripts.migrate_subscriptions.collection_memories.count_documents') as mock_count:
            mock_count.side_effect = Exception("Database connection error")
            
            stats = await self.run_migration_with_test_users_only(dry_run=False)
            
            # Should handle error gracefully and continue
            # Can't guarantee exact counts due to existing users, but should have errors
            assert stats["errors"] >= 1
            
            # User migration should fail, so no subscription fields should be added
            updated_user = collection.find_one({"id": user_id})
            assert updated_user is not None
            # User should not have subscription fields added due to error
            assert "total_memories_saved" not in updated_user
    
    def test_subscription_migrator_user_needs_migration(self):
        """Unit test: user_needs_migration correctly identifies users needing migration."""
        migrator = SubscriptionMigrator()
        
        # User missing all subscription fields
        user_no_fields = {"id": "test", "email": "test@example.com"}
        assert migrator.user_needs_migration(user_no_fields) == True
        
        # User missing some subscription fields
        user_partial_fields = {
            "id": "test",
            "email": "test@example.com",
            "subscription_tier": "free",
            # Missing other required fields
        }
        assert migrator.user_needs_migration(user_partial_fields) == True
        
        # User with all subscription fields
        now = datetime.utcnow()
        user_all_fields = {
            "id": "test",
            "email": "test@example.com",
            "subscription_tier": "free",
            "subscription_status": "active",
            "subscription_start_date": now,
            "total_memories_saved": 0,
            "monthly_summary_pages_used": 0,
            "monthly_summary_reset_date": now
        }
        assert migrator.user_needs_migration(user_all_fields) == False
    
    def test_subscription_migrator_get_defaults(self):
        """Unit test: get_subscription_defaults returns correct default values."""
        migrator = SubscriptionMigrator()
        defaults = migrator.get_subscription_defaults()
        
        assert defaults["subscription_tier"] == "free"
        assert defaults["subscription_status"] == "active"
        assert defaults["subscription_end_date"] is None
        assert defaults["total_memories_saved"] == 0
        assert defaults["monthly_summary_pages_used"] == 0
        assert isinstance(defaults["subscription_start_date"], datetime)
        assert isinstance(defaults["monthly_summary_reset_date"], datetime)
        
        # Verify reset date is first day of current month
        now = datetime.utcnow()
        expected_reset_date = datetime(now.year, now.month, 1)
        assert defaults["monthly_summary_reset_date"] == expected_reset_date 