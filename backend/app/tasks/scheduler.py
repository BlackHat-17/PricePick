"""
Task scheduler for managing background tasks
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.tasks.price_monitor import PriceMonitoringTask
from app.tasks.alert_checker import AlertCheckingTask
from app.tasks.cleanup import CleanupTask
from config import settings

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Centralized task scheduler for background operations
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.tasks = {}
        self.is_running = False
    
    async def start(self):
        """
        Start the task scheduler
        """
        try:
            if self.is_running:
                logger.warning("Task scheduler is already running")
                return
            
            # Initialize tasks
            self._initialize_tasks()
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info("Task scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start task scheduler: {str(e)}")
            raise
    
    async def stop(self):
        """
        Stop the task scheduler
        """
        try:
            if not self.is_running:
                logger.warning("Task scheduler is not running")
                return
            
            # Shutdown scheduler
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            
            logger.info("Task scheduler stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop task scheduler: {str(e)}")
            raise
    
    def _initialize_tasks(self):
        """
        Initialize all background tasks
        """
        try:
            # Price monitoring task - run every hour
            price_monitor = PriceMonitoringTask()
            self.scheduler.add_job(
                price_monitor.run,
                trigger=IntervalTrigger(hours=1),
                id="price_monitor",
                name="Price Monitoring",
                max_instances=1,
                replace_existing=True
            )
            self.tasks["price_monitor"] = price_monitor
            
            # Alert checking task - run every 30 minutes
            alert_checker = AlertCheckingTask()
            self.scheduler.add_job(
                alert_checker.run,
                trigger=IntervalTrigger(minutes=30),
                id="alert_checker",
                name="Alert Checking",
                max_instances=1,
                replace_existing=True
            )
            self.tasks["alert_checker"] = alert_checker
            
            # Cleanup task - run daily at 2 AM
            cleanup_task = CleanupTask()
            self.scheduler.add_job(
                cleanup_task.run,
                trigger=CronTrigger(hour=2, minute=0),
                id="cleanup",
                name="Data Cleanup",
                max_instances=1,
                replace_existing=True
            )
            self.tasks["cleanup"] = cleanup_task
            
            # Weekly summary task - run every Monday at 9 AM
            self.scheduler.add_job(
                self._send_weekly_summaries,
                trigger=CronTrigger(day_of_week=0, hour=9, minute=0),
                id="weekly_summary",
                name="Weekly Summary",
                max_instances=1,
                replace_existing=True
            )
            
            logger.info("All background tasks initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize tasks: {str(e)}")
            raise
    
    async def run_task(self, task_name: str, **kwargs) -> Dict[str, Any]:
        """
        Manually run a specific task
        """
        try:
            if task_name not in self.tasks:
                raise ValueError(f"Task '{task_name}' not found")
            
            task = self.tasks[task_name]
            result = await task.run(**kwargs)
            
            logger.info(f"Manually executed task '{task_name}'")
            return {
                "task_name": task_name,
                "success": True,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Failed to run task '{task_name}': {str(e)}")
            return {
                "task_name": task_name,
                "success": False,
                "error": str(e)
            }
    
    async def get_task_status(self) -> Dict[str, Any]:
        """
        Get status of all tasks
        """
        try:
            status = {
                "scheduler_running": self.is_running,
                "tasks": {}
            }
            
            for task_name, task in self.tasks.items():
                status["tasks"][task_name] = {
                    "name": task.__class__.__name__,
                    "last_run": getattr(task, 'last_run', None),
                    "next_run": None,
                    "status": "unknown"
                }
            
            # Get next run times from scheduler
            if self.is_running:
                jobs = self.scheduler.get_jobs()
                for job in jobs:
                    if job.id in status["tasks"]:
                        status["tasks"][job.id]["next_run"] = job.next_run_time.isoformat() if job.next_run_time else None
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get task status: {str(e)}")
            return {"error": str(e)}
    
    async def _send_weekly_summaries(self):
        """
        Send weekly summaries to users
        """
        try:
            from app.services.notification_service import NotificationService
            from app.database import get_db_session
            
            db = get_db_session()
            try:
                notification_service = NotificationService(db)
                
                # Get users who want weekly summaries
                from app.models.user import User
                users = db.query(User).filter(
                    User.is_active == True,
                    User.weekly_summary == True
                ).all()
                
                sent_count = 0
                for user in users:
                    try:
                        success = await notification_service.send_weekly_summary(user)
                        if success:
                            sent_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send weekly summary to user {user.id}: {str(e)}")
                
                logger.info(f"Sent weekly summaries to {sent_count} users")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to send weekly summaries: {str(e)}")
    
    def add_custom_task(self, task_id: str, task_func, trigger, **kwargs):
        """
        Add a custom task to the scheduler
        """
        try:
            self.scheduler.add_job(
                task_func,
                trigger=trigger,
                id=task_id,
                max_instances=1,
                replace_existing=True,
                **kwargs
            )
            
            logger.info(f"Added custom task '{task_id}'")
            
        except Exception as e:
            logger.error(f"Failed to add custom task '{task_id}': {str(e)}")
            raise
    
    def remove_task(self, task_id: str):
        """
        Remove a task from the scheduler
        """
        try:
            self.scheduler.remove_job(task_id)
            logger.info(f"Removed task '{task_id}'")
            
        except Exception as e:
            logger.error(f"Failed to remove task '{task_id}': {str(e)}")
            raise
