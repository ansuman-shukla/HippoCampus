from app.core.database import collection
from app.services.subscription_logging_service import subscription_logger
from datetime import datetime, timezone, timedelta
import logging
import math

logger = logging.getLogger(__name__)

# Subscription tier limits
TIER_LIMITS = {
    "free": {
        "memories": 100,
        "monthly_summary_pages": 5
    },
    "pro": {
        "memories": -1,  # -1 means unlimited
        "monthly_summary_pages": 100
    }
}

# Grace period constants
GRACE_PERIOD_DAYS = 7  # 7 days grace period after subscription expires
GRACE_PERIOD_LIMITS = {
    "memories": 5,  # Allow 5 more memories during grace period
    "monthly_summary_pages": 1  # Allow 1 more summary page during grace period
}

def get_user_subscription(user_id: str) -> dict:
    """
    Get user's subscription information from the database.
    
    Args:
        user_id: The user ID
        
    Returns:
        dict: User subscription data or None if user not found
    """
    logger.info(f"📊 SUBSCRIPTION SERVICE: Getting subscription for user {user_id}")
    
    try:
        user = collection.find_one({"id": user_id})
        if not user:
            logger.warning(f"❌ User not found: {user_id}")
            return None
            
        subscription_data = {
            "user_id": user_id,
            "subscription_tier": user.get("subscription_tier", "free"),
            "subscription_status": user.get("subscription_status", "active"),
            "subscription_start_date": user.get("subscription_start_date"),
            "subscription_end_date": user.get("subscription_end_date"),
            "total_memories_saved": user.get("total_memories_saved", 0),
            "monthly_summary_pages_used": user.get("monthly_summary_pages_used", 0),
            "monthly_summary_reset_date": user.get("monthly_summary_reset_date")
        }
        
        logger.info(f"✅ Subscription data retrieved for user {user_id}")
        logger.info(f"   ├─ Tier: {subscription_data['subscription_tier']}")
        logger.info(f"   ├─ Status: {subscription_data['subscription_status']}")
        logger.info(f"   ├─ Memories: {subscription_data['total_memories_saved']}")
        logger.info(f"   └─ Monthly pages: {subscription_data['monthly_summary_pages_used']}")
        
        return subscription_data
        
    except Exception as e:
        logger.error(f"❌ Error getting subscription for user {user_id}: {str(e)}")
        raise


def check_memory_limit(user_id: str) -> bool:
    """
    Check if user can save another memory based on their subscription tier and grace period.
    
    Args:
        user_id: The user ID
        
    Returns:
        bool: True if user can save memory, False if at limit
    """
    logger.info(f"🔍 SUBSCRIPTION SERVICE: Checking memory limit for user {user_id}")
    
    try:
        # Get enhanced status with grace period consideration
        status = get_subscription_status_with_grace(user_id)
        if not status:
            logger.warning(f"❌ Cannot check memory limit - user not found: {user_id}")
            return False
            
        effective_tier = status["effective_tier"]
        current_count = status["total_memories_saved"]
        
        # Handle different effective tiers
        if effective_tier == "pro":
            logger.info(f"✅ Pro user has unlimited memory access")
            return True
        elif effective_tier == "grace":
            # Check grace period limits
            can_save = check_grace_period_limits(user_id, "memory")
            logger.info(f"🔄 Grace period memory check: {can_save}")
            return can_save
        else:  # free tier
            tier_limit = TIER_LIMITS["free"]["memories"]
            can_save = current_count < tier_limit
            
            logger.info(f"📊 Memory limit check for free tier:")
            logger.info(f"   ├─ Current count: {current_count}")
            logger.info(f"   ├─ Tier limit: {tier_limit}")
            logger.info(f"   └─ Can save: {can_save}")
            
            return can_save
        
    except Exception as e:
        logger.error(f"❌ Error checking memory limit for user {user_id}: {str(e)}")
        return False


