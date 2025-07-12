from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schema.subscription_schema import SubscriptionTier, SubscriptionStatusEnum

class AdminUserList(BaseModel):
    """
    Pydantic model for admin user listing with subscription details.
    """
    user_id: str = Field(..., description="User identifier")
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    subscription_tier: SubscriptionTier = Field(..., description="Current subscription tier")
    subscription_status: SubscriptionStatusEnum = Field(..., description="Current subscription status")
    subscription_start_date: Optional[datetime] = Field(None, description="Subscription start date")
    subscription_end_date: Optional[datetime] = Field(None, description="Subscription end date")
    total_memories_saved: int = Field(..., ge=0, description="Total memories saved")
    monthly_summary_pages_used: int = Field(..., ge=0, description="Monthly summary pages used")
    created_at: Optional[datetime] = Field(None, description="User account creation date")
    last_sign_in_at: Optional[datetime] = Field(None, description="Last sign in date")

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

class AdminUserListResponse(BaseModel):
    """
    Response model for admin user listing endpoint.
    """
    users: List[AdminUserList] = Field(..., description="List of users with subscription details")
    total_users: int = Field(..., ge=0, description="Total number of users")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Number of users per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

class AdminSubscriptionUpdate(BaseModel):
    """
    Pydantic model for admin subscription update requests.
    """
    target_tier: SubscriptionTier = Field(..., description="Target subscription tier")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for subscription change")
    extend_days: Optional[int] = Field(None, ge=0, le=365, description="Number of days to extend subscription (for upgrades)")

    @field_validator('extend_days')
    @classmethod
    def validate_extend_days(cls, v, info):
        """Validate extend_days is only used for pro tier upgrades"""
        if v is not None and info.data.get('target_tier') != SubscriptionTier.PRO:
            raise ValueError('extend_days can only be used when upgrading to pro tier')
        return v

class AdminExtendSubscription(BaseModel):
    """
    Pydantic model for admin subscription extension requests.
    """
    extend_days: int = Field(..., ge=1, le=365, description="Number of days to extend subscription")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for subscription extension")

class AdminResetUsage(BaseModel):
    """
    Pydantic model for admin usage reset requests.
    """
    reset_memories: bool = Field(default=False, description="Whether to reset total memories count")
    reset_monthly_summaries: bool = Field(default=True, description="Whether to reset monthly summary pages")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for usage reset")

class AdminAnalytics(BaseModel):
    """
    Pydantic model for admin analytics response.
    """
    total_users: int = Field(..., ge=0, description="Total number of users")
    free_users: int = Field(..., ge=0, description="Number of free tier users")
    pro_users: int = Field(..., ge=0, description="Number of pro tier users")
    active_subscriptions: int = Field(..., ge=0, description="Number of active subscriptions")
    expired_subscriptions: int = Field(..., ge=0, description="Number of expired subscriptions")
    cancelled_subscriptions: int = Field(..., ge=0, description="Number of cancelled subscriptions")
    total_memories_saved: int = Field(..., ge=0, description="Total memories saved across all users")
    total_summary_pages_used: int = Field(..., ge=0, description="Total summary pages used this month")
    average_memories_per_user: float = Field(..., ge=0, description="Average memories per user")
    conversion_rate: float = Field(..., ge=0, le=100, description="Free to Pro conversion rate percentage")
    revenue_estimate: float = Field(..., ge=0, description="Estimated monthly revenue (pro users * $8)")

class AdminActionResponse(BaseModel):
    """
    Generic response model for admin actions.
    """
    success: bool = Field(..., description="Whether the action was successful")
    message: str = Field(..., description="Success or error message")
    user_id: str = Field(..., description="User ID that was affected")
    action: str = Field(..., description="Action that was performed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the action was performed")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details about the action")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

class AdminUserSubscriptionDetail(BaseModel):
    """
    Detailed subscription information for a specific user (admin view).
    """
    user_id: str = Field(..., description="User identifier")
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    subscription_tier: SubscriptionTier = Field(..., description="Current subscription tier")
    subscription_status: SubscriptionStatusEnum = Field(..., description="Current subscription status")
    subscription_start_date: Optional[datetime] = Field(None, description="Subscription start date")
    subscription_end_date: Optional[datetime] = Field(None, description="Subscription end date")
    total_memories_saved: int = Field(..., ge=0, description="Total memories saved")
    monthly_summary_pages_used: int = Field(..., ge=0, description="Monthly summary pages used")
    monthly_summary_reset_date: Optional[datetime] = Field(None, description="Last monthly reset date")
    created_at: Optional[datetime] = Field(None, description="User account creation date")
    last_sign_in_at: Optional[datetime] = Field(None, description="Last sign in date")
    
    # Additional admin fields
    days_remaining: Optional[int] = Field(None, description="Days remaining in current subscription")
    is_expired: bool = Field(..., description="Whether subscription is expired")
    
    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    ) 