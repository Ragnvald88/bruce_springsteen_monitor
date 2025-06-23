#!/usr/bin/env python3
"""
Quick performance test for StealthMaster
"""

import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print("StealthMaster Performance Test")
print("="*50)

# Test 1: Import time
start = time.time()
try:
    from stealthmaster import StealthMaster
    import_time = time.time() - start
    print(f"✅ Import time: {import_time:.3f}s")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Test 2: Configuration load
start = time.time()
try:
    from stealthmaster import load_config
    config = load_config()
    config_time = time.time() - start
    print(f"✅ Config load: {config_time:.3f}s")
except Exception as e:
    print(f"❌ Config failed: {e}")
    exit(1)

# Test 3: Driver creation
print("\nTesting browser launch...")
start = time.time()
try:
    bot = StealthMaster(config)
    bot.create_driver()
    browser_time = time.time() - start
    print(f"✅ Browser launch: {browser_time:.2f}s")
    
    # Test 4: Page navigation
    print("\nTesting page navigation...")
    start = time.time()
    bot.driver.get("https://www.fansale.it")
    nav_time = time.time() - start
    print(f"✅ Navigation time: {nav_time:.2f}s")
    
    # Test 5: Cookie handling
    print("\nTesting cookie handling...")
    start = time.time()
    handled = bot._handle_cookie_consent()
    cookie_time = time.time() - start
    print(f"✅ Cookie handling: {cookie_time:.2f}s (handled: {handled})")
    
    # Test 6: Login check
    print("\nTesting login detection...")
    start = time.time()
    logged_in = bot._is_logged_in()
    login_check_time = time.time() - start
    print(f"✅ Login check: {login_check_time:.3f}s (logged in: {logged_in})")
    
    # Test 7: Ticket detection
    print("\nTesting ticket detection...")
    bot.driver.get(config['target']['url'])
    time.sleep(3)
    
    start = time.time()
    tickets = bot._find_available_tickets()
    detect_time = time.time() - start
    print(f"✅ Ticket detection: {detect_time:.3f}s (found: {len(tickets)})")
    
    # Summary
    total_time = import_time + config_time + browser_time + nav_time + detect_time
    
    print("\n" + "="*50)
    print("PERFORMANCE SUMMARY")
    print("="*50)
    print(f"Browser launch: {browser_time:.1f}s")
    print(f"Page navigation: {nav_time:.1f}s")
    print(f"Ticket detection: {detect_time:.1f}s")
    print(f"Total startup time: {browser_time + nav_time:.1f}s")
    print()
    
    if browser_time < 5 and nav_time < 5:
        print("✅ EXCELLENT PERFORMANCE - Bot is competitive!")
    elif browser_time < 10 and nav_time < 10:
        print("⚠️ GOOD PERFORMANCE - Should work for most tickets")
    else:
        print("❌ NEEDS OPTIMIZATION - May miss high-demand tickets")
    
    # Cleanup
    bot.driver.quit()
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()