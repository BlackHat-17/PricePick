"""
Web scraping service for extracting product data from e-commerce sites
"""

import asyncio
import httpx
import re
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import time
import random

from app.models.product import Product
from app.models.price import Price
from app.models.scraping import ScrapingSession, ScrapingError
from config import SCRAPING_CONFIG, SUPPORTED_PLATFORMS

logger = logging.getLogger(__name__)


class ScrapingService:
    """
    Service class for web scraping operations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.config = SCRAPING_CONFIG
        self.platforms = SUPPORTED_PLATFORMS
    
    async def search_products(self, query: str, limit_per_platform: int = 5, platforms: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search products across multiple platforms concurrently.
        This uses lightweight HTML queries where possible; production setups
        should use official APIs when available to reduce scraping risk.
        """
        target_platforms = platforms or list(self.platforms.keys())
        results: List[Dict[str, Any]] = []
        
        async def search_platform(platform_key: str) -> List[Dict[str, Any]]:
            try:
                # For demonstration, we build basic search URLs. Real selectors differ per site.
                search_urls = {
                    "amazon": f"https://www.amazon.com/s?k={httpx.QueryParams({'k': query})['k']}",
                    "ebay": f"https://www.ebay.com/sch/i.html?_nkw={httpx.QueryParams({'_nkw': query})['_nkw']}",
                    "walmart": f"https://www.walmart.com/search?q={httpx.QueryParams({'q': query})['q']}"
                }
                search_url = search_urls.get(platform_key)
                if not search_url:
                    return []
                
                platform_results: List[Dict[str, Any]] = []
                async with httpx.AsyncClient(
                    timeout=self.config["timeout"],
                    headers=self.config["headers"],
                    follow_redirects=True
                ) as client:
                    response = await client.get(search_url)
                    if response.status_code != 200:
                        return []
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Very naive selectors; replace with robust ones per site
                    if platform_key == "amazon":
                        for card in soup.select('div.s-result-item')[:limit_per_platform]:
                            title_el = card.select_one('h2 a.a-link-normal')
                            price_whole = card.select_one('.a-price-whole')
                            price_fraction = card.select_one('.a-price-fraction')
                            img = card.select_one('img.s-image')
                            if title_el and title_el.get('href'):
                                title = title_el.get_text(strip=True)
                                url = title_el['href']
                                if url and url.startswith('/'):
                                    url = f"https://www.amazon.com{url}"
                                price = None
                                if price_whole:
                                    price_text = price_whole.get_text(strip=True) + (price_fraction.get_text(strip=True) if price_fraction else '')
                                    price_text = price_text.replace(',', '')
                                    try:
                                        price = float(price_text)
                                    except Exception:
                                        price = None
                                platform_results.append({
                                    "platform": platform_key,
                                    "title": title,
                                    "price": price,
                                    "currency": "USD",
                                    "product_url": url,
                                    "image_url": img['src'] if img and img.get('src') else None,
                                })
                    elif platform_key == "ebay":
                        for card in soup.select('li.s-item')[:limit_per_platform]:
                            title_el = card.select_one('a.s-item__link')
                            price_el = card.select_one('.s-item__price')
                            img = card.select_one('img.s-item__image-img')
                            if title_el and title_el.get('href'):
                                title = title_el.get_text(strip=True)
                                url = title_el['href']
                                price = None
                                if price_el:
                                    txt = price_el.get_text(strip=True).replace('$', '').replace(',', '')
                                    try:
                                        price = float(re.findall(r"\d+(?:\.\d+)?", txt)[0]) if re.findall(r"\d+(?:\.\d+)?", txt) else None
                                    except Exception:
                                        price = None
                                platform_results.append({
                                    "platform": platform_key,
                                    "title": title,
                                    "price": price,
                                    "currency": "USD",
                                    "product_url": url,
                                    "image_url": img['src'] if img and img.get('src') else None,
                                })
                    elif platform_key == "walmart":
                        for card in soup.select('div.mb0.ph0-xl')[:limit_per_platform]:
                            title_el = card.select_one('a[data-automation-id="product-title"]')
                            price_el = card.select_one('[data-automation-id="product-price"]')
                            img = card.select_one('img')
                            if title_el and title_el.get('href'):
                                title = title_el.get_text(strip=True)
                                url = title_el['href']
                                if url and url.startswith('/'):
                                    url = f"https://www.walmart.com{url}"
                                price = None
                                if price_el:
                                    txt = price_el.get_text(strip=True).replace('$', '').replace(',', '')
                                    try:
                                        price = float(re.findall(r"\d+(?:\.\d+)?", txt)[0]) if re.findall(r"\d+(?:\.\d+)?", txt) else None
                                    except Exception:
                                        price = None
                                platform_results.append({
                                    "platform": platform_key,
                                    "title": title,
                                    "price": price,
                                    "currency": "USD",
                                    "product_url": url,
                                    "image_url": img['src'] if img and img.get('src') else None,
                                })
                return platform_results
            except Exception as e:
                logger.warning(f"Search failed for {platform_key}: {str(e)}")
                return []
        
        tasks = [search_platform(p) for p in target_platforms]
        groups = await asyncio.gather(*tasks, return_exceptions=True)
        for group in groups:
            if isinstance(group, list):
                results.extend(group)
        return results
    
    async def scrape_product(self, product: Product, force: bool = False) -> Dict[str, Any]:
        """
        Scrape product data from its URL
        """
        session_id = f"scrape_{product.id}_{int(time.time())}"
        
        # Create scraping session
        session = ScrapingSession(
            session_id=session_id,
            product_id=product.id,
            platform=product.platform,
            url=product.product_url,
            status="pending"
        )
        
        try:
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            # Start session
            session.start_session()
            self.db.commit()
            
            # Perform scraping
            result = await self._scrape_product_data(product, session)
            
            # Update session
            session.complete_session(success=result["success"])
            if result["success"]:
                session.scraped_price = str(result.get("price", ""))
                session.scraped_title = result.get("title", "")
                session.scraped_availability = result.get("availability", "")
                session.scraped_image_url = result.get("image_url", "")
                session.scraped_rating = str(result.get("rating", ""))
                session.scraped_review_count = str(result.get("review_count", ""))
                session.price_found = bool(result.get("price"))
                session.title_found = bool(result.get("title"))
                session.availability_found = bool(result.get("availability"))
            
            self.db.commit()
            
            # Create price record if successful
            if result["success"] and result.get("price"):
                await self._create_price_record(product, result, session)
            
            return result
            
        except Exception as e:
            logger.error(f"Scraping failed for product {product.id}: {str(e)}")
            
            # Record error
            error = ScrapingError(
                scraping_session_id=session.id,
                error_type="scraping_error",
                error_message=str(e),
                url=product.product_url,
                stack_trace=str(e)
            )
            self.db.add(error)
            
            # Update session
            session.fail_session(str(e), "scraping_error")
            self.db.commit()
            
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def _scrape_product_data(self, product: Product, session: ScrapingSession) -> Dict[str, Any]:
        """
        Perform the actual scraping of product data
        """
        try:
            # Get platform configuration
            platform_config = self.platforms.get(product.platform)
            if not platform_config:
                raise Exception(f"Unsupported platform: {product.platform}")
            
            # Make HTTP request
            async with httpx.AsyncClient(
                timeout=self.config["timeout"],
                headers=self.config["headers"],
                follow_redirects=True
            ) as client:
                
                start_time = time.time()
                response = await client.get(product.product_url)
                response_time = int((time.time() - start_time) * 1000)
                
                # Update session with response info
                session.response_time_ms = response_time
                session.http_status_code = response.status_code
                session.headers_received = dict(response.headers)
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.reason_phrase}")
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract data
                result = {
                    "success": True,
                    "price": None,
                    "title": None,
                    "availability": None,
                    "image_url": None,
                    "rating": None,
                    "review_count": None
                }
                
                # Extract price
                result["price"] = self._extract_price(soup, product, platform_config)
                
                # Extract title
                result["title"] = self._extract_title(soup, product, platform_config)
                
                # Extract availability
                result["availability"] = self._extract_availability(soup, product, platform_config)
                
                # Extract image URL
                result["image_url"] = self._extract_image_url(soup, product, platform_config)
                
                # Extract rating
                result["rating"] = self._extract_rating(soup, product, platform_config)
                
                # Extract review count
                result["review_count"] = self._extract_review_count(soup, product, platform_config)
                
                return result
                
        except Exception as e:
            logger.error(f"Scraping error for product {product.id}: {str(e)}")
            raise
    
    def _extract_price(self, soup: BeautifulSoup, product: Product, platform_config: Dict) -> Optional[float]:
        """
        Extract price from HTML
        """
        try:
            # Use custom selector if available
            if product.price_selector:
                selectors = [product.price_selector]
            else:
                selectors = platform_config.get("price_selectors", [])
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    price_text = element.get_text(strip=True)
                    price = self._parse_price(price_text)
                    if price:
                        return price
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract price for product {product.id}: {str(e)}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup, product: Product, platform_config: Dict) -> Optional[str]:
        """
        Extract product title from HTML
        """
        try:
            # Use custom selector if available
            if product.title_selector:
                selectors = [product.title_selector]
            else:
                selectors = platform_config.get("title_selectors", [])
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text(strip=True)
                    if title:
                        return title
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract title for product {product.id}: {str(e)}")
            return None
    
    def _extract_availability(self, soup: BeautifulSoup, product: Product, platform_config: Dict) -> Optional[str]:
        """
        Extract availability status from HTML
        """
        try:
            # Use custom selector if available
            if product.availability_selector:
                selectors = [product.availability_selector]
            else:
                # Common availability indicators
                selectors = [
                    "[data-automation-id='product-availability']",
                    ".availability",
                    ".stock-status",
                    ".in-stock",
                    ".out-of-stock"
                ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    availability = element.get_text(strip=True)
                    if availability:
                        return availability
            
            # Check for common availability patterns
            page_text = soup.get_text().lower()
            if "in stock" in page_text or "available" in page_text:
                return "In Stock"
            elif "out of stock" in page_text or "unavailable" in page_text:
                return "Out of Stock"
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract availability for product {product.id}: {str(e)}")
            return None
    
    def _extract_image_url(self, soup: BeautifulSoup, product: Product, platform_config: Dict) -> Optional[str]:
        """
        Extract product image URL from HTML
        """
        try:
            # Common image selectors
            selectors = [
                "[data-automation-id='product-image'] img",
                ".product-image img",
                "#landingImage",
                ".a-dynamic-image",
                ".prod-image img"
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    img_src = element.get('src') or element.get('data-src')
                    if img_src:
                        # Convert relative URLs to absolute
                        if img_src.startswith('//'):
                            img_src = 'https:' + img_src
                        elif img_src.startswith('/'):
                            base_url = platform_config.get("base_url", "")
                            img_src = base_url + img_src
                        
                        return img_src
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract image URL for product {product.id}: {str(e)}")
            return None
    
    def _extract_rating(self, soup: BeautifulSoup, product: Product, platform_config: Dict) -> Optional[float]:
        """
        Extract product rating from HTML
        """
        try:
            # Common rating selectors
            selectors = [
                "[data-automation-id='product-rating']",
                ".rating",
                ".stars",
                ".review-rating",
                ".a-icon-alt"
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    rating_text = element.get_text(strip=True)
                    rating = self._parse_rating(rating_text)
                    if rating:
                        return rating
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract rating for product {product.id}: {str(e)}")
            return None
    
    def _extract_review_count(self, soup: BeautifulSoup, product: Product, platform_config: Dict) -> Optional[int]:
        """
        Extract review count from HTML
        """
        try:
            # Common review count selectors
            selectors = [
                "[data-automation-id='product-review-count']",
                ".review-count",
                ".num-reviews",
                ".review-text"
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    count_text = element.get_text(strip=True)
                    count = self._parse_review_count(count_text)
                    if count:
                        return count
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract review count for product {product.id}: {str(e)}")
            return None
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """
        Parse price from text
        """
        try:
            # Remove currency symbols and extra text
            price_text = re.sub(r'[^\d.,]', '', price_text)
            
            # Handle different decimal separators
            if ',' in price_text and '.' in price_text:
                # Assume comma is thousands separator
                price_text = price_text.replace(',', '')
            elif ',' in price_text:
                # Check if comma is decimal separator
                parts = price_text.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    price_text = price_text.replace(',', '.')
                else:
                    price_text = price_text.replace(',', '')
            
            return float(price_text)
            
        except (ValueError, TypeError):
            return None
    
    def _parse_rating(self, rating_text: str) -> Optional[float]:
        """
        Parse rating from text
        """
        try:
            # Extract number from rating text (e.g., "4.5 out of 5 stars" -> 4.5)
            match = re.search(r'(\d+\.?\d*)', rating_text)
            if match:
                return float(match.group(1))
            return None
        except (ValueError, TypeError):
            return None
    
    def _parse_review_count(self, count_text: str) -> Optional[int]:
        """
        Parse review count from text
        """
        try:
            # Extract number from count text (e.g., "1,234 reviews" -> 1234)
            match = re.search(r'(\d+(?:,\d+)*)', count_text)
            if match:
                return int(match.group(1).replace(',', ''))
            return None
        except (ValueError, TypeError):
            return None
    
    async def _create_price_record(self, product: Product, result: Dict[str, Any], session: ScrapingSession) -> None:
        """
        Create a new price record from scraping result
        """
        try:
            if not result.get("price"):
                return
            
            # Check if price has changed significantly
            last_price = self.db.query(Price).filter(
                Price.product_id == product.id
            ).order_by(Price.created_at.desc()).first()
            
            if last_price and last_price.price == result["price"]:
                # Price hasn't changed, skip creating new record
                return
            
            # Create new price record
            price = Price(
                product_id=product.id,
                price=result["price"],
                currency=product.currency,
                original_price=product.original_price,
                is_sale=result["price"] < (product.original_price or result["price"]),
                is_available=result.get("availability", "").lower() not in ["out of stock", "unavailable"],
                scraping_session_id=session.id,
                source_url=product.product_url
            )
            
            # Calculate price change if we have a previous price
            if last_price:
                price.price_change_amount = result["price"] - last_price.price
                if last_price.price > 0:
                    price.price_change_percentage = (price.price_change_amount / last_price.price) * 100
            
            self.db.add(price)
            
            # Update product with new price
            product.current_price = result["price"]
            if not product.original_price:
                product.original_price = result["price"]
            
            # Update other product fields if available
            if result.get("title") and not product.name:
                product.name = result["title"]
            if result.get("image_url") and not product.image_url:
                product.image_url = result["image_url"]
            if result.get("rating") and not product.rating:
                product.rating = result["rating"]
            if result.get("review_count") and not product.review_count:
                product.review_count = result["review_count"]
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create price record for product {product.id}: {str(e)}")
            raise
    
    async def scrape_multiple_products(self, products: List[Product], max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """
        Scrape multiple products concurrently
        """
        try:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def scrape_with_semaphore(product):
                async with semaphore:
                    return await self.scrape_product(product)
            
            tasks = [scrape_with_semaphore(product) for product in products]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return results
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Scraping failed for product {products[i].id}: {str(result)}")
                    valid_results.append({
                        "product_id": products[i].id,
                        "success": False,
                        "error": str(result)
                    })
                else:
                    valid_results.append(result)
            
            return valid_results
            
        except Exception as e:
            logger.error(f"Failed to scrape multiple products: {str(e)}")
            raise
