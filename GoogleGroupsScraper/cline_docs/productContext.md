# Product Context

## Purpose
This project exists to scrape Google Groups content using browser automation and API requests. It enables data extraction from Google Groups forums when direct API access isn't available.

## Problems Solved
- Bypassing Google Groups' anti-scraping protections
- Maintaining authenticated sessions using cookies
- Extracting structured data from forum threads
- Supporting both browser-based and API-based scraping approaches

## Expected Behavior
The system should:
1. Authenticate using provided cookies
2. Navigate Google Groups pages
3. Extract thread content with metadata
4. Output structured data (JSON/CSV)
5. Handle pagination and rate limiting
