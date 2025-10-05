"""
Web scraping utility functions
"""

import re
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def extract_price(html: str, selectors: List[str]) -> Optional[float]:
    """
    Extract price from HTML using CSS selectors
    """
    try:
        if not html or not selectors:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get_text(strip=True)
                price = _parse_price_text(price_text)
                if price:
                    return price
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to extract price: {str(e)}")
        return None


def extract_title(html: str, selectors: List[str]) -> Optional[str]:
    """
    Extract product title from HTML using CSS selectors
    """
    try:
        if not html or not selectors:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title:
                    return title
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to extract title: {str(e)}")
        return None


def extract_availability(html: str, selectors: List[str]) -> Optional[str]:
    """
    Extract availability status from HTML using CSS selectors
    """
    try:
        if not html or not selectors:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                availability = element.get_text(strip=True)
                if availability:
                    return availability
        
        # Check for common availability patterns in page text
        page_text = soup.get_text().lower()
        if "in stock" in page_text or "available" in page_text:
            return "In Stock"
        elif "out of stock" in page_text or "unavailable" in page_text:
            return "Out of Stock"
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to extract availability: {str(e)}")
        return None


def extract_image_url(html: str, selectors: List[str]) -> Optional[str]:
    """
    Extract product image URL from HTML using CSS selectors
    """
    try:
        if not html or not selectors:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                img_src = element.get('src') or element.get('data-src')
                if img_src:
                    # Convert relative URLs to absolute
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    elif img_src.startswith('/'):
                        # This would need the base URL to be passed in
                        pass
                    
                    return img_src
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to extract image URL: {str(e)}")
        return None


def extract_rating(html: str, selectors: List[str]) -> Optional[float]:
    """
    Extract product rating from HTML using CSS selectors
    """
    try:
        if not html or not selectors:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                rating_text = element.get_text(strip=True)
                rating = _parse_rating_text(rating_text)
                if rating:
                    return rating
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to extract rating: {str(e)}")
        return None


def extract_review_count(html: str, selectors: List[str]) -> Optional[int]:
    """
    Extract review count from HTML using CSS selectors
    """
    try:
        if not html or not selectors:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                count_text = element.get_text(strip=True)
                count = _parse_review_count_text(count_text)
                if count:
                    return count
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to extract review count: {str(e)}")
        return None


def extract_metadata(html: str, selectors: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract multiple metadata fields from HTML using CSS selectors
    """
    try:
        if not html or not selectors:
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {}
        
        for field, selector in selectors.items():
            element = soup.select_one(selector)
            if element:
                value = element.get_text(strip=True)
                if value:
                    metadata[field] = value
        
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to extract metadata: {str(e)}")
        return {}


def _parse_price_text(price_text: str) -> Optional[float]:
    """
    Parse price from text string
    """
    try:
        if not price_text:
            return None
        
        # Remove currency symbols and extra text
        price_clean = re.sub(r'[^\d.,]', '', price_text)
        
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
        
    except (ValueError, TypeError):
        return None


def _parse_rating_text(rating_text: str) -> Optional[float]:
    """
    Parse rating from text string
    """
    try:
        if not rating_text:
            return None
        
        # Extract number from rating text (e.g., "4.5 out of 5 stars" -> 4.5)
        match = re.search(r'(\d+\.?\d*)', rating_text)
        if match:
            rating = float(match.group(1))
            return rating if 0 <= rating <= 5 else None
        
        return None
        
    except (ValueError, TypeError):
        return None


def _parse_review_count_text(count_text: str) -> Optional[int]:
    """
    Parse review count from text string
    """
    try:
        if not count_text:
            return None
        
        # Extract number from count text (e.g., "1,234 reviews" -> 1234)
        match = re.search(r'(\d+(?:,\d+)*)', count_text)
        if match:
            return int(match.group(1).replace(',', ''))
        
        return None
        
    except (ValueError, TypeError):
        return None


def clean_html(html: str) -> str:
    """
    Clean HTML by removing scripts, styles, and other unwanted elements
    """
    try:
        if not html:
            return ""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
        
    except Exception as e:
        logger.error(f"Failed to clean HTML: {str(e)}")
        return html


def extract_links(html: str, base_url: str = None) -> List[str]:
    """
    Extract all links from HTML
    """
    try:
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            if base_url and href.startswith('/'):
                href = base_url.rstrip('/') + href
            elif href.startswith('//'):
                href = 'https:' + href
            
            links.append(href)
        
        return links
        
    except Exception as e:
        logger.error(f"Failed to extract links: {str(e)}")
        return []


def extract_images(html: str, base_url: str = None) -> List[str]:
    """
    Extract all image URLs from HTML
    """
    try:
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        images = []
        
        for img in soup.find_all('img', src=True):
            src = img['src']
            
            # Convert relative URLs to absolute
            if base_url and src.startswith('/'):
                src = base_url.rstrip('/') + src
            elif src.startswith('//'):
                src = 'https:' + src
            
            images.append(src)
        
        return images
        
    except Exception as e:
        logger.error(f"Failed to extract images: {str(e)}")
        return []
