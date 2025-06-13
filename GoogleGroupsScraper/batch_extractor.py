#!/usr/bin/env python3
"""
Google Groups Batch Thread Extractor

This script allows batch extraction of multiple Google Groups threads
from a list of URLs provided in a text file.

Usage:
    python batch_extractor.py <input_file> [--cookies cookies.json] [--output output_dir] [--delay seconds]

Example:
    python batch_extractor.py thread_urls.txt --cookies google_cookies.json --output threads_data --delay 5
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from scraper import GoogleGroupsScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def extract_group_url(thread_url):
    """Extract the group URL from a thread URL"""
    parts = thread_url.split('/c/')
    if len(parts) < 2 or not parts[0].startswith('https://groups.google.com/g/'):
        return None
    return parts[0]

def sanitize_filename(title):
    """Convert a thread title to a valid filename"""
    # Replace invalid filename characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '_')
    # Limit length to avoid issues with long filenames
    return title[:100]

def main():
    parser = argparse.ArgumentParser(description="Batch extract content from Google Groups threads")
    parser.add_argument("input_file", help="Text file containing thread URLs (one per line)")
    parser.add_argument("--cookies", help="Path to JSON file with authentication cookies (for private groups)")
    parser.add_argument("--output", default="threads", help="Directory to save thread content (default: 'threads')")
    parser.add_argument("--delay", type=int, default=3, help="Delay between requests in seconds (default: 3)")
    parser.add_argument("--summary", action="store_true", help="Generate a summary JSON file with all threads")
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_file):
        logging.error(f"Input file not found: {args.input_file}")
        return 1
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load thread URLs
    try:
        with open(args.input_file, 'r') as f:
            thread_urls = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
    except Exception as e:
        logging.error(f"Failed to read input file: {e}")
        return 1
    
    if not thread_urls:
        logging.error("No valid thread URLs found in the input file")
        return 1
    
    logging.info(f"Found {len(thread_urls)} thread URLs to process")
    
    # Group URLs by Google Group to minimize scraper initialization
    groups = {}
    for url in thread_urls:
        group_url = extract_group_url(url)
        if group_url:
            if group_url not in groups:
                groups[group_url] = []
            groups[group_url].append(url)
        else:
            logging.warning(f"Invalid thread URL format, skipping: {url}")
    
    # Summary data
    all_threads = []
    
    # Process each group
    for group_url, urls in groups.items():
        logging.info(f"Processing group: {group_url} ({len(urls)} threads)")
        
        # Initialize scraper for this group
        scraper = GoogleGroupsScraper(group_url)
        
        # Authenticate with cookies if provided
        if args.cookies:
            if not scraper.authenticate_with_cookies(args.cookies):
                logging.error(f"Failed to authenticate with provided cookies for {group_url}. Skipping group.")
                continue
        
        # Process each thread in this group
        for i, thread_url in enumerate(urls, 1):
            thread_id = thread_url.split('/')[-1]
            logging.info(f"Processing thread {i}/{len(urls)}: {thread_url}")
            
            # Extract thread content
            thread_content = scraper.extract_thread_content(thread_url)
            
            if not thread_content:
                logging.error(f"Failed to extract content from thread: {thread_url}")
                continue
            
            logging.info(f"Successfully extracted: {thread_content['title']} ({len(thread_content['posts'])} posts)")
            
            # Add to summary
            if args.summary:
                all_threads.append(thread_content)
            
            # Save to file
            filename = f"{sanitize_filename(thread_content['title'])}_{thread_id}.json"
            output_path = output_dir / filename
            
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(thread_content, f, indent=2, ensure_ascii=False)
                logging.info(f"Saved to {output_path}")
            except Exception as e:
                logging.error(f"Failed to save thread content: {e}")
            
            # Delay between requests to be nice to the server
            if i < len(urls):
                logging.info(f"Waiting {args.delay} seconds before next request...")
                time.sleep(args.delay)
    
    # Save summary if requested
    if args.summary and all_threads:
        summary_path = output_dir / "summary.json"
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "thread_count": len(all_threads),
                    "threads": all_threads
                }, f, indent=2, ensure_ascii=False)
            logging.info(f"Saved summary to {summary_path}")
        except Exception as e:
            logging.error(f"Failed to save summary: {e}")
    
    logging.info(f"Batch extraction complete. Processed {len(thread_urls)} threads.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 