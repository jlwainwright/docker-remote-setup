# Authentication Requirements

## Group Access Levels
1. **Public Groups**
   - No authentication required
   - Basic scraping with scraper.py or browser_scraper.py

2. **Private Groups**
   - Requires valid Google account cookies
   - Must be a group member to access content
   - Authentication must include:
     - SID
     - LSID
     - SSID
     - __Secure-1PSID
     - __Secure-3PSID

## Cookie Extraction Guide
1. **Manual Extraction Steps**
   - Log in to Google Groups in your browser
   - Open Developer Tools (F12 or right-click > Inspect)
   - Navigate to:
     - **Chrome/Edge**: Application tab > Cookies > https://groups.google.com
     - **Firefox**: Storage Inspector > Cookies > https://groups.google.com
     - **Safari**: Develop > Show JavaScript Console > Storage > Cookies
   - Extract these cookie values:
     - `SID`
     - `LSID`
     - `SSID`
     - `__Secure-1PSID`
     - `__Secure-3PSID`
   - Press Ctrl+D (or enter a blank line) to complete input in cookie_helper.py
   - Save in google_cookies.json format:
   ```json
   {
     "SID": "your_sid_value",
     "LSID": "your_lsid_value",
     "SSID": "your_ssid_value",
     "__Secure-1PSID": "your_1psid_value",
     "__Secure-3PSID": "your_3psid_value"
   }
   ```
   - Example cookie values (for reference only - use your actual cookies):
     - SID: 1aBcD... (starts with 1)
     - LSID: AA... (starts with AA)
     - SSID: S... (starts with S)
     - __Secure-1PSID: 1aBcD... (starts with 1)
     - __Secure-3PSID: CA... (starts with CA)
   ```json
   {
     "SID": "your_sid_value",
     "LSID": "your_lsid_value",
     "SSID": "your_ssid_value",
     "__Secure-1PSID": "your_1psid_value",
     "__Secure-3PSID": "your_3psid_value"
   }
   ```

2. **Using cookie_helper.py**
   ```bash
   # Interactive cookie extraction
   python cookie_helper.py

   # From cURL command
   python cookie_helper.py --format curl --input curl_command.txt
   ```

## Browser Automation Authentication
When using browser_scraper.py:
1. For manual login:
   ```bash
   python browser_scraper.py https://groups.google.com/g/groupname --visible
   ```
   - Wait for login prompt in browser
   - Complete 2FA if required

2. For automated login:
   ```bash
   python browser_scraper.py https://groups.google.com/g/groupname \
     --email your_email@gmail.com \
     --password your_password \
     --visible
   ```
   - Note: Google may block automated login attempts
   - Recommended: Use manual login for better security compliance
