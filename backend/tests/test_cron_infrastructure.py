import pytest
import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os

from app.services.cron_service import CronService, cron_service, reset_cron_metrics
from app.services.background_jobs import background_jobs_service
import logging

# Suppress APScheduler debug logs during tests
logging.getLogger('apscheduler').setLevel(logging.WARNING)

class TestCronServiceInitialization:
    """Test CRON service initialization and configuration"""
    
    def test_cron_service_initialization(self):
        """Test that CRON service initializes correctly with proper configuration"""
        # Create temporary database for test
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as f:
            temp_db = f.name
        
        try:
            service = CronService(db_path=temp_db)
            
            # Verify initialization
            assert service.db_path == temp_db
            assert service.scheduler is not None
            assert service.is_running is False
            
            # Verify metrics structure through get_job_metrics
            metrics = service.get_job_metrics()
            job_metrics = metrics["metrics"]
            assert "jobs_executed" in job_metrics
            assert "jobs_failed" in job_metrics
            assert "jobs_missed" in job_metrics
            assert "last_execution_times" in job_metrics
            assert "execution_history" in job_metrics
            
            # Verify scheduler configuration
            assert str(service.scheduler.timezone) == "UTC"
            assert hasattr(service.scheduler, '_executors')
            assert hasattr(service.scheduler, '_jobstores')
            
        finally:
            if os.path.exists(temp_db):
                os.unlink(temp_db)
    
    def test_scheduler_configuration(self):
        """Test that scheduler is configured with proper settings"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as f:
            temp_db = f.name
        
        try:
            service = CronService(db_path=temp_db)
            
            # Check job defaults
            job_defaults = service.scheduler._job_defaults
            assert job_defaults['coalesce'] is True
            assert job_defaults['max_instances'] == 1
            assert job_defaults['misfire_grace_time'] == 300
            
            # Check timezone
            assert str(service.scheduler.timezone) == "UTC"
            
        finally:
            if os.path.exists(temp_db):
                os.unlink(temp_db)

class TestCronJobScheduling:
    """Test CRON job scheduling functionality"""
    
    @pytest.fixture
    def cron_service_test(self):
        """Create a test CRON service instance"""
        # Reset metrics before each test
        reset_cron_metrics()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as f:
            temp_db = f.name
        
        service = CronService(db_path=temp_db)
        yield service
        
        # Cleanup
        try:
            if service.is_running:
                service.stop_scheduler()
        except:
            pass
        
        # Use try/except for file cleanup on Windows
        try:
            if os.path.exists(temp_db):
                os.unlink(temp_db)
        except (PermissionError, OSError):
            pass  # File may be locked on Windows, ignore cleanup error
    
    def test_start_scheduler(self, cron_service_test):
        """Integration test: CRON jobs are scheduled correctly"""
        service = cron_service_test
        
        # Start scheduler
        result = service.start_scheduler()
        
        # Verify startup
        assert result["status"] == "started"
        assert result["jobs_registered"] == 2
        assert service.is_running is True
        
        # Verify jobs are registered
        jobs = service.scheduler.get_jobs()
        assert len(jobs) == 2
        
        job_ids = [job.id for job in jobs]
        assert "monthly_summary_reset" in job_ids
        assert "daily_expiry_check" in job_ids
        
        # Verify job triggers
        for job in jobs:
            if job.id == "monthly_summary_reset":
                # Monthly job should run on 1st of month at 00:00 UTC
                assert "day='1'" in str(job.trigger)
                assert "hour='0'" in str(job.trigger)
                assert "minute='0'" in str(job.trigger)
            elif job.id == "daily_expiry_check":
                # Daily job should run at 00:00 UTC
                assert "hour='0'" in str(job.trigger) 
                assert "minute='0'" in str(job.trigger)
    
    def test_stop_scheduler(self, cron_service_test):
        """Test scheduler can be stopped gracefully"""
        service = cron_service_test
        
        # Start then stop
        start_result = service.start_scheduler()
        assert start_result["status"] == "started"
        
        stop_result = service.stop_scheduler()
        assert stop_result["status"] == "stopped"
        assert service.is_running is False
    
    def test_scheduler_already_running(self, cron_service_test):
        """Test starting scheduler when already running"""
        service = cron_service_test
        
        # Start scheduler
        result1 = service.start_scheduler()
        assert result1["status"] == "started"
        
        # Try to start again
        result2 = service.start_scheduler()
        assert result2["status"] == "already_running"
    
    def test_scheduler_already_stopped(self, cron_service_test):
        """Test stopping scheduler when already stopped"""
        service = cron_service_test
        
        # Try to stop when not running
        result = service.stop_scheduler()
        assert result["status"] == "already_stopped"

class TestCronJobExecution:
    """Test CRON job execution and monitoring"""
    
    @pytest.fixture
    def running_cron_service(self):
        """Create and start a CRON service for testing"""
        # Reset metrics before each test
        reset_cron_metrics()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as f:
            temp_db = f.name
        
        service = CronService(db_path=temp_db)
        service.start_scheduler()
        yield service
        
        # Cleanup
        try:
            service.stop_scheduler()
        except:
            pass
        
        # Use try/except for file cleanup on Windows
        try:
            if os.path.exists(temp_db):
                os.unlink(temp_db)
        except (PermissionError, OSError):
            pass  # File may be locked on Windows, ignore cleanup error
    
    @patch('app.services.background_jobs.background_jobs_service.reset_monthly_summaries')
    def test_force_execute_monthly_reset(self, mock_reset, running_cron_service):
        """Integration test: Monthly reset job executes on schedule"""
        service = running_cron_service
        
        # Mock successful execution
        mock_reset.return_value = {
            "job_name": "reset_monthly_summaries",
            "status": "success",
            "users_updated": 5,
            "reset_date": datetime.now(timezone.utc),
            "operation_time": datetime.now(timezone.utc),
            "duration_seconds": 1.5
        }
        
        # Force execute the job
        result = service.force_execute_job("monthly_summary_reset")
        
        # Verify execution
        assert result["status"] == "success"
        assert result["job_id"] == "monthly_summary_reset"
        mock_reset.assert_called_once()
        
        # Verify metrics were updated
        metrics = service.get_job_metrics()
        job_metrics = metrics["metrics"]
        assert job_metrics["jobs_executed"] == 1
        assert job_metrics["jobs_failed"] == 0
        assert "monthly_summary_reset" in job_metrics["last_execution_times"]
        
        last_exec = job_metrics["last_execution_times"]["monthly_summary_reset"]
        assert last_exec["status"] == "success"
        assert last_exec["duration_seconds"] >= 0
    
    @patch('app.services.background_jobs.background_jobs_service.check_subscription_expiry')
    def test_force_execute_expiry_check(self, mock_expiry, running_cron_service):
        """Integration test: Daily expiry check executes on schedule"""
        service = running_cron_service
        
        # Mock successful execution
        mock_expiry.return_value = {
            "job_name": "check_subscription_expiry",
            "status": "success",
            "expired_users_found": 2,
            "users_downgraded": 2,
            "downgraded_users": [
                {"user_id": "user1", "email": "user1@test.com"},
                {"user_id": "user2", "email": "user2@test.com"}
            ],
            "duration_seconds": 0.8
        }
        
        # Force execute the job
        result = service.force_execute_job("daily_expiry_check")
        
        # Verify execution
        assert result["status"] == "success"
        assert result["job_id"] == "daily_expiry_check"
        mock_expiry.assert_called_once()
        
        # Verify metrics were updated
        metrics = service.get_job_metrics()
        job_metrics = metrics["metrics"]
        assert job_metrics["jobs_executed"] == 1
        assert job_metrics["jobs_failed"] == 0
        assert "daily_expiry_check" in job_metrics["last_execution_times"]
    
    def test_force_execute_invalid_job(self, running_cron_service):
        """Test force executing non-existent job"""
        service = running_cron_service
        
        result = service.force_execute_job("invalid_job")
        
        assert result["status"] == "error"
        assert "Unknown job_id" in result["message"]
    
    def test_force_execute_when_stopped(self):
        """Test force executing when scheduler is stopped"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as f:
            temp_db = f.name
        
        try:
            service = CronService(db_path=temp_db)
            # Don't start the scheduler
            
            result = service.force_execute_job("monthly_summary_reset")
            
            assert result["status"] == "error"
            assert "Scheduler is not running" in result["message"]
            
        finally:
            if os.path.exists(temp_db):
                os.unlink(temp_db)

