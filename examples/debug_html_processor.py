#!/usr/bin/env python3
"""
Debug script for HTML processor to test comment removal.
"""

import os
import sys
import re

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.html_processor import HtmlProcessor

HTML_WITH_COMMENTS = '''
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <!-- Header comment -->
    <meta charset="utf-8">
</head>
<body>
    <h1>Test</h1>
    <!-- Single line comment -->
    <p>This is a test</p>
    
    <!--
    Multi-line comment
    that spans multiple
    lines
    -->
    
    <div>
        <!-- Comment in div -->
        <p>More content</p>
    </div>
    
    <!--[if IE]>
    <p>IE conditional comment</p>
    <![endif]-->
</body>
</html>
'''

def main():
    processor = HtmlProcessor()
    
    print("Original HTML:")
    print("-" * 40)
    print(HTML_WITH_COMMENTS)
    print("-" * 40)
    
    # Count comments in original
    comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)
    original_comments = comment_pattern.findall(HTML_WITH_COMMENTS)
    print(f"Original HTML contains {len(original_comments)} comments:")
    
    for i, comment in enumerate(original_comments):
        print(f"{i+1}. {comment.strip()}")
    
    print("\nProcessing HTML...")
    minimized = processor.minimize_html(HTML_WITH_COMMENTS)
    
    print("\nMinimized HTML:")
    print("-" * 40)
    print(minimized)
    print("-" * 40)
    
    # Check for comments in minimized HTML
    minimized_comments = comment_pattern.findall(minimized)
    if minimized_comments:
        print(f"WARNING: Minimized HTML still contains {len(minimized_comments)} comments:")
        for i, comment in enumerate(minimized_comments):
            print(f"{i+1}. {comment.strip()}")
    else:
        print("SUCCESS: All comments have been removed!")
    
    # Output stats
    original_size = len(HTML_WITH_COMMENTS)
    minimized_size = len(minimized)
    reduction = (original_size - minimized_size) / original_size * 100
    
    print(f"\nSize reduction: {original_size} bytes → {minimized_size} bytes ({reduction:.2f}%)")

if __name__ == "__main__":
    main()
