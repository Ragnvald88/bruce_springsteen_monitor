#!/usr/bin/env python3
"""
Analyze if Fansale.it requires JavaScript for ticket display
Tests both HTTP requests and browser rendering to compare
"""

import requests
import time
from bs4 import BeautifulSoup
import json
from datetime import datetime
import sys
from pathlib import Path

# Python 3.12+ fix
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def test_http_request(url):
    """Test if we can get ticket data via HTTP requests"""
    print("\n=== Testing HTTP Request Method ===")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        # First request - get main page
        print(f"Requesting: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Size: {len(response.text)} bytes")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for ticket elements
        ticket_indicators = [
            '.offer-item',
            '.ticket-item',
            '.listing-item',
            '[data-testid*="ticket"]',
            '[class*="ticket"]',
            '[class*="offer"]',
            '[class*="listing"]',
            '.price',
            '[class*="price"]'
        ]
        
        found_elements = {}
        for selector in ticket_indicators:
            elements = soup.select(selector)
            if elements:
                found_elements[selector] = len(elements)
                print(f"Found {len(elements)} elements matching '{selector}'")
        
        # Look for JavaScript data
        scripts = soup.find_all('script')
        data_scripts = []
        for script in scripts:
            if script.string and any(keyword in script.string for keyword in ['ticket', 'offer', 'price', 'listing', '__INITIAL_STATE__', 'window.__']):
                data_scripts.append({
                    'length': len(script.string),
                    'preview': script.string[:200] + '...' if len(script.string) > 200 else script.string
                })
        
        print(f"\nFound {len(scripts)} script tags, {len(data_scripts)} potentially containing data")
        
        # Check for API endpoints in scripts
        api_patterns = [
            '/api/',
            '/v1/',
            '/v2/',
            'graphql',
            '/tickets',
            '/offers',
            '/listings'
        ]
        
        api_endpoints = []
        for script in scripts:
            if script.string:
                for pattern in api_patterns:
                    if pattern in script.string:
                        # Extract potential URLs
                        import re
                        urls = re.findall(r'["\']([^"\']*' + pattern + r'[^"\']*)["\']', script.string)
                        api_endpoints.extend(urls)
        
        if api_endpoints:
            print(f"\nFound potential API endpoints:")
            for endpoint in set(api_endpoints)[:10]:  # Show first 10 unique
                print(f"  - {endpoint}")
        
        # Save raw HTML for analysis
        with open('fansale_raw_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\nSaved raw HTML to 'fansale_raw_response.html'")
        
        return {
            'status_code': response.status_code,
            'html_size': len(response.text),
            'found_elements': found_elements,
            'script_count': len(scripts),
            'data_scripts': len(data_scripts),
            'api_endpoints': list(set(api_endpoints))[:20],
            'has_ticket_data': bool(found_elements)
        }
        
    except Exception as e:
        print(f"HTTP Request Error: {e}")
        return {'error': str(e)}

def test_browser_rendering(url):
    """Test what we get with browser rendering"""
    print("\n=== Testing Browser Rendering ===")
    
    try:
        # Create minimal UC driver
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        driver = uc.Chrome(options=options)
        
        print(f"Loading page with browser: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for JS to execute
        
        # Check for tickets
        ticket_selectors = [
            '.offer-item',
            '.ticket-item',
            '.listing-item',
            '[data-testid*="ticket"]',
            '[class*="ticket"]',
            '[class*="offer"]'
        ]
        
        found_elements = {}
        for selector in ticket_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                found_elements[selector] = len(elements)
                print(f"Found {len(elements)} elements matching '{selector}'")
                
                # Get sample text from first element
                if elements[0].text:
                    print(f"  Sample text: {elements[0].text[:100]}...")
        
        # Check page source after JS execution
        rendered_html = driver.page_source
        print(f"\nRendered HTML size: {len(rendered_html)} bytes")
        
        # Check for blocked status
        if "access denied" in rendered_html.lower():
            print("WARNING: Access denied detected!")
        
        # Save rendered HTML
        with open('fansale_rendered_response.html', 'w', encoding='utf-8') as f:
            f.write(rendered_html)
        print("Saved rendered HTML to 'fansale_rendered_response.html'")
        
        # Check network requests (if possible)
        try:
            # Execute JS to get performance data
            perf_data = driver.execute_script("""
                return window.performance.getEntriesByType('resource')
                    .filter(e => e.initiatorType === 'xmlhttprequest' || e.initiatorType === 'fetch')
                    .map(e => ({name: e.name, duration: e.duration}));
            """)
            
            if perf_data:
                print(f"\nDetected {len(perf_data)} AJAX/Fetch requests:")
                for req in perf_data[:10]:  # Show first 10
                    print(f"  - {req['name']}")
        except:
            pass
        
        driver.quit()
        
        return {
            'html_size': len(rendered_html),
            'found_elements': found_elements,
            'has_ticket_data': bool(found_elements),
            'blocked': "access denied" in rendered_html.lower()
        }
        
    except Exception as e:
        print(f"Browser Error: {e}")
        return {'error': str(e)}

def compare_results(http_result, browser_result):
    """Compare HTTP vs Browser results"""
    print("\n=== Comparison Results ===")
    
    comparison = {
        'timestamp': datetime.now().isoformat(),
        'http_request': http_result,
        'browser_rendering': browser_result
    }
    
    # Analysis
    print("\nAnalysis:")
    
    if http_result.get('has_ticket_data'):
        print("✅ Tickets appear to be in initial HTML - HTTP requests might work!")
    else:
        print("❌ Tickets NOT found in initial HTML - likely loaded via JavaScript")
    
    if browser_result.get('has_ticket_data'):
        print("✅ Browser rendering shows tickets")
    else:
        print("❌ Browser rendering doesn't show tickets")
    
    if http_result.get('api_endpoints'):
        print(f"\n🔍 Found {len(http_result['api_endpoints'])} potential API endpoints")
        print("   These could be used for direct HTTP requests to fetch ticket data")
    
    # Save results
    with open('fansale_analysis_results.json', 'w') as f:
        json.dump(comparison, f, indent=2)
    print("\nFull results saved to 'fansale_analysis_results.json'")
    
    return comparison

def main():
    """Run the analysis"""
    print("=== Fansale.it JavaScript Requirement Analysis ===")
    
    # Test URL
    url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
    
    # Run tests
    http_result = test_http_request(url)
    browser_result = test_browser_rendering(url)
    
    # Compare
    comparison = compare_results(http_result, browser_result)
    
    # Recommendations
    print("\n=== Recommendations ===")
    
    if http_result.get('has_ticket_data'):
        print("1. HTTP requests CAN retrieve ticket data!")
        print("2. Consider building a faster HTTP-based scraper")
        print("3. Use the saved HTML files to analyze the structure")
    elif http_result.get('api_endpoints'):
        print("1. Tickets are loaded via JavaScript/AJAX")
        print("2. Try reverse-engineering the API calls")
        print("3. Monitor network traffic to find the exact endpoints")
    else:
        print("1. Full browser automation appears necessary")
        print("2. Focus on optimizing browser performance")
        print("3. Consider headless mode for speed")

if __name__ == "__main__":
    main()