class TestCronJobFailureHandling:
    """Test CRON job failure handling and retry logic"""
    
    @pytest.fixture
    def running_cron_service(self):
        """Create and start a CRON service for testing"""
        # Reset metrics before each test
        reset_cron_metrics()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as f:
            temp_db = f.name
        
        service = CronService(db_path=temp_db)
        service.start_scheduler()
        yield service
        
        # Cleanup
        try:
            service.stop_scheduler()
        except:
            pass
        
        # Use try/except for file cleanup on Windows
        try:
            if os.path.exists(temp_db):
                os.unlink(temp_db)
        except (PermissionError, OSError):
            pass  # File may be locked on Windows, ignore cleanup error
    
    @patch('app.services.background_jobs.background_jobs_service.reset_monthly_summaries')
    def test_job_failure_handling(self, mock_reset, running_cron_service):
        """Integration test: Job failures are logged and retried appropriately"""
        service = running_cron_service
        
        # Mock failure
        mock_reset.side_effect = Exception("Database connection failed")
        
        # Force execute the job (should fail gracefully)
        result = service.force_execute_job("monthly_summary_reset")
        
        # Verify the job execution returns error status
        assert result["status"] == "error"
        assert "Failed to execute job" in result["message"]
        
        # Verify failure metrics
        metrics = service.get_job_metrics()
        job_metrics = metrics["metrics"]
        assert job_metrics["jobs_failed"] == 1
        assert job_metrics["jobs_executed"] == 0
        assert "monthly_summary_reset" in job_metrics["last_execution_times"]
        
        last_exec = job_metrics["last_execution_times"]["monthly_summary_reset"]
        assert last_exec["status"] == "error"
        assert last_exec["duration_seconds"] >= 0
        
        # Verify execution history contains error
        assert len(job_metrics["execution_history"]) == 1
        error_record = job_metrics["execution_history"][0]
        assert error_record["status"] == "error"
        assert error_record["job_id"] == "monthly_summary_reset"
        assert "error" in error_record["result"]
    
    @patch('app.services.background_jobs.background_jobs_service.check_subscription_expiry')
    def test_partial_job_failure(self, mock_expiry, running_cron_service):
        """Integration test: Partial job failures are handled correctly"""
        service = running_cron_service
        
        # Mock partial success (some users failed to downgrade)
        mock_expiry.return_value = {
            "job_name": "check_subscription_expiry",
            "status": "partial_success",
            "expired_users_found": 3,
            "users_downgraded": 2,
            "downgraded_users": [
                {"user_id": "user1", "email": "user1@test.com"},
                {"user_id": "user2", "email": "user2@test.com"}
            ],
            "errors": ["Failed to downgrade user3: Database error"],
            "duration_seconds": 1.2
        }
        
        # Force execute the job
        result = service.force_execute_job("daily_expiry_check")
        
        # Should still be considered successful execution (not a job crash)
        assert result["status"] == "success"
        
        metrics = service.get_job_metrics()
        job_metrics = metrics["metrics"]
        assert job_metrics["jobs_executed"] == 1
        assert job_metrics["jobs_failed"] == 0
        
        # But the execution history should show partial success
        execution_record = job_metrics["execution_history"][0]
        assert execution_record["result"]["status"] == "partial_success"
        assert len(execution_record["result"]["errors"]) == 1

