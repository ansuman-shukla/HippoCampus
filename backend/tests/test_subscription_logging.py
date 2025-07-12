import pytest
import json
import tempfile
import os
import logging
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, mock_open, MagicMock

from app.services.subscription_logging_service import (
    SubscriptionLogger, 
    SubscriptionLogFormatter,
    subscription_logger
)

class TestSubscriptionLogFormatter:
    """Test cases for the custom log formatter"""
    
    def test_format_with_subscription_data(self):
        """Unit test: Formatter includes subscription data in structured logs"""
        formatter = SubscriptionLogFormatter()
        
        # Create a mock log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Add subscription-specific attributes
        record.event_type = "upgrade"
        record.user_id = "test_user_123"
        record.subscription_data = {"tier": "pro", "status": "active"}
        record.analytics_data = {"conversion_type": "free_to_pro"}
        record.output_json = True
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["event_type"] == "upgrade"
        assert parsed["user_id"] == "test_user_123"
        assert parsed["subscription_data"]["tier"] == "pro"
        assert parsed["analytics_data"]["conversion_type"] == "free_to_pro"
        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
    
    def test_format_console_output(self):
        """Unit test: Formatter provides human-readable console output"""
        formatter = SubscriptionLogFormatter()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test console message",
            args=(),
            exc_info=None
        )
        
        record.output_json = False
        
        # Should use parent formatter for console output
        formatted = formatter.format(record)
        assert "Test console message" in formatted
        assert not formatted.startswith("{")  # Not JSON

