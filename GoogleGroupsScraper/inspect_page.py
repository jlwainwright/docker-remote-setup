import requests
from bs4 import BeautifulSoup
import json
import re

def inspect_google_group():
    url = "https://groups.google.com/g/sageoneapi_southafrica"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    response = requests.get(url, headers=headers)
    
    # Print status code and content length
    print(f"Status code: {response.status_code}")
    print(f"Content length: {len(response.text)} bytes")
    
    # Save the raw HTML for inspection
    with open("page_source.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Saved raw HTML to page_source.html")
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Look for potential thread containers
    containers = [
        "div.thread-container", 
        "div.thread", 
        "div.post", 
        "div.topic", 
        ".thread-item",
        "div[jsname]",
        "table tbody tr",
        ".message"
    ]
    
    # Check all div tags with class attributes
    print("\nChecking all div tags with class attributes:")
    div_with_class = soup.select("div[class]")
    class_names = set()
    for div in div_with_class:
        classes = div.get("class", [])
        for cls in classes:
            class_names.add(cls)
    
    print(f"Found {len(class_names)} unique class names in div tags:")
    for cls in sorted(list(class_names)):
        print(f"  - {cls}")
    
    # Check for JavaScript data that might contain thread information
    print("\nLooking for JavaScript data objects:")
    scripts = soup.find_all("script")
    for i, script in enumerate(scripts):
        text = script.string
        if text:
            if "JSON.parse" in text or "window.data" in text or "AF_initDataCallback" in text:
                print(f"Found potential data script ({i}): {text[:100]}...")
            if "topics" in text.lower() or "threads" in text.lower() or "posts" in text.lower():
                print(f"Found script with keywords ({i}): {text[:100]}...")
    
    # Check for any links that might be thread links
    print("\nChecking for potential thread links:")
    links = soup.find_all("a", href=True)
    link_patterns = set()
    for link in links:
        href = link.get("href", "")
        # Extract pattern from href
        pattern = re.sub(r'/[a-zA-Z0-9_-]+(?=/|$)', '/*', href)
        link_patterns.add(pattern)
    
    print(f"Found {len(link_patterns)} unique link patterns:")
    for pattern in sorted(list(link_patterns)):
        print(f"  - {pattern}")

if __name__ == "__main__":
    inspect_google_group() 