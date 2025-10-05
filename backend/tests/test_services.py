"""
Tests for service classes
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.product_service import ProductService
from app.services.user_service import UserService
from app.services.scraping_service import ScrapingService
from app.schemas.product import ProductCreate
from app.schemas.user import UserCreate


class TestProductService:
    """Test cases for ProductService"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock()
    
    @pytest.fixture
    def product_service(self, mock_db):
        """Create ProductService instance with mock DB"""
        return ProductService(mock_db)
    
    def test_create_product(self, product_service, mock_db):
        """Test product creation"""
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Create product data
        product_data = ProductCreate(
            name="Test Product",
            platform="amazon",
            product_url="https://amazon.com/test-product",
            currency="USD"
        )
        
        # Mock the product instance
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Test Product"
        mock_db.add.return_value = mock_product
        
        # Test product creation
        result = product_service.create_product(product_data)
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()


class TestUserService:
    """Test cases for UserService"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock()
    
    @pytest.fixture
    def user_service(self, mock_db):
        """Create UserService instance with mock DB"""
        return UserService(mock_db)
    
    def test_create_user(self, user_service, mock_db):
        """Test user creation"""
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Create user data
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPassword123"
        )
        
        # Mock the user instance
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_db.add.return_value = mock_user
        
        # Test user creation
        result = user_service.create_user(user_data)
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()


class TestScrapingService:
    """Test cases for ScrapingService"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock()
    
    @pytest.fixture
    def scraping_service(self, mock_db):
        """Create ScrapingService instance with mock DB"""
        return ScrapingService(mock_db)
    
    @patch('app.services.scraping_service.httpx.AsyncClient')
    def test_scrape_product(self, mock_client, scraping_service, mock_db):
        """Test product scraping"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body><span class='price'>$29.99</span></body></html>"
        mock_response.headers = {}
        
        # Mock async client
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Create mock product
        mock_product = Mock()
        mock_product.id = 1
        mock_product.platform = "amazon"
        mock_product.product_url = "https://amazon.com/test-product"
        mock_product.price_selector = None
        mock_product.title_selector = None
        mock_product.availability_selector = None
        
        # Test scraping
        result = scraping_service.scrape_product(mock_product)
        
        # Verify HTTP request was made
        mock_client_instance.get.assert_called_once_with(mock_product.product_url)
        
        # Verify result structure
        assert "success" in result
        assert "price" in result
