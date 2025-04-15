#!/usr/bin/env python3
"""
Client for interacting with the Zyte API.
"""

import os
import json
import time
import logging
import traceback
import hashlib
import datetime
import requests
from typing import Dict, Optional, List, Any, Tuple, Union
from dotenv import load_dotenv
from scraper.html_processor import HtmlProcessor

# Import Redis for caching
import redis
from redis.exceptions import RedisError

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Set up more detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set this module's logger level to DEBUG for maximum visibility
logger.setLevel(logging.DEBUG)

class ZyteClient:
    """Client for interacting with the Zyte API with Redis caching."""
    
    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True, redis_url: Optional[str] = None, cache_ttl_days: int = 100):
        """
        Initialize the Zyte API client.
        
        Args:
            api_key: Zyte API key. If None, it will be loaded from the ZYTE_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("ZYTE_API_KEY")
        if not self.api_key:
            raise ValueError("Zyte API key is required. Set it via ZYTE_API_KEY environment variable or constructor parameter.")
            
        # Log key information for debugging (only showing first 4 chars)
        logger.debug(f"Initializing Zyte client with API key: {self.api_key[:4]}... (length: {len(self.api_key)} chars)")
        
        # Default headers for all requests
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # API endpoint URL
        self.API_URL = "https://api.zyte.com/v1/extract"
        
        # Initialize Redis cache connection if enabled
        self.use_cache = use_cache
        self.cache_ttl_seconds = cache_ttl_days * 24 * 60 * 60  # Convert days to seconds
        self.redis_client = None
        
        if self.use_cache:
            try:
                redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
                logger.info(f"Initializing Redis cache connection to {redis_url}")
                self.redis_client = redis.from_url(redis_url)
                # Test Redis connection
                self.redis_client.ping()
                logger.info("Redis cache connection successful")
            except (RedisError, ConnectionError) as e:
                logger.warning(f"Failed to connect to Redis: {e}. Caching will be disabled.")
                self.use_cache = False
        
        logger.debug("Zyte client initialized successfully")
        
    def _generate_cache_key(self, url: str, browser: bool) -> str:
        """Generate a unique cache key based on URL and browser flag."""
        # Create a key with URL and browser flag to ensure different cache for browser-rendered vs non-browser content
        key_string = f"{url}:{browser}"
        # Use MD5 to create a consistent, reasonably short key
        return f"zyte:html:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def _get_from_cache(self, url: str, browser: bool) -> Optional[Tuple[str, datetime.datetime]]:
        """Try to get content from Redis cache."""
        if not self.use_cache or not self.redis_client:
            return None
        
        cache_key = self._generate_cache_key(url, browser)
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                try:
                    data_dict = json.loads(cached_data)
                    timestamp_str = data_dict.get('timestamp')
                    html_content = data_dict.get('content')
                    
                    if timestamp_str and html_content:
                        timestamp = datetime.datetime.fromisoformat(timestamp_str)
                        logger.info(f"Found cached content for {url} from {timestamp}")
                        return html_content, timestamp
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Error parsing cached data: {e}")
        except RedisError as e:
            logger.warning(f"Redis error when getting from cache: {e}")
        
        return None
    
    def _save_to_cache(self, url: str, browser: bool, html_content: str) -> bool:
        """Save content to Redis cache with expiration."""
        if not self.use_cache or not self.redis_client or not html_content:
            return False
        
        cache_key = self._generate_cache_key(url, browser)
        timestamp = datetime.datetime.now().isoformat()
        data_to_cache = {
            'timestamp': timestamp,
            'content': html_content
        }
        
        try:
            cache_data = json.dumps(data_to_cache)
            self.redis_client.setex(cache_key, self.cache_ttl_seconds, cache_data)
            logger.info(f"Saved {len(html_content)} bytes to cache for {url}")
            return True
        except (RedisError, TypeError) as e:
            logger.warning(f"Failed to save to cache: {e}")
            return False
    
    def clear_cache(self, url: Optional[str] = None, browser: Optional[bool] = None) -> int:
        """Clear all cache or just for a specific URL."""
        if not self.use_cache or not self.redis_client:
            return 0
        
        try:
            if url and browser is not None:
                # Clear specific URL cache
                cache_key = self._generate_cache_key(url, browser)
                result = self.redis_client.delete(cache_key)
                logger.info(f"Cleared cache for specific URL: {url}")
                return result
            elif url:
                # Clear both browser and non-browser cache for URL
                keys_deleted = 0
                for browser_option in [True, False]:
                    cache_key = self._generate_cache_key(url, browser_option)
                    keys_deleted += self.redis_client.delete(cache_key)
                logger.info(f"Cleared all cache variants for URL: {url}")
                return keys_deleted
            else:
                # Clear all Zyte client cache
                keys = self.redis_client.keys("zyte:html:*")
                if keys:
                    result = self.redis_client.delete(*keys)
                    logger.info(f"Cleared all Zyte cache ({len(keys)} entries)")
                    return result
                return 0
        except RedisError as e:
            logger.warning(f"Error clearing cache: {e}")
            return 0
    
    def get_html(self, url: str, headers: Optional[Dict] = None, browser: bool = True, timeout: int = 30, force_refresh: bool = False) -> Optional[str]:
        """
        Retrieve HTML content from a URL using Zyte API with Redis caching.
        
        Args:
            url: The URL to retrieve
            headers: Optional HTTP headers
            browser: Whether to use browser rendering (default: True)
            timeout: Request timeout in seconds (default: 30)
            force_refresh: Whether to bypass cache and force a new API request (default: False)
            
        Returns:
            HTML content as string or None if request failed
        """
        try:
            # Check cache first if not forced to refresh
            if not force_refresh:
                cached_result = self._get_from_cache(url, browser)
                if cached_result:
                    html_content, timestamp = cached_result
                    cache_age = datetime.datetime.now() - timestamp
                    logger.info(f"Using cached content for {url} (age: {cache_age.days} days, {cache_age.seconds//3600} hours)")
                    return html_content
            
            # If cache miss or force refresh, proceed with API request
            logger.info(f"Cache miss or force refresh for {url}, fetching from API")
            
            # Create request payload
            payload = {
                "url": url
            }
            
            # Choose whether to use browser rendering or simple HTTP
            if browser:
                payload["browserHtml"] = True
            else:
                payload["httpResponseBody"] = True
            
            # Add custom headers if provided
            if headers:
                payload["headers"] = headers
            
            # Make the API request
            start_time = time.time()
            logger.info(f"ZYTE CLIENT: Sending request to {self.API_URL}")
            
            response = requests.post(
                self.API_URL,
                auth=(self.api_key, ""),  # Basic auth with API key as username
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            
            elapsed = time.time() - start_time
            logger.info(f"ZYTE CLIENT: Request completed in {elapsed:.2f} seconds")
            logger.info(f"ZYTE CLIENT: Status code: {response.status_code}")
            
            # Check if request was successful
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Extract HTML content based on whether browser rendering was used
                    html_content = None
                    if browser and "browserHtml" in data:
                        html_content = data["browserHtml"]
                    elif not browser and "httpResponseBody" in data:
                        html_content = data["httpResponseBody"]
                    
                    if html_content:
                        content_length = len(html_content)
                        logger.info(f"ZYTE CLIENT: Retrieved HTML content ({content_length} bytes) from URL: {url}")
                        # Process HTML content
                        processed_html = HtmlProcessor.minimize_html(html_content)
                        # Save to cache
                        self._save_to_cache(url, browser, processed_html)
                        
                        return processed_html
                    else:
                        available_keys = list(data.keys())
                        logger.warning(f"ZYTE CLIENT: No HTML content found in response. Available keys: {available_keys}")
                        return None
                        
                except ValueError:
                    logger.error("ZYTE CLIENT: Response is not valid JSON")
                    logger.error(f"ZYTE CLIENT: Raw response (first 200 chars): {response.text[:200]}")
                    return None
            else:
                logger.error(f"ZYTE CLIENT: Request failed with status code: {response.status_code}")
                logger.error(f"ZYTE CLIENT: Error response: {response.text}")
                return None
                
        except requests.Timeout:
            logger.error(f"ZYTE CLIENT: Request timed out after {timeout} seconds")
            return None
        except requests.RequestException as e:
            logger.error(f"ZYTE CLIENT: Request error: {type(e).__name__}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"ZYTE CLIENT: Unexpected error: {type(e).__name__}: {str(e)}")
            logger.error(f"ZYTE CLIENT: Traceback: {''.join(traceback.format_exception(type(e), e, e.__traceback__))}")
            return None
        finally:
            logger.info(f"ZYTE CLIENT: Request to {url} completed")
            logger.info(f"============================================================")
            
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the connection to the Zyte API.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Make a simple request to example.com
            payload = {
                "url": "https://example.com",
                "httpResponseBody": True
            }
            
            logger.info("Testing Zyte API connection...")
            start_time = time.time()
            
            response = requests.post(
                self.API_URL,
                auth=(self.api_key, ""),
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "httpResponseBody" in data:
                    content_length = len(data["httpResponseBody"])
                    success_msg = f"Connection successful! Received {content_length} bytes in {elapsed:.2f} seconds"
                    logger.info(success_msg)
                    return True, success_msg
                else:
                    error_msg = f"Connection succeeded but no content returned after {elapsed:.2f} seconds"
                    logger.warning(error_msg)
                    return False, error_msg
            else:
                error_msg = f"Connection failed with status code: {response.status_code}"
                logger.error(error_msg)
                logger.error(f"Response: {response.text}")
                return False, error_msg
                
        except Exception as e:
            return False, f"Connection failed: {type(e).__name__}: {str(e)}"
    
    def extract_product_info(self, url: str) -> Dict:
        """
        Extract product information using Zyte API's product extraction functionality.
        
        Args:
            url: The URL of the product page
            
        Returns:
            Dictionary containing extracted product information
        """
        try:
            payload = {
                "url": url,
                "productOptions": {},
                "articleBodyExtraction": True,
                "productExtraction": True
            }
            
            logger.info(f"Extracting product information from URL: {url}")
            
            response = requests.post(
                self.API_URL,
                auth=(self.api_key, ""),
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                product_data = data.get("product", {})
                
                # If no product data was extracted, return empty dict
                if not product_data:
                    logger.warning(f"No product data extracted for URL: {url}")
                    
                return product_data
            else:
                logger.error(f"Failed to extract product info. Status: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error extracting product info from {url}: {str(e)}")
            return {}
    
    def find_links(self, url: str, css_selector: str = "a[href]") -> List[str]:
        """
        Find links on a page using a CSS selector.
        
        Args:
            url: The URL to scan for links
            css_selector: CSS selector for finding links, defaults to all anchor tags with href attribute
            
        Returns:
            List of absolute URLs found on the page
        """
        # First, get the HTML content directly
        html_content = self.get_html(url, browser=False)
        
        if not html_content:
            logger.warning(f"No HTML content retrieved for URL: {url}")
            return []
        
        try:
            # Extract links using the provided CSS selector
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, "lxml")
            
            links = []
            for a_tag in soup.select(css_selector):
                href = a_tag.get("href")
                if href:
                    # Convert relative URLs to absolute
                    from urllib.parse import urljoin
                    absolute_url = urljoin(url, href)
                    links.append(absolute_url)
            
            logger.info(f"Found {len(links)} links on {url}")
            return links
            
        except Exception as e:
            logger.error(f"Error finding links on {url}: {str(e)}")
            return []
