#!/usr/bin/env python3
"""
Diagnostic script to identify why bot is blocked
Tests different browser configurations progressively
"""
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

TARGET_URL = "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388"

def test_regular_selenium():
    """Test 1: Regular Selenium (will likely be detected)"""
    print("\n🧪 TEST 1: Regular Selenium Chrome")
    print("-" * 50)
    
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        driver = webdriver.Chrome(options=options)
        
        print("✅ Browser created")
        driver.get(TARGET_URL)
        time.sleep(3)
        
        # Check page title and URL
        print(f"📍 Current URL: {driver.current_url}")
        print(f"📄 Page title: {driver.title}")
        
        # Check for blocking indicators
        if "access" in driver.current_url.lower() or "denied" in driver.title.lower():
            print("❌ BLOCKED - Access denied detected")
        else:
            print("✅ NOT BLOCKED - Page loaded successfully")
            
        # Check navigator.webdriver
        webdriver_flag = driver.execute_script("return navigator.webdriver")
        print(f"🔍 navigator.webdriver: {webdriver_flag}")
        
        input("Press Enter to close browser...")
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_undetected_chrome_minimal():
    """Test 2: Minimal undetected-chromedriver"""
    print("\n🧪 TEST 2: Minimal Undetected Chrome")
    print("-" * 50)
    
    try:
        # Absolute minimal setup
        driver = uc.Chrome()
        
        print("✅ UC Browser created")
        driver.get(TARGET_URL)
        time.sleep(3)
        
        print(f"📍 Current URL: {driver.current_url}")
        print(f"📄 Page title: {driver.title}")
        
        if "access" in driver.current_url.lower() or "denied" in driver.title.lower():
            print("❌ BLOCKED - Access denied detected")
        else:
            print("✅ NOT BLOCKED - Page loaded successfully")
            
        webdriver_flag = driver.execute_script("return navigator.webdriver")
        print(f"🔍 navigator.webdriver: {webdriver_flag}")
        
        input("Press Enter to close browser...")
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_undetected_with_profile():
    """Test 3: UC with custom profile"""
    print("\n🧪 TEST 3: UC with Profile Directory")
    print("-" * 50)
    
    try:
        options = uc.ChromeOptions()
        profile_dir = Path.home() / ".test_fansale_profile"
        options.add_argument(f'--user-data-dir={profile_dir}')
        
        driver = uc.Chrome(options=options)
        
        print("✅ UC Browser with profile created")
        driver.get(TARGET_URL)
        time.sleep(3)
        
        print(f"📍 Current URL: {driver.current_url}")
        print(f"📄 Page title: {driver.title}")
        
        if "access" in driver.current_url.lower() or "denied" in driver.title.lower():
            print("❌ BLOCKED - Profile might be flagged")
        else:
            print("✅ NOT BLOCKED")
            
        input("Press Enter to close browser...")
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_undetected_with_options():
    """Test 4: UC with common options (like in bot)"""
    print("\n🧪 TEST 4: UC with Bot Options")
    print("-" * 50)
    
    try:
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--lang=it-IT')
        
        driver = uc.Chrome(options=options, version_main=138)
        
        print("✅ UC Browser with bot options created")
        driver.get(TARGET_URL)
        time.sleep(3)
        
        print(f"📍 Current URL: {driver.current_url}")
        print(f"📄 Page title: {driver.title}")
        
        if "access" in driver.current_url.lower() or "denied" in driver.title.lower():
            print("❌ BLOCKED - Options might trigger detection")
        else:
            print("✅ NOT BLOCKED")
            
        input("Press Enter to close browser...")
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_fingerprint_comparison():
    """Test 5: Compare fingerprints"""
    print("\n🧪 TEST 5: Fingerprint Analysis")
    print("-" * 50)
    
    # Test regular Chrome
    print("\n📊 Regular Chrome Fingerprint:")
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    
    fingerprint1 = {
        "userAgent": driver.execute_script("return navigator.userAgent"),
        "webdriver": driver.execute_script("return navigator.webdriver"),
        "chrome": driver.execute_script("return window.chrome !== undefined"),
        "permissions": driver.execute_script("return navigator.permissions !== undefined"),
        "plugins": driver.execute_script("return navigator.plugins.length"),
        "languages": driver.execute_script("return navigator.languages")
    }
    
    driver.quit()
    
    # Test UC
    print("\n📊 Undetected Chrome Fingerprint:")
    driver = uc.Chrome()
    
    fingerprint2 = {
        "userAgent": driver.execute_script("return navigator.userAgent"),
        "webdriver": driver.execute_script("return navigator.webdriver"),
        "chrome": driver.execute_script("return window.chrome !== undefined"),
        "permissions": driver.execute_script("return navigator.permissions !== undefined"),
        "plugins": driver.execute_script("return navigator.plugins.length"),
        "languages": driver.execute_script("return navigator.languages")
    }
    
    driver.quit()
    
    # Compare
    print("\n🔍 Comparison:")
    for key in fingerprint1:
        if fingerprint1[key] != fingerprint2[key]:
            print(f"❌ {key}: Regular={fingerprint1[key]}, UC={fingerprint2[key]}")
        else:
            print(f"✅ {key}: {fingerprint1[key]}")

def test_network_analysis():
    """Test 6: Network analysis"""
    print("\n🧪 TEST 6: Network Analysis")
    print("-" * 50)
    
    try:
        options = uc.ChromeOptions()
        options.add_argument('--enable-logging')
        options.add_argument('--v=1')
        
        # Enable network logging
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'network': 'ALL'})
        
        driver = uc.Chrome(options=options)
        
        print("📡 Monitoring network requests...")
        driver.get(TARGET_URL)
        time.sleep(3)
        
        # Get browser logs
        logs = driver.get_log('browser')
        if logs:
            print("\n📋 Browser logs:")
            for entry in logs[:5]:  # First 5 entries
                print(f"  {entry['level']}: {entry['message'][:100]}...")
        
        print(f"\n📍 Final URL: {driver.current_url}")
        
        driver.quit()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all diagnostic tests"""
    print("🔬 FANSALE BOT BLOCKING DIAGNOSTICS")
    print("=" * 60)
    print("This will test different browser configurations to identify")
    print("what's causing the immediate blocking.\n")
    
    tests = [
        ("Regular Selenium", test_regular_selenium),
        ("Minimal UC", test_undetected_chrome_minimal),
        ("UC with Profile", test_undetected_with_profile),
        ("UC with Options", test_undetected_with_options),
        ("Fingerprint Analysis", test_fingerprint_comparison),
        ("Network Analysis", test_network_analysis)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    print("\n💡 RECOMMENDATIONS:")
    print("1. If regular Selenium works but UC doesn't: UC might be detected")
    print("2. If profile test fails: Try clearing all Chrome data")
    print("3. If options test fails: Specific options trigger detection")
    print("4. Check fingerprint differences for detection vectors")

if __name__ == "__main__":
    main()