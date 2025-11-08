"""
Task scheduler for managing background tasks (Firebase Firestore version)
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.tasks.price_monitor import PriceMonitoringTask

from app.tasks.alert_checker import AlertCheckingTask
from app.tasks.cleanup import CleanupTask
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Centralized Firestore-based task scheduler for background operations
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.tasks: Dict[str, Any] = {}
        self.is_running = False

    # ---------------------------------------------------
    # Start / Stop Scheduler
    # ---------------------------------------------------
    async def start(self):
        """
        Start the task scheduler
        """
        if self.is_running:
            logger.warning("⚠️ Task scheduler is already running")
            return

        try:
            self._initialize_tasks()
            self.scheduler.start()
            self.is_running = True
            logger.info("✅ Firestore Task Scheduler started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start task scheduler: {e}")
            raise

    async def stop(self):
        """
        Stop the task scheduler
        """
        if not self.is_running:
            logger.warning("Task scheduler is not running")
            return
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("🛑 Task scheduler stopped")
        except Exception as e:
            logger.error(f"Failed to stop task scheduler: {e}")
            raise

    # ---------------------------------------------------
    # Initialize Core Tasks
    # ---------------------------------------------------
    def _initialize_tasks(self):
        """
        Initialize background tasks (Firestore-compatible)
        """
        try:
            # Price monitoring task - hourly
            price_monitor = PriceMonitoringTask()
            self.scheduler.add_job(
                price_monitor.run,
                trigger=IntervalTrigger(hours=1),
                id="price_monitor",
                name="Price Monitoring",
                max_instances=1,
                replace_existing=True,
            )
            self.tasks["price_monitor"] = price_monitor

            # Alert checking task - every 30 min
            alert_checker = AlertCheckingTask()
            self.scheduler.add_job(
                alert_checker.run,
                trigger=IntervalTrigger(minutes=30),
                id="alert_checker",
                name="Alert Checking",
                max_instances=1,
                replace_existing=True,
            )
            self.tasks["alert_checker"] = alert_checker

            # Cleanup task - daily at 2 AM
            cleanup_task = CleanupTask()
            self.scheduler.add_job(
                cleanup_task.run,
                trigger=CronTrigger(hour=2, minute=0),
                id="cleanup",
                name="Data Cleanup",
                max_instances=1,
                replace_existing=True,
            )
            self.tasks["cleanup"] = cleanup_task

            # Weekly summary task - every Monday at 9 AM
            self.scheduler.add_job(
                self._send_weekly_summaries,
                trigger=CronTrigger(day_of_week="mon", hour=9, minute=0),
                id="weekly_summary",
                name="Weekly Summary",
                max_instances=1,
                replace_existing=True,
            )

            logger.info("🧩 All Firestore background tasks initialized")
        except Exception as e:
            logger.error(f"Failed to initialize tasks: {e}")
            raise

    # ---------------------------------------------------
    # Manual Execution
    # ---------------------------------------------------
    async def run_task(self, task_name: str, **kwargs) -> Dict[str, Any]:
        """
        Run a specific background task manually
        """
        try:
            if task_name not in self.tasks:
                raise ValueError(f"Task '{task_name}' not found")

            task = self.tasks[task_name]
            result = await task.run(**kwargs)

            logger.info(f"🧠 Manually executed task '{task_name}'")
            return {"task_name": task_name, "success": True, "result": result}
        except Exception as e:
            logger.error(f"Failed to run task '{task_name}': {e}")
            return {"task_name": task_name, "success": False, "error": str(e)}

    # ---------------------------------------------------
    # Status Overview
    # ---------------------------------------------------
    async def get_task_status(self) -> Dict[str, Any]:
        """
        Get scheduler status and next run times
        """
        try:
            status = {
                "scheduler_running": self.is_running,
                "tasks": {},
            }

            for task_name, task in self.tasks.items():
                status["tasks"][task_name] = {
                    "name": task.__class__.__name__,
                    "last_run": getattr(task, "last_run", None),
                    "next_run": None,
                    "status": "idle",
                }

            if self.is_running:
                for job in self.scheduler.get_jobs():
                    if job.id in status["tasks"]:
                        status["tasks"][job.id]["next_run"] = (
                            job.next_run_time.isoformat() if job.next_run_time else None
                        )

            return status
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return {"error": str(e)}

    # ---------------------------------------------------
    # Weekly Summary Sender (Firestore)
    # ---------------------------------------------------
    async def _send_weekly_summaries(self):
        """
        Send weekly summaries to users stored in Firestore
        """
        try:
            from firebase_admin import firestore

            db = firestore.client()
            users_ref = db.collection("users")
            users = [doc.to_dict() for doc in users_ref.stream()]

            notify_service = NotificationService()

            sent_count = 0
            for user in users:
                if user.get("is_active") and user.get("weekly_summary"):
                    try:
                        success = await notify_service.send_weekly_summary(user)
                        if success:
                            sent_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to send summary to {user.get('email')}: {e}")

            logger.info(f"📨 Sent weekly summaries to {sent_count} users")

        except Exception as e:
            logger.error(f"Failed to send weekly summaries: {e}")

    # ---------------------------------------------------
    # Manage Custom Tasks
    # ---------------------------------------------------
    def add_custom_task(self, task_id: str, task_func, trigger, **kwargs):
        """
        Add custom background task dynamically
        """
        try:
            self.scheduler.add_job(
                task_func,
                trigger=trigger,
                id=task_id,
                max_instances=1,
                replace_existing=True,
                **kwargs,
            )
            logger.info(f"Added custom task '{task_id}'")
        except Exception as e:
            logger.error(f"Failed to add custom task '{task_id}': {e}")
            raise

    def remove_task(self, task_id: str):
        """
        Remove a scheduled background task
        """
        try:
            self.scheduler.remove_job(task_id)
            logger.info(f"Removed task '{task_id}'")
        except Exception as e:
            logger.error(f"Failed to remove task '{task_id}': {e}")
            raise
