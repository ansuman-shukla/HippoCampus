import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
import sqlite3
import os

from app.services.background_jobs import background_jobs_service

logger = logging.getLogger(__name__)

# Global metrics storage for job execution tracking
_job_metrics = {
    "jobs_executed": 0,
    "jobs_failed": 0,
    "jobs_missed": 0,
    "last_execution_times": {},
    "execution_history": []
}

def _update_job_metrics(job_id: str, status: str, start_time: datetime, result: Dict[str, Any]):
    """
    Update job execution metrics for monitoring.
    
    Args:
        job_id: The job identifier
        status: 'success' or 'error'
        start_time: When the job started
        result: The job execution result
    """
    global _job_metrics
    
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()
    
    # Update counters
    if status == "success":
        _job_metrics["jobs_executed"] += 1
    else:
        _job_metrics["jobs_failed"] += 1
    
    # Update last execution times
    _job_metrics["last_execution_times"][job_id] = {
        "timestamp": end_time,
        "status": status,
        "duration_seconds": duration
    }
    
    # Add to execution history (keep last 50 executions)
    execution_record = {
        "job_id": job_id,
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration,
        "status": status,
        "result": result
    }
    
    _job_metrics["execution_history"].append(execution_record)
    
    # Keep only last 50 executions to prevent memory bloat
    if len(_job_metrics["execution_history"]) > 50:
        _job_metrics["execution_history"] = _job_metrics["execution_history"][-50:]

def execute_monthly_reset():
    """
    Standalone function to execute the monthly summary reset job.
    This needs to be a standalone function (not instance method) for APScheduler serialization.
    """
    job_id = "monthly_summary_reset"
    start_time = datetime.now(timezone.utc)
    
    try:
        logger.info(f"🔄 CRON JOB: Starting {job_id}")
        
        # Execute the background job
        result = background_jobs_service.reset_monthly_summaries()
        
        # Track metrics
        _update_job_metrics(job_id, "success", start_time, result)
        
        logger.info(f"✅ CRON JOB: {job_id} completed successfully")
        logger.info(f"   └─ Users updated: {result.get('users_updated', 0)}")
        
    except Exception as e:
        error_result = {
            "job_name": job_id,
            "status": "error",
            "error": str(e)
        }
        
        # Track metrics
        _update_job_metrics(job_id, "error", start_time, error_result)
        
        logger.error(f"❌ CRON JOB: {job_id} failed: {str(e)}")
        raise

def execute_expiry_check():
    """
    Standalone function to execute the daily subscription expiry check job.
    This needs to be a standalone function (not instance method) for APScheduler serialization.
    """
    job_id = "daily_expiry_check"
    start_time = datetime.now(timezone.utc)
    
    try:
        logger.info(f"🔍 CRON JOB: Starting {job_id}")
        
        # Execute the background job
        result = background_jobs_service.check_subscription_expiry()
        
        # Track metrics
        _update_job_metrics(job_id, "success", start_time, result)
        
        logger.info(f"✅ CRON JOB: {job_id} completed successfully")
        logger.info(f"   └─ Users downgraded: {result.get('users_downgraded', 0)}")
        
    except Exception as e:
        error_result = {
            "job_name": job_id,
            "status": "error",
            "error": str(e)
        }
        
        # Track metrics
        _update_job_metrics(job_id, "error", start_time, error_result)
        
        logger.error(f"❌ CRON JOB: {job_id} failed: {str(e)}")
        raise

