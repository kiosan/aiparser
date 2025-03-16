#!/usr/bin/env python3
"""
Main application for web scraping with OpenAI Agents and Zyte Client.
"""

import os
import argparse
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
# Handle async execution
import asyncio
from scraper.zyte_client import ZyteClient
from scraper.html_processor import HtmlProcessor
from agent.openai_agent import OpenAIAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log')
    ]
)
logger = logging.getLogger(__name__)

def setup_argparse() -> argparse.Namespace:
    """Set up command line argument parsing."""
    parser = argparse.ArgumentParser(description="Web scraper using OpenAI Agents and Zyte Client")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--output", "-o", default="output", help="Output directory for scraped data")
    parser.add_argument("--type", "-t", choices=["product", "company", "auto"], default="auto", 
                         help="Type of information to extract (product, company, or auto-detect)")
    parser.add_argument("--browser", "-b", action="store_true", help="Use browser rendering for scraping")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    return parser.parse_args()

def scrape_website(url: str, scrape_type: str, use_browser: bool) -> Dict[str, Any]:
    """
    Scrape website and extract information.
    
    Args:
        url: URL to scrape
        scrape_type: Type of information to extract (product, company, or auto)
        use_browser: Whether to use browser rendering
        
    Returns:
        Extracted information
    """
    logger.info(f"Starting scrape for URL: {url}")
    logger.info(f"Scrape type: {scrape_type}")
    logger.info(f"Browser rendering: {'enabled' if use_browser else 'disabled'}")
    
    # Initialize OpenAI agent
    openai_agent = OpenAIAgent(browser=use_browser)
    
    # Extract information based on the specified type
    result = {}
    
    
    res = asyncio.run(openai_agent.run(url))
    
    # Parse the response as JSON and extract product_urls key
    try:
        import json
        if isinstance(res, str):
            parsed_data = json.loads(res)
            if "product_urls" in parsed_data:
                result["product_urls"] = parsed_data["product_urls"]
            else:
                # If product_urls key not found, store the entire parsed response
                result["product_urls"] = parsed_data
        else:
            # If not a string, use as is
            result["product_urls"] = res
    except json.JSONDecodeError:
        logger.warning("Response is not valid JSON, using raw value")
        result["product_urls"] = res
    
    # Add metadata
    result["metadata"] = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "scrape_type": scrape_type
    }
    
    return result

def main():
    """Main entry point."""
    args = setup_argparse()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Scrape the website
    result = scrape_website(args.url, args.type, args.browser)
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename based on the URL
    from urllib.parse import urlparse
    domain = urlparse(args.url).netloc.replace(".", "_")
    output_file = output_dir / f"{domain}.json"
    
    # Save result to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Data saved to {output_file}")
    
    # Print summary
    print(f"\nScraping completed for {args.url}")
    print(f"Data saved to {output_file}")
    
    # Print information types extracted
    if "product" in result:
        print(f"Product information extracted: {len(result['product'])} fields")
    if "company" in result:
        print(f"Company information extracted: {len(result['company'])} fields")

if __name__ == "__main__":
    main()