class TestCronJobInterference:
    """Test that CRON jobs don't interfere with each other"""
    
    @pytest.fixture
    def running_cron_service(self):
        """Create and start a CRON service for testing"""
        # Reset metrics before each test
        reset_cron_metrics()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as f:
            temp_db = f.name
        
        service = CronService(db_path=temp_db)
        service.start_scheduler()
        yield service
        
        # Cleanup
        try:
            service.stop_scheduler()
        except:
            pass
        
        # Use try/except for file cleanup on Windows
        try:
            if os.path.exists(temp_db):
                os.unlink(temp_db)
        except (PermissionError, OSError):
            pass  # File may be locked on Windows, ignore cleanup error
    
    @patch('app.services.background_jobs.background_jobs_service.reset_monthly_summaries')
    @patch('app.services.background_jobs.background_jobs_service.check_subscription_expiry')
    def test_concurrent_job_execution(self, mock_expiry, mock_reset, running_cron_service):
        """Integration test: Jobs don't interfere with each other when running concurrently"""
        service = running_cron_service
        
        # Mock both jobs with delays to simulate concurrent execution
        mock_reset.return_value = {
            "job_name": "reset_monthly_summaries",
            "status": "success",
            "users_updated": 3,
            "duration_seconds": 1.0
        }
        
        mock_expiry.return_value = {
            "job_name": "check_subscription_expiry", 
            "status": "success",
            "users_downgraded": 1,
            "duration_seconds": 0.5
        }
        
        # Execute both jobs 
        result1 = service.force_execute_job("monthly_summary_reset")
        result2 = service.force_execute_job("daily_expiry_check")
        
        # Both should succeed
        assert result1["status"] == "success"
        assert result2["status"] == "success"
        
        # Verify both jobs were called
        mock_reset.assert_called_once()
        mock_expiry.assert_called_once()
        
        # Verify metrics track both executions
        metrics = service.get_job_metrics()
        job_metrics = metrics["metrics"]
        assert job_metrics["jobs_executed"] == 2
        assert job_metrics["jobs_failed"] == 0
        assert len(job_metrics["last_execution_times"]) == 2
        assert len(job_metrics["execution_history"]) == 2
        
        # Verify each job has separate execution records
        job_ids = [record["job_id"] for record in job_metrics["execution_history"]]
        assert "monthly_summary_reset" in job_ids
        assert "daily_expiry_check" in job_ids
    
    def test_job_instance_limit(self, running_cron_service):
        """Test that only one instance of each job can run at a time"""
        service = running_cron_service
        
        # Get job configurations
        jobs = service.scheduler.get_jobs()
        
        for job in jobs:
            # Each job should have max_instances = 1 to prevent overlapping runs
            assert job.max_instances == 1