def check_summary_limit(user_id: str, pages_requested: int) -> bool:
    """
    Check if user can generate summary pages based on their subscription tier and grace period.
    
    Args:
        user_id: The user ID
        pages_requested: Number of pages requested for summarization
        
    Returns:
        bool: True if user can generate summary, False if would exceed limit
    """
    logger.info(f"🔍 SUBSCRIPTION SERVICE: Checking summary limit for user {user_id}")
    logger.info(f"   └─ Pages requested: {pages_requested}")
    
    try:
        # Get enhanced status with grace period consideration
        status = get_subscription_status_with_grace(user_id)
        if not status:
            logger.warning(f"❌ Cannot check summary limit - user not found: {user_id}")
            return False
            
        effective_tier = status["effective_tier"]
        current_pages = status["monthly_summary_pages_used"]
        
        # Handle different effective tiers
        if effective_tier == "pro":
            tier_limit = TIER_LIMITS["pro"]["monthly_summary_pages"]
            new_total = current_pages + pages_requested
            can_generate = new_total <= tier_limit
            
            logger.info(f"📊 Summary limit check for pro tier:")
            logger.info(f"   ├─ Current pages: {current_pages}")
            logger.info(f"   ├─ Pages requested: {pages_requested}")
            logger.info(f"   ├─ New total would be: {new_total}")
            logger.info(f"   ├─ Tier limit: {tier_limit}")
            logger.info(f"   └─ Can generate: {can_generate}")
            
            return can_generate
        elif effective_tier == "grace":
            # Check grace period limits
            can_generate = check_grace_period_limits(user_id, "summary", pages_requested)
            logger.info(f"🔄 Grace period summary check: {can_generate}")
            return can_generate
        else:  # free tier
            tier_limit = TIER_LIMITS["free"]["monthly_summary_pages"]
            new_total = current_pages + pages_requested
            can_generate = new_total <= tier_limit
            
            logger.info(f"📊 Summary limit check for free tier:")
            logger.info(f"   ├─ Current pages: {current_pages}")
            logger.info(f"   ├─ Pages requested: {pages_requested}")
            logger.info(f"   ├─ New total would be: {new_total}")
            logger.info(f"   ├─ Tier limit: {tier_limit}")
            logger.info(f"   └─ Can generate: {can_generate}")
            
            return can_generate
        
    except Exception as e:
        logger.error(f"❌ Error checking summary limit for user {user_id}: {str(e)}")
        return False


def increment_memory_count(user_id: str) -> dict:
    """
    Increment user's total memory count after successful save.
    
    Args:
        user_id: The user ID
        
    Returns:
        dict: Updated subscription data
    """
    logger.info(f"📈 SUBSCRIPTION SERVICE: Incrementing memory count for user {user_id}")
    
    try:
        # First verify user exists and get current count
        subscription_data = get_user_subscription(user_id)
        if not subscription_data:
            raise ValueError(f"User not found: {user_id}")
            
        current_count = subscription_data["total_memories_saved"]
        new_count = current_count + 1
        
        # Update in database
        result = collection.update_one(
            {"id": user_id},
            {"$set": {"total_memories_saved": new_count}}
        )
        
        if result.modified_count == 0:
            logger.warning(f"⚠️ No documents modified when incrementing memory count")
            
        logger.info(f"✅ Memory count incremented:")
        logger.info(f"   ├─ Previous count: {current_count}")
        logger.info(f"   └─ New count: {new_count}")
        
        # Return updated subscription data
        subscription_data["total_memories_saved"] = new_count
        return subscription_data
        
    except Exception as e:
        logger.error(f"❌ Error incrementing memory count for user {user_id}: {str(e)}")
        raise


