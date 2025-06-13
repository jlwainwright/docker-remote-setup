#!/usr/bin/env python3
"""
Google Groups URL List Generator

This script scrapes a Google Group and generates a text file with thread URLs,
which can then be used with batch_extractor.py for bulk processing.

Usage:
    python generate_url_list.py <group_url> [--cookies cookies.json] [--output urls.txt] [--pages 5]

Example:
    python generate_url_list.py https://groups.google.com/g/groupname --output thread_urls.txt --pages 3
"""

import argparse
import logging
import sys
from scraper import GoogleGroupsScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def main():
    parser = argparse.ArgumentParser(description="Generate a list of thread URLs from a Google Group")
    parser.add_argument("group_url", help="URL of the Google Group to scrape")
    parser.add_argument("--cookies", help="Path to JSON file with authentication cookies (for private groups)")
    parser.add_argument("--output", default="thread_urls.txt", help="Output file for thread URLs (default: thread_urls.txt)")
    parser.add_argument("--pages", type=int, default=5, help="Maximum number of pages to scrape (default: 5)")
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = GoogleGroupsScraper(args.group_url)
    
    # Authenticate with cookies if provided
    if args.cookies:
        if not scraper.authenticate_with_cookies(args.cookies):
            logging.error("Failed to authenticate with provided cookies. Exiting.")
            return 1
    
    # Scrape threads
    logging.info(f"Scraping threads from group: {args.group_url}")
    threads = scraper.scrape_group(max_pages=args.pages)
    
    if not threads:
        logging.error("No threads found. The group might be private or empty.")
        return 1
    
    # Filter out threads without links
    valid_threads = [thread for thread in threads if thread.get('link')]
    
    if not valid_threads:
        logging.error("No valid thread links found.")
        return 1
    
    logging.info(f"Found {len(valid_threads)} threads with valid links")
    
    # Save URLs to file
    try:
        with open(args.output, 'w') as f:
            for thread in valid_threads:
                f.write(f"{thread['link']}\n")
        
        logging.info(f"Successfully saved {len(valid_threads)} thread URLs to {args.output}")
        
        # Show example usage of batch_extractor.py
        print("\nTo extract content from these threads, run:")
        print(f"python batch_extractor.py {args.output}" + (f" --cookies {args.cookies}" if args.cookies else ""))
        
    except Exception as e:
        logging.error(f"Failed to save thread URLs: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 