class TestCronMetricsTracking:
    """Test CRON job metrics and monitoring functionality"""
    
    @pytest.fixture
    def running_cron_service(self):
        """Create and start a CRON service for testing"""
        # Reset metrics before each test
        reset_cron_metrics()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as f:
            temp_db = f.name
        
        service = CronService(db_path=temp_db)
        service.start_scheduler()
        yield service
        
        # Cleanup
        try:
            service.stop_scheduler()
        except:
            pass
        
        # Use try/except for file cleanup on Windows
        try:
            if os.path.exists(temp_db):
                os.unlink(temp_db)
        except (PermissionError, OSError):
            pass  # File may be locked on Windows, ignore cleanup error
    
    def test_get_scheduler_status(self, running_cron_service):
        """Monitoring test: Job execution metrics are tracked correctly"""
        service = running_cron_service
        
        status = service.get_scheduler_status()
        
        # Verify status structure
        assert status["scheduler_running"] is True
        assert status["jobs_count"] == 2
        assert len(status["jobs"]) == 2
        assert "metrics" in status
        assert "timestamp" in status
        
        # Verify job details
        for job in status["jobs"]:
            assert "id" in job
            assert "name" in job
            assert "next_run_time" in job
            assert "trigger" in job
            assert "last_execution" in job
    
    def test_get_job_metrics(self, running_cron_service):
        """Test getting detailed job metrics"""
        service = running_cron_service
        
        metrics = service.get_job_metrics()
        
        # Verify metrics structure
        assert "metrics" in metrics
        assert "timestamp" in metrics
        
        job_metrics = metrics["metrics"]
        assert "jobs_executed" in job_metrics
        assert "jobs_failed" in job_metrics
        assert "jobs_missed" in job_metrics
        assert "last_execution_times" in job_metrics
        assert "execution_history" in job_metrics
        
        # Initial state should have zero executions
        assert job_metrics["jobs_executed"] == 0
        assert job_metrics["jobs_failed"] == 0
        assert job_metrics["jobs_missed"] == 0
        assert len(job_metrics["last_execution_times"]) == 0
        assert len(job_metrics["execution_history"]) == 0
    
    @patch('app.services.background_jobs.background_jobs_service.reset_monthly_summaries')
    def test_metrics_update_after_execution(self, mock_reset, running_cron_service):
        """Test that metrics are properly updated after job execution"""
        service = running_cron_service
        
        # Mock successful execution
        mock_reset.return_value = {
            "job_name": "reset_monthly_summaries",
            "status": "success",
            "users_updated": 4,
            "duration_seconds": 0.75
        }
        
        # Execute job
        service.force_execute_job("monthly_summary_reset")
        
        # Check updated metrics
        metrics = service.get_job_metrics()
        job_metrics = metrics["metrics"]
        
        assert job_metrics["jobs_executed"] == 1
        assert job_metrics["jobs_failed"] == 0
        assert len(job_metrics["last_execution_times"]) == 1
        assert len(job_metrics["execution_history"]) == 1
        
        # Verify execution details
        last_exec = job_metrics["last_execution_times"]["monthly_summary_reset"]
        assert last_exec["status"] == "success"
        assert last_exec["duration_seconds"] >= 0
        
        exec_record = job_metrics["execution_history"][0]
        assert exec_record["job_id"] == "monthly_summary_reset"
        assert exec_record["status"] == "success"
        assert exec_record["result"]["users_updated"] == 4
    
    def test_execution_history_limit(self, running_cron_service):
        """Test that execution history is limited to prevent memory bloat"""
        service = running_cron_service
        
        # Mock multiple executions to test history limit
        with patch('app.services.background_jobs.background_jobs_service.reset_monthly_summaries') as mock_reset:
            mock_reset.return_value = {
                "job_name": "reset_monthly_summaries",
                "status": "success",
                "users_updated": 1,
                "duration_seconds": 0.1
            }
            
            # Execute job 55 times (more than the 50 limit)
            for i in range(55):
                service.force_execute_job("monthly_summary_reset")
            
            # Check that history is limited to 50 entries
            metrics = service.get_job_metrics()
            assert len(metrics["metrics"]["execution_history"]) == 50
            assert metrics["metrics"]["jobs_executed"] == 55  # Counter should still be accurate

