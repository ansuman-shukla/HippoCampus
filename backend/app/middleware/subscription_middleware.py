from functools import wraps
from fastapi import Request, HTTPException
from app.services.subscription_service import check_memory_limit, check_summary_limit, estimate_content_pages, get_user_subscription, TIER_LIMITS
from app.services.subscription_logging_service import subscription_logger
import logging

logger = logging.getLogger(__name__)

def create_upgrade_response(message: str, pages_requested: int = None) -> dict:
    """Create a standardized 402 upgrade response"""
    response_data = {
        "error": "Subscription limit exceeded",
        "message": message,
        "action_required": "upgrade",
        "upgrade_url": "/subscription/upgrade",
        "subscription_info": {
            "current_tier": "free",
            "upgrade_benefits": [
                "Unlimited memory saves",
                "100 summary pages per month",
                "AI-powered dashboard queries"
            ]
        }
    }
    
    if pages_requested is not None:
        response_data["pages_requested"] = pages_requested
    
    return response_data

def require_memory_limit(func):
    """
    Decorator to check memory save limits before executing endpoint.
    
    Checks if the user can save another memory based on their subscription tier.
    Returns 402 Payment Required if limit is exceeded.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find the request object in args - typically first argument for FastAPI endpoints
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            logger.error("❌ SUBSCRIPTION MIDDLEWARE: No Request object found in function arguments")
            raise HTTPException(status_code=500, detail="Internal server error")
        
        # Get user_id from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            logger.error("❌ SUBSCRIPTION MIDDLEWARE: Memory limit check failed - no user_id in request state")
            raise HTTPException(status_code=401, detail="Authentication required")
        
        logger.info(f"🔍 SUBSCRIPTION MIDDLEWARE: Checking memory limit for user {user_id}")
        
        # Check memory limit using subscription service
        if not check_memory_limit(user_id):
            logger.warning(f"🚫 SUBSCRIPTION MIDDLEWARE: Memory limit exceeded for user {user_id}")
            
            # Get user subscription data for logging
            subscription_data = get_user_subscription(user_id)
            if subscription_data:
                current_usage = subscription_data["total_memories_saved"]
                tier = subscription_data["subscription_tier"]
                limit_value = TIER_LIMITS.get(tier, {}).get("memories", 100)
                
                # Log limit breach event for analytics
                subscription_logger.log_limit_breach_event(
                    user_id=user_id,
                    limit_type="memory",
                    current_usage=current_usage,
                    limit_value=limit_value,
                    tier=tier
                )
            
            response_data = create_upgrade_response(
                "You've reached your memory save limit (100 saves). Upgrade to Pro for unlimited saves."
            )
            raise HTTPException(status_code=402, detail=response_data)
        
        logger.info(f"✅ SUBSCRIPTION MIDDLEWARE: Memory limit check passed for user {user_id}")
        
        # Call the original function
        return await func(*args, **kwargs)
    
    return wrapper

def require_summary_limit(pages_requested: int = None):
    """
    Decorator factory to check summary page limits before executing endpoint.
    
    Args:
        pages_requested: Number of pages requested (if known ahead of time)
    
    Returns:
        Decorator that checks if user can generate summary pages based on their tier.
        Returns 402 Payment Required if limit would be exceeded.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object in args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                logger.error("❌ SUBSCRIPTION MIDDLEWARE: No Request object found in function arguments")
                raise HTTPException(status_code=500, detail="Internal server error")
            
            # Get user_id from request state (set by auth middleware)
            user_id = getattr(request.state, 'user_id', None)
            if not user_id:
                logger.error("❌ SUBSCRIPTION MIDDLEWARE: Summary limit check failed - no user_id in request state")
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Determine pages requested
            estimated_pages = pages_requested
            if estimated_pages is None:
                # Try to extract content from request body or state to estimate pages
                content = getattr(request.state, 'content', None)
                if content:
                    estimated_pages = estimate_content_pages(content)
                else:
                    # Default to 1 page if no content available
                    estimated_pages = 1
            
            logger.info(f"🔍 SUBSCRIPTION MIDDLEWARE: Checking summary limit for user {user_id}")
            logger.info(f"   └─ Pages requested: {estimated_pages}")
            
            # Check summary limit using subscription service
            if not check_summary_limit(user_id, estimated_pages):
                logger.warning(f"🚫 SUBSCRIPTION MIDDLEWARE: Summary limit exceeded for user {user_id}")
                logger.warning(f"   └─ Pages requested: {estimated_pages}")
                
                # Get user subscription data for logging
                subscription_data = get_user_subscription(user_id)
                if subscription_data:
                    current_usage = subscription_data["monthly_summary_pages_used"]
                    tier = subscription_data["subscription_tier"]
                    limit_value = TIER_LIMITS.get(tier, {}).get("monthly_summary_pages", 5)
                    
                    # Log limit breach event for analytics
                    subscription_logger.log_limit_breach_event(
                        user_id=user_id,
                        limit_type="summary",
                        current_usage=current_usage,
                        limit_value=limit_value,
                        tier=tier,
                        pages_requested=estimated_pages
                    )
                
                response_data = create_upgrade_response(
                    f"This summary ({estimated_pages} pages) would exceed your monthly limit (5 pages). "
                    f"Upgrade to Pro for 100 pages per month.",
                    pages_requested=estimated_pages
                )
                raise HTTPException(status_code=402, detail=response_data)
            
            logger.info(f"✅ SUBSCRIPTION MIDDLEWARE: Summary limit check passed for user {user_id}")
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

