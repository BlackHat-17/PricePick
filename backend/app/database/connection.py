"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_CONFIG
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Create database engine
db_url = DATABASE_CONFIG["url"]
parsed = urlparse(db_url)
is_mysql = parsed.scheme.startswith("mysql")

connect_args = {}
if is_mysql:
    # Enable SSL when using Aiven or other MySQL with SSL
    ssl_args = {}
    ca_path = DATABASE_CONFIG.get("ssl_ca")
    if ca_path:
        ssl_args["ca"] = ca_path
    # If any SSL params present, pass the ssl/ssl_ca
    if ssl_args:
        connect_args["ssl"] = ssl_args

engine = create_engine(
    db_url,
    echo=DATABASE_CONFIG["echo"],
    pool_size=DATABASE_CONFIG["pool_size"],
    max_overflow=DATABASE_CONFIG["max_overflow"],
    pool_pre_ping=DATABASE_CONFIG["pool_pre_ping"],
    pool_recycle=DATABASE_CONFIG["pool_recycle"],
    connect_args=connect_args,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session():
    """
    Get a database session (for use outside of FastAPI dependency injection)
    """
    return SessionLocal()


def close_db_session(db):
    """
    Close a database session
    """
    try:
        db.close()
    except Exception as e:
        logger.error(f"Error closing database session: {str(e)}")


def test_connection():
    """
    Test database connection
    """
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            return result.fetchone()[0] == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False
