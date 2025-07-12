from fastapi import APIRouter, HTTPException, Request, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import math

from app.services.admin_service import (
    is_admin_user,
    get_all_users_with_subscriptions,
    get_user_subscription_detail,
    admin_upgrade_user_subscription,
    admin_downgrade_user_subscription,
    admin_extend_user_subscription,
    admin_reset_user_usage,
    get_admin_analytics
)
from app.schema.admin_schema import (
    AdminUserListResponse,
    AdminUserList,
    AdminUserSubscriptionDetail,
    AdminSubscriptionUpdate,
    AdminExtendSubscription,
    AdminResetUsage,
    AdminAnalytics,
    AdminActionResponse
)
from app.services.subscription_logging_service import subscription_logger

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/admin", 
    tags=["admin"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin privileges required"},
        500: {"description": "Internal server error"}
    }
)

def require_admin(request: Request) -> dict:
    """
    Dependency to ensure the authenticated user has admin privileges.
    
    This dependency checks that:
    1. User is authenticated (has valid session)
    2. User has admin role/privileges in the system
    
    Args:
        request: FastAPI request object with user authentication
        
    Returns:
        dict: User payload if admin, raises HTTPException if not
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
    """
    # Check if user is authenticated
    user_payload = getattr(request.state, 'user_payload', None)
    if not user_payload:
        logger.warning("❌ ADMIN ACCESS: Authentication required for admin endpoint")
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Check if user has admin privileges
    if not is_admin_user(user_payload):
        user_email = user_payload.get("email", "unknown")
        logger.warning(f"❌ ADMIN ACCESS: Forbidden - {user_email} attempted admin access")
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    
    logger.info(f"✅ ADMIN ACCESS: Granted for {user_payload.get('email', 'unknown')}")
    return user_payload

