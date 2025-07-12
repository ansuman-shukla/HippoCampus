from app.core.database import collection
from app.services.subscription_service import reset_monthly_summaries as subscription_reset_monthly_summaries
from app.services.subscription_logging_service import subscription_logger
from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class BackgroundJobsService:
    """
    Service for handling background jobs related to subscription management.
    Includes monthly resets and subscription expiry checks.
    """
    
    def __init__(self):
        self.logger = logger
        
    def reset_monthly_summaries(self) -> Dict[str, Any]:
        """
        Reset monthly summary page counts for all users.
        This should be called on the 1st of each month.
        
        Returns:
            dict: Summary of reset operation including success/failure details
        """
        job_start_time = datetime.now(timezone.utc)
        self.logger.info(f"🔄 BACKGROUND JOBS: Starting monthly summary reset job")
        self.logger.info(f"   └─ Job start time: {job_start_time}")
        
        try:
            # Use the existing subscription service function
            reset_result = subscription_reset_monthly_summaries()
            
            job_end_time = datetime.now(timezone.utc)
            duration = (job_end_time - job_start_time).total_seconds()
            
            success_result = {
                "job_name": "reset_monthly_summaries",
                "status": "success",
                "users_updated": reset_result.get("users_updated", 0),
                "reset_date": reset_result.get("reset_date"),
                "operation_time": reset_result.get("operation_time"),
                "job_start_time": job_start_time,
                "job_end_time": job_end_time,
                "duration_seconds": duration,
                "errors": []
            }
            
            self.logger.info(f"✅ Monthly summary reset job completed successfully")
            self.logger.info(f"   ├─ Users updated: {success_result['users_updated']}")
            self.logger.info(f"   ├─ Duration: {duration:.2f} seconds")
            self.logger.info(f"   └─ Reset date: {success_result['reset_date']}")
            
            # Log monthly reset event for analytics
            subscription_logger.log_monthly_reset_event(
                total_users_reset=success_result['users_updated'],
                summary_pages_reset=0,  # This info isn't available from reset_result
                execution_time=duration
            )
            
            return success_result
            
        except Exception as e:
            job_end_time = datetime.now(timezone.utc)
            duration = (job_end_time - job_start_time).total_seconds()
            
            error_result = {
                "job_name": "reset_monthly_summaries",
                "status": "error",
                "users_updated": 0,
                "reset_date": None,
                "operation_time": None,
                "job_start_time": job_start_time,
                "job_end_time": job_end_time,
                "duration_seconds": duration,
                "errors": [str(e)]
            }
            
            self.logger.error(f"❌ Monthly summary reset job failed")
            self.logger.error(f"   ├─ Error: {str(e)}")
            self.logger.error(f"   ├─ Duration: {duration:.2f} seconds")
            self.logger.error(f"   └─ Job terminated with errors")
            
            return error_result
    
    def check_subscription_expiry(self) -> Dict[str, Any]:
        """
        Check for expired pro subscriptions and handle grace period transitions.
        This should be called daily.
        
        Returns:
            dict: Summary of expiry check operation including status transitions
        """
        job_start_time = datetime.now(timezone.utc)
        self.logger.info(f"🔍 BACKGROUND JOBS: Starting subscription expiry check job with grace period support")
        self.logger.info(f"   └─ Job start time: {job_start_time}")
        
        expired_to_grace = []  # Users moved to grace period
        grace_to_free = []     # Users moved from grace to free
        errors = []
        
        try:
            # Import here to avoid circular imports
            from app.services.subscription_service import GRACE_PERIOD_DAYS
            
            now = datetime.now(timezone.utc)
            grace_cutoff = now - timedelta(days=GRACE_PERIOD_DAYS)
            
            # 1. Find active pro users whose subscriptions just expired (move to grace period)
            recently_expired_query = {
                "subscription_tier": "pro",
                "subscription_status": "active",
                "subscription_end_date": {"$lte": now}
            }
            
            recently_expired_users = list(collection.find(recently_expired_query))
            self.logger.info(f"🔍 Found {len(recently_expired_users)} recently expired pro subscriptions to move to grace period")
            
            for user in recently_expired_users:
                try:
                    user_id = user.get("id")
                    user_email = user.get("email", "unknown")
                    end_date = user.get("subscription_end_date")
                    
                    self.logger.info(f"⏳ Moving expired user to grace period: {user_id} (email: {user_email})")
                    self.logger.info(f"   └─ Expired on: {end_date}")
                    
                    # Move to grace period (expired status but keep pro tier)
                    grace_result = collection.update_one(
                        {"id": user_id},
                        {
                            "$set": {
                                "subscription_status": "expired"
                                # Keep tier as "pro" during grace period
                                # Keep end_date for grace period calculation
                            }
                        }
                    )
                    
                    if grace_result.modified_count > 0:
                        expired_to_grace_info = {
                            "user_id": user_id,
                            "email": user_email,
                            "subscription_tier": "pro",
                            "previous_status": "active",
                            "new_status": "expired",
                            "expired_date": end_date,
                            "grace_period_end": end_date + timedelta(days=GRACE_PERIOD_DAYS) if end_date else None,
                            "moved_to_grace_at": now
                        }
                        expired_to_grace.append(expired_to_grace_info)
                        
                        # Log grace period entry event for analytics
                        grace_days_remaining = GRACE_PERIOD_DAYS
                        subscription_logger.log_grace_period_event(
                            user_id=user_id,
                            grace_action="entered",
                            days_remaining=grace_days_remaining
                        )
                        
                        self.logger.info(f"✅ Successfully moved user {user_id} to grace period")
                    else:
                        error_msg = f"Failed to move user {user_id} to grace period - no documents modified"
                        errors.append(error_msg)
                        self.logger.warning(f"⚠️ {error_msg}")
                        
                except Exception as user_error:
                    error_msg = f"Error moving user {user.get('id', 'unknown')} to grace period: {str(user_error)}"
                    errors.append(error_msg)
                    self.logger.error(f"❌ {error_msg}")
            
            # 2. Find users whose grace period has ended (move to free tier)
            grace_expired_query = {
                "subscription_tier": "pro",
                "subscription_status": "expired",
                "subscription_end_date": {"$lte": grace_cutoff}
            }
            
            grace_expired_users = list(collection.find(grace_expired_query))
            self.logger.info(f"🔍 Found {len(grace_expired_users)} users whose grace period has ended")
            
            for user in grace_expired_users:
                try:
                    user_id = user.get("id")
                    user_email = user.get("email", "unknown")
                    end_date = user.get("subscription_end_date")
                    
                    self.logger.info(f"⬇️ Downgrading grace period expired user: {user_id} (email: {user_email})")
                    self.logger.info(f"   └─ Grace period ended: {end_date + timedelta(days=GRACE_PERIOD_DAYS) if end_date else 'unknown'}")
                    
                    # Downgrade to free tier
                    downgrade_result = collection.update_one(
                        {"id": user_id},
                        {
                            "$set": {
                                "subscription_tier": "free",
                                "subscription_status": "expired"
                                # Keep end_date for audit trail
                            }
                        }
                    )
                    
                    if downgrade_result.modified_count > 0:
                        grace_to_free_info = {
                            "user_id": user_id,
                            "email": user_email,
                            "previous_tier": "pro",
                            "new_tier": "free",
                            "new_status": "expired",
                            "original_expiry_date": end_date,
                            "grace_period_end": end_date + timedelta(days=GRACE_PERIOD_DAYS) if end_date else None,
                            "downgraded_at": now
                        }
                        grace_to_free.append(grace_to_free_info)
                        
                        # Log grace period expiry and downgrade events for analytics
                        subscription_logger.log_grace_period_event(
                            user_id=user_id,
                            grace_action="expired"
                        )
                        
                        subscription_logger.log_downgrade_event(
                            user_id=user_id,
                            previous_tier="pro",
                            new_tier="free",
                            method="system",
                            reason="grace_period_expired"
                        )
                        
                        self.logger.info(f"✅ Successfully downgraded user {user_id} from grace period to free")
                    else:
                        error_msg = f"Failed to downgrade user {user_id} from grace period - no documents modified"
                        errors.append(error_msg)
                        self.logger.warning(f"⚠️ {error_msg}")
                        
                except Exception as user_error:
                    error_msg = f"Error downgrading grace period user {user.get('id', 'unknown')}: {str(user_error)}"
                    errors.append(error_msg)
                    self.logger.error(f"❌ {error_msg}")
            
            job_end_time = datetime.now(timezone.utc)
            duration = (job_end_time - job_start_time).total_seconds()
            
            total_processed = len(recently_expired_users) + len(grace_expired_users)
            total_transitions = len(expired_to_grace) + len(grace_to_free)
            
            result = {
                "job_name": "check_subscription_expiry_with_grace",
                "status": "success" if len(errors) == 0 else "partial_success" if total_transitions > 0 else "error",
                "total_users_processed": total_processed,
                "total_transitions": total_transitions,
                "expired_to_grace": {
                    "count": len(expired_to_grace),
                    "users": expired_to_grace
                },
                "grace_to_free": {
                    "count": len(grace_to_free),
                    "users": grace_to_free
                },
                "job_start_time": job_start_time,
                "job_end_time": job_end_time,
                "duration_seconds": duration,
                "errors": errors,
                "grace_period_days": GRACE_PERIOD_DAYS
            }
            
            if len(errors) == 0:
                self.logger.info(f"✅ Subscription expiry check with grace period completed successfully")
            else:
                self.logger.warning(f"⚠️ Subscription expiry check with grace period completed with {len(errors)} errors")
                
            self.logger.info(f"   ├─ Total users processed: {total_processed}")
            self.logger.info(f"   ├─ Moved to grace period: {len(expired_to_grace)}")
            self.logger.info(f"   ├─ Downgraded from grace: {len(grace_to_free)}")
            self.logger.info(f"   ├─ Errors: {len(errors)}")
            self.logger.info(f"   └─ Duration: {duration:.2f} seconds")
            
            return result
            
        except Exception as e:
            job_end_time = datetime.now(timezone.utc)
            duration = (job_end_time - job_start_time).total_seconds()
            
            error_result = {
                "job_name": "check_subscription_expiry_with_grace",
                "status": "error",
                "total_users_processed": 0,
                "total_transitions": 0,
                "expired_to_grace": {"count": 0, "users": []},
                "grace_to_free": {"count": 0, "users": []},
                "job_start_time": job_start_time,
                "job_end_time": job_end_time,
                "duration_seconds": duration,
                "errors": [str(e)],
                "grace_period_days": 7  # Default fallback
            }
            
            self.logger.error(f"❌ Subscription expiry check with grace period failed")
            self.logger.error(f"   ├─ Error: {str(e)}")
            self.logger.error(f"   ├─ Duration: {duration:.2f} seconds")
            self.logger.error(f"   └─ Job terminated with critical error")
            
            return error_result
    
    def get_users_needing_monthly_reset(self) -> List[Dict[str, Any]]:
        """
        Helper function to get users that need monthly reset (for testing purposes).
        
        Returns:
            List[dict]: Users with non-zero monthly summary pages
        """
        try:
            users_with_summary_pages = list(collection.find(
                {"monthly_summary_pages_used": {"$gt": 0}},
                {"id": 1, "email": 1, "monthly_summary_pages_used": 1, "subscription_tier": 1}
            ))
            
            self.logger.info(f"📊 Found {len(users_with_summary_pages)} users with non-zero summary pages")
            return users_with_summary_pages
            
        except Exception as e:
            self.logger.error(f"❌ Error getting users needing reset: {str(e)}")
            return []
    
    def get_users_with_expiring_subscriptions(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Helper function to get users with subscriptions expiring soon (for monitoring/alerting).
        
        Args:
            days_ahead: Number of days to look ahead for expiring subscriptions
            
        Returns:
            List[dict]: Users with subscriptions expiring within the specified days
        """
        try:
            from datetime import timedelta
            
            now = datetime.now(timezone.utc)
            future_date = now + timedelta(days=days_ahead)
            
            expiring_query = {
                "subscription_tier": "pro",
                "subscription_status": "active",
                "subscription_end_date": {
                    "$gte": now,
                    "$lte": future_date
                }
            }
            
            expiring_users = list(collection.find(
                expiring_query,
                {"id": 1, "email": 1, "subscription_end_date": 1, "subscription_tier": 1}
            ))
            
            self.logger.info(f"📊 Found {len(expiring_users)} users with subscriptions expiring within {days_ahead} days")
            return expiring_users
            
        except Exception as e:
            self.logger.error(f"❌ Error getting expiring subscriptions: {str(e)}")
            return []

# Create global instance for easy import
background_jobs_service = BackgroundJobsService()

# Convenience functions for direct import
def reset_monthly_summaries() -> Dict[str, Any]:
    """
    Reset monthly summary page counts for all users.
    Convenience function that calls the service method.
    
    Returns:
        dict: Summary of reset operation
    """
    return background_jobs_service.reset_monthly_summaries()

def check_subscription_expiry() -> Dict[str, Any]:
    """
    Check for expired pro subscriptions and downgrade them to free tier.
    Convenience function that calls the service method.
    
    Returns:
        dict: Summary of expiry check operation
    """
    return background_jobs_service.check_subscription_expiry() 