def increment_summary_pages(user_id: str, pages: int) -> dict:
    """
    Increment user's monthly summary pages used.
    
    Args:
        user_id: The user ID
        pages: Number of pages to add
        
    Returns:
        dict: Updated subscription data
    """
    logger.info(f"📈 SUBSCRIPTION SERVICE: Incrementing summary pages for user {user_id}")
    logger.info(f"   └─ Pages to add: {pages}")
    
    try:
        # First verify user exists and get current count
        subscription_data = get_user_subscription(user_id)
        if not subscription_data:
            raise ValueError(f"User not found: {user_id}")
            
        current_pages = subscription_data["monthly_summary_pages_used"]
        new_pages = current_pages + pages
        
        # Update in database
        result = collection.update_one(
            {"id": user_id},
            {"$set": {"monthly_summary_pages_used": new_pages}}
        )
        
        if result.modified_count == 0:
            logger.warning(f"⚠️ No documents modified when incrementing summary pages")
            
        logger.info(f"✅ Summary pages incremented:")
        logger.info(f"   ├─ Previous pages: {current_pages}")
        logger.info(f"   └─ New pages: {new_pages}")
        
        # Return updated subscription data
        subscription_data["monthly_summary_pages_used"] = new_pages
        return subscription_data
        
    except Exception as e:
        logger.error(f"❌ Error incrementing summary pages for user {user_id}: {str(e)}")
        raise


def reset_monthly_summaries() -> dict:
    """
    Reset monthly summary page counts for all users (called by monthly cron job).
    
    Returns:
        dict: Summary of reset operation
    """
    logger.info(f"🔄 SUBSCRIPTION SERVICE: Resetting monthly summary counts for all users")
    
    try:
        # Calculate new reset date (first day of current month)
        now = datetime.utcnow()
        new_reset_date = datetime(now.year, now.month, 1)
        
        # Reset all users' monthly summary pages
        result = collection.update_many(
            {},  # Empty filter to update all documents
            {
                "$set": {
                    "monthly_summary_pages_used": 0,
                    "monthly_summary_reset_date": new_reset_date
                }
            }
        )
        
        logger.info(f"✅ Monthly summary reset completed:")
        logger.info(f"   ├─ Users updated: {result.modified_count}")
        logger.info(f"   └─ Reset date: {new_reset_date}")
        
        return {
            "users_updated": result.modified_count,
            "reset_date": new_reset_date,
            "operation_time": now
        }
        
    except Exception as e:
        logger.error(f"❌ Error resetting monthly summaries: {str(e)}")
        raise


def estimate_content_pages(content: str) -> int:
    """
    Estimate the number of pages in content for summary limits.
    Based on average 500 words per page, ~3000 characters per page.
    
    Args:
        content: The content to estimate
        
    Returns:
        int: Estimated number of pages (minimum 1)
    """
    if not content or content.strip() == "":
        return 1  # Minimum 1 page for any content
        
    # Rough estimation: 3000 characters per page
    # This accounts for typical document formatting
    characters_per_page = 3000
    content_length = len(content.strip())
    
    # Calculate pages and round up (any partial page counts as full page)
    estimated_pages = math.ceil(content_length / characters_per_page)
    
    # Ensure minimum 1 page
    estimated_pages = max(1, estimated_pages)
    
    logger.info(f"📏 CONTENT ESTIMATION:")
    logger.info(f"   ├─ Content length: {content_length} characters")
    logger.info(f"   ├─ Characters per page: {characters_per_page}")
    logger.info(f"   └─ Estimated pages: {estimated_pages}")
    
    return estimated_pages 


