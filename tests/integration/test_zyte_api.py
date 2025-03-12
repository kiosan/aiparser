#!/usr/bin/env python3
"""
Simple test script for verifying the Zyte API connection.
"""

# Fix import path to find scraper module
import os
import sys

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

import argparse
import time
from dotenv import load_dotenv

from scraper.zyte_client import ZyteClient
from scraper.html_processor import HtmlProcessor

# Load environment variables from .env file
load_dotenv()

def test_zyte_api(url, use_browser=True, timeout=15):
    """Test the Zyte API connection.
    
    Args:
        url: The URL to fetch
        use_browser: Whether to use browser rendering
        timeout: Request timeout in seconds
        
    Returns:
        None, prints results to stdout
    """
    print(f"Testing Zyte API connection...")
    print(f"URL: {url}")
    print(f"Browser rendering: {'enabled' if use_browser else 'disabled'}")
    print(f"Timeout: {timeout} seconds")
    print("-" * 40)
    
    # Check if API key is set
    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("ERROR: ZYTE_API_KEY environment variable is not set.")
        print("Please set it in your .env file or export it as an environment variable.")
        return False
    
    print("API Key: Found (first 4 chars: " + api_key[:4] + "...)")
    print("-" * 40)
    
    # Initialize client
    try:
        client = ZyteClient()
        print("Client initialization: Success")
    except Exception as e:
        print(f"Client initialization: Failed - {str(e)}")
        return False
    
    # Fetch HTML
    try:
        print("Fetching URL... (this may take a moment)")
        start_time = time.time()
        
        # Set a shorter timeout for the test
        html_content = client.get_html(url, browser=use_browser, timeout=timeout)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        if html_content:
            print(f"Request: Success (took {elapsed:.2f} seconds)")
            print(f"Response size: {len(html_content)} bytes")
            
            # Get a sample of the content
            sample = html_content[:100] + "..." if len(html_content) > 100 else html_content
            print(f"Content sample: {sample}")
            
            # Check if it looks like valid HTML
            if "<html" in html_content.lower() and "</html>" in html_content.lower():
                print("Content validation: Looks like valid HTML")
            else:
                print("Content validation: WARNING - Does not appear to be valid HTML")
            
            # Try minimizing it
            print("-" * 40)
            print("Testing HTML minimization...")
            try:
                minimized = HtmlProcessor.minimize_html(html_content)
                reduction = (1 - len(minimized) / len(html_content)) * 100
                print(f"Original size: {len(html_content)} bytes")
                print(f"Minimized size: {len(minimized)} bytes")
                print(f"Reduction: {reduction:.2f}%")
                return True
            except Exception as e:
                print(f"HTML minimization failed: {str(e)}")
                return False
        else:
            print(f"Request: Failed - No content returned after {elapsed:.2f} seconds")
            return False
            
    except TimeoutError:
        print(f"Request: Failed - Timeout after {timeout} seconds")
        return False
    except Exception as e:
        print(f"Request: Failed - {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test Zyte API connection')
    parser.add_argument('url', help='URL to fetch')
    parser.add_argument('--no-browser', action='store_true', help='Disable browser rendering')
    parser.add_argument('--timeout', type=int, default=15, help='Request timeout in seconds (default: 15)')
    
    args = parser.parse_args()
    
    try:
        result = test_zyte_api(
            args.url,
            use_browser=not args.no_browser,
            timeout=args.timeout
        )
        
        if result:
            print("\nTEST PASSED: Zyte API connection is working correctly.")
            sys.exit(0)
        else:
            print("\nTEST FAILED: Could not successfully retrieve content from Zyte API.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest canceled by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()
