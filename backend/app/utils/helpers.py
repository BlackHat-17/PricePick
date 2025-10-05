"""
General helper utility functions
"""

import re
import secrets
import string
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def generate_id(length: int = 8, prefix: str = "") -> str:
    """
    Generate a random ID string
    """
    try:
        # Generate random string
        characters = string.ascii_letters + string.digits
        random_string = ''.join(secrets.choice(characters) for _ in range(length))
        
        # Add prefix if provided
        if prefix:
            return f"{prefix}_{random_string}"
        
        return random_string
        
    except Exception as e:
        logger.error(f"Failed to generate ID: {str(e)}")
        return f"id_{int(datetime.utcnow().timestamp())}"


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string by removing unwanted characters and limiting length
    """
    try:
        if not text or not isinstance(text, str):
            return ""
        
        # Remove control characters and normalize whitespace
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Limit length if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip()
        
        return sanitized
        
    except Exception as e:
        logger.error(f"Failed to sanitize string: {str(e)}")
        return ""


def calculate_price_change(old_price: float, new_price: float) -> Dict[str, float]:
    """
    Calculate price change metrics
    """
    try:
        if not old_price or old_price == 0:
            return {
                "change_amount": 0.0,
                "change_percentage": 0.0,
                "is_increase": False,
                "is_decrease": False
            }
        
        change_amount = new_price - old_price
        change_percentage = (change_amount / old_price) * 100
        
        return {
            "change_amount": round(change_amount, 2),
            "change_percentage": round(change_percentage, 2),
            "is_increase": change_amount > 0,
            "is_decrease": change_amount < 0
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate price change: {str(e)}")
        return {
            "change_amount": 0.0,
            "change_percentage": 0.0,
            "is_increase": False,
            "is_decrease": False
        }


def calculate_savings(original_price: float, current_price: float) -> Dict[str, float]:
    """
    Calculate savings metrics
    """
    try:
        if not original_price or original_price == 0:
            return {
                "savings_amount": 0.0,
                "savings_percentage": 0.0,
                "is_on_sale": False
            }
        
        savings_amount = original_price - current_price
        savings_percentage = (savings_amount / original_price) * 100 if original_price > 0 else 0
        
        return {
            "savings_amount": round(max(0, savings_amount), 2),
            "savings_percentage": round(max(0, savings_percentage), 2),
            "is_on_sale": current_price < original_price
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate savings: {str(e)}")
        return {
            "savings_amount": 0.0,
            "savings_percentage": 0.0,
            "is_on_sale": False
        }


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL
    """
    try:
        if not url:
            return None
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.lower()
        
    except Exception as e:
        logger.error(f"Failed to extract domain from URL: {str(e)}")
        return None


def is_valid_email(email: str) -> bool:
    """
    Check if email is valid
    """
    try:
        if not email or not isinstance(email, str):
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
        
    except Exception:
        return False


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid
    """
    try:
        if not url or not isinstance(url, str):
            return False
        
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
        
    except Exception:
        return False


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """
    Hash a string using specified algorithm
    """
    try:
        if not text:
            return ""
        
        if algorithm == "md5":
            return hashlib.md5(text.encode()).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(text.encode()).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(text.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
    except Exception as e:
        logger.error(f"Failed to hash string: {str(e)}")
        return ""


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size
    """
    try:
        if not lst or chunk_size <= 0:
            return []
        
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
        
    except Exception as e:
        logger.error(f"Failed to chunk list: {str(e)}")
        return []


def remove_duplicates(lst: List[Any]) -> List[Any]:
    """
    Remove duplicates from list while preserving order
    """
    try:
        if not lst:
            return []
        
        seen = set()
        result = []
        
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to remove duplicates: {str(e)}")
        return lst


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries, with dict2 taking precedence
    """
    try:
        if not dict1:
            return dict2 or {}
        if not dict2:
            return dict1 or {}
        
        result = dict1.copy()
        result.update(dict2)
        return result
        
    except Exception as e:
        logger.error(f"Failed to merge dictionaries: {str(e)}")
        return dict1 or {}


def get_nested_value(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get nested value from dictionary using dot notation
    """
    try:
        if not data or not key_path:
            return default
        
        keys = key_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
        
    except Exception as e:
        logger.error(f"Failed to get nested value: {str(e)}")
        return default


def set_nested_value(data: Dict[str, Any], key_path: str, value: Any) -> bool:
    """
    Set nested value in dictionary using dot notation
    """
    try:
        if not data or not key_path:
            return False
        
        keys = key_path.split('.')
        current = data
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
        return True
        
    except Exception as e:
        logger.error(f"Failed to set nested value: {str(e)}")
        return False


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes to human readable format
    """
    try:
        if bytes_size < 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while bytes_size >= 1024 and i < len(size_names) - 1:
            bytes_size /= 1024.0
            i += 1
        
        return f"{bytes_size:.1f} {size_names[i]}"
        
    except Exception:
        return "0 B"


def time_ago(dt: datetime) -> str:
    """
    Get human readable time ago string
    """
    try:
        if not dt:
            return "Unknown"
        
        now = datetime.utcnow()
        if dt.tzinfo is not None:
            now = now.replace(tzinfo=dt.tzinfo)
        
        diff = now - dt
        
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
        return "Unknown"