def get_subscription_status_with_grace(user_id: str) -> dict:
    """
    Get user's subscription status including grace period consideration.
    
    Args:
        user_id: The user ID
        
    Returns:
        dict: Enhanced subscription data with grace period information
    """
    logger.info(f"🔍 SUBSCRIPTION SERVICE: Checking subscription status with grace for user {user_id}")
    
    try:
        subscription_data = get_user_subscription(user_id)
        if not subscription_data:
            return None
            
        now = datetime.now(timezone.utc)
        tier = subscription_data["subscription_tier"]
        status = subscription_data["subscription_status"]
        end_date = subscription_data["subscription_end_date"]
        
        # Enhanced status information
        enhanced_status = {
            **subscription_data,
            "is_active": False,
            "is_expired": False,
            "is_in_grace_period": False,
            "grace_period_end": None,
            "days_remaining": None,
            "grace_days_remaining": None,
            "effective_tier": tier,  # What tier user should be treated as
            "grace_period_usage": {
                "memories_used": 0,
                "summary_pages_used": 0
            }
        }
        
        if tier == "free":
            enhanced_status["is_active"] = (status == "active")
            enhanced_status["effective_tier"] = "free"
        elif tier == "pro" and end_date:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
            grace_period_end = end_date + timedelta(days=GRACE_PERIOD_DAYS)
            enhanced_status["grace_period_end"] = grace_period_end
            
            if now <= end_date:
                # Subscription is still active
                enhanced_status["is_active"] = True
                enhanced_status["days_remaining"] = (end_date - now).days
                enhanced_status["effective_tier"] = "pro"
            elif now <= grace_period_end:
                # In grace period
                enhanced_status["is_expired"] = True
                enhanced_status["is_in_grace_period"] = True
                enhanced_status["grace_days_remaining"] = (grace_period_end - now).days
                enhanced_status["effective_tier"] = "grace"
                
                # Get grace period usage
                grace_usage = _get_grace_period_usage(user_id, end_date)
                enhanced_status["grace_period_usage"] = grace_usage
            else:
                # Fully expired
                enhanced_status["is_expired"] = True
                enhanced_status["effective_tier"] = "free"
                
        logger.info(f"✅ Enhanced subscription status for user {user_id}:")
        logger.info(f"   ├─ Tier: {tier} → Effective: {enhanced_status['effective_tier']}")
        logger.info(f"   ├─ Active: {enhanced_status['is_active']}")
        logger.info(f"   ├─ Expired: {enhanced_status['is_expired']}")
        logger.info(f"   ├─ In grace: {enhanced_status['is_in_grace_period']}")
        logger.info(f"   └─ Grace days remaining: {enhanced_status['grace_days_remaining']}")
        
        return enhanced_status
        
    except Exception as e:
        logger.error(f"❌ Error checking subscription status with grace for user {user_id}: {str(e)}")
        raise


def _get_grace_period_usage(user_id: str, subscription_end_date: datetime) -> dict:
    """
    Get usage statistics during the grace period for a user.
    
    Args:
        user_id: The user ID
        subscription_end_date: When the subscription officially ended
        
    Returns:
        dict: Grace period usage statistics
    """
    try:
        # For now, we'll implement a simple approach
        # In a real system, you'd track grace period specific usage
        # This is a placeholder that assumes grace usage is minimal
        
        logger.info(f"📊 Getting grace period usage for user {user_id}")
        
        # This would typically query a separate grace_period_usage table
        # For this implementation, we'll return default values
        grace_usage = {
            "memories_used": 0,  # Grace period memories used
            "summary_pages_used": 0,  # Grace period summary pages used
            "grace_period_start": subscription_end_date
        }
        
        logger.info(f"   └─ Grace usage: {grace_usage}")
        return grace_usage
        
    except Exception as e:
        logger.error(f"❌ Error getting grace period usage: {str(e)}")
        return {"memories_used": 0, "summary_pages_used": 0}