class TestCronIntegrationWithFastAPI:
    """Test CRON service integration with FastAPI lifecycle"""
    
    def test_convenience_functions_import(self):
        """Test that convenience functions can be imported and work correctly"""
        from app.services.cron_service import (
            start_cron_scheduler, 
            stop_cron_scheduler, 
            get_cron_status, 
            get_cron_metrics, 
            force_execute_cron_job
        )
        
        # Test that functions are available
        assert callable(start_cron_scheduler)
        assert callable(stop_cron_scheduler)
        assert callable(get_cron_status)
        assert callable(get_cron_metrics)
        assert callable(force_execute_cron_job)
    
    def test_global_cron_service_instance(self):
        """Test that global cron_service instance is available"""
        from app.services.cron_service import cron_service
        
        assert cron_service is not None
        assert hasattr(cron_service, 'start_scheduler')
        assert hasattr(cron_service, 'stop_scheduler')
        assert hasattr(cron_service, 'get_scheduler_status')
    
    @patch('app.services.cron_service.cron_service.start_scheduler')
    def test_fastapi_startup_integration(self, mock_start):
        """Test integration with FastAPI startup event"""
        from app.services.cron_service import start_cron_scheduler
        
        mock_start.return_value = {
            "status": "started",
            "jobs_registered": 2,
            "message": "Scheduler started successfully"
        }
        
        # Test the convenience function
        result = start_cron_scheduler()
        
        assert result["status"] == "started"
        assert result["jobs_registered"] == 2
        mock_start.assert_called_once()
    
    @patch('app.services.cron_service.cron_service.stop_scheduler')
    def test_fastapi_shutdown_integration(self, mock_stop):
        """Test integration with FastAPI shutdown event"""
        from app.services.cron_service import stop_cron_scheduler
        
        mock_stop.return_value = {
            "status": "stopped",
            "message": "Scheduler stopped successfully"
        }
        
        # Test the convenience function
        result = stop_cron_scheduler()
        
        assert result["status"] == "stopped"
        mock_stop.assert_called_once()

# Integration test to verify the complete CRON system works end-to-end
class TestCronEndToEndIntegration:
    """End-to-end integration tests for the complete CRON system"""
    
    def test_complete_cron_lifecycle(self):
        """Test complete CRON service lifecycle from startup to shutdown"""
        # Reset metrics before test
        reset_cron_metrics()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as f:
            temp_db = f.name
        
        try:
            # Initialize service
            service = CronService(db_path=temp_db)
            assert service.is_running is False
            
            # Start scheduler
            start_result = service.start_scheduler()
            assert start_result["status"] == "started"
            assert service.is_running is True
            
            # Verify jobs are scheduled
            status = service.get_scheduler_status()
            assert status["scheduler_running"] is True
            assert status["jobs_count"] == 2
            
            # Execute a job to verify everything works
            with patch('app.services.background_jobs.background_jobs_service.reset_monthly_summaries') as mock_reset:
                mock_reset.return_value = {
                    "job_name": "reset_monthly_summaries",
                    "status": "success",
                    "users_updated": 2,
                    "duration_seconds": 0.5
                }
                
                exec_result = service.force_execute_job("monthly_summary_reset")
                assert exec_result["status"] == "success"
            
            # Verify metrics
            metrics = service.get_job_metrics()
            assert metrics["metrics"]["jobs_executed"] == 1
            
            # Stop scheduler
            stop_result = service.stop_scheduler()
            assert stop_result["status"] == "stopped"
            assert service.is_running is False
            
        finally:
            # Use try/except for file cleanup on Windows
            try:
                if os.path.exists(temp_db):
                    os.unlink(temp_db)
            except (PermissionError, OSError):
                pass  # File may be locked on Windows, ignore cleanup error 