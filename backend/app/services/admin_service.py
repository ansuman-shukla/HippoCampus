from app.core.database import collection
from app.models.user_model import userModel, userModels
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import math
import os

logger = logging.getLogger(__name__)

# Admin email addresses (in production, this should be in environment variables)
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").split(",")
ADMIN_EMAILS = [email.strip().lower() for email in ADMIN_EMAILS if email.strip()]

def is_admin_user(user_payload: dict) -> bool:
    """
    Check if the authenticated user has admin privileges.
    
    Args:
        user_payload: JWT payload from authenticated user
        
    Returns:
        bool: True if user is admin, False otherwise
    """
    try:
        user_email = user_payload.get("email", "").lower()
        
        # Check if user email is in admin list
        if user_email in ADMIN_EMAILS:
            logger.info(f"✅ Admin access granted for {user_email}")
            return True
        
        # Check for admin role in user metadata
        user_metadata = user_payload.get("user_metadata", {})
        if user_metadata.get("role") == "admin":
            logger.info(f"✅ Admin access granted via role for {user_email}")
            return True
            
        logger.warning(f"❌ Admin access denied for {user_email}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error checking admin privileges: {str(e)}")
        return False

def get_all_users_with_subscriptions(page: int = 1, page_size: int = 50) -> Tuple[List[dict], int]:
    """
    Get all users with their subscription details (paginated).
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of users per page
        
    Returns:
        Tuple[List[dict], int]: List of users and total count
    """
    logger.info(f"📊 ADMIN SERVICE: Getting all users with subscriptions")
    logger.info(f"   ├─ Page: {page}")
    logger.info(f"   └─ Page size: {page_size}")
    
    try:
        # Calculate skip for pagination
        skip = (page - 1) * page_size
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get users with pagination
        users_cursor = collection.find({}).skip(skip).limit(page_size)
        users = list(users_cursor)
        
        # Convert to user models
        user_models = userModels(users)
        
        logger.info(f"✅ Retrieved {len(user_models)} users (page {page}/{math.ceil(total_count/page_size)})")
        logger.info(f"   └─ Total users: {total_count}")
        
        return user_models, total_count
        
    except Exception as e:
        logger.error(f"❌ Error getting users with subscriptions: {str(e)}")
        raise

def get_user_subscription_detail(user_id: str) -> Optional[dict]:
    """
    Get detailed subscription information for a specific user.
    
    Args:
        user_id: The user ID
        
    Returns:
        dict: Detailed user subscription data or None if not found
    """
    logger.info(f"📊 ADMIN SERVICE: Getting detailed subscription for user {user_id}")
    
    try:
        user = collection.find_one({"id": user_id})
        if not user:
            logger.warning(f"❌ User not found: {user_id}")
            return None
            
        user_data = userModel(user)
        
        # Calculate additional admin fields
        now = datetime.now(timezone.utc)
        days_remaining = None
        is_expired = False
        
        if user_data.get("subscription_end_date"):
            end_date = user_data["subscription_end_date"]
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            if end_date > now:
                days_remaining = (end_date - now).days
            else:
                is_expired = True
                
        user_data["days_remaining"] = days_remaining
        user_data["is_expired"] = is_expired
        
        logger.info(f"✅ Detailed subscription data retrieved for user {user_id}")
        logger.info(f"   ├─ Tier: {user_data.get('subscription_tier')}")
        logger.info(f"   ├─ Status: {user_data.get('subscription_status')}")
        logger.info(f"   ├─ Days remaining: {days_remaining}")
        logger.info(f"   └─ Is expired: {is_expired}")
        
        return user_data
        
    except Exception as e:
        logger.error(f"❌ Error getting user subscription detail: {str(e)}")
        raise

def admin_upgrade_user_subscription(user_id: str, target_tier: str, extend_days: Optional[int] = None, reason: Optional[str] = None) -> dict:
    """
    Admin upgrade user subscription to specified tier.
    
    Args:
        user_id: The user ID
        target_tier: Target subscription tier
        extend_days: Number of days to extend (for pro upgrades)
        reason: Reason for the upgrade
        
    Returns:
        dict: Updated subscription data
    """
    logger.info(f"⬆️ ADMIN SERVICE: Admin upgrading user subscription")
    logger.info(f"   ├─ User ID: {user_id}")
    logger.info(f"   ├─ Target tier: {target_tier}")
    logger.info(f"   ├─ Extend days: {extend_days}")
    logger.info(f"   └─ Reason: {reason}")
    
    try:
        # Verify user exists
        user = collection.find_one({"id": user_id})
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        now = datetime.now(timezone.utc)
        update_data = {
            "subscription_tier": target_tier,
            "subscription_status": "active"
        }
        
        # Set subscription dates based on tier
        if target_tier == "pro":
            # Set start date to now
            update_data["subscription_start_date"] = now
            
            # Calculate end date
            if extend_days:
                end_date = now + timedelta(days=extend_days)
            else:
                end_date = now + timedelta(days=30)  # Default 30 days
                
            update_data["subscription_end_date"] = end_date
            
        elif target_tier == "free":
            # For downgrade, set end date to now
            update_data["subscription_end_date"] = now
            update_data["subscription_status"] = "cancelled"
        
        # Update in database
        result = collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise Exception("Failed to update subscription in database")
        
        logger.info(f"✅ Admin subscription upgrade completed")
        logger.info(f"   ├─ New tier: {target_tier}")
        logger.info(f"   ├─ Status: {update_data['subscription_status']}")
        logger.info(f"   └─ End date: {update_data.get('subscription_end_date', 'N/A')}")
        
        return {
            "user_id": user_id,
            "previous_tier": user.get("subscription_tier", "free"),
            "new_tier": target_tier,
            "subscription_status": update_data["subscription_status"],
            "subscription_end_date": update_data.get("subscription_end_date"),
            "reason": reason,
            "updated_by": "admin",
            "updated_at": now
        }
        
    except Exception as e:
        logger.error(f"❌ Error upgrading user subscription: {str(e)}")
        raise

