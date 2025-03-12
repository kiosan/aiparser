import logging
from typing import Dict, Optional, List, Any
from bs4 import BeautifulSoup

from .models import Product
from .html_processor import HtmlProcessor

logger = logging.getLogger(__name__)

class ProductExtractor:
    """Extracts structured product information from HTML."""
    
    def __init__(self, selectors: Optional[Dict[str, str]] = None):
        """
        Initialize the product extractor with optional CSS selectors.
        
        Args:
            selectors: Dictionary mapping product attributes to CSS selectors
        """
        # Default selectors that can be overridden
        self.selectors = {
            "name": "h1",
            "price": ".price, .product-price, span[itemprop='price']",
            "currency": "meta[itemprop='priceCurrency']",
            "description": "div[itemprop='description'], .product-description, #product-description",
            "images": "img.product-image, img[itemprop='image']",
            "brand": "meta[itemprop='brand'], .brand",
            "availability": ".availability, [itemprop='availability']"
        }
        
        # Update selectors if provided
        if selectors:
            self.selectors.update(selectors)
            
        self.html_processor = HtmlProcessor()
    
    def extract_from_html(self, url: str, html: str) -> Product:
        """
        Extract product information from HTML content.
        
        Args:
            url: The URL of the product
            html: HTML content of the product page
            
        Returns:
            Product object with extracted information
        """
        # Minimize the HTML first
        minimized_html = self.html_processor.minimize_html(html)
        
        # Create a base product with the URL and raw HTML
        product = Product(
            url=url,
            name="Unknown Product",  # Default name that will be overridden
            raw_html=minimized_html
        )
        
        # Extract basic product info using the HTML processor and CSS selectors
        product.name = self.html_processor.extract_text(minimized_html, self.selectors["name"]) or "Unknown Product"
        product.price = self.html_processor.extract_text(minimized_html, self.selectors["price"])
        product.description = self.html_processor.extract_text(minimized_html, self.selectors["description"])
        product.brand = self.html_processor.extract_text(minimized_html, self.selectors["brand"])
        product.availability = self.html_processor.extract_text(minimized_html, self.selectors["availability"])
        
        # Extract currency
        currency_element = self.html_processor.extract_attribute(
            minimized_html, 
            self.selectors["currency"], 
            "content"
        )
        if currency_element:
            product.currency = currency_element
        
        # Extract product images
        image_urls = self.html_processor.extract_multiple_attributes(
            minimized_html,
            self.selectors["images"],
            "src"
        )
        
        # Convert relative URLs to absolute
        from urllib.parse import urljoin
        product.images = [urljoin(url, img_url) for img_url in image_urls]
        
        # Extract product specifications (this is more complex and site-specific)
        self._extract_specifications(product, minimized_html)
        
        # Try to infer category from breadcrumbs or URL structure
        product.category = self._extract_category(url, minimized_html)
        
        return product
    
    def _extract_specifications(self, product: Product, html: str) -> None:
        """
        Extract product specifications from HTML.
        This is a common pattern, but may need customization for specific websites.
        
        Args:
            product: Product object to update
            html: HTML content
        """
        # Common patterns for specification tables
        spec_selectors = [
            ".specifications tr", 
            ".product-specs tr",
            "table.specs tr",
            "dl.product-specs dt, dl.product-specs dd"
        ]
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Try each selector pattern
        for selector in spec_selectors:
            elements = soup.select(selector)
            
            if elements and 'tr' in selector:
                # Handle table-based specs
                for row in elements:
                    cells = row.select('th, td')
                    if len(cells) >= 2:
                        key = cells[0].get_text().strip().rstrip(':')
                        value = cells[1].get_text().strip()
                        if key and value:
                            product.specifications[key] = value
                            
            elif elements and 'dt' in selector:
                # Handle definition list-based specs
                for i in range(0, len(elements) - 1, 2):
                    if i + 1 < len(elements):
                        key = elements[i].get_text().strip().rstrip(':')
                        value = elements[i + 1].get_text().strip()
                        if key and value:
                            product.specifications[key] = value
            
            # If we found specifications, no need to try other selectors
            if product.specifications:
                break
    
    def _extract_category(self, url: str, html: str) -> Optional[str]:
        """
        Try to extract product category from breadcrumbs or URL structure.
        
        Args:
            url: Product URL
            html: HTML content
            
        Returns:
            Category string or None if not found
        """
        # Try breadcrumbs first (common patterns)
        breadcrumb_selectors = [
            ".breadcrumbs li",
            ".breadcrumb li",
            "nav[aria-label='breadcrumb'] li",
            "[itemtype='http://schema.org/BreadcrumbList'] li"
        ]
        
        for selector in breadcrumb_selectors:
            breadcrumbs = self.html_processor.extract_multiple_texts(html, selector)
            if breadcrumbs and len(breadcrumbs) > 1:
                # Usually the last but one breadcrumb is the category
                # (last one is often the product name)
                return breadcrumbs[-2]
        
        # Fallback: Try to extract from URL
        import re
        from urllib.parse import urlparse
        
        # Common patterns in e-commerce URLs
        path = urlparse(url).path
        
        # Try to find category in path segments like /category/subcategory/product
        path_segments = [s for s in path.split('/') if s]
        if len(path_segments) > 1:
            return path_segments[-2].replace('-', ' ').replace('_', ' ').title()
        
        return None
