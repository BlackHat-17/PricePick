"""
Web scraping service for extracting product data from e-commerce sites (Firebase Firestore version)
"""

import asyncio
import httpx
import re
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import time
import random

from firebase_admin import firestore
from config import SCRAPING_CONFIG, SUPPORTED_PLATFORMS

logger = logging.getLogger(__name__)
db = firestore.client()


class ScrapingService:
    """
    Firebase Firestore-based Scraping Service
    """

    def __init__(self):
        self.config = SCRAPING_CONFIG
        self.platforms = SUPPORTED_PLATFORMS
        self.products_ref = db.collection("products")
        self.prices_ref = db.collection("prices")
        self.sessions_ref = db.collection("scraping_sessions")
        self.errors_ref = db.collection("scraping_errors")

    # ---------------------------------
    # Search Products (Amazon, eBay, Walmart)
    # ---------------------------------
    async def search_products(
        self,
        query: str,
        limit_per_platform: int = 5,
        platforms: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search products across supported platforms concurrently.
        """
        target_platforms = platforms or list(self.platforms.keys())
        results: List[Dict[str, Any]] = []

        async def search_platform(platform_key: str) -> List[Dict[str, Any]]:
            try:
                search_urls = {
                    "amazon": f"https://www.amazon.com/s?k={query}",
                    "ebay": f"https://www.ebay.com/sch/i.html?_nkw={query}",
                    "walmart": f"https://www.walmart.com/search?q={query}",
                }
                search_url = search_urls.get(platform_key)
                if not search_url:
                    return []

                platform_results: List[Dict[str, Any]] = []
                async with httpx.AsyncClient(
                    timeout=self.config["timeout"],
                    headers=self.config["headers"],
                    follow_redirects=True,
                ) as client:
                    response = await client.get(search_url)
                    if response.status_code != 200:
                        return []

                    soup = BeautifulSoup(response.content, "html.parser")
                    if platform_key == "amazon":
                        for card in soup.select("div.s-result-item")[:limit_per_platform]:
                            title_el = card.select_one("h2 a.a-link-normal")
                            price_whole = card.select_one(".a-price-whole")
                            price_fraction = card.select_one(".a-price-fraction")
                            img = card.select_one("img.s-image")
                            if not title_el or not title_el.get("href"):
                                continue
                            title = title_el.get_text(strip=True)
                            url = title_el["href"]
                            if url.startswith("/"):
                                url = f"https://www.amazon.com{url}"
                            price = None
                            if price_whole:
                                price_text = (
                                    price_whole.get_text(strip=True)
                                    + (price_fraction.get_text(strip=True) if price_fraction else "")
                                )
                                price_text = price_text.replace(",", "")
                                try:
                                    price = float(price_text)
                                except:
                                    price = None
                            platform_results.append(
                                {
                                    "platform": "amazon",
                                    "title": title,
                                    "price": price,
                                    "currency": "USD",
                                    "product_url": url,
                                    "image_url": img["src"] if img and img.get("src") else None,
                                }
                            )
                    elif platform_key == "ebay":
                        for card in soup.select("li.s-item")[:limit_per_platform]:
                            title_el = card.select_one("a.s-item__link")
                            price_el = card.select_one(".s-item__price")
                            img = card.select_one("img.s-item__image-img")
                            if not title_el or not title_el.get("href"):
                                continue
                            title = title_el.get_text(strip=True)
                            url = title_el["href"]
                            price = None
                            if price_el:
                                txt = price_el.get_text(strip=True).replace("$", "").replace(",", "")
                                try:
                                    price = float(re.findall(r"\d+(?:\.\d+)?", txt)[0])
                                except:
                                    price = None
                            platform_results.append(
                                {
                                    "platform": "ebay",
                                    "title": title,
                                    "price": price,
                                    "currency": "USD",
                                    "product_url": url,
                                    "image_url": img["src"] if img and img.get("src") else None,
                                }
                            )
                    elif platform_key == "walmart":
                        for card in soup.select("div.mb0.ph0-xl")[:limit_per_platform]:
                            title_el = card.select_one('a[data-automation-id="product-title"]')
                            price_el = card.select_one('[data-automation-id="product-price"]')
                            img = card.select_one("img")
                            if not title_el or not title_el.get("href"):
                                continue
                            title = title_el.get_text(strip=True)
                            url = title_el["href"]
                            if url.startswith("/"):
                                url = f"https://www.walmart.com{url}"
                            price = None
                            if price_el:
                                txt = price_el.get_text(strip=True).replace("$", "").replace(",", "")
                                try:
                                    price = float(re.findall(r"\d+(?:\.\d+)?", txt)[0])
                                except:
                                    price = None
                            platform_results.append(
                                {
                                    "platform": "walmart",
                                    "title": title,
                                    "price": price,
                                    "currency": "USD",
                                    "product_url": url,
                                    "image_url": img["src"] if img and img.get("src") else None,
                                }
                            )

                return platform_results
            except Exception as e:
                logger.warning(f"Search failed for {platform_key}: {e}")
                return []

        tasks = [search_platform(p) for p in target_platforms]
        results_group = await asyncio.gather(*tasks, return_exceptions=True)
        for group in results_group:
            if isinstance(group, list):
                results.extend(group)
        return results

    # ---------------------------------
    # Scrape Single Product
    # ---------------------------------
    async def scrape_product(self, product: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
        """
        Scrape product data from its URL and store in Firestore
        """
        session_id = f"scrape_{product['id']}_{int(time.time())}"
        session_ref = self.sessions_ref.document(session_id)
        session_ref.set(
            {
                "session_id": session_id,
                "product_id": product["id"],
                "platform": product["platform"],
                "url": product["product_url"],
                "status": "pending",
                "started_at": datetime.utcnow(),
            }
        )

        try:
            result = await self._scrape_product_data(product)

            # Update Firestore
            session_ref.update(
                {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "success": result.get("success", False),
                }
            )

            if result.get("success") and result.get("price"):
                await self._create_price_record(product, result)

            return result

        except Exception as e:
            logger.error(f"Scraping failed for {product['id']}: {e}")
            self.errors_ref.add(
                {
                    "session_id": session_id,
                    "error_message": str(e),
                    "product_url": product.get("product_url"),
                    "timestamp": datetime.utcnow(),
                }
            )
            session_ref.update(
                {
                    "status": "failed",
                    "completed_at": datetime.utcnow(),
                    "error_message": str(e),
                }
            )
            return {"success": False, "error": str(e), "session_id": session_id}

    # ---------------------------------
    # Core Scraping Logic
    # ---------------------------------
    async def _scrape_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform the actual scraping of product data
        """
        try:
            platform_config = self.platforms.get(product["platform"])
            if not platform_config:
                raise Exception(f"Unsupported platform: {product['platform']}")

            async with httpx.AsyncClient(
                timeout=self.config["timeout"],
                headers=self.config["headers"],
                follow_redirects=True,
            ) as client:
                start = time.time()
                response = await client.get(product["product_url"])
                response_time = int((time.time() - start) * 1000)

                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.reason_phrase}")

                soup = BeautifulSoup(response.content, "html.parser")
                result = {
                    "success": True,
                    "price": self._extract_price(soup),
                    "title": self._extract_title(soup),
                    "availability": self._extract_availability(soup),
                    "image_url": self._extract_image_url(soup, platform_config),
                    "rating": self._extract_rating(soup),
                    "review_count": self._extract_review_count(soup),
                    "response_time_ms": response_time,
                }
                return result
        except Exception as e:
            logger.error(f"Scraping error for {product['id']}: {e}")
            return {"success": False, "error": str(e)}

    # ---------------------------------
    # Data Extraction Helpers
    # ---------------------------------
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        text = soup.get_text()
        matches = re.findall(r"\$\s?(\d+(?:\.\d{1,2})?)", text)
        return float(matches[0]) if matches else None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        h1 = soup.select_one("h1") or soup.title
        return h1.get_text(strip=True) if h1 else None

    def _extract_availability(self, soup: BeautifulSoup) -> Optional[str]:
        txt = soup.get_text().lower()
        if "out of stock" in txt:
            return "Out of Stock"
        if "in stock" in txt:
            return "In Stock"
        return None

    def _extract_image_url(self, soup: BeautifulSoup, config: Dict) -> Optional[str]:
        img = soup.select_one("img") or soup.select_one("#landingImage")
        if img:
            src = img.get("src") or img.get("data-src")
            if src and src.startswith("//"):
                src = "https:" + src
            elif src and src.startswith("/"):
                src = config.get("base_url", "") + src
            return src
        return None

    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        match = re.search(r"(\d+(\.\d+)?)\s*out of\s*5", soup.get_text(), re.I)
        return float(match.group(1)) if match else None

    def _extract_review_count(self, soup: BeautifulSoup) -> Optional[int]:
        match = re.search(r"(\d{1,3}(?:,\d{3})*)\s*(customer )?reviews?", soup.get_text(), re.I)
        return int(match.group(1).replace(",", "")) if match else None

    # ---------------------------------
    # Create Price Record
    # ---------------------------------
    async def _create_price_record(self, product: Dict[str, Any], result: Dict[str, Any]):
        """
        Create or update price record in Firestore
        """
        try:
            current_price = result.get("price")
            product_ref = self.products_ref.document(product["id"])
            product_ref.update(
                {
                    "current_price": current_price,
                    "updated_at": datetime.utcnow(),
                    "last_scraped": datetime.utcnow(),
                }
            )

            self.prices_ref.add(
                {
                    "product_id": product["id"],
                    "price": current_price,
                    "currency": product.get("currency", "USD"),
                    "created_at": datetime.utcnow(),
                    "source_url": product.get("product_url"),
                }
            )
        except Exception as e:
            logger.error(f"Failed to create price record for {product['id']}: {e}")
            raise

    # ---------------------------------
    # Multiple Products
    # ---------------------------------
    async def scrape_multiple_products(
        self, products: List[Dict[str, Any]], max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple products concurrently
        """
        try:
            semaphore = asyncio.Semaphore(max_concurrent)

            async def scrape_with_limit(p):
                async with semaphore:
                    return await self.scrape_product(p)

            results = await asyncio.gather(*[scrape_with_limit(p) for p in products])
            return results
        except Exception as e:
            logger.error(f"Failed to scrape multiple products: {e}")
            raise