def check_grace_period_limits(user_id: str, operation_type: str, pages_requested: int = 1) -> bool:
    """
    Check if user can perform an operation during grace period.
    
    Args:
        user_id: The user ID
        operation_type: Type of operation ('memory' or 'summary')
        pages_requested: Number of pages for summary operations
        
    Returns:
        bool: True if operation is allowed in grace period
    """
    logger.info(f"🔍 GRACE PERIOD: Checking limits for user {user_id}")
    logger.info(f"   ├─ Operation: {operation_type}")
    logger.info(f"   └─ Pages requested: {pages_requested}")
    
    try:
        status = get_subscription_status_with_grace(user_id)
        if not status or not status["is_in_grace_period"]:
            logger.info(f"❌ User not in grace period")
            return False
            
        grace_usage = status["grace_period_usage"]
        
        if operation_type == "memory":
            current_usage = grace_usage["memories_used"]
            limit = GRACE_PERIOD_LIMITS["memories"]
            can_perform = current_usage < limit
            
            logger.info(f"📊 Grace period memory check:")
            logger.info(f"   ├─ Current usage: {current_usage}")
            logger.info(f"   ├─ Limit: {limit}")
            logger.info(f"   └─ Can perform: {can_perform}")
            
        elif operation_type == "summary":
            current_usage = grace_usage["summary_pages_used"]
            limit = GRACE_PERIOD_LIMITS["monthly_summary_pages"]
            new_total = current_usage + pages_requested
            can_perform = new_total <= limit
            
            logger.info(f"📊 Grace period summary check:")
            logger.info(f"   ├─ Current usage: {current_usage}")
            logger.info(f"   ├─ Pages requested: {pages_requested}")
            logger.info(f"   ├─ New total: {new_total}")
            logger.info(f"   ├─ Limit: {limit}")
            logger.info(f"   └─ Can perform: {can_perform}")
            
        else:
            logger.warning(f"❌ Unknown operation type: {operation_type}")
            return False
            
        return can_perform
        
    except Exception as e:
        logger.error(f"❌ Error checking grace period limits: {str(e)}")
        return False


def reactivate_subscription(user_id: str, payment_method: str = "manual") -> dict:
    """
    Reactivate an expired or cancelled subscription.
    
    Args:
        user_id: The user ID
        payment_method: Payment method used for reactivation
        
    Returns:
        dict: Reactivation result with new subscription details
    """
    logger.info(f"🔄 SUBSCRIPTION SERVICE: Reactivating subscription for user {user_id}")
    logger.info(f"   └─ Payment method: {payment_method}")
    
    try:
        # Get current subscription status
        status = get_subscription_status_with_grace(user_id)
        if not status:
            raise ValueError(f"User not found: {user_id}")
            
        current_tier = status["subscription_tier"]
        current_status = status["subscription_status"]
        
        # Determine if reactivation is allowed
        can_reactivate = (
            current_tier == "pro" and 
            (current_status in ["expired", "cancelled"] or status["is_in_grace_period"])
        )
        
        if not can_reactivate:
            raise ValueError(f"User subscription cannot be reactivated. Current tier: {current_tier}, status: {current_status}")
        
        # Calculate new subscription dates
        now = datetime.now(timezone.utc)
        new_end_date = now + timedelta(days=30)  # Standard 30-day subscription
        
        # Reset monthly usage if we're in a new month
        update_data = {
            "subscription_status": "active",
            "subscription_start_date": now,
            "subscription_end_date": new_end_date
        }
        
        # Check if we need to reset monthly usage (new month)
        monthly_reset_date = status.get("monthly_summary_reset_date")
        if monthly_reset_date:
            if isinstance(monthly_reset_date, str):
                monthly_reset_date = datetime.fromisoformat(monthly_reset_date.replace('Z', '+00:00'))
            
            current_month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
            if monthly_reset_date < current_month_start:
                update_data["monthly_summary_pages_used"] = 0
                update_data["monthly_summary_reset_date"] = current_month_start
                logger.info(f"   └─ Resetting monthly usage for new month")
        
        # Update in database
        result = collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise Exception("Failed to update subscription in database")
        
        reactivation_result = {
            "user_id": user_id,
            "previous_status": current_status,
            "new_status": "active",
            "subscription_tier": "pro",
            "new_start_date": now,
            "new_end_date": new_end_date,
            "payment_method": payment_method,
            "reactivated_at": now,
            "was_in_grace_period": status["is_in_grace_period"]
        }
        
        logger.info(f"✅ Subscription reactivated successfully:")
        logger.info(f"   ├─ Previous status: {current_status}")
        logger.info(f"   ├─ New end date: {new_end_date}")
        logger.info(f"   └─ Was in grace period: {status['is_in_grace_period']}")
        
        # Log reactivation event for analytics  
        subscription_logger.log_reactivation_event(
            user_id=user_id,
            previous_status=current_status,
            was_in_grace=status['is_in_grace_period'],
            payment_method=payment_method
        )
        
        return reactivation_result
        
    except Exception as e:
        logger.error(f"❌ Error reactivating subscription for user {user_id}: {str(e)}")
        raise


