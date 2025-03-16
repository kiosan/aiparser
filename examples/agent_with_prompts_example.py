#!/usr/bin/env python3
"""
Example script demonstrating how to use the OpenAI Agent with prompt storage.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.openai_agent import OpenAIAgent
from scraper.zyte_client import ZyteClient
from scraper.html_processor import HtmlProcessor
from utils.prompt_storage import get_prompt, get_prompt_storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_argparse() -> argparse.Namespace:
    """Set up command line argument parsing."""
    parser = argparse.ArgumentParser(description="OpenAI Agent with Prompt Storage Example")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--type", "-t", choices=["product", "company", "summary"], default="summary", 
                        help="Type of information to extract")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--prompts", "-p", default="prompts.txt", help="Path to prompts file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = setup_argparse()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Print the available prompt keys
    prompt_storage = get_prompt_storage(args.prompts)
    keys = prompt_storage.get_all_keys()
    logger.info(f"Available prompt keys: {', '.join(keys)}")
    
    # Initialize Zyte client to fetch HTML content
    zyte_client = ZyteClient()
    
    # Fetch HTML content from the specified URL
    logger.info(f"Fetching HTML content from {args.url}")
    html_content = zyte_client.get_html(args.url, browser=True)
    
    if not html_content:
        logger.error(f"Failed to retrieve HTML content from {args.url}")
        sys.exit(1)
    
    # Process HTML content
    logger.info("Processing HTML content")
    processed_html = HtmlProcessor.minimize_html(html_content)
    
    # Initialize OpenAI agent with the prompts file
    logger.info(f"Initializing OpenAI Agent with prompts file: {args.prompts}")
    agent = OpenAIAgent(prompts_file=args.prompts)
    
    # Extract information based on the specified type
    logger.info(f"Extracting {args.type} information")
    result = {}
    
    if args.type == "product":
        product_info = agent.extract_product_info(processed_html)
        result = product_info
    elif args.type == "company":
        company_info = agent.extract_company_info(processed_html)
        result = company_info
    elif args.type == "summary":
        summary = agent.summarize_webpage(processed_html)
        result = {"summary": summary}
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    from urllib.parse import urlparse
    from datetime import datetime
    domain = urlparse(args.url).netloc.replace(".", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{domain}_{args.type}_{timestamp}.json"
    
    # Save result to file
    agent.save_to_json(result, str(output_file))
    
    # Print summary
    print(f"\nExtraction completed for {args.url}")
    print(f"Type: {args.type}")
    print(f"Output saved to: {output_file}")
    
    # If it's a summary, print it to the console
    if args.type == "summary" and "summary" in result:
        print("\nSummary:")
        print("-" * 60)
        print(result["summary"])

if __name__ == "__main__":
    main()
