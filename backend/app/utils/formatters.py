"""
Formatting utility functions
"""

import re
from typing import Optional, Union
from decimal import Decimal, ROUND_HALF_UP


def format_price(price: Union[float, int, str], currency: str = "USD", decimal_places: int = 2) -> str:
    """
    Format price with currency symbol
    """
    try:
        if price is None:
            return "N/A"
        
        # Convert to float
        price_float = float(price)
        
        # Round to specified decimal places
        price_rounded = round(price_float, decimal_places)
        
        # Format with currency symbol
        currency_symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "CAD": "C$",
            "AUD": "A$"
        }
        
        symbol = currency_symbols.get(currency.upper(), currency.upper() + " ")
        
        if currency.upper() == "JPY":
            # Japanese Yen doesn't use decimal places
            return f"{symbol}{price_rounded:,.0f}"
        else:
            return f"{symbol}{price_rounded:,.2f}"
            
    except (ValueError, TypeError):
        return "N/A"


def format_percentage(percentage: Union[float, int, str], decimal_places: int = 2) -> str:
    """
    Format percentage with proper sign and symbol
    """
    try:
        if percentage is None:
            return "N/A"
        
        # Convert to float
        percentage_float = float(percentage)
        
        # Round to specified decimal places
        percentage_rounded = round(percentage_float, decimal_places)
        
        # Add sign and percentage symbol
        if percentage_rounded > 0:
            return f"+{percentage_rounded}%"
        else:
            return f"{percentage_rounded}%"
            
    except (ValueError, TypeError):
        return "N/A"


def format_currency(amount: Union[float, int, str], currency: str = "USD") -> str:
    """
    Format currency amount with proper formatting
    """
    try:
        if amount is None:
            return "N/A"
        
        # Convert to float
        amount_float = float(amount)
        
        # Format based on currency
        if currency.upper() == "USD":
            return f"${amount_float:,.2f}"
        elif currency.upper() == "EUR":
            return f"€{amount_float:,.2f}"
        elif currency.upper() == "GBP":
            return f"£{amount_float:,.2f}"
        elif currency.upper() == "JPY":
            return f"¥{amount_float:,.0f}"
        else:
            return f"{currency.upper()} {amount_float:,.2f}"
            
    except (ValueError, TypeError):
        return "N/A"


def format_number(number: Union[float, int, str], decimal_places: int = 2) -> str:
    """
    Format number with thousands separator
    """
    try:
        if number is None:
            return "N/A"
        
        # Convert to float
        number_float = float(number)
        
        # Round to specified decimal places
        number_rounded = round(number_float, decimal_places)
        
        # Format with thousands separator
        return f"{number_rounded:,.{decimal_places}f}"
        
    except (ValueError, TypeError):
        return "N/A"


def format_rating(rating: Union[float, int, str], max_rating: int = 5) -> str:
    """
    Format product rating
    """
    try:
        if rating is None:
            return "N/A"
        
        # Convert to float
        rating_float = float(rating)
        
        # Ensure rating is within valid range
        if rating_float < 0:
            rating_float = 0
        elif rating_float > max_rating:
            rating_float = max_rating
        
        # Format with stars
        stars = "★" * int(rating_float)
        half_star = "☆" if rating_float % 1 >= 0.5 else ""
        empty_stars = "☆" * (max_rating - int(rating_float) - (1 if half_star else 0))
        
        return f"{stars}{half_star}{empty_stars} ({rating_float:.1f})"
        
    except (ValueError, TypeError):
        return "N/A"


def format_duration(seconds: Union[float, int]) -> str:
    """
    Format duration in seconds to human readable format
    """
    try:
        if seconds is None or seconds < 0:
            return "N/A"
        
        seconds = int(seconds)
        
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds}s"
        elif seconds < 86400:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            return f"{hours}h {remaining_minutes}m"
        else:
            days = seconds // 86400
            remaining_hours = (seconds % 86400) // 3600
            return f"{days}d {remaining_hours}h"
            
    except (ValueError, TypeError):
        return "N/A"


def format_file_size(bytes_size: Union[float, int]) -> str:
    """
    Format file size in bytes to human readable format
    """
    try:
        if bytes_size is None or bytes_size < 0:
            return "N/A"
        
        bytes_size = int(bytes_size)
        
        if bytes_size == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while bytes_size >= 1024 and i < len(size_names) - 1:
            bytes_size /= 1024.0
            i += 1
        
        return f"{bytes_size:.1f} {size_names[i]}"
        
    except (ValueError, TypeError):
        return "N/A"


def format_phone(phone: str) -> str:
    """
    Format phone number
    """
    try:
        if not phone:
            return "N/A"
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) == 10:
            # US format: (XXX) XXX-XXXX
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            # US format with country code: +1 (XXX) XXX-XXXX
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            # International format
            return f"+{digits}"
            
    except Exception:
        return phone


def format_date(date, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format date to string
    """
    try:
        if date is None:
            return "N/A"
        
        if hasattr(date, 'strftime'):
            return date.strftime(format_str)
        else:
            return str(date)
            
    except Exception:
        return "N/A"


def format_relative_time(date) -> str:
    """
    Format date as relative time (e.g., "2 hours ago")
    """
    try:
        if date is None:
            return "N/A"
        
        from datetime import datetime, timezone
        
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        
        now = datetime.now(timezone.utc)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        
        diff = now - date
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
            
    except Exception:
        return "N/A"
