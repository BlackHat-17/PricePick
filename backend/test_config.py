#!/usr/bin/env python3
"""
Test configuration script for PricePick backend
Run this script to verify your configuration is working
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config import settings
from app.database.init import test_connection
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_config():
    """Test database configuration"""
    logger.info("Testing database configuration...")
    
    try:
        logger.info(f"Database Host: {settings.DB_HOST}")
        logger.info(f"Database Port: {settings.DB_PORT}")
        logger.info(f"Database User: {settings.DB_USER}")
        logger.info(f"Database Name: {settings.DB_NAME}")
        logger.info(f"Database URL: {settings.DATABASE_URL}")
        
        # Test connection
        if test_connection():
            logger.info("✅ Database connection successful!")
            return True
        else:
            logger.error("❌ Database connection failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database configuration error: {str(e)}")
        return False


def test_smtp_config():
    """Test SMTP configuration"""
    logger.info("Testing SMTP configuration...")
    
    try:
        smtp_fields = [
            ("SMTP Host", settings.SMTP_HOST),
            ("SMTP Port", settings.SMTP_PORT),
            ("SMTP Username", settings.SMTP_USERNAME),
            ("SMTP Password", settings.SMTP_PASSWORD),
            ("SMTP From Email", settings.SMTP_FROM_EMAIL),
        ]
        
        all_configured = True
        for field_name, field_value in smtp_fields:
            if field_value:
                logger.info(f"{field_name}: {'*' * len(str(field_value)) if 'password' in field_name.lower() else field_value}")
            else:
                logger.warning(f"{field_name}: Not configured")
                all_configured = False
        
        if all_configured:
            logger.info("✅ SMTP configuration complete!")
            return True
        else:
            logger.warning("⚠️  SMTP configuration incomplete (some fields missing)")
            return False
            
    except Exception as e:
        logger.error(f"❌ SMTP configuration error: {str(e)}")
        return False


def test_other_config():
    """Test other important configuration"""
    logger.info("Testing other configuration...")
    
    try:
        configs = [
            ("App Name", settings.APP_NAME),
            ("Debug Mode", settings.DEBUG),
            ("Host", settings.HOST),
            ("Port", settings.PORT),
            ("Secret Key", "Set" if settings.SECRET_KEY != "your-secret-key-change-in-production" else "Default (change this!)"),
            ("Email Notifications", settings.ENABLE_EMAIL_NOTIFICATIONS),
        ]
        
        for config_name, config_value in configs:
            logger.info(f"{config_name}: {config_value}")
        
        logger.info("✅ Other configuration loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration error: {str(e)}")
        return False


def main():
    """Main test function"""
    logger.info("Starting PricePick configuration test...")
    logger.info("=" * 50)
    
    results = []
    
    # Test database
    results.append(test_database_config())
    logger.info("")
    
    # Test SMTP
    results.append(test_smtp_config())
    logger.info("")
    
    # Test other config
    results.append(test_other_config())
    logger.info("")
    
    # Summary
    logger.info("=" * 50)
    logger.info("Configuration Test Summary:")
    logger.info(f"Database: {'✅ PASS' if results[0] else '❌ FAIL'}")
    logger.info(f"SMTP: {'✅ PASS' if results[1] else '⚠️  PARTIAL' if results[1] is not False else '❌ FAIL'}")
    logger.info(f"Other: {'✅ PASS' if results[2] else '❌ FAIL'}")
    
    if all(results):
        logger.info("🎉 All tests passed! Your configuration is ready.")
        return True
    else:
        logger.warning("⚠️  Some tests failed. Please check your configuration.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