@router.get(
    "/users", 
    response_model=AdminUserListResponse,
    summary="List All Users",
    description="""
    Get a paginated list of all users with their subscription details.
    
    This endpoint provides comprehensive user management information including:
    - User account details (ID, email, name, creation date)
    - Current subscription tier and status
    - Usage statistics (memories saved, summary pages used)
    - Subscription dates and activity information
    
    **Admin Use Cases**:
    - User account overview and management
    - Subscription status monitoring
    - Usage pattern analysis
    - Customer support and account investigations
    
    **Pagination**: Results are paginated for performance with configurable page size.
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully retrieved paginated user list",
            "content": {
                "application/json": {
                    "example": {
                        "users": [
                            {
                                "user_id": "user_12345",
                                "email": "user@example.com",
                                "full_name": "John Doe",
                                "subscription_tier": "pro",
                                "subscription_status": "active",
                                "subscription_start_date": "2024-01-01T00:00:00Z",
                                "subscription_end_date": "2024-02-01T00:00:00Z",
                                "total_memories_saved": 150,
                                "monthly_summary_pages_used": 25,
                                "created_at": "2023-12-01T10:00:00Z",
                                "last_sign_in_at": "2024-01-14T15:30:00Z"
                            }
                        ],
                        "total_users": 1250,
                        "page": 1,
                        "page_size": 50,
                        "total_pages": 25
                    }
                }
            }
        }
    }
)
async def list_all_users(
    request: Request,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=50, ge=1, le=100, description="Users per page (max 100)"),
    admin_user: dict = Depends(require_admin)
):
    """
    List all users with their subscription details (paginated).
    
    Admin endpoint to view all users in the system with their subscription information.
    Returns paginated results for efficient loading of large user bases.
    """
    logger.info(f"👥 ADMIN USERS: Getting user list")
    logger.info(f"   ├─ Admin: {admin_user.get('email')}")
    logger.info(f"   ├─ Page: {page}")
    logger.info(f"   └─ Page size: {page_size}")
    
    try:
        users, total_count = get_all_users_with_subscriptions(page, page_size)
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
        
        # Convert to AdminUserList models
        admin_users = []
        for user in users:
            admin_user_data = AdminUserList(
                user_id=user["id"],
                email=user["email"],
                full_name=user.get("full_name"),
                subscription_tier=user["subscription_tier"],
                subscription_status=user["subscription_status"],
                subscription_start_date=user.get("subscription_start_date"),
                subscription_end_date=user.get("subscription_end_date"),
                total_memories_saved=user["total_memories_saved"],
                monthly_summary_pages_used=user["monthly_summary_pages_used"],
                created_at=user.get("created_at"),
                last_sign_in_at=user.get("last_sign_in_at")
            )
            admin_users.append(admin_user_data)
        
        response = AdminUserListResponse(
            users=admin_users,
            total_users=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
        logger.info(f"✅ User list retrieved successfully")
        logger.info(f"   ├─ Users on page: {len(admin_users)}")
        logger.info(f"   ├─ Total users: {total_count}")
        logger.info(f"   └─ Total pages: {total_pages}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error getting user list: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user list")

@router.get(
    "/users/{user_id}/subscription", 
    response_model=AdminUserSubscriptionDetail,
    summary="Get User Subscription Details",
    description="""
    Get comprehensive subscription information for a specific user.
    
    This endpoint provides detailed user information including:
    - Complete subscription history and status
    - Detailed usage statistics and limits
    - Account creation and activity dates
    - Subscription expiration and renewal information
    - Days remaining calculation for active subscriptions
    
    **Admin Use Cases**:
    - Customer support investigations
    - Account troubleshooting
    - Subscription verification
    - Usage analysis for specific users
    - Billing and payment inquiries
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully retrieved detailed user subscription information",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "user_12345",
                        "email": "user@example.com",
                        "full_name": "John Doe",
                        "subscription_tier": "pro",
                        "subscription_status": "active",
                        "subscription_start_date": "2024-01-01T00:00:00Z",
                        "subscription_end_date": "2024-02-01T00:00:00Z",
                        "total_memories_saved": 150,
                        "monthly_summary_pages_used": 25,
                        "monthly_summary_reset_date": "2024-01-01T00:00:00Z",
                        "created_at": "2023-12-01T10:00:00Z",
                        "last_sign_in_at": "2024-01-14T15:30:00Z",
                        "days_remaining": 17,
                        "is_expired": False
                    }
                }
            }
        },
        404: {"description": "User not found in the system"}
    }
)
async def get_user_subscription(
    user_id: str,
    request: Request,
    admin_user: dict = Depends(require_admin)
):
    """
    Get detailed subscription information for a specific user.
    
    Returns comprehensive subscription details, usage statistics, and account information
    for the specified user ID.
    """
    logger.info(f"👤 ADMIN USER DETAIL: Getting subscription for user {user_id}")
    logger.info(f"   └─ Admin: {admin_user.get('email')}")
    
    try:
        user_data = get_user_subscription_detail(user_id)
        
        if not user_data:
            logger.warning(f"❌ User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        response = AdminUserSubscriptionDetail(
            user_id=user_data["id"],
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            subscription_tier=user_data["subscription_tier"],
            subscription_status=user_data["subscription_status"],
            subscription_start_date=user_data.get("subscription_start_date"),
            subscription_end_date=user_data.get("subscription_end_date"),
            total_memories_saved=user_data["total_memories_saved"],
            monthly_summary_pages_used=user_data["monthly_summary_pages_used"],
            monthly_summary_reset_date=user_data.get("monthly_summary_reset_date"),
            created_at=user_data.get("created_at"),
            last_sign_in_at=user_data.get("last_sign_in_at"),
            days_remaining=user_data.get("days_remaining"),
            is_expired=user_data.get("is_expired", False)
        )
        
        logger.info(f"✅ User subscription detail retrieved successfully")
        logger.info(f"   ├─ User: {user_data.get('email')}")
        logger.info(f"   ├─ Tier: {user_data['subscription_tier']}")
        logger.info(f"   └─ Status: {user_data['subscription_status']}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting user subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user subscription")

