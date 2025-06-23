#!/usr/bin/env python3
"""
Quick test to verify Akamai cookie behavior on FanSale
"""

import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_cookie_pattern():
    """Test the first request success, then 403 pattern"""
    
    print("🧪 Testing Akamai Cookie Pattern")
    print("=" * 50)
    
    # Setup simple Chrome
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(options=options)
    
    try:
        # Step 1: First visit (no cookies)
        print("\n1️⃣ First visit to FanSale...")
        driver.get("https://www.fansale.it")
        time.sleep(3)
        
        # Check initial cookies
        cookies = driver.get_cookies()
        abck = next((c for c in cookies if c['name'] == '_abck'), None)
        print(f"   _abck cookie: {'Found' if abck else 'Not found'}")
        
        # Step 2: Navigate to API endpoint directly
        print("\n2️⃣ First API call (should work)...")
        api_url = "https://www.fansale.it/json/offers/17844388"
        
        # Use JavaScript to make API call
        result = driver.execute_script("""
            return fetch(arguments[0])
                .then(r => ({status: r.status, ok: r.ok}))
                .catch(e => ({error: e.message}));
        """, api_url)
        
        print(f"   Result: {result}")
        
        # Check cookies after first API call
        time.sleep(2)
        cookies = driver.get_cookies()
        abck = next((c for c in cookies if c['name'] == '_abck'), None)
        if abck:
            print(f"   _abck cookie value: {abck['value'][:30]}...")
            print(f"   Cookie invalid: {abck['value'].endswith('~0~-1~-1')}")
        
        # Step 3: Second API call (might fail)
        print("\n3️⃣ Second API call (might get 403)...")
        time.sleep(2)
        
        result2 = driver.execute_script("""
            return fetch(arguments[0])
                .then(r => ({status: r.status, ok: r.ok}))
                .catch(e => ({error: e.message}));
        """, api_url)
        
        print(f"   Result: {result2}")
        
        # Step 4: Try with XMLHttpRequest
        print("\n4️⃣ Testing with XMLHttpRequest...")
        xhr_result = driver.execute_script("""
            return new Promise((resolve) => {
                const xhr = new XMLHttpRequest();
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        resolve({
                            status: xhr.status,
                            headers: xhr.getAllResponseHeaders()
                        });
                    }
                };
                xhr.open('GET', arguments[0], true);
                xhr.withCredentials = true;
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                xhr.send();
            });
        """, api_url)
        
        print(f"   XMLHttpRequest result: {xhr_result['status']}")
        
        # Final cookie check
        print("\n5️⃣ Final cookie analysis...")
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie['name'] in ['_abck', 'ak_bmsc', 'bm_sz', 'bm_sv']:
                print(f"   {cookie['name']}: {cookie['value'][:30]}...")
        
        # Save cookies for analysis
        cookie_file = Path("test_cookies.json")
        with open(cookie_file, 'w') as f:
            json.dump(cookies, f, indent=2)
        print(f"\n✅ Cookies saved to {cookie_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    test_cookie_pattern()
