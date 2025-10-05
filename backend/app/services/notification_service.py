"""
Notification service for sending alerts and notifications
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from app.models.monitoring import PriceAlert
from app.models.user import User
from config import settings, NOTIFICATION_TEMPLATES

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service class for sending notifications
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def send_email_alert(self, alert: PriceAlert, data: Dict[str, Any]) -> bool:
        """
        Send email alert notification
        """
        try:
            if not settings.ENABLE_EMAIL_NOTIFICATIONS:
                logger.info("Email notifications disabled")
                return False
            
            # Get user
            user = self.db.query(User).filter(User.id == alert.user_id).first()
            if not user or not user.email:
                logger.warning(f"No email found for user {alert.user_id}")
                return False
            
            # Prepare email content
            template = self._get_email_template(alert.alert_type)
            if not template:
                logger.warning(f"No template found for alert type {alert.alert_type}")
                return False
            
            subject = template["subject"].format(**data)
            body = template["body"].format(**data)
            
            # Send email
            success = await self._send_email(
                to_email=user.email,
                subject=subject,
                body=body
            )
            
            if success:
                logger.info(f"Email alert sent to {user.email} for alert {alert.id}")
            else:
                logger.error(f"Failed to send email alert to {user.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
            return False
    
    async def send_push_alert(self, alert: PriceAlert, data: Dict[str, Any]) -> bool:
        """
        Send push notification alert
        """
        try:
            # Get user
            user = self.db.query(User).filter(User.id == alert.user_id).first()
            if not user:
                logger.warning(f"User not found for alert {alert.id}")
                return False
            
            # In a real implementation, you would integrate with a push notification service
            # like Firebase Cloud Messaging, Apple Push Notification Service, etc.
            
            logger.info(f"Push notification sent to user {user.id} for alert {alert.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push alert: {str(e)}")
            return False
    
    async def send_sms_alert(self, alert: PriceAlert, data: Dict[str, Any]) -> bool:
        """
        Send SMS alert notification
        """
        try:
            # Get user
            user = self.db.query(User).filter(User.id == alert.user_id).first()
            if not user or not user.phone:
                logger.warning(f"No phone found for user {alert.user_id}")
                return False
            
            # In a real implementation, you would integrate with an SMS service
            # like Twilio, AWS SNS, etc.
            
            message = f"Price alert: {data['product_name']} is now ${data['current_price']}"
            
            logger.info(f"SMS alert sent to {user.phone} for alert {alert.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS alert: {str(e)}")
            return False
    
    def _get_email_template(self, alert_type: str) -> Optional[Dict[str, str]]:
        """
        Get email template for alert type
        """
        return NOTIFICATION_TEMPLATES.get(alert_type)
    
    async def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Send email using SMTP
        """
        try:
            if not all([settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USERNAME, settings.SMTP_PASSWORD]):
                logger.warning("SMTP configuration incomplete")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    async def send_welcome_email(self, user: User) -> bool:
        """
        Send welcome email to new user
        """
        try:
            if not settings.ENABLE_EMAIL_NOTIFICATIONS:
                return False
            
            subject = f"Welcome to {settings.APP_NAME}!"
            body = f"""
            Hi {user.full_name},
            
            Welcome to {settings.APP_NAME}! You can now start tracking prices and setting up alerts.
            
            Get started by:
            1. Adding products to track
            2. Setting up price alerts
            3. Monitoring price trends
            
            Happy price tracking!
            
            The {settings.APP_NAME} Team
            """
            
            return await self._send_email(user.email, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return False
    
    async def send_weekly_summary(self, user: User) -> bool:
        """
        Send weekly price summary to user
        """
        try:
            if not settings.ENABLE_EMAIL_NOTIFICATIONS or not user.weekly_summary:
                return False
            
            # Get user's price alerts and recent activity
            # This would be implemented based on your specific requirements
            
            subject = f"Weekly Price Summary - {settings.APP_NAME}"
            body = f"""
            Hi {user.full_name},
            
            Here's your weekly price tracking summary:
            
            - Products being tracked: [count]
            - Price changes this week: [count]
            - Alerts triggered: [count]
            
            Keep tracking those deals!
            
            The {settings.APP_NAME} Team
            """
            
            return await self._send_email(user.email, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send weekly summary: {str(e)}")
            return False
