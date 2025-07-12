from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.services.subscription_service import (
    get_user_subscription, 
    check_memory_limit, 
    check_summary_limit,
    TIER_LIMITS
)
from app.schema.subscription_schema import (
    SubscriptionStatus, 
    SubscriptionUpgrade, 
    UsageResponse,
    SubscriptionTier,
    SubscriptionStatusEnum
)
from app.core.database import collection
from app.services.subscription_logging_service import subscription_logger
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/subscription", 
    tags=["subscription"],
    responses={
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)

@router.get(
    "/status", 
    response_model=SubscriptionStatus,
    summary="Get Subscription Status",
    description="""
    Get comprehensive subscription information for the authenticated user.
    
    This endpoint returns detailed information about the user's current subscription including:
    - Subscription tier (free or pro)
    - Subscription status (active, expired, cancelled)
    - Usage statistics (memories saved, summary pages used)
    - Important dates (start, end, reset dates)
    
    **Authentication Required**: User must be logged in via session cookies or authorization headers.
    """,
    responses={
        200: {
            "description": "Successfully retrieved subscription status",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "user_12345",
                        "subscription_tier": "free",
                        "subscription_status": "active",
                        "subscription_start_date": "2024-01-01T00:00:00Z",
                        "subscription_end_date": None,
                        "total_memories_saved": 25,
                        "monthly_summary_pages_used": 3,
                        "monthly_summary_reset_date": "2024-01-01T00:00:00Z"
                    }
                }
            }
        },
        404: {"description": "User not found in the system"}
    }
)
async def get_subscription_status(request: Request):
    """
    Get current subscription information for the authenticated user.
    
    Returns comprehensive subscription details including tier, status, usage, and dates.
    """
    logger.info(f"📊 SUBSCRIPTION STATUS: Getting status for user")
    logger.info(f"   └─ User ID: {request.state.user_id}")
    
    try:
        subscription_data = get_user_subscription(request.state.user_id)
        
        if not subscription_data:
            logger.error(f"❌ User not found: {request.state.user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        response = SubscriptionStatus(
            user_id=subscription_data["user_id"],
            subscription_tier=subscription_data["subscription_tier"],
            subscription_status=subscription_data["subscription_status"],
            subscription_start_date=subscription_data["subscription_start_date"],
            subscription_end_date=subscription_data["subscription_end_date"],
            total_memories_saved=subscription_data["total_memories_saved"],
            monthly_summary_pages_used=subscription_data["monthly_summary_pages_used"],
            monthly_summary_reset_date=subscription_data["monthly_summary_reset_date"]
        )
        
        logger.info(f"✅ Subscription status retrieved successfully")
        logger.info(f"   ├─ Tier: {response.subscription_tier}")
        logger.info(f"   ├─ Status: {response.subscription_status}")
        logger.info(f"   └─ Memories: {response.total_memories_saved}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post(
    "/upgrade",
    summary="Upgrade to Pro Subscription",
    description="""
    Upgrade user subscription from Free to Pro tier with payment processing simulation.
    
    This endpoint handles the complete upgrade flow:
    - Validates user eligibility for upgrade
    - Processes payment (currently simulated)
    - Updates subscription tier and dates
    - Logs upgrade event for analytics
    
    **Pro Tier Benefits**:
    - Unlimited memory saves (vs 100 for free)
    - 100 summary pages per month (vs 5 for free)
    - Priority support
    - Advanced analytics
    
    **Payment**: Currently simulated - in production this would integrate with Stripe/PayPal.
    
    **Authentication Required**: User must be logged in.
    """,
    responses={
        200: {
            "description": "Successfully upgraded to Pro subscription",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Subscription upgraded to Pro successfully",
                        "subscription": {
                            "tier": "pro",
                            "status": "active",
                            "start_date": "2024-01-15T10:30:00Z",
                            "end_date": "2024-02-15T10:30:00Z",
                            "billing_email": "user@example.com"
                        },
                        "benefits": {
                            "unlimited_memories": True,
                            "monthly_summary_pages": 100,
                            "ai_dashboard_access": True
                        }
                    }
                }
            }
        },
        400: {"description": "User already has Pro subscription or invalid request"},
        402: {"description": "Payment processing failed"},
        404: {"description": "User not found in the system"}
    }
)
async def upgrade_subscription(
    upgrade_request: SubscriptionUpgrade,
    request: Request
):
    """
    Upgrade user subscription to Pro tier with payment simulation.
    
    Processes subscription upgrade including payment validation and tier change.
    """
    logger.info(f"⬆️ SUBSCRIPTION UPGRADE: Processing upgrade request")
    logger.info(f"   ├─ User ID: {request.state.user_id}")
    logger.info(f"   ├─ Target tier: {upgrade_request.target_tier}")
    logger.info(f"   └─ Payment method: {upgrade_request.payment_method_id}")
    
    try:
        # Validate user exists and get current subscription
        current_subscription = get_user_subscription(request.state.user_id)
        if not current_subscription:
            logger.error(f"❌ User not found: {request.state.user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is already on Pro tier
        if current_subscription["subscription_tier"] == "pro":
            logger.warning(f"⚠️ User already has Pro subscription")
            raise HTTPException(status_code=400, detail="User already has Pro subscription")
        
        # Simulate payment processing
        logger.info(f"💳 PAYMENT SIMULATION: Processing payment")
        
        # In a real implementation, this would integrate with Stripe, PayPal, etc.
        # For now, we simulate a successful payment
        payment_success = True
        
        if not payment_success:
            logger.error(f"❌ Payment simulation failed")
            raise HTTPException(status_code=402, detail="Payment processing failed")
        
        # Set subscription dates
        now = datetime.now(timezone.utc)
        start_date = now
        end_date = now + timedelta(days=30)  # 30-day subscription
        
        # Update user subscription in database
        update_data = {
            "subscription_tier": "pro",
            "subscription_status": "active",
            "subscription_start_date": start_date,
            "subscription_end_date": end_date
        }
        
        result = collection.update_one(
            {"id": request.state.user_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            logger.error(f"❌ Failed to update subscription in database")
            raise HTTPException(status_code=500, detail="Failed to update subscription")
        
        logger.info(f"✅ Subscription upgraded successfully")
        logger.info(f"   ├─ New tier: pro")
        logger.info(f"   ├─ Start date: {start_date.isoformat()}")
        logger.info(f"   └─ End date: {end_date.isoformat()}")
        
        # Log subscription upgrade event for analytics
        subscription_logger.log_upgrade_event(
            user_id=request.state.user_id,
            previous_tier=current_subscription["subscription_tier"],
            new_tier="pro",
            method="user",
            payment_method=upgrade_request.payment_method_id,
            amount=8.0  # $8/month Pro plan
        )
        
        return {
            "success": True,
            "message": "Subscription upgraded to Pro successfully",
            "subscription": {
                "tier": "pro",
                "status": "active",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "billing_email": upgrade_request.billing_email
            },
            "benefits": {
                "unlimited_memories": True,
                "monthly_summary_pages": TIER_LIMITS["pro"]["monthly_summary_pages"],
                "ai_dashboard_access": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing subscription upgrade: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/usage", 
    response_model=UsageResponse,
    summary="Get Usage Statistics",
    description="""
    Get detailed usage statistics and limits for the authenticated user.
    
    This endpoint provides comprehensive usage information including:
    - Current usage counts (memories saved, summary pages used)
    - Tier-specific limits and remaining allowances
    - Capability flags (can save memory, can generate summary)
    - Next reset date for monthly limits
    - Usage percentages for visual indicators
    
    **Usage Tracking**:
    - Memory saves are tracked lifetime (reset only for free tier at 100 limit)
    - Summary pages reset monthly on the reset date
    - Capabilities are checked in real-time against current usage
    
    **Authentication Required**: User must be logged in.
    """,
    responses={
        200: {
            "description": "Successfully retrieved usage statistics",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "user_12345",
                        "subscription_tier": "free",
                        "memories_used": 25,
                        "memories_limit": 100,
                        "summary_pages_used": 3,
                        "summary_pages_limit": 5,
                        "can_save_memory": True,
                        "can_generate_summary": True,
                        "monthly_reset_date": "2024-02-01T00:00:00Z",
                        "memories_percentage": 25.0,
                        "summary_pages_percentage": 60.0
                    }
                }
            }
        },
        404: {"description": "User not found in the system"}
    }
)
async def get_usage_statistics(request: Request):
    """
    Get current usage statistics and limits for the authenticated user.
    
    Returns detailed usage information with tier-specific limits and capabilities.
    """
    logger.info(f"📈 SUBSCRIPTION USAGE: Getting usage stats for user")
    logger.info(f"   └─ User ID: {request.state.user_id}")
    
    try:
        subscription_data = get_user_subscription(request.state.user_id)
        
        if not subscription_data:
            logger.error(f"❌ User not found: {request.state.user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        tier = subscription_data["subscription_tier"]
        memories_used = subscription_data["total_memories_saved"]
        summary_pages_used = subscription_data["monthly_summary_pages_used"]
        
        # Get limits for the user's tier
        memories_limit = TIER_LIMITS[tier]["memories"]
        summary_pages_limit = TIER_LIMITS[tier]["monthly_summary_pages"]
        
        # Check current capabilities
        can_save_memory = check_memory_limit(request.state.user_id)
        can_generate_summary = check_summary_limit(request.state.user_id, 1)  # Check for 1 page
        
        response = UsageResponse(
            user_id=request.state.user_id,
            subscription_tier=tier,
            memories_used=memories_used,
            memories_limit=memories_limit,
            summary_pages_used=summary_pages_used,
            summary_pages_limit=summary_pages_limit,
            can_save_memory=can_save_memory,
            can_generate_summary=can_generate_summary,
            monthly_reset_date=subscription_data["monthly_summary_reset_date"]
        )
        
        logger.info(f"✅ Usage statistics retrieved successfully")
        logger.info(f"   ├─ Tier: {tier}")
        logger.info(f"   ├─ Memories: {memories_used}/{memories_limit}")
        logger.info(f"   ├─ Summary pages: {summary_pages_used}/{summary_pages_limit}")
        logger.info(f"   ├─ Can save memory: {can_save_memory}")
        logger.info(f"   └─ Can generate summary: {can_generate_summary}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting usage statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post(
    "/downgrade",
    summary="Downgrade to Free Subscription",
    description="""
    Cancel Pro subscription and downgrade to Free tier immediately.
    
    This endpoint handles subscription cancellation:
    - Validates user has an active Pro subscription
    - Changes tier to Free with immediate effect
    - Preserves existing memories (but limits future saves)
    - Logs downgrade event for analytics and retention analysis
    
    **Impact of Downgrade**:
    - Memory saves limited to 100 total (existing preserved)
    - Summary pages limited to 5 per month
    - Loss of Pro features and priority support
    
    **Data Preservation**: All existing memories are preserved and searchable.
    
    **Authentication Required**: User must be logged in.
    """,
    responses={
        200: {
            "description": "Successfully downgraded to Free subscription",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Subscription downgraded to Free successfully",
                        "subscription": {
                            "tier": "free",
                            "status": "cancelled",
                            "end_date": "2024-01-15T10:30:00Z"
                        },
                        "new_limits": {
                            "memories": 100,
                            "monthly_summary_pages": 5,
                            "ai_dashboard_access": False
                        },
                        "note": "Your existing memories are preserved, but you may be limited in saving new ones."
                    }
                }
            }
        },
        400: {"description": "User already has Free subscription"},
        404: {"description": "User not found in the system"}
    }
)
async def downgrade_subscription(request: Request):
    """
    Cancel Pro subscription and downgrade to Free tier.
    
    Immediately cancels Pro subscription while preserving existing user data.
    """
    logger.info(f"⬇️ SUBSCRIPTION DOWNGRADE: Processing downgrade request")
    logger.info(f"   └─ User ID: {request.state.user_id}")
    
    try:
        # Validate user exists and get current subscription
        current_subscription = get_user_subscription(request.state.user_id)
        if not current_subscription:
            logger.error(f"❌ User not found: {request.state.user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is on Free tier already
        if current_subscription["subscription_tier"] == "free":
            logger.warning(f"⚠️ User already has Free subscription")
            raise HTTPException(status_code=400, detail="User already has Free subscription")
        
        # Update user subscription in database
        now = datetime.now(timezone.utc)
        update_data = {
            "subscription_tier": "free",
            "subscription_status": "cancelled",
            "subscription_end_date": now  # Set end date to now
        }
        
        result = collection.update_one(
            {"id": request.state.user_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            logger.error(f"❌ Failed to update subscription in database")
            raise HTTPException(status_code=500, detail="Failed to update subscription")
        
        logger.info(f"✅ Subscription downgraded successfully")
        logger.info(f"   ├─ New tier: free")
        logger.info(f"   ├─ Status: cancelled")
        logger.info(f"   └─ End date: {now.isoformat()}")
        
        # Log subscription downgrade event for analytics
        subscription_logger.log_downgrade_event(
            user_id=request.state.user_id,
            previous_tier=current_subscription["subscription_tier"],
            new_tier="free",
            method="user",
            reason="user_initiated_cancellation"
        )
        
        return {
            "success": True,
            "message": "Subscription downgraded to Free successfully",
            "subscription": {
                "tier": "free",
                "status": "cancelled",
                "end_date": now.isoformat()
            },
            "new_limits": {
                "memories": TIER_LIMITS["free"]["memories"],
                "monthly_summary_pages": TIER_LIMITS["free"]["monthly_summary_pages"],
                "ai_dashboard_access": False
            },
            "note": "Your existing memories are preserved, but you may be limited in saving new ones."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing subscription downgrade: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 