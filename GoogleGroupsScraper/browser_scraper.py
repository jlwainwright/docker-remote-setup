#!/usr/bin/env python3
"""
Google Groups Browser Scraper

This script uses Playwright to automate browser actions for scraping Google Groups.
It supports interactive login and can extract data from private groups.

Requirements:
- playwright
- python-dotenv (optional, for credentials)

Install:
pip install playwright python-dotenv
playwright install
"""

import asyncio
import argparse
import json
import os
import sys
import time
import logging
from urllib.parse import quote_plus
from pathlib import Path

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("Error: Playwright is required for this script.")
    print("Install it with: pip install playwright")
    print("Then run: playwright install")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Optional dependency
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

class GoogleGroupsBrowserScraper:
    def __init__(self, headless=False, slow_mo=100):
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser = None
        self.page = None
        self.context = None
        
    async def start(self):
        """Initialize the browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self.context = await self.browser.new_context(viewport={"width": 1280, "height": 800})
        self.page = await self.context.new_page()
        
    async def close(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def login(self, email=None, password=None, cookies_path=None):
        """
        Log in to Google account
        
        Args:
            email: Google account email (if None, will use environment variable GOOGLE_EMAIL)
            password: Google account password (if None, will use environment variable GOOGLE_PASSWORD)
            cookies_path: Path to save/load cookies (if None, won't save/load cookies)
        """
        # Try to load cookies if available
        if cookies_path and os.path.exists(cookies_path):
            try:
                logging.info(f"Loading cookies from {cookies_path}")
                with open(cookies_path, 'r') as f:
                    cookies = json.load(f)
                await self.context.add_cookies(cookies)
                logging.info("Cookies loaded successfully")
                
                # Check if still logged in
                await self.page.goto("https://accounts.google.com/")
                current_url = self.page.url
                if "myaccount.google.com" in current_url or "accounts.google.com/InteractiveLogin" not in current_url:
                    logging.info("Already logged in from cookies")
                    return True
            except Exception as e:
                logging.error(f"Error loading cookies: {e}")
        
        # Interactive login if cookies not available or not valid
        email = email or os.environ.get("GOOGLE_EMAIL")
        password = password or os.environ.get("GOOGLE_PASSWORD")
        
        if not email or not password:
            logging.warning("No email/password provided. Will require manual login.")
            
        # Go to Google login page
        await self.page.goto("https://accounts.google.com/signin")
        
        if email:
            try:
                # Enter email
                await self.page.fill('input[type="email"]', email)
                await self.page.click('#identifierNext button')
                
                # Wait for password field
                await self.page.wait_for_selector('input[type="password"]', timeout=5000)
                
                if password:
                    # Enter password
                    await self.page.fill('input[type="password"]', password)
                    await self.page.click('#passwordNext button')
                else:
                    logging.info("Password not provided. Please enter it manually...")
                    # Wait for manual password entry and completion
                    await self.page.wait_for_url("**/myaccount.google.com/**", timeout=120000)
            except PlaywrightTimeoutError:
                logging.info("Login flow changed or requires manual intervention")
                logging.info("Please complete the login process manually...")
                # Wait for login to complete manually
                await self.page.wait_for_url("**/myaccount.google.com/**", timeout=300000)
        else:
            logging.info("Please log in manually...")
            # Wait for manual login
            await self.page.wait_for_url("**/myaccount.google.com/**", timeout=300000)
        
        logging.info("Login successful")
        
        # Save cookies if path provided
        if cookies_path:
            cookies_dir = os.path.dirname(cookies_path)
            if cookies_dir and not os.path.exists(cookies_dir):
                os.makedirs(cookies_dir)
                
            cookies = await self.context.cookies()
            with open(cookies_path, 'w') as f:
                json.dump(cookies, f)
            logging.info(f"Cookies saved to {cookies_path}")
            
        return True
    
    async def navigate_to_group(self, group_email):
        """Navigate to the Google Group page"""
        encoded_group = quote_plus(group_email)
        url = f"https://groups.google.com/g/{encoded_group}"
        
        logging.info(f"Navigating to group: {url}")
        await self.page.goto(url)
        
        # Check if we need to log in
        if "accounts.google.com/signin" in self.page.url:
            logging.info("Login required to access this group")
            return False
            
        # Check if we have access to the group
        no_access_selector = "text='You don't have permission to access this content'"
        try:
            no_access = await self.page.wait_for_selector(no_access_selector, timeout=2000)
            if no_access:
                logging.error("You don't have permission to access this group")
                return False
        except PlaywrightTimeoutError:
            # No access message not found, which is good
            pass
            
        return True
    
    async def scrape_topics(self, max_topics=20):
        """Scrape topics from the current group page"""
        topics = []
        
        # Wait for topics to load
        try:
            # Look for topic containers - the exact selector may change
            # Try different possible selectors
            selectors = [
                "div.sZwd7c", 
                "div.i4WypI", 
                "div.NpYXU", 
                "a[href*='/m/']",
                "a[href*='/c/']"
            ]
            
            topic_selector = None
            for selector in selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    topic_selector = selector
                    logging.info(f"Found topics with selector: {selector}")
                    break
                except PlaywrightTimeoutError:
                    continue
                    
            if not topic_selector:
                logging.error("Couldn't find any topics on the page")
                return topics
                
            # Get all topic elements
            topic_elements = await self.page.query_selector_all(topic_selector)
            
            for element in topic_elements[:max_topics]:
                topic = {}
                
                # Extract title
                title_element = await element.query_selector("h3") or await element.query_selector("span") or element
                if title_element:
                    topic["title"] = await title_element.inner_text()
                
                # Extract URL if it's a link
                href = await element.get_attribute("href")
                if href:
                    if href.startswith("/"):
                        topic["url"] = f"https://groups.google.com{href}"
                    else:
                        topic["url"] = href
                
                # Extract author if available
                author_element = await element.query_selector("span[role='author']") or await element.query_selector(".bZI0O")
                if author_element:
                    topic["author"] = await author_element.inner_text()
                
                # Extract date if available
                date_element = await element.query_selector("span[role='date']") or await element.query_selector(".wJMDsd")
                if date_element:
                    topic["date"] = await date_element.inner_text()
                
                if topic and "title" in topic:
                    topics.append(topic)
            
            logging.info(f"Scraped {len(topics)} topics")
            
        except Exception as e:
            logging.error(f"Error scraping topics: {e}")
            
        return topics
    
    async def scrape_group(self, group_email, max_topics=20):
        """
        Scrape a Google Group
        
        Args:
            group_email: The email address of the Google Group
            max_topics: Maximum number of topics to scrape
            
        Returns:
            List of topics with their details
        """
        # Navigate to the group
        has_access = await self.navigate_to_group(group_email)
        if not has_access:
            return []
            
        # Scrape topics
        topics = await self.scrape_topics(max_topics)
        return topics

async def main():
    parser = argparse.ArgumentParser(description="Scrape Google Groups using browser automation")
    parser.add_argument("group", help="Google Group email address (e.g., groupname@googlegroups.com)")
    parser.add_argument("--email", help="Google account email (if not provided, will use GOOGLE_EMAIL environment variable)")
    parser.add_argument("--password", help="Google account password (if not provided, will use GOOGLE_PASSWORD environment variable)")
    parser.add_argument("--cookies", default="cookies/google_cookies.json", help="Path to save/load cookies (default: cookies/google_cookies.json)")
    parser.add_argument("--topics", type=int, default=20, help="Number of topics to fetch (default: 20)")
    parser.add_argument("--output", help="Output file path for JSON results")
    parser.add_argument("--visible", action="store_true", help="Show the browser window during scraping")
    parser.add_argument("--slow", type=int, default=100, help="Slow down automation by this many milliseconds (default: 100)")
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = GoogleGroupsBrowserScraper(
        headless=not args.visible,
        slow_mo=args.slow
    )
    
    try:
        await scraper.start()
        
        # Login if needed
        await scraper.login(args.email, args.password, args.cookies)
        
        # Scrape group
        topics = await scraper.scrape_group(args.group, args.topics)
        
        if topics:
            if args.output:
                # Save to file
                with open(args.output, 'w') as f:
                    json.dump(topics, f, indent=2)
                logging.info(f"Topics saved to {args.output}")
            else:
                # Print to console
                print(f"\nFound {len(topics)} topics in {args.group}:\n")
                for i, topic in enumerate(topics, 1):
                    print(f"{i}. {topic.get('title', 'No Title')}")
                    if "author" in topic:
                        print(f"   Author: {topic['author']}")
                    if "date" in topic:
                        print(f"   Date: {topic['date']}")
                    if "url" in topic:
                        print(f"   URL: {topic['url']}")
                    print()
        else:
            print(f"\nNo topics found or unable to access the group: {args.group}")
            print("Note: If this is a private group, you need to be a member and logged in.")
    
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())