@router.post(
    "/users/{user_id}/upgrade", 
    response_model=AdminActionResponse,
    summary="Manually Upgrade User Subscription",
    description="""
    Manually upgrade a user to Pro tier with optional subscription extension.
    
    This endpoint allows admins to:
    - Upgrade users from Free to Pro tier
    - Set custom subscription durations with extend_days parameter
    - Track administrative actions with reason codes
    - Handle special cases (customer support, promotional upgrades, etc.)
    
    **Admin Use Cases**:
    - Customer support resolutions
    - Promotional upgrades and campaigns
    - Account recovery and restoration
    - Testing and development scenarios
    - Compensation for service issues
    
    **Upgrade Process**:
    - Validates current subscription status
    - Updates tier and sets appropriate dates
    - Logs administrative action for audit trail
    - Preserves existing user data and memories
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully upgraded user to Pro subscription",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "User successfully upgraded to pro tier",
                        "user_id": "user_12345",
                        "action": "upgrade",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "details": {
                            "previous_tier": "free",
                            "new_tier": "pro",
                            "subscription_status": "active",
                            "subscription_end_date": "2024-02-15T10:30:00Z",
                            "reason": "Customer support resolution",
                            "admin_email": "admin@hippocampus.ai"
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid upgrade request (user already Pro, invalid parameters)"},
        404: {"description": "User not found in the system"}
    }
)
async def manually_upgrade_user(
    user_id: str,
    upgrade_request: AdminSubscriptionUpdate,
    request: Request,
    admin_user: dict = Depends(require_admin)
):
    """
    Manually upgrade user to Pro tier (admin action).
    
    Processes administrative subscription upgrade with optional extension days
    and reason tracking for audit purposes.
    """
    logger.info(f"⬆️ ADMIN UPGRADE: Manually upgrading user {user_id}")
    logger.info(f"   ├─ Admin: {admin_user.get('email')}")
    logger.info(f"   ├─ Target tier: {upgrade_request.target_tier}")
    logger.info(f"   ├─ Extend days: {upgrade_request.extend_days}")
    logger.info(f"   └─ Reason: {upgrade_request.reason}")
    
    try:
        result = admin_upgrade_user_subscription(
            user_id=user_id,
            target_tier=upgrade_request.target_tier.value,
            extend_days=upgrade_request.extend_days,
            reason=upgrade_request.reason
        )
        
        response = AdminActionResponse(
            success=True,
            message=f"User successfully upgraded to {upgrade_request.target_tier} tier",
            user_id=user_id,
            action="upgrade",
            details={
                "previous_tier": result["previous_tier"],
                "new_tier": result["new_tier"],
                "subscription_status": result["subscription_status"],
                "subscription_end_date": result.get("subscription_end_date"),
                "reason": upgrade_request.reason,
                "admin_email": admin_user.get("email")
            }
        )
        
        logger.info(f"✅ Admin upgrade completed successfully")
        logger.info(f"   ├─ {result['previous_tier']} → {result['new_tier']}")
        logger.info(f"   └─ End date: {result.get('subscription_end_date', 'N/A')}")
        
        # Log admin-initiated upgrade event for analytics
        subscription_logger.log_upgrade_event(
            user_id=user_id,
            previous_tier=result["previous_tier"],
            new_tier=result["new_tier"],
            method="admin",
            admin_user=admin_user.get("email"),
            payment_method="admin_manual"
        )
        
        return response
        
    except ValueError as e:
        logger.warning(f"❌ Invalid upgrade request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error upgrading user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upgrade user")

@router.post(
    "/users/{user_id}/downgrade", 
    response_model=AdminActionResponse,
    summary="Manually Downgrade User Subscription",
    description="""
    Manually downgrade a user from Pro to Free tier.
    
    This endpoint allows admins to:
    - Downgrade users from Pro to Free tier immediately
    - Handle subscription cancellations and refunds
    - Process policy violations or abuse cases
    - Track administrative actions with reason codes
    
    **Admin Use Cases**:
    - Customer-requested cancellations
    - Chargeback and payment dispute handling
    - Policy violation enforcement
    - Account suspension scenarios
    - Testing and development
    
    **Downgrade Process**:
    - Validates current Pro subscription
    - Changes tier to Free with immediate effect
    - Preserves existing memories and data
    - Logs administrative action for audit trail
    - Applies Free tier limits to future usage
    
    **Data Preservation**: All existing memories are preserved and searchable.
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully downgraded user to Free subscription",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "User successfully downgraded to Free tier",
                        "user_id": "user_12345",
                        "action": "downgrade",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "details": {
                            "previous_tier": "pro",
                            "new_tier": "free",
                            "subscription_status": "cancelled",
                            "subscription_end_date": "2024-01-15T10:30:00Z",
                            "reason": "Customer requested cancellation",
                            "admin_email": "admin@hippocampus.ai"
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid downgrade request (user already Free)"},
        404: {"description": "User not found in the system"}
    }
)
async def manually_downgrade_user(
    user_id: str,
    request: Request,
    reason: Optional[str] = Query(None, description="Reason for downgrade"),
    admin_user: dict = Depends(require_admin)
):
    """
    Manually downgrade user to Free tier (admin action).
    
    Processes administrative subscription downgrade while preserving user data
    and tracking the action for audit purposes.
    """
    logger.info(f"⬇️ ADMIN DOWNGRADE: Manually downgrading user {user_id}")
    logger.info(f"   ├─ Admin: {admin_user.get('email')}")
    logger.info(f"   └─ Reason: {reason}")
    
    try:
        result = admin_downgrade_user_subscription(
            user_id=user_id,
            reason=reason
        )
        
        response = AdminActionResponse(
            success=True,
            message="User successfully downgraded to Free tier",
            user_id=user_id,
            action="downgrade",
            details={
                "previous_tier": result["previous_tier"],
                "new_tier": result["new_tier"],
                "subscription_status": result["subscription_status"],
                "subscription_end_date": result.get("subscription_end_date"),
                "reason": reason,
                "admin_email": admin_user.get("email")
            }
        )
        
        logger.info(f"✅ Admin downgrade completed successfully")
        logger.info(f"   ├─ {result['previous_tier']} → {result['new_tier']}")
        logger.info(f"   └─ Status: {result['subscription_status']}")
        
        # Log admin-initiated downgrade event for analytics
        subscription_logger.log_downgrade_event(
            user_id=user_id,
            previous_tier=result["previous_tier"],
            new_tier=result["new_tier"],
            method="admin",
            admin_user=admin_user.get("email"),
            reason=reason or "admin_initiated"
        )
        
        return response
        
    except ValueError as e:
        logger.warning(f"❌ Invalid downgrade request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error downgrading user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to downgrade user")