def admin_downgrade_user_subscription(user_id: str, reason: Optional[str] = None) -> dict:
    """
    Admin downgrade user subscription to free tier.
    
    Args:
        user_id: The user ID
        reason: Reason for the downgrade
        
    Returns:
        dict: Updated subscription data
    """
    logger.info(f"⬇️ ADMIN SERVICE: Admin downgrading user subscription")
    logger.info(f"   ├─ User ID: {user_id}")
    logger.info(f"   └─ Reason: {reason}")
    
    try:
        # Verify user exists
        user = collection.find_one({"id": user_id})
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        now = datetime.now(timezone.utc)
        update_data = {
            "subscription_tier": "free",
            "subscription_status": "cancelled",
            "subscription_end_date": now
        }
        
        # Update in database
        result = collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise Exception("Failed to update subscription in database")
        
        logger.info(f"✅ Admin subscription downgrade completed")
        logger.info(f"   ├─ New tier: free")
        logger.info(f"   ├─ Status: cancelled")
        logger.info(f"   └─ End date: {now}")
        
        return {
            "user_id": user_id,
            "previous_tier": user.get("subscription_tier", "pro"),
            "new_tier": "free",
            "subscription_status": "cancelled",
            "subscription_end_date": now,
            "reason": reason,
            "updated_by": "admin",
            "updated_at": now
        }
        
    except Exception as e:
        logger.error(f"❌ Error downgrading user subscription: {str(e)}")
        raise

def admin_extend_user_subscription(user_id: str, extend_days: int, reason: Optional[str] = None) -> dict:
    """
    Admin extend user subscription end date.
    
    Args:
        user_id: The user ID
        extend_days: Number of days to extend
        reason: Reason for the extension
        
    Returns:
        dict: Updated subscription data
    """
    logger.info(f"📅 ADMIN SERVICE: Admin extending user subscription")
    logger.info(f"   ├─ User ID: {user_id}")
    logger.info(f"   ├─ Extend days: {extend_days}")
    logger.info(f"   └─ Reason: {reason}")
    
    try:
        # Verify user exists
        user = collection.find_one({"id": user_id})
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        current_end_date = user.get("subscription_end_date")
        now = datetime.now(timezone.utc)
        
        # Calculate new end date
        if current_end_date:
            if isinstance(current_end_date, str):
                current_end_date = datetime.fromisoformat(current_end_date.replace('Z', '+00:00'))
            # Extend from current end date (even if in the past)
            new_end_date = current_end_date + timedelta(days=extend_days)
        else:
            # No existing end date, extend from now
            new_end_date = now + timedelta(days=extend_days)
        
        # Update subscription status to active if extending
        update_data = {
            "subscription_end_date": new_end_date,
            "subscription_status": "active"
        }
        
        # Update in database
        result = collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise Exception("Failed to update subscription in database")
        
        logger.info(f"✅ Admin subscription extension completed")
        logger.info(f"   ├─ Previous end date: {current_end_date}")
        logger.info(f"   ├─ New end date: {new_end_date}")
        logger.info(f"   └─ Days extended: {extend_days}")
        
        return {
            "user_id": user_id,
            "previous_end_date": current_end_date,
            "new_end_date": new_end_date,
            "days_extended": extend_days,
            "subscription_status": "active",
            "reason": reason,
            "updated_by": "admin",
            "updated_at": now
        }
        
    except Exception as e:
        logger.error(f"❌ Error extending user subscription: {str(e)}")
        raise

