"""
Tests for database models
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Product, Price, User, PriceAlert
from app.database.connection import get_db


class TestModels:
    """Test cases for database models"""
    
    @pytest.fixture
    def db_session(self):
        """Create a test database session"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    def test_product_creation(self, db_session):
        """Test product model creation"""
        product = Product(
            name="Test Product",
            platform="amazon",
            product_url="https://amazon.com/test-product",
            currency="USD"
        )
        
        db_session.add(product)
        db_session.commit()
        
        assert product.id is not None
        assert product.name == "Test Product"
        assert product.platform == "amazon"
        assert product.is_active == True
        assert product.is_tracking == True
    
    def test_price_creation(self, db_session):
        """Test price model creation"""
        # Create product first
        product = Product(
            name="Test Product",
            platform="amazon",
            product_url="https://amazon.com/test-product",
            currency="USD"
        )
        db_session.add(product)
        db_session.commit()
        
        # Create price
        price = Price(
            product_id=product.id,
            price=29.99,
            currency="USD"
        )
        
        db_session.add(price)
        db_session.commit()
        
        assert price.id is not None
        assert price.product_id == product.id
        assert price.price == 29.99
        assert price.currency == "USD"
    
    def test_user_creation(self, db_session):
        """Test user model creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active == True
    
    def test_price_alert_creation(self, db_session):
        """Test price alert model creation"""
        # Create user and product first
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        
        product = Product(
            name="Test Product",
            platform="amazon",
            product_url="https://amazon.com/test-product",
            currency="USD"
        )
        db_session.add(product)
        db_session.commit()
        
        # Create price alert
        alert = PriceAlert(
            user_id=user.id,
            product_id=product.id,
            alert_type="price_drop",
            target_price=25.00
        )
        
        db_session.add(alert)
        db_session.commit()
        
        assert alert.id is not None
        assert alert.user_id == user.id
        assert alert.product_id == product.id
        assert alert.alert_type == "price_drop"
        assert alert.target_price == 25.00
        assert alert.is_active == True
