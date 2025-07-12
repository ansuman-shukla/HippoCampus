#!/usr/bin/env python3
"""
Migration script to backfill existing users with subscription data.

This script:
1. Finds all existing users without subscription fields
2. Calculates correct total_memories_saved from existing data
3. Sets proper subscription defaults and monthly reset dates
4. Is idempotent and safe to run multiple times

Usage:
    python scripts/migrate_subscriptions.py
    
For dry run (no actual changes):
    python scripts/migrate_subscriptions.py --dry-run
"""

import sys
import os
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, List
import logging

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import collection, collection_memories
from pymongo.errors import PyMongoError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SubscriptionMigrator:
    """Handles migration of subscription data for existing users."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.stats = {
            "users_processed": 0,
            "users_updated": 0,
            "users_skipped": 0,
            "memories_counted": 0,
            "errors": 0
        }
    
    def get_subscription_defaults(self) -> Dict[str, Any]:
        """Get default subscription values for new users."""
        now = datetime.utcnow()
        monthly_reset_date = datetime(now.year, now.month, 1)
        
        return {
            "subscription_tier": "free",
            "subscription_status": "active", 
            "subscription_start_date": now,
            "subscription_end_date": None,
            "total_memories_saved": 0,  # Will be calculated per user
            "monthly_summary_pages_used": 0,
            "monthly_summary_reset_date": monthly_reset_date
        }
    
    def user_needs_migration(self, user: Dict[str, Any]) -> bool:
        """Check if user needs subscription field migration."""
        required_fields = [
            "subscription_tier",
            "subscription_status", 
            "subscription_start_date",
            "total_memories_saved",
            "monthly_summary_pages_used",
            "monthly_summary_reset_date"
        ]
        
        missing_fields = [field for field in required_fields if field not in user]
        
        if missing_fields:
            logger.info(f"User {user.get('id', 'unknown')} missing fields: {missing_fields}")
            return True
            
        return False
    
    async def count_user_memories(self, user_id: str) -> int:
        """Count existing memories for a user."""
        try:
            # Use sync count since we're not using the safe wrapper here
            count = collection_memories.count_documents({"user_id": user_id})
            logger.debug(f"User {user_id} has {count} existing memories")
            return count
        except PyMongoError as e:
            logger.error(f"Error counting memories for user {user_id}: {str(e)}")
            return 0
    
    async def migrate_user(self, user: Dict[str, Any]) -> bool:
        """Migrate a single user's subscription data."""
        user_id = user.get("id")
        if not user_id:
            logger.error(f"User missing ID field: {user}")
            return False
            
        try:
            # Get defaults
            defaults = self.get_subscription_defaults()
            
            # Count existing memories for this user
            memory_count = await self.count_user_memories(user_id)
            defaults["total_memories_saved"] = memory_count
            
            # Prepare update document with only missing fields
            update_fields = {}
            for field, value in defaults.items():
                if field not in user:
                    update_fields[field] = value
            
            if not update_fields:
                logger.info(f"User {user_id} already has all subscription fields - skipping")
                self.stats["users_skipped"] += 1
                return True
            
            # Log what will be updated
            logger.info(f"Migrating user {user_id}:")
            logger.info(f"  Adding fields: {list(update_fields.keys())}")
            logger.info(f"  Memory count: {memory_count}")
            
            if not self.dry_run:
                # Perform the update
                result = collection.update_one(
                    {"id": user_id},
                    {"$set": update_fields}
                )
                
                if result.modified_count != 1:
                    logger.warning(f"Expected to modify 1 document for user {user_id}, but modified {result.modified_count}")
                    return False
                    
                logger.info(f"✅ Successfully migrated user {user_id}")
            else:
                logger.info(f"🔍 DRY RUN: Would update user {user_id} with fields: {update_fields}")
            
            self.stats["users_updated"] += 1
            self.stats["memories_counted"] += memory_count
            return True
            
        except Exception as e:
            logger.error(f"Error migrating user {user_id}: {str(e)}")
            self.stats["errors"] += 1
            return False
    
    async def migrate_all_users(self) -> Dict[str, Any]:
        """Migrate all users that need subscription data."""
        logger.info("🚀 Starting subscription migration...")
        
        if self.dry_run:
            logger.info("🔍 Running in DRY RUN mode - no changes will be made")
        
        try:
            # Get all users
            users = list(collection.find({}))
            total_users = len(users)
            
            logger.info(f"Found {total_users} users to process")
            
            for i, user in enumerate(users, 1):
                logger.info(f"Processing user {i}/{total_users}...")
                self.stats["users_processed"] += 1
                
                if self.user_needs_migration(user):
                    await self.migrate_user(user)
                else:
                    logger.info(f"User {user.get('id', 'unknown')} already has subscription data - skipping")
                    self.stats["users_skipped"] += 1
            
            # Print final stats
            logger.info("🎉 Migration completed!")
            logger.info("📊 Final Statistics:")
            logger.info(f"  Users processed: {self.stats['users_processed']}")
            logger.info(f"  Users updated: {self.stats['users_updated']}")
            logger.info(f"  Users skipped: {self.stats['users_skipped']}")
            logger.info(f"  Total memories counted: {self.stats['memories_counted']}")
            logger.info(f"  Errors: {self.stats['errors']}")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Fatal error during migration: {str(e)}")
            self.stats["errors"] += 1
            raise

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate subscription data for existing users")
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Run in dry-run mode (no actual changes)"
    )
    
    args = parser.parse_args()
    
    migrator = SubscriptionMigrator(dry_run=args.dry_run)
    
    try:
        # Run the migration
        stats = asyncio.run(migrator.migrate_all_users())
        
        if stats["errors"] > 0:
            logger.error(f"Migration completed with {stats['errors']} errors")
            sys.exit(1)
        else:
            logger.info("Migration completed successfully!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 