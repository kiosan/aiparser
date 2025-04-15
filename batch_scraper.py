#!/usr/bin/env python3
"""
Batch scraper script that processes multiple URLs from a file.
This script reads URLs from uavs.txt and runs the parser for each URL.

Features:
- Resumable processing (can continue from where it left off)
- Error tracking and retries
- API throttling with configurable delays
- Detailed logging and reporting
- Tracking processed websites in processed.txt
"""

import os
import sys
import logging
import argparse
import json
import asyncio
import time
import traceback
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

# Import scraper components
from scraper.zyte_client import ZyteClient
from agent.openai_agent import OpenAIAgent
from dotenv import load_dotenv

# Configure logging
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def check_processed(url):
    """
    Check if a URL has already been processed according to processed.txt
    
    Args:
        url: The URL to check
        
    Returns:
        True if the URL has been processed, False otherwise
    """
    if not os.path.exists('processed.txt'):
        return False
        
    domain = urlparse(url.lower().strip()).netloc.replace('www.', '')
    
    try:
        with open('processed.txt', 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                    
                if domain in line.split(' - ')[0].strip():
                    logger.info(f"URL {url} found in processed.txt, skipping")
                    return True
    except Exception as e:
        logger.error(f"Error checking processed.txt: {e}")
    
    return False

def update_processed(url, product_count):
    """
    Update processed.txt with a successfully processed URL and product count
    
    Args:
        url: The URL that was processed
        product_count: Number of products found
    """
    domain = urlparse(url.lower().strip()).netloc.replace('www.', '')
    
    try:
        with open('processed.txt', 'a') as f:
            f.write(f"{domain} - {product_count}\n")
        logger.info(f"Added {domain} with {product_count} products to processed.txt")
    except Exception as e:
        logger.error(f"Error updating processed.txt: {e}")

def process_url(url, output_dir, type_arg="auto", browser=True, retries=3, retry_delay=5):
    """
    Process a single URL using the specified scraper type with retries.
    
    Args:
        url: The URL to scrape
        output_dir: Directory to save output
        type_arg: Type of scraper to use ('auto', 'agent', 'manual')
        browser: Whether to use browser rendering
        retries: Number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        Path to the output file or None if failed
    """
    # Normalize URL if needed
    if not url.startswith('http'):
        url = f'https://{url}'
        
    # Extract domain for filename
    domain = urlparse(url).netloc.replace('www.', '')
    output_file = os.path.join(output_dir, f"{domain.replace('.', '_')}.json")
    status_file = os.path.join(output_dir, f"{domain.replace('.', '_')}.status.json")
    
    # Check if already processed in processed.txt
    if check_processed(url):
        logger.info(f"URL {url} was already processed according to processed.txt, skipping")
        return output_file
    
    # Check if already processed successfully
    if os.path.exists(output_file):
        logger.info(f"URL {url} was already processed, skipping")
        return output_file
    
    # Check if there's a failed status file
    status = {}
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
            logger.info(f"Found status file for {url}, attempts so far: {status.get('attempts', 0)}")
        except json.JSONDecodeError:
            logger.warning(f"Invalid status file for {url}, starting fresh")
            status = {}
    
    # Initialize status if new
    if not status:
        status = {
            "url": url,
            "attempts": 0,
            "last_attempt": None,
            "errors": []
        }
    
    # Process with retries
    attempt = 0
    max_attempts = status.get('attempts', 0) + retries
    
    while status.get('attempts', 0) < max_attempts:
        attempt = status.get('attempts', 0) + 1
        status['attempts'] = attempt
        status['last_attempt'] = datetime.now().isoformat()
        
        try:
            logger.info(f"Processing URL: {url} (Attempt {attempt}/{max_attempts})")
            
            # Initialize the agent
            agent = OpenAIAgent(model="o3-mini", browser=browser)
            
            # Scrape the website
            logger.info(f"Starting scrape with type: {type_arg}, browser: {browser}")
            # Properly handle the async function by running it in an event loop
            result = asyncio.run(agent.run(url))
            
            # Add metadata
            result["metadata"] = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "scrape_type": type_arg,
                "attempts": attempt
            }
            
            # If no result or empty result, raise exception
            if not result or not result.get("product_urls"):
                error_msg = f"No products found for {url}"
                status['errors'].append({"attempt": attempt, "error": error_msg})
                
                # Save status file for later resume
                with open(status_file, 'w') as f:
                    json.dump(status, f, indent=2)
                    
                logger.warning(error_msg)
                raise ValueError(error_msg)
                
            # Save result to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Results saved to {output_file}")
            
            # Update processed.txt with the number of products
            product_count = len(result.get("product_urls", []))
            update_processed(url, product_count)
            
            # Clean up status file on success
            if os.path.exists(status_file):
                os.remove(status_file)
                
            return output_file
        
        except Exception as e:
            error_details = {
                "attempt": attempt,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            status['errors'].append(error_details)
            
            # Save status file for later resume
            with open(status_file, 'w') as f:
                json.dump(status, f, indent=2)
            
            logger.error(f"Error processing URL {url} (Attempt {attempt}/{max_attempts}): {e}")
            update_processed(url, 0)
            # Break if we've reached max attempts
            if attempt >= max_attempts:
                logger.error(f"Max attempts reached for {url}, giving up")
                break
                
            # Wait before retry
            retry_time = retry_delay * attempt  # Exponential backoff
            logger.info(f"Retrying in {retry_time} seconds...")
            time.sleep(retry_time)
    
    return None

def main():
    """Main function to process URLs from urls.txt file."""
    parser = argparse.ArgumentParser(description='Process multiple URLs from a file.')
    parser.add_argument('--file', default='urls.txt', help='File containing URLs to process (one per line)')
    parser.add_argument('--output', default='output', help='Output directory for results')
    parser.add_argument('--type', default='auto', choices=['auto', 'agent', 'manual'], 
                      help='Type of scraper to use (auto, agent, manual)')
    parser.add_argument('--browser', action='store_true', default=True,
                      help='Use browser rendering for scraping')
    parser.add_argument('--limit', type=int, default=0,
                      help='Limit the number of URLs to process (0 for no limit)')
    parser.add_argument('--delay', type=int, default=2,
                      help='Delay between URL processing in seconds')
    parser.add_argument('--retries', type=int, default=1,
                      help='Number of retry attempts for failed URLs')
    parser.add_argument('--retry-delay', type=int, default=5,
                      help='Initial delay between retries in seconds (grows exponentially)')
    parser.add_argument('--log-file', default='',
                      help='Log file path (in addition to console output)')
    parser.add_argument('--skip-processed', action='store_true',
                      help='Skip URLs that have already been processed (checks output files)')
    parser.add_argument('--skip-in-processed-file', action='store_true', default=True,
                      help='Skip URLs that are listed in processed.txt file')
    parser.add_argument('--debug', action='store_true', 
                      help='Enable debug logging')

    
    args = parser.parse_args()
    
    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.log_file:
        log_dir = os.path.dirname(args.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    # Read URLs from file
    try:
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        logger.error(f"URL file not found: {args.file}")
        sys.exit(1)
    
    if not urls:
        logger.error(f"No URLs found in {args.file}")
        sys.exit(1)
    
    # Apply limit if specified
    if args.limit > 0:
        urls = urls[:args.limit]
    
    logger.info(f"Found {len(urls)} URLs to process")
    
    # Skip already processed URLs if requested
    if args.skip_processed:
        processed_urls = set()
        for url in urls:
            domain = urlparse(url.strip().lower()).netloc.replace('www.', '')
            output_file = os.path.join(args.output, f"{domain.replace('.', '_')}.json")
            if os.path.exists(output_file):
                processed_urls.add(url)
        
        remaining_urls = [url for url in urls if url not in processed_urls]
        logger.info(f"Skipping {len(processed_urls)} already processed URLs based on output files")
        urls = remaining_urls
        
        if not urls:
            logger.info("All URLs have been processed already, exiting")
            sys.exit(0)
            
    # Skip URLs that are in processed.txt
    if args.skip_in_processed_file:
        if os.path.exists('processed.txt'):
            processed_domains = set()
            
            # Read domains from processed.txt
            try:
                with open('processed.txt', 'r') as f:
                    for line in f:
                        if line.startswith('#') or not line.strip():
                            continue
                        parts = line.split(' - ')
                        if len(parts) >= 1:
                            processed_domains.add(parts[0].strip())
            except Exception as e:
                logger.error(f"Error reading processed.txt: {e}")
            
            # Filter URLs
            pre_filter_count = len(urls)
            urls = [url for url in urls if urlparse(url.strip().lower()).netloc.replace('www.', '') not in processed_domains]
            
            skipped_count = pre_filter_count - len(urls)
            if skipped_count > 0:
                logger.info(f"Skipping {skipped_count} URLs found in processed.txt")
            
            if not urls:
                logger.info("All URLs have been processed according to processed.txt, exiting")
                sys.exit(0)
    
    # Process each URL sequentially
    results = []
    errors = []
    
    start_time = time.time()
    for idx, url in enumerate(urls, 1):
        try:
            logger.info(f"Processing URL {idx}/{len(urls)}: {url}")
            output_file = process_url(
                url, 
                output_dir, 
                args.type, 
                args.browser,
                args.retries,
                args.retry_delay
            )
            
            if output_file:
                results.append(output_file)
            else:
                errors.append(url)
        except Exception as e:
            logger.error(f"Unexpected error processing {url}: {e}")
            errors.append(url)
        
        # Add a delay between requests to avoid overwhelming APIs
        if idx < len(urls):
            logger.info(f"Waiting {args.delay} seconds before next URL...")
            time.sleep(args.delay)
    
    # Calculate duration
    duration = time.time() - start_time
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    duration_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    # Print summary
    logger.info("===== Batch Processing Summary =====")
    logger.info(f"Total URLs: {len(urls)}")
    logger.info(f"Successfully processed: {len(results)}/{len(urls)} URLs")
    logger.info(f"Failed: {len(errors)}/{len(urls)} URLs")
    logger.info(f"Total duration: {duration_str}")
    
    if results:
        logger.info("\nSuccessful results:")
        for result in results:
            logger.info(f"  - {result}")
    
    if errors:
        logger.info("\nFailed URLs:")
        for error_url in errors:
            logger.info(f"  - {error_url}")
    
    # Save summary to file
    summary_file = os.path.join(output_dir, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(summary_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_urls": len(urls),
            "successful": len(results),
            "failed": len(errors),
            "duration_seconds": duration,
            "duration_formatted": duration_str,
            "successful_results": results,
            "failed_urls": errors
        }, f, indent=2)
    
    logger.info(f"Summary saved to {summary_file}")
    
    # Exit with error code if any failures
    if errors:
        sys.exit(1)

if __name__ == "__main__":
    main()