class TestSubscriptionLogger:
    """Test cases for the subscription logging service"""
    
    @pytest.fixture
    def temp_logs_dir(self):
        """Create temporary logs directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            yield tmpdir
            os.chdir(original_cwd)
    
    @pytest.fixture
    def test_logger(self, temp_logs_dir):
        """Create a test logger instance"""
        return SubscriptionLogger()
    
    def test_logger_initialization(self, temp_logs_dir):
        """Unit test: Logger initializes with proper handlers and formatters"""
        logger_instance = SubscriptionLogger()
        
        # Verify logger has handlers (console, file, error handlers)
        assert len(logger_instance.logger.handlers) >= 3, "Logger should have console, file, and error handlers"
        
        # Verify log level is set correctly
        assert logger_instance.logger.level == logging.INFO
        
        # Verify logger has the expected name
        assert logger_instance.logger.name == "subscription_events"
        
        # Verify propagation is disabled to avoid duplicates
        assert logger_instance.logger.propagate is False
    
    def test_log_upgrade_event(self, test_logger, temp_logs_dir):
        """Unit test: Upgrade events are logged correctly with proper data structure"""
        test_logger.log_upgrade_event(
            user_id="user_123",
            previous_tier="free",
            new_tier="pro",
            method="user",
            payment_method="stripe",
            amount=8.0
        )
        
        # Verify logs were created
        logs_dir = Path("logs")
        event_log = logs_dir / "subscription_events.jsonl"
        
        # Check if log file exists and has content
        if event_log.exists():
            with open(event_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    log_data = json.loads(last_line)
                    
                    assert log_data["event_type"] == "upgrade"
                    assert log_data["user_id"] == "user_123"
                    assert log_data["subscription_data"]["previous_tier"] == "free"
                    assert log_data["subscription_data"]["new_tier"] == "pro"
                    assert log_data["analytics_data"]["revenue_impact"] == 8.0
    
    def test_log_downgrade_event(self, test_logger, temp_logs_dir):
        """Unit test: Downgrade events are logged correctly with churn data"""
        test_logger.log_downgrade_event(
            user_id="user_456",
            previous_tier="pro",
            new_tier="free",
            method="user",
            reason="cost_concerns"
        )
        
        logs_dir = Path("logs")
        event_log = logs_dir / "subscription_events.jsonl"
        
        if event_log.exists():
            with open(event_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    log_data = json.loads(last_line)
                    
                    assert log_data["event_type"] == "downgrade"
                    assert log_data["user_id"] == "user_456"
                    assert log_data["analytics_data"]["churn_reason"] == "cost_concerns"
    
    def test_log_limit_breach_event(self, test_logger, temp_logs_dir):
        """Unit test: Limit breach events are logged with usage analytics"""
        test_logger.log_limit_breach_event(
            user_id="user_789",
            limit_type="memory",
            current_usage=100,
            limit_value=100,
            tier="free"
        )
        
        logs_dir = Path("logs")
        event_log = logs_dir / "subscription_events.jsonl"
        
        if event_log.exists():
            with open(event_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    log_data = json.loads(last_line)
                    
                    assert log_data["event_type"] == "limit_breach"
                    assert log_data["subscription_data"]["limit_type"] == "memory"
                    assert log_data["analytics_data"]["usage_percentage"] == 100.0
                    assert log_data["analytics_data"]["potential_conversion_trigger"] is True
    
    def test_log_grace_period_event(self, test_logger, temp_logs_dir):
        """Unit test: Grace period events are logged with retention data"""
        test_logger.log_grace_period_event(
            user_id="user_grace",
            grace_action="entered",
            days_remaining=7
        )
        
        logs_dir = Path("logs")
        event_log = logs_dir / "subscription_events.jsonl"
        
        if event_log.exists():
            with open(event_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    log_data = json.loads(last_line)
                    
                    assert log_data["event_type"] == "grace_period"
                    assert log_data["subscription_data"]["grace_action"] == "entered"
                    assert log_data["analytics_data"]["retention_opportunity"] is True
    
    def test_log_error_event(self, test_logger, temp_logs_dir):
        """Unit test: Error events are logged with proper error information"""
        test_error = Exception("Test subscription error")
        
        test_logger.log_error_event(
            user_id="user_error",
            error_type="payment_failed",
            error_message="Payment processing failed",
            error=test_error,
            context={"payment_method": "stripe", "amount": 8.0}
        )
        
        logs_dir = Path("logs")
        error_log = logs_dir / "subscription_errors.jsonl"
        
        if error_log.exists():
            with open(error_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    log_data = json.loads(last_line)
                    
                    assert log_data["event_type"] == "error"
                    assert log_data["level"] == "ERROR"
                    assert log_data["analytics_data"]["requires_investigation"] is True


class TestSubscriptionLoggingIntegration:
    """Integration tests for subscription logging across the system"""
    
    @pytest.fixture
    def temp_logs_dir(self):
        """Create temporary logs directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            yield tmpdir
            os.chdir(original_cwd)
    
    def test_log_format_consistency(self, temp_logs_dir):
        """Integration test: All log events follow consistent format structure"""
        logger_instance = SubscriptionLogger()
        
        # Log various event types
        events = [
            ("upgrade", lambda: logger_instance.log_upgrade_event("user1", "free", "pro")),
            ("downgrade", lambda: logger_instance.log_downgrade_event("user2", "pro", "free")),
            ("limit_breach", lambda: logger_instance.log_limit_breach_event("user3", "memory", 100, 100, "free")),
            ("grace_period", lambda: logger_instance.log_grace_period_event("user4", "entered", 7)),
            ("reactivation", lambda: logger_instance.log_reactivation_event("user5", "expired", True, "stripe")),
            ("monthly_reset", lambda: logger_instance.log_monthly_reset_event(1000, 5000, 2.5))
        ]
        
        for event_type, log_func in events:
            log_func()
        
        # Verify all logs have consistent structure
        logs_dir = Path("logs")
        event_log = logs_dir / "subscription_events.jsonl"
        
        if event_log.exists():
            with open(event_log, 'r') as f:
                lines = f.readlines()
                
                for line in lines:
                    log_data = json.loads(line)
                    
                    # Verify required fields exist
                    assert "timestamp" in log_data
                    assert "level" in log_data
                    assert "event_type" in log_data
                    assert "user_id" in log_data
                    assert "message" in log_data
                    assert "analytics_data" in log_data
                    
                    # Verify timestamp format
                    timestamp = datetime.fromisoformat(log_data["timestamp"].replace('Z', '+00:00'))
                    assert timestamp.tzinfo == timezone.utc
    
    def test_log_levels_appropriate(self, temp_logs_dir):
        """Integration test: Log levels are set appropriately for different event types"""
        logger_instance = SubscriptionLogger()
        
        # Log events with different severity levels
        logger_instance.log_upgrade_event("user1", "free", "pro")  # INFO
        logger_instance.log_limit_breach_event("user2", "memory", 100, 100, "free")  # WARNING
        logger_instance.log_error_event("user3", "payment_failed", "Error", Exception("test"), {})  # ERROR
        
        logs_dir = Path("logs")
        event_log = logs_dir / "subscription_events.jsonl"
        error_log = logs_dir / "subscription_errors.jsonl"
        
        if event_log.exists():
            with open(event_log, 'r') as f:
                lines = f.readlines()
                
                if len(lines) >= 2:
                    # Check upgrade event (INFO level)
                    upgrade_log = json.loads(lines[-2])
                    assert upgrade_log["level"] == "INFO"
                    
                    # Check limit breach (WARNING level)
                    breach_log = json.loads(lines[-1])
                    assert breach_log["level"] == "WARNING"
        
        # Error events should also go to error log
        if error_log.exists():
            with open(error_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    error_log_data = json.loads(lines[-1])
                    assert error_log_data["level"] == "ERROR"
    
    def test_log_handler_configuration(self, temp_logs_dir):
        """Integration test: Log handlers are properly configured"""
        logger_instance = SubscriptionLogger()
        
        # Verify we have the expected number of handlers
        handlers = logger_instance.logger.handlers
        assert len(handlers) >= 3, "Should have console, file, and error handlers"
        
        # Verify handler types
        handler_types = [type(handler).__name__ for handler in handlers]
        assert "StreamHandler" in handler_types, "Should have console handler"
        assert "RotatingFileHandler" in handler_types, "Should have rotating file handlers"
        
        # Verify that different handlers have different log levels
        log_levels = [handler.level for handler in handlers]
        assert logging.INFO in log_levels, "Should have INFO level handler"
        assert logging.ERROR in log_levels, "Should have ERROR level handler"
        
        # Verify formatters are set
        for handler in handlers:
            assert handler.formatter is not None, "All handlers should have formatters"


class TestAnalyticsDataParsing:
    """Test cases for analytics data structure and parsing"""
    
    @pytest.fixture
    def temp_logs_dir(self):
        """Create temporary logs directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            yield tmpdir
            os.chdir(original_cwd)
    
    def test_analytics_data_structure(self, temp_logs_dir):
        """Monitoring test: Logs can be parsed by analytics tools with proper JSON structure"""
        logger_instance = SubscriptionLogger()
        
        # Generate various subscription events
        logger_instance.log_upgrade_event(
            user_id="analytics_user_1",
            previous_tier="free",
            new_tier="pro",
            method="user",
            payment_method="stripe",
            amount=8.0
        )
        
        logger_instance.log_limit_breach_event(
            user_id="analytics_user_2",
            limit_type="summary",
            current_usage=5,
            limit_value=5,
            tier="free",
            pages_requested=3
        )
        
        logs_dir = Path("logs")
        event_log = logs_dir / "subscription_events.jsonl"
        
        if event_log.exists():
            with open(event_log, 'r') as f:
                lines = f.readlines()
                
                for line in lines:
                    # Verify each line is valid JSON
                    log_data = json.loads(line)
                    
                    # Verify analytics data structure
                    analytics_data = log_data.get("analytics_data", {})
                    
                    # Common analytics fields
                    assert "event_timestamp" in analytics_data
                    assert "admin_initiated" in analytics_data
                    
                    # Event-specific analytics fields
                    if log_data["event_type"] == "upgrade":
                        assert "conversion_type" in analytics_data
                        assert "revenue_impact" in analytics_data
                        assert analytics_data["revenue_impact"] == 8.0
                    
                    elif log_data["event_type"] == "limit_breach":
                        assert "limit_breach_type" in analytics_data
                        assert "usage_percentage" in analytics_data
                        assert "potential_conversion_trigger" in analytics_data
                        assert analytics_data["potential_conversion_trigger"] is True
    
    def test_analytics_timestamp_format(self, temp_logs_dir):
        """Monitoring test: Timestamps are in ISO format for analytics processing"""
        logger_instance = SubscriptionLogger()
        
        logger_instance.log_monthly_reset_event(
            total_users_reset=500,
            summary_pages_reset=2500,
            execution_time=1.23
        )
        
        logs_dir = Path("logs")
        event_log = logs_dir / "subscription_events.jsonl"
        
        if event_log.exists():
            with open(event_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    log_data = json.loads(lines[-1])
                    
                    # Verify main timestamp
                    timestamp = log_data["timestamp"]
                    parsed_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    assert parsed_timestamp.tzinfo == timezone.utc
                    
                    # Verify analytics timestamp
                    analytics_timestamp = log_data["analytics_data"]["event_timestamp"]
                    parsed_analytics_timestamp = datetime.fromisoformat(analytics_timestamp.replace('Z', '+00:00'))
                    assert parsed_analytics_timestamp.tzinfo == timezone.utc
    
    def test_structured_data_completeness(self, temp_logs_dir):
        """Monitoring test: All required analytics fields are present for different event types"""
        logger_instance = SubscriptionLogger()
        
        # Test all major event types for completeness
        test_events = [
            {
                "type": "upgrade",
                "func": lambda: logger_instance.log_upgrade_event("user1", "free", "pro", amount=8.0),
                "required_fields": ["conversion_type", "revenue_impact", "upgrade_method"]
            },
            {
                "type": "downgrade", 
                "func": lambda: logger_instance.log_downgrade_event("user2", "pro", "free", reason="cost"),
                "required_fields": ["churn_type", "churn_reason", "downgrade_method"]
            },
            {
                "type": "limit_breach",
                "func": lambda: logger_instance.log_limit_breach_event("user3", "memory", 100, 100, "free"),
                "required_fields": ["limit_breach_type", "usage_percentage", "potential_conversion_trigger"]
            },
            {
                "type": "grace_period",
                "func": lambda: logger_instance.log_grace_period_event("user4", "entered", 7),
                "required_fields": ["grace_period_stage", "retention_opportunity"]
            }
        ]
        
        for event in test_events:
            event["func"]()
        
        logs_dir = Path("logs")
        event_log = logs_dir / "subscription_events.jsonl"
        
        if event_log.exists():
            with open(event_log, 'r') as f:
                lines = f.readlines()
                
                # Match events with their required fields
                for i, line in enumerate(lines[-len(test_events):]):
                    log_data = json.loads(line)
                    expected_event = test_events[i]
                    
                    assert log_data["event_type"] == expected_event["type"]
                    
                    analytics_data = log_data["analytics_data"]
                    for required_field in expected_event["required_fields"]:
                        assert required_field in analytics_data, f"Missing {required_field} in {expected_event['type']} event"


class TestGlobalLoggerInstance:
    """Test cases for the global subscription logger instance"""
    
    def test_global_logger_singleton(self):
        """Unit test: Global subscription logger is properly initialized"""
        # Import the global instance
        from app.services.subscription_logging_service import subscription_logger
        
        assert subscription_logger is not None
        assert isinstance(subscription_logger, SubscriptionLogger)
        assert hasattr(subscription_logger, 'log_upgrade_event')
        assert hasattr(subscription_logger, 'log_downgrade_event')
        assert hasattr(subscription_logger, 'log_limit_breach_event')
    
    def test_global_logger_methods_callable(self):
        """Unit test: All logging methods are callable on global instance"""
        from app.services.subscription_logging_service import subscription_logger
        
        # Test that methods exist and are callable
        assert callable(subscription_logger.log_upgrade_event)
        assert callable(subscription_logger.log_downgrade_event) 
        assert callable(subscription_logger.log_limit_breach_event)
        assert callable(subscription_logger.log_grace_period_event)
        assert callable(subscription_logger.log_reactivation_event)
        assert callable(subscription_logger.log_monthly_reset_event)
        assert callable(subscription_logger.log_error_event)
        assert callable(subscription_logger.log_subscription_event) 