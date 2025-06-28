#!/usr/bin/env python3
"""
Quick test script for FanSale Bot V6
Tests basic browser creation and navigation
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Force reload environment
load_dotenv(override=True)

# Check environment
print("🔍 Quick Test - FanSale Bot V6")
print("=" * 50)

# Check FANSALE_URL
fansale_url = os.getenv('FANSALE_URL')
if not fansale_url:
    print("\n❌ ERROR: FANSALE_URL not set in .env file!")
    print("\n📝 Please create a .env file with:")
    print("FANSALE_URL=https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388")
    print("\nOr your specific event URL")
    exit(1)

print(f"✅ Target URL: {fansale_url[:50]}...")

# Test browser creation
print("\n🌐 Testing browser creation...")
try:
    import undetected_chromedriver as uc
    
    options = uc.ChromeOptions()
    options.headless = False
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    print("📍 Creating browser...")
    driver = uc.Chrome(options=options)
    
    print("📍 Navigating to FanSale...")
    driver.get(fansale_url)
    
    print("✅ SUCCESS! Browser opened and navigated to FanSale")
    print("\n⏳ Keeping browser open for 10 seconds...")
    time.sleep(10)
    
    print("🧹 Closing browser...")
    driver.quit()
    
    print("\n✅ Test completed successfully!")
    print("You can now run: python fansale_v6.py")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure Chrome/Chromium is installed")
    print("2. Run: pip install -r requirements_v6.txt")
    print("3. Check debug_v6.py for more details")
