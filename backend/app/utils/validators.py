"""
Validation utility functions
"""

import re
import logging
from typing import Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_price(price: Union[str, float, int]) -> Optional[float]:
    """
    Validate and convert price string to float
    """
    try:
        if isinstance(price, (int, float)):
            return float(price) if price >= 0 else None
        
        if isinstance(price, str):
            # Remove currency symbols and extra text
            price_clean = re.sub(r'[^\d.,]', '', price.strip())
            
            if not price_clean:
                return None
            
            # Handle different decimal separators
            if ',' in price_clean and '.' in price_clean:
                # Assume comma is thousands separator
                price_clean = price_clean.replace(',', '')
            elif ',' in price_clean:
                # Check if comma is decimal separator
                parts = price_clean.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    price_clean = price_clean.replace(',', '.')
                else:
                    price_clean = price_clean.replace(',', '')
            
            price_float = float(price_clean)
            return price_float if price_float >= 0 else None
        
        return None
        
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid price format: {price} - {str(e)}")
        return None


def validate_currency(currency: str) -> bool:
    """
    Validate currency code format
    """
    try:
        if not currency or not isinstance(currency, str):
            return False
        
        # Check if it's a 3-letter currency code
        return len(currency) == 3 and currency.isalpha()
        
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """
    Validate email format
    """
    try:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    except Exception:
        return False


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format
    """
    try:
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Check if it has 10-15 digits (international format)
        return 10 <= len(digits) <= 15
        
    except Exception:
        return False


def validate_platform(platform: str) -> bool:
    """
    Validate e-commerce platform
    """
    try:
        supported_platforms = [
            'amazon', 'ebay', 'walmart', 'target', 
            'bestbuy', 'homedepot', 'lowes'
        ]
        return platform.lower() in supported_platforms
    except Exception:
        return False


def validate_alert_type(alert_type: str) -> bool:
    """
    Validate price alert type
    """
    try:
        valid_types = ['price_drop', 'price_increase', 'target_price']
        return alert_type in valid_types
    except Exception:
        return False


def validate_percentage(percentage: Union[str, float, int]) -> Optional[float]:
    """
    Validate percentage value
    """
    try:
        if isinstance(percentage, (int, float)):
            return float(percentage) if 0 <= percentage <= 100 else None
        
        if isinstance(percentage, str):
            # Remove % symbol if present
            percentage_clean = percentage.replace('%', '').strip()
            percentage_float = float(percentage_clean)
            return percentage_float if 0 <= percentage_float <= 100 else None
        
        return None
        
    except (ValueError, TypeError):
        return None


def validate_rating(rating: Union[str, float, int]) -> Optional[float]:
    """
    Validate product rating
    """
    try:
        if isinstance(rating, (int, float)):
            return float(rating) if 0 <= rating <= 5 else None
        
        if isinstance(rating, str):
            rating_float = float(rating)
            return rating_float if 0 <= rating_float <= 5 else None
        
        return None
        
    except (ValueError, TypeError):
        return None


def validate_sku(sku: str) -> bool:
    """
    Validate SKU format
    """
    try:
        if not sku or not isinstance(sku, str):
            return False
        
        # SKU should be alphanumeric and reasonable length
        return 1 <= len(sku) <= 100 and sku.replace('-', '').replace('_', '').isalnum()
        
    except Exception:
        return False


def validate_upc(upc: str) -> bool:
    """
    Validate UPC format
    """
    try:
        if not upc or not isinstance(upc, str):
            return False
        
        # Remove any non-digit characters
        digits = re.sub(r'\D', '', upc)
        
        # UPC should be 12 digits
        return len(digits) == 12 and digits.isdigit()
        
    except Exception:
        return False


def validate_asin(asin: str) -> bool:
    """
    Validate Amazon ASIN format
    """
    try:
        if not asin or not isinstance(asin, str):
            return False
        
        # ASIN should be 10 characters, alphanumeric
        return len(asin) == 10 and asin.isalnum()
        
    except Exception:
        return False
