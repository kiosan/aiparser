#!/usr/bin/env python3
"""
Script to clear the Redis cache for the Zyte client.
"""

import logging
from scraper.zyte_client import ZyteClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Clear the Redis cache used by the Zyte client."""
    logger.info("Initializing Zyte client...")
    client = ZyteClient()
    
    logger.info("Clearing Redis cache...")
    cleared_keys = client.clear_cache()
    
    logger.info(f"Successfully cleared {cleared_keys} keys from the Redis cache.")
    logger.info("Cache clearing operation complete.")

if __name__ == "__main__":
    main()