@router.post(
    "/users/{user_id}/extend", 
    response_model=AdminActionResponse,
    summary="Extend User Subscription",
    description="""
    Extend a user's subscription end date by specified number of days.
    
    This endpoint allows admins to:
    - Extend active Pro subscriptions
    - Add time for service disruptions or compensation
    - Handle special promotional extensions
    - Manage subscription renewals manually
    
    **Admin Use Cases**:
    - Service disruption compensation
    - Customer support resolutions
    - Promotional campaigns and bonuses
    - Manual renewal processing
    - Testing subscription lifecycle
    
    **Extension Process**:
    - Validates user has an existing subscription
    - Adds specified days to current end date
    - Maintains subscription status and tier
    - Logs administrative action for audit trail
    
    **Note**: This extends existing subscriptions, not create new ones.
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully extended user subscription",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "User subscription extended by 30 days",
                        "user_id": "user_12345",
                        "action": "extend",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "details": {
                            "previous_end_date": "2024-02-01T00:00:00Z",
                            "new_end_date": "2024-03-02T00:00:00Z",
                            "days_extended": 30,
                            "subscription_status": "active",
                            "reason": "Service disruption compensation",
                            "admin_email": "admin@hippocampus.ai"
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid extension request (no subscription to extend, invalid days)"},
        404: {"description": "User not found in the system"}
    }
)
async def extend_user_subscription(
    user_id: str,
    extend_request: AdminExtendSubscription,
    request: Request,
    admin_user: dict = Depends(require_admin)
):
    """
    Extend user subscription end date (admin action).
    
    Adds specified days to user's current subscription end date while preserving
    all other subscription details.
    """
    logger.info(f"📅 ADMIN EXTEND: Extending user subscription {user_id}")
    logger.info(f"   ├─ Admin: {admin_user.get('email')}")
    logger.info(f"   ├─ Extend days: {extend_request.extend_days}")
    logger.info(f"   └─ Reason: {extend_request.reason}")
    
    try:
        result = admin_extend_user_subscription(
            user_id=user_id,
            extend_days=extend_request.extend_days,
            reason=extend_request.reason
        )
        
        response = AdminActionResponse(
            success=True,
            message=f"User subscription extended by {extend_request.extend_days} days",
            user_id=user_id,
            action="extend",
            details={
                "previous_end_date": result.get("previous_end_date"),
                "new_end_date": result["new_end_date"],
                "days_extended": result["days_extended"],
                "subscription_status": result["subscription_status"],
                "reason": extend_request.reason,
                "admin_email": admin_user.get("email")
            }
        )
        
        logger.info(f"✅ Admin extension completed successfully")
        logger.info(f"   ├─ Days extended: {result['days_extended']}")
        logger.info(f"   └─ New end date: {result['new_end_date']}")
        
        return response
        
    except ValueError as e:
        logger.warning(f"❌ Invalid extension request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error extending user subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to extend subscription")

@router.post(
    "/users/{user_id}/reset-usage", 
    response_model=AdminActionResponse,
    summary="Reset User Usage Counters",
    description="""
    Reset user usage counters for memories and/or monthly summaries.
    
    This endpoint allows admins to:
    - Reset total memory count (rare, for account recovery)
    - Reset monthly summary pages (common, for billing disputes)
    - Handle usage corrections and adjustments
    - Manage special promotional resets
    
    **Admin Use Cases**:
    - Billing dispute resolutions
    - Account recovery and data corrections
    - Testing and development resets
    - Promotional campaign implementations
    - Customer support goodwill gestures
    
    **Reset Options**:
    - **Memory Reset**: Resets total_memories_saved to 0 (use with caution)
    - **Monthly Summary Reset**: Resets monthly_summary_pages_used to 0
    - Both resets can be performed simultaneously or separately
    
    **Impact Considerations**:
    - Memory reset affects lifetime usage limits for Free tier users
    - Monthly summary reset provides immediate additional page allowance
    - All resets are logged for audit and tracking purposes
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully reset user usage counters",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "User usage counters reset: monthly summaries",
                        "user_id": "user_12345",
                        "action": "reset-usage",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "details": {
                            "reset_memories": False,
                            "reset_monthly_summaries": True,
                            "previous_values": {
                                "monthly_summary_pages_used": 5
                            },
                            "new_values": {
                                "monthly_summary_pages_used": 0
                            },
                            "reason": "Billing dispute resolution",
                            "admin_email": "admin@hippocampus.ai"
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid reset request (no reset options selected)"},
        404: {"description": "User not found in the system"}
    }
)
async def reset_user_usage_counters(
    user_id: str,
    reset_request: AdminResetUsage,
    request: Request,
    admin_user: dict = Depends(require_admin)
):
    """
    Reset user usage counters (admin action).
    
    Resets specified usage counters to zero while tracking previous values
    and logging the administrative action.
    """
    logger.info(f"🔄 ADMIN RESET: Resetting user usage {user_id}")
    logger.info(f"   ├─ Admin: {admin_user.get('email')}")
    logger.info(f"   ├─ Reset memories: {reset_request.reset_memories}")
    logger.info(f"   ├─ Reset summaries: {reset_request.reset_monthly_summaries}")
    logger.info(f"   └─ Reason: {reset_request.reason}")
    
    try:
        result = admin_reset_user_usage(
            user_id=user_id,
            reset_memories=reset_request.reset_memories,
            reset_monthly_summaries=reset_request.reset_monthly_summaries,
            reason=reset_request.reason
        )
        
        reset_types = []
        if reset_request.reset_memories:
            reset_types.append("memories")
        if reset_request.reset_monthly_summaries:
            reset_types.append("monthly summaries")
        
        response = AdminActionResponse(
            success=True,
            message=f"User usage counters reset: {', '.join(reset_types)}",
            user_id=user_id,
            action="reset-usage",
            details={
                "reset_memories": result["reset_memories"],
                "reset_monthly_summaries": result["reset_monthly_summaries"],
                "previous_values": result["previous_values"],
                "new_values": result["new_values"],
                "reason": reset_request.reason,
                "admin_email": admin_user.get("email")
            }
        )
        
        logger.info(f"✅ Admin usage reset completed successfully")
        for key, value in result["previous_values"].items():
            logger.info(f"   ├─ {key}: {value} → 0")
        
        return response
        
    except ValueError as e:
        logger.warning(f"❌ Invalid reset request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error resetting user usage: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset usage")

