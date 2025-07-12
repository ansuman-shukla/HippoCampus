from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class SubscriptionTier(str, Enum):
    """Enumeration for subscription tiers"""
    FREE = "free"
    PRO = "pro"

class SubscriptionStatusEnum(str, Enum):
    """Enumeration for subscription status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class SubscriptionStatus(BaseModel):
    """
    Pydantic model for subscription status response.
    Returns current subscription information for a user.
    """
    user_id: str = Field(..., description="User identifier")
    subscription_tier: SubscriptionTier = Field(default=SubscriptionTier.FREE, description="Current subscription tier")
    subscription_status: SubscriptionStatusEnum = Field(default=SubscriptionStatusEnum.ACTIVE, description="Current subscription status")
    subscription_start_date: Optional[datetime] = Field(None, description="Subscription start date")
    subscription_end_date: Optional[datetime] = Field(None, description="Subscription end date")
    total_memories_saved: int = Field(default=0, ge=0, description="Total number of memories saved")
    monthly_summary_pages_used: int = Field(default=0, ge=0, description="Number of summary pages used this month")
    monthly_summary_reset_date: Optional[datetime] = Field(None, description="Date when monthly summary count was last reset")

    @field_validator('subscription_end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        """Ensure end date is after start date if both are provided"""
        if v and info.data.get('subscription_start_date'):
            if v <= info.data['subscription_start_date']:
                raise ValueError('subscription_end_date must be after subscription_start_date')
        return v

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

class SubscriptionUpgrade(BaseModel):
    """
    Pydantic model for subscription upgrade requests.
    Used when a user wants to upgrade their subscription.
    """
    user_id: str = Field(..., description="User identifier")
    target_tier: Literal[SubscriptionTier.PRO] = Field(..., description="Target subscription tier (only PRO upgrades supported)")
    payment_method_id: Optional[str] = Field(None, description="Payment method identifier from payment processor")
    billing_email: Optional[str] = Field(None, description="Email for billing notifications")
    
    @field_validator('billing_email')
    @classmethod
    def validate_email_format(cls, v):
        """Basic email validation"""
        if v is not None:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        return v

    model_config = ConfigDict(use_enum_values=True)

class UsageResponse(BaseModel):
    """
    Pydantic model for usage statistics response.
    Returns detailed usage information and limits for a user.
    """
    user_id: str = Field(..., description="User identifier")
    subscription_tier: SubscriptionTier = Field(..., description="Current subscription tier")
    
    # Memory usage
    memories_used: int = Field(..., ge=0, description="Number of memories currently saved")
    memories_limit: int = Field(..., description="Maximum memories allowed (-1 for unlimited)")
    
    # Summary usage
    summary_pages_used: int = Field(..., ge=0, description="Summary pages used this month")
    summary_pages_limit: int = Field(..., ge=0, description="Monthly summary pages limit")
    
    # Additional info
    can_save_memory: bool = Field(..., description="Whether user can save more memories")
    can_generate_summary: bool = Field(..., description="Whether user can generate summaries")
    monthly_reset_date: Optional[datetime] = Field(None, description="When monthly limits will reset")

    @computed_field
    @property
    def memories_percentage(self) -> Optional[float]:
        """Calculate memory usage percentage"""
        if self.memories_limit == -1:  # Unlimited
            return None
        elif self.memories_limit > 0:
            return round((self.memories_used / self.memories_limit) * 100, 1)
        return None

    @computed_field
    @property
    def summary_pages_percentage(self) -> float:
        """Calculate summary usage percentage"""
        if self.summary_pages_limit > 0:
            return round((self.summary_pages_used / self.summary_pages_limit) * 100, 1)
        return 0.0

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    ) 