# System Architecture Patterns

## Core Patterns
1. **Multi-Scraper Architecture**
   - Web scraper (scraper.py) for basic HTML extraction
   - API scraper (api_scraper.py) for direct API access
   - Browser automation (browser_scraper.py) for complex rendering

2. **Cookie-Based Authentication**
   - Centralized cookie handling through cookie_helper.py
   - Support for both raw cookie strings and cURL format
   - Cookie injection in headers for API/web requests

3. **Modular Script Design**
   - Single-purpose scripts with clear separation of concerns
   - Shared utilities in common.py (if exists) for reusable functions
   - Command-line interface with argparse for consistent UX

4. **Structured Data Pipeline**
   - Thread list extraction -> Thread content extraction -> Output formatting
   - JSON as primary output format with metadata preservation
   - Batch processing pattern for large-scale scraping

## Implementation Details
- **Pagination Handling**: Implemented through page parameter in URL construction
- **Rate Limiting**: Managed via delay parameter in batch_extractor.py
- **Content Extraction**: Uses CSS selectors with fallback mechanisms
- **Error Handling**: Retry logic with exponential backoff in API/web scrapers