def admin_reset_user_usage(user_id: str, reset_memories: bool = False, reset_monthly_summaries: bool = True, reason: Optional[str] = None) -> dict:
    """
    Admin reset user usage counters.
    
    Args:
        user_id: The user ID
        reset_memories: Whether to reset total memories count
        reset_monthly_summaries: Whether to reset monthly summary pages
        reason: Reason for the reset
        
    Returns:
        dict: Reset operation details
    """
    logger.info(f"🔄 ADMIN SERVICE: Admin resetting user usage")
    logger.info(f"   ├─ User ID: {user_id}")
    logger.info(f"   ├─ Reset memories: {reset_memories}")
    logger.info(f"   ├─ Reset monthly summaries: {reset_monthly_summaries}")
    logger.info(f"   └─ Reason: {reason}")
    
    try:
        # Verify user exists
        user = collection.find_one({"id": user_id})
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Build update data
        update_data = {}
        previous_values = {}
        
        if reset_memories:
            previous_values["total_memories_saved"] = user.get("total_memories_saved", 0)
            update_data["total_memories_saved"] = 0
        
        if reset_monthly_summaries:
            previous_values["monthly_summary_pages_used"] = user.get("monthly_summary_pages_used", 0)
            update_data["monthly_summary_pages_used"] = 0
            
            # Update reset date
            now = datetime.now(timezone.utc)
            update_data["monthly_summary_reset_date"] = datetime(now.year, now.month, 1)
        
        if not update_data:
            raise ValueError("No reset options specified")
        
        # Update in database
        result = collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise Exception("Failed to update usage counters in database")
        
        logger.info(f"✅ Admin usage reset completed")
        for key, value in previous_values.items():
            logger.info(f"   ├─ {key}: {value} → 0")
        
        return {
            "user_id": user_id,
            "reset_memories": reset_memories,
            "reset_monthly_summaries": reset_monthly_summaries,
            "previous_values": previous_values,
            "new_values": {k: 0 for k in previous_values.keys()},
            "reason": reason,
            "updated_by": "admin",
            "updated_at": datetime.now(timezone.utc)
        }
        
    except Exception as e:
        logger.error(f"❌ Error resetting user usage: {str(e)}")
        raise

def get_admin_analytics() -> dict:
    """
    Get subscription analytics and metrics for admin dashboard.
    
    Returns:
        dict: Analytics data including user counts, conversion rates, etc.
    """
    logger.info(f"📊 ADMIN SERVICE: Generating admin analytics")
    
    try:
        # Get all users
        all_users = list(collection.find({}))
        total_users = len(all_users)
        
        if total_users == 0:
            return {
                "total_users": 0,
                "free_users": 0,
                "pro_users": 0,
                "active_subscriptions": 0,
                "expired_subscriptions": 0,
                "cancelled_subscriptions": 0,
                "total_memories_saved": 0,
                "total_summary_pages_used": 0,
                "average_memories_per_user": 0.0,
                "conversion_rate": 0.0,
                "revenue_estimate": 0.0
            }
        
        # Initialize counters
        free_users = 0
        pro_users = 0
        active_subscriptions = 0
        expired_subscriptions = 0
        cancelled_subscriptions = 0
        total_memories = 0
        total_summary_pages = 0
        
        now = datetime.now(timezone.utc)
        
        for user in all_users:
            # Count subscription tiers
            tier = user.get("subscription_tier", "free")
            if tier == "free":
                free_users += 1
            elif tier == "pro":
                pro_users += 1
            
            # Count subscription statuses
            status = user.get("subscription_status", "active")
            end_date = user.get("subscription_end_date")
            
            # Check if subscription is actually expired
            if end_date:
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
                if end_date <= now:
                    expired_subscriptions += 1
                elif status == "active":
                    active_subscriptions += 1
                elif status == "cancelled":
                    cancelled_subscriptions += 1
            elif status == "active":
                active_subscriptions += 1
            elif status == "cancelled":
                cancelled_subscriptions += 1
            
            # Sum usage statistics
            total_memories += user.get("total_memories_saved", 0)
            total_summary_pages += user.get("monthly_summary_pages_used", 0)
        
        # Calculate metrics
        average_memories = total_memories / total_users if total_users > 0 else 0.0
        conversion_rate = (pro_users / total_users * 100) if total_users > 0 else 0.0
        revenue_estimate = pro_users * 8.0  # $8 per pro user per month
        
        analytics = {
            "total_users": total_users,
            "free_users": free_users,
            "pro_users": pro_users,
            "active_subscriptions": active_subscriptions,
            "expired_subscriptions": expired_subscriptions,
            "cancelled_subscriptions": cancelled_subscriptions,
            "total_memories_saved": total_memories,
            "total_summary_pages_used": total_summary_pages,
            "average_memories_per_user": round(average_memories, 2),
            "conversion_rate": round(conversion_rate, 2),
            "revenue_estimate": round(revenue_estimate, 2)
        }
        
        logger.info(f"✅ Admin analytics generated successfully")
        logger.info(f"   ├─ Total users: {total_users}")
        logger.info(f"   ├─ Free: {free_users}, Pro: {pro_users}")
        logger.info(f"   ├─ Active: {active_subscriptions}, Expired: {expired_subscriptions}")
        logger.info(f"   ├─ Conversion rate: {conversion_rate:.2f}%")
        logger.info(f"   └─ Revenue estimate: ${revenue_estimate:.2f}")
        
        return analytics
        
    except Exception as e:
        logger.error(f"❌ Error generating admin analytics: {str(e)}")
        raise 