@router.get(
    "/analytics", 
    response_model=AdminAnalytics,
    summary="Get Subscription Analytics",
    description="""
    Get comprehensive subscription analytics and business metrics.
    
    This endpoint provides detailed business intelligence including:
    - User distribution across subscription tiers
    - Subscription status breakdown (active, expired, cancelled)
    - Usage analytics (memories saved, summary pages used)
    - Conversion rate analysis (Free to Pro)
    - Revenue estimates and financial projections
    - User engagement metrics
    
    **Analytics Categories**:
    - **User Metrics**: Total users, tier distribution, growth patterns
    - **Subscription Health**: Active vs expired subscriptions, churn analysis
    - **Usage Patterns**: Memory saves, summary generation, feature adoption
    - **Financial Metrics**: Conversion rates, revenue estimates, ARPU
    - **Engagement Metrics**: Average usage per user, activity levels
    
    **Business Use Cases**:
    - Executive dashboard and reporting
    - Product strategy and feature planning
    - Marketing campaign effectiveness
    - Customer success and retention analysis
    - Financial planning and forecasting
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully retrieved subscription analytics",
            "content": {
                "application/json": {
                    "example": {
                        "total_users": 1250,
                        "free_users": 1100,
                        "pro_users": 150,
                        "active_subscriptions": 140,
                        "expired_subscriptions": 8,
                        "cancelled_subscriptions": 2,
                        "total_memories_saved": 45000,
                        "total_summary_pages_used": 2500,
                        "average_memories_per_user": 36.0,
                        "conversion_rate": 12.0,
                        "revenue_estimate": 1200.0
                    }
                }
            }
        }
    }
)
async def get_subscription_analytics(
    request: Request,
    admin_user: dict = Depends(require_admin)
):
    """
    Get subscription analytics and metrics (admin dashboard).
    
    Returns comprehensive business analytics including user distribution,
    subscription health, usage patterns, and financial metrics.
    """
    logger.info(f"📊 ADMIN ANALYTICS: Getting subscription analytics")
    logger.info(f"   └─ Admin: {admin_user.get('email')}")
    
    try:
        analytics_data = get_admin_analytics()
        
        response = AdminAnalytics(
            total_users=analytics_data["total_users"],
            free_users=analytics_data["free_users"],
            pro_users=analytics_data["pro_users"],
            active_subscriptions=analytics_data["active_subscriptions"],
            expired_subscriptions=analytics_data["expired_subscriptions"],
            cancelled_subscriptions=analytics_data["cancelled_subscriptions"],
            total_memories_saved=analytics_data["total_memories_saved"],
            total_summary_pages_used=analytics_data["total_summary_pages_used"],
            average_memories_per_user=analytics_data["average_memories_per_user"],
            conversion_rate=analytics_data["conversion_rate"],
            revenue_estimate=analytics_data["revenue_estimate"]
        )
        
        logger.info(f"✅ Admin analytics retrieved successfully")
        logger.info(f"   ├─ Total users: {response.total_users}")
        logger.info(f"   ├─ Free: {response.free_users}, Pro: {response.pro_users}")
        logger.info(f"   ├─ Conversion rate: {response.conversion_rate}%")
        logger.info(f"   └─ Revenue estimate: ${response.revenue_estimate}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error getting admin analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics") 