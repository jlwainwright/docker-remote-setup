# Technology Stack

## Core Technologies
- **Python 3.6+**: Primary language for all scripts
- **Requests**: HTTP client for API/web requests
- **BeautifulSoup4**: HTML parsing for web scraping
- **Playwright**: Browser automation for complex rendering (in browser_scraper.py)
- **Argparse**: Command-line interface handling
- **JSON**: Data serialization format

## Development Setup
1. Install core dependencies:
```bash
pip install requests beautifulsoup4
```

2. For browser automation:
```bash
pip install playwright python-dotenv
playwright install
```

3. Environment structure:
- Scripts in root directory (scraper.py, api_scraper.py, etc.)
- Configuration files:
  - sample_cookies.json (authentication example)
  - requirements.txt (project dependencies)

## Technical Constraints
- **Cookie Management**: Requires manual extraction and periodic renewal
- **Rate Limiting**: Google Groups enforces request limits
- **API Stability**: Undocumented API endpoints may change without notice
- **HTML Structure**: Scraping depends on consistent page structure
- **Execution Environment**: Must run in environment with network access to Google services