async def check_memory_middleware(request: Request) -> None:
    """
    Middleware function to check memory limits (alternative to decorator approach).
    
    Can be called directly within endpoint functions for more flexible usage.
    
    Args:
        request: FastAPI Request object
        
    Raises:
        HTTPException: 402 if memory limit exceeded, 401 if not authenticated
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        logger.error("❌ SUBSCRIPTION MIDDLEWARE: Memory middleware check failed - no user_id in request state")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(f"🔍 SUBSCRIPTION MIDDLEWARE: Middleware memory check for user {user_id}")
    
    if not check_memory_limit(user_id):
        logger.warning(f"🚫 SUBSCRIPTION MIDDLEWARE: Memory limit exceeded for user {user_id}")
        
        # Get user subscription data for logging
        subscription_data = get_user_subscription(user_id)
        if subscription_data:
            current_usage = subscription_data["total_memories_saved"]
            tier = subscription_data["subscription_tier"]
            limit_value = TIER_LIMITS.get(tier, {}).get("memories", 100)
            
            # Log limit breach event for analytics
            subscription_logger.log_limit_breach_event(
                user_id=user_id,
                limit_type="memory",
                current_usage=current_usage,
                limit_value=limit_value,
                tier=tier
            )
        
        response_data = create_upgrade_response(
            "You've reached your memory save limit (100 saves). Upgrade to Pro for unlimited saves."
        )
        raise HTTPException(status_code=402, detail=response_data)
    
    logger.info(f"✅ SUBSCRIPTION MIDDLEWARE: Memory middleware check passed for user {user_id}")

async def check_summary_middleware(request: Request, pages_requested: int = 1) -> None:
    """
    Middleware function to check summary limits (alternative to decorator approach).
    
    Can be called directly within endpoint functions for more flexible usage.
    
    Args:
        request: FastAPI Request object
        pages_requested: Number of pages requested for summarization
        
    Raises:
        HTTPException: 402 if summary limit exceeded, 401 if not authenticated
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        logger.error("❌ SUBSCRIPTION MIDDLEWARE: Summary middleware check failed - no user_id in request state")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(f"🔍 SUBSCRIPTION MIDDLEWARE: Middleware summary check for user {user_id}")
    logger.info(f"   └─ Pages requested: {pages_requested}")
    
    if not check_summary_limit(user_id, pages_requested):
        logger.warning(f"🚫 SUBSCRIPTION MIDDLEWARE: Summary limit exceeded for user {user_id}")
        logger.warning(f"   └─ Pages requested: {pages_requested}")
        
        # Get user subscription data for logging
        subscription_data = get_user_subscription(user_id)
        if subscription_data:
            current_usage = subscription_data["monthly_summary_pages_used"]
            tier = subscription_data["subscription_tier"]
            limit_value = TIER_LIMITS.get(tier, {}).get("monthly_summary_pages", 5)
            
            # Log limit breach event for analytics
            subscription_logger.log_limit_breach_event(
                user_id=user_id,
                limit_type="summary",
                current_usage=current_usage,
                limit_value=limit_value,
                tier=tier,
                pages_requested=pages_requested
            )
        
        response_data = create_upgrade_response(
            f"This summary ({pages_requested} pages) would exceed your monthly limit (5 pages). "
            f"Upgrade to Pro for 100 pages per month.",
            pages_requested=pages_requested
        )
        raise HTTPException(status_code=402, detail=response_data)
    
    logger.info(f"✅ SUBSCRIPTION MIDDLEWARE: Summary middleware check passed for user {user_id}")

def require_pro_subscription(func):
    """
    Decorator to require Pro subscription for accessing endpoint.
    
    Used for features that are only available to Pro users (like AI dashboard queries).
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find the request object in args
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            logger.error("❌ SUBSCRIPTION MIDDLEWARE: No Request object found in function arguments")
            raise HTTPException(status_code=500, detail="Internal server error")
        
        # Get user_id from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            logger.error("❌ SUBSCRIPTION MIDDLEWARE: Pro subscription check failed - no user_id in request state")
            raise HTTPException(status_code=401, detail="Authentication required")
        
        logger.info(f"🔍 SUBSCRIPTION MIDDLEWARE: Checking Pro subscription for user {user_id}")
        
        # Import here to avoid circular imports
        from app.services.subscription_service import get_user_subscription
        
        subscription_data = get_user_subscription(user_id)
        if not subscription_data:
            logger.error(f"❌ SUBSCRIPTION MIDDLEWARE: Could not retrieve subscription data for user {user_id}")
            raise HTTPException(status_code=500, detail="Could not verify subscription status")
        
        if subscription_data["subscription_tier"] != "pro":
            logger.warning(f"🚫 SUBSCRIPTION MIDDLEWARE: Pro access denied for user {user_id} (tier: {subscription_data['subscription_tier']})")
            response_data = create_upgrade_response(
                "This feature is only available to Pro subscribers. Upgrade to unlock AI-powered dashboard queries."
            )
            raise HTTPException(status_code=402, detail=response_data)
        
        logger.info(f"✅ SUBSCRIPTION MIDDLEWARE: Pro subscription verified for user {user_id}")
        
        # Call the original function
        return await func(*args, **kwargs)
    
    return wrapper 