#!/usr/bin/env python3
"""
Database setup script for PricePick backend
Run this script to initialize the MySQL database with tables and indexes
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database.init import init_db, test_connection, get_database_info
from config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Main setup function
    """
    try:
        logger.info("Starting PricePick database setup...")
        logger.info(f"Database URL: {settings.DATABASE_URL}")
        logger.info(f"Database Host: {settings.DB_HOST}")
        logger.info(f"Database Port: {settings.DB_PORT}")
        logger.info(f"Database Name: {settings.DB_NAME}")
        logger.info(f"Database User: {settings.DB_USER}")
        
        # Test connection first
        logger.info("Testing database connection...")
        if not test_connection():
            logger.error("Database connection test failed!")
            logger.error("Please check your database configuration in the .env file")
            logger.error("Make sure MySQL is running and the database exists")
            return False
        
        logger.info("Database connection successful!")
        
        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        
        # Get database info
        logger.info("Getting database information...")
        db_info = get_database_info()
        
        logger.info("Database setup completed successfully!")
        logger.info(f"Connection status: {db_info['connection_status']}")
        
        if db_info['tables']:
            logger.info("Tables created:")
            for table_name, info in db_info['tables'].items():
                logger.info(f"  - {table_name}: {info['total']} total records")
        
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        logger.info("Setup completed successfully!")
        sys.exit(0)
    else:
        logger.error("Setup failed!")
        sys.exit(1)
