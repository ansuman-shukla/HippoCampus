import logging
import logging.handlers
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path
import os

class SubscriptionLogFormatter(logging.Formatter):
    """
    Custom formatter for subscription events that outputs structured JSON logs
    for analytics parsing while maintaining human-readable console logs.
    """
    
    def format(self, record):
        # Create structured log entry for analytics
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event_type": getattr(record, 'event_type', 'unknown'),
            "user_id": getattr(record, 'user_id', None),
            "message": record.getMessage()
        }
        
        # Add subscription-specific data if present
        if hasattr(record, 'subscription_data'):
            log_entry["subscription_data"] = record.subscription_data
            
        if hasattr(record, 'analytics_data'):
            log_entry["analytics_data"] = record.analytics_data
        
        # Add error information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # For file logging, output structured JSON
        if getattr(record, 'output_json', False):
            return json.dumps(log_entry)
        
        # For console logging, use the existing emoji-based format
        return super().format(record)

class SubscriptionLogger:
    """
    Centralized logging service for subscription events following existing patterns.
    Provides structured logging for analytics while maintaining readable console output.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("subscription_events")
        self.console_logger = logging.getLogger("subscription_console")
        
        # Only setup if not already configured (avoid duplicate handlers)
        if not self.logger.handlers:
            self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging handlers with rotation and structured format"""
        
        # Ensure logs directory exists
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Console handler with emoji format (follows main.py pattern)
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        
        # File handler for structured analytics logs with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            "logs/subscription_events.jsonl",
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        file_formatter = SubscriptionLogFormatter()
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)
        
        # Error file handler for error-level events
        error_handler = logging.handlers.RotatingFileHandler(
            "logs/subscription_errors.jsonl",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setFormatter(file_formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Configure main subscription logger
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        
        # Prevent log propagation to avoid duplicates
        self.logger.propagate = False
    
    def log_subscription_event(self, 
                             event_type: str, 
                             user_id: str, 
                             message: str,
                             level: str = "INFO",
                             subscription_data: Optional[Dict[str, Any]] = None,
                             analytics_data: Optional[Dict[str, Any]] = None,
                             admin_user: Optional[str] = None,
                             error: Optional[Exception] = None):
        """
        Log a subscription event with structured data for analytics.
        
        Args:
            event_type: Type of event (upgrade, downgrade, limit_breach, etc.)
            user_id: The affected user ID
            message: Human-readable message following emoji patterns
            level: Log level (INFO, WARNING, ERROR)
            subscription_data: Subscription-related data for analytics
            analytics_data: Additional analytics metadata
            admin_user: Admin user email if action was performed by admin
            error: Exception object if this is an error event
        """
        
        # Create log record with structured data
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Create console log with emoji format (following main.py patterns)
        if log_level == logging.ERROR:
            console_msg = f"❌ SUBSCRIPTION {event_type.upper()}: {message}"
        elif log_level == logging.WARNING:
            console_msg = f"⚠️ SUBSCRIPTION {event_type.upper()}: {message}"
        elif event_type == "upgrade":
            console_msg = f"⬆️ SUBSCRIPTION UPGRADE: {message}"
        elif event_type == "downgrade":
            console_msg = f"⬇️ SUBSCRIPTION DOWNGRADE: {message}"
        elif event_type == "limit_breach":
            console_msg = f"🚫 SUBSCRIPTION LIMIT: {message}"
        elif event_type == "grace_period":
            console_msg = f"⏳ SUBSCRIPTION GRACE: {message}"
        elif event_type == "reactivation":
            console_msg = f"🔄 SUBSCRIPTION REACTIVATION: {message}"
        elif event_type == "monthly_reset":
            console_msg = f"🔄 SUBSCRIPTION RESET: {message}"
        else:
            console_msg = f"📊 SUBSCRIPTION {event_type.upper()}: {message}"
        
        # Add user context following main.py pattern
        console_msg += f"\n   └─ User ID: {user_id}"
        if admin_user:
            console_msg += f"\n   └─ Admin: {admin_user}"
        
        # Log to console
        extra_data = {
            'event_type': event_type,
            'user_id': user_id,
            'output_json': False
        }
        
        if subscription_data:
            extra_data['subscription_data'] = subscription_data
        if analytics_data:
            extra_data['analytics_data'] = analytics_data
        
        if error:
            self.logger.log(log_level, console_msg, exc_info=error, extra=extra_data)
        else:
            self.logger.log(log_level, console_msg, extra=extra_data)
        
        # Log structured data for analytics
        analytics_extra = extra_data.copy()
        analytics_extra['output_json'] = True
        analytics_extra['analytics_data'] = analytics_data or {}
        analytics_extra['analytics_data'].update({
            'event_timestamp': datetime.now(timezone.utc).isoformat(),
            'admin_initiated': bool(admin_user),
            'admin_user': admin_user
        })
        
        if error:
            self.logger.log(log_level, message, exc_info=error, extra=analytics_extra)
        else:
            self.logger.log(log_level, message, extra=analytics_extra)
    
    def log_upgrade_event(self, user_id: str, previous_tier: str, new_tier: str, 
                         method: str = "user", admin_user: Optional[str] = None,
                         payment_method: Optional[str] = None, amount: Optional[float] = None):
        """Log subscription upgrade event"""
        
        message = f"User upgraded from {previous_tier} to {new_tier}"
        if admin_user:
            message += f" (admin action by {admin_user})"
        
        subscription_data = {
            "previous_tier": previous_tier,
            "new_tier": new_tier,
            "upgrade_method": method,
            "payment_method": payment_method,
            "amount": amount
        }
        
        analytics_data = {
            "conversion_type": f"{previous_tier}_to_{new_tier}",
            "upgrade_method": method,
            "revenue_impact": amount or 0.0
        }
        
        self.log_subscription_event(
            event_type="upgrade",
            user_id=user_id,
            message=message,
            subscription_data=subscription_data,
            analytics_data=analytics_data,
            admin_user=admin_user
        )
    
    def log_downgrade_event(self, user_id: str, previous_tier: str, new_tier: str,
                          method: str = "user", admin_user: Optional[str] = None,
                          reason: Optional[str] = None):
        """Log subscription downgrade event"""
        
        message = f"User downgraded from {previous_tier} to {new_tier}"
        if reason:
            message += f" (reason: {reason})"
        if admin_user:
            message += f" (admin action by {admin_user})"
        
        subscription_data = {
            "previous_tier": previous_tier,
            "new_tier": new_tier,
            "downgrade_method": method,
            "reason": reason
        }
        
        analytics_data = {
            "churn_type": f"{previous_tier}_to_{new_tier}",
            "downgrade_method": method,
            "churn_reason": reason
        }
        
        self.log_subscription_event(
            event_type="downgrade",
            user_id=user_id,
            message=message,
            subscription_data=subscription_data,
            analytics_data=analytics_data,
            admin_user=admin_user
        )
    
    def log_limit_breach_event(self, user_id: str, limit_type: str, 
                             current_usage: int, limit_value: int,
                             tier: str, pages_requested: Optional[int] = None):
        """Log subscription limit breach event"""
        
        if limit_type == "memory":
            message = f"Memory save limit exceeded: {current_usage}/{limit_value} saves"
        elif limit_type == "summary":
            pages_msg = f" (requested {pages_requested} pages)" if pages_requested else ""
            message = f"Summary page limit exceeded: {current_usage}/{limit_value} pages{pages_msg}"
        else:
            message = f"Subscription limit exceeded for {limit_type}: {current_usage}/{limit_value}"
        
        subscription_data = {
            "limit_type": limit_type,
            "current_usage": current_usage,
            "limit_value": limit_value,
            "subscription_tier": tier,
            "pages_requested": pages_requested
        }
        
        analytics_data = {
            "limit_breach_type": limit_type,
            "usage_percentage": (current_usage / limit_value * 100) if limit_value > 0 else 100,
            "subscription_tier": tier,
            "potential_conversion_trigger": True
        }
        
        self.log_subscription_event(
            event_type="limit_breach",
            user_id=user_id,
            message=message,
            level="WARNING",
            subscription_data=subscription_data,
            analytics_data=analytics_data
        )
    
    def log_grace_period_event(self, user_id: str, grace_action: str, 
                             days_remaining: Optional[int] = None,
                             usage_data: Optional[Dict[str, int]] = None):
        """Log grace period events"""
        
        if grace_action == "entered":
            message = f"User entered grace period ({days_remaining} days remaining)"
        elif grace_action == "usage":
            message = f"Grace period usage: {usage_data}"
        elif grace_action == "expired":
            message = "Grace period expired, downgrading to free tier"
        else:
            message = f"Grace period event: {grace_action}"
        
        subscription_data = {
            "grace_action": grace_action,
            "days_remaining": days_remaining,
            "grace_usage": usage_data
        }
        
        analytics_data = {
            "grace_period_stage": grace_action,
            "retention_opportunity": grace_action in ["entered", "usage"]
        }
        
        self.log_subscription_event(
            event_type="grace_period",
            user_id=user_id,
            message=message,
            subscription_data=subscription_data,
            analytics_data=analytics_data
        )
    
    def log_reactivation_event(self, user_id: str, previous_status: str,
                             was_in_grace: bool, payment_method: str):
        """Log subscription reactivation event"""
        
        message = f"Subscription reactivated from {previous_status}"
        if was_in_grace:
            message += " (was in grace period)"
        
        subscription_data = {
            "previous_status": previous_status,
            "was_in_grace_period": was_in_grace,
            "payment_method": payment_method
        }
        
        analytics_data = {
            "reactivation_type": "grace_period" if was_in_grace else "standard",
            "win_back_success": True
        }
        
        self.log_subscription_event(
            event_type="reactivation",
            user_id=user_id,
            message=message,
            subscription_data=subscription_data,
            analytics_data=analytics_data
        )
    
    def log_monthly_reset_event(self, total_users_reset: int, 
                              summary_pages_reset: int,
                              execution_time: float):
        """Log monthly reset batch operation"""
        
        message = f"Monthly reset completed: {total_users_reset} users, {summary_pages_reset} total pages reset"
        
        analytics_data = {
            "users_affected": total_users_reset,
            "total_pages_reset": summary_pages_reset,
            "execution_time_seconds": execution_time,
            "operation_type": "batch_reset"
        }
        
        self.log_subscription_event(
            event_type="monthly_reset",
            user_id="system",
            message=message,
            analytics_data=analytics_data
        )
    
    def log_error_event(self, user_id: str, error_type: str, 
                       error_message: str, error: Exception,
                       context: Optional[Dict[str, Any]] = None):
        """Log subscription-related errors"""
        
        message = f"Subscription error ({error_type}): {error_message}"
        
        subscription_data = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context
        }
        
        analytics_data = {
            "error_category": "subscription",
            "error_type": error_type,
            "requires_investigation": True
        }
        
        self.log_subscription_event(
            event_type="error",
            user_id=user_id,
            message=message,
            level="ERROR",
            subscription_data=subscription_data,
            analytics_data=analytics_data,
            error=error
        )

# Global subscription logger instance
subscription_logger = SubscriptionLogger() 