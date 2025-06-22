#!/usr/bin/env python3
"""
Analyze Fansale.it bot detection mechanisms
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse

def analyze_fansale():
    url = "https://www.fansale.it"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    print("Analyzing https://www.fansale.it...")
    print("=" * 50)
    
    try:
        # Initial request
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
        
        print(f"Status Code: {response.status_code}")
        print(f"Final URL: {response.url}")
        print("\nResponse Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print("\nCookies:")
        for cookie in session.cookies:
            print(f"  {cookie.name}: {cookie.value[:50]}... (domain: {cookie.domain})")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for bot detection services
        print("\nBot Detection Analysis:")
        
        # Check for Cloudflare
        if 'cloudflare' in response.text.lower() or 'cf-ray' in response.headers:
            print("  ✓ Cloudflare detected")
            cf_ray = response.headers.get('cf-ray', 'Not found')
            print(f"    CF-Ray: {cf_ray}")
        
        # Check for Imperva/Incapsula
        if 'incapsula' in response.text.lower() or '_incap_' in str(session.cookies):
            print("  ✓ Imperva/Incapsula detected")
        
        # Check for DataDome
        if 'datadome' in response.text.lower():
            print("  ✓ DataDome detected")
        
        # Check for PerimeterX
        if '_px' in str(session.cookies) or 'perimeterx' in response.text.lower():
            print("  ✓ PerimeterX detected")
        
        # Find all script tags
        print("\nJavaScript Files:")
        scripts = soup.find_all('script')
        for script in scripts:
            src = script.get('src')
            if src:
                print(f"  - {src}")
                # Check for bot detection patterns
                if any(pattern in src.lower() for pattern in ['captcha', 'challenge', 'bot', 'security', 'protect']):
                    print(f"    ^ Possible bot detection script")
        
        # Find inline scripts with bot detection patterns
        print("\nInline Scripts with Bot Detection Patterns:")
        bot_patterns = [
            r'navigator\.webdriver',
            r'phantom',
            r'selenium',
            r'webdriver',
            r'headless',
            r'bot',
            r'crawler',
            r'scraper',
            r'fingerprint',
            r'challenge',
            r'captcha'
        ]
        
        for script in scripts:
            if script.string:
                for pattern in bot_patterns:
                    if re.search(pattern, script.string, re.IGNORECASE):
                        print(f"  Found pattern '{pattern}' in inline script")
                        # Show a snippet
                        match = re.search(pattern, script.string, re.IGNORECASE)
                        if match:
                            start = max(0, match.start() - 50)
                            end = min(len(script.string), match.end() + 50)
                            snippet = script.string[start:end].replace('\n', ' ')
                            print(f"    Context: ...{snippet}...")
        
        # Check for forms and hidden fields
        print("\nForms and Hidden Fields:")
        forms = soup.find_all('form')
        for i, form in enumerate(forms):
            action = form.get('action', 'No action')
            method = form.get('method', 'No method')
            print(f"  Form {i+1}: action='{action}', method='{method}'")
            
            # Find hidden inputs
            hidden_inputs = form.find_all('input', type='hidden')
            if hidden_inputs:
                print("    Hidden fields:")
                for inp in hidden_inputs:
                    name = inp.get('name', 'unnamed')
                    value = inp.get('value', 'no value')
                    if len(str(value)) > 50:
                        value = str(value)[:50] + "..."
                    print(f"      - {name}: {value}")
        
        # Check meta tags
        print("\nSecurity-related Meta Tags:")
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', '')
            content = meta.get('content', '')
            if any(keyword in name.lower() + content.lower() for keyword in ['csrf', 'token', 'security', 'bot']):
                print(f"  {name}: {content}")
        
        # Save response for manual inspection
        with open('fansale_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\nFull response saved to fansale_response.html")
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    analyze_fansale()