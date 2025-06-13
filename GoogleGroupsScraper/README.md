# Google Groups Scraper

A collection of tools to scrape and extract data from Google Groups, including private groups with proper authentication.

## Features

- Scrape Google Groups using web scraping or API methods
- Support for both public and private groups
- Extract thread titles, authors, dates, and content
- Follow pagination to retrieve multiple pages of threads
- Extract complete thread contents including all posts
- Export data to JSON format
- Authentication helper for accessing private groups

## Requirements

- Python 3.6+
- Required Python packages:
  - requests
  - beautifulsoup4
  - python-dotenv (optional, for browser_scraper.py)
  - playwright (optional, for browser_scraper.py)

Install required packages:

```bash
# Install base requirements
pip install requests beautifulsoup4

# Or use the requirements file
pip install -r requirements.txt

# For browser automation (optional)
pip install playwright python-dotenv
playwright install
```

## Scripts Overview

1. **scraper.py** - Web scraper for Google Groups with thread content extraction and cookie authentication
2. **api_scraper.py** - Uses Google Groups API to extract data (works with private groups when authenticated)
3. **cookie_helper.py** - Utility to extract and save authentication cookies for private groups
4. **browser_scraper.py** - Advanced scraper using Playwright for browser automation (requires additional dependencies)
5. **thread_extractor.py** - Utility to extract content from a specific thread URL
6. **batch_extractor.py** - Batch extraction of multiple threads from a URL list
7. **generate_url_list.py** - Generates a list of thread URLs from a Google Group

## Usage

### Enhanced Web Scraper

The enhanced web scraper supports thread content extraction and cookie-based authentication:

```bash
# Basic usage with a public group
python scraper.py https://groups.google.com/g/groupname

# Specify number of pages to scrape
python scraper.py https://groups.google.com/g/groupname --pages 5

# Scrape thread contents (in addition to thread list)
python scraper.py https://groups.google.com/g/groupname --content

# Limit the number of threads to scrape content from
python scraper.py https://groups.google.com/g/groupname --content --threads 10

# Use cookies for authentication with private groups
python scraper.py https://groups.google.com/g/private-group --cookies google_cookies.json

# Save results to a JSON file
python scraper.py https://groups.google.com/g/groupname --content --output results.json
```

### API Scraper

For more reliable access, especially to private groups, use the API scraper:

```bash
# Basic usage (will likely fail for private groups)
python api_scraper.py groupname@googlegroups.com

# With authentication for private groups
python api_scraper.py groupname@googlegroups.com --cookies google_cookies.json

# Save results to a file
python api_scraper.py groupname@googlegroups.com --cookies google_cookies.json --output results.json

# Specify number of topics to fetch
python api_scraper.py groupname@googlegroups.com --cookies google_cookies.json --topics 50
```

### Browser Automation Scraper

For the most reliable access, especially for groups with complex layouts:

```bash
# Requires: pip install playwright python-dotenv
# And: playwright install

# Interactive mode with browser visible
python browser_scraper.py groupname@googlegroups.com --visible

# With saved cookies
python browser_scraper.py groupname@googlegroups.com --cookies browser_cookies.json
```

### Utility Scripts

#### Single Thread Extractor

Extract content from a specific thread:

```bash
# Extract content from a specific thread
python thread_extractor.py https://groups.google.com/g/groupname/c/threadid

# Use authentication for private threads
python thread_extractor.py https://groups.google.com/g/groupname/c/threadid --cookies google_cookies.json

# Save the thread content to a file
python thread_extractor.py https://groups.google.com/g/groupname/c/threadid --output thread.json
```

#### Batch Thread Extractor

Extract content from multiple threads in batch:

```bash
# Create a text file with thread URLs (one per line)
echo "https://groups.google.com/g/groupname/c/threadid1" > thread_urls.txt
echo "https://groups.google.com/g/groupname/c/threadid2" >> thread_urls.txt

# Process all threads in the file
python batch_extractor.py thread_urls.txt

# Use authentication for private threads
python batch_extractor.py thread_urls.txt --cookies google_cookies.json

# Save output to a specific directory
python batch_extractor.py thread_urls.txt --output threads_data

# Add delay between requests (in seconds)
python batch_extractor.py thread_urls.txt --delay 5

# Generate a summary file with all thread contents
python batch_extractor.py thread_urls.txt --summary
```

#### URL List Generator

Generate a list of thread URLs from a Google Group:

```bash
# Generate a list of thread URLs from a group
python generate_url_list.py https://groups.google.com/g/groupname

# Use authentication for private groups
python generate_url_list.py https://groups.google.com/g/groupname --cookies google_cookies.json

# Specify output file
python generate_url_list.py https://groups.google.com/g/groupname --output my_threads.txt

# Specify number of pages to scrape
python generate_url_list.py https://groups.google.com/g/groupname --pages 10
```

### Workflow for Bulk Extraction

For extracting many threads from a group, use this workflow:

1. Generate a list of thread URLs:
   ```bash
   python generate_url_list.py https://groups.google.com/g/groupname --output thread_urls.txt
   ```

2. Extract content from all threads in the list:
   ```bash
   python batch_extractor.py thread_urls.txt --output extracted_threads
   ```

3. The extracted threads will be saved as individual JSON files in the output directory.

### Authentication for Private Groups

To access private groups, you need to:

1. Log in to Google Groups in your browser
2. Extract your authentication cookies
3. Save them in a format the scraper can use

The `cookie_helper.py` script makes this process easier:

```bash
# Interactive mode (will prompt for cookie input)
python cookie_helper.py

# Specify input file and output file
python cookie_helper.py --input cookies.txt --output google_cookies.json

# Specify the format of input
python cookie_helper.py --format curl --input curl_command.txt
```

## Extracting Cookies from Your Browser

### Chrome

1. Log in to Google Groups
2. Open Developer Tools (F12 or Ctrl+Shift+I)
3. Go to the Network tab
4. Reload the page
5. Click on any request to groups.google.com
6. In the Headers tab, find the "Cookie" header
7. Copy the entire cookie string
8. Paste it when prompted by cookie_helper.py

### Firefox

1. Log in to Google Groups
2. Open Developer Tools (F12 or Ctrl+Shift+I)
3. Go to the Network tab
4. Reload the page
5. Right-click any request to groups.google.com
6. Select "Copy" > "Copy as cURL"
7. Paste the cURL command when prompted by cookie_helper.py with format "curl"

## Example Output

When using the enhanced web scraper with thread content extraction, the JSON output will have the following structure:

```json
{
  "group_url": "https://groups.google.com/g/groupname",
  "threads": [
    {
      "title": "Thread Title",
      "link": "https://groups.google.com/g/groupname/c/threadid",
      "author": "Author Name",
      "date": "Jan 1, 2023"
    },
    ...
  ],
  "thread_contents": [
    {
      "url": "https://groups.google.com/g/groupname/c/threadid",
      "title": "Thread Title",
      "posts": [
        {
          "author": "Author Name",
          "date": "Jan 1, 2023",
          "content": "Post content text..."
        },
        ...
      ]
    },
    ...
  ]
}
```

## Notes

- Google may change their API or page structure at any time, which could break these scripts
- Authentication cookies expire, so you may need to extract new ones periodically
- Respect Google's Terms of Service and don't use this for abusive purposes
- These scripts are for educational purposes only
- Be mindful of rate limiting and add appropriate delays between requests

## Limitations

- The API method relies on undocumented Google APIs that may change
- Cookie authentication requires manual cookie extraction
- Some advanced features (like searching) are not implemented
- Google Groups might use different HTML structures for different groups, requiring selector updates 