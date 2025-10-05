"""
Tests for utility functions
"""

import pytest
from datetime import datetime

from app.utils.validators import validate_url, validate_price, validate_currency
from app.utils.formatters import format_price, format_percentage, format_currency
from app.utils.helpers import calculate_price_change, calculate_savings


class TestValidators:
    """Test cases for validation utilities"""
    
    def test_validate_url(self):
        """Test URL validation"""
        assert validate_url("https://example.com") == True
        assert validate_url("http://example.com") == True
        assert validate_url("https://www.example.com/path") == True
        assert validate_url("invalid-url") == False
        assert validate_url("") == False
        assert validate_url(None) == False
    
    def test_validate_price(self):
        """Test price validation"""
        assert validate_price("29.99") == 29.99
        assert validate_price("$29.99") == 29.99
        assert validate_price("29,99") == 29.99
        assert validate_price(29.99) == 29.99
        assert validate_price("invalid") == None
        assert validate_price("") == None
        assert validate_price(None) == None
    
    def test_validate_currency(self):
        """Test currency validation"""
        assert validate_currency("USD") == True
        assert validate_currency("EUR") == True
        assert validate_currency("GBP") == True
        assert validate_currency("US") == False
        assert validate_currency("") == False
        assert validate_currency(None) == False


class TestFormatters:
    """Test cases for formatting utilities"""
    
    def test_format_price(self):
        """Test price formatting"""
        assert format_price(29.99, "USD") == "$29.99"
        assert format_price(29.99, "EUR") == "€29.99"
        assert format_price(29.99, "GBP") == "£29.99"
        assert format_price(29.99, "JPY") == "¥30"
        assert format_price(None) == "N/A"
    
    def test_format_percentage(self):
        """Test percentage formatting"""
        assert format_percentage(5.5) == "+5.5%"
        assert format_percentage(-3.2) == "-3.2%"
        assert format_percentage(0) == "0.0%"
        assert format_percentage(None) == "N/A"
    
    def test_format_currency(self):
        """Test currency formatting"""
        assert format_currency(29.99, "USD") == "$29.99"
        assert format_currency(29.99, "EUR") == "€29.99"
        assert format_currency(29.99, "GBP") == "£29.99"
        assert format_currency(29.99, "JPY") == "¥30"
        assert format_currency(None) == "N/A"


class TestHelpers:
    """Test cases for helper utilities"""
    
    def test_calculate_price_change(self):
        """Test price change calculation"""
        result = calculate_price_change(100.0, 120.0)
        assert result["change_amount"] == 20.0
        assert result["change_percentage"] == 20.0
        assert result["is_increase"] == True
        assert result["is_decrease"] == False
        
        result = calculate_price_change(100.0, 80.0)
        assert result["change_amount"] == -20.0
        assert result["change_percentage"] == -20.0
        assert result["is_increase"] == False
        assert result["is_decrease"] == True
    
    def test_calculate_savings(self):
        """Test savings calculation"""
        result = calculate_savings(100.0, 80.0)
        assert result["savings_amount"] == 20.0
        assert result["savings_percentage"] == 20.0
        assert result["is_on_sale"] == True
        
        result = calculate_savings(100.0, 120.0)
        assert result["savings_amount"] == 0.0
        assert result["savings_percentage"] == 0.0
        assert result["is_on_sale"] == False
