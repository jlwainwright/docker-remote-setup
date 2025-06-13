import requests
from bs4 import BeautifulSoup
import time
import logging
import sys
import re
import json
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

class GoogleGroupsScraper:
    def __init__(self, group_url):
        self.group_url = group_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.session = requests.Session()
    
    def authenticate_with_cookies(self, cookies_file):
        """
        Set authentication cookies from a JSON file
        
        Args:
            cookies_file: Path to JSON file containing cookies
        
        Returns:
            bool: True if cookies were loaded successfully, False otherwise
        """
        try:
            with open(cookies_file, 'r') as f:
                cookies = json.load(f)
                
            for name, value in cookies.items():
                self.session.cookies.set(name, value, domain='.google.com')
            
            logging.info(f"Loaded {len(cookies)} cookies from {cookies_file}")
            return True
        except Exception as e:
            logging.error(f"Failed to load cookies: {e}")
            return False
    
    def get_page(self, url):
        """Fetch a page with error handling and retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed: {e}")
                if attempt < max_retries - 1:
                    sleep_time = 2 ** attempt  # Exponential backoff
                    logging.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logging.error("Max retries reached. Giving up.")
                    return None
    
    def extract_thread_info(self, soup):
        """Extract thread titles and links from the page"""
        threads = []
        
        # Try different selectors as Google Groups structure might change
        selectors = [
            ".thread-subject", 
            "a[data-topic-id]", 
            ".thread-header a",
            "a.thread-title",
            "div.jXigdo", # Newer Google Groups format
            "h3.Ds0dsb", # Thread titles in new format
            "a[href*='/c/']", # Thread links format
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if items:
                logging.info(f"Found {len(items)} threads using selector: {selector}")
                for item in items:
                    title = item.get_text(strip=True)
                    link = item.get('href')
                    if link and not link.startswith('http'):
                        link = f"https://groups.google.com{link}"
                    
                    # Try to find author and date information if available
                    author = None
                    date = None
                    
                    # Look for parent container that might have author/date info
                    parent = item.parent
                    if parent:
                        # Look for author info
                        author_elem = parent.select_one(".author, span[role='author'], .bZI0O")
                        if author_elem:
                            author = author_elem.get_text(strip=True)
                        
                        # Look for date info
                        date_elem = parent.select_one(".date, span[role='date'], .wJMDsd")
                        if date_elem:
                            date = date_elem.get_text(strip=True)
                    
                    if title:
                        thread_info = {
                            "title": title,
                            "link": link
                        }
                        
                        if author:
                            thread_info["author"] = author
                        
                        if date:
                            thread_info["date"] = date
                            
                        threads.append(thread_info)
                return threads
        
        logging.warning("No threads found with any selector.")
        return threads
    
    def extract_next_page(self, soup):
        """Extract the next page link if available"""
        next_links = soup.select("a.next-page-link, a[aria-label='Next page'], a.ZIKj2d")
        if next_links:
            next_link = next_links[0].get('href')
            if next_link and not next_link.startswith('http'):
                next_link = f"https://groups.google.com{next_link}"
            return next_link
        return None

    def extract_thread_content(self, thread_url):
        """
        Extract content from a specific thread
        
        Args:
            thread_url: URL of the thread to scrape
            
        Returns:
            dict: Thread details including posts
        """
        logging.info(f"Extracting content from thread: {thread_url}")
        
        response = self.get_page(thread_url)
        if not response:
            logging.error(f"Failed to fetch thread: {thread_url}")
            return None
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract thread title
        title_selectors = ["h1.thread-title", "h2.thread-title", "h1.iUvsJ", "h2.iUvsJ"]
        title = None
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
                
        if not title:
            # Try to find the title in the page title
            page_title = soup.title.string if soup.title else None
            if page_title:
                title = page_title.replace(" - Google Groups", "").strip()
        
        # Extract posts
        posts = []
        
        # Try different selectors for posts
        post_selectors = [
            "div.post", 
            "div.message", 
            "div.EGkKVb", # Newer format
            "div.z7U2we", # Alternative newer format
            "div[role='article']"
        ]
        
        found_posts = False
        for selector in post_selectors:
            post_elements = soup.select(selector)
            if post_elements:
                logging.info(f"Found {len(post_elements)} posts using selector: {selector}")
                found_posts = True
                
                for post_elem in post_elements:
                    post = {}
                    
                    # Extract author
                    author_selectors = [".author", "span[role='author']", ".UXbBWb", ".PBuZLb"]
                    for author_selector in author_selectors:
                        author_elem = post_elem.select_one(author_selector)
                        if author_elem:
                            post["author"] = author_elem.get_text(strip=True)
                            break
                    
                    # Extract date
                    date_selectors = [".date", "span[role='date']", ".ZRWfre", ".nMTYKd"]
                    for date_selector in date_selectors:
                        date_elem = post_elem.select_one(date_selector)
                        if date_elem:
                            post["date"] = date_elem.get_text(strip=True)
                            break
                    
                    # Extract content
                    content_selectors = [".content", ".message-body", ".tlFcqe", ".Xs9Rsd"]
                    for content_selector in content_selectors:
                        content_elem = post_elem.select_one(content_selector)
                        if content_elem:
                            # Preserve line breaks in content
                            post["content"] = "\n".join([line.strip() for line in content_elem.get_text().split("\n") if line.strip()])
                            break
                    
                    # If we couldn't find content with selectors, try getting all text from the post
                    if "content" not in post:
                        # Filter out author and date text if we've found them
                        full_text = post_elem.get_text(strip=True)
                        if "author" in post:
                            full_text = full_text.replace(post["author"], "", 1)
                        if "date" in post:
                            full_text = full_text.replace(post["date"], "", 1)
                        post["content"] = full_text.strip()
                    
                    if post:
                        posts.append(post)
                
                break  # Found posts with this selector, no need to try others
        
        if not found_posts:
            logging.warning(f"No posts found in thread: {thread_url}")
        
        return {
            "url": thread_url,
            "title": title,
            "posts": posts
        }
    
    def scrape_group(self, max_pages=5):
        """Scrape the Google Group for threads, with pagination support"""
        all_threads = []
        current_url = self.group_url
        page_count = 0
        
        while current_url and page_count < max_pages:
            logging.info(f"Scraping page {page_count + 1}: {current_url}")
            response = self.get_page(current_url)
            
            if not response:
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            threads = self.extract_thread_info(soup)
            all_threads.extend(threads)
            
            # Check for next page
            next_page = self.extract_next_page(soup)
            if not next_page or next_page == current_url:
                break
                
            current_url = next_page
            page_count += 1
            
            # Be nice to the server
            time.sleep(2)
        
        return all_threads
    
    def scrape_thread_contents(self, threads, max_threads=None):
        """
        Scrape content from multiple threads
        
        Args:
            threads: List of thread dictionaries with 'link' key
            max_threads: Maximum number of threads to scrape (None for all)
            
        Returns:
            list: Thread details including posts
        """
        thread_contents = []
        
        if max_threads:
            threads = threads[:max_threads]
            
        total_threads = len(threads)
        logging.info(f"Scraping content from {total_threads} threads")
        
        for i, thread in enumerate(threads, 1):
            logging.info(f"Scraping thread {i}/{total_threads}: {thread['title']}")
            
            if 'link' not in thread or not thread['link']:
                logging.warning(f"Thread has no link, skipping: {thread['title']}")
                continue
                
            thread_content = self.extract_thread_content(thread['link'])
            if thread_content:
                thread_contents.append(thread_content)
                
            # Be nice to the server
            if i < total_threads:
                time.sleep(1)
        
        return thread_contents

def main():
    parser = argparse.ArgumentParser(description="Scrape Google Groups for threads and content")
    parser.add_argument("group_url", help="URL of the Google Group to scrape")
    parser.add_argument("--pages", type=int, default=3, help="Maximum number of pages to scrape (default: 3)")
    parser.add_argument("--threads", type=int, default=None, help="Maximum number of threads to scrape content from (default: all)")
    parser.add_argument("--cookies", help="Path to JSON file with authentication cookies for private groups")
    parser.add_argument("--output", help="Path to save the results as JSON")
    parser.add_argument("--content", action="store_true", help="Scrape thread contents in addition to thread list")
    
    args = parser.parse_args()
    
    scraper = GoogleGroupsScraper(args.group_url)
    
    # Authenticate with cookies if provided
    if args.cookies:
        if not scraper.authenticate_with_cookies(args.cookies):
            logging.error("Failed to authenticate with provided cookies. Exiting.")
            return
    
    # Scrape threads
    threads = scraper.scrape_group(max_pages=args.pages)
    
    if not threads:
        logging.warning("No threads were found. The page structure might have changed or the group might be private.")
        return
        
    logging.info(f"Found {len(threads)} threads in total")
    
    # Scrape thread contents if requested
    thread_contents = []
    if args.content:
        thread_contents = scraper.scrape_thread_contents(threads, max_threads=args.threads)
        logging.info(f"Scraped content from {len(thread_contents)} threads")
    
    # Save results or print to console
    if args.output:
        output_data = {
            "group_url": args.group_url,
            "threads": threads
        }
        
        if thread_contents:
            output_data["thread_contents"] = thread_contents
            
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Results saved to {args.output}")
        except Exception as e:
            logging.error(f"Failed to save results: {e}")
    else:
        # Print threads to console
        for i, thread in enumerate(threads, 1):
            print(f"{i}. {thread['title']}")
            if 'author' in thread:
                print(f"   Author: {thread['author']}")
            if 'date' in thread:
                print(f"   Date: {thread['date']}")
            if thread['link']:
                print(f"   Link: {thread['link']}")
            print()
            
        # Print thread contents if available
        if thread_contents:
            print("\n--- Thread Contents ---\n")
            for thread in thread_contents:
                print(f"Thread: {thread['title']}")
                print(f"URL: {thread['url']}")
                print(f"Posts: {len(thread['posts'])}")
                print()
                
                for i, post in enumerate(thread['posts'], 1):
                    print(f"  Post #{i}")
                    if 'author' in post:
                        print(f"  Author: {post['author']}")
                    if 'date' in post:
                        print(f"  Date: {post['date']}")
                    print(f"  Content: {post['content'][:150]}...")
                    print()
                print("-" * 50)
        
if __name__ == "__main__":
    main() 