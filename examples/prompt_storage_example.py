#!/usr/bin/env python3
"""
Example script demonstrating how to use the PromptStorage utility.
"""

import sys
import os
import logging

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.prompt_storage import get_prompt, get_prompt_storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point."""
    # Get all available prompt keys
    prompt_storage = get_prompt_storage()
    keys = prompt_storage.get_all_keys()
    
    print(f"Available prompt keys: {', '.join(keys)}")
    print("-" * 60)
    
    # Display all prompts
    for key in keys:
        prompt = get_prompt(key)
        print(f"[{key}]")
        print("-" * (len(key) + 2))
        print(prompt)
        print("\n" + "=" * 60 + "\n")
    
    # Example of using a specific prompt
    product_prompt = get_prompt("PRODUCT_EXTRACTION")
    if product_prompt:
        print("Using PRODUCT_EXTRACTION prompt with an agent:")
        print("-" * 40)
        print(f"Agent would receive: {product_prompt[:100]}...")  # Show first 100 chars
    
    # Example of non-existent prompt
    missing_prompt = get_prompt("NON_EXISTENT_KEY")
    if missing_prompt is None:
        print("\nNon-existent prompt key returns None")

if __name__ == "__main__":
    main()
