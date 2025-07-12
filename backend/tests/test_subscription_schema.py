import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

# Import the schema models to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))
from schema.subscription_schema import (
    SubscriptionStatus,
    SubscriptionUpgrade,
    UsageResponse,
    SubscriptionTier,
    SubscriptionStatusEnum
)


class TestSubscriptionStatus:
    """Test SubscriptionStatus schema model"""
    
    def test_subscription_status_valid_data_minimal(self):
        """Unit test: Schema validation accepts valid subscription data with minimal fields"""
        data = {
            "user_id": "user123"
        }
        
        result = SubscriptionStatus(**data)
        
        # Verify required field
        assert result.user_id == "user123"
        
        # Verify defaults are applied
        assert result.subscription_tier == SubscriptionTier.FREE
        assert result.subscription_status == SubscriptionStatusEnum.ACTIVE
        assert result.total_memories_saved == 0
        assert result.monthly_summary_pages_used == 0
        assert result.subscription_start_date is None
        assert result.subscription_end_date is None
        assert result.monthly_summary_reset_date is None
    
    def test_subscription_status_valid_data_complete(self):
        """Unit test: Schema validation accepts valid subscription data with all fields"""
        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        reset_date = datetime(2023, 12, 1, tzinfo=timezone.utc)
        
        data = {
            "user_id": "user123",
            "subscription_tier": "pro",
            "subscription_status": "active",
            "subscription_start_date": start_date,
            "subscription_end_date": end_date,
            "total_memories_saved": 50,
            "monthly_summary_pages_used": 10,
            "monthly_summary_reset_date": reset_date
        }
        
        result = SubscriptionStatus(**data)
        
        assert result.user_id == "user123"
        assert result.subscription_tier == SubscriptionTier.PRO
        assert result.subscription_status == SubscriptionStatusEnum.ACTIVE
        assert result.subscription_start_date == start_date
        assert result.subscription_end_date == end_date
        assert result.total_memories_saved == 50
        assert result.monthly_summary_pages_used == 10
        assert result.monthly_summary_reset_date == reset_date
    
    def test_subscription_status_invalid_tier_values(self):
        """Unit test: Schema validation rejects invalid tier values"""
        data = {
            "user_id": "user123",
            "subscription_tier": "premium"  # Invalid tier
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionStatus(**data)
        
        error = exc_info.value
        assert "subscription_tier" in str(error)
    
    def test_subscription_status_invalid_status_values(self):
        """Unit test: Schema validation rejects invalid status values"""
        data = {
            "user_id": "user123",
            "subscription_status": "pending"  # Invalid status
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionStatus(**data)
        
        error = exc_info.value
        assert "subscription_status" in str(error)
    
    def test_subscription_status_negative_counts(self):
        """Unit test: Schema validation rejects negative memory/summary counts"""
        # Test negative memories
        data = {
            "user_id": "user123",
            "total_memories_saved": -5
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionStatus(**data)
        
        error = exc_info.value
        assert "total_memories_saved" in str(error)
        
        # Test negative summary pages
        data = {
            "user_id": "user123",
            "monthly_summary_pages_used": -2
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionStatus(**data)
        
        error = exc_info.value
        assert "monthly_summary_pages_used" in str(error)
    
    def test_subscription_status_end_date_validation(self):
        """Unit test: Schema validation rejects end date before start date"""
        start_date = datetime(2023, 6, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 1, 1, tzinfo=timezone.utc)  # Before start date
        
        data = {
            "user_id": "user123",
            "subscription_start_date": start_date,
            "subscription_end_date": end_date
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionStatus(**data)
        
        error = exc_info.value
        assert "subscription_end_date must be after subscription_start_date" in str(error)
    
    def test_subscription_status_handles_optional_fields(self):
        """Unit test: Schema validation handles optional fields correctly"""
        # Test with some optional fields
        data = {
            "user_id": "user123",
            "subscription_tier": "pro",
            "total_memories_saved": 25
            # Other fields remain as defaults/None
        }
        
        result = SubscriptionStatus(**data)
        
        assert result.user_id == "user123"
        assert result.subscription_tier == SubscriptionTier.PRO
        assert result.total_memories_saved == 25
        assert result.subscription_start_date is None
        assert result.subscription_end_date is None
        assert result.monthly_summary_reset_date is None


class TestSubscriptionUpgrade:
    """Test SubscriptionUpgrade schema model"""
    
    def test_subscription_upgrade_valid_data_minimal(self):
        """Unit test: Schema validation accepts valid upgrade data with minimal fields"""
        data = {
            "user_id": "user123",
            "target_tier": "pro"
        }
        
        result = SubscriptionUpgrade(**data)
        
        assert result.user_id == "user123"
        assert result.target_tier == SubscriptionTier.PRO
        assert result.payment_method_id is None
        assert result.billing_email is None
    
    def test_subscription_upgrade_valid_data_complete(self):
        """Unit test: Schema validation accepts valid upgrade data with all fields"""
        data = {
            "user_id": "user123",
            "target_tier": "pro",
            "payment_method_id": "pm_1234567890",
            "billing_email": "user@example.com"
        }
        
        result = SubscriptionUpgrade(**data)
        
        assert result.user_id == "user123"
        assert result.target_tier == SubscriptionTier.PRO
        assert result.payment_method_id == "pm_1234567890"
        assert result.billing_email == "user@example.com"
    
    def test_subscription_upgrade_invalid_target_tier(self):
        """Unit test: Schema validation rejects invalid tier values"""
        # Test invalid tier (only PRO upgrades allowed)
        data = {
            "user_id": "user123",
            "target_tier": "free"  # Not allowed for upgrades
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionUpgrade(**data)
        
        error = exc_info.value
        assert "target_tier" in str(error)
        
        # Test completely invalid tier
        data = {
            "user_id": "user123",
            "target_tier": "enterprise"  # Invalid tier
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionUpgrade(**data)
        
        error = exc_info.value
        assert "target_tier" in str(error)
    
    def test_subscription_upgrade_invalid_email(self):
        """Unit test: Schema validation rejects invalid email format"""
        data = {
            "user_id": "user123",
            "target_tier": "pro",
            "billing_email": "invalid-email"  # Invalid email format
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionUpgrade(**data)
        
        error = exc_info.value
        assert "Invalid email format" in str(error)
        
        # Test another invalid email
        data["billing_email"] = "user@"  # Incomplete email
        
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionUpgrade(**data)
    
    def test_subscription_upgrade_valid_email_formats(self):
        """Unit test: Schema validation accepts valid email formats"""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "user+tag@example.org",
            "123@numbers.net"
        ]
        
        for email in valid_emails:
            data = {
                "user_id": "user123",
                "target_tier": "pro",
                "billing_email": email
            }
            
            result = SubscriptionUpgrade(**data)
            assert result.billing_email == email
    
    def test_subscription_upgrade_handles_optional_fields(self):
        """Unit test: Schema validation handles optional fields correctly"""
        data = {
            "user_id": "user123",
            "target_tier": "pro"
            # Optional fields not provided
        }
        
        result = SubscriptionUpgrade(**data)
        
        assert result.user_id == "user123"
        assert result.target_tier == SubscriptionTier.PRO
        assert result.payment_method_id is None
        assert result.billing_email is None


class TestUsageResponse:
    """Test UsageResponse schema model"""
    
    def test_usage_response_valid_data_free_tier(self):
        """Unit test: Schema validation accepts valid usage data for free tier"""
        reset_date = datetime(2023, 12, 1, tzinfo=timezone.utc)
        
        data = {
            "user_id": "user123",
            "subscription_tier": "free",
            "memories_used": 50,
            "memories_limit": 100,
            "summary_pages_used": 3,
            "summary_pages_limit": 5,
            "can_save_memory": True,
            "can_generate_summary": True,
            "monthly_reset_date": reset_date
        }
        
        result = UsageResponse(**data)
        
        assert result.user_id == "user123"
        assert result.subscription_tier == SubscriptionTier.FREE
        assert result.memories_used == 50
        assert result.memories_limit == 100
        assert result.memories_percentage == 50.0  # Auto-calculated
        assert result.summary_pages_used == 3
        assert result.summary_pages_limit == 5
        assert result.summary_pages_percentage == 60.0  # Auto-calculated
        assert result.can_save_memory is True
        assert result.can_generate_summary is True
        assert result.monthly_reset_date == reset_date
    
    def test_usage_response_valid_data_pro_tier_unlimited(self):
        """Unit test: Schema validation accepts valid usage data for pro tier with unlimited memories"""
        data = {
            "user_id": "user123",
            "subscription_tier": "pro",
            "memories_used": 500,
            "memories_limit": -1,  # Unlimited
            "summary_pages_used": 25,
            "summary_pages_limit": 100,
            "can_save_memory": True,
            "can_generate_summary": True
        }
        
        result = UsageResponse(**data)
        
        assert result.user_id == "user123"
        assert result.subscription_tier == SubscriptionTier.PRO
        assert result.memories_used == 500
        assert result.memories_limit == -1
        assert result.memories_percentage is None  # None for unlimited
        assert result.summary_pages_used == 25
        assert result.summary_pages_limit == 100
        assert result.summary_pages_percentage == 25.0  # Auto-calculated
        assert result.can_save_memory is True
        assert result.can_generate_summary is True
    
    def test_usage_response_percentage_calculations(self):
        """Unit test: Schema automatically calculates usage percentages correctly"""
        # Test exact percentages
        data = {
            "user_id": "user123",
            "subscription_tier": "free",
            "memories_used": 75,
            "memories_limit": 100,
            "summary_pages_used": 4,
            "summary_pages_limit": 5,
            "can_save_memory": True,
            "can_generate_summary": True
        }
        
        result = UsageResponse(**data)
        
        assert result.memories_percentage == 75.0
        assert result.summary_pages_percentage == 80.0
        
        # Test rounding
        data.update({
            "memories_used": 33,
            "memories_limit": 100,
            "summary_pages_used": 1,
            "summary_pages_limit": 3
        })
        
        result = UsageResponse(**data)
        
        assert result.memories_percentage == 33.0
        assert result.summary_pages_percentage == 33.3  # Rounded to 1 decimal place
    
    def test_usage_response_invalid_tier_values(self):
        """Unit test: Schema validation rejects invalid tier values"""
        data = {
            "user_id": "user123",
            "subscription_tier": "enterprise",  # Invalid tier
            "memories_used": 50,
            "memories_limit": 100,
            "summary_pages_used": 3,
            "summary_pages_limit": 5,
            "can_save_memory": True,
            "can_generate_summary": True
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UsageResponse(**data)
        
        error = exc_info.value
        assert "subscription_tier" in str(error)
    
    def test_usage_response_negative_values(self):
        """Unit test: Schema validation rejects negative usage values"""
        # Test negative memories used
        data = {
            "user_id": "user123",
            "subscription_tier": "free",
            "memories_used": -5,
            "memories_limit": 100,
            "summary_pages_used": 3,
            "summary_pages_limit": 5,
            "can_save_memory": True,
            "can_generate_summary": True
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UsageResponse(**data)
        
        error = exc_info.value
        assert "memories_used" in str(error)
        
        # Test negative summary pages used
        data.update({
            "memories_used": 50,
            "summary_pages_used": -2
        })
        
        with pytest.raises(ValidationError) as exc_info:
            UsageResponse(**data)
        
        error = exc_info.value
        assert "summary_pages_used" in str(error)
    
    def test_usage_response_percentage_bounds(self):
        """Unit test: Schema validation ensures percentage values are within bounds"""
        # This should be handled automatically by the calculation, but test edge cases
        data = {
            "user_id": "user123",
            "subscription_tier": "free",
            "memories_used": 100,
            "memories_limit": 100,  # Exactly at limit
            "summary_pages_used": 5,
            "summary_pages_limit": 5,  # Exactly at limit
            "can_save_memory": False,
            "can_generate_summary": False
        }
        
        result = UsageResponse(**data)
        
        assert result.memories_percentage == 100.0
        assert result.summary_pages_percentage == 100.0
        assert 0 <= result.memories_percentage <= 100
        assert 0 <= result.summary_pages_percentage <= 100
    
    def test_usage_response_handles_optional_fields(self):
        """Unit test: Schema validation handles optional fields correctly"""
        data = {
            "user_id": "user123",
            "subscription_tier": "free",
            "memories_used": 50,
            "memories_limit": 100,
            "summary_pages_used": 3,
            "summary_pages_limit": 5,
            "can_save_memory": True,
            "can_generate_summary": True
            # monthly_reset_date is optional
        }
        
        result = UsageResponse(**data)
        
        assert result.user_id == "user123"
        assert result.subscription_tier == SubscriptionTier.FREE
        assert result.monthly_reset_date is None
        assert result.memories_percentage == 50.0
        assert result.summary_pages_percentage == 60.0
    
    def test_usage_response_zero_limits_edge_case(self):
        """Unit test: Schema handles edge case of zero limits correctly"""
        data = {
            "user_id": "user123",
            "subscription_tier": "free",
            "memories_used": 0,
            "memories_limit": 0,  # Edge case
            "summary_pages_used": 0,
            "summary_pages_limit": 0,  # Edge case
            "can_save_memory": False,
            "can_generate_summary": False
        }
        
        result = UsageResponse(**data)
        
        # Should not crash and handle gracefully
        # For zero limits, percentage should be None (memories) or 0.0 (summary)
        assert result.memories_percentage is None  # Division by zero case
        assert result.summary_pages_percentage == 0.0


class TestSchemaEnumValues:
    """Test that enums work correctly with the schemas"""
    
    def test_subscription_tier_enum_values(self):
        """Test that SubscriptionTier enum values work in schemas"""
        # Test using enum directly
        data = {
            "user_id": "user123",
            "subscription_tier": SubscriptionTier.PRO
        }
        
        result = SubscriptionStatus(**data)
        assert result.subscription_tier == SubscriptionTier.PRO
        
        # Test using string value
        data["subscription_tier"] = "free"
        result = SubscriptionStatus(**data)
        assert result.subscription_tier == SubscriptionTier.FREE
    
    def test_subscription_status_enum_values(self):
        """Test that SubscriptionStatusEnum values work in schemas"""
        # Test using enum directly
        data = {
            "user_id": "user123",
            "subscription_status": SubscriptionStatusEnum.EXPIRED
        }
        
        result = SubscriptionStatus(**data)
        assert result.subscription_status == SubscriptionStatusEnum.EXPIRED
        
        # Test using string value
        data["subscription_status"] = "cancelled"
        result = SubscriptionStatus(**data)
        assert result.subscription_status == SubscriptionStatusEnum.CANCELLED 