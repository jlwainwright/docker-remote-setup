#!/usr/bin/env python3
"""
Google Groups Thread Extractor

This script demonstrates how to use the enhanced GoogleGroupsScraper
to extract content from a specific thread URL.

Usage:
    python thread_extractor.py <thread_url> [--cookies cookies.json] [--output output.json]

Example:
    python thread_extractor.py https://groups.google.com/g/groupname/c/threadid --output thread.json
"""

import argparse
import json
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
    parser = argparse.ArgumentParser(description="Extract content from a Google Groups thread")
    parser.add_argument("thread_url", help="URL of the Google Groups thread to extract")
    parser.add_argument("--cookies", help="Path to JSON file with authentication cookies (for private groups)")
    parser.add_argument("--output", help="Path to save the results as JSON")
    
    args = parser.parse_args()
    
    # Extract group URL from thread URL
    # Format: https://groups.google.com/g/groupname/c/threadid
    parts = args.thread_url.split('/c/')
    if len(parts) < 2 or not parts[0].startswith('https://groups.google.com/g/'):
        logging.error("Invalid thread URL format. Expected: https://groups.google.com/g/groupname/c/threadid")
        return 1
        
    group_url = parts[0]
    logging.info(f"Extracted group URL: {group_url}")
    
    # Initialize the scraper with the group URL
    scraper = GoogleGroupsScraper(group_url)
    
    # Authenticate with cookies if provided
    if args.cookies:
        if not scraper.authenticate_with_cookies(args.cookies):
            logging.error("Failed to authenticate with provided cookies. Exiting.")
            return 1
    
    # Extract thread content
    logging.info(f"Extracting content from thread: {args.thread_url}")
    thread_content = scraper.extract_thread_content(args.thread_url)
    
    if not thread_content:
        logging.error("Failed to extract content from the thread.")
        return 1
    
    logging.info(f"Successfully extracted thread: {thread_content['title']}")
    logging.info(f"Found {len(thread_content['posts'])} posts")
    
    # Save to file or print to console
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(thread_content, f, indent=2, ensure_ascii=False)
            logging.info(f"Thread content saved to {args.output}")
        except Exception as e:
            logging.error(f"Failed to save thread content: {e}")
            return 1
    else:
        # Print thread content to console
        print(f"\nThread: {thread_content['title']}")
        print(f"URL: {thread_content['url']}")
        print(f"Posts: {len(thread_content['posts'])}")
        print("\n" + "="*50 + "\n")
        
        for i, post in enumerate(thread_content['posts'], 1):
            print(f"Post #{i}")
            if 'author' in post:
                print(f"Author: {post['author']}")
            if 'date' in post:
                print(f"Date: {post['date']}")
            print("\nContent:")
            print("-"*50)
            print(post['content'])
            print("\n" + "="*50 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 