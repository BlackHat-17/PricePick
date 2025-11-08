"""
Database initialization and table creation
"""

from sqlalchemy import text
from .connection import engine, SessionLocal
from app.models.base import Base
import logging

logger = logging.getLogger(__name__)


async def init_db():
    """
    Initialize database and create tables
    """
    try:
        logger.info("Initializing database...")
        
        # Test connection first
        if not test_connection():
            raise Exception("Database connection test failed")
        
        # Create all tables
        create_tables()
        
        # Run any additional initialization
        await run_initialization_scripts()
        
        logger.info("Database initialized successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


def create_tables():
    """
    Create all database tables
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped!")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {str(e)}")
        raise


async def run_initialization_scripts():
    """
    Run any additional initialization scripts
    """
    try:
        # Create indexes for better performance
        await create_indexes()
        
        # Insert any default data
        await insert_default_data()
        
        logger.info("Initialization scripts completed!")
        
    except Exception as e:
        logger.error(f"Initialization scripts failed: {str(e)}")
        raise


async def create_indexes():
    """
    Create additional database indexes for better performance
    MySQL doesn't support IF NOT EXISTS in CREATE INDEX, so we check if index exists first
    """
    try:
        db = SessionLocal()
        
        # Helper function to check if index exists (MySQL compatible)
        def index_exists(index_name: str) -> bool:
            try:
                result = db.execute(text(
                    "SELECT COUNT(*) FROM information_schema.statistics "
                    "WHERE table_schema = DATABASE() AND index_name = :index_name"
                ), {"index_name": index_name})
                return result.scalar() > 0
            except Exception:
                return False
        
        # Create composite indexes for common queries
        indexes = [
            # Product indexes
            ("idx_products_platform_tracking", "CREATE INDEX idx_products_platform_tracking ON products(platform, is_tracking, is_active)"),
            ("idx_products_category_brand", "CREATE INDEX idx_products_category_brand ON products(category, brand, is_active)"),
            
            # Price indexes
            ("idx_prices_product_created", "CREATE INDEX idx_prices_product_created ON prices(product_id, created_at DESC)"),
            ("idx_prices_currency_available", "CREATE INDEX idx_prices_currency_available ON prices(currency, is_available, is_active)"),
            
            # User indexes
            ("idx_users_email_active", "CREATE INDEX idx_users_email_active ON users(email, is_active)"),
            ("idx_users_username_active", "CREATE INDEX idx_users_username_active ON users(username, is_active)"),
            
            # Alert indexes
            ("idx_alerts_user_active", "CREATE INDEX idx_alerts_user_active ON price_alerts(user_id, is_active, alert_type)"),
            ("idx_alerts_product_active", "CREATE INDEX idx_alerts_product_active ON price_alerts(product_id, is_active)"),
            
            # History indexes
            ("idx_history_product_created", "CREATE INDEX idx_history_product_created ON price_history(product_id, created_at DESC)"),
            
            # Session indexes
            ("idx_sessions_product_status", "CREATE INDEX idx_sessions_product_status ON scraping_sessions(product_id, status, created_at DESC)"),
            ("idx_sessions_platform_success", "CREATE INDEX idx_sessions_platform_success ON scraping_sessions(platform, success, created_at DESC)"),
        ]
        
        for index_name, index_sql in indexes:
            try:
                # Check if index already exists (MySQL doesn't support IF NOT EXISTS)
                if not index_exists(index_name):
                    db.execute(text(index_sql))
                    db.commit()
                    logger.debug(f"Created index: {index_name}")
                else:
                    logger.debug(f"Index already exists: {index_name}")
            except Exception as e:
                # If index already exists, MySQL will raise an error - that's okay
                error_str = str(e).lower()
                if "duplicate key name" in error_str or "already exists" in error_str:
                    logger.debug(f"Index {index_name} already exists, skipping")
                else:
                    logger.warning(f"Failed to create index {index_name}: {e}")
                db.rollback()
        
        db.close()
        logger.info("Additional indexes created successfully!")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {str(e)}")
        raise


async def insert_default_data():
    """
    Insert any default data needed for the application
    """
    try:
        db = SessionLocal()
        
        # Check if we need to insert default data
        from app.models.user import User
        
        # Check if any users exist
        user_count = db.query(User).count()
        
        if user_count == 0:
            logger.info("No users found, skipping default data insertion")
        else:
            logger.info(f"Found {user_count} users, skipping default data insertion")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Failed to insert default data: {str(e)}")
        raise


def test_connection():
    """
    Test database connection
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False


def get_database_info():
    """
    Get database information and statistics
    """
    try:
        db = SessionLocal()
        
        # Get table information
        tables_info = {}
        
        # Import all models
        from app.models import Product, Price, User, PriceAlert, PriceHistory, ScrapingSession, ScrapingError
        
        models = [Product, Price, User, PriceAlert, PriceHistory, ScrapingSession, ScrapingError]
        
        for model in models:
            table_name = model.__tablename__
            count = db.query(model).count()
            active_count = db.query(model).filter(model.is_active == True).count()
            
            tables_info[table_name] = {
                "total": count,
                "active": active_count,
                "inactive": count - active_count
            }
        
        db.close()
        
        return {
            "database_url": engine.url,
            "tables": tables_info,
            "connection_status": "connected"
        }
        
    except Exception as e:
        logger.error(f"Failed to get database info: {str(e)}")
        return {
            "database_url": str(engine.url),
            "tables": {},
            "connection_status": "error",
            "error": str(e)
        }
