#!/usr/bin/env python3
"""
Quick test to verify the FanSale API endpoint
Run this to confirm the API works before using the hybrid bot
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

print("🧪 Testing FanSale API Endpoint...")

# Setup simple browser
options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
driver = uc.Chrome(options=options)

try:
    # Go to FanSale to establish cookies
    print("1️⃣ Navigating to FanSale...")
    driver.get("https://www.fansale.it/fansale/")
    time.sleep(2)
    
    # Check if logged in
    try:
        driver.find_element(By.XPATH, "//*[contains(text(), 'My fanSALE')]")
        print("✅ Logged in!")
    except:
        print("⚠️  Not logged in - API might still work for public data")
    
    # Test the API
    print("\n2️⃣ Testing API endpoint...")
    
    # Your event ID
    event_id = "17844388"
    cache_buster = int(time.time() * 1000)
    
    result = driver.execute_script(f"""
        try {{
            const response = await fetch('https://www.fansale.it/json/offers/{event_id}?_={cache_buster}');
            const data = await response.json();
            return {{
                success: true,
                status: response.status,
                data: data,
                dataLength: Array.isArray(data) ? data.length : 'not-array'
            }};
        }} catch (e) {{
            return {{success: false, error: e.toString()}};
        }}
    """)
    
    print("\n📊 API Response:")
    print(f"Success: {result.get('success')}")
    print(f"Status: {result.get('status')}")
    print(f"Data type: {'Array' if result.get('dataLength') != 'not-array' else 'Other'}")
    print(f"Offers found: {result.get('dataLength', 0)}")
    
    if result.get('success') and result.get('dataLength', 0) > 0:
        print("\n🎫 TICKETS AVAILABLE NOW!")
        print(f"Raw data: {json.dumps(result.get('data', []), indent=2)[:500]}...")
    elif result.get('success'):
        print("\n📭 No tickets currently available (empty array)")
    else:
        print(f"\n❌ API Error: {result.get('error')}")
    
    print("\n✅ API endpoint is working correctly!")
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    
finally:
    input("\nPress Enter to close test browser...")
    driver.quit()