class CronService:
    """
    Service for managing scheduled CRON jobs for subscription maintenance.
    
    This service uses APScheduler to handle:
    - Monthly summary resets (1st of each month at UTC 00:00)
    - Daily subscription expiry checks (daily at UTC 00:00)
    - Job monitoring, error handling, and metrics tracking
    """
    
    def __init__(self, db_path: str = "jobs.sqlite"):
        self.logger = logger
        self.db_path = db_path
        self.scheduler = None
        self.is_running = False
        
        self._setup_scheduler()
    
    def _setup_scheduler(self):
        """
        Configure APScheduler with SQLite persistence and thread pool execution.
        """
        try:
            # Configure job store with SQLite for persistence
            jobstores = {
                'default': SQLAlchemyJobStore(url=f'sqlite:///{self.db_path}')
            }
            
            # Configure executors
            executors = {
                'default': ThreadPoolExecutor(max_workers=2)
            }
            
            # Job defaults
            job_defaults = {
                'coalesce': True,  # Combine multiple missed executions into one
                'max_instances': 1,  # Only one instance of each job at a time
                'misfire_grace_time': 300  # Allow 5 minutes grace for missed jobs
            }
            
            # Create scheduler
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone='UTC'
            )
            
            # Add event listeners for monitoring
            self.scheduler.add_listener(self._job_executed_listener, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
            self.scheduler.add_listener(self._job_missed_listener, EVENT_JOB_MISSED)
            
            self.logger.info("🔧 CRON SERVICE: APScheduler configured successfully")
            self.logger.info(f"   ├─ Database path: {self.db_path}")
            self.logger.info(f"   ├─ Max workers: 2")
            self.logger.info(f"   ├─ Misfire grace time: 5 minutes")
            self.logger.info(f"   └─ Timezone: UTC")
            
        except Exception as e:
            self.logger.error(f"❌ CRON SERVICE: Failed to setup scheduler: {str(e)}")
            raise
    
    def start_scheduler(self) -> Dict[str, Any]:
        """
        Start the CRON scheduler and register jobs.
        
        Returns:
            dict: Status of scheduler startup and job registration
        """
        try:
            if self.is_running:
                return {
                    "status": "already_running",
                    "message": "Scheduler is already running",
                    "timestamp": datetime.now(timezone.utc)
                }
            
            self.logger.info("🚀 CRON SERVICE: Starting scheduler...")
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            # Register jobs
            self._register_jobs()
            
            # Get job information
            jobs = self.scheduler.get_jobs()
            job_info = [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time,
                    "trigger": str(job.trigger)
                }
                for job in jobs
            ]
            
            result = {
                "status": "started",
                "message": "Scheduler started successfully",
                "jobs_registered": len(jobs),
                "jobs": job_info,
                "timestamp": datetime.now(timezone.utc)
            }
            
            self.logger.info("✅ CRON SERVICE: Scheduler started successfully")
            self.logger.info(f"   ├─ Jobs registered: {len(jobs)}")
            self.logger.info(f"   └─ Running jobs: {[job.id for job in jobs]}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ CRON SERVICE: Failed to start scheduler: {str(e)}")
            self.is_running = False
            return {
                "status": "error",
                "message": f"Failed to start scheduler: {str(e)}",
                "timestamp": datetime.now(timezone.utc)
            }
    
    def stop_scheduler(self) -> Dict[str, Any]:
        """
        Stop the CRON scheduler.
        
        Returns:
            dict: Status of scheduler shutdown
        """
        try:
            if not self.is_running:
                return {
                    "status": "already_stopped",
                    "message": "Scheduler is not running",
                    "timestamp": datetime.now(timezone.utc)
                }
            
            self.logger.info("🛑 CRON SERVICE: Stopping scheduler...")
            
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            
            result = {
                "status": "stopped",
                "message": "Scheduler stopped successfully",
                "timestamp": datetime.now(timezone.utc)
            }
            
            self.logger.info("✅ CRON SERVICE: Scheduler stopped successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ CRON SERVICE: Failed to stop scheduler: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to stop scheduler: {str(e)}",
                "timestamp": datetime.now(timezone.utc)
            }
    
    def _register_jobs(self):
        """
        Register all CRON jobs with the scheduler.
        """
        try:
            # Monthly summary reset - 1st of each month at UTC 00:00
            self.scheduler.add_job(
                func=execute_monthly_reset,
                trigger=CronTrigger(
                    day=1,      # 1st of the month
                    hour=0,     # 00:00 UTC
                    minute=0,
                    timezone='UTC'
                ),
                id='monthly_summary_reset',
                name='Monthly Summary Reset',
                replace_existing=True
            )
            
            # Daily expiry check - Every day at UTC 00:00
            self.scheduler.add_job(
                func=execute_expiry_check,
                trigger=CronTrigger(
                    hour=0,     # 00:00 UTC
                    minute=0,
                    timezone='UTC'
                ),
                id='daily_expiry_check',
                name='Daily Subscription Expiry Check',
                replace_existing=True
            )
            
            self.logger.info("📅 CRON SERVICE: Jobs registered successfully")
            self.logger.info("   ├─ Monthly reset: 1st of month at 00:00 UTC")
            self.logger.info("   └─ Daily expiry check: Daily at 00:00 UTC")
            
        except Exception as e:
            self.logger.error(f"❌ CRON SERVICE: Failed to register jobs: {str(e)}")
            raise
    

    
    def _job_executed_listener(self, event):
        """Event listener for successful job executions."""
        self.logger.info(f"📊 CRON EVENT: Job {event.job_id} executed successfully")
    
    def _job_error_listener(self, event):
        """Event listener for job execution errors."""
        self.logger.error(f"📊 CRON EVENT: Job {event.job_id} failed with error: {event.exception}")
    
    def _job_missed_listener(self, event):
        """Event listener for missed job executions."""
        global _job_metrics
        _job_metrics["jobs_missed"] += 1
        self.logger.warning(f"📊 CRON EVENT: Job {event.job_id} was missed")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get current scheduler status and job information.
        
        Returns:
            dict: Comprehensive scheduler and job status
        """
        try:
            if not self.is_running:
                return {
                    "scheduler_running": False,
                    "message": "Scheduler is not running",
                    "timestamp": datetime.now(timezone.utc)
                }
            
            jobs = self.scheduler.get_jobs()
            job_details = []
            
            for job in jobs:
                job_info = {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time,
                    "trigger": str(job.trigger),
                    "last_execution": _job_metrics["last_execution_times"].get(job.id)
                }
                job_details.append(job_info)
            
            return {
                "scheduler_running": True,
                "jobs_count": len(jobs),
                "jobs": job_details,
                "metrics": _job_metrics,
                "timestamp": datetime.now(timezone.utc)
            }
            
        except Exception as e:
            self.logger.error(f"❌ CRON SERVICE: Failed to get status: {str(e)}")
            return {
                "scheduler_running": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc)
            }
    
    def get_job_metrics(self) -> Dict[str, Any]:
        """
        Get detailed job execution metrics.
        
        Returns:
            dict: Job execution metrics and history
        """
        return {
            "metrics": _job_metrics.copy(),
            "timestamp": datetime.now(timezone.utc)
        }
    
    def force_execute_job(self, job_id: str) -> Dict[str, Any]:
        """
        Force execute a specific job immediately (for testing/admin purposes).
        
        Args:
            job_id: The job to execute ('monthly_summary_reset' or 'daily_expiry_check')
            
        Returns:
            dict: Execution result
        """
        try:
            if not self.is_running:
                return {
                    "status": "error",
                    "message": "Scheduler is not running",
                    "timestamp": datetime.now(timezone.utc)
                }
            
            if job_id == "monthly_summary_reset":
                execute_monthly_reset()
                return {
                    "status": "success",
                    "message": "Monthly reset job executed successfully",
                    "job_id": job_id,
                    "timestamp": datetime.now(timezone.utc)
                }
            elif job_id == "daily_expiry_check":
                execute_expiry_check()
                return {
                    "status": "success",
                    "message": "Daily expiry check job executed successfully",
                    "job_id": job_id,
                    "timestamp": datetime.now(timezone.utc)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Unknown job_id: {job_id}",
                    "timestamp": datetime.now(timezone.utc)
                }
                
        except Exception as e:
            self.logger.error(f"❌ CRON SERVICE: Failed to force execute job {job_id}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to execute job: {str(e)}",
                "job_id": job_id,
                "timestamp": datetime.now(timezone.utc)
            }

# Global instance
cron_service = CronService()

# Convenience functions for easy import
def start_cron_scheduler() -> Dict[str, Any]:
    """Start the CRON scheduler and register jobs."""
    return cron_service.start_scheduler()

def stop_cron_scheduler() -> Dict[str, Any]:
    """Stop the CRON scheduler."""
    return cron_service.stop_scheduler()

def get_cron_status() -> Dict[str, Any]:
    """Get current CRON scheduler status."""
    return cron_service.get_scheduler_status()

def get_cron_metrics() -> Dict[str, Any]:
    """Get CRON job execution metrics."""
    return cron_service.get_job_metrics()

def force_execute_cron_job(job_id: str) -> Dict[str, Any]:
    """Force execute a specific CRON job."""
    return cron_service.force_execute_job(job_id)

def reset_cron_metrics():
    """Reset CRON job metrics to initial state (for testing purposes)."""
    global _job_metrics
    _job_metrics = {
        "jobs_executed": 0,
        "jobs_failed": 0,
        "jobs_missed": 0,
        "last_execution_times": {},
        "execution_history": []
    } 