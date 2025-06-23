#!/usr/bin/env python3
"""
Advanced analysis of Fansale.it to determine if HTTP requests can work
Tests with cookies, proper headers, and session management
"""

import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime

# Python 3.12+ fix
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def analyze_with_browser_session():
    """First use browser to establish session, then test HTTP requests"""
    print("=== Advanced Fansale.it Analysis ===\n")
    
    # Step 1: Use browser to get initial cookies and session
    print("Step 1: Establishing browser session...")
    options = uc.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = uc.Chrome(options=options)
    
    try:
        # Load main page first
        driver.get("https://www.fansale.it")
        time.sleep(3)
        
        # Accept cookies if present
        try:
            cookie_btn = driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
            cookie_btn.click()
            print("✓ Accepted cookies")
            time.sleep(2)
        except:
            print("- No cookie banner found")
        
        # Navigate to tickets page
        ticket_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        print(f"\nNavigating to: {ticket_url}")
        driver.get(ticket_url)
        time.sleep(5)
        
        # Check if we're blocked
        if "access denied" in driver.page_source.lower():
            print("❌ Blocked by access control")
            return
        
        # Get cookies from browser
        browser_cookies = driver.get_cookies()
        print(f"\nCollected {len(browser_cookies)} cookies from browser session")
        
        # Look for tickets in rendered page
        print("\nSearching for tickets in browser...")
        ticket_elements = driver.find_elements(By.CSS_SELECTOR, ".offer-item, .ticket-item, [class*='offer'], [class*='ticket']")
        print(f"Found {len(ticket_elements)} potential ticket elements")
        
        if ticket_elements:
            print("\nSample ticket content:")
            for i, elem in enumerate(ticket_elements[:3]):
                if elem.text:
                    print(f"{i+1}. {elem.text[:100]}...")
        
        # Analyze network requests
        print("\n\nStep 2: Analyzing network requests...")
        
        # Execute JavaScript to capture XMLHttpRequest/Fetch calls
        driver.execute_script("""
            window.capturedRequests = [];
            
            // Capture fetch
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                window.capturedRequests.push({
                    type: 'fetch',
                    url: args[0],
                    method: args[1]?.method || 'GET',
                    timestamp: Date.now()
                });
                return originalFetch.apply(this, args);
            };
            
            // Capture XMLHttpRequest
            const originalOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(method, url, ...rest) {
                this._url = url;
                this._method = method;
                window.capturedRequests.push({
                    type: 'xhr',
                    url: url,
                    method: method,
                    timestamp: Date.now()
                });
                return originalOpen.apply(this, [method, url, ...rest]);
            };
        """)
        
        # Refresh to capture requests
        print("Refreshing page to capture network requests...")
        driver.refresh()
        time.sleep(5)
        
        # Get captured requests
        captured = driver.execute_script("return window.capturedRequests || [];")
        print(f"\nCaptured {len(captured)} network requests:")
        
        api_endpoints = []
        for req in captured:
            print(f"  - {req['method']} {req['url']}")
            if any(pattern in req['url'] for pattern in ['/api/', '/ajax/', 'ticket', 'offer', 'listing']):
                api_endpoints.append(req)
        
        # Look for data in page scripts
        scripts = driver.find_elements(By.TAG_NAME, "script")
        print(f"\nFound {len(scripts)} script tags")
        
        data_patterns = []
        for script in scripts:
            try:
                content = script.get_attribute('innerHTML') or ''
                if content and any(keyword in content for keyword in ['ticket', 'offer', '__INITIAL', 'window.__']):
                    # Look for JSON-like structures
                    json_matches = re.findall(r'(\{[^{}]*ticket[^{}]*\})', content, re.IGNORECASE)
                    if json_matches:
                        data_patterns.append({
                            'preview': content[:200],
                            'potential_data': len(json_matches)
                        })
            except:
                pass
        
        print(f"Found {len(data_patterns)} scripts with potential ticket data")
        
        # Step 3: Test HTTP requests with session cookies
        print("\n\nStep 3: Testing HTTP requests with browser session...")
        
        # Convert cookies for requests
        session = requests.Session()
        for cookie in browser_cookies:
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
        
        # Set headers from browser
        headers = {
            'User-Agent': driver.execute_script("return navigator.userAgent;"),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'max-age=0'
        }
        
        # Test HTTP request with session
        print(f"\nTesting HTTP request to: {ticket_url}")
        response = session.get(ticket_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Size: {len(response.text)} bytes")
        
        # Parse response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for tickets in HTTP response
        http_tickets = soup.select('.offer-item, .ticket-item, [class*="offer"], [class*="ticket"]')
        print(f"Found {len(http_tickets)} ticket elements in HTTP response")
        
        # Test API endpoints if found
        if api_endpoints:
            print("\n\nStep 4: Testing discovered API endpoints...")
            for endpoint in api_endpoints[:5]:  # Test first 5
                try:
                    api_url = endpoint['url']
                    if not api_url.startswith('http'):
                        api_url = f"https://www.fansale.it{api_url}"
                    
                    print(f"\nTesting: {endpoint['method']} {api_url}")
                    api_response = session.request(endpoint['method'], api_url, headers=headers)
                    print(f"  Status: {api_response.status_code}")
                    
                    if api_response.status_code == 200:
                        print(f"  Response size: {len(api_response.text)} bytes")
                        if 'json' in api_response.headers.get('content-type', ''):
                            data = api_response.json()
                            print(f"  JSON data with {len(data)} keys")
                except Exception as e:
                    print(f"  Error: {e}")
        
        # Save analysis results
        results = {
            'timestamp': datetime.now().isoformat(),
            'browser_session': {
                'cookies_collected': len(browser_cookies),
                'tickets_found': len(ticket_elements),
                'blocked': False
            },
            'network_analysis': {
                'requests_captured': len(captured),
                'api_endpoints': [e['url'] for e in api_endpoints],
                'scripts_with_data': len(data_patterns)
            },
            'http_test': {
                'status_code': response.status_code,
                'response_size': len(response.text),
                'tickets_found': len(http_tickets)
            }
        }
        
        with open('fansale_advanced_analysis.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n\n=== Analysis Summary ===")
        print(f"Browser rendering: {'✅ Shows tickets' if ticket_elements else '❌ No tickets'}")
        print(f"HTTP with cookies: {'✅ Shows tickets' if http_tickets else '❌ No tickets'}")
        print(f"API endpoints found: {'✅ Yes' if api_endpoints else '❌ No'}")
        
        print("\n=== Recommendations ===")
        if http_tickets:
            print("1. ✅ HTTP requests WITH proper session/cookies CAN work!")
            print("2. Implement session management to maintain cookies")
            print("3. Use the browser only for initial session establishment")
        elif api_endpoints:
            print("1. Tickets are loaded via AJAX/API calls")
            print("2. Reverse engineer the API endpoints")
            print("3. Use HTTP requests directly to API endpoints")
        else:
            print("1. Full browser automation is required")
            print("2. Tickets are rendered entirely client-side")
            print("3. Focus on optimizing browser performance")
        
        # Save cookies for future use
        with open('data/cookies/fansale_session_cookies.json', 'w') as f:
            json.dump(browser_cookies, f, indent=2)
        print("\nSaved session cookies to data/cookies/fansale_session_cookies.json")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_with_browser_session()