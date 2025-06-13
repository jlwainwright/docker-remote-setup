# Troubleshooting Guide

## Common Issues

### 1. No Threads Found
**Possible Causes:**
- Group is private (requires authentication)
- HTML structure has changed (selectors need updating)
- JavaScript-rendered content (requires browser automation)

**Solutions:**
- Use `--cookies` with valid authentication tokens
- Update CSS selectors in `scraper.py` or use `browser_scraper.py`
- Verify group URL format and structure

### 2. Authentication Failures
**Possible Causes:**
- Expired cookies
- Incorrect cookie format
- Missing required cookie fields

**Solutions:**
- Re-extract cookies using `cookie_helper.py`
- Ensure cookies include all required fields (SID, LSID, etc.)
- Use `--visible` flag in browser_scraper.py to debug login

### 3. Rate Limiting
**Symptoms:**
- Sudden request failures
- Empty responses
- IP blocking

**Solutions:**
- Add `--delay` parameter in batch_extractor.py
- Implement exponential backoff in request logic
- Use rotating proxy setup for large-scale scraping

## Selector Maintenance
When Google Groups updates their HTML structure:

1. Use `inspect_page.py` to analyze current page structure
2. Update selectors in `scraper.py`:
   - Thread list container: `.thread-list` or similar
   - Thread item pattern: `.thread-item` or equivalent
   - Content extraction points: `.post-content`, `.author`, `.date`

3. Test selectors with:
```bash
python inspect_page.py page_source.html