def handle_timezone_safe_operations(target_date: datetime, user_timezone: str = None) -> datetime:
    """
    Handle timezone-safe operations for subscription dates.
    
    Args:
        target_date: The target date to process
        user_timezone: User's timezone (optional, defaults to UTC)
        
    Returns:
        datetime: Timezone-aware datetime in UTC
    """
    logger.info(f"🌍 TIMEZONE HANDLER: Processing date {target_date}")
    logger.info(f"   └─ User timezone: {user_timezone or 'UTC'}")
    
    try:
        # Always work in UTC for consistency
        if target_date.tzinfo is None:
            # Naive datetime, assume UTC
            result = target_date.replace(tzinfo=timezone.utc)
            logger.info(f"   └─ Added UTC timezone to naive datetime")
        elif target_date.tzinfo != timezone.utc:
            # Convert to UTC
            result = target_date.astimezone(timezone.utc)
            logger.info(f"   └─ Converted to UTC from {target_date.tzinfo}")
        else:
            # Already UTC
            result = target_date
            logger.info(f"   └─ Already in UTC")
        
        logger.info(f"✅ Timezone processing result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error handling timezone operations: {str(e)}")
        # Fallback to current UTC time
        return datetime.now(timezone.utc)


def handle_leap_year_edge_cases(year: int, month: int, day: int) -> datetime:
    """
    Handle leap year edge cases when calculating subscription dates.
    
    Args:
        year: Target year
        month: Target month
        day: Target day
        
    Returns:
        datetime: Valid datetime handling leap year edge cases
    """
    logger.info(f"📅 LEAP YEAR HANDLER: Processing date {year}-{month:02d}-{day:02d}")
    
    try:
        # Handle February 29th edge cases
        if month == 2 and day == 29:
            # Check if it's a leap year
            is_leap_year = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
            
            if not is_leap_year:
                # Not a leap year, use February 28th
                logger.info(f"   └─ {year} is not a leap year, using Feb 28th instead of Feb 29th")
                day = 28
        
        # Handle other month-end edge cases
        days_in_month = {
            1: 31, 2: 29 if ((year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)) else 28,
            3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
        }
        
        max_day = days_in_month.get(month, 31)
        if day > max_day:
            logger.info(f"   └─ Day {day} exceeds max for month {month}, using {max_day}")
            day = max_day
        
        result = datetime(year, month, day, tzinfo=timezone.utc)
        logger.info(f"✅ Leap year safe date: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error handling leap year edge case: {str(e)}")
        # Fallback to first day of the month
        return datetime(year, month, 1, tzinfo=timezone.utc)


def get_users_requiring_grace_period_processing() -> list:
    """
    Get users who are in grace period and need processing.
    
    Returns:
        list: Users currently in grace period
    """
    logger.info(f"🔍 GRACE PERIOD: Finding users requiring grace period processing")
    
    try:
        now = datetime.now(timezone.utc)
        grace_cutoff = now - timedelta(days=GRACE_PERIOD_DAYS)
        
        # Find pro users who expired within grace period window
        grace_period_query = {
            "subscription_tier": "pro",
            "subscription_status": {"$in": ["expired", "active"]},
            "subscription_end_date": {
                "$gte": grace_cutoff,
                "$lte": now
            }
        }
        
        users_in_grace = list(collection.find(grace_period_query))
        
        logger.info(f"📊 Found {len(users_in_grace)} users in grace period")
        
        return users_in_grace
        
    except Exception as e:
        logger.error(f"❌ Error finding users in grace period: {str(e)}")
        return [] 