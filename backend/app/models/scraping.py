"""
Scraping models for tracking web scraping sessions and errors
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from .base import Base


class ScrapingSession(Base):
    """
    Scraping session model for tracking web scraping operations
    """
    __tablename__ = "scraping_sessions"
    
    # Foreign key to product
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Session information
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    url = Column(Text, nullable=False)
    
    # Session status
    status = Column(String(20), nullable=False, index=True)  # pending, running, completed, failed
    started_at = Column(String(50), nullable=True)  # ISO datetime string
    completed_at = Column(String(50), nullable=True)  # ISO datetime string
    
    # Scraping results
    success = Column(Boolean, default=False, nullable=False)
    price_found = Column(Boolean, default=False, nullable=False)
    title_found = Column(Boolean, default=False, nullable=False)
    availability_found = Column(Boolean, default=False, nullable=False)
    
    # Scraped data
    scraped_price = Column(String(50), nullable=True)
    scraped_title = Column(Text, nullable=True)
    scraped_availability = Column(String(50), nullable=True)
    scraped_image_url = Column(Text, nullable=True)
    scraped_rating = Column(String(10), nullable=True)
    scraped_review_count = Column(String(20), nullable=True)
    
    # Technical details
    response_time_ms = Column(Integer, nullable=True)
    http_status_code = Column(Integer, nullable=True)
    user_agent = Column(String(200), nullable=True)
    headers_sent = Column(JSON, nullable=True)
    headers_received = Column(JSON, nullable=True)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_type = Column(String(50), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Additional metadata
    extra_metadata = Column("metadata", JSON, nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="scraping_sessions")
    prices = relationship("Price", back_populates="scraping_session")
    price_history = relationship("PriceHistory", back_populates="scraping_session")
    errors = relationship("ScrapingError", back_populates="scraping_session", cascade="all, delete-orphan")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_session_product_status', 'product_id', 'status'),
        Index('idx_session_platform_status', 'platform', 'status'),
        Index('idx_session_success', 'success', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<ScrapingSession(id={self.id}, product_id={self.product_id}, status='{self.status}')>"
    
    @property
    def duration_seconds(self) -> float:
        """
        Calculate session duration in seconds
        """
        if not self.started_at or not self.completed_at:
            return 0.0
        
        from datetime import datetime
        try:
            start = datetime.fromisoformat(self.started_at.replace('Z', '+00:00'))
            end = datetime.fromisoformat(self.completed_at.replace('Z', '+00:00'))
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return 0.0
    
    @property
    def is_successful(self) -> bool:
        """
        Check if scraping session was successful
        """
        return self.success and self.status == "completed"
    
    def start_session(self) -> None:
        """
        Mark session as started
        """
        from datetime import datetime
        self.status = "running"
        self.started_at = datetime.utcnow().isoformat()
    
    def complete_session(self, success: bool = True) -> None:
        """
        Mark session as completed
        """
        from datetime import datetime
        self.status = "completed"
        self.success = success
        self.completed_at = datetime.utcnow().isoformat()
    
    def fail_session(self, error_message: str, error_type: str = "unknown") -> None:
        """
        Mark session as failed
        """
        from datetime import datetime
        self.status = "failed"
        self.success = False
        self.error_message = error_message
        self.error_type = error_type
        self.completed_at = datetime.utcnow().isoformat()


class ScrapingError(Base):
    """
    Scraping error model for tracking and analyzing scraping failures
    """
    __tablename__ = "scraping_errors"
    
    # Foreign key to scraping session
    scraping_session_id = Column(Integer, ForeignKey("scraping_sessions.id"), nullable=False, index=True)
    
    # Error information
    error_type = Column(String(50), nullable=False, index=True)  # timeout, connection, parsing, rate_limit, etc.
    error_message = Column(Text, nullable=False)
    error_code = Column(String(20), nullable=True)
    
    # Error context
    url = Column(Text, nullable=True)
    http_status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Technical details
    user_agent = Column(String(200), nullable=True)
    headers_sent = Column(JSON, nullable=True)
    headers_received = Column(JSON, nullable=True)
    response_content = Column(Text, nullable=True)  # First 1000 chars of response
    
    # Error metadata
    stack_trace = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    
    # Relationships
    scraping_session = relationship("ScrapingSession", back_populates="errors")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_error_type', 'error_type'),
        Index('idx_error_session', 'scraping_session_id'),
        Index('idx_error_http_status', 'http_status_code'),
    )
    
    def __repr__(self) -> str:
        return f"<ScrapingError(id={self.id}, type='{self.error_type}', message='{self.error_message[:50]}...')>"
    
    @property
    def is_retryable(self) -> bool:
        """
        Check if this error type is retryable
        """
        retryable_errors = [
            "timeout",
            "connection",
            "rate_limit",
            "server_error",
            "temporary_failure"
        ]
        return self.error_type in retryable_errors
    
    @property
    def severity(self) -> str:
        """
        Get error severity level
        """
        if self.error_type in ["rate_limit", "timeout"]:
            return "low"
        elif self.error_type in ["connection", "server_error"]:
            return "medium"
        elif self.error_type in ["parsing", "authentication"]:
            return "high"
        else:
            return "unknown"
