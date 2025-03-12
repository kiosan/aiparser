import logging
import re
from typing import List, Dict, Set, Optional
from urllib.parse import urlparse, urljoin

from .zyte_client import ZyteClient
from .product_extractor import ProductExtractor
from .models import Product

logger = logging.getLogger(__name__)

class ScraperAgent:
    """Agent for scraping websites and extracting product information."""
    
    def __init__(
        self, 
        zyte_api_key: Optional[str] = None, 
        selectors: Optional[Dict[str, str]] = None,
        max_pages: int = 100,
        max_depth: int = 3,
        use_browser: bool = True
    ):
        """
        Initialize the scraper agent.
        
        Args:
            zyte_api_key: Optional Zyte API key
            selectors: Optional CSS selectors for product extraction
            max_pages: Maximum number of pages to scrape
            max_depth: Maximum depth for crawling
            use_browser: Whether to use browser rendering with Zyte API (default: True)
        """
        self.zyte_client = ZyteClient(api_key=zyte_api_key)
        self.product_extractor = ProductExtractor(selectors=selectors)
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.use_browser = use_browser
        
        # Keep track of visited URLs to avoid duplicates
        self.visited_urls: Set[str] = set()
        
        # Product detection patterns
        self.product_url_patterns = [
            r'/product[s]?/',
            r'/item/',
            r'/p/',
            r'/pd/',
            r'/detail/',
        ]
    
    def scrape_website(self, start_url: str) -> List[Product]:
        """
        Scrape a website starting from the given URL.
        
        Args:
            start_url: The starting URL for scraping
            
        Returns:
            List of extracted products
        """
        products = []
        base_domain = self._get_domain(start_url)
        
        # URLs to visit, with their depth
        urls_to_visit = [(start_url, 0)]
        
        # Keep scraping until we reach the maximum or run out of URLs
        while urls_to_visit and len(self.visited_urls) < self.max_pages:
            current_url, depth = urls_to_visit.pop(0)
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
                
            logger.info(f"Scraping URL: {current_url}")
            self.visited_urls.add(current_url)
            
            # Get HTML content with browser rendering as configured
            html = self.zyte_client.get_html(current_url, browser=self.use_browser)
            if not html:
                logger.warning(f"Failed to retrieve HTML content for URL: {current_url}")
                continue
                
            # Check if this is a product page
            if self._is_product_page(current_url, html):
                product = self.product_extractor.extract_from_html(current_url, html)
                products.append(product)
                logger.info(f"Extracted product: {product.name}")
            
            # If we haven't reached max depth, find more links to visit
            if depth < self.max_depth:
                # We don't pass browser parameter here because find_links already uses
                # the HTML we fetched with browser rendering if that option was enabled
                links = self.zyte_client.find_links(current_url)
                
                for link in links:
                    # Only follow links from the same domain
                    if self._get_domain(link) == base_domain and link not in self.visited_urls:
                        urls_to_visit.append((link, depth + 1))
        
        logger.info(f"Scraping completed. Extracted {len(products)} products.")
        return products
    
    def scrape_website_sync(self, start_url: str) -> List[Product]:
        """
        Synchronous version of scrape_website.
        
        Args:
            start_url: The starting URL for scraping
            
        Returns:
            List of extracted products
        """
        # Call the synchronous scrape_website method directly
        return self.scrape_website(start_url)
    
    def _is_product_page(self, url: str, html: str) -> bool:
        """
        Determine if a page is a product page based on URL and content.
        
        Args:
            url: The URL of the page
            html: HTML content of the page
            
        Returns:
            True if the page is likely a product page, False otherwise
        """
        # Check URL patterns
        for pattern in self.product_url_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        # Check common product page indicators in the HTML
        product_indicators = [
            r'<[^>]*itemprop=["\']price["\']',
            r'<[^>]*itemprop=["\']product["\']',
            r'<[^>]*class=["\'].*product.*["\']',
            r'<[^>]*id=["\']product["\']',
            r'<[^>]*class=["\'].*add-to-cart.*["\']',
            r'<[^>]*class=["\'].*buy-now.*["\']',
        ]
        
        for indicator in product_indicators:
            if re.search(indicator, html, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def _get_domain(url: str) -> str:
        """
        Extract the domain from a URL.
        
        Args:
            url: The URL to extract the domain from
            
        Returns:
            Domain name
        """
        parsed_url = urlparse(url)
        return parsed_url.netloc
