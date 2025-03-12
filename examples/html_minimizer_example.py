#!/usr/bin/env python3
"""
Example script demonstrating HTML minimization functionality using Zyte API.
"""

import os
import sys
import argparse
import base64
from dotenv import load_dotenv

# Add parent directory to path to import scraper module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.html_processor import HtmlProcessor
from scraper.zyte_client import ZyteClient

# Load environment variables from .env file
load_dotenv()

def fetch_html_with_zyte(url, use_browser=True, timeout=30):
    """Fetch HTML content using Zyte API.
    
    Args:
        url: The URL to fetch
        use_browser: Whether to use browser rendering (default: True)
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        HTML content as string or None if request failed
    """
    zyte_client = ZyteClient()
    return zyte_client.get_html(url, browser=use_browser, timeout=timeout)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Minimize HTML content')
    parser.add_argument('input', help='HTML input file or URL')
    parser.add_argument('-o', '--output', help='Output file path (default: stdout)')
    parser.add_argument('-u', '--url', action='store_true', help='Input is a URL instead of a file')
    parser.add_argument('--standard', action='store_true', help='Use standard requests library instead of Zyte API')
    parser.add_argument('--no-browser', action='store_true', help='Disable browser rendering when using Zyte API')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds for Zyte API requests (default: 30)')
    
    args = parser.parse_args()
    
    # Get HTML content
    if args.url:
        if args.standard:
            # Use standard requests library
            import requests
            try:
                response = requests.get(args.input)
                response.raise_for_status()
                html_content = response.text
            except Exception as e:
                print(f"Error retrieving URL: {str(e)}", file=sys.stderr)
                sys.exit(1)
        else:
            # Use Zyte API
            try:
                use_browser = not args.no_browser  # Use browser rendering unless --no-browser flag is set
                try:
                    print(f"Fetching URL with Zyte API (browser rendering: {'enabled' if use_browser else 'disabled'}, timeout: {args.timeout}s)...", file=sys.stderr)
                    html_content = fetch_html_with_zyte(args.input, use_browser=use_browser, timeout=args.timeout)
                except KeyboardInterrupt:
                    print("\nRequest canceled by user.", file=sys.stderr)
                    sys.exit(1)
                
                if not html_content:
                    print(f"Error: No HTML content retrieved from Zyte API. Please check your API key and target URL.", file=sys.stderr)
                    sys.exit(1)
                
                # Check if the content appears to be base64 encoded
                if len(html_content) > 20 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in html_content[:100]):
                    try:
                        # Try to decode base64 content
                        decoded_content = base64.b64decode(html_content).decode('utf-8')
                        print(f"Detected base64 encoded content, decoded successfully", file=sys.stderr)
                        html_content = decoded_content
                    except Exception as decode_error:
                        print(f"Note: Content may be base64 encoded but decoding failed: {str(decode_error)}", file=sys.stderr)
                    
                print(f"Successfully retrieved {len(html_content)} bytes of HTML content", file=sys.stderr)
            except Exception as e:
                print(f"Error retrieving URL with Zyte API: {str(e)}", file=sys.stderr)
                sys.exit(1)
    else:
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            print(f"Error reading file: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    # Minimize HTML
    processor = HtmlProcessor()
    minimized_html = processor.minimize_html(html_content)
    
    # Output result
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(minimized_html)
            print(f"Minimized HTML saved to {args.output}")
        except Exception as e:
            print(f"Error writing to file: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        print(minimized_html)
    
    # Print statistics
    original_size = len(html_content)
    minimized_size = len(minimized_html)
    reduction = (1 - minimized_size / original_size) * 100
    
    print(f"\nHTML size reduction:", file=sys.stderr)
    print(f"Original: {original_size} bytes", file=sys.stderr)
    print(f"Minimized: {minimized_size} bytes", file=sys.stderr)
    print(f"Reduction: {reduction:.2f}%", file=sys.stderr)

if __name__ == "__main__":
    main()
