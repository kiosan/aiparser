#!/usr/bin/env python3
"""
CLI script for running the web scraper agent.
"""

import argparse
import json
import logging
import sys
import os
from dotenv import load_dotenv

from scraper.agent import ScraperAgent

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Scrape product information from websites')
    
    parser.add_argument('url', help='The URL of the website to scrape')
    parser.add_argument('-o', '--output', help='Output file path (JSON format)')
    parser.add_argument('-m', '--max-pages', type=int, default=100, help='Maximum number of pages to scrape')
    parser.add_argument('-d', '--max-depth', type=int, default=3, help='Maximum crawl depth')
    parser.add_argument('-k', '--api-key', help='Zyte API key (can also be set via ZYTE_API_KEY environment variable)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Configure verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get API key from arguments or environment
    api_key = args.api_key or os.getenv("ZYTE_API_KEY")
    if not api_key:
        logger.error("Zyte API key not provided. Use --api-key or set ZYTE_API_KEY environment variable.")
        sys.exit(1)
    
    try:
        # Initialize the scraper agent
        agent = ScraperAgent(
            zyte_api_key=api_key,
            max_pages=args.max_pages,
            max_depth=args.max_depth
        )
        
        logger.info(f"Starting scraper for URL: {args.url}")
        logger.info(f"Maximum pages: {args.max_pages}, Maximum depth: {args.max_depth}")
        
        # Run the scraper
        products = agent.scrape_website_sync(args.url)
        
        logger.info(f"Scraped {len(products)} products")
        
        # Convert to JSON-serializable format
        product_dicts = [product.to_dict() for product in products]
        
        # Output results
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(product_dicts, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {args.output}")
        else:
            # Pretty print first 5 products to console
            for i, product in enumerate(products[:5]):
                logger.info(f"Product {i+1}: {product.name}")
                logger.info(f"  URL: {product.url}")
                logger.info(f"  Price: {product.price} {product.currency}")
                logger.info(f"  Images: {len(product.images)} found")
                logger.info("  " + "-" * 40)
                
            if len(products) > 5:
                logger.info(f"...and {len(products) - 5} more products")
    
    except Exception as e:
        logger.exception(f"Error scraping website: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
