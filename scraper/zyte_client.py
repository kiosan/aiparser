#!/usr/bin/env python3
"""
Client for interacting with the Zyte API.
"""

import os
import json
import time
import logging
import traceback
import requests
from typing import Dict, Optional, List, Any, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class ZyteClient:
    """Client for interacting with the Zyte API."""
    
    def __init__(self, api_key: Optional[str] = None):
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
        
        logger.debug("Zyte client initialized successfully")
        
    def get_html(self, url: str, headers: Optional[Dict] = None, browser: bool = True, timeout: int = 30) -> Optional[str]:
        """
        Retrieve HTML content from a URL using Zyte API.
        
        Args:
            url: The URL to retrieve
            headers: Optional HTTP headers
            browser: Whether to use browser rendering (default: True)
            timeout: Request timeout in seconds (default: 30)
            
        Returns:
            HTML content as string or None if request failed
        """
        try:
            # Log attempt with detailed information
            logger.info(f"Fetching URL with Zyte API: {url}")
            logger.info(f"Browser rendering: {'enabled' if browser else 'disabled'}")
            logger.info(f"Timeout: {timeout} seconds")
            
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
            
            # Log the request payload
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            # Make the API request
            start_time = time.time()
            logger.debug(f"Sending request to {self.API_URL}")
            
            response = requests.post(
                self.API_URL,
                auth=(self.api_key, ""),  # Basic auth with API key as username
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            
            elapsed = time.time() - start_time
            logger.debug(f"Request completed in {elapsed:.2f} seconds")
            logger.debug(f"Status code: {response.status_code}")
            
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
                        logger.info(f"Retrieved HTML content ({content_length} bytes) from URL: {url}")
                        return html_content
                    else:
                        available_keys = list(data.keys())
                        logger.warning(f"No HTML content found in response. Available keys: {available_keys}")
                        return None
                        
                except ValueError:
                    logger.error("Response is not valid JSON")
                    logger.error(f"Raw response (first 200 chars): {response.text[:200]}")
                    return None
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                logger.error(f"Error response: {response.text}")
                return None
                
        except requests.Timeout:
            logger.error(f"Request timed out after {timeout} seconds")
            return None
        except requests.RequestException as e:
            logger.error(f"Request error: {type(e).__name__}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {str(e)}")
            logger.error(f"Traceback: {''.join(traceback.format_exception(type(e), e, e.__traceback__))}")
            return None
            
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
