#!/usr/bin/env python3
"""
Cookie Helper for Google Groups Scraper

This script helps you extract and save authentication cookies from your browser
to use with the Google Groups API Scraper.

Instructions:
1. Log in to Google Groups in your browser
2. Copy your cookies using browser developer tools
3. Use this script to format and save them for use with api_scraper.py
"""

import json
import sys
import os
import re
import argparse
from pprint import pprint

def extract_cookie_string(cookie_string):
    """
    Extract cookies from a raw cookie string (copied from browser)
    """
    cookies = {}
    
    # Handle different formats
    # Format: "name=value; name2=value2;"
    if ';' in cookie_string:
        cookie_pairs = cookie_string.split(';')
        for pair in cookie_pairs:
            pair = pair.strip()
            if '=' in pair:
                name, value = pair.split('=', 1)
                cookies[name.strip()] = value.strip()
    
    # Format: name=value
    elif '=' in cookie_string:
        name, value = cookie_string.split('=', 1)
        cookies[name.strip()] = value.strip()
    
    return cookies

def extract_from_curl(curl_command):
    """
    Extract cookies from a curl command (copied from browser)
    """
    cookies = {}
    
    # Look for cookie parameters in the curl command
    matches = re.finditer(r'-H\s+[\'"]Cookie:\s+([^\'"]+)[\'"]', curl_command)
    for match in matches:
        cookie_string = match.group(1)
        cookies.update(extract_cookie_string(cookie_string))
    
    # Also look for --cookie parameter
    matches = re.finditer(r'--cookie\s+[\'"]([^\'"]+)[\'"]', curl_command)
    for match in matches:
        cookie_string = match.group(1)
        cookies.update(extract_cookie_string(cookie_string))
    
    return cookies

def extract_from_browser_json(json_data):
    """
    Extract cookies from browser JSON export format
    """
    cookies = {}
    
    try:
        data = json.loads(json_data)
        if isinstance(data, list):
            for cookie in data:
                if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                    cookies[cookie['name']] = cookie['value']
    except json.JSONDecodeError:
        pass  # Not valid JSON
    
    return cookies

def main():
    parser = argparse.ArgumentParser(description="Extract and save authentication cookies for Google Groups API")
    parser.add_argument("--input", "-i", help="Input file containing cookies (if not provided, will prompt for input)")
    parser.add_argument("--output", "-o", default="google_cookies.json", help="Output JSON file for cookies (default: google_cookies.json)")
    parser.add_argument("--format", "-f", choices=["raw", "curl", "json"], help="Format of the input (raw cookie string, curl command, or browser JSON)")
    
    args = parser.parse_args()
    
    cookies = {}
    
    # Get input from file or prompt
    input_data = ""
    if args.input:
        try:
            with open(args.input, 'r') as f:
                input_data = f.read()
        except Exception as e:
            print(f"Error reading input file: {e}")
            return 1
    else:
        print("\nPlease paste your cookies or curl command below.")
        print("(Enter a blank line or press Ctrl+D when finished)\n")
        
        lines = []
        try:
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
        except EOFError:
            pass
        
        input_data = "\n".join(lines)
    
    if not input_data.strip():
        print("No input provided. Exiting.")
        return 1
    
    # Determine format if not specified
    format_type = args.format
    if not format_type:
        if input_data.strip().startswith('curl '):
            format_type = "curl"
        elif input_data.strip().startswith('[') and input_data.strip().endswith(']'):
            format_type = "json"
        else:
            format_type = "raw"
    
    # Extract cookies based on format
    if format_type == "raw":
        cookies = extract_cookie_string(input_data)
    elif format_type == "curl":
        cookies = extract_from_curl(input_data)
    elif format_type == "json":
        cookies = extract_from_browser_json(input_data)
    
    # Check if we got any cookies
    if not cookies:
        print("No cookies could be extracted from the input. Please check the format and try again.")
        return 1
    
    # Essential Google auth cookies to look for
    essential_cookies = [
        "SID", "HSID", "SSID", "APISID", "SAPISID", "NID", "1P_JAR", "__Secure-1PSID", 
        "__Secure-3PSID", "__Secure-1PAPISID", "__Secure-3PAPISID"
    ]
    
    found_essential = [cookie for cookie in essential_cookies if cookie in cookies]
    
    print(f"\nExtracted {len(cookies)} cookies")
    print(f"Found {len(found_essential)}/{len(essential_cookies)} essential authentication cookies")
    
    # Save cookies to file
    try:
        with open(args.output, 'w') as f:
            json.dump(cookies, f, indent=2)
        print(f"\nCookies saved to {args.output}")
    except Exception as e:
        print(f"Error saving cookies: {e}")
        return 1
    
    # Show how to use with the scraper
    print("\nTo use these cookies with the API scraper, run:")
    print(f"python api_scraper.py groupname@googlegroups.com --cookies {args.output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 